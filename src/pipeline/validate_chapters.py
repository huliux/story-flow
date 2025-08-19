#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节文件校验和重新生成脚本
校验 input_chapters.json 中的内容是否与 input.md 中的内容匹配
如果没有json则生成json，如果有json则校验内容，如果匹配则进行下一步，如果不匹配则重新根据input.md生成json
"""

import os
import sys
import json
import hashlib
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.pipeline.text_splitter import MarkdownSplitter

def calculate_md5(text: str) -> str:
    """计算文本的MD5哈希值"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def read_input_md() -> str:
    """读取input.md文件内容"""
    input_file = config.input_md_file
    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_file}")
    
    splitter = MarkdownSplitter()
    return splitter.read_markdown_file(input_file)

def read_chapters_json() -> list:
    """读取input_chapters.json文件内容"""
    chapters_file = config.input_dir / "input_chapters.json"
    if not chapters_file.exists():
        return None
    
    try:
        with open(chapters_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        print(f"读取章节JSON文件失败: {e}")
        return None

def extract_content_from_chapters(chapters: list) -> str:
    """从章节JSON中提取所有内容并合并"""
    if not chapters:
        return ""
    
    content_parts = []
    for chapter in chapters:
        if 'content' in chapter:
            content_parts.append(chapter['content'])
    
    return '\n\n'.join(content_parts)

def generate_chapters_from_md(md_content: str) -> list:
    """根据input.md内容生成章节JSON"""
    splitter = MarkdownSplitter()
    chapters = splitter.split_markdown(md_content)
    return chapters

def save_chapters_json(chapters: list) -> bool:
    """保存章节JSON文件"""
    try:
        splitter = MarkdownSplitter()
        return splitter.save_chapters_as_json(chapters)
    except Exception as e:
        print(f"保存章节JSON文件失败: {e}")
        return False

def validate_and_regenerate_chapters():
    """校验章节文件并在需要时重新生成"""
    print("开始校验章节文件...")
    
    try:
        # 1. 读取input.md内容
        print("正在读取input.md文件...")
        md_content = read_input_md()
        md_hash = calculate_md5(md_content)
        print(f"input.md文件MD5: {md_hash[:8]}...")
        
        # 2. 检查input_chapters.json是否存在
        chapters_file = config.input_dir / "input_chapters.json"
        print(f"检查章节文件: {chapters_file}")
        
        chapters_data = read_chapters_json()
        
        if chapters_data is None:
            print("❌ 章节JSON文件不存在或无法读取")
            print("正在根据input.md生成新的章节文件...")
            
            # 生成新的章节文件
            new_chapters = generate_chapters_from_md(md_content)
            if save_chapters_json(new_chapters):
                print(f"✅ 成功生成章节文件，共 {len(new_chapters)} 个章节")
                return True
            else:
                print("❌ 生成章节文件失败")
                return False
        
        # 3. 校验内容是否匹配
        print("正在校验章节内容与input.md是否匹配...")
        
        # 从章节JSON中提取内容
        chapters_content = extract_content_from_chapters(chapters_data)
        chapters_hash = calculate_md5(chapters_content)
        print(f"章节JSON内容MD5: {chapters_hash[:8]}...")
        
        # 生成基于当前input.md的章节内容用于对比
        expected_chapters = generate_chapters_from_md(md_content)
        expected_content = extract_content_from_chapters(expected_chapters)
        expected_hash = calculate_md5(expected_content)
        print(f"预期章节内容MD5: {expected_hash[:8]}...")
        
        # 比较哈希值
        if chapters_hash == expected_hash:
            print("✅ 章节内容与input.md匹配，无需重新生成")
            print(f"当前章节数量: {len(chapters_data)}")
            return True
        else:
            print("❌ 章节内容与input.md不匹配")
            print("正在重新生成章节文件...")
            
            # 重新生成章节文件
            if save_chapters_json(expected_chapters):
                print(f"✅ 成功重新生成章节文件，共 {len(expected_chapters)} 个章节")
                
                # 显示章节标题
                print("\n📋 章节列表:")
                for i, chapter in enumerate(expected_chapters, 1):
                    title = chapter.get('title', f'章节{i}')
                    print(f"  {i}. {title}")
                
                return True
            else:
                print("❌ 重新生成章节文件失败")
                return False
                
    except Exception as e:
        print(f"校验过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("章节文件校验和重新生成工具")
    print("=" * 60)
    
    success = validate_and_regenerate_chapters()
    
    if success:
        print("\n🎉 章节文件校验完成，可以进行下一步处理")
        return True
    else:
        print("\n❌ 章节文件校验失败")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)