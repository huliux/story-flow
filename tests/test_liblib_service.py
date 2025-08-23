#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiblibAI服务单元测试
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import time
import requests
from datetime import datetime

# 添加项目根目录到Python路径
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.image.liblib_service import (
    LiblibService, LiblibConfig, GenerateResult, GenerateStatus
)
from src.config import Config


class TestLiblibService(unittest.TestCase):
    """LiblibAI服务测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = LiblibConfig(
            access_key="test_access_key",
            secret_key="test_secret_key",
            base_url="https://test.liblib.art",
            timeout=30,
            max_retries=2,
            retry_delay=1
        )
        self.app_config = Config()
        self.service = LiblibService(self.config, self.app_config)
    
    def test_config_initialization(self):
        """测试配置初始化"""
        self.assertEqual(self.config.access_key, "test_access_key")
        self.assertEqual(self.config.secret_key, "test_secret_key")
        self.assertEqual(self.config.base_url, "https://test.liblib.art")
        self.assertEqual(self.config.timeout, 30)
        self.assertEqual(self.config.max_retries, 2)
        self.assertEqual(self.config.retry_delay, 1)
    
    def test_generate_signature(self):
        """测试签名生成"""
        uri = "/api/v1/f1/text-to-image"
        
        signature_headers = self.service._generate_signature(uri)
        
        # 验证签名头部包含必要字段
        self.assertIn('Timestamp', signature_headers)
        self.assertIn('Signature', signature_headers)
        self.assertIsInstance(signature_headers['Signature'], str)
        self.assertGreater(len(signature_headers['Signature']), 0)
    
    @patch.object(requests.Session, 'post')
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
        
        result = self.service._make_request("POST", "/test", {"test": "data"})
        
        self.assertEqual(result["code"], 0)
        self.assertEqual(result["data"]["task_id"], "test_task_id")
    
    @patch.object(requests.Session, 'post')
    def test_make_request_failure(self, mock_post):
        """测试失败的API请求"""
        # 模拟失败响应
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad Request"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.service._make_request("POST", "/test", {"test": "data"})
        
        self.assertIn("API请求失败", str(context.exception))
    
    @patch.object(requests.Session, 'post')
    def test_make_request_retry(self, mock_post):
        """测试API请求重试机制"""
        # 第一次请求失败，第二次成功
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.json.return_value = {"error": "Server Error"}
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "code": 0,
            "message": "success",
            "data": {"task_id": "test_task_id"}
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        result = self.service._make_request("POST", "/test", {"test": "data"})
        
        self.assertEqual(result["code"], 0)
        self.assertEqual(mock_post.call_count, 2)
    
    @patch.object(LiblibService, '_make_request')
    def test_f1_text_to_image_success(self, mock_request):
        """测试F1文生图成功"""
        from src.services.image.liblib_service import F1GenerationParams
        
        mock_request.return_value = {
            "code": 0,
            "message": "success",
            "data": {
                "generateUuid": "test_task_123",
                "generateStatus": 1,
                "progress": 0,
                "message": "任务已提交",
                "pointsCost": 10,
                "accountBalance": 100,
                "images": []
            }
        }
        
        params = F1GenerationParams(
            prompt="a beautiful landscape",
            steps=20,
            width=512,
            height=512
        )
        
        result = self.service.f1_text_to_image(params)
        
        self.assertIsInstance(result, GenerateResult)
        self.assertEqual(result.generate_uuid, "test_task_123")
        mock_request.assert_called_once()
    

    
    def test_generate_result_initialization(self):
        """测试GenerateResult初始化"""
        result = GenerateResult(
            generate_uuid="test-uuid",
            status=GenerateStatus.SUCCESS,
            progress=100.0,
            message="生成成功",
            points_cost=10,
            account_balance=100,
            images=[{"url": "https://example.com/image1.jpg"}]
        )
        
        self.assertEqual(result.status, GenerateStatus.SUCCESS)
        self.assertEqual(len(result.images), 1)
        self.assertEqual(result.images[0]["url"], "https://example.com/image1.jpg")
        self.assertEqual(result.generate_uuid, "test-uuid")
        self.assertEqual(result.progress, 100.0)
    
    def test_generate_status_enum(self):
        """测试生成状态枚举"""
        self.assertEqual(GenerateStatus.PENDING.value, 1)
        self.assertEqual(GenerateStatus.PROCESSING.value, 2)
        self.assertEqual(GenerateStatus.SUCCESS.value, 5)
        self.assertEqual(GenerateStatus.FAILED.value, 6)
        self.assertEqual(GenerateStatus.TIMEOUT.value, 7)


if __name__ == '__main__':
    unittest.main()