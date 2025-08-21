#!/usr/bin/env python3
"""
图像生成服务管理器

这个模块负责管理不同的图像生成服务（Stable Diffusion和LiblibAI），
根据配置选择合适的服务，并提供统一的接口。

支持的功能：
1. 服务选择和切换
2. 回退机制
3. 统一的生成接口
4. 错误处理和重试
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.liblib_service import LiblibService, LiblibConfig, F1GenerationParams


class ImageService(Enum):
    """图像生成服务枚举"""
    STABLE_DIFFUSION = "stable_diffusion"
    LIBLIB = "liblib"
    LIBLIB_F1 = "liblib_f1"


@dataclass
class GenerationResult:
    """图像生成结果"""
    success: bool
    images: List[str]  # 图片文件路径列表
    service_used: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ImageServiceManager:
    """图像生成服务管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 初始化服务
        self.liblib_service = None
        self._init_liblib_service()
        
        # 获取配置
        self.primary_service = config.image_generation_service
        self.service_priority = config.image_service_priority
        self.fallback_enabled = config.image_service_fallback_enabled
        
        self.logger.info(f"图像服务管理器初始化完成，主服务: {self.primary_service}")
    
    def _setup_logging(self):
        """设置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _init_liblib_service(self):
        """初始化LiblibAI服务"""
        try:
            if config.liblib_access_key and config.liblib_secret_key:
                liblib_config = LiblibConfig(
                    access_key=config.liblib_access_key,
                    secret_key=config.liblib_secret_key,
                    base_url=config.liblib_base_url,
                    timeout=config.liblib_timeout,
                    max_retries=config.liblib_max_retries,
                    retry_delay=config.liblib_retry_delay,
                    max_wait_time=config.liblib_max_wait_time,
                    check_interval=config.liblib_check_interval
                )
                self.liblib_service = LiblibService(liblib_config)
                self.logger.info("LiblibAI服务初始化成功")
            else:
                self.logger.warning("LiblibAI API密钥未配置，服务不可用")
        except Exception as e:
            self.logger.error(f"初始化LiblibAI服务失败: {e}")
    
    def is_service_available(self, service: ImageService) -> bool:
        """检查服务是否可用"""
        if service == ImageService.STABLE_DIFFUSION:
            return self._check_sd_availability()
        elif service in [ImageService.LIBLIB, ImageService.LIBLIB_F1]:
            return self.liblib_service is not None
        return False
    
    def _check_sd_availability(self) -> bool:
        """检查Stable Diffusion服务可用性"""
        try:
            import requests
            url = config.sd_api_url
            if not url.endswith('/'):
                url += '/'
            response = requests.get(f"{url}sdapi/v1/options", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def get_available_services(self) -> List[ImageService]:
        """获取可用的服务列表"""
        available = []
        for service in ImageService:
            if self.is_service_available(service):
                available.append(service)
        return available
    
    def select_service(self, preferred_service: Optional[str] = None) -> ImageService:
        """选择要使用的服务"""
        # 如果指定了首选服务，优先使用
        if preferred_service:
            try:
                service = ImageService(preferred_service)
                if self.is_service_available(service):
                    return service
            except ValueError:
                pass
        
        # 根据配置的优先级选择
        if self.service_priority == "liblib_first":
            priority_order = [ImageService.LIBLIB_F1, ImageService.LIBLIB, ImageService.STABLE_DIFFUSION]
        else:  # stable_diffusion_first
            priority_order = [ImageService.STABLE_DIFFUSION, ImageService.LIBLIB_F1, ImageService.LIBLIB]
        
        # 按优先级查找可用服务
        for service in priority_order:
            if self.is_service_available(service):
                return service
        
        raise RuntimeError("没有可用的图像生成服务")
    
    def generate_from_json(self, json_file: Path, output_dir: Path, preferred_service: Optional[str] = None) -> GenerationResult:
        """从JSON文件生成图片"""
        try:
            # 选择服务
            service = self.select_service(preferred_service)
            self.logger.info(f"使用服务: {service.value}")
            
            # 读取JSON文件
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            prompts = []
            if isinstance(data, list):
                prompts = data
            elif isinstance(data, dict) and 'prompts' in data:
                prompts = data['prompts']
            else:
                return GenerationResult(
                    success=False,
                    images=[],
                    service_used=service.value,
                    error_message="JSON文件格式不正确"
                )
            
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 根据服务类型生成图片
            if service == ImageService.STABLE_DIFFUSION:
                return self._generate_with_sd(prompts, output_dir)
            elif service == ImageService.LIBLIB_F1:
                return self._generate_with_liblib_f1(prompts, output_dir)
            elif service == ImageService.LIBLIB:
                return self._generate_with_liblib(prompts, output_dir)
            else:
                return GenerationResult(
                    success=False,
                    images=[],
                    service_used=service.value,
                    error_message=f"不支持的服务: {service.value}"
                )
        
        except Exception as e:
            self.logger.error(f"生成图片时出错: {e}")
            
            # 如果启用了回退机制，尝试其他服务
            if self.fallback_enabled and preferred_service:
                self.logger.info("尝试使用回退服务...")
                return self.generate_from_json(json_file, output_dir, None)
            
            return GenerationResult(
                success=False,
                images=[],
                service_used="unknown",
                error_message=str(e)
            )
    
    def _generate_with_sd(self, prompts: List[Dict], output_dir: Path) -> GenerationResult:
        """使用Stable Diffusion生成图片"""
        try:
            # 导入SD模块
            from . import image_generator
            
            self.logger.info("使用Stable Diffusion服务生成图片")
            
            # 调用原有的SD生成逻辑
            success = image_generator.main()
            
            if success:
                # 获取生成的图片文件
                image_files = []
                if output_dir.exists():
                    for file in output_dir.glob("*.png"):
                        image_files.append(str(file))
                
                return GenerationResult(
                    success=True,
                    images=image_files,
                    service_used="stable_diffusion",
                    metadata={"total_generated": len(image_files)}
                )
            else:
                return GenerationResult(
                    success=False,
                    images=[],
                    service_used="stable_diffusion",
                    error_message="Stable Diffusion生成失败"
                )
        
        except Exception as e:
            return GenerationResult(
                success=False,
                images=[],
                service_used="stable_diffusion",
                error_message=f"Stable Diffusion错误: {str(e)}"
            )
    
    def _generate_with_liblib_f1(self, prompts: List[Dict], output_dir: Path) -> GenerationResult:
        """使用LiblibAI F.1模型生成图片"""
        try:
            self.logger.info("使用LiblibAI F.1服务生成图片")
            
            image_files = []
            success_count = 0
            
            for i, prompt_data in enumerate(prompts):
                if isinstance(prompt_data, str):
                    prompt = prompt_data
                    params = {}
                elif isinstance(prompt_data, dict):
                    prompt = prompt_data.get('prompt', '')
                    params = {k: v for k, v in prompt_data.items() if k != 'prompt'}
                else:
                    continue
                
                try:
                    # 创建F.1参数
                    f1_params = F1GenerationParams(
                        prompt=prompt,
                        width=params.get('width', config.f1_default_width),
                        height=params.get('height', config.f1_default_height),
                        steps=params.get('steps', config.f1_default_steps),
                        img_count=params.get('img_count', config.f1_default_img_count),
                        restore_faces=params.get('restore_faces', config.f1_default_restore_faces),
                        seed=params.get('seed', config.f1_default_seed)
                    )
                    
                    # 生成图片
                    result = self.liblib_service.f1_text_to_image(f1_params)
                    
                    if result and result.images:
                        for j, image_url in enumerate(result.images):
                            filename = f"liblib_f1_{result.task_id}_{i+1}_{j+1}.png"
                            filepath = output_dir / filename
                            
                            # 下载并保存图片
                            import requests
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                                image_files.append(str(filepath))
                                success_count += 1
                
                except Exception as e:
                    self.logger.error(f"生成第{i+1}张图片失败: {e}")
                    continue
            
            return GenerationResult(
                success=success_count > 0,
                images=image_files,
                service_used="liblib_f1",
                metadata={
                    "total_generated": success_count,
                    "total_requested": len(prompts)
                }
            )
        
        except Exception as e:
            return GenerationResult(
                success=False,
                images=[],
                service_used="liblib_f1",
                error_message=f"LiblibAI F.1错误: {str(e)}"
            )
    
    def _generate_with_liblib(self, prompts: List[Dict], output_dir: Path) -> GenerationResult:
        """使用LiblibAI传统模型生成图片"""
        try:
            self.logger.info("使用LiblibAI传统服务生成图片")
            
            image_files = []
            success_count = 0
            
            for i, prompt_data in enumerate(prompts):
                if isinstance(prompt_data, str):
                    prompt = prompt_data
                    params = {}
                elif isinstance(prompt_data, dict):
                    prompt = prompt_data.get('prompt', '')
                    params = {k: v for k, v in prompt_data.items() if k != 'prompt'}
                else:
                    continue
                
                try:
                    # 生成图片
                    result = self.liblib_service.text_to_image(
                        prompt=prompt,
                        width=params.get('width', 512),
                        height=params.get('height', 512),
                        steps=params.get('steps', config.liblib_default_steps)
                    )
                    
                    if result and result.images:
                        for j, image_url in enumerate(result.images):
                            filename = f"liblib_{result.task_id}_{i+1}_{j+1}.png"
                            filepath = output_dir / filename
                            
                            # 下载并保存图片
                            import requests
                            response = requests.get(image_url)
                            if response.status_code == 200:
                                with open(filepath, 'wb') as f:
                                    f.write(response.content)
                                image_files.append(str(filepath))
                                success_count += 1
                
                except Exception as e:
                    self.logger.error(f"生成第{i+1}张图片失败: {e}")
                    continue
            
            return GenerationResult(
                success=success_count > 0,
                images=image_files,
                service_used="liblib",
                metadata={
                    "total_generated": success_count,
                    "total_requested": len(prompts)
                }
            )
        
        except Exception as e:
            return GenerationResult(
                success=False,
                images=[],
                service_used="liblib",
                error_message=f"LiblibAI错误: {str(e)}"
            )


def main():
    """主函数：图像服务管理器的命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="图像生成服务管理器")
    parser.add_argument('--json-file', type=Path, help='包含提示词的JSON文件路径')
    parser.add_argument('--output-dir', type=Path, help='输出目录路径')
    parser.add_argument('--service', choices=['stable_diffusion', 'liblib', 'liblib_f1'], help='指定使用的服务')
    parser.add_argument('--list-services', action='store_true', help='列出可用的服务')
    
    args = parser.parse_args()
    
    # 创建服务管理器
    manager = ImageServiceManager()
    
    if args.list_services:
        available = manager.get_available_services()
        print("可用的图像生成服务:")
        for service in available:
            print(f"  - {service.value}")
        return
    
    if not args.json_file or not args.output_dir:
        print("错误: 请指定JSON文件和输出目录")
        parser.print_help()
        return
    
    if not args.json_file.exists():
        print(f"错误: JSON文件不存在: {args.json_file}")
        return
    
    # 生成图片
    result = manager.generate_from_json(args.json_file, args.output_dir, args.service)
    
    if result.success:
        print(f"✅ 图片生成成功！使用服务: {result.service_used}")
        print(f"生成了 {len(result.images)} 张图片")
        if result.metadata:
            print(f"详细信息: {result.metadata}")
    else:
        print(f"❌ 图片生成失败: {result.error_message}")
        sys.exit(1)


if __name__ == '__main__':
    main()