#!/usr/bin/env python3
"""
测试大语言模型服务
支持OpenAI和DeepSeek的功能测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config
from src.llm_client import llm_client

def test_provider_info():
    """测试服务商信息"""
    print("🔍 测试服务商信息...")
    info = llm_client.get_provider_info()
    print(f"✅ 服务商: {info['provider']}")
    print(f"✅ 模型: {info['model']}")
    print(f"✅ API地址: {info['api_base']}")
    print(f"✅ API密钥: {'已配置' if info['has_api_key'] else '未配置'}")
    return info['has_api_key']

def test_translation():
    """测试文本翻译功能"""
    print("\n🔤 测试文本翻译...")
    test_text = "这是一个测试文本，用于验证AI翻译功能。"
    
    try:
        result = llm_client.translate_to_english(test_text)
        print(f"原文: {test_text}")
        print(f"译文: {result}")
        return True
    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        return False

def test_storyboard():
    """测试分镜脚本生成"""
    print("\n🎬 测试分镜脚本生成...")
    test_text = "一个年轻的女孩在花园里散步，她穿着白色的连衣裙。"
    
    try:
        messages = [
            {"role": "system", "content": "You are a professional storyboard assistant."},
            {"role": "user", "content": f"Based on the text \"{test_text}\", create a storyboard. Create a detailed description for image generation."}
        ]
        result = llm_client.chat_completion(messages)
        print(f"原文: {test_text}")
        print(f"分镜: {result}")
        return True
    except Exception as e:
        print(f"❌ 分镜生成失败: {e}")
        return False

def test_api_limits():
    """测试API限制和重试机制"""
    print("\n⏱️ 测试API配置...")
    print(f"最大令牌数: {config.llm_max_tokens}")
    print(f"温度参数: {config.llm_temperature}")
    print(f"冷却时间: {config.llm_cooldown_seconds}秒")
    print(f"最大请求数: {config.llm_max_requests}")

def main():
    """主测试函数"""
    print("🚀 大语言模型服务测试")
    print("=" * 50)
    
    # 测试配置
    print(f"当前LLM服务商: {config.llm_provider}")
    
    # 测试服务商信息
    has_key = test_provider_info()
    if not has_key:
        print("\n❌ 测试终止: 未配置API密钥")
        if config.llm_provider == 'openai':
            print("请在.env中设置: OPENAI_API_KEY")
        elif config.llm_provider == 'deepseek':
            print("请在.env中设置: DEEPSEEK_API_KEY")
        sys.exit(1)
    
    # 测试API配置
    test_api_limits()
    
    # 功能测试
    print("\n" + "=" * 50)
    print("🧪 功能测试")
    
    translation_ok = test_translation()
    storyboard_ok = test_storyboard()
    
    # 测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果")
    
    if translation_ok and storyboard_ok:
        print("🎉 所有测试通过！系统可以正常使用。")
        return True
    else:
        print("❌ 部分测试失败，请检查配置和网络连接。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
