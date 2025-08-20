import os
import sys
import json
import re
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

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
        {"role": "system", "content": "请仔细阅读输入的文本生成扩散提示。\n\n你是一位稳定的扩散提示工程师，对视觉故事讲述和角色一致性有深入的了解。你的主要任务是将提供的叙事文本转换为准确和高质量的稳定扩散提示，这些提示要在整个故事中保持角色连续性和场景连贯性。\n请仔细阅读输入的文本生成扩散提示。\n\n生成提示时，请牢记以下技术规格：\n- 输出应该是单行，用逗号分隔的元素。\n- 代币限制最多为75个代币。\n- 仅使用英语单词或短语，避免使用连字符或下划线。\n- 可以使用（元素：1.0 - 1.5）来强调，但限制为3个加权元素。\n- 根据文本中的人物主体，使用1girl、1boy、2girls、1pig、2pig、1animal等字符格式。\n元素优先级（从左到右排列）如下：\n1. 人物主体/性别\n2. 核心情绪/表达\n3. 关键的身体特征\n4. 服装/风格\n5. 场景/设置\n6. 姿势/动作\n7. 镜头角度\n8. 环境细节\n9. 艺术风格/质量\n上下文意识指南：\n- 确保性格与既定特征的一致性。\n- 反映情绪语气和叙述语境。\n- 考虑场景的连续性和故事的进展。\n- 平衡明确的细节和隐含的氛围。\n质量标准：\n- 优先考虑视觉故事讲述而不是技术完美。\n- 确保提示清晰，并与稳定扩散兼容。\n- 避免冗余，同时保持描述的丰富性。\n首先，在<思考>标签中分析叙事文本，并思考如何将其转换为符合上述所有要求的提示。然后，在<提示>标签中生成提示，并以单行、逗号分隔的格式编写。\n<思考>\n[在这里提供关于您如何将叙述文本转化为提示的详细分析]\n</思考>\n<提示>\n[您生成的提示在这里]\n</提示>\n\n\n注意：只需要生成并返回提示本身，不要说其它与故事无关的话，不要返回任何XML标签！"},
        {"role": "user", "content": f"Transform this narrative text into a Stable Diffusion prompt: \"{text}\""},
    ]
    return llm_client.chat_completion(messages)

# 章节处理相关函数已移除，采用直接处理模式

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

# 定义一个函数，创建数据列表用于JSON输出
def create_data_list(sentences, character_mappings):
    """创建包含句子的数据列表"""
    data = []
    for sentence in sentences:
        # 更严格的过滤条件：忽略空行、纯英文内容、和明显的提示词模板
        sentence_clean = sentence.strip()
        if (sentence_clean and 
            not is_english_template(sentence_clean) and 
            len(sentence_clean) > 3):  # 至少3个字符
            replaced_text, lora_ids = apply_character_replacement(sentence_clean, character_mappings)
            data.append({
                "原始中文": sentence_clean,
                "英文翻译": "",
                "故事板提示词": "",
                "替换后中文": replaced_text,
                "LoRA编号": lora_ids
            })
    
    return data

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

def process_single_chapter_json(chapter, output_file_path):
    """处理单个章节，生成JSON文件"""
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
        
        # 创建数据列表
        data_list = create_data_list(sentences, character_mappings)
        
        # 自动处理，不需要用户输入
        max_workers = min(len(sentences), config.max_workers_translation)            

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 使用替换后的文本进行翻译
            futures_translation = {executor.submit(translate_to_english, data_list[idx]["替换后中文"].strip()): idx 
                                   for idx in range(len(data_list))}
            futures_storyboard = {} 

            for future in tqdm(as_completed(futures_translation), total=len(futures_translation), desc='正在翻译文本'):
                idx = futures_translation[future]
                translated_text = future.result()
                data_list[idx]["英文翻译"] = translated_text
                futures_storyboard[executor.submit(translate_to_storyboard, translated_text)] = idx

            for future in tqdm(as_completed(futures_storyboard), total=len(futures_storyboard), desc='正在生成故事板'):
                idx = futures_storyboard[future]
                data_list[idx]["故事板提示词"] = future.result()

        # 保存为JSON文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        return True
        
    except Exception as e:
        print(f"处理章节JSON时发生错误: {e}")
        return False

# process_chapter_to_json函数已移除，直接使用process_single_chapter_json

def process_input_file_directly():
    """直接处理input.md文件生成JSON文件"""
    try:
        # 读取input.md文件
        input_file = config.input_dir / "input.md"
        if not input_file.exists():
            print(f"错误: 找不到输入文件 {input_file}")
            return False
        
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 创建一个虚拟章节对象，包含整个文件内容
        chapter = {
            'title': '完整故事',
            'content': content
        }
        
        # 处理文件生成JSON
        output_file = config.output_dir_txt / "txt.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"正在处理输入文件: {input_file}")
        
        if process_single_chapter_json(chapter, output_file):
            print(f"JSON文件已生成: {output_file}")
            return True
        else:
            print("JSON文件生成失败")
            return False
        
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数 - 直接处理input.md文件生成JSON文件"""
    return process_input_file_directly()

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)