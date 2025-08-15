import os
import re
import sys
import docx
from tqdm import tqdm
from src.config import config

def print_warning():
    print("Step 0: 文本分章切割运行中...")
    return True

def assert_warning_exists():
    try:
        return print_warning()
    except NameError:
        sys.exit()

if assert_warning_exists():
    pass

# 使用配置文件中的路径
input_file_path = config.input_txt_file
output_dir = config.input_dir

def read_file_with_encoding(file_path, encodings=None):
    """
    尝试使用多种编码读取文件
    """
    if encodings is None:
        encodings = config.encoding_list
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f'无法使用任何尝试过的编码方式解码文件: {file_path}')

def main():
    """主函数：执行文本分章切割"""
    print(f"输入文件: {input_file_path}")
    print(f"输出目录: {output_dir}")
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 检查输入文件是否存在
    if not input_file_path.exists():
        print(f"错误: 输入文件不存在 - {input_file_path}")
        return False
    
    try:
        # 读取文本文件
        print("正在读取文本文件...")
        text = read_file_with_encoding(input_file_path)
        
        # 按章节分割
        print("正在分割章节...")
        chapters = re.split('(\n*第.+章.*\n)', text)[1:]
        if len(chapters) % 2 != 0:
            print("警告: 章节分割结果异常，可能文本格式不符合预期")
        
        chapters = [i + j for i, j in zip(chapters[0::2], chapters[1::2])]
        print(f"发现 {len(chapters)} 个章节")
        
        if not chapters:
            print("错误: 未发现任何章节，请检查文本格式是否包含'第X章'标题")
            return False
        
        # 获取输入文件名（不含扩展名）
        input_filename = input_file_path.stem
        
        # 生成docx文件
        print("正在生成docx文件...")
        for i, chapter in tqdm(enumerate(chapters, 1), total=len(chapters), ncols=75, desc="生成章节文件"):
            doc = docx.Document()
            # 移除章节标题，只保留内容
            chapter_content = re.sub('(\n*第.+章.*\n)', '', chapter)
            doc.add_paragraph(chapter_content)
            
            output_file = output_dir / f'{input_filename}_{i}.docx'
            doc.save(str(output_file))
        
        print(f"成功生成 {len(chapters)} 个章节文件到目录: {output_dir}")
        return True
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
