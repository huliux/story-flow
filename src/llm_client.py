"""
统一的大语言模型客户端
支持OpenAI和DeepSeek等多个服务商
"""

import time
from typing import Any, Dict, List, Optional

import openai

from src.config import config

# 检查OpenAI库版本兼容性
try:
    # 新版本 openai >= 1.0
    from openai import OpenAI

    OPENAI_V1 = True
except ImportError:
    # 旧版本 openai < 1.0
    OPENAI_V1 = False


class LLMClient:
    """统一的大语言模型客户端"""

    def __init__(self):
        self.provider = config.llm_provider
        self.client = None
        self.model = None
        self._setup_client()

    def _setup_client(self):
        """根据配置设置客户端"""
        if self.provider == "openai":
            if OPENAI_V1:
                # 新版本API
                self.client = OpenAI(
                    api_key=config.openai_api_key, base_url=config.openai_base_url
                )
            else:
                # 旧版本API
                openai.api_key = config.openai_api_key
                if config.openai_base_url != "https://api.openai.com/v1":
                    openai.api_base = config.openai_base_url
            self.model = config.openai_model

        elif self.provider == "deepseek":
            if OPENAI_V1:
                # 新版本API
                self.client = OpenAI(
                    api_key=config.deepseek_api_key, base_url=config.deepseek_base_url
                )
            else:
                # 旧版本API
                openai.api_key = config.deepseek_api_key
                openai.api_base = config.deepseek_base_url
            self.model = config.deepseek_model
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> str:
        """
        发送聊天完成请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "text"}]
            max_tokens: 最大token数
            temperature: 温度参数
            max_retries: 最大重试次数

        Returns:
            str: 模型响应内容
        """
        if max_tokens is None:
            max_tokens = config.llm_max_tokens
        if temperature is None:
            temperature = config.llm_temperature

        for attempt in range(max_retries):
            try:
                if OPENAI_V1:
                    # 新版本API
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        n=1,
                        stop=None,
                    )
                    return response.choices[0].message.content.strip()
                else:
                    # 旧版本API
                    response = openai.ChatCompletion.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        n=1,
                        stop=None,
                    )
                    return response["choices"][0]["message"]["content"].strip()

            except Exception as e:
                error_msg = str(e)

                # 处理速率限制
                if "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(
                            f"触发速率限制，等待 {config.llm_cooldown_seconds} 秒后重试..."
                        )
                        time.sleep(config.llm_cooldown_seconds)
                        continue

                # 处理API错误
                if "api" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"API错误，等待10秒后重试: {e}")
                        time.sleep(10)
                        continue

                # 其他错误
                if attempt < max_retries - 1:
                    print(f"请求失败，等待10秒后重试: {e}")
                    time.sleep(10)
                else:
                    raise e

    def chat_completion_with_model(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> str:
        """
        使用指定模型发送聊天完成请求

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "text"}]
            model: 指定的模型名称
            max_tokens: 最大token数
            temperature: 温度参数
            max_retries: 最大重试次数

        Returns:
            str: 模型响应内容
        """
        if max_tokens is None:
            max_tokens = config.llm_max_tokens
        if temperature is None:
            temperature = config.llm_temperature

        for attempt in range(max_retries):
            try:
                if OPENAI_V1:
                    # 新版本API
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        n=1,
                        stop=None,
                    )
                    return response.choices[0].message.content.strip()
                else:
                    # 旧版本API
                    response = openai.ChatCompletion.create(
                        model=model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        n=1,
                        stop=None,
                    )
                    return response["choices"][0]["message"]["content"].strip()

            except Exception as e:
                error_msg = str(e)

                # 处理速率限制
                if "rate limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(
                            f"触发速率限制，等待 {config.llm_cooldown_seconds} 秒后重试..."
                        )
                        time.sleep(config.llm_cooldown_seconds)
                        continue

                # 处理API错误
                if "api" in error_msg.lower():
                    if attempt < max_retries - 1:
                        print(f"API错误，等待10秒后重试: {e}")
                        time.sleep(10)
                        continue

                # 其他错误
                if attempt < max_retries - 1:
                    print(f"请求失败，等待10秒后重试: {e}")
                    time.sleep(10)
                else:
                    raise e

    def translate_to_english(self, text: str) -> str:
        """将中文文本翻译为英文"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                # TODO: 手动修复长行 -                 "content": f'Translate the following text to English: "{text}". Ensure the translation is fluent and semantically similar, rather than being a direct translation. You can infer and supplement missing or implicit information from the sentence\'s context, but do not overdo it. Apart from the translated result, do not include any irrelevant content or explanations in your response.',
            },
        ]
        return self.chat_completion(messages)

    def generate_storyboard(self, text: str) -> str:
        """根据文本生成分镜脚本"""
        messages = [
            {
                "role": "system",
                "content": "You are a professional storyboard assistant.",
            },
            {
                "role": "user",
                # TODO: 手动修复长行 -                 "content": "Based on the text \"{text}\", create a storyboard. Don't enumerate the storyboard content, but rather form a single, comprehensive and detailed sentence describing the background scenes, character appearances, and character actions. Note: avoid providing any information that isn't related to the background scenes, character appearances, or character actions!",
            },
        ]
        return self.chat_completion(messages)

    def get_provider_info(self) -> Dict[str, Any]:
        """获取当前提供商信息"""
        if self.provider == "openai":
            return {
                "provider": "OpenAI",
                "model": self.model,
                "api_base": config.openai_base_url,
                "has_api_key": bool(config.openai_api_key),
            }
        elif self.provider == "deepseek":
            return {
                "provider": "DeepSeek",
                "model": self.model,
                "api_base": config.deepseek_base_url,
                "has_api_key": bool(config.deepseek_api_key),
            }
        else:
            return {
                "provider": "Unknown",
                "model": "Unknown",
                "api_base": "Unknown",
                "has_api_key": False,
            }


# 全局LLM客户端实例
llm_client = LLMClient()
