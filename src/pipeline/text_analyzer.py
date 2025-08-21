import os
import sys
import json
import re
from pathlib import Path

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


# 定义一个函数，通过模型一次性处理所有字段
def process_all_fields_with_model(data_list, character_mappings, story_content):
    """通过模型分批处理所有字段"""
    # 分批处理，每批最多1个条目
    batch_size = 1
    processed_results = []
    
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i + batch_size]
        print(f"正在处理第 {i//batch_size + 1} 批数据，包含 {len(batch)} 个条目")
        
        batch_result = process_batch_with_model(batch, character_mappings, story_content)
        processed_results.extend(batch_result)
    
    return processed_results

def process_batch_with_model(data_batch, character_mappings, story_content):
    """处理单个批次的数据"""
    # 构建系统提示词
    system_prompt = f"""
基于以下文件内容：

角色映射配置：
{json.dumps(character_mappings, ensure_ascii=False, indent=2)}

完整故事内容：
{story_content}

请严格按照以下步骤和处理规则，系统性地处理以下 JSON 数组中的数据。

处理规则：

角色识别与替换：

输入： 读取输入数据中每一个对象的 "原始中文" 字段。

映射依据： 使用提供的角色映射配置（如下所示）作为唯一标准。

操作： 扫描 "原始中文" 文本，识别并定位所有出现的角色称谓。将识别到的所有角色称谓（如“你”、“小猪”、“皮皮”、“大灰狼”、“兄弟们”、“生物们”等），严格按照映射关系替换为对应的 "new_name" 值。

输出： 将完成替换后的完整文本更新到该对象的 "替换后中文" 字段。

场景识别与添加：

输入： 在完成角色替换的 "替换后中文" 文本基础上进行分析。

操作： 判断该句文本所描述的核心事件或环境（例如：“建房子”、“发现诅咒”、“被围攻”、“完成仪式”）。用一个简洁的名词性短语（如：“森林建设场景”、“诅咒揭示场景”、“村庄围攻场景”、“月光仪式场景”）总结该场景。

输出： 将此场景短语添加为 "替换后中文" 文本的后缀，与前文用句号分隔。格式为：[完成角色替换的原文]。[场景短语]。

提示词生成：

输入： 以上一步得到的、包含场景的最终版 "替换后中文" 文本为依据。

操作： 将其翻译并提炼成高质量的 Stable Diffusion 英文提示词。提示词须包含：

核心主体 (Subject): 明确的主语（如：1只穿着简朴勇敢的年轻小猪）。

关键动作 (Action): 描述正在发生什么（如：building a house, evading fiery ravens）。

镜头(Camera lens): 结合语境描述大胆的镜头视角与大胆的构图。（如：Wide-angle lens with first-person perspective）

环境氛围 (Environment/Atmosphere): 描述地点、时间、光线和情绪（如：in a lush enchanted forest, during a moonlit night, dark and cursed atmosphere）。

风格与质量 (Style/Quality): 指定艺术风格和画质（如：fantasy art style, digital painting, cinematic lighting, highly detailed, masterpiece）。

输出： 将生成的英文提示词更新到该对象的 "故事板提示词" 字段。

LoRA 编号映射：

输入： 检查每个对象 "替换后中文" 字段中出现的 "new_name" 内容。

映射规则：

如果文本中包含 "1只穿着简朴勇敢的年轻小猪"（即主角），则 "LoRA编号" 设为 "0"。

如果文本中仅包含 "多只形态各异被诅咒的森林生物" 或 "1只穿着皮毛凶猛的中成年狼"，或场景描述与主角无关，则 "LoRA编号" 设为空字符串 ""。

注意： 此规则需根据您的具体映射配置调整。当前规则基于您上次提供的配置假设。

输出： 将确定的编号更新到该对象的 "LoRA编号" 字段。

请直接返回处理后的完整JSON数组，不要添加任何其他说明文字。
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"请处理以下JSON数据：\n{json.dumps(data_batch, ensure_ascii=False, indent=2)}"}
    ]
    
    response = llm_client.chat_completion(messages)
    
    try:
        # 清理响应内容，移除可能的控制字符和格式标记
        cleaned_response = response.strip()
        
        # 移除可能的markdown代码块标记
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        # 移除控制字符（保留换行符、制表符和回车符）
        import re
        cleaned_response = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned_response)
        
        cleaned_response = cleaned_response.strip()
        
        # 检查JSON是否完整，如果不完整则尝试修复
        if not cleaned_response.endswith(']'):
            # 找到最后一个完整的对象
            last_complete_obj = cleaned_response.rfind('},')
            if last_complete_obj != -1:
                # 截取到最后一个完整对象，并添加结束符
                cleaned_response = cleaned_response[:last_complete_obj + 1] + '\n]'
                print(f"检测到不完整的JSON，已修复为: {len(cleaned_response)} 字符")
        
        # 尝试解析清理后的JSON
        processed_data = json.loads(cleaned_response)
        return processed_data
    except json.JSONDecodeError as e:
        print(f"模型返回的数据不是有效的JSON格式: {e}")
        return data_batch  # 返回原始数据

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

# apply_character_replacement函数已移除，功能由模型处理

# 定义一个函数，创建初始数据列表（只包含原始中文字段）
def create_initial_data_list(sentences):
    """创建只包含原始中文字段的初始数据列表"""
    data = []
    for sentence in sentences:
        # 更严格的过滤条件：忽略空行、纯英文内容、和明显的提示词模板
        sentence_clean = sentence.strip()
        if (sentence_clean and 
            not is_english_template(sentence_clean) and 
            len(sentence_clean) > 3):  # 至少3个字符
            data.append({
                "原始中文": sentence_clean,
                "故事板提示词": "",
                "替换后中文": "",
                "LoRA编号": ""
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

# replace_text_in_sentences函数已移除，功能由模型处理

def process_single_chapter_json(chapter, output_file_path):
    """处理单个章节，分两阶段生成JSON文件"""
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

        # 第一阶段：创建只包含"原始中文"字段的初始数据列表
        print("第一阶段：生成初始JSON文件（只包含原始中文字段）")
        initial_data_list = create_initial_data_list(sentences)
        
        # 保存初始JSON文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data_list, f, ensure_ascii=False, indent=2)
        print(f"初始JSON文件已保存: {output_file_path}")
        
        # 第二阶段：通过模型一次性处理其他字段
        print("第二阶段：通过模型处理其他字段")
        
        # 读取角色映射配置
        character_mappings = read_character_mapping()
        
        # 通过模型一次性处理所有字段
        processed_data_list = process_all_fields_with_model(
            initial_data_list, 
            character_mappings, 
            content
        )
        
        # 处理完成
        
        # 读取story_bg并翻译成英文，添加到故事板提示词末尾
        story_bg = None
        for item in character_mappings:
            if 'story_bg' in item:
                story_bg = item['story_bg']
                break
        
        if story_bg:
            # 翻译story_bg到英文
            translate_prompt = f"请将以下中文文本翻译成英文，保持简洁和准确：{story_bg}"
            messages = [
                {"role": "user", "content": translate_prompt}
            ]
            translated_bg = llm_client.chat_completion(messages).strip()
            
            # 将翻译后的story_bg添加到每个条目的故事板提示词末尾
            for item in processed_data_list:
                if item.get('故事板提示词'):
                    item['故事板提示词'] = f"{item['故事板提示词']}, {translated_bg}"
        
        # 保存最终的JSON文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data_list, f, ensure_ascii=False, indent=2)
        print(f"最终JSON文件已保存: {output_file_path}")
        
        return True
        
    except Exception as e:
        print(f"处理章节JSON时发生错误: {e}")
        import traceback
        traceback.print_exc()
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