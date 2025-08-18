"""语音合成器模块的单元测试"""

import pytest
from unittest.mock import Mock, patch, mock_open
import os
import tempfile
import asyncio
from pathlib import Path
import azure.cognitiveservices.speech as speechsdk

from src.pipeline.voice_synthesizer import SpeechProvider


class TestVoiceSynthesizer:
    """语音合成器的测试"""
    
    def test_voice_configuration_validation(self, mock_config):
        """测试语音配置验证"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            provider = SpeechProvider()
            
            # 验证配置属性
            assert provider.subscription == "test_key"
            assert provider.region == "eastus"
            assert provider.voice_name == "zh-CN-XiaoxiaoNeural"
            assert provider.style == "cheerful"
            assert provider.role == "Girl"
            assert provider.prosody_rate == "medium"
            assert provider.prosody_pitch == "medium"
            assert provider.prosody_volume == "medium"
            assert provider.emphasis_level == "moderate"
            assert provider.style_degree == "1.0"
    
    def test_init_missing_key(self, mock_config):
        """测试缺少API密钥时的初始化"""
        mock_config.azure_speech_key = None
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            # SpeechProvider不会在初始化时验证密钥，所以这个测试应该成功
            provider = SpeechProvider()
            assert provider.subscription is None
    
    def test_init_missing_region(self, mock_config):
        """测试缺少区域时的初始化"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = None
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            # SpeechProvider不会在初始化时验证区域，所以这个测试应该成功
            provider = SpeechProvider()
            assert provider.region is None
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_success(self, mock_config):
        """测试成功的TTS音频获取"""
        # 配置mock
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('src.pipeline.voice_synthesizer.SpeechConfig') as mock_speech_config:
                with patch('src.pipeline.voice_synthesizer.SpeechSynthesizer') as mock_synthesizer_class:
                    # Mock成功的合成结果
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    mock_result = Mock()
                    mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
                    mock_result.audio_data = b"fake_audio_data"
                    
                    # Mock异步调用
                    mock_async_result = Mock()
                    mock_async_result.get.return_value = mock_result
                    mock_synthesizer.speak_ssml_async.return_value = mock_async_result
                    
                    provider = SpeechProvider()
                    result = await provider.get_tts_audio("测试文本", "zh-CN", 1)
                    
                    # 验证结果
                    assert result['index'] == 1
                    assert result['error'] is None
                    assert result['audio_data'] is not None
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_failure(self, mock_config):
        """测试TTS音频获取失败"""
        # 配置mock
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('azure.cognitiveservices.speech.SpeechSynthesizer') as mock_synthesizer_class:
                with patch('azure.cognitiveservices.speech.SpeechConfig'):
                    # Mock失败的合成结果
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    mock_result = Mock()
                    mock_result.reason = 1  # SynthesisResult.Reason.Canceled
                    mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
                    
                    provider = SpeechProvider()
                    result = await provider.get_tts_audio("测试文本", "zh-CN", 1)
                    
                    # 验证结果
                    assert result['index'] == 1
                    assert result['error'] is not None
                    assert result['audio_data'] is None
    
    def test_speech_provider_initialization(self, mock_config):
        """测试SpeechProvider初始化"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            provider = SpeechProvider()
            
            assert provider.subscription == "test_key"
            assert provider.region == "eastus"
            assert provider.voice_name == "zh-CN-XiaoxiaoNeural"
            assert provider.style == "cheerful"
            assert provider.role == "Girl"
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_empty_text(self, mock_config):
        """测试空文本TTS音频获取"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('src.pipeline.voice_synthesizer.SpeechConfig'):
                with patch('src.pipeline.voice_synthesizer.SpeechSynthesizer') as mock_synthesizer_class:
                    # Mock成功的合成结果（即使是空文本也可能成功）
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    mock_result = Mock()
                    mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
                    mock_result.audio_data = b""
                    
                    mock_async_result = Mock()
                    mock_async_result.get.return_value = mock_result
                    mock_synthesizer.speak_ssml_async.return_value = mock_async_result
                    
                    provider = SpeechProvider()
                    
                    # 测试空字符串
                    result = await provider.get_tts_audio("", "zh-CN", 1)
                    assert result['index'] == 1
                    assert result['error'] is None
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_none_text(self, mock_config):
        """测试None文本TTS音频获取"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('src.pipeline.voice_synthesizer.SpeechConfig'):
                with patch('src.pipeline.voice_synthesizer.SpeechSynthesizer'):
                    provider = SpeechProvider()
                    
                    # None文本会导致异常，但被捕获并返回错误结果
                    result = await provider.get_tts_audio(None, "zh-CN", 1)
                    assert result['index'] == 1
                    assert result['error'] is not None
                    assert result['audio_data'] is None
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_invalid_language(self, mock_config):
        """测试无效语言代码"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('azure.cognitiveservices.speech.SpeechSynthesizer') as mock_synthesizer_class:
                with patch('azure.cognitiveservices.speech.SpeechConfig'):
                    # Mock失败的合成结果
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    mock_result = Mock()
                    mock_result.reason = 1  # Canceled
                    mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
                    
                    provider = SpeechProvider()
                    
                    # 测试无效语言代码
                    result = await provider.get_tts_audio("测试文本", "invalid-lang", 1)
                    assert result['index'] == 1
                    assert result['error'] is not None
                    assert result['audio_data'] is None
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_network_error(self, mock_config):
        """测试网络错误处理"""
        # 配置mock
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('src.pipeline.voice_synthesizer.SpeechConfig'):
                with patch('src.pipeline.voice_synthesizer.SpeechSynthesizer') as mock_synthesizer_class:
                    # Mock Azure Speech SDK抛出网络异常
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    mock_synthesizer.speak_ssml_async.side_effect = Exception("网络连接错误")
                    
                    provider = SpeechProvider()
                    
                    # 网络错误应该被捕获并返回错误结果，而不是抛出异常
                    result = await provider.get_tts_audio("测试文本", "zh-CN", 1)
                    assert result['index'] == 1
                    assert result['error'] is not None
                    assert "网络连接错误" in result['error']
    
    def test_voice_configuration_validation_duplicate(self, mock_config):
        """测试语音配置验证（重复测试）"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            synthesizer = SpeechProvider()
            
            # 验证配置被正确设置
            assert synthesizer.voice_name == "zh-CN-XiaoxiaoNeural"
            assert synthesizer.prosody_rate == "medium"
            assert synthesizer.prosody_pitch == "medium"
    
    @pytest.mark.asyncio
    async def test_get_tts_audio_batch(self, mock_config):
        """测试批量TTS音频获取"""
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
        mock_config.azure_voice_style = "cheerful"
        mock_config.azure_voice_role = "Girl"
        mock_config.azure_voice_rate = "medium"
        mock_config.azure_voice_pitch = "medium"
        mock_config.azure_voice_volume = "medium"
        mock_config.azure_voice_emphasis = "moderate"
        mock_config.azure_voice_style_degree = "1.0"
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            with patch('src.pipeline.voice_synthesizer.SpeechConfig'):
                with patch('src.pipeline.voice_synthesizer.SpeechSynthesizer') as mock_synthesizer_class:
                    # Mock成功的合成结果
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    mock_result = Mock()
                    mock_result.reason = speechsdk.ResultReason.SynthesizingAudioCompleted
                    mock_result.audio_data = b"fake_audio_data"
                    
                    mock_async_result = Mock()
                    mock_async_result.get.return_value = mock_result
                    mock_synthesizer.speak_ssml_async.return_value = mock_async_result
                    
                    provider = SpeechProvider()
                    
                    texts = ["文本1", "文本2", "文本3"]
                    
                    results = []
                    for i, text in enumerate(texts):
                        result = await provider.get_tts_audio(text, "zh-CN", i)
                        results.append(result)
                    
                    # 验证所有合成都成功
                    assert len(results) == 3
                    for i, result in enumerate(results):
                        assert result['index'] == i
                        assert result['error'] is None
                        assert result['audio_data'] is not None