#!/usr/bin/env python3
"""
图生视频模块 - Image to Video Generator

使用ComfyUI API将图片转换为视频的核心模块。
支持批量处理图片，使用指定的工作流和提示词生成视频。

功能特性:
- 支持ComfyUI API调用
- 批量处理图片文件
- 支持多种提示词来源选择
- 自动下载和保存生成的视频
- 完整的错误处理和日志记录
"""

import json
import logging
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.comfyui_client import ComfyUIClient as ImprovedComfyUIClient
from src.config import config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LegacyComfyUIClient:
    """旧版ComfyUI客户端，保留用于兼容性"""

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def upload_image(self, image_path: Path) -> Optional[str]:
        """上传图片到ComfyUI"""
        try:
            url = urljoin(self.server_url, "/upload/image")

            with open(image_path, "rb") as f:
                files = {"image": (image_path.name, f, "image/png")}
                # 移除Content-Type header让requests自动设置multipart/form-data
                headers = (
                    {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
                )

                response = requests.post(url, files=files, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"图片上传成功: {image_path.name}")
                return result.get("name", image_path.name)

        except requests.exceptions.RequestException as e:
            logger.error(f"上传图片时网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"上传图片时发生错误: {e}")
            return None

    def queue_prompt(self, workflow: Dict) -> Optional[str]:
        """提交工作流到队列"""
        try:
            url = urljoin(self.server_url, "/prompt")

            # 根据官方文档，API密钥应该在extra_data中传递
            payload = {
                "prompt": workflow,
                "client_id": str(uuid.uuid4()),
                "extra_data": {"api_key_comfy_org": self.api_key},
            }

            # 添加调试日志
            logger.debug(f"发送请求到: {url}")
            logger.debug(f"请求payload keys: {list(payload.keys())}")
            logger.debug(f"工作流节点数量: {len(workflow)}")

            # 设置Content-Type头
            headers = {"Content-Type": "application/json"}

            response = requests.post(url, json=payload, headers=headers)

            # 记录响应状态和内容
            logger.debug(f"响应状态码: {response.status_code}")
            if response.status_code != 200:
                logger.error(f"响应内容: {response.text}")

            response.raise_for_status()

            result = response.json()
            prompt_id = result.get("prompt_id")

            if prompt_id:
                logger.info(f"工作流已提交，prompt_id: {prompt_id}")
                return prompt_id
            else:
                logger.error(f"提交工作流失败: {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"提交工作流时网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"提交工作流时发生错误: {e}")
            return None

    def check_status(self, prompt_id: str) -> Tuple[str, Optional[Dict]]:
        """检查任务状态

        Returns:
            Tuple[str, Optional[Dict]]: (状态, 结果数据)
            状态可能值: 'pending', 'running', 'completed', 'failed'
        """
        try:
            url = urljoin(self.server_url, f"/history/{prompt_id}")
            response = self.session.get(url)
            response.raise_for_status()

            history = response.json()

            if prompt_id not in history:
                return "pending", None

            task_data = history[prompt_id]
            status = task_data.get("status", {}).get("status_str", "unknown")

            if status == "success":
                # 检查是否有Kling API的视频URL在outputs中
                outputs = task_data.get("outputs", {})
                for node_id, node_output in outputs.items():
                    # 检查节点输出中是否包含video_url（Kling API响应）
                    if isinstance(node_output, dict) and "video_url" in node_output:
                        # 将video_url提升到顶层，方便extract_video_url方法处理
                        task_data["video_url"] = node_output["video_url"]
                        logger.info(
                            f"从节点{node_id}输出中发现Kling视频URL: {node_output['video_url']}"
                        )
                        break
                    # 检查是否有嵌套的结构包含video_url
                    elif isinstance(node_output, list) and len(node_output) > 0:
                        for item in node_output:
                            if isinstance(item, dict) and "video_url" in item:
                                task_data["video_url"] = item["video_url"]
                                logger.info(
                                    f"从节点{node_id}输出列表中发现Kling视频URL: {item['video_url']}"
                                )
                                break
                        if "video_url" in task_data:
                            break

                return "completed", task_data
            elif status == "error":
                # 提取错误信息
                error_info = {}
                if "status" in task_data and "messages" in task_data["status"]:
                    error_info["messages"] = task_data["status"]["messages"]
                if "outputs" in task_data:
                    error_info["outputs"] = task_data["outputs"]
                logger.error(f"ComfyUI任务执行失败: {error_info}")
                return "failed", error_info
            else:
                return "running", task_data

        except requests.exceptions.RequestException as e:
            logger.error(f"检查状态时网络错误: {e}")
            return "failed", None
        except Exception as e:
            logger.error(f"检查状态时发生错误: {e}")
            return "failed", None

    def download_video(self, video_url: str, save_path: Path) -> bool:
        """下载生成的视频"""
        try:
            # 如果是相对URL，转换为绝对URL
            if not video_url.startswith("http"):
                video_url = urljoin(self.server_url, video_url)

            response = self.session.get(video_url, stream=True)
            response.raise_for_status()

            # 确保保存目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"视频已保存到: {save_path}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"下载视频时网络错误: {e}")
            return False
        except Exception as e:
            logger.error(f"下载视频时发生错误: {e}")
            return False


class ImageToVideoGenerator:
    """图生视频生成器"""

    def __init__(self):
        # 使用config.py中的配置
        self.comfyui_server = config.comfyui_server_url
        self.comfyui_api_key = config.comfyui_api_key

        # 初始化ComfyUI客户端

        # 路径配置
        self.images_dir = Path(config.output_dir_image)
        self.video_clips_dir = Path(config.output_dir_video_clips)
        self.workflow_file = Path(config.comfyui_workflow_file)
        self.sd_prompt_file = Path(config.output_dir_txt) / "sd_prompt.json"
        self.flux_prompt_file = Path(config.output_dir_txt) / "Flux1_prompt.json"

        # 初始化改进的ComfyUI客户端
        self.client = ImprovedComfyUIClient(
            server_url=self.comfyui_server,
            api_key=self.comfyui_api_key,
            timeout=config.comfyui_timeout,
            check_interval=config.comfyui_check_interval,
        )

        # 保留旧客户端用于上传功能
        self.legacy_client = LegacyComfyUIClient(
            self.comfyui_server, self.comfyui_api_key
        )

        # 确保输出目录存在
        self.video_clips_dir.mkdir(parents=True, exist_ok=True)

    def load_workflow(self) -> Optional[Dict]:
        """加载ComfyUI工作流"""
        try:
            if not self.workflow_file.exists():
                logger.error(f"工作流文件不存在: {self.workflow_file}")
                return None

            with open(self.workflow_file, "r", encoding="utf-8") as f:
                workflow = json.load(f)

            logger.info(f"已加载工作流: {self.workflow_file}")
            return workflow

        except Exception as e:
            logger.error(f"加载工作流失败: {e}")
            return None

    def load_prompts(self, prompt_source: str = "sd") -> Optional[List[Dict]]:
        """加载提示词数据

        Args:
            prompt_source: 'sd' 或 'flux'
        """
        try:
            if prompt_source.lower() == "sd":
                prompt_file = self.sd_prompt_file
            elif prompt_source.lower() == "flux":
                prompt_file = self.flux_prompt_file
            else:
                logger.error(f"不支持的提示词源: {prompt_source}")
                return None

            if not prompt_file.exists():
                logger.error(f"提示词文件不存在: {prompt_file}")
                return None

            with open(prompt_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            storyboards = data.get("storyboards", [])
            logger.info(f"已加载 {len(storyboards)} 个提示词，来源: {prompt_source}")
            return storyboards

        except Exception as e:
            logger.error(f"加载提示词失败: {e}")
            return None

    def get_image_files(self) -> List[Path]:
        """获取按序号排序的图片文件列表"""
        try:
            if not self.images_dir.exists():
                logger.error(f"图片目录不存在: {self.images_dir}")
                return []

            # 支持的图片格式
            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".webp"}

            # 获取所有图片文件
            image_files = []
            for file_path in self.images_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)

            # 按文件名排序（假设文件名包含序号）
            image_files.sort(key=lambda x: x.name)

            logger.info(f"找到 {len(image_files)} 个图片文件")
            return image_files

        except Exception as e:
            logger.error(f"获取图片文件失败: {e}")
            return []

    def truncate_prompt(self, prompt: str, max_length: int = 500) -> str:
        """截断提示词到指定长度

        Args:
            prompt: 原始提示词
            max_length: 最大长度，默认500字符

        Returns:
            截断后的提示词
        """
        if len(prompt) <= max_length:
            return prompt

        # 在句号、逗号或空格处截断，避免截断单词
        truncated = prompt[:max_length]

        # 寻找最后一个合适的截断点
        for delimiter in [". ", ", ", " "]:
            last_pos = truncated.rfind(delimiter)
            if last_pos > max_length * 0.8:  # 至少保留80%的长度
                truncated = truncated[: last_pos + len(delimiter.rstrip())]
                break

        logger.warning(f"提示词过长，已截断: {len(prompt)} -> {len(truncated)} 字符")
        return truncated

    def update_workflow_for_image(
        self, workflow: Dict, image_path: Path, prompt: str
    ) -> Dict:
        """更新工作流中的图片路径和提示词"""
        try:
            # 深拷贝工作流
            import copy

            updated_workflow = copy.deepcopy(workflow)

            # 更新图片路径（节点40是LoadImage节点）
            # ComfyUI通常只接受文件名，图片需要在其input目录中
            if "40" in updated_workflow:
                updated_workflow["40"]["inputs"]["image"] = image_path.name

            # 更新提示词（节点43是KlingImage2VideoNode节点）
            if "43" in updated_workflow:
                # 截断过长的提示词
                truncated_prompt = self.truncate_prompt(prompt, max_length=500)
                updated_workflow["43"]["inputs"]["prompt"] = truncated_prompt
                # API密钥通过ComfyUIClient的extra_data传递，不需要在工作流节点中设置
                # 连接到LoadImage节点的输出，而不是直接使用文件名
                updated_workflow["43"]["inputs"]["start_frame"] = ["40", 0]

            return updated_workflow

        except Exception as e:
            logger.error(f"更新工作流失败: {e}")
            return workflow

    # 注意：wait_for_completion 和 extract_video_url 方法已移至改进的ComfyUI客户端中

    def process_single_image(
        self, image_path: Path, prompt: str, output_filename: str
    ) -> bool:
        """处理单个图片生成视频"""
        try:
            logger.info(f"开始处理图片: {image_path.name}")

            # 构建输出路径
            output_path = self.video_clips_dir / output_filename

            # 使用改进的客户端生成视频（包含图片上传）
            success = self.client.generate_video(
                image_path=str(image_path),
                prompt=prompt,
                negative_prompt="",  # 可以根据需要设置负面提示词
                output_path=output_path,
            )

            if success:
                logger.info(
                    f"图片 {image_path.name} 处理完成，视频保存为: {output_filename}"
                )
            else:
                logger.error(f"图片 {image_path.name} 处理失败")

            return success

        except Exception as e:
            logger.error(f"处理图片 {image_path.name} 时发生错误: {e}")
            return False

    def get_processing_status(self, prompt_source: str = "sd") -> Dict:
        """获取处理状态信息

        Args:
            prompt_source: 提示词来源，'sd' 或 'flux'

        Returns:
            包含状态信息的字典
        """
        try:
            # 获取图片文件数量
            image_files = self.get_image_files()
            image_count = len(image_files)

            # 获取视频文件数量
            video_files = list(self.video_clips_dir.glob("*.mp4"))
            video_count = len(video_files)

            # 检查提示词文件是否存在
            prompt_file = (
                self.sd_prompt_file if prompt_source == "sd" else self.flux_prompt_file
            )
            prompt_file_exists = prompt_file.exists()

            return {
                "image_count": image_count,
                "video_count": video_count,
                "prompt_file_exists": prompt_file_exists,
                "prompt_source": prompt_source,
            }

        except Exception as e:
            logger.error(f"获取处理状态失败: {e}")
            return {
                "image_count": 0,
                "video_count": 0,
                "prompt_file_exists": False,
                "prompt_source": prompt_source,
            }

    def generate_videos(
        self,
        prompt_source: str = "sd",
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
    ) -> bool:
        """批量生成视频

        Args:
            prompt_source: 提示词来源，'sd' 或 'flux'
            start_index: 开始处理的索引（从0开始）
            end_index: 结束处理的索引（不包含）
        """
        try:
            logger.info("开始批量图生视频处理...")

            # 加载提示词
            prompts = self.load_prompts(prompt_source)
            if not prompts:
                return False

            # 获取图片文件
            image_files = self.get_image_files()
            if not image_files:
                return False

            # 检查数量匹配
            if len(image_files) != len(prompts):
                logger.warning(
                    f"图片数量({len(image_files)})与提示词数量({len(prompts)})不匹配"
                )
                # 使用较小的数量
                min_count = min(len(image_files), len(prompts))
                image_files = image_files[:min_count]
                prompts = prompts[:min_count]

            # 应用索引范围
            if start_index is not None or end_index is not None:
                start = start_index if start_index is not None else 0
                end = end_index if end_index is not None else len(image_files)
                start = max(0, start)
                end = min(len(image_files), end)
                if start >= end:
                    logger.error(f"无效的索引范围: start={start}, end={end}")
                    return False
                image_files = image_files[start:end]
                prompts = prompts[start:end]
                logger.info(f"处理范围: {start} 到 {end-1} (共 {len(image_files)} 个)")

            # 批量处理
            success_count = 0
            total_count = len(image_files)

            for i, (image_path, prompt_data) in enumerate(zip(image_files, prompts)):
                try:
                    # 获取英文提示词
                    english_prompt = prompt_data.get("english_prompt", "")
                    if not english_prompt:
                        logger.warning(f"第 {i+1} 个提示词为空，跳过")
                        continue

                    # 生成输出文件名
                    scene_id = prompt_data.get("scene_id", i + 1)
                    if isinstance(scene_id, str):
                        try:
                            scene_id = int(scene_id)
                        except ValueError:
                            scene_id = i + 1
                    output_filename = f"video_{scene_id:03d}.mp4"

                    logger.info(f"处理进度: {i+1}/{total_count} - {image_path.name}")

                    # 处理单个图片
                    if self.process_single_image(
                        image_path, english_prompt, output_filename
                    ):
                        success_count += 1
                        logger.info(f"✓ 成功处理: {image_path.name}")
                    else:
                        logger.error(f"✗ 处理失败: {image_path.name}")

                    # 添加延迟，避免过于频繁的API调用
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"处理第 {i+1} 个图片时发生错误: {e}")
                    continue

            logger.info(f"批量处理完成: {success_count}/{total_count} 成功")
            return success_count > 0

        except Exception as e:
            logger.error(f"批量生成视频失败: {e}")
            return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="图生视频生成器")
    parser.add_argument(
        "--prompt-source",
        choices=["sd", "flux"],
        default="sd",
        help="提示词来源: sd (SD提示词) 或 flux (Flux提示词)",
    )
    parser.add_argument("--start", type=int, help="开始处理的图片索引")
    parser.add_argument("--end", type=int, help="结束处理的图片索引")
    parser.add_argument("--status", action="store_true", help="显示处理状态")

    args = parser.parse_args()

    try:
        print("=== 图生视频生成器 ===")
        print()

        # 创建生成器
        generator = ImageToVideoGenerator()

        # 如果请求显示状态
        if args.status:
            status = generator.get_processing_status(args.prompt_source)
            print(f"处理状态 ({args.prompt_source.upper()}):")
            print(f"  图片文件: {status['image_count']} 个")
            print(f"  视频文件: {status['video_count']} 个")
            print(
                f"  提示词文件: {'存在' if status['prompt_file_exists'] else '不存在'}"
            )
            return True

        print(f"使用提示词来源: {args.prompt_source.upper()}")
        print()

        # 开始生成
        print("开始图生视频处理...")
        success = generator.generate_videos(args.prompt_source, args.start, args.end)

        if success:
            print("\n✓ 图生视频处理完成！")
            print(f"生成的视频已保存到: {generator.video_clips_dir}")
        else:
            print("\n✗ 图生视频处理失败")

        return success

    except KeyboardInterrupt:
        print("\n用户中断操作")
        return False
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        print(f"\n程序执行出错: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
