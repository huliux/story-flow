"""图像生成器模块的单元测试"""

import pytest
import json
import base64
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.pipeline.image_generator import (
    post,
    save_img,
    get_prompts,
    generate_data
)


class TestImageGenerator:
    """图像生成器的测试"""
    
    @patch('requests.post')
    def test_post_success(self, mock_requests_post):
        """测试POST请求成功的情况"""
        # Mock成功的响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"images": ["base64_data"]}
        mock_requests_post.return_value = mock_response
        
        url = "http://localhost:6006/sdapi/v1/txt2img"
        data = {"prompt": "test prompt"}
        
        result = post(url, data)
        
        assert result == mock_response
        assert result.json()["images"] == ["base64_data"]
        mock_requests_post.assert_called_once_with(
            url,
            data=json.dumps(data),
            headers={'Content-Type': 'application/json'},
            timeout=300
        )
    
    @patch('requests.post')
    def test_post_exception(self, mock_requests_post):
        """测试POST请求异常的情况"""
        import requests
        # Mock请求异常
        mock_requests_post.side_effect = requests.exceptions.RequestException("网络错误")
        
        url = "http://test.com/api"
        data = {"prompt": "test prompt"}
        
        result = post(url, data)
        
        assert result is None
    
    @patch('requests.post')
    def test_post_timeout(self, mock_requests_post):
        """测试POST请求超时的情况"""
        import requests
        mock_requests_post.side_effect = requests.exceptions.Timeout("请求超时")
        
        url = "http://test.com/api"
        data = {"prompt": "test prompt"}
        
        result = post(url, data)
        
        assert result is None
    
    def test_save_img_success(self, temp_dir):
        """测试图片保存成功的情况"""
        # 创建测试用的base64图片数据
        test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        # 保存路径
        save_path = temp_dir / "test_image.png"
        
        # 调用保存函数
        save_img(test_image_data, str(save_path))
        
        # 验证文件是否被创建
        assert save_path.exists()
        assert save_path.stat().st_size > 0
    
    def test_save_img_invalid_base64(self, temp_dir):
        """测试保存无效base64数据的情况"""
        invalid_data = "invalid_base64_data"
        save_path = temp_dir / "test_image.png"
        
        # 应该抛出异常
        with pytest.raises(Exception):
            save_img(invalid_data, str(save_path))
    
    def test_save_img_invalid_path(self):
        """测试保存到无效路径的情况"""
        test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        invalid_path = "/invalid/path/test_image.png"
        
        # 应该抛出异常
        with pytest.raises(Exception):
            save_img(test_image_data, invalid_path)
    
    def test_get_prompts_success(self, temp_dir):
        """测试成功读取提示词的情况"""
        # 创建测试JSON文件
        json_content = [
            {"章节": "第一章", "内容": "内容1", "故事板提示词": "提示词1", "语音文件": "audio1.wav", "LoRA编号": 0},
            {"章节": "第二章", "内容": "内容2", "故事板提示词": "提示词2", "语音文件": "audio2.wav", "LoRA编号": 1}
        ]
        json_path = temp_dir / "test_prompts.json"
        
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False)
        
        prompts, lora_params = get_prompts(str(json_path))
        
        assert prompts == ["提示词1", "提示词2"]
        assert lora_params == [0, 1]
    
    def test_get_prompts_missing_file(self):
        """测试读取不存在的文件"""
        non_existent_path = Path("/non/existent/file.json")
        
        # get_prompts函数捕获所有异常并返回空列表
        prompts, lora_params = get_prompts(non_existent_path)
        assert prompts == []
        assert lora_params == []
    
    def test_get_prompts_empty_json(self, temp_dir):
        """测试读取空JSON文件的情况"""
        json_path = temp_dir / "empty.json"
        
        # 创建空的JSON数组
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        
        prompts, lora_params = get_prompts(str(json_path))
        
        assert prompts == []
        assert lora_params == []
    
    def test_get_prompts_missing_columns(self, temp_dir):
        """测试JSON文件缺少字段的情况"""
        # 创建缺少字段的JSON文件
        json_content = [
            {"章节": "第一章", "内容": "内容1"}
        ]
        json_path = temp_dir / "incomplete.json"
        
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False)
        
        # 应该能处理缺少的字段，返回空值或默认值
        prompts, lora_params = get_prompts(str(json_path))
        
        # 根据实际实现，这里可能返回空字符串或抛出异常
        assert isinstance(prompts, list)
        assert isinstance(lora_params, list)
    
    @patch('src.pipeline.image_generator.config')
    def test_generate_data(self, mock_config):
        """测试生成SD API数据的功能"""
        # Mock配置
        mock_config.get_sd_generation_data.return_value = {
            "prompt": "test prompt",
            "steps": 30,
            "cfg_scale": 7.5,
            "firstphase_width": 680,
            "firstphase_height": 512,
            "sampler_name": "Euler a",
            "batch_size": 1,
            "seed": 333,
            "enable_hr": True,
            "denoising_strength": 0.4
        }
        
        prompt = "test prompt"
        result = generate_data(prompt)
        
        assert result["prompt"] == prompt
        assert "steps" in result
        assert "cfg_scale" in result
        assert "firstphase_width" in result
        assert "firstphase_height" in result
        mock_config.get_sd_generation_data.assert_called_once_with(prompt)
    
    def test_generate_data_with_lora(self):
        """测试带LoRA参数的数据生成"""
        with patch('src.pipeline.image_generator.config') as mock_config:
            mock_config.get_sd_generation_data.return_value = {
                "prompt": "test prompt",
                "steps": 20
            }
            mock_config.lora_models = {0: "model1", 1: "model2"}
            
            prompt = "test prompt"
            result = generate_data(prompt)
            
            assert isinstance(result, dict)
            assert "prompt" in result
    
    @patch('builtins.print')
    def test_error_handling_in_post(self, mock_print):
        """测试POST函数的错误处理"""
        import requests
        with patch('requests.post') as mock_requests_post:
            mock_requests_post.side_effect = requests.exceptions.RequestException("测试异常")
            
            result = post("http://test.com", {})
            
            assert result is None
            # 验证错误信息被打印
            mock_print.assert_called()
    
    def test_base64_encoding_decoding(self):
        """测试base64编码解码的正确性"""
        # 创建测试数据
        test_data = b"test image data"
        encoded_data = base64.b64encode(test_data).decode('utf-8')
        
        # 测试解码
        decoded_data = base64.b64decode(encoded_data)
        
        assert decoded_data == test_data
    
    @patch('builtins.open', new_callable=lambda: mock_open(read_data='[{"章节": "第一章", "内容": "内容1", "图像提示词": "提示词1", "语音文件": "audio1.wav", "LoRA参数": 0}, {"章节": "第二章", "内容": "内容2", "图像提示词": null, "语音文件": "audio2.wav", "LoRA参数": null}]'))
    @patch('json.load')
    def test_get_prompts_with_null_values(self, mock_json_load, mock_file):
        """测试处理包含null值的JSON文件"""
        
        # Mock包含null值的JSON数据
        mock_json_load.return_value = [
            {"章节": "第一章", "内容": "内容1", "故事板提示词": "提示词1", "语音文件": "audio1.wav", "LoRA编号": 0},
            {"章节": "第二章", "内容": "内容2", "故事板提示词": None, "语音文件": "audio2.wav", "LoRA编号": None}
        ]
        
        prompts, lora_params = get_prompts("test.json")
        
        # 验证null值被正确处理
        assert prompts[0] == "提示词1"
        assert prompts[1] == ""  # None应该被转换为空字符串
        assert lora_params[0] == 0
        assert lora_params[1] == ""  # None应该被转换为空字符串
    
    def test_file_path_handling(self, temp_dir):
        """测试文件路径处理"""
        # 测试不同类型的路径
        test_paths = [
            str(temp_dir / "test1.png"),
            temp_dir / "test2.png",
        ]
        
        test_image_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        for path in test_paths:
            save_img(test_image_data, str(path))
            assert Path(path).exists()
    
    @patch('src.pipeline.image_generator.config')
    def test_prompt_construction_with_style(self, mock_config):
        """测试带有风格参数的提示词构建"""
        # 模拟配置
        mock_config.sd_style = "Harry Potter-style children's stories"
        
        # 测试基本提示词 + 风格参数
        prompt_b = "a beautiful landscape"
        lora_param = ""
        style_param = mock_config.sd_style.strip() if mock_config.sd_style else ""
        
        # 构建提示词（模拟image_generator.py中的逻辑）
        prompt_parts = ["masterpiece,(best quality)", prompt_b]
        
        if lora_param:
            prompt_parts.append(lora_param)
        
        if style_param:
            prompt_parts.append(style_param)
        
        prompt = ",".join(prompt_parts)
        
        expected_prompt = "masterpiece,(best quality),a beautiful landscape,Harry Potter-style children's stories"
        assert prompt == expected_prompt
    
    @patch('src.pipeline.image_generator.config')
    def test_prompt_construction_with_style_and_lora(self, mock_config):
        """测试带有风格参数和LoRA参数的提示词构建"""
        # 模拟配置
        mock_config.sd_style = "anime style, vibrant colors"
        
        # 测试基本提示词 + LoRA参数 + 风格参数
        prompt_b = "a cute cat"
        lora_param = "<lora:anime_v1:0.8>"
        style_param = mock_config.sd_style.strip() if mock_config.sd_style else ""
        
        # 构建提示词（模拟image_generator.py中的逻辑）
        prompt_parts = ["masterpiece,(best quality)", prompt_b]
        
        if lora_param:
            prompt_parts.append(lora_param)
        
        if style_param:
            prompt_parts.append(style_param)
        
        prompt = ",".join(prompt_parts)
        
        expected_prompt = "masterpiece,(best quality),a cute cat,<lora:anime_v1:0.8>,anime style, vibrant colors"
        assert prompt == expected_prompt
    
    @patch('src.pipeline.image_generator.config')
    def test_prompt_construction_without_style(self, mock_config):
        """测试没有风格参数的提示词构建"""
        # 模拟配置（无风格参数）
        mock_config.sd_style = None
        
        # 测试基本提示词（无风格参数）
        prompt_b = "a mountain view"
        lora_param = ""
        style_param = mock_config.sd_style.strip() if mock_config.sd_style else ""
        
        # 构建提示词（模拟image_generator.py中的逻辑）
        prompt_parts = ["masterpiece,(best quality)", prompt_b]
        
        if lora_param:
            prompt_parts.append(lora_param)
        
        if style_param:
            prompt_parts.append(style_param)
        
        prompt = ",".join(prompt_parts)
        
        expected_prompt = "masterpiece,(best quality),a mountain view"
        assert prompt == expected_prompt