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
import time
import uuid
import requests
import websocket
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urljoin

from src.config import config


class ComfyUIClient:
    """ComfyUI API客户端"""
    
    def __init__(self):
        self.server_url = config.comfyui_server_url
        self.api_key = config.comfyui_api_key
        self.timeout = config.comfyui_timeout
        self.check_interval = config.comfyui_check_interval
        self.max_wait_time = config.comfyui_max_wait_time
        
        # API端点
        self.api_base = f"{self.server_url}/api"
        self.prompt_endpoint = f"{self.api_base}/prompt"
        self.history_endpoint = f"{self.api_base}/history"
        self.view_endpoint = f"{self.server_url}/view"
        
        # WebSocket连接
        self.ws_url = f"ws://{self.server_url.replace('http://', '').replace('https://', '')}/ws"
        self.ws = None
        self.ws_messages = []
        self.ws_lock = threading.Lock()
        
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _connect_websocket(self, client_id: str) -> bool:
        """连接WebSocket"""
        try:
            ws_url_with_client = f"{self.ws_url}?clientId={client_id}"
            self.ws = websocket.WebSocketApp(
                ws_url_with_client,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )
            
            # 在后台线程中运行WebSocket
            ws_thread = threading.Thread(target=self.ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # 等待连接建立
            time.sleep(1)
            return True
            
        except Exception as e:
            print(f"WebSocket连接失败: {e}")
            return False
    
    def _on_ws_message(self, ws, message):
        """WebSocket消息处理"""
        try:
            data = json.loads(message)
            with self.ws_lock:
                self.ws_messages.append(data)
        except Exception as e:
            print(f"WebSocket消息解析失败: {e}")
    
    def _on_ws_error(self, ws, error):
        """WebSocket错误处理"""
        print(f"WebSocket错误: {error}")
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭处理"""
        print("WebSocket连接已关闭")
    
    def _disconnect_websocket(self):
        """断开WebSocket连接"""
        if self.ws:
            self.ws.close()
            self.ws = None
    
    def load_workflow(self, workflow_path: Path) -> Dict[str, Any]:
        """加载工作流文件"""
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            return workflow
        except Exception as e:
            raise Exception(f"加载工作流文件失败: {e}")
    
    def update_workflow_params(self, workflow: Dict[str, Any], 
                             image_path: str, prompt: str, 
                             negative_prompt: str = "") -> Dict[str, Any]:
        """更新工作流参数"""
        try:
            # 更新图像路径
            if "40" in workflow and "inputs" in workflow["40"]:
                workflow["40"]["inputs"]["image"] = image_path
            
            # 更新提示词
            if "43" in workflow and "inputs" in workflow["43"]:
                workflow["43"]["inputs"]["prompt"] = prompt
                if negative_prompt:
                    workflow["43"]["inputs"]["negative_prompt"] = negative_prompt
            
            return workflow
            
        except Exception as e:
            raise Exception(f"更新工作流参数失败: {e}")
    
    def submit_workflow(self, workflow: Dict[str, Any]) -> Tuple[str, str]:
        """提交工作流
        
        Returns:
            Tuple[str, str]: (prompt_id, client_id)
        """
        try:
            # 生成客户端ID
            client_id = str(uuid.uuid4())
            
            # 连接WebSocket
            if not self._connect_websocket(client_id):
                raise Exception("WebSocket连接失败")
            
            # 提交工作流
            payload = {
                "prompt": workflow,
                "client_id": client_id
            }
            
            response = requests.post(
                self.prompt_endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"提交工作流失败: {response.status_code} - {response.text}")
            
            result = response.json()
            prompt_id = result.get('prompt_id')
            
            if not prompt_id:
                raise Exception("未获取到prompt_id")
            
            print(f"工作流已提交，prompt_id: {prompt_id}")
            return prompt_id, client_id
            
        except Exception as e:
            self._disconnect_websocket()
            raise Exception(f"提交工作流失败: {e}")
    
    def wait_for_completion(self, prompt_id: str, client_id: str) -> Dict[str, Any]:
        """等待任务完成
        
        Returns:
            Dict[str, Any]: 任务结果
        """
        start_time = time.time()
        
        try:
            while time.time() - start_time < self.max_wait_time:
                # 检查WebSocket消息
                with self.ws_lock:
                    for message in self.ws_messages:
                        if message.get('type') == 'executed' and message.get('data', {}).get('prompt_id') == prompt_id:
                            print("任务执行完成")
                            return self._get_task_result(prompt_id)
                        elif message.get('type') == 'execution_error':
                            error_data = message.get('data', {})
                            if error_data.get('prompt_id') == prompt_id:
                                raise Exception(f"任务执行失败: {error_data}")
                
                # 通过API检查任务状态
                try:
                    history_response = requests.get(
                        f"{self.history_endpoint}/{prompt_id}",
                        headers=self._get_headers(),
                        timeout=self.timeout
                    )
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        if prompt_id in history_data:
                            print("任务完成")
                            return history_data[prompt_id]
                    
                except Exception as e:
                    print(f"检查任务状态失败: {e}")
                
                print(f"等待任务完成... ({int(time.time() - start_time)}s)")
                time.sleep(self.check_interval)
            
            raise Exception(f"任务超时 ({self.max_wait_time}秒)")
            
        finally:
            self._disconnect_websocket()
    
    def _get_task_result(self, prompt_id: str) -> Dict[str, Any]:
        """获取任务结果"""
        try:
            response = requests.get(
                f"{self.history_endpoint}/{prompt_id}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"获取任务结果失败: {response.status_code}")
            
            result = response.json()
            if prompt_id not in result:
                raise Exception("任务结果不存在")
            
            return result[prompt_id]
            
        except Exception as e:
            raise Exception(f"获取任务结果失败: {e}")
    
    def download_video(self, task_result: Dict[str, Any], output_path: Path) -> bool:
        """下载生成的视频
        
        Args:
            task_result: 任务结果
            output_path: 输出路径
            
        Returns:
            bool: 是否下载成功
        """
        try:
            # 从任务结果中提取视频文件信息
            outputs = task_result.get('outputs', {})
            
            # 查找保存视频的节点输出
            video_info = None
            for node_id, node_output in outputs.items():
                if 'videos' in node_output:
                    video_info = node_output['videos'][0]
                    break
            
            if not video_info:
                raise Exception("未找到视频文件信息")
            
            # 构建下载URL
            filename = video_info['filename']
            subfolder = video_info.get('subfolder', '')
            
            if subfolder:
                download_url = f"{self.view_endpoint}?filename={filename}&subfolder={subfolder}&type=output"
            else:
                download_url = f"{self.view_endpoint}?filename={filename}&type=output"
            
            print(f"正在下载视频: {filename}")
            
            # 下载文件
            response = requests.get(
                download_url,
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code != 200:
                raise Exception(f"下载失败: {response.status_code}")
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"视频已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"下载视频失败: {e}")
            return False
    
    def generate_video(self, image_path: str, prompt: str, 
                      output_path: Path, negative_prompt: str = "") -> bool:
        """生成视频的完整流程
        
        Args:
            image_path: 输入图像路径
            prompt: 提示词
            output_path: 输出视频路径
            negative_prompt: 负面提示词
            
        Returns:
            bool: 是否生成成功
        """
        try:
            print(f"开始生成视频: {image_path} -> {output_path}")
            
            # 加载工作流
            workflow = self.load_workflow(config.comfyui_workflow_file)
            
            # 更新工作流参数
            workflow = self.update_workflow_params(
                workflow, image_path, prompt, negative_prompt
            )
            
            # 提交工作流
            prompt_id, client_id = self.submit_workflow(workflow)
            
            # 等待完成
            task_result = self.wait_for_completion(prompt_id, client_id)
            
            # 下载视频
            return self.download_video(task_result, output_path)
            
        except Exception as e:
            print(f"生成视频失败: {e}")
            return False