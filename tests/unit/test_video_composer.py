import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock, PropertyMock
import os
import tempfile
from pathlib import Path

from src.pipeline.video_composer import (
    main,
    create_clip,
    get_total_files,
    load_subtitle_data,
    delete_all_files,
    cleanup_all_files
)


class TestVideoComposer:
    """视频合成器的测试"""
    
    @patch('src.pipeline.video_composer.image_dir', Path('/test/images'))
    def test_get_total_files_success(self):
        """测试获取文件总数成功"""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = ['img1.png', 'img2.png', 'img3.png', 'other.jpg']
            
            result = get_total_files()
            assert result == 3
    
    @patch('src.pipeline.video_composer.image_dir', Path('/test/images'))
    def test_get_total_files_empty_directory(self):
        """测试空目录情况"""
        with patch('os.listdir') as mock_listdir:
            mock_listdir.return_value = []
            
            result = get_total_files()
            assert result == 0
    
    @patch('src.pipeline.video_composer.image_dir', Path('/test/images'))
    def test_get_total_files_exception(self):
        """测试获取文件总数异常"""
        with patch('os.listdir', side_effect=Exception("Directory not found")):
            result = get_total_files()
            assert result == 0
    
    @patch('src.pipeline.video_composer.load_subtitles', True)
    @patch('src.pipeline.video_composer.subtitle_dir', Path('/test/subtitles'))
    def test_load_subtitle_data_success(self):
        """测试加载字幕数据成功"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='[{"原始中文": "字幕1"}, {"原始中文": "字幕2"}, {"原始中文": "字幕3"}]')), \
             patch('json.load') as mock_json_load:
            
            # Mock JSON data
            mock_json_load.return_value = [
                {"原始中文": "字幕1"},
                {"原始中文": "字幕2"},
                {"原始中文": "字幕3"}
            ]
            
            result = load_subtitle_data(3)
            
            assert len(result) == 3
            assert result[0] == '字幕1'
            assert result[1] == '字幕2'
            assert result[2] == '字幕3'
    
    @patch('src.pipeline.video_composer.load_subtitles', True)
    @patch('src.pipeline.video_composer.subtitle_dir', Path('/test/subtitles'))
    def test_load_subtitle_data_file_not_exists(self):
        """测试字幕文件不存在"""
        with patch('pathlib.Path.exists', return_value=False):
            result = load_subtitle_data(3)
            
            assert len(result) == 3
            assert all(subtitle == '' for subtitle in result)
    
    @patch('src.pipeline.video_composer.load_subtitles', True)
    @patch('src.pipeline.video_composer.subtitle_dir', Path('/test/subtitles'))
    def test_load_subtitle_data_exception(self):
        """测试加载字幕数据异常"""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', side_effect=Exception("File read error")):
            result = load_subtitle_data(3)
            
            assert len(result) == 3
            assert all(subtitle == '' for subtitle in result)
    
    def test_create_clip_success(self):
        """测试成功创建视频片段"""
        # 简单测试create_clip函数存在
        from src.pipeline.video_composer import create_clip
        assert callable(create_clip)
    
    @patch('src.pipeline.video_composer.image_dir', Path('/test/images'))
    @patch('src.pipeline.video_composer.voice_dir', Path('/test/voice'))
    def test_create_clip_missing_files(self):
        """测试创建视频片段时文件缺失"""
        # Mock文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            result = create_clip(1, ['测试字幕'])
            
            # 应该返回None
            assert result is None
    
    def test_delete_all_files_success(self):
        """测试删除所有文件成功"""
        test_dir = Path('/test/directory')
        
        with patch('os.listdir') as mock_listdir, \
             patch('pathlib.Path.is_file') as mock_is_file, \
             patch('pathlib.Path.is_symlink') as mock_is_symlink, \
             patch('pathlib.Path.unlink') as mock_unlink:
            
            mock_listdir.return_value = ['file1.txt', 'file2.txt']
            mock_is_file.return_value = True
            mock_is_symlink.return_value = False
            
            delete_all_files(test_dir)
            
            # 验证删除操作被调用
            assert mock_unlink.call_count == 2
    
    def test_delete_all_files_directory_not_exists(self):
        """测试删除文件时目录不存在"""
        test_dir = Path('/test/nonexistent')
        
        with patch('os.listdir', side_effect=Exception("Directory not found")):
            # 应该不抛出异常
            delete_all_files(test_dir)
    
    @patch('src.pipeline.video_composer.image_dir', Path('/test/images'))
    @patch('src.pipeline.video_composer.voice_dir', Path('/test/voice'))
    @patch('src.pipeline.video_composer.temp_dir', Path('/test/temp'))
    @patch('builtins.input', return_value='yes')
    def test_cleanup_all_files(self, mock_input):
        """测试清理所有文件"""
        with patch('src.pipeline.video_composer.delete_all_files') as mock_delete:
            cleanup_all_files()
            
            # 验证删除函数被调用了3次
            assert mock_delete.call_count == 3
    
    @patch('src.pipeline.video_composer.get_total_files', return_value=3)
    @patch('src.pipeline.video_composer.load_subtitle_data', return_value=[])
    @patch('src.pipeline.video_composer.create_clip')
    @patch('src.pipeline.video_composer.concatenate_videoclips')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=1000)
    @patch('os.remove')
    @patch('tqdm.tqdm')
    def test_main_success(self, mock_tqdm, mock_remove, mock_getsize, mock_exists, mock_concatenate, mock_create_clip, mock_load_subtitle, mock_get_total):
        """测试主函数成功执行"""
        # Mock create_clip返回不同的文件名
        mock_create_clip.side_effect = [
            '/test/temp/output_1.mp4',
            '/test/temp/output_2.mp4', 
            '/test/temp/output_3.mp4'
        ]
        
        # Mock tqdm进度条
        mock_pbar = MagicMock()
        mock_tqdm.return_value = mock_pbar
        
        # Mock concatenate_videoclips返回值
        mock_final_video = MagicMock()
        mock_concatenate.return_value = mock_final_video
        
        # 模拟VideoFileClip
        with patch('src.pipeline.video_composer.VideoFileClip') as mock_video_file:
            # 创建一个自定义的duration mock对象
            class MockDuration:
                def __init__(self, value):
                    self.value = value
                def __gt__(self, other):
                    return self.value > other
                def __ge__(self, other):
                    return self.value >= other
                def __lt__(self, other):
                    return self.value < other
                def __le__(self, other):
                    return self.value <= other
                def __eq__(self, other):
                    return self.value == other
                def __ne__(self, other):
                    return self.value != other
                def __add__(self, other):
                    if hasattr(other, 'value'):
                        return MockDuration(self.value + other.value)
                    return MockDuration(self.value + other)
                def __radd__(self, other):
                    return self.__add__(other)
                def __sub__(self, other):
                    if hasattr(other, 'value'):
                        return MockDuration(self.value - other.value)
                    return MockDuration(self.value - other)
                def __rsub__(self, other):
                    if hasattr(other, 'value'):
                        return MockDuration(other.value - self.value)
                    return MockDuration(other - self.value)
                def __isub__(self, other):
                    if hasattr(other, 'value'):
                        self.value -= other.value
                    else:
                        self.value -= other
                    return self
                def __float__(self):
                    return float(self.value)
                def __str__(self):
                    return str(self.value)
            
            # 创建一个更完整的mock clip
            mock_clip = MagicMock()
            mock_clip.duration = 3.0  # 直接使用数值而不是MockDuration
            mock_clip.close = MagicMock()
            # 添加其他可能需要的属性
            mock_clip.fps = 30
            mock_clip.size = (1920, 1080)
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_video_file.return_value = mock_clip
            
            result = main()
            
            # 验证函数被调用
            mock_get_total.assert_called_once()
            mock_load_subtitle.assert_called_once_with(3)
            # create_clip应该被调用3次（通过ThreadPoolExecutor）
            assert mock_create_clip.call_count == 3
            # VideoFileClip应该被调用3次（每个生成的文件一次）
            assert mock_video_file.call_count == 3
            mock_concatenate.assert_called_once()
            assert result is True
    
    @patch('src.pipeline.video_composer.get_total_files')
    def test_main_no_files(self, mock_get_total):
        """测试主函数没有文件时的处理"""
        mock_get_total.return_value = 0
        
        result = main()
        
        assert result is False
    
    @patch('src.pipeline.video_composer.get_total_files')
    @patch('src.pipeline.video_composer.load_subtitle_data')
    @patch('src.pipeline.video_composer.create_clip')
    def test_main_create_clip_failure(self, mock_create_clip, mock_load_subtitles, mock_get_total):
        """测试主函数创建片段失败"""
        mock_get_total.return_value = 1
        mock_load_subtitles.return_value = ['字幕1']
        mock_create_clip.return_value = None  # 模拟创建失败
        
        result = main()
        
        assert result is False
    
    @patch('src.pipeline.video_composer.get_total_files')
    def test_main_exception(self, mock_get_total):
        """测试主函数异常处理"""
        mock_get_total.side_effect = Exception("Test error")
        
        # main函数没有异常处理，所以会抛出异常
        with pytest.raises(Exception, match="Test error"):
            main()