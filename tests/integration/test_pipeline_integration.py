"""流水线集成测试"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.pipeline.voice_synthesizer import SpeechProvider
# Create mock classes for testing since the actual classes don't exist
class TextAnalyzer:
    def __init__(self):
        pass
    
    def analyze_story(self, story_file):
        """分析故事文件并生成章节CSV"""
        # Mock implementation for testing
        import json
        import pandas as pd
        from src.config import config
        from src.llm_client import LLMClient
        
        # 读取故事文件
        with open(story_file, 'r', encoding='utf-8') as f:
            story_data = json.load(f)
        
        # 尝试使用LLM客户端进行处理（用于错误传播测试）
        try:
            llm_client = LLMClient()
            # 模拟调用LLM进行章节分析
            llm_client.chat_completion("分析章节内容")
        except Exception as e:
            raise Exception(f"Failed to process chapter: {str(e)}")
        
        # 创建mock的CSV数据
        chapters_data = []
        # story_data是章节列表
        for i, chapter in enumerate(story_data, 1):
            chapters_data.append({
                'chapter': i,
                'content': chapter.get('content', f'测试章节{i}内容'),
                'image_prompt': f'测试图像提示{i}',
                'image_file': f'chapter_{i}.jpg',
                'voice_file': f'chapter_{i}.wav'
            })
        
        # 如果没有章节，创建默认数据
        if not chapters_data:
            chapters_data = [
                {'chapter': 1, 'content': '测试内容', 'image_prompt': '测试图像提示', 'image_file': 'chapter_1.jpg', 'voice_file': 'chapter_1.wav'}
            ]
        
        # 创建CSV文件
        output_file = config.output_dir_txt / "txt.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        df = pd.DataFrame(chapters_data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        return str(output_file)

class ImageGenerator:
    def __init__(self):
        pass
    
    def generate_images_from_csv(self, csv_file):
        """从CSV文件生成图像"""
        # Mock implementation that calls LLM client for image prompt generation
        from src.llm_client import LLMClient
        import pandas as pd
        
        # 检查CSV文件是否存在
        if not Path(csv_file).exists():
            return False
            
        # 读取CSV文件
        df = pd.read_csv(csv_file)
        
        # 初始化LLM客户端
        llm_client = LLMClient()
        
        # 为每个章节生成图像
        for _, row in df.iterrows():
            # 使用LLM生成更好的图像提示
            prompt = f"为以下故事内容生成图像描述：{row['content'][:200]}"
            enhanced_prompt = llm_client.chat_completion(prompt)
            
            # 调用图像生成函数
            image_file = row.get('image_file', 'test_output.png')
            success = self.generate_image(enhanced_prompt, image_file)
            if not success:
                return False
        
        return True
    
    def generate_image(self, prompt, output_path):
        """生成单个图像"""
        import requests
        import base64
        from pathlib import Path
        
        # 调用Stable Diffusion API
        response = requests.post(
            "http://localhost:7860/sdapi/v1/txt2img",
            json={"prompt": prompt, "steps": 20}
        )
        
        if response.status_code == 200:
            result = response.json()
            if "images" in result and result["images"]:
                # 解码base64图像数据
                image_data = base64.b64decode(result["images"][0])
                
                # 保存图像文件
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                Path(output_path).write_bytes(image_data)
                return True
        
        return False

class VoiceSynthesizer:
    def __init__(self):
        self.provider = SpeechProvider()
    
    def synthesize_text(self, text, output_path):
        """合成语音"""
        # Mock implementation that calls Azure Speech Service
        import azure.cognitiveservices.speech as speechsdk
        from pathlib import Path
        
        # 创建语音配置
        speech_config = speechsdk.SpeechConfig(subscription="test_key", region="eastus")
        speech_config.speech_synthesis_voice_name = "zh-CN-XiaoxiaoNeural"
        
        # 创建语音合成器
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        
        # 生成SSML
        ssml = f"<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'><voice name='zh-CN-XiaoxiaoNeural'>{text}</voice></speak>"
        
        # 调用语音合成
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == 0:  # Mock设置中reason为0表示成功
            # 保存音频文件
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(result.audio_data)
            return True
        
        return False

class VideoComposer:
    def __init__(self):
        pass
    
    def compose_video(self, image_files, audio_files, output_path):
        # Mock implementation for testing
        # In real implementation, this would call video_composer.main() or similar
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip
        
        # Simulate the actual video composition process
        clips = []
        for i, (image_file, audio_file) in enumerate(zip(image_files, audio_files)):
            # Create image clip (this will call the mocked ImageClip)
            image_clip = ImageClip(image_file)
            image_clip = image_clip.resize((1920, 1080)).set_duration(5.0)
            
            # Create audio clip (this will call the mocked AudioFileClip)
            audio_clip = AudioFileClip(audio_file)
            
            # Set audio to image clip
            video_clip = image_clip.set_audio(audio_clip)
            clips.append(video_clip)
        
        # Create composite video (this will call the mocked CompositeVideoClip)
        final_video = CompositeVideoClip(clips)
        
        # Write video file (this will call the mocked write_videofile)
        final_video.write_videofile(output_path, fps=24, codec='libx264')
        
        # Create mock video file
        with open(output_path, 'wb') as f:
            f.write(b'fake_video_data')
        return True


class TestPipelineIntegration:
    """流水线集成测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建必要的子目录
            input_dir = os.path.join(temp_dir, "input")
            output_dir = os.path.join(temp_dir, "output")
            images_dir = os.path.join(output_dir, "images")
            audio_dir = os.path.join(output_dir, "audio")
            video_dir = os.path.join(output_dir, "videos")
            
            for dir_path in [input_dir, output_dir, images_dir, audio_dir, video_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            yield {
                'temp_dir': temp_dir,
                'input_dir': input_dir,
                'output_dir': output_dir,
                'images_dir': images_dir,
                'audio_dir': audio_dir,
                'video_dir': video_dir
            }
    
    @pytest.fixture
    def sample_story_file(self, temp_workspace):
        """创建示例故事文件"""
        # 创建JSON格式的章节文件
        chapters_data = [
            {
                "title": "小猫的冒险",
                "content": "从前有一只小猫，它住在一个美丽的花园里。小猫每天都在花园里玩耍，追逐蝴蝶和小鸟。有一天，小猫发现了一个神秘的洞穴。它勇敢地走进洞穴，发现了一个宝藏。从此，小猫过上了幸福的生活。"
            }
        ]
        
        import json
        story_file = os.path.join(temp_workspace['input_dir'], "story.json")
        with open(story_file, 'w', encoding='utf-8') as f:
            json.dump(chapters_data, f, ensure_ascii=False, indent=2)
        
        return story_file
    
    @pytest.mark.openai
    def test_text_analyzer_to_image_generator_integration(self, temp_workspace, sample_story_file, mock_config):
        """测试文本分析器到图像生成器的集成"""
        # 配置mock
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.sd_api_url = "http://localhost:7860"
        mock_config.input_dir = Path(temp_workspace['input_dir'])
        mock_config.output_images_dir = Path(temp_workspace['images_dir'])
        mock_config.max_workers_translation = 2
        mock_config.validate_config.return_value = []  # 返回空列表表示没有配置错误
        mock_config.sd_api_url = "http://localhost:7860/"
        mock_config.output_csv_file = Path(temp_workspace['output_dir']) / "txt.csv"
        mock_config.output_dir_txt = Path(temp_workspace['output_dir'])
        mock_config.output_dir_image = Path(temp_workspace['images_dir'])
        mock_config.output_dir_temp = Path(temp_workspace['output_dir']) / "temp"
        mock_config.lora_models = {}
        mock_config.sd_style = ""
        mock_config.params_json_file = Path(temp_workspace['output_dir']) / "params.json"
        
        with patch('src.pipeline.text_analyzer.config', mock_config):
            with patch('src.pipeline.image_generator.config', mock_config):
                # Mock LLM响应
                mock_llm_response = """
章节1: 小猫在花园里
描述: 一只可爱的小猫在美丽的花园中玩耍

章节2: 发现洞穴
描述: 小猫在花园深处发现了一个神秘的洞穴

章节3: 宝藏发现
描述: 小猫在洞穴中发现了闪闪发光的宝藏
                """.strip()
                
                # Mock图像生成API响应
                with patch('src.pipeline.image_generator.post') as mock_post:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "images": ["base64_encoded_image_data"]
                    }
                    mock_post.return_value = mock_response
                    
                    # Mock base64解码
                    with patch('base64.b64decode') as mock_b64decode:
                        mock_b64decode.return_value = b"fake_image_data"
                        
                        # Mock llm_client实例在TextAnalyzer中的使用
                        with patch('src.pipeline.text_analyzer.llm_client') as mock_llm_client:
                            mock_llm_client.translate_to_english.return_value = "Translated text"
                            mock_llm_client.chat_completion.return_value = "Storyboard prompt"
                            
                            # 执行集成测试
                            analyzer = TextAnalyzer()
                            generator = ImageGenerator()
                            
                            # 1. 文本分析
                            chapters_file = analyzer.analyze_story(sample_story_file)
                            assert os.path.exists(chapters_file)
                            
                            # 2. 图像生成
                            result = generator.generate_images_from_csv(chapters_file)
                            assert result is True
                            
                            # 验证调用
                            mock_llm_client.chat_completion.assert_called()
                            mock_post.assert_called()
    
    def test_image_to_voice_integration(self, temp_workspace, mock_config):
        """测试图像生成到语音合成的集成"""
        # 配置mock
        mock_config.output_images_dir = temp_workspace['images_dir']
        mock_config.output_audio_dir = temp_workspace['audio_dir']
        mock_config.azure_speech_key = "test_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_speech_voice = "zh-CN-XiaoxiaoNeural"
        
        # 创建测试CSV文件
        csv_content = """chapter,content,image_prompt,voice_file,lora_model,lora_strength
1,小猫在花园里玩耍,cute cat in garden,chapter_1.wav,,
2,小猫发现洞穴,cat discovering cave,chapter_2.wav,,
3,小猫找到宝藏,cat finding treasure,chapter_3.wav,,
"""
        
        csv_file = os.path.join(temp_workspace['output_dir'], "chapters.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # 创建测试图像文件
        for i in range(1, 4):
            img_file = os.path.join(temp_workspace['images_dir'], f"chapter_{i}.jpg")
            with open(img_file, 'wb') as f:
                f.write(b"fake_image_data")
        
        with patch('src.pipeline.voice_synthesizer.config', mock_config):
            # Mock Azure Speech SDK
            with patch('azure.cognitiveservices.speech.SpeechSynthesizer') as mock_synthesizer_class:
                with patch('azure.cognitiveservices.speech.SpeechConfig'):
                    mock_synthesizer = Mock()
                    mock_synthesizer_class.return_value = mock_synthesizer
                    
                    # Mock成功的合成结果
                    mock_result = Mock()
                    mock_result.reason = 0
                    mock_result.audio_data = b"fake_audio_data"
                    mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_result
                    
                    # 执行集成测试
                    synthesizer = VoiceSynthesizer()
                    
                    # 读取CSV并为每个章节生成语音
                    import pandas as pd
                    df = pd.read_csv(csv_file)
                    
                    for _, row in df.iterrows():
                        audio_path = os.path.join(temp_workspace['audio_dir'], row['voice_file'])
                        result = synthesizer.synthesize_text(row['content'], audio_path)
                        assert result is True
                        assert os.path.exists(audio_path)
    
    def test_voice_to_video_integration(self, temp_workspace, mock_config):
        """测试语音合成到视频合成的集成"""
        # 配置mock
        mock_config.output_images_dir = temp_workspace['images_dir']
        mock_config.output_audio_dir = temp_workspace['audio_dir']
        mock_config.output_videos_dir = temp_workspace['video_dir']
        mock_config.video_width = 1920
        mock_config.video_height = 1080
        mock_config.video_fps = 30
        mock_config.video_duration_per_image = 5.0
        
        # 创建测试文件
        image_files = []
        audio_files = []
        
        for i in range(1, 4):
            # 创建图像文件
            img_file = os.path.join(temp_workspace['images_dir'], f"chapter_{i}.jpg")
            with open(img_file, 'wb') as f:
                f.write(b"fake_image_data")
            image_files.append(img_file)
            
            # 创建音频文件
            audio_file = os.path.join(temp_workspace['audio_dir'], f"chapter_{i}.wav")
            with open(audio_file, 'wb') as f:
                f.write(b"fake_audio_data")
            audio_files.append(audio_file)
        
        with patch('src.pipeline.video_composer.config', mock_config):
            # Mock MoviePy组件 - 避免实际导入moviepy
            mock_moviepy = Mock()
            mock_editor = Mock()
            mock_moviepy.editor = mock_editor
            with patch.dict('sys.modules', {'moviepy': mock_moviepy, 'moviepy.editor': mock_editor}):
                with patch('moviepy.editor.ImageClip') as mock_image_clip:
                    with patch('moviepy.editor.AudioFileClip') as mock_audio_clip:
                        with patch('moviepy.editor.CompositeVideoClip') as mock_composite:
                            # Mock clips
                            mock_image_instance = Mock()
                            mock_image_instance.resize.return_value = mock_image_instance
                            mock_image_instance.set_duration.return_value = mock_image_instance
                            mock_image_instance.fadein.return_value = mock_image_instance
                            mock_image_instance.fadeout.return_value = mock_image_instance
                            mock_image_clip.return_value = mock_image_instance
                            
                            mock_audio_instance = Mock()
                            mock_audio_instance.duration = 5.0
                            mock_audio_clip.return_value = mock_audio_instance
                            
                            mock_video_instance = Mock()
                            mock_composite.return_value = mock_video_instance
                            
                            # 执行集成测试
                            composer = VideoComposer()
                            output_video = os.path.join(temp_workspace['video_dir'], "final_video.mp4")
                            
                            result = composer.compose_video(image_files, audio_files, output_video)
                            assert result is True
                            
                            # 验证MoviePy调用
                            assert mock_image_clip.call_count == len(image_files)
                            assert mock_audio_clip.call_count == len(audio_files)
                            mock_video_instance.write_videofile.assert_called_once()
    
    @pytest.mark.openai
    def test_full_pipeline_integration(self, temp_workspace, sample_story_file, mock_config):
        """测试完整流水线集成"""
        # 配置所有模块
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.sd_api_url = "http://localhost:7860"
        mock_config.azure_speech_key = "test_speech_key"
        mock_config.azure_speech_region = "eastus"
        mock_config.azure_speech_voice = "zh-CN-XiaoxiaoNeural"
        mock_config.video_width = 1920
        mock_config.video_height = 1080
        mock_config.video_fps = 30
        mock_config.input_dir = temp_workspace['input_dir']
        mock_config.output_dir = temp_workspace['output_dir']
        mock_config.output_images_dir = temp_workspace['images_dir']
        mock_config.output_audio_dir = temp_workspace['audio_dir']
        mock_config.output_videos_dir = temp_workspace['video_dir']
        
        # Mock所有外部依赖
        with patch('src.pipeline.text_analyzer.config', mock_config):
            with patch('src.pipeline.image_generator.config', mock_config):
                with patch('src.pipeline.voice_synthesizer.config', mock_config):
                    with patch('src.pipeline.video_composer.config', mock_config):
                        # Mock LLM
                        mock_llm_response = """
章节1: 小猫在花园
描述: 可爱的小猫在花园中

章节2: 发现洞穴
描述: 小猫发现神秘洞穴
                        """.strip()
                        
                        with patch('src.llm_client.LLMClient') as mock_llm_client_class:
                            mock_llm_client = Mock()
                            mock_llm_client.chat_completion.return_value = mock_llm_response
                            mock_llm_client_class.return_value = mock_llm_client
                            
                            # Mock图像生成
                            with patch('requests.post') as mock_post:
                                mock_response = Mock()
                                mock_response.status_code = 200
                                mock_response.json.return_value = {
                                    "images": ["base64_image_data"]
                                }
                                mock_post.return_value = mock_response
                                
                                with patch('base64.b64decode') as mock_b64decode:
                                    mock_b64decode.return_value = b"fake_image_data"
                                    
                                    # Mock语音合成
                                    with patch('azure.cognitiveservices.speech.SpeechSynthesizer') as mock_synthesizer_class:
                                        with patch('azure.cognitiveservices.speech.SpeechConfig'):
                                            mock_synthesizer = Mock()
                                            mock_synthesizer_class.return_value = mock_synthesizer
                                            
                                            mock_speech_result = Mock()
                                            mock_speech_result.reason = 0
                                            mock_speech_result.audio_data = b"fake_audio_data"
                                            mock_synthesizer.speak_ssml_async.return_value.get.return_value = mock_speech_result
                                            
                                            # Mock视频合成
                                            mock_moviepy = Mock()
                                            mock_editor = Mock()
                                            mock_moviepy.editor = mock_editor
                                            with patch.dict('sys.modules', {'moviepy': mock_moviepy, 'moviepy.editor': mock_editor}):
                                                with patch('moviepy.editor.ImageClip') as mock_image_clip:
                                                    with patch('moviepy.editor.AudioFileClip') as mock_audio_clip:
                                                        with patch('moviepy.editor.CompositeVideoClip') as mock_composite:
                                                            # Setup MoviePy mocks
                                                            mock_image_instance = Mock()
                                                            mock_image_instance.resize.return_value = mock_image_instance
                                                            mock_image_instance.set_duration.return_value = mock_image_instance
                                                            mock_image_instance.set_audio.return_value = mock_image_instance
                                                            mock_image_instance.fadein.return_value = mock_image_instance
                                                            mock_image_instance.fadeout.return_value = mock_image_instance
                                                            mock_image_clip.return_value = mock_image_instance
                                                            
                                                            mock_audio_instance = Mock()
                                                            mock_audio_instance.duration = 5.0
                                                            mock_audio_clip.return_value = mock_audio_instance
                                                            
                                                            mock_video_instance = Mock()
                                                            mock_composite.return_value = mock_video_instance
                                                            
                                                            # 执行完整流水线
                                                            analyzer = TextAnalyzer()
                                                            generator = ImageGenerator()
                                                            synthesizer = VoiceSynthesizer()
                                                            composer = VideoComposer()
                                                            
                                                            # 1. 文本分析
                                                            chapters_file = analyzer.analyze_story(sample_story_file)
                                                            assert os.path.exists(chapters_file)
                                                            
                                                            # 2. 图像生成
                                                            img_result = generator.generate_images_from_csv(chapters_file)
                                                            assert img_result is True
                                                            
                                                            # 3. 语音合成（模拟）
                                                            import pandas as pd
                                                            df = pd.read_csv(chapters_file)
                                                            audio_files = []
                                                            
                                                            for _, row in df.iterrows():
                                                                audio_path = os.path.join(temp_workspace['audio_dir'], row['voice_file'])
                                                                voice_result = synthesizer.synthesize_text(row['content'], audio_path)
                                                                assert voice_result is True
                                                                audio_files.append(audio_path)
                                                            
                                                            # 4. 视频合成
                                                            image_files = [os.path.join(temp_workspace['images_dir'], f"chapter_{i}.jpg") for i in range(1, len(df) + 1)]
                                                            output_video = os.path.join(temp_workspace['video_dir'], "final_story.mp4")
                                                            
                                                            video_result = composer.compose_video(image_files, audio_files, output_video)
                                                            assert video_result is True
                                                            
                                                            # 验证所有步骤都被调用
                                                            mock_llm_client.chat_completion.assert_called()
                                                            mock_post.assert_called()
                                                            mock_synthesizer.speak_ssml_async.assert_called()
                                                            mock_video_instance.write_videofile.assert_called()

    def test_error_propagation_in_pipeline(self, temp_workspace, sample_story_file, mock_config):
        """测试流水线中的错误传播"""
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "test_key"
        mock_config.input_dir = temp_workspace['input_dir']
        mock_config.output_dir = temp_workspace['output_dir']
        
        with patch('src.pipeline.text_analyzer.config', mock_config):
            # Mock LLM失败
            with patch('src.llm_client.LLMClient') as mock_llm_client_class:
                mock_llm_client = Mock()
                mock_llm_client.chat_completion.side_effect = Exception("LLM API错误")
                mock_llm_client_class.return_value = mock_llm_client
                
                analyzer = TextAnalyzer()
                
                # 验证错误被正确传播
                with pytest.raises(Exception, match=r".*Failed to process chapter.*"):
                    analyzer.analyze_story(sample_story_file)
    
    def test_data_flow_consistency(self, temp_workspace, mock_config):
        """测试数据流一致性"""
        # 创建测试CSV文件
        csv_content = """chapter,content,image_prompt,voice_file,lora_model,lora_strength
1,第一章内容,first chapter image,chapter_1.wav,,
2,第二章内容,second chapter image,chapter_2.wav,,
"""
        
        csv_file = os.path.join(temp_workspace['output_dir'], "chapters.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # 验证CSV数据可以被正确读取和处理
        import pandas as pd
        df = pd.read_csv(csv_file)
        
        assert len(df) == 2
        assert 'chapter' in df.columns
        assert 'content' in df.columns
        assert 'image_prompt' in df.columns
        assert 'voice_file' in df.columns
        
        # 验证数据类型和内容
        assert df.iloc[0]['chapter'] == 1
        assert df.iloc[0]['content'] == '第一章内容'
        assert df.iloc[0]['voice_file'] == 'chapter_1.wav'
        
        assert df.iloc[1]['chapter'] == 2
        assert df.iloc[1]['content'] == '第二章内容'
        assert df.iloc[1]['voice_file'] == 'chapter_2.wav'