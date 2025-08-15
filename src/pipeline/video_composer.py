import os
import sys
import gc
import random
import shutil
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from PIL import Image, ImageFilter
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
import numpy as np
import pandas as pd
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

print(f"Step 4: 视频合成")
print(f"配置信息:")
print(f"  FPS: {fps}")
print(f"  字幕: {'启用' if load_subtitles else '禁用'}")
print(f"  背景效果: {'启用' if enlarge_background else '禁用'}")
print(f"  特效: {'启用' if enable_effect else '禁用'} ({effect_type if enable_effect else 'N/A'})")

# 获取文件总数
def get_total_files():
    """获取图片文件总数"""
    try:
        files = [f for f in os.listdir(image_dir) if f.endswith('.png')]
        return len(files)
    except Exception as e:
        print(f"获取图片文件列表失败: {e}")
        return 0

total_files = get_total_files()
print(f"发现 {total_files} 个图片文件")

if total_files == 0:
    print("错误: 未找到任何图片文件")
    sys.exit(1)

# 读取字幕
def load_subtitle_data():
    """加载字幕数据"""
    if not load_subtitles:
        return [""] * total_files
    
    try:
        subtitle_file = subtitle_dir / 'txt.xlsx'
        if not subtitle_file.exists():
            print(f"警告: 字幕文件不存在 - {subtitle_file}")
            return [""] * total_files
            
        df = pd.read_excel(subtitle_file, usecols=[0], header=None, engine='openpyxl')
        col_name = df.columns[0]
        subtitles = df[col_name].str.replace('\n', ' ', regex=False).tolist()
        
        # 确保字幕数量与图片数量匹配
        if len(subtitles) < total_files:
            subtitles.extend([""] * (total_files - len(subtitles)))
        elif len(subtitles) > total_files:
            subtitles = subtitles[:total_files]
            
        print(f"加载了 {len(subtitles)} 条字幕")
        return subtitles
        
    except Exception as e:
        print(f"加载字幕失败: {e}，将使用空字幕")
        return [""] * total_files

subtitles = load_subtitle_data()

def create_clip(i):
    """创建单个视频片段"""
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
            max_width = im.width * 0.8 
            
            # 从配置获取字幕样式参数
            fontsize = config.subtitle_fontsize
            fontcolor = config.subtitle_fontcolor
            stroke_color = config.subtitle_stroke_color
            stroke_width = config.subtitle_stroke_width
            font = config.subtitle_font
            method = 'caption'
            align = config.subtitle_align
            pixel_from_bottom = config.subtitle_pixel_from_bottom
            
            size = [max_width, None]
            
            txt_clip = TextClip(subtitle, fontsize=fontsize, color=fontcolor, stroke_color=stroke_color, 
                                stroke_width=stroke_width, font=font, method=method, 
                                align=align, size=size)

            # 定义字幕位置
            def calculate_position(t):
                return ('center', im.height - pixel_from_bottom)  
            txt_clip = txt_clip.set_pos(calculate_position).set_duration(audio_duration)
        except Exception as e:
            print(f"创建字幕失败: {e}")
            txt_clip = None

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
        img_foreground = img_foreground.set_audio(audio)

    # 组合视频片段
    if load_subtitles and txt_clip:
        final_clip = CompositeVideoClip([img_background.set_position("center"), img_foreground.set_position("center"), txt_clip], size=img_blur.size)
    else:
        final_clip = CompositeVideoClip([img_background.set_position("center"), img_foreground.set_position("center")], size=img_blur.size)
       
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
        final_clip.write_videofile(str(temp_filename), logger=None, audio_codec='aac')
    except Exception as e:
        print(f"生成视频片段 {i+1} 失败: {e}")
        return None

    # 清理内存
    del final_clip
    gc.collect()

    return str(temp_filename)

def main():
    """主函数：执行视频合成"""
    max_workers = config.max_workers_video
    
    print(f"开始生成 {total_files} 个视频片段（并发数: {max_workers}）...")
    
    temp_filenames = []
    failed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        pbar = tqdm(total=total_files, ncols=None, desc="正在生成视频片段")
        futures = {executor.submit(create_clip, i): i for i in range(total_files)}

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
                clip = VideoFileClip(filename)
                clips.append(clip)
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
        final_video.write_videofile(str(final_filename), logger=None, audio_codec='aac')
        
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
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)
