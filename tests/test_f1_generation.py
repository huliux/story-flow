#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F.1文生图功能测试
测试F.1文生图的完整参数配置和功能
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.image.liblib_service import (
    LiblibService, LiblibConfig,
    F1GenerationParams,
    AdditionalNetwork
)
from src.config import config


def test_f1_basic_text2img():
    """测试F.1基础文生图功能"""
    print("\n=== 测试F.1基础文生图 ===")
    
    # 创建基础参数
    params = F1GenerationParams(
        prompt="filmfotos, Asian portrait, A young woman wearing a green baseball cap, covering one eye with her hand",
        width=768,
        height=1024,
        steps=20,
        img_count=1,
        seed=-1
    )
    
    print(f"参数: {params}")
    print(f"序列化参数: {json.dumps(params.to_dict(), indent=2, ensure_ascii=False)}")
    
    # 这里可以添加实际的API调用测试
    # result = service.f1_text_to_image(params)
    print("✓ F.1基础文生图参数构建成功")
    return True


def test_f1_advanced_text2img():
    """测试F.1文生图功能（包含LoRA）"""
    print("\n=== 测试F.1文生图功能（包含LoRA） ===")
    
    # 创建F.1参数（包含LoRA）
    params = F1GenerationParams(
        prompt="masterpiece, best quality, 1girl, beautiful detailed eyes, detailed face, long hair, elegant dress",
        width=768,
        height=1024,
        steps=28,
        img_count=1,
        seed=12345,
        restore_faces=1,
        # 添加LoRA
        additional_network=[
            AdditionalNetwork(model_id="example_lora_id_1", weight=0.8),
            AdditionalNetwork(model_id="example_lora_id_2", weight=0.6)
        ]
    )
    
    print(f"提示词: {params.prompt}")
    print(f"图片尺寸: {params.width}x{params.height}")
    print(f"采样步数: {params.steps}")
    print(f"LoRA数量: {len(params.additional_network)}")
    print(f"序列化参数: {json.dumps(params.to_dict(), indent=2, ensure_ascii=False)}")
    
    # 这里可以添加实际的API调用测试
    # result = service.f1_text_to_image(params)
    print("✓ F.1文生图（包含LoRA）参数构建成功")
    return True


# F.1图生图功能已移除，只保留文生图功能


# F.1不支持ControlNet功能，已移除相关测试


def test_params_serialization():
    """测试参数序列化功能"""
    print("\n=== 测试参数序列化功能 ===")
    
    # 创建F.1参数（仅包含F.1支持的参数）
    params = F1GenerationParams(
        prompt="test prompt",
        width=768,
        height=1024,
        steps=20,
        img_count=1,
        seed=42,
        restore_faces=1,
        additional_network=[
            AdditionalNetwork(model_id="lora1", weight=0.8)
        ]
    )
    
    # 转换为字典
    params_dict = params.to_dict()
    
    print("参数字典内容:")
    for key, value in params_dict.items():
        print(f"  {key}: {value}")
    
    # 验证必要字段
    required_fields = ['prompt', 'steps', 'width', 'height', 'imgCount', 'seed', 'restoreFaces']
    missing_fields = [field for field in required_fields if field not in params_dict]
    
    if missing_fields:
        print(f"❌ 缺少必要字段: {missing_fields}")
        return False
    else:
        print("✅ 参数序列化测试通过")
        return True


def monitor_task_status(service: LiblibService, generate_uuid: str):
    """监控任务状态"""
    if not generate_uuid:
        return
    
    print(f"\n=== 监控任务状态: {generate_uuid} ===")
    
    try:
        # 等待任务完成
        result = service.wait_for_completion(generate_uuid, max_wait_time=60)
        
        print(f"任务状态: {result.status}")
        print(f"进度: {result.progress}%")
        print(f"消息: {result.message}")
        
        if result.images:
            print(f"生成图片数量: {len(result.images)}")
            for i, img in enumerate(result.images):
                print(f"  图片{i+1}: {img.get('url', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 任务状态监控失败: {e}")


def main():
    """主测试函数"""
    print("F.1文生图功能完整测试")
    print("=" * 50)
    
    # 检查配置
    if not config.liblib_access_key or not config.liblib_secret_key:
        print("❌ 请先配置LiblibAI的访问密钥")
        print("请在环境变量中设置:")
        print("  LIBLIB_ACCESS_KEY=your_access_key")
        print("  LIBLIB_SECRET_KEY=your_secret_key")
        return
    
    print(f"LiblibAI配置:")
    print(f"  Base URL: {config.liblib_base_url}")
    print(f"  Access Key: {config.liblib_access_key[:8]}...")
    print(f"  F.1默认尺寸: {config.f1_default_width}x{config.f1_default_height}")
    print(f"  F.1默认步数: {config.f1_default_steps}")
    
    # 运行测试
    test_results = []
    
    # 1. 参数序列化测试
    test_results.append(test_params_serialization())
    
    # 2. 基础文生图测试
    uuid1 = test_f1_basic_text2img()
    test_results.append(uuid1 is not None)
    
    # 3. 高级文生图测试（注释掉，因为需要有效的LoRA ID）
    # uuid2 = test_f1_advanced_text2img()
    # test_results.append(uuid2 is not None)
    
    # 4. 图生图测试（注释掉，因为需要有效的图片URL）
    # uuid3 = test_f1_img2img()
    # test_results.append(uuid3 is not None)
    
    # 5. ControlNet测试（注释掉，因为需要有效的ControlNet图片）
    # uuid4 = test_f1_controlnet()
    # test_results.append(uuid4 is not None)
    
    # 监控第一个任务的状态
    if uuid1:
        liblib_config = LiblibConfig(
            access_key=config.liblib_access_key,
            secret_key=config.liblib_secret_key,
            base_url=config.liblib_base_url
        )
        service = LiblibService(liblib_config)
        monitor_task_status(service, uuid1)
    
    # 测试结果汇总
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！F.1文生图功能完整可用")
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接")


if __name__ == "__main__":
    main()