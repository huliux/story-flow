import os
import json
import time
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from .liblib_service import LiblibService, LiblibConfig, GenerateStatus, GenerateResult
from ..config import config


@dataclass
class LiblibGenerationParams:
    """LiblibAI生图参数类"""
    prompt: str
    negative_prompt: str = ""
    aspect_ratio: str = "square"  # square, portrait, landscape
    width: Optional[int] = None
    height: Optional[int] = None
    img_count: int = 1
    steps: int = 30
    seed: int = -1
    style: str = ""
    lora_params: Optional[Dict[str, Any]] = None
    controlnet_params: Optional[Dict[str, Any]] = None


class LiblibGenerator:
    """LiblibAI图像生成器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """初始化LiblibAI服务"""
        if not config.liblib_access_key or not config.liblib_secret_key:
            self.logger.warning("LiblibAI API密钥未配置")
            self._service = None
            return
        
        try:
            liblib_config = LiblibConfig(
                access_key=config.liblib_access_key,
                secret_key=config.liblib_secret_key,
                base_url=config.liblib_base_url,
                timeout=config.liblib_timeout,
                max_retries=config.liblib_max_retries,
                retry_delay=config.liblib_retry_delay
            )
            
            self._service = LiblibService(liblib_config)
            self.logger.info("LiblibAI服务初始化成功")
            
        except Exception as e:
            self.logger.error(f"LiblibAI服务初始化失败: {str(e)}")
            self._service = None
    
    def is_available(self) -> bool:
        """检查LiblibAI服务是否可用"""
        return (
            config.liblib_enabled and 
            self._service is not None and 
            bool(config.liblib_access_key) and 
            bool(config.liblib_secret_key)
        )
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """带退避策略的重试机制"""
        max_retries = config.liblib_max_retries
        base_delay = config.liblib_retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    self.logger.error(f"重试{max_retries}次后仍然失败: {str(e)}")
                    raise
                
                delay = base_delay * (2 ** attempt)  # 指数退避
                self.logger.warning(f"第{attempt + 1}次尝试失败: {str(e)}, {delay}秒后重试")
                time.sleep(delay)
    
    def _convert_params(self, params: LiblibGenerationParams) -> Dict[str, Any]:
        """转换生图参数为LiblibAI格式"""
        liblib_params = {
            'prompt': params.prompt,
            'img_count': params.img_count,
            'steps': params.steps if params.steps > 0 else config.liblib_default_steps
        }
        
        # 处理图片尺寸
        if params.width and params.height:
            liblib_params['image_size'] = {
                'width': params.width,
                'height': params.height
            }
        else:
            liblib_params['aspect_ratio'] = params.aspect_ratio or config.liblib_default_aspect_ratio
        
        # 处理ControlNet参数
        if params.controlnet_params:
            liblib_params['controlnet'] = params.controlnet_params
        
        return liblib_params
    
    def _convert_sd_params_to_liblib(self, sd_params: Dict[str, Any]) -> LiblibGenerationParams:
        """将Stable Diffusion参数转换为LiblibAI参数格式"""
        # 从SD参数中提取并转换为LiblibAI格式
        prompt = sd_params.get('prompt', '')
        negative_prompt = sd_params.get('negative_prompt', '')
        width = sd_params.get('width')
        height = sd_params.get('height')
        steps = sd_params.get('steps', config.liblib_default_steps)
        seed = sd_params.get('seed', -1)
        img_count = sd_params.get('batch_size', 1)
        
        # 根据宽高比确定aspect_ratio
        aspect_ratio = 'square'
        if width and height:
            ratio = width / height
            if ratio > 1.2:
                aspect_ratio = 'landscape'
            elif ratio < 0.8:
                aspect_ratio = 'portrait'
        
        return LiblibGenerationParams(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            width=width,
            height=height,
            img_count=img_count,
            steps=steps,
            seed=seed
        )
    
    def generate_images(self, params: LiblibGenerationParams) -> List[Dict[str, Any]]:
        """生成图片
        
        Args:
            params: 生图参数
        
        Returns:
            生成的图片信息列表
        """
        if not self.is_available():
            raise RuntimeError("LiblibAI服务不可用")
        
        try:
            # 转换参数
            liblib_params = self._convert_params(params)
            
            # 提交生图任务
            self.logger.info(f"提交LiblibAI文生图任务: {params.prompt[:50]}...")
            generate_uuid = self._retry_with_backoff(
                self._service.text_to_image,
                params.prompt,
                **liblib_params
            )
            
            self.logger.info(f"生图任务已提交，UUID: {generate_uuid}")
            
            # 等待生图完成
            result = self._retry_with_backoff(
                self._service.wait_for_completion,
                generate_uuid,
                config.liblib_max_wait_time,
                config.liblib_check_interval
            )
            
            if result.status == GenerateStatus.SUCCESS:
                self.logger.info(f"生图成功，共生成{len(result.images)}张图片")
                return self._process_result(result, params)
            else:
                raise RuntimeError(f"生图失败: {result.message}")
                
        except Exception as e:
            self.logger.error(f"LiblibAI生图失败: {str(e)}")
            raise
    
    def _process_result(self, result: GenerateResult, params: LiblibGenerationParams) -> List[Dict[str, Any]]:
        """处理生图结果"""
        processed_images = []
        
        for i, image_info in enumerate(result.images):
            try:
                # 下载并保存图片
                image_data = self._download_image(image_info['imageUrl'])
                filename = self._save_image(image_data, i, params)
                
                processed_images.append({
                    'filename': filename,
                    'url': image_info['imageUrl'],
                    'seed': image_info.get('seed', -1),
                    'audit_status': image_info.get('auditStatus', 0),
                    'points_cost': result.points_cost,
                    'account_balance': result.account_balance
                })
                
            except Exception as e:
                self.logger.error(f"处理第{i+1}张图片失败: {str(e)}")
                continue
        
        return processed_images
    
    def _download_image(self, image_url: str) -> bytes:
        """下载图片"""
        import requests
        
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise RuntimeError(f"下载图片失败: {str(e)}")
    
    def _save_image(self, image_data: bytes, index: int, params: LiblibGenerationParams) -> str:
        """保存图片到本地"""
        try:
            # 生成文件名
            timestamp = int(time.time())
            safe_prompt = "".join(c for c in params.prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_prompt = safe_prompt.replace(' ', '_')
            filename = f"liblib_{timestamp}_{safe_prompt}_{index}.png"
            
            # 保存到输出目录
            output_path = config.output_dir_image / filename
            output_path.write_bytes(image_data)
            
            self.logger.info(f"图片已保存: {output_path}")
            return filename
            
        except Exception as e:
            raise RuntimeError(f"保存图片失败: {str(e)}")
    
    def save_generation_params(self, params: LiblibGenerationParams, images: List[Dict[str, Any]]) -> str:
        """保存生图参数"""
        try:
            timestamp = int(time.time())
            params_data = {
                'timestamp': timestamp,
                'service': 'liblib',
                'params': {
                    'prompt': params.prompt,
                    'negative_prompt': params.negative_prompt,
                    'aspect_ratio': params.aspect_ratio,
                    'width': params.width,
                    'height': params.height,
                    'img_count': params.img_count,
                    'steps': params.steps,
                    'seed': params.seed,
                    'style': params.style,
                    'lora_params': params.lora_params,
                    'controlnet_params': params.controlnet_params
                },
                'results': images
            }
            
            params_file = config.output_dir_image / f"liblib_params_{timestamp}.json"
            with open(params_file, 'w', encoding='utf-8') as f:
                json.dump(params_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"生图参数已保存: {params_file}")
            return str(params_file)
            
        except Exception as e:
            self.logger.error(f"保存生图参数失败: {str(e)}")
            return ""
    
    def generate_from_prompts_file(self, prompts_file: str) -> List[Dict[str, Any]]:
        """从提示词文件生成图片（兼容现有接口）"""
        try:
            # 读取提示词文件
            prompts_path = Path(prompts_file)
            if not prompts_path.exists():
                raise FileNotFoundError(f"提示词文件不存在: {prompts_file}")
            
            with open(prompts_path, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            all_results = []
            
            # 处理每个提示词
            for i, prompt_info in enumerate(prompts_data.get('prompts', [])):
                try:
                    params = LiblibGenerationParams(
                        prompt=prompt_info.get('prompt', ''),
                        negative_prompt=prompt_info.get('negative_prompt', ''),
                        aspect_ratio=prompt_info.get('aspect_ratio', 'square'),
                        img_count=prompt_info.get('img_count', 1),
                        steps=prompt_info.get('steps', config.liblib_default_steps),
                        seed=prompt_info.get('seed', -1),
                        style=prompt_info.get('style', ''),
                        lora_params=prompt_info.get('lora_params'),
                        controlnet_params=prompt_info.get('controlnet_params')
                    )
                    
                    # 生成图片
                    images = self.generate_images(params)
                    
                    # 保存参数
                    self.save_generation_params(params, images)
                    
                    all_results.extend(images)
                    
                    self.logger.info(f"完成第{i+1}/{len(prompts_data['prompts'])}个提示词的生图")
                    
                except Exception as e:
                    self.logger.error(f"处理第{i+1}个提示词失败: {str(e)}")
                    continue
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"从提示词文件生成图片失败: {str(e)}")
            raise


# 全局实例（延迟初始化）
liblib_generator = None

def get_liblib_generator():
    """获取LiblibGenerator实例（延迟初始化）"""
    global liblib_generator
    if liblib_generator is None:
        liblib_generator = LiblibGenerator()
    return liblib_generator


def main():
    """主函数，用于独立运行LiblibAI生图"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LiblibAI图像生成器')
    parser.add_argument('--prompt', type=str, help='生图提示词')
    parser.add_argument('--prompts-file', type=str, help='提示词文件路径')
    parser.add_argument('--aspect-ratio', type=str, default='square', 
                       choices=['square', 'portrait', 'landscape'], help='图片宽高比')
    parser.add_argument('--img-count', type=int, default=1, help='生图张数')
    parser.add_argument('--steps', type=int, default=30, help='采样步数')
    
    args = parser.parse_args()
    
    try:
        if args.prompts_file:
            # 从文件生成
            results = liblib_generator.generate_from_prompts_file(args.prompts_file)
            print(f"成功生成{len(results)}张图片")
        elif args.prompt:
            # 单个提示词生成
            params = LiblibGenerationParams(
                prompt=args.prompt,
                aspect_ratio=args.aspect_ratio,
                img_count=args.img_count,
                steps=args.steps
            )
            
            results = liblib_generator.generate_images(params)
            liblib_generator.save_generation_params(params, results)
            
            print(f"成功生成{len(results)}张图片")
            for result in results:
                print(f"  - {result['filename']}")
        else:
            print("请提供 --prompt 或 --prompts-file 参数")
            
    except Exception as e:
        print(f"生图失败: {str(e)}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())