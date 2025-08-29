"""LiblibAI图像生成服务实现

提供LiblibAI API的完整封装，包括F.1模型和传统模型的支持。
"""

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from tqdm import tqdm

from ...config import Config
from ...models.image_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageServiceType,
)
from .base import ImageServiceBase


class GenerateStatus(Enum):
    """生图状态枚举"""

    PENDING = 1  # 排队中
    PROCESSING = 2  # 生图中
    SUCCESS = 5  # 生图成功
    FAILED = 6  # 生图失败
    TIMEOUT = 7  # 生图超时


class AuditStatus(Enum):
    """审核状态枚举"""

    PENDING = 1  # 审核中
    APPROVED = 3  # 审核通过
    REJECTED = 4  # 审核不通过


@dataclass
class LiblibConfig:
    """LiblibAI配置类"""

    access_key: str
    secret_key: str
    base_url: str = "https://openapi.liblibai.cloud"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


@dataclass
class AdditionalNetwork:
    """LoRA网络参数类"""

    model_id: str  # LoRA的模型版本uuid
    weight: float = 1.0  # LoRA权重


@dataclass
class HiResFixInfo:
    """高分辨率修复参数类"""

    hires_steps: int = 20  # 高分辨率修复步数
    hires_denoising_strength: float = 0.75  # 高分辨率去噪强度
    upscaler: int = 10  # 放大器类型
    resized_width: int = 1024  # 调整后宽度
    resized_height: int = 1536  # 调整后高度


@dataclass
class F1GenerationParams:
    """F.1文生图参数类 - 仅支持F.1模型的参数"""

    # 基础参数 - F.1支持的参数
    prompt: str  # 正向提示词
    steps: int = 20  # 采样步数
    width: int = 768  # 宽度
    height: int = 1024  # 高度
    img_count: int = 1  # 图片数量 (1-4)
    seed: int = -1  # 随机种子值，-1表示随机
    restore_faces: int = 0  # 面部修复，0关闭，1开启
    template_uuid: str = "6f7c4652458d4802969f8d089cf5b91"  # 参数模板ID
    negative_prompt: str = ""  # 负向提示词

    # 高级参数
    cfg_scale: float = 3.5  # CFG引导强度
    randn_source: int = 0  # 随机数源
    clip_skip: int = 2  # CLIP跳过层数
    sampler: int = 1  # 采样器类型

    # 扩展功能 - F.1支持LoRA网络
    additional_network: List[AdditionalNetwork] = field(
        default_factory=list
    )  # LoRA网络列表，最多5个
    hi_res_fix_info: Optional[HiResFixInfo] = None  # 高分辨率修复信息

    @classmethod
    def from_config(cls, prompt: str, config: Config, **kwargs) -> "F1GenerationParams":
        """从配置创建F.1参数对象"""
        # 从配置获取默认值
        defaults = {
            "steps": config.f1_default_steps,
            "width": config.f1_default_width,
            "height": config.f1_default_height,
            "cfg_scale": config.f1_default_cfg_scale,
            "negative_prompt": config.liblib_negative_prompt,
            "img_count": config.f1_default_img_count,
            "seed": config.f1_default_seed,
            "restore_faces": config.f1_default_restore_faces,
            "clip_skip": config.f1_default_clip_skip,
            "sampler": config.f1_default_sampler,
            "randn_source": config.f1_default_randn_source,
            "template_uuid": config.f1_default_template_uuid,
        }

        # 添加AdditionalNetwork默认配置
        if (
            config.f1_default_additional_network_enabled
            and config.f1_default_additional_network_model_id
        ):
            defaults["additional_network"] = [
                AdditionalNetwork(
                    model_id=config.f1_default_additional_network_model_id,
                    weight=config.f1_default_additional_network_weight,
                )
            ]

        # 添加HiResFixInfo默认配置
        if config.f1_default_hires_enabled:
            defaults["hi_res_fix_info"] = HiResFixInfo(
                hires_steps=config.f1_default_hires_steps,
                hires_denoising_strength=config.f1_default_hires_denoising_strength,
                upscaler=config.f1_default_upscaler,
                resized_width=config.f1_default_hires_resized_width,
                resized_height=config.f1_default_hires_resized_height,
            )

        # 用kwargs覆盖默认值
        defaults.update(kwargs)

        return cls(prompt=prompt, **defaults)

    def to_dict(self) -> Dict[str, Any]:
        """转换为API请求格式"""
        result = {
            "prompt": self.prompt,
            "steps": self.steps,
            "width": self.width,
            "height": self.height,
            "imgCount": self.img_count,  # 使用驼峰命名
            "seed": self.seed,
            "restoreFaces": self.restore_faces,  # 使用驼峰命名
            "negativePrompt": self.negative_prompt,  # 使用驼峰命名
            "cfgScale": self.cfg_scale,  # 使用驼峰命名
            "randnSource": self.randn_source,  # 使用驼峰命名
            "clipSkip": self.clip_skip,  # 使用驼峰命名
            "sampler": self.sampler,
        }

        # 添加LoRA网络
        if self.additional_network:
            result["additionalNetwork"] = [  # 使用驼峰命名
                {"modelId": network.model_id, "weight": network.weight}  # 使用驼峰命名
                for network in self.additional_network
            ]

        # 添加高分辨率修复
        if self.hi_res_fix_info:
            result["hiResFixInfo"] = {  # 使用驼峰命名
                "hiresSteps": self.hi_res_fix_info.hires_steps,  # 使用驼峰命名
                # TODO: 手动修复长行 -                 "hiresDenoisingStrength": self.hi_res_fix_info.hires_denoising_strength,  # 使用驼峰命名
                "upscaler": self.hi_res_fix_info.upscaler,
                "resizedWidth": self.hi_res_fix_info.resized_width,  # 使用驼峰命名
                "resizedHeight": self.hi_res_fix_info.resized_height,  # 使用驼峰命名
            }

        return result


@dataclass
class GenerateResult:
    """生图结果类"""

    generate_uuid: str
    status: GenerateStatus
    progress: float
    message: str
    points_cost: int
    account_balance: int
    images: List[Dict[str, Any]]


class LiblibService(ImageServiceBase):
    """LiblibAI图像生成服务"""

    def __init__(self, liblib_config: LiblibConfig, app_config: Config):
        super().__init__(ImageServiceType.LIBLIB_AI)
        self.config = liblib_config
        self.app_config = app_config
        self.session = requests.Session()
        self.session.timeout = liblib_config.timeout

    def _generate_signature(self, uri: str) -> Dict[str, str]:
        """生成API签名"""
        timestamp = str(int(time.time() * 1000))
        signature_nonce = str(uuid.uuid4())

        # 拼接原文
        content = f"{uri}&{timestamp}&{signature_nonce}"

        # 生成签名
        digest = hmac.new(
            self.config.secret_key.encode(), content.encode(), hashlib.sha1
        ).digest()

        # 生成URL安全的base64签名
        signature = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

        return {
            "AccessKey": self.config.access_key,
            "Signature": signature,
            "Timestamp": timestamp,
            "SignatureNonce": signature_nonce,
        }

    def _make_request(
        self, method: str, uri: str, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """发起API请求"""
        auth_params = self._generate_signature(uri)
        url = f"{self.config.base_url}{uri}"

        headers = {"Content-Type": "application/json"}

        # 打印请求信息
        print("\n=== LiblibAI API 请求信息 ===")
        print(f"请求方法: {method.upper()}")
        print(f"请求URL: {url}")
        print(f"认证参数: {json.dumps(auth_params, indent=2, ensure_ascii=False)}")
        if data:
            print(f"请求体: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("=" * 40)

        try:
            if method.upper() == "POST":
                response = self.session.post(
                    url, params=auth_params, headers=headers, json=data
                )
            else:
                response = self.session.get(url, params=auth_params, headers=headers)

            # 打印响应信息（安全模式，避免敏感信息泄露）
            print("\n=== LiblibAI API 响应信息 ===")
            print(f"状态码: {response.status_code}")

            # 仅在调试模式下记录完整响应体
            debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
            if debug_mode:
                print(
                    f"响应体: {json.dumps(response.json(), indent=2, ensure_ascii=False)}"
                )
            else:
                # 生产模式下仅记录基本信息
                response_data = response.json()
                safe_info = {
                    "status": response_data.get("status", "unknown"),
                    "message": response_data.get("message", "no message"),
                    "data_keys": (
                        list(response_data.get("data", {}).keys())
                        if "data" in response_data
                        else []
                    ),
                }
                print(
                    f"响应摘要: {json.dumps(safe_info, indent=2, ensure_ascii=False)}"
                )
            print("=" * 40)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"\n❌ API请求失败: {str(e)}")
            raise Exception(f"API请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"\n❌ 响应解析失败: {str(e)}")
            raise Exception(f"响应解析失败: {str(e)}")

    async def generate_image(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """生成图像 - 统一接口实现"""
        try:
            # 使用F.1模型生成
            params = F1GenerationParams(
                prompt=request.prompt,
                width=request.width,
                height=request.height,
                steps=request.steps or 20,
                img_count=request.num_images,
                negative_prompt=request.negative_prompt or "",
                cfg_scale=request.guidance_scale or 3.5,
                seed=request.seed or -1,
            )

            # 生成图片
            result = self.f1_text_to_image(params)

            # 等待完成
            result = self.wait_for_completion(result.generate_uuid)

            if result.status == GenerateStatus.SUCCESS:
                image_urls = [
                    img.get("url", img.get("imageUrl", "")) for img in result.images
                ]
                return ImageGenerationResponse(
                    success=True,
                    images=image_urls,
                    message=result.message,
                    metadata={
                        "generate_uuid": result.generate_uuid,
                        "points_cost": result.points_cost,
                        "account_balance": result.account_balance,
                    },
                )
            else:
                return ImageGenerationResponse(
                    success=False,
                    images=[],
                    message=f"生成失败: {result.message}",
                    error=result.message,
                )

        except Exception as e:
            return self._create_error_response(f"LiblibAI生成失败: {str(e)}")

    async def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            # 简单的API调用测试服务可用性
            uri = "/api/generate/webui/status"
            data = {"generateUuid": "test"}
            self._make_request("POST", uri, data)
            # 即使返回错误，只要能连接到API就认为服务可用
            return True
        except Exception:
            return False

    async def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        # LiblibAI主要支持F.1模型和传统模型
        return [
            "F.1",  # F.1模型
            "SD1.5",  # Stable Diffusion 1.5
            "SDXL",  # Stable Diffusion XL
            "其他自定义模型",  # 其他支持的模型
        ]

    def f1_text_to_image(self, params: F1GenerationParams) -> GenerateResult:
        """F.1文生图（完整参数版本）"""
        uri = "/api/generate/webui/text2img"

        data = {
            "templateUuid": params.template_uuid,
            "generateParams": params.to_dict(),
        }

        response = self._make_request("POST", uri, data)

        if response.get("code") != 0:
            raise Exception(f"F.1文生图请求失败: {response.get('msg', '未知错误')}")

        return GenerateResult(
            generate_uuid=response["data"]["generateUuid"],
            status=GenerateStatus.PENDING,
            progress=0.0,
            message="F.1文生图任务已提交",
            points_cost=0,
            account_balance=0,
            images=[],
        )

    def create_f1_text_params(self, prompt: str, **kwargs) -> F1GenerationParams:
        """创建F.1文生图参数对象（使用配置默认值）"""
        return F1GenerationParams.from_config(prompt, self.app_config, **kwargs)

    def get_generate_status(self, generate_uuid: str) -> GenerateResult:
        """查询生图结果"""
        uri = "/api/generate/webui/status"
        data = {"generateUuid": generate_uuid}

        response = self._make_request("POST", uri, data)

        if response.get("code") != 0:
            raise Exception(f"查询生图状态失败: {response.get('msg', '未知错误')}")

        result_data = response["data"]

        return GenerateResult(
            generate_uuid=result_data["generateUuid"],
            status=GenerateStatus(result_data["generateStatus"]),
            progress=result_data.get("percentCompleted", 0.0),
            message=result_data.get("generateMsg", ""),
            points_cost=result_data.get("pointsCost", 0),
            account_balance=result_data.get("accountBalance", 0),
            images=result_data.get("images", []),
        )

    def wait_for_completion(
        self, generate_uuid: str, max_wait_time: int = 300, check_interval: int = 5
    ) -> GenerateResult:
        """等待生图完成"""
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            result = self.get_generate_status(generate_uuid)

            if result.status in [
                GenerateStatus.SUCCESS,
                GenerateStatus.FAILED,
                GenerateStatus.TIMEOUT,
            ]:
                return result

            time.sleep(check_interval)

        raise Exception(f"生图任务超时: {generate_uuid}")

    def batch_generate_from_json(
        self, json_file_path: str, output_dir: str, use_f1: bool = True, **kwargs
    ) -> List[str]:
        """从JSON文件批量生成图片"""
        # 读取JSON文件
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 处理不同的JSON格式
        if isinstance(data, dict) and "storyboards" in data:
            # 新的标准化格式
            prompts_data = data["storyboards"]
            print(f"检测到标准化格式，包含 {len(prompts_data)} 个故事板")
        elif isinstance(data, list):
            # 旧格式兼容
            prompts_data = data
            print(f"检测到旧格式，包含 {len(prompts_data)} 个条目")
        else:
            raise ValueError("不支持的JSON格式")

        # 确保输出目录存在
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # 批量生成图片
        for i, item in enumerate(tqdm(prompts_data, desc="生成图片")):
            try:
                # 支持多种字段名
                prompt = (
                    item.get("english_prompt")  # 新格式
                    or item.get("故事板提示词")  # 旧格式
                    or item.get("prompt")  # 通用格式
                    or item.get("text", "")  # 备用格式
                )

                if not prompt:
                    print(f"跳过第{i+1}项：没有找到提示词")
                    continue

                # 获取LoRA ID
                item.get("lora_id") or item.get("LoRA编号", "")
                scene_id = item.get("scene_id", str(i + 1))

                # 准备生成参数
                if use_f1:
                    params = self.create_f1_text_params(prompt, **kwargs)

                    # 添加LoRA网络支持
                    if "lora_networks" in kwargs:
                        params.additional_network = kwargs["lora_networks"]

                    # 生成图片
                    result = self.f1_text_to_image(params)
                    # 等待完成
                    result = self.wait_for_completion(result.generate_uuid)
                else:
                    # 使用传统模型
                    generate_uuid = self.text_to_image(
                        prompt=prompt,
                        img_count=kwargs.get("img_count", 1),
                        steps=kwargs.get("steps", 30),
                        **kwargs,
                    )
                    # 等待完成
                    result = self.wait_for_completion(generate_uuid)

                if result.status == GenerateStatus.SUCCESS and result.images:
                    # 保存图片
                    for j, image_info in enumerate(result.images):
                        image_url = image_info.get(
                            "url", image_info.get("imageUrl", "")
                        )
                        if image_url:
                            # 下载图片
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                # 生成文件名，使用scene_id
                                filename = f"scene_{scene_id}_{j+1}.png"
                                file_path = output_path / filename

                                # 保存图片
                                with open(file_path, "wb") as img_file:
                                    img_file.write(response.content)

                                generated_files.append(str(file_path))
                                print(f"已保存: {file_path}")
                            else:
                                print(f"下载图片失败: {image_url}")
                else:
                    print(f"第{i+1}项生成失败: {result.message}")

            except Exception as e:
                print(f"处理第{i+1}项时出错: {str(e)}")
                continue

        print(f"批量生成完成，共生成 {len(generated_files)} 张图片")
        return generated_files
