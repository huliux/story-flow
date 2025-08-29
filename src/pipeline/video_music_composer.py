#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频音乐合成模块
将视频片段与音乐文件进行合成，音乐长度自动匹配视频总长度
"""

import argparse
import sys
import warnings
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 抑制 MoviePy 的警告
warnings.filterwarnings("ignore", message=".*bytes wanted but.*bytes read.*")
warnings.filterwarnings("ignore", category=UserWarning, module="moviepy")

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import (
    concatenate_videoclips,
)
from moviepy.video.io.VideoFileClip import VideoFileClip

from src.config import config


class VideoMusicComposer:
    """视频音乐合成器"""

    def __init__(self):
        """初始化视频音乐合成器"""
        self.video_clips_dir = config.output_dir_video_clips
        self.music_dir = config.output_dir_music
        self.output_dir = config.output_dir_video
        self.temp_dir = config.output_dir_temp

        # 配置参数
        self.music_volume = config.video_music_volume
        self.fade_duration = config.video_music_fade_duration
        self.original_audio_volume = config.video_music_original_audio_volume
        self.default_music_file = config.video_music_default_file

        # 确保目录存在
        for directory in [self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_video_clips(self) -> List[Path]:
        """获取所有视频片段文件，按文件名中的数字顺序排序"""
        video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv"]
        video_files = []

        if not self.video_clips_dir.exists():
            print(f"警告: 视频片段目录不存在 - {self.video_clips_dir}")
            return video_files

        for ext in video_extensions:
            video_files.extend(self.video_clips_dir.glob(f"*{ext}"))

        # 按文件名中的数字顺序排序
        import re

        def extract_number(filename):
            """从文件名中提取数字用于排序"""
            numbers = re.findall(r"\d+", filename.stem)
            return int(numbers[-1]) if numbers else 0

        video_files.sort(key=lambda x: extract_number(x))

        print("视频文件排序结果:")
        for i, video_file in enumerate(video_files):
            print(f"  {i+1}. {video_file.name}")

        return video_files

    def get_music_file(self, music_filename: Optional[str] = None) -> Optional[Path]:
        """获取指定的音乐文件"""
        if music_filename is None:
            music_filename = self.default_music_file

        music_path = self.music_dir / music_filename

        if not music_path.exists():
            print(f"警告: 音乐文件不存在 - {music_path}")
            return None

        return music_path

    def calculate_total_video_duration(self, video_files: List[Path]) -> float:
        """计算所有视频片段的总时长"""
        total_duration = 0.0

        print("正在计算视频总时长...")
        for video_file in tqdm(video_files, desc="分析视频文件"):
            try:
                with VideoFileClip(str(video_file)) as clip:
                    total_duration += clip.duration
            except Exception as e:
                print(f"警告: 无法读取视频文件 {video_file}: {e}")
                continue

        return total_duration

    def prepare_background_music(
        self, music_path: Path, target_duration: float
    ) -> AudioFileClip:
        """准备背景音乐，调整长度以匹配视频总时长"""
        print(f"正在处理背景音乐: {music_path.name}")

        try:
            music_clip = AudioFileClip(str(music_path))
            print(f"音频文件加载成功: {music_path}")
            print(f"音频clip对象: {music_clip}")
            print(f"音频clip.reader: {music_clip.reader}")
            if music_clip.reader is None:
                print("错误: 音频文件reader为None")
                return None
            music_duration = music_clip.duration

            print(f"音乐原始时长: {music_duration:.2f}秒")
            print(f"目标时长: {target_duration:.2f}秒")

            # 根据音乐和视频长度关系进行处理
            if music_duration > target_duration:
                # 音乐比视频长，裁剪音乐
                print(f"音乐过长，裁剪至 {target_duration:.2f}秒")
                background_music = music_clip.subclipped(0, target_duration)
            elif music_duration < target_duration:
                # 音乐比视频短，循环音乐
                print(f"音乐过短，循环播放至 {target_duration:.2f}秒")
                loop_count = int(target_duration / music_duration) + 1
                print(f"需要循环 {loop_count} 次")

                # 创建循环音频片段列表
                audio_segments = []
                remaining_duration = target_duration

                for i in range(loop_count):
                    if remaining_duration <= 0:
                        break

                    if remaining_duration >= music_duration:
                        # 完整添加一次音乐
                        audio_segments.append(music_clip)
                        remaining_duration -= music_duration
                    else:
                        # 添加剩余部分
                        audio_segments.append(
                            music_clip.subclipped(0, remaining_duration)
                        )
                        remaining_duration = 0

                # 连接所有音频片段
                from moviepy.audio.AudioClip import concatenate_audioclips

                background_music = concatenate_audioclips(audio_segments)

                # 确保最终长度精确匹配
                if background_music.duration > target_duration:
                    background_music = background_music.subclipped(0, target_duration)
            else:
                # 音乐长度刚好匹配
                print("音乐长度与视频长度匹配")
                background_music = music_clip

            print(f"处理后音乐时长: {background_music.duration:.2f}秒")
            return background_music

        except Exception as e:
            print(f"处理音乐文件失败: {e}")
            raise

    def compose_video_with_music(
        self,
        video_files: List[Path],
        music_path: Path,
        output_filename: str = "final_video_with_music.mp4",
    ) -> bool:
        """合成视频与音乐"""
        if not video_files:
            print("错误: 没有找到视频文件")
            return False

        if not music_path:
            print("错误: 音乐文件不存在")
            return False

        # 生成带时间戳的文件名，避免覆盖
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_parts = output_filename.rsplit(".", 1)
        if len(name_parts) == 2:
            timestamped_filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            timestamped_filename = f"{output_filename}_{timestamp}"
        output_path = self.output_dir / timestamped_filename

        try:
            print(f"开始合成 {len(video_files)} 个视频片段...")

            # 加载所有视频片段
            video_clips = []
            for video_file in tqdm(video_files, desc="加载视频片段"):
                try:
                    clip = VideoFileClip(str(video_file))
                    # 检查视频片段是否有有效的duration
                    if clip.duration is None or clip.duration <= 0:
                        print(f"警告: 视频文件 {video_file} 没有有效的时长")
                        clip.close()
                        continue
                    video_clips.append(clip)
                except Exception as e:
                    print(f"警告: 无法加载视频文件 {video_file}: {e}")
                    continue

            if not video_clips:
                print("错误: 没有成功加载任何视频片段")
                return False

            # 连接所有视频片段
            print("正在连接视频片段...")
            final_video = concatenate_videoclips(video_clips, method="chain")
            print(f"连接后的视频对象: {final_video}")
            print(f"连接后的视频类型: {type(final_video)}")
            if final_video is None:
                print("错误: concatenate_videoclips 返回了 None")
                return False
            total_duration = final_video.duration
            print(f"连接后的视频时长: {total_duration}")

            print(f"视频总时长: {total_duration:.2f}秒")

            # 准备背景音乐
            background_music = self.prepare_background_music(music_path, total_duration)

            # 暂时移除音量调整以调试问题
            # background_music = background_music.with_volume_scaled(self.music_volume)  # 使用配置的音乐音量
            print("跳过音量调整，直接使用原始音量")

            # 合成视频和音乐
            print("正在合成视频和音乐...")
            print(f"final_video对象: {final_video}")
            print(f"final_video.audio: {final_video.audio}")
            print(f"background_music对象: {background_music}")

            if final_video.audio is not None:
                # 如果视频有原始音频，我们暂时只使用背景音乐（避免CompositeAudioClip的问题）
                print("视频有原始音频，但为了避免混合问题，只使用背景音乐")
                final_video_with_music = final_video.with_audio(background_music)
            else:
                # 如果视频没有原始音频，直接设置背景音乐
                print("视频没有原始音频，直接设置背景音乐")
                final_video_with_music = final_video.with_audio(background_music)

            print(f"final_video_with_music对象: {final_video_with_music}")
            print(f"final_video_with_music类型: {type(final_video_with_music)}")
            if final_video_with_music is None:
                print("错误: final_video_with_music 为 None")
                return False

            # 输出最终视频
            print(f"正在输出最终视频: {output_path}")
            try:
                final_video_with_music.write_videofile(
                    str(output_path),
                    fps=config.video_fps,
                    codec="libx264",
                    audio_codec="aac",
                    remove_temp=True,
                    logger=None,
                )
            except Exception as write_error:
                print(f"write_videofile错误: {write_error}")
                print(f"错误类型: {type(write_error)}")
                import traceback

                traceback.print_exc()
                raise write_error

            # 清理资源
            for clip in video_clips:
                clip.close()
            final_video.close()
            final_video_with_music.close()
            background_music.close()

            print(f"✅ 视频音乐合成完成: {output_path}")
            return True

        except Exception as e:
            print(f"❌ 视频音乐合成失败: {e}")
            return False

    def run(
        self,
        music_filename: Optional[str] = None,
        output_filename: str = "final_video_with_music.mp4",
    ) -> bool:
        """运行视频音乐合成"""
        print("🎵 开始视频音乐合成...")
        print("=" * 50)

        # 获取视频文件
        video_files = self.get_video_clips()
        if not video_files:
            print(f"❌ 在目录 {self.video_clips_dir} 中未找到任何视频文件")
            print("请确保已生成视频片段")
            return False

        print(f"找到 {len(video_files)} 个视频片段:")
        for video_file in video_files:
            print(f"  - {video_file.name}")

        # 获取音乐文件
        music_path = self.get_music_file(music_filename)
        if not music_path:
            print(f"❌ 未找到音乐文件: {music_filename}")
            print(f"请将音乐文件放置在: {self.music_dir}")
            return False

        print(f"使用音乐文件: {music_path.name}")

        # 执行合成
        success = self.compose_video_with_music(
            video_files, music_path, output_filename
        )

        if success:
            print("\n🎉 视频音乐合成成功完成!")
        else:
            print("\n❌ 视频音乐合成失败")

        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="视频音乐合成工具")
    parser.add_argument(
        "--music",
        "-m",
        type=str,
        default=None,
        help=f"音乐文件名 (默认: {config.video_music_default_file})",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="final_video_with_music.mp4",
        help="输出文件名 (默认: final_video_with_music.mp4)",
    )

    args = parser.parse_args()

    try:
        composer = VideoMusicComposer()
        success = composer.run(args.music, args.output)

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
