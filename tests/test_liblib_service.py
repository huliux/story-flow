#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiblibAI服务单元测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
from datetime import datetime

# 添加项目根目录到Python路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline.liblib_service import (
    LiblibService, LiblibConfig, LiblibResult, GenerateStatus
)


class TestLiblibService(unittest.TestCase):
    """LiblibAI服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = LiblibConfig(
            access_key="test_access_key",
            secret_key="test_secret_key",
            api_base_url="https://test.liblib.art",
            timeout=30,
            max_retries=2,
            retry_delay=1
        )
        self.service = LiblibService(self.config)
    
    def test_config_initialization(self):
        """测试配置初始化"""
        self.assertEqual(self.config.access_key, "test_access_key")
        self.assertEqual(self.config.secret_key, "test_secret_key")
        self.assertEqual(self.config.api_base_url, "https://test.liblib.art")
        self.assertEqual(self.config.timeout, 30)
        self.assertEqual(self.config.max_retries, 2)
        self.assertEqual(self.config.retry_delay, 1)
    
    def test_generate_signature(self):
        """测试签名生成"""
        params = {"prompt": "test prompt", "steps": 20}
        timestamp = "1234567890"
        
        signature = self.service._generate_signature(params, timestamp)
        
        # 验证签名不为空且为字符串
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)
    
    @patch('requests.post')
    def test_make_request_success(self, mock_post):
        """测试成功的API请求"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {"task_id": "test_task_id"}
        }
        mock_post.return_value = mock_response
        
        result = self.service._make_request("/test", {"test": "data"})
        
        self.assertEqual(result["code"], 0)
        self.assertEqual(result["data"]["task_id"], "test_task_id")
    
    @patch('requests.post')
    def test_make_request_failure(self, mock_post):
        """测试失败的API请求"""
        # 模拟失败响应
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "code": 1001,
            "message": "Invalid parameters"
        }
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.service._make_request("/test", {"test": "data"})
        
        self.assertIn("API请求失败", str(context.exception))
    
    @patch('requests.post')
    def test_make_request_retry(self, mock_post):
        """测试请求重试机制"""
        # 第一次请求失败，第二次成功
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = Exception("Server Error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {"task_id": "test_task_id"}
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        result = self.service._make_request("/test", {"test": "data"})
        
        self.assertEqual(result["code"], 0)
        self.assertEqual(mock_post.call_count, 2)
    
    @patch.object(LiblibService, '_make_request')
    def test_text_to_image_success(self, mock_request):
        """测试文生图成功"""
        mock_request.return_value = {
            "code": 0,
            "message": "success",
            "data": {"task_id": "test_task_123"}
        }
        
        params = {
            "prompt": "a beautiful landscape",
            "steps": 20,
            "width": 512,
            "height": 512
        }
        
        task_id = self.service.text_to_image(params)
        
        self.assertEqual(task_id, "test_task_123")
        mock_request.assert_called_once()
    
    @patch.object(LiblibService, '_make_request')
    def test_get_generation_result_success(self, mock_request):
        """测试获取生成结果成功"""
        mock_request.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "generateStatus": 2,  # 成功
                "auditStatus": 1,     # 通过审核
                "imageUrls": ["https://example.com/image1.jpg"],
                "generateParams": {"prompt": "test", "steps": 20}
            }
        }
        
        result = self.service.get_generation_result("test_task_123")
        
        self.assertIsInstance(result, LiblibResult)
        self.assertEqual(result.status, GenerateStatus.SUCCESS)
        self.assertEqual(len(result.image_urls), 1)
        self.assertEqual(result.image_urls[0], "https://example.com/image1.jpg")
    
    @patch.object(LiblibService, '_make_request')
    def test_get_generation_result_processing(self, mock_request):
        """测试获取生成结果处理中"""
        mock_request.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "generateStatus": 1,  # 处理中
                "auditStatus": 0,     # 审核中
                "imageUrls": [],
                "generateParams": {"prompt": "test", "steps": 20}
            }
        }
        
        result = self.service.get_generation_result("test_task_123")
        
        self.assertIsInstance(result, LiblibResult)
        self.assertEqual(result.status, GenerateStatus.PROCESSING)
        self.assertEqual(len(result.image_urls), 0)
    
    @patch.object(LiblibService, '_make_request')
    def test_get_generation_result_failed(self, mock_request):
        """测试获取生成结果失败"""
        mock_request.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "generateStatus": 3,  # 失败
                "auditStatus": 1,     # 通过审核
                "imageUrls": [],
                "generateParams": {"prompt": "test", "steps": 20}
            }
        }
        
        result = self.service.get_generation_result("test_task_123")
        
        self.assertIsInstance(result, LiblibResult)
        self.assertEqual(result.status, GenerateStatus.FAILED)
        self.assertEqual(len(result.image_urls), 0)
    
    def test_liblib_result_initialization(self):
        """测试LiblibResult初始化"""
        result = LiblibResult(
            status=GenerateStatus.SUCCESS,
            image_urls=["https://example.com/image1.jpg"],
            params={"prompt": "test", "steps": 20},
            audit_status=1
        )
        
        self.assertEqual(result.status, GenerateStatus.SUCCESS)
        self.assertEqual(len(result.image_urls), 1)
        self.assertEqual(result.image_urls[0], "https://example.com/image1.jpg")
        self.assertEqual(result.params["prompt"], "test")
        self.assertEqual(result.audit_status, 1)
    
    def test_generate_status_enum(self):
        """测试生成状态枚举"""
        self.assertEqual(GenerateStatus.PROCESSING.value, 1)
        self.assertEqual(GenerateStatus.SUCCESS.value, 2)
        self.assertEqual(GenerateStatus.FAILED.value, 3)


if __name__ == '__main__':
    unittest.main()