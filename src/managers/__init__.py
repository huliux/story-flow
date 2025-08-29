# -*- coding: utf-8 -*-
"""
管理器模块

提供统一的服务管理和协调功能
"""

from .image_manager import ImageManager

# 向后兼容性别名
ImageServiceManager = ImageManager
ImageServiceSelector = ImageManager

__all__ = [
    "ImageManager",
    "ImageServiceManager",  # 向后兼容
    "ImageServiceSelector",  # 向后兼容
]
