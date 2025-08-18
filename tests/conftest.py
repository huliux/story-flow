"""pytest配置和共享fixtures

这个文件包含了所有测试共享的配置和fixtures。
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """返回项目根目录路径"""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir():
    """返回测试数据目录路径"""
    return Path(__file__).parent / "fixtures" / "data"


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 清理临时目录
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    config = Mock()
    config.project_root = project_root
    config.input_dir = project_root / "data" / "input"
    config.output_dir_txt = project_root / "data" / "output" / "processed"
    config.output_dir_image = project_root / "data" / "output" / "images"
    config.output_dir_voice = project_root / "data" / "output" / "audio"
    config.output_dir_video = project_root / "data" / "output" / "videos"
    config.output_dir_temp = project_root / "data" / "temp"
    config.input_md_file = config.input_dir / "input.md"
    config.output_csv_file = config.output_dir_txt / "chapters.csv"
    config.min_sentence_length = 10
    config.max_workers_translation = 2
    config.llm_provider = "openai"
    config.openai_model = "gpt-3.5-turbo"
    config.llm_max_tokens = 1000
    config.llm_temperature = 0.7
    config.sd_api_url = "http://localhost:7860"
    config.azure_speech_key = "test_key"
    config.azure_speech_region = "eastus"
    config.azure_voice_name = "zh-CN-XiaoxiaoNeural"
    return config


@pytest.fixture
def mock_llm_client():
    """模拟LLM客户端"""
    client = Mock()
    client.get_provider_info.return_value = {
        'provider': 'openai',
        'model': 'gpt-3.5-turbo',
        'has_api_key': True
    }
    client.generate_text.return_value = "测试生成的文本"
    return client


@pytest.fixture
def sample_text():
    """示例文本数据"""
    return """# 第一章 开始

这是一个测试故事的开始。主人公小明走在回家的路上，心情很好。

突然，他看到了一只小猫。小猫很可爱，毛色是橘色的。

# 第二章 遇见

小明决定帮助这只小猫。他轻轻地走向小猫，伸出手来。

小猫似乎不害怕，反而主动靠近了小明。
"""


@pytest.fixture
def sample_chapters_data():
    """示例章节数据"""
    return [
        {
            "chapter": "第一章 开始",
            "content": "这是一个测试故事的开始。主人公小明走在回家的路上，心情很好。",
            "image_prompt": "A young man walking on a street, happy mood, anime style",
            "lora_param": 0
        },
        {
            "chapter": "第一章 开始", 
            "content": "突然，他看到了一只小猫。小猫很可爱，毛色是橘色的。",
            "image_prompt": "A cute orange cat, anime style",
            "lora_param": 0
        }
    ]


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """设置测试环境"""
    # 设置测试环境变量
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test_key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
    monkeypatch.setenv("AZURE_SPEECH_KEY", "test_key")
    
    # 禁用网络请求
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"success": True}
        yield


@pytest.fixture
def no_network(monkeypatch):
    """禁用网络访问的fixture"""
    def mock_requests(*args, **kwargs):
        raise ConnectionError("网络访问在测试中被禁用")
    
    monkeypatch.setattr("requests.get", mock_requests)
    monkeypatch.setattr("requests.post", mock_requests)
    monkeypatch.setattr("requests.put", mock_requests)
    monkeypatch.setattr("requests.delete", mock_requests)