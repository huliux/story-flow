#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F.1文生图完整参数使用示例
展示如何使用用户要求的完整参数结构进行F.1文生图
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.image.liblib_service import (
    LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork
)
from config import config
import time

def main():
    """F.1文生图完整参数示例"""
    print("=== F.1文生图完整参数示例 ===")
    
    # 初始化LiblibAI服务
    liblib_config = LiblibConfig(
        access_key=config.liblib_access_key,
        secret_key=config.liblib_secret_key
    )
    service = LiblibService(liblib_config)
    
    # 创建F.1文生图参数（完全按照用户要求的结构）
    params = F1GenerationParams(
        # 基础参数
        prompt="filmfotos, Asian portrait,A young woman wearing a green baseball cap,covering one eye with her hand",
        steps=20,
        width=768,
        height=1024,
        img_count=1,
        seed=-1,
        restore_faces=0,  # 面部修复，0关闭，1开启
        template_uuid="6f7c4652458d4802969f8d089cf5b91f",  # 参数模板ID
        
        # LoRA配置（使用用户指定的LoRA模型ID）
        additional_network=[
            AdditionalNetwork(
                model_id="10880f7e4a06400e88c059886e9bc363",  # 用户指定的LoRA ID
                weight=1.0  # LoRA权重
            )
        ]
    )
    
    print("\n=== 参数配置 ===")
    print(f"提示词: {params.prompt}")
    print(f"模板UUID: {params.template_uuid}")
    print(f"图片尺寸: {params.width}x{params.height}")
    print(f"采样步数: {params.steps}")
    print(f"面部修复: {params.restore_faces}")
    print(f"LoRA模型ID: {params.additional_network[0].model_id}")
    print(f"LoRA权重: {params.additional_network[0].weight}")
    
    # 显示生成的完整参数结构
    generate_params = params.to_dict()
    print("\n=== 完整参数结构 ===")
    print("{")  
    print(f'    "templateUuid": "{params.template_uuid}",')  
    print('    "generateParams": {')
    for key, value in generate_params.items():
        if key == "additionalNetwork":
            print(f'        "{key}": [')
            for lora in value:
                print('            {')
                print(f'                "modelId": "{lora["modelId"]}",')  
                print(f'                "weight": {lora["weight"]}')
                print('            }')
            print('        ]')
        elif isinstance(value, str):
            print(f'        "{key}": "{value}",')
        else:
            print(f'        "{key}": {value},')
    print('    }')
    print('}')
    
    try:
        # 提交F.1文生图任务
        print("\n=== 提交F.1文生图任务 ===")
        result = service.f1_text_to_image(params)
        
        print(f"✅ 任务提交成功")
        print(f"任务UUID: {result.generate_uuid}")
        print(f"状态: {result.status}")
        print(f"消息: {result.message}")
        
        # 等待并查询任务状态
        print("\n=== 等待生图完成 ===")
        max_wait_time = 300  # 最大等待5分钟
        check_interval = 10  # 每10秒检查一次
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            status_result = service.get_generate_status(result.generate_uuid)
            print(f"[{elapsed_time}s] 状态: {status_result.status}, 进度: {status_result.progress:.1f}%")
            
            if status_result.status.value == 5:  # SUCCESS
                print(f"\n🎉 生图成功！共生成 {len(status_result.images)} 张图片")
                for i, img in enumerate(status_result.images):
                    print(f"图片 {i+1}: {img.get('url', 'N/A')}")
                break
            elif status_result.status.value == 6:  # FAILED
                print(f"\n❌ 生图失败: {status_result.message}")
                break
            elif status_result.status.value == 7:  # TIMEOUT
                print(f"\n⏰ 生图超时: {status_result.message}")
                break
        else:
            print(f"\n⏰ 等待超时（{max_wait_time}秒），请稍后手动查询任务状态")
            print(f"任务UUID: {result.generate_uuid}")
        
    except Exception as e:
        print(f"\n❌ 生图失败: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ F.1文生图示例运行完成")
    else:
        print("\n❌ F.1文生图示例运行失败")
        sys.exit(1)
