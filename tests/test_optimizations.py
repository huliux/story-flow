import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

# 导入要测试的模块
try:
    from src.liblib.async_service import AsyncLiblibService, AsyncGenerationResult
    from src.liblib.monitoring import performance_monitor
    from src.liblib.cache_manager import cache_manager
except ImportError:
    # 如果导入失败，跳过测试
    pytest.skip("LiblibAI modules not available", allow_module_level=True)

@pytest.fixture
def mock_config():
    class MockConfig:
        access_key = "test_key"
        secret_key = "test_secret"
        api_base_url = "https://api.test.com"
        max_concurrent_requests = 3
        timeout = 30
    return MockConfig()

@pytest.mark.asyncio
async def test_async_single_generation(mock_config):
    """测试异步单张图片生成"""
    async with AsyncLiblibService(mock_config) as service:
        with patch.object(service, '_submit_generation_task', new_callable=AsyncMock) as mock_submit:
            with patch.object(service, '_wait_for_completion_async', new_callable=AsyncMock) as mock_wait:
                with patch.object(service, '_download_image_async', new_callable=AsyncMock) as mock_download:
                    
                    mock_submit.return_value = "test_task_id"
                    mock_wait.return_value = {'status': 'completed', 'image_url': 'http://test.com/image.jpg'}
                    mock_download.return_value = Path('/test/image.jpg')
                    
                    result = await service.generate_single_async("test prompt")
                    
                    assert result.success is True
                    assert result.image_path == Path('/test/image.jpg')
                    assert result.generation_time > 0
                    
                    mock_submit.assert_called_once()
                    mock_wait.assert_called_once_with("test_task_id")
                    mock_download.assert_called_once()

def test_performance_monitoring():
    """测试性能监控"""
    performance_monitor.reset_metrics()
    
    # 模拟函数调用
    performance_monitor.record_call("test_function", 1.5, True)
    performance_monitor.record_call("test_function", 2.0, True)
    performance_monitor.record_call("test_function", 1.0, False)
    
    metrics = performance_monitor.get_metrics("test_function")
    
    assert metrics['total_calls'] == 3
    assert metrics['success_rate'] == 2/3
    assert metrics['error_rate'] == 1/3
    assert metrics['avg_time'] == (1.5 + 2.0 + 1.0) / 3

def test_cache_manager():
    """测试缓存管理器"""
    @cache_manager.cache_status(ttl=30)
    def test_function(x):
        return x * 2
    
    # 第一次调用
    result1 = test_function(5)
    assert result1 == 10
    
    # 第二次调用应该从缓存获取
    result2 = test_function(5)
    assert result2 == 10
    
    # 验证缓存统计
    stats = cache_manager.get_cache_stats()
    assert stats['status_cache']['size'] > 0
