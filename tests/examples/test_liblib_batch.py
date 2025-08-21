#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试liblib_service批量生图功能
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.pipeline.liblib_service import LiblibService, LiblibConfig
from src.config import config

def create_test_json():
    """创建测试用的JSON文件"""
    test_data = [
        {
            "prompt": "a beautiful landscape with mountains and lakes",
            "故事板提示词": "a beautiful landscape with mountains and lakes"
        },
        {
            "prompt": "a cute cat sitting on a windowsill",
            "故事板提示词": "a cute cat sitting on a windowsill"
        },
        {
            "prompt": "a futuristic city with flying cars",
            "故事板提示词": "a futuristic city with flying cars"
        }
    ]
    
    test_file = Path("test_prompts.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    return test_file

def test_batch_generation():
    """测试批量生图功能"""
    print("开始测试liblib_service批量生图功能...")
    
    # 创建测试JSON文件
    test_file = create_test_json()
    print(f"创建测试文件: {test_file}")
    
    # 创建输出目录
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 创建LiblibConfig
        liblib_config = LiblibConfig(
            access_key=config.liblib_access_key,
            secret_key=config.liblib_secret_key,
            base_url=config.liblib_base_url,
            timeout=config.liblib_timeout,
            max_retries=config.liblib_max_retries,
            retry_delay=config.liblib_retry_delay
        )
        
        # 初始化LiblibService
        service = LiblibService(liblib_config)
        
        # 执行批量生图
        print("开始批量生图...")
        generated_files = service.batch_generate_from_json(
            json_file_path=str(test_file),
            output_dir=str(output_dir),
            use_f1=True,
            width=512,
            height=512,
            steps=20,
            img_count=1
        )
        
        print(f"\n批量生图完成！")
        print(f"生成的文件: {generated_files}")
        
        return True
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False
    
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"清理测试文件: {test_file}")

if __name__ == "__main__":
    success = test_batch_generation()
    sys.exit(0 if success else 1)