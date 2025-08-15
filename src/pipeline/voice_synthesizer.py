import os
import sys
import openpyxl
import asyncio
from tqdm.asyncio import tqdm as async_tqdm
import argparse
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioDataStream, ResultReason
from io import BytesIO
import html
from pydub import AudioSegment
from pydub.silence import split_on_silence
from src.config import config

# 验证Azure配置
if not config.azure_speech_key:
    print("错误: 未配置Azure语音服务密钥，请在.env文件中设置AZURE_SPEECH_KEY")
    sys.exit(1)

class SpeechProvider:
    def __init__(self):
        """初始化语音合成提供者"""
        self.subscription = config.azure_speech_key
        self.region = config.azure_speech_region
        self.voice_name = config.azure_voice_name
        self.style = config.azure_voice_style
        self.role = config.azure_voice_role
        self.prosody_rate = config.azure_voice_rate
        self.prosody_pitch = config.azure_voice_pitch
        self.prosody_volume = config.azure_voice_volume
        self.emphasis_level = config.azure_voice_emphasis
        self.style_degree = config.azure_voice_style_degree

    async def get_tts_audio(self, message, language, index, max_retries=3):
        """获取TTS音频数据"""
        for attempt in range(max_retries):
            try:
                speech_config = SpeechConfig(subscription=self.subscription, region=self.region)
                speech_config.speech_synthesis_voice_name = self.voice_name

                synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)

                escaped_message = html.escape(message)

                ssml_text = f"""
                <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='{language}'>
                  <voice name='{self.voice_name}'>
                    <mstts:express-as style='{self.style}' role='{self.role}' styledegree='{self.style_degree}'>
                      <prosody rate='{self.prosody_rate}' pitch='{self.prosody_pitch}' volume='{self.prosody_volume}'>
                        {escaped_message}
                      </prosody>
                    </mstts:express-as>
                  </voice>
                </speak>
                """

                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, lambda: synthesizer.speak_ssml_async(ssml_text).get())

                if result.reason == ResultReason.SynthesizingAudioCompleted:
                    audio_data = BytesIO(result.audio_data)
                    return {"index": index, "audio_data": audio_data, "error": None}
                elif result.reason == ResultReason.Canceled:
                    cancellation_details = speechsdk.SpeechSynthesisCancellationDetails(result)
                    error_msg = f"语音合成被取消：{cancellation_details.reason} - {cancellation_details.error_details}"
                    if attempt < max_retries - 1:
                        print(f"序号 {index} 合成失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                        await asyncio.sleep(1)  # 等待1秒后重试
                    else:
                        return {"index": index, "audio_data": None, "error": error_msg}
                        
            except Exception as e:
                error_msg = f"语音合成异常: {str(e)}"
                if attempt < max_retries - 1:
                    print(f"序号 {index} 合成异常 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                    await asyncio.sleep(1)  # 等待1秒后重试
                else:
                    return {"index": index, "audio_data": None, "error": error_msg}
        
        return {"index": index, "audio_data": None, "error": "达到最大重试次数"}

def remove_silence(audio_path):
    """移除音频文件中的静音部分"""
    try:
        # Load audio
        audio = AudioSegment.from_wav(audio_path)
        # Split on silence
        chunks = split_on_silence(audio, min_silence_len=10, silence_thresh=-50)
        if chunks:  # 确保有音频块
            # Concatenate non-silent chunks and export
            non_silent_audio = sum(chunks)
            non_silent_audio.export(audio_path, format="wav")
        else:
            print(f"警告: {audio_path} 可能完全是静音")
    except Exception as e:
        print(f"处理音频文件 {audio_path} 时出错: {e}")

async def process_text_files(input_file, output_dir, language):
    """处理文本文件生成语音"""
    print(f"Step 3: 语音合成")
    print(f"输入文件: {input_file}")
    print(f"输出目录: {output_dir}")
    print(f"语言: {language}")
    
    # 检查输入文件
    if not input_file.exists():
        print(f"错误: 输入文件不存在 - {input_file}")
        return []
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        wb = openpyxl.load_workbook(input_file)
        sheet = wb.active
        column = sheet["A"]
        
        # 过滤掉空的单元格
        texts = [(i, cell.value) for i, cell in enumerate(column, 1) if cell.value and cell.value.strip()]
        
        if not texts:
            print("错误: 未找到任何文本内容")
            return []
        
        print(f"找到 {len(texts)} 个文本片段")
        
        provider = SpeechProvider()
        
        # 创建任务
        tasks = [provider.get_tts_audio(text, language, index) for index, text in texts]
        
        results = []
        success_count = 0
        error_count = 0
        
        for f in async_tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="正在合成配音"):
            result = await f
            
            if result['error']:
                print(f"合成失败 - 序号 {result['index']}: {result['error']}")
                error_count += 1
                continue
            
            audio_data = result['audio_data']
            if audio_data:
                output_path = output_dir / f"output_{result['index']}.wav"
                try:
                    with open(output_path, 'wb') as f:
                        f.write(audio_data.getbuffer())
                    remove_silence(output_path)  # Remove silence after saving the audio file
                    success_count += 1
                except Exception as e:
                    print(f"保存音频文件失败 - 序号 {result['index']}: {e}")
                    error_count += 1
            else:
                error_count += 1
                
            results.append(result)
        
        wb.close()
        print(f"语音合成完成！成功: {success_count}, 失败: {error_count}")
        return results
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")
        return []

def main():
    """主函数"""
    # 使用配置文件中的路径
    input_file = config.output_excel_file
    output_dir = config.output_dir_voice
    language = "zh-CN"
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    try:
        # 运行异步处理
        results = asyncio.run(process_text_files(input_file, output_dir, language))
        
        # 检查结果
        success_results = [r for r in results if not r.get('error')]
        
        if success_results:
            print(f"成功生成 {len(success_results)} 个语音文件")
            return True
        else:
            print("没有成功生成任何语音文件")
            return False
            
    except Exception as e:
        print(f"程序执行出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)