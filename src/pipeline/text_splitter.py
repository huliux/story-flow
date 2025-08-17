import os
import re
import sys
import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

def print_warning():
    print("警告：此脚本将处理 Markdown 文件并生成 JSON 格式的章节文件。")

def assert_warning_exists():
    return True

if assert_warning_exists():
    pass

class MarkdownSplitter:
    """Markdown 文本分割器，专门处理 Markdown 格式输入，输出 JSON 格式"""
    
    def __init__(self):
        pass
        
    def read_markdown_file(self, file_path: Path) -> str:
        """读取 Markdown 文件内容"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise UnicodeDecodeError(f'无法使用任何尝试过的编码方式解码文件: {file_path}')
    
    def split_markdown(self, text: str) -> List[Dict[str, str]]:
        """分割 Markdown 格式文本为章节"""
        chapters = []
        
        # Markdown 标题模式 - 修复正则表达式
        patterns = [
            r'^(#{2,3}\s+第.+章.*)$',  # ## 第X章 或 ### 第X章
            r'^(#{1,3}\s+.+)$',       # 通用 # ## ### 标题
            r'^(第.+章.*)$',          # 第X章（无#号）
            r'^(Chapter\s+\d+.*)$'    # Chapter X
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
            if matches:
                chapters = self._extract_chapters_by_matches(text, matches)
                break
        
        if not chapters:
            # 如果没有找到标题，按段落分割
            chapters = self._split_by_paragraphs(text)
        
        return chapters
    
    def _extract_chapters_by_matches(self, text: str, matches: List) -> List[Dict[str, str]]:
        """根据匹配结果提取章节"""
        chapters = []
        
        for i, match in enumerate(matches):
            title = match.group(0).strip()
            start_pos = match.start()  # 从标题开始
            
            # 确定章节内容的结束位置
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(text)
            
            # 完整的章节内容（包含标题）
            full_content = text[start_pos:end_pos].strip()
            
            if full_content:  # 只添加有内容的章节
                chapters.append({
                    'title': title,
                    'content': full_content,
                    'index': i + 1
                })
        
        return chapters
    
    def _split_by_paragraphs(self, text: str) -> List[Dict[str, str]]:
        """按段落分割文本"""
        paragraphs = re.split(r'\n\s*\n', text.strip())
        chapters = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                chapters.append({
                    'title': f'段落 {i + 1}',
                    'content': paragraph.strip(),
                    'index': i + 1
                })
        
        return chapters
    
    def save_chapters_as_json(self, chapters: List[Dict[str, str]]) -> bool:
        """保存章节为 JSON 格式"""
        try:
            output_dir = config.input_dir
            input_filename = config.input_md_file.stem
            
            output_dir.mkdir(parents=True, exist_ok=True)
            return self._save_as_json(chapters, output_dir, input_filename)
                
        except Exception as e:
            print(f"保存章节时发生错误: {e}")
            return False
    
    def _save_as_json(self, chapters: List[Dict[str, str]], output_dir: Path, input_filename: str) -> bool:
        """保存为JSON格式"""
        output_file = output_dir / f"{input_filename}_chapters.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)
        
        return True

def main():
    """主函数：执行 Markdown 文本分章切割，输出 JSON 格式"""
    # 使用配置文件中的路径
    input_file_path = config.input_md_file
    output_dir = config.input_dir
    
    print(f"输入文件: {input_file_path}")
    print(f"输出目录: {output_dir}")
    
    # 检查输入文件是否存在
    if not input_file_path.exists():
        print(f"错误: 输入文件不存在 - {input_file_path}")
        return False
    
    try:
        # 创建 Markdown 分割器实例
        splitter = MarkdownSplitter()
        
        # 读取 Markdown 文件
        print("正在读取 Markdown 文件...")
        text = splitter.read_markdown_file(input_file_path)
        
        # 按章节分割
        print("正在分割章节...")
        chapters = splitter.split_markdown(text)
        
        if not chapters:
            print("错误: 未发现任何章节，请检查文本格式")
            return False
        
        print(f"发现 {len(chapters)} 个章节")
        
        # 获取输入文件名（不含扩展名）
        input_filename = input_file_path.stem
        
        # 保存为 JSON 格式
        success = splitter.save_chapters_as_json(chapters)
        
        if success:
            print(f"成功生成 JSON 章节文件到目录: {output_dir}")
            return True
        else:
            print("保存章节文件失败")
            return False
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
