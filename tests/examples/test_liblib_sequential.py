#!/usr/bin/env python3
"""
测试liblib服务的顺序生成功能
验证按照image_generator.py的逻辑进行文件命名和输出
"""

import json
import os
from pathlib import Path

def create_test_json():
    """创建测试用的JSON文件"""
    test_data = [
        {
            "原始中文": "一个美丽的花园",
            "故事板提示词": "A beautiful garden with colorful flowers, peaceful atmosphere, natural lighting",
            "替换后中文": "一个美丽的花园，有着五彩斑斓的花朵",
            "LoRA编号": "001"
        },
        {
            "原始中文": "夕阳下的城市",
            "故事板提示词": "City skyline at sunset, golden hour lighting, urban landscape, warm colors",
            "替换后中文": "夕阳西下的城市天际线",
            "LoRA编号": "002"
        },
        {
            "原始中文": "森林中的小屋",
            "故事板提示词": "Cozy cabin in the forest, surrounded by tall trees, peaceful setting",
            "替换后中文": "森林深处的温馨小屋",
            "LoRA编号": "003"
        }
    ]
    
    test_file = Path("test_sequential.json")
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"测试JSON文件已创建: {test_file}")
    return test_file

def test_sequential_generation():
    """测试顺序生成功能"""
    print("=== 测试liblib服务顺序生成功能 ===")
    
    # 创建测试JSON文件
    test_file = create_test_json()
    
    # 设置输出目录
    output_dir = Path("test_sequential_output")
    
    # 运行批量生成
    print(f"\n开始批量生成，输出目录: {output_dir}")
    print("使用F.1模型，顺序生成（无并发）")
    
    # 构建命令
    cmd = [
        "python", "src/liblib_standalone.py",
        "--json-file", str(test_file),
        "--output-dir", str(output_dir),
        "--use-f1",
        "--max-concurrent", "1"  # 确保顺序生成
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 执行命令
    import subprocess
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        print("\n=== 执行结果 ===")
        print(f"返回码: {result.returncode}")
        
        if result.stdout:
            print("\n标准输出:")
            print(result.stdout)
        
        if result.stderr:
            print("\n错误输出:")
            print(result.stderr)
        
        # 检查输出文件
        if output_dir.exists():
            files = list(output_dir.glob("*.png"))
            print(f"\n生成的文件数量: {len(files)}")
            for file in files:
                print(f"  - {file.name} ({file.stat().st_size} bytes)")
        else:
            print("\n输出目录不存在")
            
    except subprocess.TimeoutExpired:
        print("\n命令执行超时（5分钟）")
    except Exception as e:
        print(f"\n执行命令时出错: {e}")
    
    # 清理测试文件
    if test_file.exists():
        test_file.unlink()
        print(f"\n已清理测试文件: {test_file}")

def preview_file_naming():
    """预览文件命名逻辑"""
    print("\n=== 文件命名逻辑预览 ===")
    print("按照image_generator.py的逻辑:")
    print("- 文件名格式: output_{i}.png")
    print("- i 从1开始递增")
    print("- 如果文件已存在，会跳过生成")
    print("- 输出目录会自动创建")

if __name__ == "__main__":
    preview_file_naming()
    test_sequential_generation()