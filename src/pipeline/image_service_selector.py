import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

from .liblib_generator import LiblibGenerator, LiblibGenerationParams
from ..config import config


class ImageService(Enum):
    """图像生成服务枚举"""
    LIBLIB = "liblib"
    STABLE_DIFFUSION = "stable_diffusion"


@dataclass
class ServiceStatus:
    """服务状态"""
    service: ImageService
    available: bool
    error_message: str = ""
    priority: int = 0


class ImageServiceSelector:
    """图像生成服务选择器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._liblib_generator = None
        self._sd_generator = None
        self._initialize_services()
    
    def _initialize_services(self):
        """初始化所有可用的图像生成服务"""
        # 初始化LiblibAI服务
        try:
            if config.liblib_enabled:
                from .liblib_generator import liblib_generator
                self._liblib_generator = liblib_generator
                self.logger.info("LiblibAI服务已初始化")
        except Exception as e:
            self.logger.warning(f"LiblibAI服务初始化失败: {str(e)}")
        
        # 初始化Stable Diffusion服务（延迟加载）
        self.logger.info("图像服务选择器初始化完成")
    
    def get_service_status(self) -> List[ServiceStatus]:
        """获取所有服务状态"""
        statuses = []
        
        # 检查LiblibAI服务
        if self._liblib_generator:
            try:
                available = self._liblib_generator.is_available()
                priority = 1 if config.liblib_priority else 2
                statuses.append(ServiceStatus(
                    service=ImageService.LIBLIB,
                    available=available,
                    priority=priority
                ))
            except Exception as e:
                statuses.append(ServiceStatus(
                    service=ImageService.LIBLIB,
                    available=False,
                    error_message=str(e),
                    priority=2
                ))
        
        # 检查Stable Diffusion服务
        try:
            sd_available = bool(config.sd_api_url)
            priority = 2 if config.liblib_priority else 1
            statuses.append(ServiceStatus(
                service=ImageService.STABLE_DIFFUSION,
                available=sd_available,
                priority=priority
            ))
        except Exception as e:
            statuses.append(ServiceStatus(
                service=ImageService.STABLE_DIFFUSION,
                available=False,
                error_message=str(e),
                priority=3
            ))
        
        # 按优先级排序
        statuses.sort(key=lambda x: (not x.available, x.priority))
        return statuses
    
    def select_best_service(self) -> Optional[ImageService]:
        """选择最佳可用服务"""
        statuses = self.get_service_status()
        
        for status in statuses:
            if status.available:
                self.logger.info(f"选择图像生成服务: {status.service.value}")
                return status.service
        
        self.logger.error("没有可用的图像生成服务")
        return None
    
    def list_available_services(self) -> List[str]:
        """获取可用服务列表"""
        statuses = self.get_service_status()
        return [status.service.value for status in statuses if status.available]
    
    def get_best_service(self) -> Optional[str]:
        """获取最佳服务名称"""
        service = self.select_best_service()
        return service.value if service else None
    
    def generate_images_with_fallback(self, prompt: str, **kwargs) -> List[Dict[str, Any]]:
        """使用回退机制生成图片
        
        Args:
            prompt: 生图提示词
            **kwargs: 其他生图参数
        
        Returns:
            生成的图片信息列表
        """
        statuses = self.get_service_status()
        last_error = None
        
        for status in statuses:
            if not status.available:
                continue
            
            try:
                self.logger.info(f"尝试使用{status.service.value}服务生成图片")
                
                if status.service == ImageService.LIBLIB:
                    return self._generate_with_liblib(prompt, **kwargs)
                elif status.service == ImageService.STABLE_DIFFUSION:
                    return self._generate_with_sd(prompt, **kwargs)
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"{status.service.value}服务生图失败: {str(e)}，尝试下一个服务")
                continue
        
        # 所有服务都失败
        error_msg = f"所有图像生成服务都不可用。最后错误: {str(last_error) if last_error else '未知错误'}"
        self.logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    def _generate_with_liblib(self, prompt: str, **kwargs) -> List[Dict[str, Any]]:
        """使用LiblibAI生成图片"""
        if not self._liblib_generator:
            raise RuntimeError("LiblibAI服务未初始化")
        
        # 转换参数格式
        params = LiblibGenerationParams(
            prompt=prompt,
            negative_prompt=kwargs.get('negative_prompt', ''),
            aspect_ratio=kwargs.get('aspect_ratio', config.liblib_default_aspect_ratio),
            width=kwargs.get('width'),
            height=kwargs.get('height'),
            img_count=kwargs.get('img_count', 1),
            steps=kwargs.get('steps', config.liblib_default_steps),
            seed=kwargs.get('seed', -1),
            style=kwargs.get('style', ''),
            lora_params=kwargs.get('lora_params'),
            controlnet_params=kwargs.get('controlnet_params')
        )
        
        images = self._liblib_generator.generate_images(params)
        self._liblib_generator.save_generation_params(params, images)
        
        return images
    
    def _generate_with_sd(self, prompt: str, **kwargs) -> List[Dict[str, Any]]:
        """使用Stable Diffusion生成图片"""
        # 延迟导入以避免循环依赖
        try:
            from . import image_generator
            
            # 调用原有的Stable Diffusion生成逻辑
            # 这里需要根据实际的image_generator接口进行调整
            self.logger.info("使用Stable Diffusion服务生成图片")
            
            # 构建SD参数（这里需要根据实际接口调整）
            sd_params = {
                'prompt': prompt,
                'negative_prompt': kwargs.get('negative_prompt', config.sd_negative_prompt),
                'width': kwargs.get('width', config.sd_firstphase_width),
                'height': kwargs.get('height', config.sd_firstphase_height),
                'batch_size': kwargs.get('img_count', config.sd_batch_size),
                'steps': kwargs.get('steps', config.sd_steps),
                'cfg_scale': kwargs.get('cfg_scale', config.sd_cfg_scale),
                'seed': kwargs.get('seed', config.sd_seed)
            }
            
            # 调用SD生成函数（需要根据实际接口调整）
            # 这里返回模拟结果，实际需要调用真实的SD接口
            return [{
                'filename': f'sd_generated_{int(time.time())}.png',
                'service': 'stable_diffusion',
                'params': sd_params
            }]
            
        except ImportError as e:
            raise RuntimeError(f"Stable Diffusion服务不可用: {str(e)}")
    
    def generate_from_prompts_file(self, prompts_file: str, preferred_service: Optional[ImageService] = None) -> List[Dict[str, Any]]:
        """从提示词文件生成图片
        
        Args:
            prompts_file: 提示词文件路径
            preferred_service: 首选服务
        
        Returns:
            生成的图片信息列表
        """
        if preferred_service:
            # 尝试使用指定服务
            try:
                if preferred_service == ImageService.LIBLIB and self._liblib_generator:
                    return self._liblib_generator.generate_from_prompts_file(prompts_file)
                elif preferred_service == ImageService.STABLE_DIFFUSION:
                    # 调用SD的批量生成接口
                    from . import image_generator
                    return image_generator.main()  # 需要根据实际接口调整
            except Exception as e:
                self.logger.warning(f"指定服务{preferred_service.value}失败: {str(e)}，使用回退机制")
        
        # 使用回退机制
        import json
        from pathlib import Path
        
        prompts_path = Path(prompts_file)
        if not prompts_path.exists():
            raise FileNotFoundError(f"提示词文件不存在: {prompts_file}")
        
        with open(prompts_path, 'r', encoding='utf-8') as f:
            prompts_data = json.load(f)
        
        all_results = []
        for prompt_info in prompts_data.get('prompts', []):
            try:
                images = self.generate_images_with_fallback(
                    prompt=prompt_info.get('prompt', ''),
                    **prompt_info
                )
                all_results.extend(images)
            except Exception as e:
                self.logger.error(f"生成图片失败: {str(e)}")
                continue
        
        return all_results


# 全局实例
image_service_selector = ImageServiceSelector()


def generate_images(prompt: str, **kwargs) -> List[Dict[str, Any]]:
    """统一的图像生成接口"""
    return image_service_selector.generate_images_with_fallback(prompt, **kwargs)


def generate_from_file(prompts_file: str, preferred_service: Optional[str] = None) -> List[Dict[str, Any]]:
    """从文件生成图片的统一接口"""
    service = None
    if preferred_service:
        try:
            service = ImageService(preferred_service)
        except ValueError:
            logging.warning(f"未知的服务类型: {preferred_service}")
    
    return image_service_selector.generate_from_prompts_file(prompts_file, service)


def get_available_services() -> List[str]:
    """获取可用服务列表"""
    statuses = image_service_selector.get_service_status()
    return [status.service.value for status in statuses if status.available]


if __name__ == '__main__':
    import argparse
    import time
    
    parser = argparse.ArgumentParser(description='图像生成服务选择器')
    parser.add_argument('--status', action='store_true', help='显示服务状态')
    parser.add_argument('--prompt', type=str, help='生图提示词')
    parser.add_argument('--service', type=str, choices=['liblib', 'stable_diffusion'], help='指定服务')
    
    args = parser.parse_args()
    
    if args.status:
        statuses = image_service_selector.get_service_status()
        print("图像生成服务状态:")
        for status in statuses:
            print(f"  {status.service.value}: {'可用' if status.available else '不可用'} (优先级: {status.priority})")
            if status.error_message:
                print(f"    错误: {status.error_message}")
    
    elif args.prompt:
        try:
            kwargs = {}
            if args.service:
                # 这里可以添加服务特定的参数处理
                pass
            
            results = generate_images(args.prompt, **kwargs)
            print(f"成功生成{len(results)}张图片")
            for result in results:
                print(f"  - {result.get('filename', 'unknown')}")
        except Exception as e:
            print(f"生图失败: {str(e)}")
    
    else:
        print("请使用 --status 查看服务状态或 --prompt 生成图片")