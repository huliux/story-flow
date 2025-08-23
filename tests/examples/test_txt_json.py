#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试从指定的sd_prompt.json文件读取"故事板提示词"字段进行批量生成
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.services.image.liblib_service import LiblibService, LiblibConfig
from src.liblib_standalone import batch_generate_from_json


def test_txt_json_batch_generation():
    """测试从sd_prompt.json文件批量生成图片"""
    print("=== 测试从sd_prompt.json文件批量生成图片 ===")
    
    # 指定的sd_prompt.json文件路径
    txt_json_path = Path('/Users/forest/story-flow/data/output/processed/sd_prompt.json')
    
    if not txt_json_path.exists():
        print(f"错误: 文件不存在: {txt_json_path}")
        return
    
    try:
        # 初始化服务
        liblib_config = LiblibConfig(
            access_key=config.liblib_access_key,
            secret_key=config.liblib_secret_key
        )
        service = LiblibService(liblib_config, config)
        
        # 创建输出目录
        output_dir = Path('./txt_json_output')
        output_dir.mkdir(exist_ok=True)
        
        print(f"\n开始从sd_prompt.json文件批量生成...")
        print(f"输入文件: {txt_json_path}")
        print(f"输出目录: {output_dir}")
        print(f"最大并发数: 3")
        print(f"使用F.1模型: 是")
        
        # 记录开始时间
        start_time = time.time()
        
        # 执行批量生成（只生成前3张图片进行测试）
        batch_generate_from_json(
            service=service,
            json_file=txt_json_path,
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


def preview_txt_json_prompts():
    """预览sd_prompt.json文件中的故事板提示词"""
    print("\n=== 预览sd_prompt.json文件中的故事板提示词 ===")
    
    txt_json_path = Path('/Users/forest/story-flow/data/output/processed/sd_prompt.json')
    
    if not txt_json_path.exists():
        print(f"错误: 文件不存在: {txt_json_path}")
        return
    
    try:
        import json
        
        with open(txt_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"文件包含 {len(data)} 个条目")
        
        # 检查数据结构
        if isinstance(data, dict) and 'storyboards' in data:
            storyboards = data['storyboards']
            print(f"找到标准化格式，包含 {len(storyboards)} 个故事板")
            
            # 显示前5个故事板提示词
            for i, item in enumerate(storyboards[:5], 1):
                if isinstance(item, dict) and 'english_prompt' in item:
                    prompt = item['english_prompt']
                    lora_id = item.get('lora_id', '')
                    scene_id = item.get('scene_id', '')
                    print(f"\n{i}. 场景ID: {scene_id}")
                    print(f"   英文提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
                    print(f"   LoRA编号: {lora_id if lora_id else '无'}")
                else:
                    print(f"\n{i}. 无效数据格式")
            
            if len(storyboards) > 5:
                print(f"\n... 还有 {len(storyboards) - 5} 个条目")
            
            # 统计有效的故事板提示词数量
            valid_prompts = 0
            for item in storyboards:
                if isinstance(item, dict) and item.get('english_prompt'):
                    valid_prompts += 1
            
            print(f"\n有效的故事板提示词数量: {valid_prompts}/{len(storyboards)}")
        else:
            # 兼容旧格式
            print("检测到旧格式，尝试兼容处理...")
            if isinstance(data, list):
                # 显示前5个故事板提示词
                for i, item in enumerate(data[:5], 1):
                    if isinstance(item, dict) and '故事板提示词' in item:
                        prompt = item['故事板提示词']
                        lora_id = item.get('LoRA编号', '')
                        print(f"\n{i}. 故事板提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
                        print(f"   LoRA编号: {lora_id if lora_id else '无'}")
                    else:
                        print(f"\n{i}. 无效数据格式")
                
                if len(data) > 5:
                    print(f"\n... 还有 {len(data) - 5} 个条目")
                
                # 统计有效的故事板提示词数量
                valid_prompts = 0
                for item in data:
                    if isinstance(item, dict) and item.get('故事板提示词'):
                        valid_prompts += 1
                
                print(f"\n有效的故事板提示词数量: {valid_prompts}/{len(data)}")
        
    except Exception as e:
        print(f"预览文件时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("开始测试sd_prompt.json文件批量生成功能...")
    
    # 预览文件内容
    preview_txt_json_prompts()
    
    # 测试批量生成（需要有效的API密钥）
    if config.liblib_access_key and config.liblib_secret_key:
        user_input = input("\n是否继续进行批量生成测试？(y/N): ")
        if user_input.lower() in ['y', 'yes']:
            test_txt_json_batch_generation()
        else:
            print("跳过批量生成测试")
    else:
        print("\n⚠️  跳过批量生成测试（缺少API密钥配置）")
    
    print("\n测试完成！")
