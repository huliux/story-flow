# -*- coding: utf-8 -*-
"""
图像服务基类

定义所有图像服务的统一接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from ...models.image_models import (
    ImageGenerationRequest, 
    ImageGenerationResponse, 
    ServiceStatus, 
    ImageServiceType
)


class ImageServiceBase(ABC):
    """图像服务基类"""
    
    def __init__(self, service_type: ImageServiceType, priority: int = 1):
        """
        初始化图像服务
        
        Args:
            service_type: 服务类型
            priority: 服务优先级，数字越小优先级越高
        """
        self.service_type = service_type
        self.priority = priority
        self.logger = logging.getLogger(f"{__name__}.{service_type.value}")
        self._last_status_check = None
        self._cached_status = None
        
    @abstractmethod
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """
        生成图像
        
        Args:
            request: 图像生成请求
            
        Returns:
            ImageGenerationResponse: 图像生成响应
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            bool: 服务是否可用
        """
        pass
    
    @abstractmethod
    async def get_supported_models(self) -> List[str]:
        """
        获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型名称列表
        """
        pass
    
    async def get_status(self, force_refresh: bool = False) -> ServiceStatus:
        """
        获取服务状态
        
        Args:
            force_refresh: 是否强制刷新状态
            
        Returns:
            ServiceStatus: 服务状态
        """
        now = datetime.now()
        
        # 如果有缓存且不强制刷新，且缓存时间小于30秒，则返回缓存
        if (not force_refresh and 
            self._cached_status and 
            self._last_status_check and 
            (now - self._last_status_check).seconds < 30):
            return self._cached_status
        
        try:
            start_time = now.timestamp()
            available = await self.is_available()
            response_time = datetime.now().timestamp() - start_time
            
            status = ServiceStatus(
                service=self.service_type,
                available=available,
                priority=self.priority,
                response_time=response_time,
                last_check=now.isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"检查服务状态失败: {str(e)}")
            status = ServiceStatus(
                service=self.service_type,
                available=False,
                priority=self.priority,
                error_message=str(e),
                last_check=now.isoformat()
            )
        
        # 缓存状态
        self._cached_status = status
        self._last_status_check = now
        
        return status
    
    def validate_request(self, request: ImageGenerationRequest) -> bool:
        """
        验证请求参数
        
        Args:
            request: 图像生成请求
            
        Returns:
            bool: 请求是否有效
        """
        if not request.prompt or not request.prompt.strip():
            return False
            
        if request.width <= 0 or request.height <= 0:
            return False
            
        if request.steps <= 0 or request.steps > 100:
            return False
            
        if request.cfg_scale <= 0 or request.cfg_scale > 20:
            return False
            
        if request.batch_size <= 0 or request.batch_size > 10:
            return False
            
        return True
    
    def create_error_response(self, error_message: str, 
                            generation_time: float = 0.0) -> ImageGenerationResponse:
        """
        创建错误响应
        
        Args:
            error_message: 错误信息
            generation_time: 生成时间
            
        Returns:
            ImageGenerationResponse: 错误响应
        """
        return ImageGenerationResponse(
            success=False,
            images=[],
            service_type=self.service_type,
            generation_time=generation_time,
            error_message=error_message
        )
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.service_type.value})"
    
    def __repr__(self) -> str:
        return self.__str__()