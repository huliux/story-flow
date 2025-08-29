# -*- coding: utf-8 -*-
"""
图像相关数据模型

定义图像生成服务中使用的数据结构
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class ImageServiceType(Enum):
    """图像服务类型枚举"""

    LIBLIB_AI = "liblib_ai"
    LIBLIB_F1 = "liblib_f1"
    STABLE_DIFFUSION = "stable_diffusion"


@dataclass
class ImageGenerationRequest:
    """图像生成请求数据模型"""

    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 512
    height: int = 512
    steps: int = 20
    cfg_scale: float = 7.0
    seed: Optional[int] = None
    batch_size: int = 1
    model_name: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "prompt": self.prompt,
            "width": self.width,
            "height": self.height,
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "batch_size": self.batch_size,
        }

        if self.negative_prompt:
            result["negative_prompt"] = self.negative_prompt
        if self.seed is not None:
            result["seed"] = self.seed
        if self.model_name:
            result["model_name"] = self.model_name
        if self.extra_params:
            result.update(self.extra_params)

        return result


@dataclass
class ImageGenerationResponse:
    """图像生成响应数据模型"""

    success: bool
    images: List[str]  # Base64编码的图像或图像URL
    service_type: ImageServiceType
    generation_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ServiceStatus:
    """服务状态数据模型"""

    service: ImageServiceType
    available: bool
    priority: int
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.last_check is None:
            from datetime import datetime

            self.last_check = datetime.now().isoformat()
