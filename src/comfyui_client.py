#!/usr/bin/env python3
"""
ComfyUI API客户端模块

提供与ComfyUI服务器通信的功能，包括：
- 工作流提交
- 任务状态查询
- 结果获取
- 文件下载
"""

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests
import websocket

from src.config import config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI API客户端"""

    def __init__(
        self,
        server_url: str = None,
        api_key: str = None,
        timeout: int = None,
        check_interval: int = None,
    ):
        self.server_url = server_url or config.comfyui_server_url
        self.api_key = api_key or config.comfyui_api_key
        self.timeout = timeout or config.comfyui_timeout
        self.check_interval = check_interval or config.comfyui_check_interval
        self.max_wait_time = config.comfyui_max_wait_time

        # API端点
        self.api_base = f"{self.server_url}/api"
        self.prompt_endpoint = f"{self.api_base}/prompt"
        self.history_endpoint = f"{self.api_base}/history"
        self.view_endpoint = f"{self.server_url}/view"

        # WebSocket连接
        self.ws_url = (
            f"ws://{self.server_url.replace('http://', '').replace('https://', '')}/ws"
        )
        self.ws = None
        self.ws_messages = []
        self.ws_lock = threading.Lock()
        self.ws_connected = False

        # 重试配置
        self.max_retries = 3
        self.retry_delay = 2  # 秒
        self.connection_timeout = 30  # WebSocket连接超时

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _connect_websocket(self, client_id: str) -> bool:
        """连接WebSocket，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                logger.info(f"尝试连接WebSocket (第{attempt + 1}次)...")
                ws_url = f"{self.ws_url}?clientId={client_id}"

                self.ws_connected = False
                self.ws = websocket.WebSocketApp(
                    ws_url,
                    on_open=self._on_ws_open,
                    on_message=self._on_ws_message,
                    on_error=self._on_ws_error,
                    on_close=self._on_ws_close,
                )

                # 在新线程中运行WebSocket
                ws_thread = threading.Thread(target=self.ws.run_forever)
                ws_thread.daemon = True
                ws_thread.start()

                # 等待连接建立，带超时
                start_time = time.time()
                while (
                    not self.ws_connected
                    and (time.time() - start_time) < self.connection_timeout
                ):
                    time.sleep(0.1)

                if self.ws_connected:
                    logger.info("WebSocket连接成功")
                    return True
                else:
                    logger.warning(f"WebSocket连接超时 (第{attempt + 1}次尝试)")

            except Exception as e:
                logger.error(f"WebSocket连接失败 (第{attempt + 1}次尝试): {e}")

            if attempt < self.max_retries - 1:
                logger.info(f"等待{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)

        logger.error("WebSocket连接失败，已达到最大重试次数")
        return False

    def _on_ws_open(self, ws):
        """WebSocket连接打开"""
        self.ws_connected = True
        logger.info("WebSocket连接已建立")

    def _on_ws_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            with self.ws_lock:
                parsed_message = json.loads(message)
                self.ws_messages.append(parsed_message)
                logger.debug(
                    f"收到WebSocket消息: {parsed_message.get('type', 'unknown')}"
                )
        except json.JSONDecodeError as e:
            logger.error(f"解析WebSocket消息失败: {e}")

    def _on_ws_error(self, ws, error):
        """处理WebSocket错误"""
        self.ws_connected = False
        logger.error(f"WebSocket错误: {error}")

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭"""
        self.ws_connected = False
        logger.warning(f"WebSocket连接关闭: {close_status_code} - {close_msg}")

    def _disconnect_websocket(self):
        """断开WebSocket连接"""
        if self.ws:
            try:
                self.ws.close()
                logger.info("WebSocket连接已断开")
            except Exception as e:
                logger.error(f"断开WebSocket连接时出错: {e}")
            finally:
                self.ws = None
                self.ws_connected = False

    def _make_request_with_retry(
        self, method: str, url: str, **kwargs
    ) -> requests.Response:
        """带重试机制的HTTP请求"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"发送{method}请求到{url} (第{attempt + 1}次)")
                response = requests.request(method, url, timeout=self.timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.ConnectionError as e:
                logger.error(f"连接错误 (第{attempt + 1}次尝试): {e}")
            except requests.exceptions.Timeout as e:
                logger.error(f"请求超时 (第{attempt + 1}次尝试): {e}")
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP错误 (第{attempt + 1}次尝试): {e}")
                if response.status_code < 500:  # 客户端错误，不重试
                    raise
            except Exception as e:
                logger.error(f"请求失败 (第{attempt + 1}次尝试): {e}")

            if attempt < self.max_retries - 1:
                logger.info(f"等待{self.retry_delay}秒后重试...")
                time.sleep(self.retry_delay)

        raise Exception(f"HTTP请求失败，已达到最大重试次数: {url}")

    def upload_image(self, image_path: Path) -> Optional[str]:
        """上传图片到ComfyUI"""
        try:
            url = urljoin(self.server_url, "/upload/image")

            with open(image_path, "rb") as f:
                files = {"image": (image_path.name, f, "image/png")}
                headers = self._get_headers()
                # 移除Content-Type header让requests自动设置multipart/form-data
                if "Content-Type" in headers:
                    del headers["Content-Type"]

                response = self._make_request_with_retry(
                    "POST", url, files=files, headers=headers
                )

                result = response.json()
                logger.info(f"图片上传成功: {image_path.name}")
                return result.get("name", image_path.name)

        except requests.exceptions.RequestException as e:
            logger.error(f"上传图片时网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"上传图片时发生错误: {e}")
            return None

    def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """加载工作流文件"""
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
            return workflow
        except Exception as e:
            raise Exception(f"加载工作流文件失败: {e}")

    def update_workflow_params(
        self,
        workflow: Dict[str, Any],
        image_path: str,
        prompt: str,
        negative_prompt: str = "",
    ) -> Dict[str, Any]:
        """更新工作流参数，修复数据类型问题"""
        try:
            updated_workflow = workflow.copy()

            # 更新图像路径
            for node_id, node in updated_workflow.items():
                if node.get("class_type") == "LoadImage":
                    node["inputs"]["image"] = image_path
                    logger.debug(f"更新LoadImage节点图像路径: {image_path}")
                    break

            # 更新提示词和修复数据类型
            for node_id, node in updated_workflow.items():
                if node.get("class_type") == "KlingImage2VideoNode":
                    inputs = node["inputs"]

                    # 更新提示词
                    if prompt:
                        inputs["prompt"] = prompt
                        logger.debug(f"更新prompt: {prompt[:50]}...")
                    if negative_prompt:
                        inputs["negative_prompt"] = negative_prompt
                        logger.debug(f"更新negative_prompt: {negative_prompt[:50]}...")

                    # API密钥通过extra_data传递，不需要在节点inputs中添加
                    # 根据ComfyUI官方文档，API密钥应在submit_workflow的extra_data中传递

                    # 修复数据类型问题，解决Pydantic序列化警告
                    if "aspect_ratio" in inputs and isinstance(
                        inputs["aspect_ratio"], str
                    ):
                        # 确保aspect_ratio是正确的枚举值
                        valid_ratios = ["1:1", "4:3", "3:4", "16:9", "9:16"]
                        if inputs["aspect_ratio"] in valid_ratios:
                            logger.debug(
                                f"aspect_ratio类型正确: {inputs['aspect_ratio']}"
                            )
                        else:
                            logger.warning(
                                f"无效的aspect_ratio值: {inputs['aspect_ratio']}，使用默认值16:9"
                            )
                            inputs["aspect_ratio"] = "16:9"

                    # 确保其他数值字段的类型正确
                    if "cfg_scale" in inputs:
                        inputs["cfg_scale"] = float(inputs["cfg_scale"])
                    if "duration" in inputs:
                        inputs["duration"] = str(
                            inputs["duration"]
                        )  # 确保duration是字符串

                    logger.debug("更新KlingImage2VideoNode节点参数")
                    break

            # 兼容旧版本的节点ID方式
            if "40" in updated_workflow and "inputs" in updated_workflow["40"]:
                updated_workflow["40"]["inputs"]["image"] = image_path

            if "43" in updated_workflow and "inputs" in updated_workflow["43"]:
                updated_workflow["43"]["inputs"]["prompt"] = prompt
                if negative_prompt:
                    updated_workflow["43"]["inputs"][
                        "negative_prompt"
                    ] = negative_prompt

            return updated_workflow

        except Exception as e:
            raise Exception(f"更新工作流参数失败: {e}")

    def submit_workflow(self, workflow: Dict[str, Any]) -> Tuple[str, str]:
        """提交工作流到ComfyUI，带重试机制

        Returns:
            Tuple[str, str]: (prompt_id, client_id)
        """
        client_id = None
        try:
            # 生成客户端ID
            client_id = str(uuid.uuid4())
            logger.info(f"生成客户端ID: {client_id}")

            # 连接WebSocket
            if not self._connect_websocket(client_id):
                raise Exception("WebSocket连接失败")

            # 提交工作流，根据ComfyUI官方文档，API密钥应在extra_data中传递
            payload = {
                "prompt": workflow,
                "client_id": client_id,
                "extra_data": {"api_key_comfy_org": self.api_key},
            }

            logger.info("提交工作流到ComfyUI服务器...")
            logger.debug("API密钥已添加到extra_data中")

            # 不再在headers中传递API密钥，使用基本headers
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "ComfyUI-Client/1.0",
            }

            response = self._make_request_with_retry(
                "POST", self.prompt_endpoint, json=payload, headers=headers
            )

            result = response.json()
            prompt_id = result.get("prompt_id")

            if not prompt_id:
                raise Exception("未获取到prompt_id")

            logger.info(f"工作流提交成功，prompt_id: {prompt_id}")
            return prompt_id, client_id

        except Exception as e:
            logger.error(f"提交工作流失败: {e}")
            if client_id:
                self._disconnect_websocket()
            raise Exception(f"提交工作流失败: {e}")

    def wait_for_completion(self, prompt_id: str, client_id: str) -> Dict[str, Any]:
        """等待任务完成，带改进的错误处理

        Returns:
            Dict[str, Any]: 任务结果
        """
        start_time = time.time()
        logger.info(
            f"开始等待任务完成，prompt_id: {prompt_id}，最大等待时间: {self.max_wait_time}秒"
        )

        try:
            while time.time() - start_time < self.max_wait_time:
                # 检查WebSocket消息
                with self.ws_lock:
                    for message in self.ws_messages:
                        if (
                            message.get("type") == "executed"
                            and message.get("data", {}).get("prompt_id") == prompt_id
                        ):
                            logger.info("通过WebSocket接收到任务完成消息")
                            return self._get_task_result(prompt_id)
                        elif message.get("type") == "execution_error":
                            error_data = message.get("data", {})
                            if error_data.get("prompt_id") == prompt_id:
                                error_msg = f"任务执行失败: {error_data}"
                                logger.error(error_msg)
                                raise Exception(error_msg)

                # 通过API检查任务状态
                try:
                    history_response = self._make_request_with_retry(
                        "GET",
                        f"{self.history_endpoint}/{prompt_id}",
                        headers=self._get_headers(),
                    )

                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        if prompt_id in history_data:
                            logger.info("通过API轮询获取到任务结果")
                            return history_data[prompt_id]

                except Exception as e:
                    logger.warning(f"API轮询检查状态失败: {e}")

                elapsed_time = time.time() - start_time
                logger.debug(f"任务进行中，已等待 {elapsed_time:.1f}秒")
                time.sleep(self.check_interval)

            error_msg = f"任务超时，超过最大等待时间 {self.max_wait_time} 秒"
            logger.error(error_msg)
            raise Exception(error_msg)

        finally:
            self._disconnect_websocket()

    def _get_task_result(self, prompt_id: str) -> Dict[str, Any]:
        """获取任务结果，带重试机制"""
        try:
            logger.debug(f"获取任务结果，prompt_id: {prompt_id}")
            response = self._make_request_with_retry(
                "GET",
                f"{self.history_endpoint}/{prompt_id}",
                headers=self._get_headers(),
            )

            result = response.json()
            if prompt_id not in result:
                raise Exception("任务结果不存在")

            logger.info("成功获取任务结果")
            return result[prompt_id]

        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            raise Exception(f"获取任务结果失败: {e}")

    def download_video(self, task_result: Dict[str, Any], output_path: Path) -> bool:
        """下载生成的视频，带重试机制和改进的错误处理

        Args:
            task_result: 任务结果
            output_path: 输出路径

        Returns:
            bool: 是否下载成功
        """
        try:
            logger.info(f"开始下载视频到: {output_path}")

            # 从任务结果中提取视频文件信息
            outputs = task_result.get("outputs", {})
            logger.debug(f"任务输出节点数量: {len(outputs)}")

            # 查找保存视频的节点输出
            video_info = None
            for node_id, node_output in outputs.items():
                logger.debug(f"检查节点 {node_id} 的输出")

                if "videos" in node_output:
                    videos = node_output["videos"]
                    logger.debug(f"找到 {len(videos)} 个视频文件")

                    if videos and len(videos) > 0:
                        video_info = videos[0]
                        logger.debug(f"视频信息: {video_info}")
                        break

            if not video_info:
                error_msg = "未找到视频文件信息"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 构建下载URL
            filename = video_info["filename"]
            subfolder = video_info.get("subfolder", "")

            if subfolder:
                download_url = f"{self.view_endpoint}?filename={filename}&subfolder={subfolder}&type=output"
            else:
                download_url = f"{self.view_endpoint}?filename={filename}&type=output"

            logger.info(f"正在下载视频: {filename}")
            logger.info(f"下载URL: {download_url}")

            # 下载文件，使用重试机制
            response = self._make_request_with_retry(
                "GET",
                download_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                stream=True,  # 流式下载大文件
            )

            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 验证文件是否成功保存
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(
                    f"视频已成功保存到: {output_path}，文件大小: {output_path.stat().st_size} 字节"
                )
                return True
            else:
                raise Exception("视频文件保存失败或文件为空")

        except Exception as e:
            logger.error(f"下载视频失败: {e}")
            return False

    def generate_video(
        self, image_path: str, prompt: str, output_path: Path, negative_prompt: str = ""
    ) -> bool:
        """生成视频的完整流程，带完整的错误处理

        Args:
            image_path: 输入图像路径
            prompt: 提示词
            output_path: 输出视频路径
            negative_prompt: 负面提示词

        Returns:
            bool: 是否生成成功
        """
        client_id = None
        try:
            logger.info("开始生成视频流程")
            logger.info(f"输入图片: {image_path}")
            logger.info(
                f"提示词: {prompt[:100]}..."
                if len(prompt) > 100
                else f"提示词: {prompt}"
            )
            logger.info(f"输出路径: {output_path}")

            # 验证输入文件
            if not Path(image_path).exists():
                error_msg = f"输入图片文件不存在: {image_path}"
                logger.error(error_msg)
                raise Exception(error_msg)

            # 上传图片到ComfyUI
            logger.info("上传图片到ComfyUI...")
            uploaded_filename = self.upload_image(Path(image_path))
            if not uploaded_filename:
                error_msg = f"图片上传失败: {image_path}"
                logger.error(error_msg)
                raise Exception(error_msg)
            logger.info(f"图片上传成功，文件名: {uploaded_filename}")

            # 加载工作流
            logger.info("加载工作流配置...")
            workflow = self.load_workflow(config.comfyui_workflow_file)

            # 更新工作流参数（使用上传后的文件名）
            logger.info("更新工作流参数...")
            workflow = self.update_workflow_params(
                workflow, uploaded_filename, prompt, negative_prompt
            )

            # 提交工作流
            logger.info("提交工作流...")
            prompt_id, client_id = self.submit_workflow(workflow)
            logger.info(
                f"工作流提交成功，prompt_id: {prompt_id}, client_id: {client_id}"
            )

            # 等待完成
            logger.info("等待任务完成...")
            task_result = self.wait_for_completion(prompt_id, client_id)
            logger.info(f"任务完成，结果节点数: {len(task_result.get('outputs', {}))}")

            # 下载视频
            logger.info("下载生成的视频...")
            success = self.download_video(task_result, output_path)

            if success:
                logger.info("✅ 视频生成流程完成")
                return True
            else:
                error_msg = "❌ 视频下载失败"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            error_msg = f"生成视频失败: {str(e)}"
            logger.error(error_msg)
            # 重新抛出异常，让调用方能够获得详细错误信息
            raise Exception(error_msg)
        finally:
            # 确保WebSocket连接被关闭
            if client_id:
                logger.info("清理WebSocket连接...")
                self._disconnect_websocket()
