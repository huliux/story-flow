# -*- coding: utf-8 -*-
"""
图像服务工厂

负责创建和管理图像服务实例
"""

from typing import Dict, List, Optional, Type
import logging

from .base import ImageServiceBase
from ...models.image_models import ImageServiceType, ServiceStatus


class ImageServiceFactory:
    """图像服务工厂类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._service_classes: Dict[ImageServiceType, Type[ImageServiceBase]] = {}
        self._service_instances: Dict[ImageServiceType, ImageServiceBase] = {}
        self._registered_services: List[ImageServiceType] = []
    
    def register_service(self, service_type: ImageServiceType, 
                        service_class: Type[ImageServiceBase]) -> None:
        """
        注册服务类
        
        Args:
            service_type: 服务类型
            service_class: 服务类
        """
        self._service_classes[service_type] = service_class
        if service_type not in self._registered_services:
            self._registered_services.append(service_type)
        self.logger.info(f"注册图像服务: {service_type.value}")
    
    def create_service(self, service_type: ImageServiceType, 
                      **kwargs) -> Optional[ImageServiceBase]:
        """
        创建服务实例
        
        Args:
            service_type: 服务类型
            **kwargs: 服务初始化参数
            
        Returns:
            Optional[ImageServiceBase]: 服务实例
        """
        if service_type not in self._service_classes:
            self.logger.error(f"未注册的服务类型: {service_type.value}")
            return None
        
        try:
            service_class = self._service_classes[service_type]
            service_instance = service_class(**kwargs)
            self._service_instances[service_type] = service_instance
            self.logger.info(f"创建图像服务实例: {service_type.value}")
            return service_instance
        except Exception as e:
            self.logger.error(f"创建服务实例失败 {service_type.value}: {str(e)}")
            return None
    
    def get_service(self, service_type: ImageServiceType) -> Optional[ImageServiceBase]:
        """
        获取服务实例
        
        Args:
            service_type: 服务类型
            
        Returns:
            Optional[ImageServiceBase]: 服务实例
        """
        return self._service_instances.get(service_type)
    
    def get_all_services(self) -> List[ImageServiceBase]:
        """
        获取所有服务实例
        
        Returns:
            List[ImageServiceBase]: 所有服务实例列表
        """
        return list(self._service_instances.values())
    
    def get_registered_service_types(self) -> List[ImageServiceType]:
        """
        获取已注册的服务类型
        
        Returns:
            List[ImageServiceType]: 已注册的服务类型列表
        """
        return self._registered_services.copy()
    
    async def get_available_services(self) -> List[ImageServiceBase]:
        """
        获取可用的服务列表
        
        Returns:
            List[ImageServiceBase]: 可用的服务列表
        """
        available_services = []
        
        for service in self._service_instances.values():
            try:
                if await service.is_available():
                    available_services.append(service)
            except Exception as e:
                self.logger.warning(f"检查服务可用性失败 {service.service_type.value}: {str(e)}")
        
        # 按优先级排序
        available_services.sort(key=lambda s: s.priority)
        return available_services
    
    async def get_best_service(self) -> Optional[ImageServiceBase]:
        """
        获取最佳可用服务
        
        Returns:
            Optional[ImageServiceBase]: 最佳服务实例
        """
        available_services = await self.get_available_services()
        return available_services[0] if available_services else None
    
    async def get_all_service_status(self) -> List[ServiceStatus]:
        """
        获取所有服务的状态
        
        Returns:
            List[ServiceStatus]: 所有服务状态列表
        """
        statuses = []
        
        for service in self._service_instances.values():
            try:
                status = await service.get_status()
                statuses.append(status)
            except Exception as e:
                self.logger.error(f"获取服务状态失败 {service.service_type.value}: {str(e)}")
        
        # 按优先级排序
        statuses.sort(key=lambda s: s.priority)
        return statuses
    
    def clear_instances(self) -> None:
        """
        清除所有服务实例
        """
        self._service_instances.clear()
        self.logger.info("清除所有服务实例")
    
    def remove_service(self, service_type: ImageServiceType) -> bool:
        """
        移除服务
        
        Args:
            service_type: 服务类型
            
        Returns:
            bool: 是否成功移除
        """
        removed = False
        
        if service_type in self._service_instances:
            del self._service_instances[service_type]
            removed = True
        
        if service_type in self._service_classes:
            del self._service_classes[service_type]
            removed = True
        
        if service_type in self._registered_services:
            self._registered_services.remove(service_type)
            removed = True
        
        if removed:
            self.logger.info(f"移除图像服务: {service_type.value}")
        
        return removed


# 全局工厂实例
image_service_factory = ImageServiceFactory()