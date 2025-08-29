#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stable Diffusion图像生成服务

这个模块提供了Stable Diffusion API的封装，实现了统一的图像服务接口。
支持文本到图像生成、批量生成、参数配置等功能。
"""

import base64
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from ...config import config
from ...models.image_models import (
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImageServiceType,
)
from .base import ImageServiceBase


@dataclass
class StableDiffusionConfig:
    """Stable Diffusion配置类"""

    api_url: str
    enable_hr: bool = True
    denoising_strength: float = 0.5
    firstphase_width: int = 960
    firstphase_height: int = 540
    hr_scale: int = 2
    hr_upscaler: str = "4x-UltraSharp"
    hr_second_pass_steps: int = 10
    hr_resize_x: int = 1920
    hr_resize_y: int = 1080
    seed: int = 333
    sampler_name: str = "DPM++ 2M Karras"
    batch_size: int = 1
    steps: int = 20
    cfg_scale: float = 7.5
    restore_faces: bool = False
    tiling: bool = False
    negative_prompt: str = (
        # TODO: 手动修复长行 -         "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    )
    style: str = ""
    adetailer_enabled: bool = True
    adetailer_face_model: str = "face_yolov8n.pt"
    adetailer_hand_model: str = "hand_yolov8n.pt"
    timeout: int = 300  # 5分钟超时


class StableDiffusionService(ImageServiceBase):
    """Stable Diffusion图像生成服务"""

    def __init__(self, sd_config: Optional[StableDiffusionConfig] = None):
        """初始化Stable Diffusion服务

        Args:
            sd_config: Stable Diffusion配置，如果为None则从全局配置加载
        """
        super().__init__()
        self.service_type = ImageServiceType.STABLE_DIFFUSION

        # 加载配置
        if sd_config:
            self.config = sd_config
        else:
            self.config = self._load_config_from_global()

        # 构建API URL
        self.api_url = self.config.api_url
        if not self.api_url.endswith("/"):
            self.api_url += "/"
        self.txt2img_url = self.api_url + "sdapi/v1/txt2img"

        self.logger.info(f"Stable Diffusion服务初始化完成，API URL: {self.api_url}")

    def _load_config_from_global(self) -> StableDiffusionConfig:
        """从全局配置加载Stable Diffusion配置"""
        return StableDiffusionConfig(
            api_url=config.sd_api_url,
            enable_hr=config.sd_enable_hr,
            denoising_strength=config.sd_denoising_strength,
            firstphase_width=config.sd_firstphase_width,
            firstphase_height=config.sd_firstphase_height,
            hr_scale=config.sd_hr_scale,
            hr_upscaler=config.sd_hr_upscaler,
            hr_second_pass_steps=config.sd_hr_second_pass_steps,
            hr_resize_x=config.sd_hr_resize_x,
            hr_resize_y=config.sd_hr_resize_y,
            seed=config.sd_seed,
            sampler_name=config.sd_sampler_name,
            batch_size=config.sd_batch_size,
            steps=config.sd_steps,
            cfg_scale=config.sd_cfg_scale,
            restore_faces=config.sd_restore_faces,
            tiling=config.sd_tiling,
            negative_prompt=config.sd_negative_prompt,
            style=config.sd_style,
            adetailer_enabled=config.sd_adetailer_enabled,
            adetailer_face_model=config.sd_adetailer_face_model,
            adetailer_hand_model=config.sd_adetailer_hand_model,
        )

    def generate_image(
        self, request: ImageGenerationRequest
    ) -> ImageGenerationResponse:
        """生成图像

        Args:
            request: 图像生成请求

        Returns:
            ImageGenerationResponse: 生成结果
        """
        try:
            # 验证请求
            validation_error = self._validate_request(request)
            if validation_error:
                return self._create_error_response(validation_error)

            # 构建API请求数据
            api_data = self._build_api_request(request)

            # 发送请求
            response = self._make_request(api_data)

            if response and response.status_code == 200:
                response_data = response.json()
                if "images" in response_data and response_data["images"]:
                    # 保存图像
                    image_data = response_data["images"][0]
                    filename = f"sd_generated_{int(time.time())}.png"

                    return ImageGenerationResponse(
                        success=True,
                        image_data=image_data,
                        filename=filename,
                        service=self.service_type.value,
                        params=api_data,
                        message="图像生成成功",
                    )
                else:
                    return self._create_error_response("API响应中没有图像数据")
            else:
                error_code = response.status_code if response else "连接失败"
                return self._create_error_response(f"API请求失败，错误码: {error_code}")

        except Exception as e:
            self.logger.error(f"Stable Diffusion图像生成失败: {str(e)}")
            return self._create_error_response(f"生成过程中发生错误: {str(e)}")

    def is_available(self) -> bool:
        """检查服务是否可用"""
        try:
            if not self.config.api_url or not self.config.api_url.startswith("http"):
                return False

            # 发送健康检查请求
            health_url = self.api_url + "sdapi/v1/options"
            response = requests.get(health_url, timeout=10)
            return response.status_code == 200

        except Exception as e:
            self.logger.warning(f"Stable Diffusion服务健康检查失败: {str(e)}")
            return False

    def _build_api_request(self, request: ImageGenerationRequest) -> Dict[str, Any]:
        """构建API请求数据

        Args:
            request: 图像生成请求

        Returns:
            Dict: API请求数据
        """
        # 构建完整提示词
        prompt_parts = ["masterpiece,(best quality)", request.prompt]

        # 添加LoRA参数
        if hasattr(request, "lora_params") and request.lora_params:
            prompt_parts.append(request.lora_params)

        # 添加风格参数
        if self.config.style:
            prompt_parts.append(self.config.style)

        prompt = ",".join(prompt_parts)

        # 构建基础请求数据
        api_data = {
            "prompt": prompt,
            "negative_prompt": request.negative_prompt or self.config.negative_prompt,
            "width": request.width or self.config.firstphase_width,
            "height": request.height or self.config.firstphase_height,
            "steps": request.steps or self.config.steps,
            "cfg_scale": request.cfg_scale or self.config.cfg_scale,
            "seed": request.seed or self.config.seed,
            "batch_size": request.batch_size or self.config.batch_size,
            "sampler_name": self.config.sampler_name,
            "restore_faces": self.config.restore_faces,
            "tiling": self.config.tiling,
            "enable_hr": self.config.enable_hr,
            "denoising_strength": self.config.denoising_strength,
            "hr_scale": self.config.hr_scale,
            "hr_upscaler": self.config.hr_upscaler,
            "hr_second_pass_steps": self.config.hr_second_pass_steps,
            "hr_resize_x": self.config.hr_resize_x,
            "hr_resize_y": self.config.hr_resize_y,
        }

        # 添加ADetailer配置
        if self.config.adetailer_enabled:
            api_data["alwayson_scripts"] = {
                "ADetailer": {
                    "args": [
                        {"ad_model": self.config.adetailer_face_model},
                        {"ad_model": self.config.adetailer_hand_model},
                    ]
                }
            }

        return api_data

    def _make_request(self, data: Dict[str, Any]) -> Optional[requests.Response]:
        """发送API请求

        Args:
            data: 请求数据

        Returns:
            requests.Response: 响应对象，失败时返回None
        """
        try:
            response = requests.post(
                self.txt2img_url,
                data=json.dumps(data),
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout,
            )
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Stable Diffusion API请求失败: {str(e)}")
            return None

    def save_image(self, image_data: str, output_path: Path) -> bool:
        """保存base64图像到文件

        Args:
            image_data: base64编码的图像数据
            output_path: 输出文件路径

        Returns:
            bool: 保存是否成功
        """
        try:
            with open(output_path, "wb") as file:
                file.write(base64.b64decode(image_data))
            return True
        except Exception as e:
            self.logger.error(f"保存图片失败 {output_path}: {str(e)}")
            return False

    def batch_generate_from_json(
        self, json_file_path: Path, output_dir: Path
    ) -> Dict[str, Any]:
        """从JSON文件批量生成图像

        Args:
            json_file_path: JSON文件路径
            output_dir: 输出目录

        Returns:
            Dict: 生成结果统计
        """
        try:
            # 读取JSON文件
            with open(json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 处理不同的JSON格式
            if isinstance(data, dict) and "storyboards" in data:
                data_list = data["storyboards"]
                self.logger.info(f"检测到标准化格式，包含 {len(data_list)} 个故事板")
            elif isinstance(data, list):
                data_list = data
                self.logger.info(f"检测到旧格式，包含 {len(data_list)} 个条目")
            else:
                raise ValueError("不支持的JSON格式")

            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            existing_files = set(os.listdir(output_dir))

            # 获取LoRA模型配置
            lora_models = getattr(config, "lora_models", {})

            success_count = 0
            total_count = len(data_list)

            for i, item in enumerate(data_list):
                if not isinstance(item, dict):
                    self.logger.warning(f"跳过非字典项: {item}")
                    continue

                # 提取提示词
                prompt = (
                    item.get("english_prompt", "")
                    or item.get("故事板提示词", "")
                    or item.get("processed_chinese", "")
                    or item.get("prompt", "")
                    or ""
                )

                if not prompt or not prompt.strip():
                    continue

                # 提取LoRA参数
                lora_id = item.get("lora_id", "") or item.get("LoRA编号", "") or ""
                lora_param_no = int(lora_id) if lora_id else 0
                lora_params = lora_models.get(lora_param_no, "")

                # 构建请求
                request = ImageGenerationRequest(prompt=prompt, lora_params=lora_params)

                # 检查文件是否已存在
                output_file = f"output_{i+1}.png"
                output_path = output_dir / output_file

                if output_file in existing_files:
                    success_count += 1
                    continue

                # 生成图像
                self.logger.info(f"生成图片 {i+1}/{total_count}: {prompt[:50]}...")
                response = self.generate_image(request)

                if response.success:
                    # 保存图像
                    if self.save_image(response.image_data, output_path):
                        existing_files.add(output_file)
                        success_count += 1
                        self.logger.info(f"图片 {i+1} 生成成功")
                    else:
                        self.logger.error(f"图片 {i+1} 保存失败")
                else:
                    self.logger.error(f"图片 {i+1} 生成失败: {response.message}")

            result = {
                "success_count": success_count,
                "total_count": total_count,
                "success_rate": success_count / total_count if total_count > 0 else 0,
            }

            self.logger.info(f"批量生成完成！成功: {success_count}/{total_count}")
            return result

        except Exception as e:
            self.logger.error(f"批量生成失败: {str(e)}")
            return {
                "success_count": 0,
                "total_count": 0,
                "success_rate": 0,
                "error": str(e),
            }

    def _create_error_response(self, error_message: str) -> ImageGenerationResponse:
        """创建错误响应

        Args:
            error_message: 错误信息

        Returns:
            ImageGenerationResponse: 错误响应
        """
        return ImageGenerationResponse(
            success=False, service=self.service_type.value, message=error_message
        )
