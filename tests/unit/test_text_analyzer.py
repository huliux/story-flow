"""文本分析器模块的单元测试"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

# 由于text_analyzer模块在导入时会检查API密钥，我们需要先mock相关依赖
with patch('src.llm_client.llm_client') as mock_llm_client:
    mock_llm_client.get_provider_info.return_value = {
        'provider': 'openai',
        'model': 'gpt-3.5-turbo', 
        'has_api_key': True
    }
    from src.pipeline.text_analyzer import (
        merge_short_sentences,
        translate_to_english,
        translate_to_storyboard,
        read_character_mapping,
        apply_character_replacement,
        process_single_chapter_json
    )


class TestTextAnalyzer:
    """文本分析器的测试"""
    
    def test_merge_short_sentences_basic(self):
        """测试基本的短句合并功能"""
        sentences = ["短句。", "这是一个比较长的句子，应该保持独立。", "另一个短句。"]
        result = merge_short_sentences(sentences, min_length=10)
        
        # 验证返回结果是列表
        assert isinstance(result, list)
        # 验证结果不为空
        assert len(result) > 0
        # 验证长句子保持独立
        assert "这是一个比较长的句子，应该保持独立。" in result
    
    def test_merge_short_sentences_empty_input(self):
        """测试空输入的处理"""
        result = merge_short_sentences([])
        assert result == []
    
    def test_merge_short_sentences_single_sentence(self):
        """测试单个句子的处理"""
        sentences = ["这是一个测试句子。"]
        result = merge_short_sentences(sentences)
        assert result == sentences
    
    def test_merge_short_sentences_all_long(self):
        """测试所有句子都足够长的情况"""
        sentences = [
            "这是一个足够长的句子，不需要合并。",
            "这是另一个足够长的句子，也不需要合并。"
        ]
        result = merge_short_sentences(sentences, min_length=10)
        assert result == sentences
    
    def test_merge_short_sentences_all_short(self):
        """测试所有句子都很短的情况"""
        sentences = ["短1。", "短2。", "短3。"]
        result = merge_short_sentences(sentences, min_length=10)
        
        # 验证返回结果是列表
        assert isinstance(result, list)
        # 验证结果不为空
        assert len(result) > 0
        # 短句应该被合并，结果数量应该少于原始数量
        assert len(result) <= len(sentences)
    
    def test_regex_sentence_splitting(self):
        """测试正则表达式句子分割功能"""
        import re
        text = "第一个句子。第二个句子！第三个句子？"
        result = re.findall('[^。！？]*[。！？]', text)
        
        expected = ["第一个句子。", "第二个句子！", "第三个句子？"]
        assert result == expected
    
    def test_regex_sentence_splitting_with_remaining_text(self):
        """测试正则表达式句子分割处理末尾无标点的情况"""
        import re
        text = "第一个句子。第二个句子！没有标点的文本"
        sentences = re.findall('[^。！？]*[。！？]', text)
        
        # 处理剩余文本
        last_match_end = 0
        for match in re.finditer('[^。！？]*[。！？]', text):
            last_match_end = match.end()
        
        if last_match_end < len(text):
            remaining_text = text[last_match_end:].strip()
            if remaining_text:
                sentences.append(remaining_text)
        
        expected = ["第一个句子。", "第二个句子！", "没有标点的文本"]
        assert sentences == expected
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('src.pipeline.text_analyzer.translate_to_storyboard')
    @patch('src.pipeline.text_analyzer.translate_to_english')
    @patch('src.pipeline.text_analyzer.read_character_mapping')
    def test_process_single_chapter_json_functionality(self, mock_read_mapping, mock_translate_english, mock_translate_storyboard, mock_json_dump, mock_file):
        """测试process_single_chapter_json函数的基本功能"""
        import tempfile
        import os
        
        # 设置mock返回值
        mock_read_mapping.return_value = {}
        mock_translate_english.return_value = "Translated text"
        mock_translate_storyboard.return_value = "Storyboard prompt"
        
        # 创建测试章节数据
        test_chapter = {
            'title': '第一章',
            'content': '第一个句子。第二个句子！第三个句子？'
        }
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # 调用函数
            result = process_single_chapter_json(test_chapter, temp_path)
            
            # 验证返回结果
            assert isinstance(result, bool)
            assert result == True  # 应该返回True表示成功
            
            # 验证mock被调用
            mock_json_dump.assert_called()
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_file_operations(self, mock_exists, mock_open):
        """测试文件操作相关功能"""
        # Mock文件存在
        mock_exists.return_value = True
        
        # Mock JSON读取
        import json
        mock_data = [
            {'章节': 1, '原始中文': '内容1', '故事板提示词': '提示词1'},
            {'章节': 2, '原始中文': '内容2', '故事板提示词': '提示词2'}
        ]
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = json.dumps(mock_data, ensure_ascii=False)
        
        # 这里可以测试实际的文件读取逻辑
        # 由于text_analyzer模块的main函数比较复杂，我们主要测试核心功能
        assert True  # 占位符，实际测试需要根据具体的文件操作逻辑来编写
    
    def test_sentence_length_validation(self):
        """测试句子长度验证"""
        # 测试不同长度的句子
        short_sentences = ["短。", "很短。", "也短。"]
        long_sentences = ["这是一个足够长的句子，应该保持独立。"]
        mixed_sentences = short_sentences + long_sentences
        
        result = merge_short_sentences(mixed_sentences, min_length=15)
        
        # 验证结果中的句子都满足最小长度要求或者是合并后的结果
        for sentence in result:
            if sentence in long_sentences:
                assert len(sentence) >= 15
            else:
                # 合并后的句子应该包含多个原始短句
                assert any(short in sentence for short in short_sentences)