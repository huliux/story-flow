import os
import sys
import json
import re
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.llm_client import llm_client

# 将验证代码移到main函数中执行，避免在导入时执行
# provider_info = llm_client.get_provider_info()
# if not provider_info['has_api_key']:
#     print(f"错误: 未配置{provider_info['provider']} API密钥")
#     if config.llm_provider == 'openai':
#         print("请在.env文件中设置OPENAI_API_KEY")
#     elif config.llm_provider == 'deepseek':
#         print("请在.env文件中设置DEEPSEEK_API_KEY")
#     sys.exit(1)
# 
# print(f"✅ 使用 {provider_info['provider']} - {provider_info['model']}")

# 使用正则表达式进行中文句子分割，零依赖，性能最佳


# 定义一个函数，将字符数少于设定值的句子进行合并
def merge_short_sentences(sentences, min_length=None):
    """合并短句子以确保语义完整性"""
    if min_length is None:
        min_length = config.min_sentence_length
    
    merged_sentences = []
    buffer_sentence = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if len(buffer_sentence + sentence) < min_length:
            buffer_sentence += " " + sentence if buffer_sentence else sentence
        else:
            if buffer_sentence:
                merged_sentences.append(buffer_sentence)
            buffer_sentence = sentence

    if buffer_sentence:
        merged_sentences.append(buffer_sentence)

    return merged_sentences


# 定义一个函数，翻译文本为英文
def translate_to_english(text):
    """翻译文本为英文"""
    return llm_client.translate_to_english(text)

# 定义一个函数，将文本翻译为分镜脚本
def translate_to_storyboard(text):
    """将文本翻译为分镜脚本"""
    messages = [
        {"role": "system", "content": "You are an expert Stable Diffusion prompt engineer with deep understanding of visual storytelling and character consistency. Your role is to transform narrative text into precise, high-quality prompts that maintain character continuity and scene coherence throughout a story. You excel at balancing technical SD syntax with artistic vision, ensuring each prompt captures both the explicit details and implicit emotional undertones of the source material. You prioritize character consistency, emotional authenticity, and visual storytelling flow."},
        {"role": "user", "content": f"Transform this narrative text into a Stable Diffusion prompt: \"{text}\"\n\n**Technical Specifications:**\n- Output: Single line, comma-separated elements\n- Token limit: 75 tokens maximum\n- Syntax: English words/phrases, no hyphens or underscores\n- Weighting: Use (element:1.0-1.5) for emphasis, limit to 3 weighted elements\n- Character format: 1girl, 1boy, 2girls, etc.\n\n**Element Priority (arrange left to right):**\n1. Character count/gender → 2. Core emotion/expression → 3. Key physical traits → 4. Clothing/style → 5. Scene/setting → 6. Pose/action → 7. Camera angle → 8. Environment details → 9. Art style/quality\n\n**Context Awareness Guidelines:**\n- Maintain character consistency with established traits\n- Reflect the emotional tone and narrative context\n- Consider scene continuity and story progression\n- Balance explicit details with implied atmosphere\n\n**Quality Standards:**\n- Prioritize visual storytelling over technical perfection\n- Ensure prompt clarity and SD compatibility\n- Avoid redundancy while maintaining descriptive richness\n\nGenerate the optimized prompt:"},
    ]
    return llm_client.chat_completion(messages)

# 定义一个函数，读取JSON章节文件
def read_chapters_json(file_path):
    """读取JSON格式的章节文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            chapters = json.load(file)
            if not chapters:
                raise ValueError("章节文件内容为空")
            return chapters
    except FileNotFoundError:
        raise ValueError(f"章节文件不存在: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"章节文件格式错误: {file_path}")
    except Exception as e:
        raise ValueError(f"读取章节文件时发生错误: {e}")

# 定义一个函数，读取角色映射配置
def read_character_mapping():
    """读取角色映射配置文件"""
    mapping_file = config.input_dir / "character_mapping.json"
    if not mapping_file.exists():
        print(f"警告: 角色映射文件不存在 {mapping_file}，将不进行角色名替换")
        return []
    
    try:
        with open(mapping_file, 'r', encoding='utf-8') as file:
            mappings = json.load(file)
            return mappings
    except Exception as e:
        print(f"警告: 读取角色映射文件时发生错误: {e}，将不进行角色名替换")
        return []

# 定义一个函数，应用角色名替换
def apply_character_replacement(text, character_mappings):
    """应用角色名替换并返回替换后的文本和LoRA编号列表"""
    replaced_text = text
    lora_ids = set()
    
    for mapping in character_mappings:
        original_name = mapping.get('original_name', '')
        new_name = mapping.get('new_name', '')
        lora_id = mapping.get('lora_id', '')
        
        if original_name in replaced_text:
            replaced_text = replaced_text.replace(original_name, new_name)
            if lora_id:
                lora_ids.add(lora_id)
    
    # 将LoRA编号列表转换为逗号分隔的字符串
    lora_string = ','.join(sorted(lora_ids)) if lora_ids else ''
    
    return replaced_text, lora_string

# 定义一个函数，创建DataFrame用于CSV输出
def create_dataframe(sentences, character_mappings):
    """创建包含句子的DataFrame"""
    data = []
    for sentence in sentences:
        # 更严格的过滤条件：忽略空行、纯英文内容、和明显的提示词模板
        sentence_clean = sentence.strip()
        if (sentence_clean and 
            not is_english_template(sentence_clean) and 
            len(sentence_clean) > 3):  # 至少3个字符
            replaced_text, lora_ids = apply_character_replacement(sentence_clean, character_mappings)
            data.append([sentence_clean, "", "", replaced_text, lora_ids])  # A列：原始中文，B列：英文翻译，C列：故事板，D列：替换后中文，E列：LoRA编号
    
    df = pd.DataFrame(data, columns=["原始中文", "英文翻译", "故事板提示词", "替换后中文", "LoRA编号"])
    return df

def clean_content(content):
    """清理章节内容，移除不相关的模板文本"""
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # 跳过空行和明显的英文模板内容
        if line and not is_english_template(line):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def is_english_template(text):
    """检测是否为英文模板或提示词内容"""
    # 检测英文比例
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return True
    
    english_ratio = english_chars / total_chars
    
    # 如果英文字符超过80%，认为是英文内容
    if english_ratio > 0.8:
        return True
    
    # 检测常见的提示词模板关键词
    template_keywords = [
        'Would you like me to',
        'Please share',
        'I can\'t yet generate',
        'Without the actual',
        'Token count:',
        'character descriptions',
        'emotional tone',
        'environmental setting',
        'narrative text',
        'placeholder text',
        'prompt engineering',
        'I\'ll ensure',
        'visual coherence'
    ]
    
    text_lower = text.lower()
    for keyword in template_keywords:
        if keyword.lower() in text_lower:
            return True
    
    return False

def replace_text_in_sentences(sentences, original_text, new_text):
    return [sentence.replace(original_text, new_text) for sentence in sentences]

def process_single_chapter_csv(chapter, output_file_path):
    """处理单个章节，生成CSV文件"""
    try:
        sentences = []
        # 从章节内容中提取句子
        content = chapter.get('content', '')
        
        # 预处理：清理内容，移除不相关的模板文本
        content = clean_content(content)
        
        # 移除Markdown标题标记
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        # 按句子分割 - 使用优化的正则表达式，零依赖，性能最佳
        chapter_sentences = re.findall('[^。！？]*[。！？]', content)
        
        # 处理边界情况：文本末尾没有标点符号的情况
        last_match_end = 0
        for match in re.finditer('[^。！？]*[。！？]', content):
            last_match_end = match.end()
        
        # 如果有剩余文本（末尾没有标点符号），添加到句子列表中
        if last_match_end < len(content):
            remaining_text = content[last_match_end:].strip()
            if remaining_text:
                chapter_sentences.append(remaining_text)
        
        sentences.extend(chapter_sentences)

        sentences = merge_short_sentences(sentences)  

        # 读取角色映射配置
        character_mappings = read_character_mapping()
        
        # 创建DataFrame
        df = create_dataframe(sentences, character_mappings)
        
        # 自动处理，不需要用户输入
        max_workers = min(len(sentences), config.max_workers_translation)            

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 使用替换后的文本进行翻译
            futures_translation = {executor.submit(translate_to_english, df.iloc[idx, 3].strip()): idx 
                                   for idx in range(len(df))}
            futures_storyboard = {} 

            for future in tqdm(as_completed(futures_translation), total=len(futures_translation), desc='正在翻译文本'):
                idx = futures_translation[future]
                translated_text = future.result()
                df.iloc[idx, 1] = translated_text  # 英文翻译列
                futures_storyboard[executor.submit(translate_to_storyboard, translated_text)] = idx

            for future in tqdm(as_completed(futures_storyboard), total=len(futures_storyboard), desc='正在生成故事板'):
                idx = futures_storyboard[future]
                df.iloc[idx, 2] = future.result()  # 故事板提示词列

        # 保存为CSV文件
        df.to_csv(output_file_path, index=False, encoding='utf-8')
        return True
        
    except Exception as e:
        print(f"处理章节CSV时发生错误: {e}")
        return False

def process_chapter_to_csv(chapter, output_file_path):
    """处理单个章节，生成CSV文件"""
    return process_single_chapter_csv(chapter, output_file_path)

def main():
    """主函数 - 处理指定章节生成CSV文件"""
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='处理指定章节生成CSV文件')
    parser.add_argument('--chapter-index', type=int, default=0, help='要处理的章节索引（从0开始）')
    args = parser.parse_args()
    
    try:
        # 读取章节数据
        chapters_file = config.input_dir / "input_chapters.json"
        if not chapters_file.exists():
            print(f"错误: 找不到章节文件 {chapters_file}")
            return False
        
        chapters = read_chapters_json(chapters_file)
        
        # 验证章节索引
        if args.chapter_index < 0 or args.chapter_index >= len(chapters):
            print(f"错误: 章节索引 {args.chapter_index} 超出范围 (0-{len(chapters)-1})")
            return False
        
        # 处理指定章节生成CSV文件
        chapter = chapters[args.chapter_index]
        output_file = config.output_dir_txt / "txt.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"正在处理章节: {chapter.get('title', '未命名章节')}")
        
        if process_chapter_to_csv(chapter, output_file):
            print(f"CSV文件已生成: {output_file}")
            return True
        else:
            print("CSV文件生成失败")
            return False
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)