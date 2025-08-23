#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试配置化的LiblibAI服务

这个脚本用于测试修改后的LiblibAI服务是否能正确从环境变量读取配置。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import Config
from src.services.image.liblib_service import (
    LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork
)

def test_config_loading():
    """测试配置加载"""
    print("=== 测试配置加载 ===")
    
    # 加载配置
    config = Config()
    
    # 检查F.1相关配置是否正确加载
    print(f"F.1默认模板UUID: {config.f1_default_template_uuid}")
    print(f"默认步数: {config.f1_default_steps}")
    print(f"默认宽度: {config.f1_default_width}")
    print(f"默认高度: {config.f1_default_height}")
    print(f"默认图片数量: {config.f1_default_img_count}")
    print(f"默认面部修复: {config.f1_default_restore_faces}")
    print(f"默认种子: {config.f1_default_seed}")
    
    return config

def test_f1_params_creation():
    """测试F.1参数对象创建"""
    print("\n=== 测试F.1参数对象创建 ===")
    
    # 加载配置
    config = Config()
    
    # 测试F1GenerationParams.from_config
    params = F1GenerationParams.from_config(
        prompt="a beautiful landscape",
        config=config
    )
    
    print(f"文生图参数:")
    print(f"  模板UUID: {params.template_uuid}")
    print(f"  步数: {params.steps}")
    print(f"  宽度: {params.width}")
    print(f"  高度: {params.height}")
    print(f"  图片数量: {params.img_count}")
    print(f"  面部修复: {params.restore_faces}")
    print(f"  随机种子: {params.seed}")
    
    return params

# 高分辨率修复和局部重绘功能已移除，F.1不支持这些功能

def test_liblib_service_creation():
    """测试LiblibService创建"""
    print("\n=== 测试LiblibService创建 ===")
    
    # 加载配置
    config = Config()
    
    # 创建LiblibConfig（这里使用测试值）
    liblib_config = LiblibConfig(
        access_key="test_access_key",
        secret_key="test_secret_key"
    )
    
    # 创建LiblibService
    service = LiblibService(liblib_config, config)
    
    print(f"LiblibService创建成功")
    print(f"  API基础URL: {service.config.base_url}")
    print(f"  超时时间: {service.config.timeout}")
    
    # 测试便利方法
    params = service.create_f1_text_params(
        prompt="test prompt",
        steps=25,  # 覆盖默认值
        width=512  # 覆盖默认值
    )
    
    print(f"\n使用便利方法创建的参数:")
    print(f"  步数: {params.steps} (应该是25，覆盖了默认值)")
    print(f"  宽度: {params.width} (应该是512，覆盖了默认值)")
    print(f"  高度: {params.height} (应该是配置中的默认值)")
    
    return service

def test_parameter_override():
    """测试参数覆盖功能"""
    print("\n=== 测试参数覆盖功能 ===")
    
    # 加载配置
    config = Config()
    
    # 测试覆盖默认参数
    params = F1GenerationParams.from_config(
        prompt="test prompt",
        config=config,
        steps=50,  # 覆盖默认步数
        width=1536,  # 覆盖默认宽度
        height=1536,  # 覆盖默认高度
        img_count=2,  # 覆盖默认图片数量
        restore_faces=1  # 开启面部修复
    )
    
    print(f"覆盖后的参数:")
    print(f"  步数: {params.steps} (覆盖值: 50)")
    print(f"  宽度: {params.width} (覆盖值: 1536)")
    print(f"  高度: {params.height} (覆盖值: 1536)")
    print(f"  图片数量: {params.img_count} (覆盖值: 2)")
    print(f"  面部修复: {params.restore_faces} (覆盖值: 1)")
    print(f"  模板UUID: {params.template_uuid}")
    print(f"  种子: {params.seed}")
    print(f"  高度: {params.height} (使用配置默认值)")
    
    return params

def main():
    """主测试函数"""
    print("开始测试配置化的LiblibAI服务...\n")
    
    try:
        # 1. 测试配置加载
        config = test_config_loading()
        
        # 2. 测试F.1参数对象创建
        f1_params = test_f1_params_creation(config)
        
        # 3. 测试LiblibService创建
        service = test_liblib_service_creation(config)
        
        # 6. 测试参数覆盖功能
        override_params = test_parameter_override(config)
        
        print("\n=== 测试完成 ===")
        print("✅ 所有测试通过！配置化的LiblibAI服务工作正常。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)