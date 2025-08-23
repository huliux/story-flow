#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一图像管理器

这个模块提供了统一的图像服务管理接口，整合了原有的ImageServiceManager和ImageServiceSelector的功能。
支持服务发现、选择、状态检查、图像生成等功能，提供了更清晰的架构和更好的可维护性。
"""

import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

from ..services.image.factory import ImageServiceFactory
from ..services.image.base import ImageServiceBase
from ..models.image_models import (
    ImageGenerationRequest,
    ImageGenerationResponse, 
    ServiceStatus,
    ImageServiceType
)
from ..config import config


@dataclass
class GenerationResult:
    """图像生成结果"""
    success: bool
    image_path: Optional[Path] = None
    service_used: Optional[str] = None
    generation_time: Optional[float] = None
    error_message: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


class ImageManager:
    """统一图像管理器
    
    整合了原有ImageServiceManager和ImageServiceSelector的功能：
    - 服务发现和注册
    - 服务状态检查和监控
    - 智能服务选择
    - 图像生成和批量处理
    - 故障转移和重试机制
    """
    
    def __init__(self):
        """初始化图像管理器"""
        self.logger = logging.getLogger(__name__)
        self.factory = ImageServiceFactory()
        self._service_cache = {}
        self._last_status_check = 0
        self._status_cache_duration = 30  # 30秒缓存
        
        # 注册默认服务
        self._register_default_services()
        
        self.logger.info("ImageManager初始化完成")
    
    def _register_default_services(self):
        """注册默认的图像服务"""
        try:
            # 注册LiblibAI服务
            from ..services.image.liblib_service import LiblibService
            self.factory.register_service(ImageServiceType.LIBLIB_AI, LiblibService)
            self.factory.register_service(ImageServiceType.LIBLIB_F1, LiblibService)
            
            # 注册Stable Diffusion服务
            from ..services.image.stable_diffusion_service import StableDiffusionService
            self.factory.register_service(ImageServiceType.STABLE_DIFFUSION, StableDiffusionService)
            
            self.logger.info("默认图像服务注册完成")
            
        except ImportError as e:
            self.logger.error(f"注册默认服务失败: {str(e)}")
    
    def get_service_status(self, service_type: Optional[ImageServiceType] = None) -> Union[ServiceStatus, List[ServiceStatus]]:
        """获取服务状态
        
        Args:
            service_type: 指定服务类型，如果为None则返回所有服务状态
            
        Returns:
            ServiceStatus或ServiceStatus列表
        """
        current_time = time.time()
        
        # 检查缓存是否过期
        if current_time - self._last_status_check > self._status_cache_duration:
            self._update_status_cache()
            self._last_status_check = current_time
        
        if service_type:
            return self._service_cache.get(service_type, ServiceStatus(
                service=service_type,
                available=False,
                message="服务未注册"
            ))
        else:
            return list(self._service_cache.values())
    
    def _update_status_cache(self):
        """更新服务状态缓存"""
        self._service_cache.clear()
        
        # 检查LiblibAI服务
        liblib_available = self._check_liblib_availability()
        self._service_cache[ImageServiceType.LIBLIB_AI] = ServiceStatus(
            service=ImageServiceType.LIBLIB_AI,
            available=liblib_available,
            message="LiblibAI服务可用" if liblib_available else "LiblibAI服务不可用"
        )
        
        self._service_cache[ImageServiceType.LIBLIB_F1] = ServiceStatus(
            service=ImageServiceType.LIBLIB_F1,
            available=liblib_available,
            message="LiblibAI F1服务可用" if liblib_available else "LiblibAI F1服务不可用"
        )
        
        # 检查Stable Diffusion服务
        sd_available = self._check_sd_availability()
        self._service_cache[ImageServiceType.STABLE_DIFFUSION] = ServiceStatus(
            service=ImageServiceType.STABLE_DIFFUSION,
            available=sd_available,
            message="Stable Diffusion服务可用" if sd_available else "Stable Diffusion服务不可用"
        )
    
    def _check_liblib_availability(self) -> bool:
        """检查LiblibAI服务可用性"""
        try:
            # 检查必要的配置
            if not config.liblib_api_key or not config.liblib_api_secret:
                return False
            
            # 尝试创建服务实例并检查可用性
            service = self.factory.get_service(ImageServiceType.LIBLIB_AI)
            return service.is_available() if service else False
            
        except Exception as e:
            self.logger.warning(f"LiblibAI服务可用性检查失败: {str(e)}")
            return False
    
    def _check_sd_availability(self) -> bool:
        """检查Stable Diffusion服务可用性"""
        try:
            # 检查API URL配置
            if not config.sd_api_url or not config.sd_api_url.startswith('http'):
                return False
            
            # 尝试创建服务实例并检查可用性
            service = self.factory.get_service(ImageServiceType.STABLE_DIFFUSION)
            return service.is_available() if service else False
            
        except Exception as e:
            self.logger.warning(f"Stable Diffusion服务可用性检查失败: {str(e)}")
            return False
    
    def get_available_services(self) -> List[ImageServiceType]:
        """获取可用的服务列表
        
        Returns:
            List[ImageServiceType]: 可用服务类型列表
        """
        available_services = []
        statuses = self.get_service_status()
        
        if isinstance(statuses, list):
            for status in statuses:
                if status.available:
                    available_services.append(status.service)
        
        return available_services
    
    def get_best_service(self, preferred_service: Optional[ImageServiceType] = None) -> Optional[ImageServiceType]:
        """选择最佳的图像生成服务
        
        Args:
            preferred_service: 首选服务类型
            
        Returns:
            ImageServiceType: 最佳服务类型，如果没有可用服务则返回None
        """
        available_services = self.get_available_services()
        
        if not available_services:
            self.logger.warning("没有可用的图像生成服务")
            return None
        
        # 如果指定了首选服务且可用，直接返回
        if preferred_service and preferred_service in available_services:
            return preferred_service
        
        # 根据配置的优先级选择服务
        priority = config.image_service_priority
        
        if priority == 'liblib_first':
            priority_order = [ImageServiceType.LIBLIB_F1, ImageServiceType.LIBLIB_AI, ImageServiceType.STABLE_DIFFUSION]
        else:  # stable_diffusion_first
            priority_order = [ImageServiceType.STABLE_DIFFUSION, ImageServiceType.LIBLIB_F1, ImageServiceType.LIBLIB_AI]
        
        # 按优先级返回第一个可用的服务
        for service_type in priority_order:
            if service_type in available_services:
                return service_type
        
        # 如果优先级列表中没有可用服务，返回第一个可用的
        return available_services[0]
    
    def generate_image(self, 
                      prompt: str, 
                      service_type: Optional[ImageServiceType] = None,
                      output_path: Optional[Path] = None,
                      **kwargs) -> GenerationResult:
        """生成图像
        
        Args:
            prompt: 图像生成提示词
            service_type: 指定服务类型，如果为None则自动选择最佳服务
            output_path: 输出文件路径
            **kwargs: 其他生成参数
            
        Returns:
            GenerationResult: 生成结果
        """
        start_time = time.time()
        
        try:
            # 选择服务
            if not service_type:
                service_type = self.get_best_service()
            
            if not service_type:
                return GenerationResult(
                    success=False,
                    error_message="没有可用的图像生成服务"
                )
            
            # 获取服务实例
            service = self.factory.get_service(service_type)
            if not service:
                return GenerationResult(
                    success=False,
                    error_message=f"无法创建{service_type.value}服务实例"
                )
            
            # 构建请求
            request = ImageGenerationRequest(
                prompt=prompt,
                negative_prompt=kwargs.get('negative_prompt'),
                width=kwargs.get('width'),
                height=kwargs.get('height'),
                steps=kwargs.get('steps'),
                cfg_scale=kwargs.get('cfg_scale'),
                seed=kwargs.get('seed'),
                batch_size=kwargs.get('batch_size', 1)
            )
            
            # 生成图像
            self.logger.info(f"使用{service_type.value}服务生成图像: {prompt[:50]}...")
            response = service.generate_image(request)
            
            if response.success:
                generation_time = time.time() - start_time
                
                # 保存图像（如果指定了输出路径）
                if output_path and hasattr(service, 'save_image'):
                    if service.save_image(response.image_data, output_path):
                        return GenerationResult(
                            success=True,
                            image_path=output_path,
                            service_used=service_type.value,
                            generation_time=generation_time,
                            params=response.params
                        )
                    else:
                        return GenerationResult(
                            success=False,
                            service_used=service_type.value,
                            error_message="图像保存失败"
                        )
                else:
                    return GenerationResult(
                        success=True,
                        service_used=service_type.value,
                        generation_time=generation_time,
                        params=response.params
                    )
            else:
                # 尝试故障转移
                return self._try_fallback_generation(prompt, service_type, output_path, start_time, **kwargs)
                
        except Exception as e:
            self.logger.error(f"图像生成过程中发生错误: {str(e)}")
            return GenerationResult(
                success=False,
                error_message=f"生成过程中发生错误: {str(e)}"
            )
    
    def _try_fallback_generation(self, 
                                prompt: str, 
                                failed_service: ImageServiceType,
                                output_path: Optional[Path],
                                start_time: float,
                                **kwargs) -> GenerationResult:
        """尝试故障转移生成
        
        Args:
            prompt: 图像生成提示词
            failed_service: 失败的服务类型
            output_path: 输出文件路径
            start_time: 开始时间
            **kwargs: 其他生成参数
            
        Returns:
            GenerationResult: 生成结果
        """
        available_services = self.get_available_services()
        fallback_services = [s for s in available_services if s != failed_service]
        
        if not fallback_services:
            return GenerationResult(
                success=False,
                service_used=failed_service.value,
                error_message="主服务失败且没有可用的备用服务"
            )
        
        # 尝试第一个备用服务
        fallback_service = fallback_services[0]
        self.logger.info(f"主服务{failed_service.value}失败，尝试使用备用服务{fallback_service.value}")
        
        try:
            service = self.factory.get_service(fallback_service)
            if not service:
                return GenerationResult(
                    success=False,
                    service_used=failed_service.value,
                    error_message=f"无法创建备用服务{fallback_service.value}实例"
                )
            
            request = ImageGenerationRequest(
                prompt=prompt,
                negative_prompt=kwargs.get('negative_prompt'),
                width=kwargs.get('width'),
                height=kwargs.get('height'),
                steps=kwargs.get('steps'),
                cfg_scale=kwargs.get('cfg_scale'),
                seed=kwargs.get('seed'),
                batch_size=kwargs.get('batch_size', 1)
            )
            
            response = service.generate_image(request)
            
            if response.success:
                generation_time = time.time() - start_time
                
                if output_path and hasattr(service, 'save_image'):
                    if service.save_image(response.image_data, output_path):
                        return GenerationResult(
                            success=True,
                            image_path=output_path,
                            service_used=fallback_service.value,
                            generation_time=generation_time,
                            params=response.params
                        )
                    else:
                        return GenerationResult(
                            success=False,
                            service_used=fallback_service.value,
                            error_message="备用服务图像保存失败"
                        )
                else:
                    return GenerationResult(
                        success=True,
                        service_used=fallback_service.value,
                        generation_time=generation_time,
                        params=response.params
                    )
            else:
                return GenerationResult(
                    success=False,
                    service_used=fallback_service.value,
                    error_message=f"备用服务生成失败: {response.message}"
                )
                
        except Exception as e:
            self.logger.error(f"备用服务生成失败: {str(e)}")
            return GenerationResult(
                success=False,
                service_used=fallback_service.value,
                error_message=f"备用服务生成过程中发生错误: {str(e)}"
            )
    
    def batch_generate_from_json(self, 
                                json_file_path: Path, 
                                output_dir: Path,
                                service_type: Optional[ImageServiceType] = None) -> Dict[str, Any]:
        """从JSON文件批量生成图像
        
        Args:
            json_file_path: JSON文件路径
            output_dir: 输出目录
            service_type: 指定服务类型，如果为None则自动选择最佳服务
            
        Returns:
            Dict: 生成结果统计
        """
        try:
            # 选择服务
            if not service_type:
                service_type = self.get_best_service()
            
            if not service_type:
                return {
                    'success_count': 0,
                    'total_count': 0,
                    'success_rate': 0,
                    'error': '没有可用的图像生成服务'
                }
            
            # 获取服务实例
            service = self.factory.get_service(service_type)
            if not service:
                return {
                    'success_count': 0,
                    'total_count': 0,
                    'success_rate': 0,
                    'error': f'无法创建{service_type.value}服务实例'
                }
            
            # 调用服务的批量生成方法
            if hasattr(service, 'batch_generate_from_json'):
                self.logger.info(f"使用{service_type.value}服务进行批量生成")
                return service.batch_generate_from_json(json_file_path, output_dir)
            else:
                return {
                    'success_count': 0,
                    'total_count': 0,
                    'success_rate': 0,
                    'error': f'{service_type.value}服务不支持批量生成'
                }
                
        except Exception as e:
            self.logger.error(f"批量生成失败: {str(e)}")
            return {
                'success_count': 0,
                'total_count': 0,
                'success_rate': 0,
                'error': str(e)
            }
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息
        
        Returns:
            Dict: 服务信息
        """
        statuses = self.get_service_status()
        available_services = self.get_available_services()
        best_service = self.get_best_service()
        
        return {
            'registered_services': [s.value for s in self.factory.get_registered_services()],
            'available_services': [s.value for s in available_services],
            'best_service': best_service.value if best_service else None,
            'service_statuses': [
                {
                    'service': status.service.value,
                    'available': status.available,
                    'message': status.message
                }
                for status in (statuses if isinstance(statuses, list) else [statuses])
            ]
        }


# 向后兼容性：提供原有类的别名
ImageServiceManager = ImageManager
ImageServiceSelector = ImageManager