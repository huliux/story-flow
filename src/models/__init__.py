# -*- coding: utf-8 -*-
"""
数据模型模块

定义项目中使用的数据结构和模型
"""

from .image_models import ImageGenerationRequest, ImageGenerationResponse, ServiceStatus

__all__ = [
    'ImageGenerationRequest',
    'ImageGenerationResponse', 
    'ServiceStatus'
]