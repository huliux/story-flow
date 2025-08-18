"""LLM客户端模块的单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.llm_client import LLMClient


class TestLLMClient:
    """LLM客户端的测试"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置对象"""
        config = Mock()
        config.llm_cooldown_seconds = 1
        return config
    
    @pytest.mark.openai
    @patch('src.llm_client.OpenAI')
    def test_init_openai_provider(self, mock_openai_class, mock_config):
        """测试OpenAI提供商的初始化"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-3.5-turbo"
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            
            assert client.provider == "openai"
            assert client.model == "gpt-3.5-turbo"
            # 验证OpenAI客户端被正确初始化
            mock_openai_class.assert_called_once_with(
                api_key="test_key",
                base_url="https://api.openai.com/v1"
            )
    
    def test_init_deepseek_provider(self, mock_config):
        """测试DeepSeek提供商的初始化"""
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.deepseek_model = "deepseek-chat"
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI') as mock_openai:
                client = LLMClient()
                
                assert client.provider == "deepseek"
                assert client.model == "deepseek-chat"
                # 验证OpenAI客户端被正确初始化
                mock_openai.assert_called_once_with(
                    api_key="test_key",
                    base_url="https://api.deepseek.com/v1"
                )
    
    def test_init_unsupported_provider(self, mock_config):
        """测试不支持的提供商"""
        mock_config.llm_provider = "unsupported"
        
        with patch('src.llm_client.config', mock_config):
            with pytest.raises(ValueError, match="Unsupported LLM provider"):
                LLMClient()
    
    @pytest.mark.openai
    @patch('src.llm_client.OpenAI')
    def test_get_provider_info_openai_with_key(self, mock_openai_class, mock_config):
        """测试获取OpenAI提供商信息（有API密钥）"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            info = client.get_provider_info()
            
            assert info['provider'] == 'OpenAI'
            assert info['model'] == 'gpt-3.5-turbo'
            assert info['has_api_key'] is True
    
    @pytest.mark.openai
    @patch('src.llm_client.OpenAI')
    def test_get_provider_info_openai_without_key(self, mock_openai_class, mock_config):
        """测试获取OpenAI提供商信息（无API密钥）"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = None
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            info = client.get_provider_info()
            
            assert info['provider'] == 'OpenAI'
            assert info['model'] == 'gpt-3.5-turbo'
            assert info['has_api_key'] is False
    
    def test_get_provider_info_deepseek_with_key(self, mock_config):
        """测试获取DeepSeek提供商信息（有API密钥）"""
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_model = "deepseek-chat"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI'):
                client = LLMClient()
                info = client.get_provider_info()
                
                assert info['provider'] == 'DeepSeek'
                assert info['model'] == 'deepseek-chat'
                assert info['has_api_key'] is True
    
    def test_get_provider_info_deepseek_without_key(self, mock_config):
        """测试获取DeepSeek提供商信息（无API密钥）"""
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = ""
        mock_config.deepseek_model = "deepseek-chat"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI'):
                client = LLMClient()
                info = client.get_provider_info()
                
                assert info['provider'] == 'DeepSeek'
                assert info['model'] == 'deepseek-chat'
                assert info['has_api_key'] is False
    
    @pytest.mark.openai
    @patch('src.llm_client.OpenAI')
    def test_chat_completion_openai_success(self, mock_openai_class, mock_config):
        """测试OpenAI聊天完成成功"""
        # 配置mock
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.llm_max_tokens = 1000
        mock_config.llm_temperature = 0.7
        
        # Mock OpenAI客户端
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "生成的文本内容"
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            messages = [{"role": "user", "content": "测试提示"}]
            result = client.chat_completion(messages)
            
            assert result == "生成的文本内容"
            mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.openai
    @patch('src.llm_client.OpenAI')
    def test_chat_completion_openai_failure(self, mock_openai_class, mock_config):
        """测试OpenAI聊天完成失败"""
        # 配置mock
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-3.5-turbo"
        
        # Mock OpenAI客户端抛出异常
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API错误")
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            messages = [{"role": "user", "content": "测试提示"}]
            
            with pytest.raises(Exception, match="API错误"):
                client.chat_completion(messages)
    
    def test_chat_completion_deepseek_success(self, mock_config):
        """测试DeepSeek聊天完成成功"""
        # 配置mock
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.deepseek_model = "deepseek-chat"
        mock_config.llm_max_tokens = 1000
        mock_config.llm_temperature = 0.7
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI') as mock_openai_class:
                # Mock OpenAI客户端和响应
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "生成的文本内容"
                mock_client.chat.completions.create.return_value = mock_response
                
                client = LLMClient()
                messages = [{"role": "user", "content": "测试提示"}]
                result = client.chat_completion(messages)
                
                assert result == "生成的文本内容"
                mock_client.chat.completions.create.assert_called_once()
    
    @patch('requests.post')
    def test_chat_completion_deepseek_http_error(self, mock_post, mock_config):
        """测试DeepSeek HTTP错误"""
        # 配置mock
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.deepseek_model = "deepseek-chat"
        
        # Mock HTTP错误响应
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            messages = [{"role": "user", "content": "测试提示"}]
            
            with pytest.raises(Exception):
                client.chat_completion(messages)
    
    def test_chat_completion_deepseek_network_error(self, mock_config):
        """测试DeepSeek网络错误"""
        # 配置mock
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.deepseek_model = "deepseek-chat"
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI') as mock_openai_class:
                # Mock网络异常
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                mock_client.chat.completions.create.side_effect = Exception("网络连接错误")
                
                client = LLMClient()
                messages = [{"role": "user", "content": "测试提示"}]
                
                with pytest.raises(Exception, match="网络连接错误"):
                    client.chat_completion(messages)
    
    @patch('src.llm_client.OpenAI')
    def test_chat_completion_empty_messages(self, mock_openai_class, mock_config):
        """测试空消息的处理"""
        mock_config.llm_provider = "deepseek"  # 使用deepseek避免OpenAI依赖
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_model = "deepseek-chat"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.llm_max_tokens = 1000
        mock_config.llm_temperature = 0.7
        
        # 模拟OpenAI客户端和响应
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = 'Empty response'
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            
            # 空消息会被传递给API，不会在客户端抛出异常
            result = client.chat_completion([])
            assert result == 'Empty response'
    
    @pytest.mark.openai
    def test_chat_completion_none_messages(self, mock_config):
        """测试None消息的处理"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-3.5-turbo"
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            
            # None消息应该抛出异常
            with pytest.raises((ValueError, TypeError, Exception)):
                client.chat_completion(None)
    
    @patch('time.sleep')
    @patch('src.llm_client.OpenAI')
    def test_rate_limiting(self, mock_openai_class, mock_sleep, mock_config):
        """测试速率限制功能"""
        mock_config.llm_provider = "deepseek"
        mock_config.deepseek_api_key = "test_key"
        mock_config.deepseek_model = "deepseek-chat"
        mock_config.deepseek_base_url = "https://api.deepseek.com/v1"
        mock_config.llm_cooldown_seconds = 1
        mock_config.llm_max_tokens = 1000
        mock_config.llm_temperature = 0.7
        
        # 模拟OpenAI客户端
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # 第一次调用成功，第二次触发速率限制
        def side_effect(*args, **kwargs):
            if mock_client.chat.completions.create.call_count == 1:
                # 第一次调用成功
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = '测试响应'
                return mock_response
            else:
                # 第二次调用触发速率限制
                raise Exception("rate limit exceeded")
        
        mock_client.chat.completions.create.side_effect = side_effect
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            
            # 第一次调用成功
            messages1 = [{"role": "user", "content": "测试1"}]
            result1 = client.chat_completion(messages1)
            assert result1 == "测试响应"
            
            # 第二次调用触发速率限制，应该重试并调用sleep
            messages2 = [{"role": "user", "content": "测试2"}]
            try:
                client.chat_completion(messages2)
            except Exception:
                pass  # 预期会失败
            
            # 验证sleep被调用（速率限制）
            mock_sleep.assert_called()
    
    @pytest.mark.openai
    def test_api_key_validation(self, mock_config):
        """测试API密钥验证"""
        # 测试缺少API密钥
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = ""
        mock_config.openai_base_url = "https://api.openai.com/v1"
        
        with patch('src.llm_client.config', mock_config):
            client = LLMClient()
            messages = [{"role": "user", "content": "测试提示"}]
            
            with pytest.raises((ValueError, Exception)):
                client.chat_completion(messages)
    
    @pytest.mark.openai
    def test_model_configuration(self, mock_config):
        """测试模型配置"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_base_url = "https://api.openai.com/v1"
        mock_config.openai_model = "gpt-4"
        
        with patch('src.llm_client.config', mock_config):
            with patch('src.llm_client.OpenAI') as mock_openai_class:
                mock_client = Mock()
                mock_openai_class.return_value = mock_client
                
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "GPT-4响应"
                mock_client.chat.completions.create.return_value = mock_response
                
                client = LLMClient()
                messages = [{"role": "user", "content": "测试提示"}]
                result = client.chat_completion(messages)
                
                assert result == "GPT-4响应"
                # 验证使用了正确的模型
                call_args = mock_client.chat.completions.create.call_args
                assert call_args[1]['model'] == 'gpt-4'