#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F.1文生图完整参数测试脚本
测试用户要求的完整参数结构支持
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加src目录到路径
sys.path.insert(0, str(project_root / 'src'))

from pipeline.liblib_service import (
    LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork
)
from config import Config

# 创建配置实例
config = Config()

def test_f1_complete_params():
    """测试F.1文生图完整参数结构"""
    print("=== F.1文生图完整参数测试 ===")
    
    # 初始化服务
    liblib_config = LiblibConfig(
        access_key=config.liblib_access_key,
        secret_key=config.liblib_secret_key
    )
    service = LiblibService(liblib_config, config)
    
    # 创建完整参数配置（使用from_config方法，包含hiResFixInfo）
    params = F1GenerationParams.from_config(
        prompt="filmfotos, Asian portrait,A young woman wearing a green baseball cap,covering one eye with her hand",
        config=config,
        # 覆盖部分默认参数
        steps=20,
        width=768,
        height=1024,
        img_count=1,
        seed=-1,
        restore_faces=0,
        template_uuid="6f7c4652458d4802969f8d089cf5b91f",  # 用户指定的模板ID
        # LoRA配置会使用配置文件中的默认值
    )
    
    print(f"提示词: {params.prompt}")
    print(f"模板UUID: {params.template_uuid}")
    print(f"LoRA模型ID: {params.additional_network[0].model_id}")
    print(f"图片尺寸: {params.width}x{params.height}")
    print(f"采样步数: {params.steps}")
    print(f"面部修复: {params.restore_faces}")
    
    # 检查生成的参数字典结构
    generate_params = params.to_dict()
    print("\n=== 生成的参数结构 ===")
    print(f"generateParams: {generate_params}")
    
    # 验证参数结构是否符合用户要求
    expected_keys = ["prompt", "steps", "width", "height", "imgCount", "seed", "restoreFaces", "additionalNetwork"]
    missing_keys = [key for key in expected_keys if key not in generate_params]
    if missing_keys:
        print(f"❌ 缺少参数: {missing_keys}")
        return False
    
    # 验证LoRA结构
    if "additionalNetwork" in generate_params:
        lora = generate_params["additionalNetwork"][0]
        if "modelId" not in lora or "weight" not in lora:
            print("❌ LoRA参数结构不正确")
            return False
        print(f"✅ LoRA配置正确: modelId={lora['modelId']}, weight={lora['weight']}")
    
    try:
        # 发送请求
        print("\n=== 发送F.1文生图请求 ===")
        result = service.f1_text_to_image(params)
        
        print(f"✅ 请求成功提交")
        print(f"任务UUID: {result.generate_uuid}")
        print(f"状态: {result.status}")
        print(f"消息: {result.message}")
        
        # 查询任务状态
        print("\n=== 查询任务状态 ===")
        status_result = service.get_generate_status(result.generate_uuid)
        print(f"当前状态: {status_result.status}")
        print(f"进度: {status_result.progress}%")
        
        if status_result.status.value == 5:  # SUCCESS
            print(f"✅ 生图成功，共生成 {len(status_result.images)} 张图片")
            for i, img in enumerate(status_result.images):
                print(f"图片 {i+1}: {img.get('url', 'N/A')}")
        else:
            print(f"⏳ 任务进行中，状态: {status_result.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False

def main():
    """主函数"""
    success = test_f1_complete_params()
    
    if success:
        print("\n🎉 F.1文生图完整参数测试通过！")
        print("✅ 支持用户要求的完整参数结构")
        print("✅ templateUuid可配置")
        print("✅ generateParams包含所有必需参数")
        print("✅ LoRA配置正确")
    else:
        print("\n❌ 测试失败，请检查参数配置")
        sys.exit(1)

if __name__ == "__main__":
    main()