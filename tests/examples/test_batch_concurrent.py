#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量生成功能的并发控制和prompt字段读取
"""

import json
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.services.image.liblib_service import LiblibService, LiblibConfig
from src.liblib_standalone import batch_generate_from_json


def create_test_json():
    """创建测试用的JSON文件，模拟sd_prompt.json格式"""
    from datetime import datetime
    
    test_data = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "video_theme": "测试场景集合",
            "file_type": "sd_prompts"
        },
        "storyboards": [
            {
                "scene_id": "1",
                "original_chinese": "一只可爱的小猫在花园里玩耍",
                "english_prompt": "一只可爱的小猫在花园里玩耍，阳光明媚，卡通风格",
                "processed_chinese": "一只可爱的小猫在花园里玩耍",
                "lora_id": "001"
            },
            {
                "scene_id": "2",
                "original_chinese": "一个现代化的城市夜景",
                "english_prompt": "一个现代化的城市夜景，霓虹灯闪烁，科幻风格",
                "processed_chinese": "一个现代化的城市夜景",
                "lora_id": "002"
            },
            {
                "scene_id": "3",
                "original_chinese": "一片宁静的湖泊",
                "english_prompt": "一片宁静的湖泊，山峦倒影，水彩画风格",
                "processed_chinese": "一片宁静的湖泊",
                "lora_id": "003"
            },
            {
                "scene_id": "4",
                "original_chinese": "一个温馨的咖啡厅内部",
                "english_prompt": "一个温馨的咖啡厅内部，暖色调灯光，写实风格",
                "processed_chinese": "一个温馨的咖啡厅内部",
                "lora_id": "004"
            },
            {
                "scene_id": "5",
                "original_chinese": "一朵盛开的樱花树",
                "english_prompt": "一朵盛开的樱花树，粉色花瓣飘落，日式风格",
                "processed_chinese": "一朵盛开的樱花树",
                "lora_id": "005"
            }
        ]
    }
    
    test_file = Path('test_prompts.json')
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"创建测试文件: {test_file}")
    print(f"包含 {len(test_data)} 个测试提示词")
    return test_file


def test_batch_generation():
    """测试批量生成功能"""
    print("=== 测试批量生成功能（并发控制 + prompt字段读取）===")
    
    # 创建测试JSON文件
    test_file = create_test_json()
    
    try:
        # 初始化服务
        liblib_config = LiblibConfig(
            access_key=config.liblib_access_key,
            secret_key=config.liblib_secret_key
        )
        service = LiblibService(liblib_config, config)
        
        # 创建输出目录
        output_dir = Path('./test_batch_output')
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n开始测试批量生成...")
        print(f"输出目录: {output_dir}")
        print(f"最大并发数: 3")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行批量生成
        batch_generate_from_json(
            service=service,
            json_file=test_file,
            output_dir=output_dir,
            use_f1=True,  # 使用F.1模型
            max_concurrent=3  # 最大并发3张
        )
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n批量生成完成，总耗时: {duration:.2f}秒")
        
        # 检查输出文件
        output_files = list(output_dir.glob('*.png'))
        print(f"生成的图片文件数量: {len(output_files)}")
        
        for file in output_files:
            print(f"  - {file.name}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
            print(f"\n清理测试文件: {test_file}")


def test_prompt_field_extraction():
    """测试prompt字段提取功能"""
    print("\n=== 测试prompt字段提取功能 ===")
    
    # 测试数据
    test_cases = [
        # 包含"故事板提示词"字段的对象数组
        {
            "name": "故事板提示词格式",
            "data": [
                {"故事板提示词": "测试提示词1", "其他字段": "值1"},
                {"故事板提示词": "测试提示词2", "其他字段": "值2"}
            ],
            "expected_prompts": ["测试提示词1", "测试提示词2"]
        },
        # 包含prompt字段的对象数组（兼容性测试）
        {
            "name": "prompt字段格式",
            "data": [
                {"prompt": "测试提示词3", "其他字段": "值3"},
                {"prompt": "测试提示词4", "其他字段": "值4"}
            ],
            "expected_prompts": ["测试提示词3", "测试提示词4"]
        },
        # 字符串数组
        {
            "name": "字符串数组格式",
            "data": ["测试提示词5", "测试提示词6"],
            "expected_prompts": ["测试提示词5", "测试提示词6"]
        }
    ]
    
    for case in test_cases:
        print(f"\n测试 {case['name']}:")
        
        # 创建临时测试文件
        temp_file = Path(f'temp_{case["name"].replace(" ", "_")}.json')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(case['data'], f, ensure_ascii=False, indent=2)
        
        try:
            # 模拟提取逻辑
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            prompts = []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        prompt = item.get('故事板提示词', item.get('prompt', ''))
                        if prompt:
                            prompts.append(prompt)
                    elif isinstance(item, str):
                        prompts.append(item)
            
            print(f"  提取的prompts: {prompts}")
            print(f"  期望的prompts: {case['expected_prompts']}")
            
            if prompts == case['expected_prompts']:
                print(f"  ✅ 测试通过")
            else:
                print(f"  ❌ 测试失败")
        
        finally:
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()


if __name__ == '__main__':
    print("开始测试批量生成功能...")
    
    # 测试prompt字段提取
    test_prompt_field_extraction()
    
    # 测试批量生成（需要有效的API密钥）
    if config.liblib_access_key and config.liblib_secret_key:
        test_batch_generation()
    else:
        print("\n⚠️  跳过批量生成测试（缺少API密钥配置）")
    
    print("\n测试完成！")
