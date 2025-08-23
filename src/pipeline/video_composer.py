import os
import sys
import gc
import random
import shutil
import time
import warnings
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import threading

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 抑制 MoviePy 的 ffmpeg_reader 警告
warnings.filterwarnings("ignore", message=".*bytes wanted but.*bytes read.*")
from PIL import Image, ImageFilter
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.CompositeVideoClip import concatenate_videoclips
from moviepy.video.VideoClip import TextClip
import numpy as np
import json
import argparse
from tqdm import tqdm
from src.config import config

# 获取配置的目录路径
image_dir = config.output_dir_image
voice_dir = config.output_dir_voice
video_dir = config.output_dir_video
temp_dir = config.output_dir_temp
subtitle_dir = config.output_dir_txt

# 确保所有目录存在
for directory in [video_dir, temp_dir]:
    directory.mkdir(parents=True, exist_ok=True)

# 从配置获取视频设置
fps = config.video_fps
load_subtitles = config.video_load_subtitles
enlarge_background = config.video_enlarge_background
enable_effect = config.video_enable_effect
effect_type = config.video_effect_type

# 移到main函数中执行，避免在导入时打印
# print(f"Step 4: 视频合成")
# print(f"配置信息:")
# print(f"  FPS: {fps}")
# print(f"  字幕: {'启用' if load_subtitles else '禁用'}")
# print(f"  背景效果: {'启用' if enlarge_background else '禁用'}")
# print(f"  特效: {'启用' if enable_effect else '禁用'} ({effect_type if enable_effect else 'N/A'})")

# 获取文件总数
def get_total_files():
    """获取图片文件总数"""
    try:
        files = [f for f in os.listdir(image_dir) if f.endswith('.png')]
        return len(files)
    except Exception as e:
        print(f"获取图片文件列表失败: {e}")
        return 0

# 将这些代码移到main函数中执行，避免在导入时执行
# total_files = get_total_files()
# print(f"发现 {total_files} 个图片文件")
# 
# if total_files == 0:
#     print("错误: 未找到任何图片文件")
#     sys.exit(1)

# 读取字幕
def load_subtitle_data(total_files, json_file_path=None):
    """加载字幕数据"""
    # 检查字幕功能是否启用
    if not load_subtitles:
        print(f"字幕功能已禁用 (VIDEO_SUBTITLE={load_subtitles})")
        return [""]*total_files
    
    print(f"字幕功能已启用 (VIDEO_SUBTITLE={load_subtitles})")
    
    try:
        if json_file_path:
            subtitle_file = Path(json_file_path)
        else:
            subtitle_file = config.output_json_file
        if not subtitle_file.exists():
            print(f"警告: 字幕文件不存在 - {subtitle_file}")
            print("提示: 请确保文本分析步骤已完成并生成了字幕文件")
            return [""]*total_files
            
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理新的标准化格式和旧格式的兼容性
        if isinstance(data, dict) and 'storyboards' in data:
            # 新的标准化格式
            data_list = data['storyboards']
        elif isinstance(data, list):
            # 旧的列表格式
            data_list = data
        else:
            print("错误: 无法识别的JSON格式")
            return [""]*total_files
        
        # 从JSON数据中提取原始中文字幕
        subtitles = [item.get('original_chinese', item.get('原始中文', '')).replace('\n', ' ') for item in data_list]
        
        # 确保字幕数量与图片数量匹配
        if len(subtitles) < total_files:
            print(f"警告: 字幕数量({len(subtitles)}) 少于图片数量({total_files})，将用空字幕补齐")
            subtitles.extend([""]*(total_files - len(subtitles)))
        elif len(subtitles) > total_files:
            print(f"警告: 字幕数量({len(subtitles)}) 多于图片数量({total_files})，将截取前{total_files}条")
            subtitles = subtitles[:total_files]
            
        print(f"成功加载了 {len(subtitles)} 条字幕")
        return subtitles
        
    except Exception as e:
        print(f"加载字幕失败: {e}，将使用空字幕")
        print("提示: 请检查字幕文件格式是否正确")
        return [""]*total_files

# subtitles = load_subtitle_data()  # 移到main函数中执行

def create_clip(i, subtitles, retry_count=0):
    """创建单个视频片段"""
    max_retries = 2  # 最大重试次数
    filename = f'output_{i+1}.png'
    audio_filename_mp3 = f'output_{i+1}.mp3'
    audio_filename_wav = f'output_{i+1}.wav'
    subtitle = subtitles[i] if i < len(subtitles) else ""
    
    image_path = image_dir / filename
    temp_filename = temp_dir / f'output_{i+1}.mp4'

    # 检查图片文件是否存在
    if not image_path.exists():
        print(f"警告: 图片文件不存在 - {image_path}")
        return None
        
    try:
        im = Image.open(image_path)
    except Exception as e:
        print(f"无法打开图片 {image_path}: {e}")
        return None
   
    # 检查音频文件
    audio_path_mp3 = voice_dir / audio_filename_mp3
    audio_path_wav = voice_dir / audio_filename_wav
    
    audio = None
    if audio_path_mp3.exists():
        try:
            audio = AudioFileClip(str(audio_path_mp3))
        except Exception as e:
            print(f"无法加载音频文件 {audio_path_mp3}: {e}")
    elif audio_path_wav.exists():
        try:
            audio = AudioFileClip(str(audio_path_wav))
        except Exception as e:
            print(f"无法加载音频文件 {audio_path_wav}: {e}")
    
    if audio is None:
        print(f"警告: 未找到音频文件 output_{i+1}，将使用默认2秒时长")
        # 创建2秒的静音
        audio_duration = 2.0
    else:
        audio_duration = audio.duration

    # 创建字幕
    txt_clip = None
    if load_subtitles and subtitle and subtitle.strip():
        try:
            max_width = int(im.width * 0.8)
            
            # 从配置获取字幕样式参数
            base_fontsize = config.subtitle_fontsize
            fontcolor = config.subtitle_fontcolor
            stroke_color = config.subtitle_stroke_color
            stroke_width = config.subtitle_stroke_width
            font = config.subtitle_font
            method = 'caption'
            align = config.subtitle_align
            pixel_from_bottom = config.subtitle_pixel_from_bottom
            
            # 动态计算字体大小，防止长字幕被截断
            def get_dynamic_fontsize(subtitle_text, base_fontsize):
                """根据字幕长度动态计算字体大小"""
                char_count = len(subtitle_text)
                
                if char_count <= 30:
                    return base_fontsize
                elif char_count <= 60:
                    return max(32, base_fontsize - 8)
                elif char_count <= 90:
                    return max(28, base_fontsize - 12)
                else:
                    return max(24, base_fontsize - 16)
            
            fontsize = get_dynamic_fontsize(subtitle, base_fontsize)
            size = [max_width, None]
            
            # 验证字幕配置参数
            if fontsize <= 0:
                print(f"警告: 字幕字体大小无效 ({fontsize})，使用默认值 60")
                fontsize = 60
            
            # 输出字幕调试信息
            if len(subtitle) > 30:
                print(f"长字幕检测: 字符数={len(subtitle)}, 调整字体大小 {base_fontsize}→{fontsize}")
            
            txt_clip = TextClip(text=subtitle, font_size=fontsize, color=fontcolor, stroke_color=stroke_color, 
                                stroke_width=stroke_width, method=method, 
                                text_align=align, size=size, font=font)

            # 定义字幕位置
            def calculate_position(t):
                if pixel_from_bottom < 0:
                    # 负值表示从顶部开始
                    return ('center', abs(pixel_from_bottom))
                elif pixel_from_bottom == 0:
                    # 0表示居中
                    return ('center', 'center')
                else:
                    # 正值表示从底部开始
                    return ('center', im.height - pixel_from_bottom)
            txt_clip = txt_clip.with_position(calculate_position).with_duration(audio_duration)
            
        except Exception as e:
            print(f"创建字幕失败: {e}")
            print(f"字幕内容: {subtitle[:50]}..." if len(subtitle) > 50 else f"字幕内容: {subtitle}")
            print("提示: 请检查字幕配置参数和字体文件是否正确")
            txt_clip = None
    elif load_subtitles and not subtitle.strip():
        # 字幕功能启用但当前片段无字幕内容
        pass

    # 计算Ken Burns效果参数
    x_speed = (im.width - im.width * 9 / 10) / audio_duration
    y_speed = (im.height - im.height * 9 / 10) / audio_duration

    n_frames = int(fps * audio_duration)

    def transform(img, t, move_on_x, move_positive):
        crop_width = im.width * 9 / 10
        crop_height = im.height * 9 / 10

        if move_on_x:
            if move_positive:
                left = min(x_speed * t, img.width - crop_width)
            else:
                left = max(img.width - crop_width - x_speed * t, 0)
            upper = (img.height - crop_height) / 2
        else:
            left = (img.width - crop_width) / 2
            if move_positive:
                upper = min(y_speed * t, img.height - crop_height)
            else:
                upper = max(img.height - crop_height - y_speed * t, 0)

        right = left + crop_width
        lower = upper + crop_height

        cropped_img = img.crop((left, upper, right, lower))
        resized_img = cropped_img.resize(im.size)

        return np.array(resized_img)

    move_on_x = random.choice([True, False])
    move_positive = random.choice([True, False])

    frames_foreground = [transform(im, t / fps, move_on_x, move_positive) for t in range(n_frames)]
    img_foreground = ImageSequenceClip(frames_foreground, fps=fps)
 
    del frames_foreground
    gc.collect()

    img_blur = im.filter(ImageFilter.GaussianBlur(radius=30))
    if enlarge_background:
        new_size = (int(im.width * 1.1), int(im.height * 1.1))
        img_blur = img_blur.resize(new_size, Image.ANTIALIAS)

    frames_background = [np.array(img_blur) for _ in range(n_frames)]
    img_background = ImageSequenceClip(frames_background, fps=fps)

    del frames_background
    gc.collect()

    # 设置音频
    if audio:
        img_foreground = img_foreground.with_audio(audio)

    # 组合视频片段
    if load_subtitles and txt_clip:
        final_clip = CompositeVideoClip([img_background.with_position("center"), img_foreground.with_position("center"), txt_clip], size=img_blur.size)
    else:
        final_clip = CompositeVideoClip([img_background.with_position("center"), img_foreground.with_position("center")], size=img_blur.size)
       
    # 应用特效
    if enable_effect:
        try:
            if effect_type == 'slide':
                final_clip = final_clip.crossfadein(2).crossfadeout(4)
            elif effect_type == 'rotate':
                final_clip = final_clip.rotate(lambda t: 360*t/10)
            elif effect_type == 'scroll':
                # 导入vfx模块
                from moviepy.video.fx import scroll
                final_clip = final_clip.fx(scroll, h=lambda t: 50*t)
            elif effect_type == 'flip_horizontal':
                from moviepy.video.fx import mirror_x
                final_clip = final_clip.fx(mirror_x)
            elif effect_type == 'flip_vertical':
                from moviepy.video.fx import mirror_y
                final_clip = final_clip.fx(mirror_y)
            elif effect_type == 'fade':
                final_clip = final_clip.fadein(0.5).fadeout(0.5)
        except Exception as e:
            print(f"应用特效 {effect_type} 失败: {e}")

    # 生成视频片段
    try:
        # 使用更稳定的编码参数
        final_clip.write_videofile(
            str(temp_filename), 
            logger=None, 
            audio_codec='aac',
            codec='libx264',
            preset='slow',  # 更保守的预设，确保质量
            ffmpeg_params=[
                '-pix_fmt', 'yuv420p',
                '-crf', '18',  # 更高质量
                '-profile:v', 'baseline',  # 基线配置，最大兼容性
                '-level', '3.0',  # 兼容性级别
                '-movflags', '+faststart',  # 优化流媒体
                '-strict', 'experimental'  # 允许实验性编码器
            ]
        )
        
        # 短暂延迟确保文件写入完成
        time.sleep(0.2)
        
        # 验证生成的文件
        if not temp_filename.exists() or temp_filename.stat().st_size == 0:
            print(f"警告: 视频片段 {i+1} 生成的文件无效")
            return None
            
        # 验证文件可以被 MoviePy 正确读取
        try:
            test_clip = VideoFileClip(str(temp_filename))
            if test_clip.duration <= 0:
                print(f"警告: 视频片段 {i+1} 时长无效")
                test_clip.close()
                return None
            test_clip.close()
        except Exception as e:
            print(f"警告: 视频片段 {i+1} 无法正确读取: {e}")
            # 删除损坏的文件并重试
            if temp_filename.exists():
                temp_filename.unlink()
            if retry_count < max_retries:
                print(f"重试生成视频片段 {i+1} (第 {retry_count + 1} 次重试)")
                time.sleep(0.5)  # 短暂延迟后重试
                return create_clip(i, subtitles, retry_count + 1)
            return None
            
    except Exception as e:
        print(f"生成视频片段 {i+1} 失败: {e}")
        # 删除可能存在的不完整文件并重试
        if temp_filename.exists():
            temp_filename.unlink()
        if retry_count < max_retries:
            print(f"重试生成视频片段 {i+1} (第 {retry_count + 1} 次重试)")
            time.sleep(0.5)  # 短暂延迟后重试
            return create_clip(i, subtitles, retry_count + 1)
        return None

    # 清理内存
    del final_clip
    gc.collect()

    return str(temp_filename)

def main(json_file_path=None):
    """主函数：执行视频合成"""
    # 打印配置信息
    print(f"Step 4: 视频合成")
    print(f"配置信息:")
    print(f"  FPS: {fps}")
    print(f"  字幕: {'启用' if load_subtitles else '禁用'}")
    if load_subtitles:
        print(f"    - 字体大小: {config.subtitle_fontsize}")
        print(f"    - 字体颜色: {config.subtitle_fontcolor}")
        print(f"    - 字体: {config.subtitle_font}")
        print(f"    - 对齐方式: {config.subtitle_align}")
        print(f"    - 位置: {config.subtitle_pixel_from_bottom} 像素")
    print(f"  背景效果: {'启用' if enlarge_background else '禁用'}")
    print(f"  特效: {'启用' if enable_effect else '禁用'} ({effect_type if enable_effect else 'N/A'})")
    
    # 初始化文件计数和字幕数据
    total_files = get_total_files()
    print(f"发现 {total_files} 个图片文件")
    
    if total_files == 0:
        print("错误: 未找到任何图片文件")
        return False
    
    subtitles = load_subtitle_data(total_files, json_file_path)
    
    # 为了避免文件冲突，适当降低并发数
    original_max_workers = config.max_workers_video
    max_workers = min(original_max_workers, 3)  # 限制最大并发数为3
    
    print(f"开始生成 {total_files} 个视频片段（并发数: {max_workers}，原配置: {original_max_workers}）...")
    if max_workers < original_max_workers:
        print(f"为提高稳定性，已将并发数从 {original_max_workers} 调整为 {max_workers}")
    
    temp_filenames = []
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pbar = tqdm(total=total_files, ncols=None, desc="正在生成视频片段")
        futures = {executor.submit(create_clip, i, subtitles): i for i in range(total_files)}

        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            try:
                result = future.result()
                if result:
                    temp_filenames.append(result)
                else:
                    failed_count += 1
                    print(f"视频片段 {i+1} 生成失败")
            except Exception as e:
                failed_count += 1
                print(f"视频片段 {i+1} 生成异常: {e}")
            pbar.update(1)

        pbar.close()

    if not temp_filenames:
        print("错误: 没有成功生成任何视频片段")
        return False

    print(f"成功生成 {len(temp_filenames)} 个视频片段，失败 {failed_count} 个")

    # 按文件名排序
    temp_filenames.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))

    # 合并视频片段
    print("正在合并视频片段...")
    try:
        clips = []
        for filename in temp_filenames:
            try:
                # 验证文件完整性
                if not os.path.exists(filename) or os.path.getsize(filename) == 0:
                    print(f"跳过无效的视频文件: {filename}")
                    continue
                    
                clip = VideoFileClip(filename)
                # 验证视频片段是否有效
                if clip.duration > 0:
                    clips.append(clip)
                else:
                    print(f"跳过时长为0的视频片段: {filename}")
                    clip.close()
            except Exception as e:
                print(f"加载视频片段失败 {filename}: {e}")

        if not clips:
            print("错误: 没有可用的视频片段进行合并")
            return False

        final_video = concatenate_videoclips(clips, method="compose")
        
        # 生成最终视频文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        final_filename = video_dir / f'output_{timestamp}.mp4'
        
        print(f"正在输出最终视频: {final_filename}")
        final_video.write_videofile(
            str(final_filename), 
            logger=None, 
            audio_codec='aac',
            codec='libx264',
            preset='slow',  # 更保守的预设，确保质量
            ffmpeg_params=[
                '-pix_fmt', 'yuv420p',
                '-crf', '18',  # 更高质量
                '-profile:v', 'baseline',  # 基线配置，最大兼容性
                '-level', '3.0',  # 兼容性级别
                '-movflags', '+faststart',  # 优化流媒体
                '-strict', 'experimental'  # 允许实验性编码器
            ]
        )
        
        # 清理资源
        for clip in clips:
            clip.close()
        final_video.close()
        
        print(f"视频生成完成: {final_filename}")
        
    except Exception as e:
        print(f"合并视频失败: {e}")
        return False

    # 清理临时文件
    print("清理临时文件...")
    for filename in temp_filenames:
        try:
            os.remove(filename)
        except Exception as e:
            print(f"删除临时文件失败 {filename}: {e}")

    return True

def delete_all_files(directory):
    """删除目录中的所有文件"""
    try:
        for filename in os.listdir(directory):
            file_path = directory / filename
            try:
                if file_path.is_file() or file_path.is_symlink():
                    file_path.unlink()
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'删除文件失败 {file_path}: {e}')
    except Exception as e:
        print(f'访问目录失败 {directory}: {e}')

# 可选的清理功能（默认注释掉）
def cleanup_all_files():
    """清理所有生成的文件（慎用）"""
    print("警告: 即将删除所有生成的文件")
    response = input("确认删除吗？(yes/no): ")
    if response.lower() == 'yes':
        delete_all_files(image_dir)
        delete_all_files(voice_dir)
        delete_all_files(temp_dir)
        print("清理完成")
    else:
        print("清理已取消")

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='视频合成工具')
        parser.add_argument('--json-file', type=str, help='指定JSON文件路径')
        args = parser.parse_args()
        
        success = main(args.json_file)
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)
