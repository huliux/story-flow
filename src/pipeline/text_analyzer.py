import os
import sys
import json
import re
import spacy
import time
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.llm_client import llm_client

# 验证LLM配置
provider_info = llm_client.get_provider_info()
if not provider_info['has_api_key']:
    print(f"错误: 未配置{provider_info['provider']} API密钥")
    if config.llm_provider == 'openai':
        print("请在.env文件中设置OPENAI_API_KEY")
    elif config.llm_provider == 'deepseek':
        print("请在.env文件中设置DEEPSEEK_API_KEY")
    sys.exit(1)

print(f"✅ 使用 {provider_info['provider']} - {provider_info['model']}")

# 加载 Spacy 的中文模型，用于句子的分割
try:
    nlp = spacy.load('zh_core_web_sm')
    print("✅ 已加载中文spaCy模型")
except OSError:
    print("⚠️  警告: 未安装中文spaCy模型，将使用简单的句子分割方法")
    print("   如需完整功能，请运行: uv add https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.7.0/zh_core_web_sm-3.7.0-py3-none-any.whl")
    nlp = None


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
        {"role": "system", "content": "You are a professional storyboard assistant."},
        {"role": "user", "content": f"Based on the text \"{text}\", 基于我给的文本，在提示的生成中，您需要使用提示词来描述角色属性、主题、外表、情感、服装、姿势、视角、行动、背景。使用英语单词或短语甚至自然语言标签进行描述不仅限于我给你的单词。每次生成一组提示词，提示词应该使用英语词组或简短的句子，每组不能大于75个token。然后将您想要的类似提示词组合在一起，使用英语半角作为分隔符，并按从最重要到最不重要的顺序排列。在角色属性中，1girl表示你生成了一个女孩，1boy表示你生成了一个男孩，人数可以是多个。另请注意，提示不能包含-和_。可以有空格和自然语言，但不能太多，单词不能重复。包括角色的性别、主题、外表、情感、服装、姿势、视角、行动、背景，并按从最重要到最不重要的顺序排列，越靠前的词组权重越大；可以使用括号+数字表示增加或减少权重，例如 (depth effect:1.16)，数字的范围是0-2，大于1表示增加权重，小于1表示减少权重，权重一般不超过1.5； 需要优先表现的提示词才可以增加权重，且增加权重的提示词不超过3个；优先级定义：性别>情感>外表>服装>主题>姿势>主题>行动>视角>背景>其它。我会给出一些结构示例 :1boy, club setting, daily routine, viewing others, 1girl, 18 years old, (long red hair:1.5), (casual clothing:1.2), (standing pose:1.1), side view, nightlife background。提示单词应以纯文本输出，不需要有任何解释或示例，不加引号。不要回答不必要的内容，不要问我，也不要给我举例。"},
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
        if sentence.strip():  # Ignore blank lines
            replaced_text, lora_ids = apply_character_replacement(sentence, character_mappings)
            data.append([sentence, "", "", replaced_text, lora_ids])  # A列：原始中文，B列：英文翻译，C列：故事板，D列：替换后中文，E列：LoRA编号
    
    df = pd.DataFrame(data, columns=["原始中文", "英文翻译", "故事板提示词", "替换后中文", "LoRA编号"])
    return df

def replace_text_in_sentences(sentences, original_text, new_text):
    return [sentence.replace(original_text, new_text) for sentence in sentences]

def process_single_chapter_csv(chapter, output_file_path):
    """处理单个章节，生成CSV文件"""
    try:
        sentences = []
        # 从章节内容中提取句子
        content = chapter.get('content', '')
        # 移除Markdown标题标记
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        # 按句子分割
        chapter_sentences = re.findall('.*?[。！？]', content)
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
    """主函数 - 只处理单个章节生成CSV文件"""
    try:
        # 读取章节数据
        chapters_file = config.input_dir / "input_chapters.json"
        if not chapters_file.exists():
            print(f"错误: 找不到章节文件 {chapters_file}")
            return
        
        chapters = read_chapters_json(chapters_file)
        
        # 只处理第一个章节生成CSV文件
        chapter = chapters[0]
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