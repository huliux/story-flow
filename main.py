#!/usr/bin/env python3
"""
Story Flow - 自动化视频生成流水线

这是Story Flow项目的主入口文件，提供完整的自动化流水线功能。
支持从文本到视频的完整处理流程，包括文本分析、图像生成、语音合成和视频合成。

使用方法:
    python main.py              # 交互式菜单模式
    python main.py --auto       # 自动执行所有流程
    python main.py --help       # 显示帮助信息
"""

import sys
import os
import subprocess
import json
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import config
from src.story_generator import story_generator
from src.viral_video_generator import viral_video_generator

# 要运行的模块列表（按顺序执行）
MODULES = [
    "text_analyzer",
    "image_generator", 
    "voice_synthesizer",
    "video_composer"
]

def clean_output_files():
    """清理输出文件，为新的处理做准备"""
    try:
        import shutil
        
        # 需要清理的目录和文件
        cleanup_paths = [
            config.output_dir_txt / "txt.csv",  # CSV文件
            config.output_dir_image,   # 图片目录
            config.output_dir_voice,   # 音频目录
            # 注意：不清理videos目录
        ]
        
        for path in cleanup_paths:
            if path.exists():
                if path.is_file():
                    path.unlink()  # 删除文件
                    print(f"  已删除文件: {path.name}")
                elif path.is_dir():
                    # 清空目录但保留目录结构和.gitkeep文件
                    for item in path.iterdir():
                        # 跳过.gitkeep文件
                        if item.name == ".gitkeep":
                            continue
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    print(f"  已清空目录: {path.name}")
        
        print("  输出文件清理完成")
        
    except Exception as e:
        print(f"  清理输出文件时出错: {e}")
        # 不要因为清理失败而中断处理流程
        pass

def run_pipeline_module(module_name):
    """运行指定的pipeline模块"""
    try:
        print(f"正在运行 {module_name}...")
        
        # 构建命令
        cmd = [sys.executable, "-m", f"src.pipeline.{module_name}"]
        
        # 对于需要用户交互或需要显示进度的模块，直接运行不捕获输出
        if module_name in ["image_generator", "text_analyzer", "voice_synthesizer", "video_composer"]:
            result = subprocess.run(cmd, cwd=project_root, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        else:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )
        
        if result.returncode == 0:
            print(f"{module_name} 执行成功")
            if hasattr(result, 'stdout') and result.stdout:
                print(f"输出: {result.stdout.strip()}")
            return True
        else:
            print(f"{module_name} 执行失败")
            if hasattr(result, 'stderr') and result.stderr:
                print(f"错误: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"运行 {module_name} 时出错: {e}")
        return False

def run_direct_pipeline():
    """运行直接处理模式的完整流水线"""
    try:
        print("\n🚀 开始直接处理模式...")
        print("=" * 60)
        
        # 0. 清理之前的输出文件
        print("\n步骤 0/4: 清理之前的输出文件...")
        clean_output_files()
        
        # 1. 生成CSV文件
        print("\n步骤 1/4: 生成CSV文件...")
        if not run_pipeline_module("text_analyzer"):
            print("CSV文件生成失败，跳过后续步骤")
            return False
        
        # 2. 生成图片
        print("\n步骤 2/4: 生成图片...")
        if not run_image_generator(auto_mode=True):
            print("图片生成失败，跳过后续步骤")
            return False
        
        # 3. 生成音频
        print("\n步骤 3/4: 生成音频...")
        if not run_pipeline_module("voice_synthesizer"):
            print("音频生成失败，跳过视频合成")
            return False
        
        # 4. 合成视频
        print("\n步骤 4/4: 合成视频...")
        if not run_pipeline_module("video_composer"):
            print("视频合成失败")
            return False
        
        print("\n🎉 所有流程处理完成！")
        return True
        
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def ensure_input_file():
    """确保输入文件存在，如果不存在则生成故事内容"""
    # 检查input.md文件是否存在且包含有效内容
    if not story_generator.check_input_file_exists():
        print("\n📝 检测到没有有效的input.md文件")
        
        # 提示用户生成故事
        success = story_generator.generate_and_save_story()
        if not success:
            print("❌ 故事生成失败，无法继续")
            return False
    
    return True

# 章节处理相关函数已移除，采用直接处理模式

def run_text_analyzer():
    """运行文本分析器（生成故事板）"""
    if not ensure_chapters_file():
        return False
    print("\n正在生成故事板...")
    return run_pipeline_module("text_analyzer")

def run_image_generator(auto_mode=False):
    """运行图像生成器
    
    Args:
        auto_mode (bool): 是否启用自动化模式，跳过交互式重绘
    """
    print("\n正在生成图像...")
    
    try:
        # 先获取JSON文件路径（只选择一次）
        json_file = config.output_json_file
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
    except FileNotFoundError:
        print("❌ 未找到有效的JSON文件")
        return False
    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
        return False
    
    # 检查配置的图像生成服务
    image_service = config.image_generation_service
    print(f"使用图像生成服务: {image_service}")
    
    # 根据配置选择不同的生成方式，传递已选择的JSON文件路径
    if image_service == 'liblib':
        return run_liblib_generator_with_file(json_file, auto_mode)
    elif image_service == 'stable_diffusion':
        return run_stable_diffusion_generator_with_file(json_file, auto_mode)
    else:
        # 使用图像服务管理器（支持自动选择和回退）
        return run_image_service_manager_with_file(json_file, auto_mode)

def run_stable_diffusion_generator_with_file(json_file, auto_mode=False):
    """运行Stable Diffusion图像生成器（使用指定的JSON文件）"""
    print("使用Stable Diffusion服务生成图像...")
    
    try:
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        # 构建命令，传递JSON文件路径
        cmd = [sys.executable, "-m", "src.pipeline.image_generator", "--json-file", str(json_file)]
        if auto_mode:
            cmd.append("--auto")
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Stable Diffusion图像生成成功")
            return True
        else:
            print("❌ Stable Diffusion图像生成失败")
            return False
    except Exception as e:
        print(f"运行Stable Diffusion生成器时出错: {e}")
        return False

def run_stable_diffusion_generator(auto_mode=False):
    """运行Stable Diffusion图像生成器"""
    print("使用Stable Diffusion服务生成图像...")
    
    try:
        # 先获取JSON文件路径（可能触发用户选择）
        json_file = config.output_json_file
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        # 构建命令，传递JSON文件路径
        cmd = [sys.executable, "-m", "src.pipeline.image_generator", "--json-file", str(json_file)]
        if auto_mode:
            cmd.append("--auto")
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ Stable Diffusion图像生成成功")
            return True
        else:
            print("❌ Stable Diffusion图像生成失败")
            return False
    except FileNotFoundError:
        print("❌ 未找到有效的JSON文件")
        return False
    except KeyboardInterrupt:
        print("\n❌ 用户取消操作")
        return False
    except Exception as e:
        print(f"运行Stable Diffusion生成器时出错: {e}")
        return False

def run_liblib_generator_with_file(json_file, auto_mode=False):
    """运行LiblibAI图像生成器（使用指定的JSON文件）"""
    print("使用LiblibAI服务生成图像...")
    
    try:
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        # 构建命令，传递JSON文件路径
        cmd = [sys.executable, "-m", "src.liblib_standalone", "--json-file", str(json_file)]
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ LiblibAI图像生成成功")
            return True
        else:
            print("❌ LiblibAI图像生成失败")
            return False
    except Exception as e:
        print(f"运行LiblibAI生成器时出错: {e}")
        return False

def run_liblib_generator(auto_mode=False):
    """运行LiblibAI图像生成器"""
    print("使用LiblibAI服务生成图像...")
    
    try:
        # 获取JSON文件路径（可能会触发用户选择）
        try:
            json_file = config.output_json_file
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return False
        except KeyboardInterrupt:
            print("\n操作已取消")
            return False
            
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        output_dir = config.output_dir_image
        
        # 使用liblib独立脚本，直接传递选择的JSON文件路径
        cmd = [
            sys.executable, 
            "src/liblib_standalone.py",
            "--json-file", str(json_file),
            "--output-dir", str(output_dir),
            "--use-f1"  # 默认使用F.1模型
        ]
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("✅ LiblibAI图像生成成功")
            return True
        else:
            print("❌ LiblibAI图像生成失败")
            return False
    except Exception as e:
        print(f"运行LiblibAI生成器时出错: {e}")
        return False

def run_image_service_manager_with_file(json_file, auto_mode=False):
    """运行图像服务管理器（使用指定的JSON文件）"""
    print("使用图像服务管理器生成图像...")
    
    try:
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        # 使用新的图像管理器架构
        from src.managers.image_manager import ImageManager
        
        manager = ImageManager()
        
        # 从JSON文件批量生成图像
        success = manager.batch_generate_from_json(str(json_file))
        
        if success:
            print("✅ 图像服务管理器执行成功")
            return True
        else:
            print("❌ 图像服务管理器执行失败")
            return False
    except Exception as e:
        print(f"运行图像服务管理器时出错: {e}")
        return False

def run_image_service_manager(auto_mode=False):
    """运行图像服务管理器（支持自动选择和回退）"""
    print("使用图像服务管理器生成图像...")
    
    try:
        # 检查必要的文件
        json_file = config.output_json_file
        if not json_file.exists():
            print(f"错误: JSON文件不存在 - {json_file}")
            return False
        
        # 使用新的图像管理器架构
        from src.managers.image_manager import ImageManager
        
        manager = ImageManager()
        
        # 从JSON文件批量生成图像
        success = manager.batch_generate_from_json(str(json_file))
        
        if success:
            print("✅ 图像服务管理器执行成功")
            return True
        else:
            print("❌ 图像服务管理器执行失败")
            return False
    except Exception as e:
        print(f"运行图像服务管理器时出错: {e}")
        return False

def run_liblib_standalone():
    """运行LiblibAI独立生图工具 - 自动执行批量生图"""
    print("\n🎨 LiblibAI 独立生图工具")
    print("="*40)
    
    try:
        # 使用新的自动选择逻辑获取JSON文件
        try:
            json_file = config.output_json_file
        except FileNotFoundError as e:
            print(f"❌ {e}")
            print("请先运行 '生成故事板' 步骤")
            return False
        except KeyboardInterrupt:
            print("\n操作已取消")
            return False
        
        if not json_file.exists():
            print(f"❌ JSON文件不存在: {json_file}")
            print("请先运行 '生成故事板' 步骤")
            return False
        
        output_dir = config.output_dir_image
        
        # 默认使用F.1模型，不再询问用户
        cmd = [
            sys.executable, 
            "src/liblib_standalone.py",
            "--json-file", str(json_file),
            "--output-dir", str(output_dir),
            "--use-f1"  # 默认使用F.1模型
        ]
        
        print(f"\n正在从 {json_file} 批量生成图像...")
        print("使用F.1模型进行生成")
        
        # 执行命令，不捕获输出以显示实时进度条
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ LiblibAI图像生成成功")
            return True
        else:
            print(f"\n❌ LiblibAI图像生成失败，退出码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ 运行LiblibAI生图工具时出错: {e}")
        return False

def run_voice_synthesizer():
    """运行语音合成器"""
    print("\n🎵 开始生成音频...")
    
    # 检查章节文件
    if not ensure_chapters_file():
        return False
    
    # 获取JSON文件路径
    try:
        json_file_path = config.output_json_file
        success = run_voice_synthesizer_with_file(str(json_file_path))
    except (FileNotFoundError, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\n用户取消操作")
        else:
            print(f"\n❌ 未找到JSON文件: {e}")
        return False
    
    if success:
        print("\n✅ 音频生成完成")
    else:
        print("\n❌ 音频生成失败")
    
    return success

def run_voice_synthesizer_with_file(json_file_path):
    """使用指定的JSON文件运行语音合成器"""
    cmd = [sys.executable, "-m", "src.pipeline.voice_synthesizer", "--json-file", json_file_path]
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_video_composer():
    """运行视频合成器"""
    print("\n🎥 开始合成视频...")
    
    # 检查章节文件
    if not ensure_chapters_file():
        return False
    
    # 获取JSON文件路径
    try:
        json_file_path = config.output_json_file
        success = run_video_composer_with_file(str(json_file_path))
    except (FileNotFoundError, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\n用户取消操作")
        else:
            print(f"\n❌ 未找到JSON文件: {e}")
        return False
    
    if success:
        print("\n✅ 视频合成完成")
    else:
        print("\n❌ 视频合成失败")
    
    return success

def run_video_composer_with_file(json_file_path):
    """使用指定的JSON文件运行视频合成器"""
    cmd = [sys.executable, "-m", "src.pipeline.video_composer", "--json-file", json_file_path]
    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode == 0

def run_semantic_analyzer():
    """运行语义分析器"""
    print("\n🔍 语义分析器")
    print("="*40)
    
    # 检查输入文件是否存在
    if not config.input_md_file.exists():
        print(f"❌ 输入文件不存在: {config.input_md_file}")
        print("请先运行 '故事生成' 步骤")
        return False
    
    try:
        # 运行语义分析器
        cmd = [sys.executable, "src/semantic_analyzer.py"]
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ 语义分析完成")
            return True
        else:
            print(f"\n❌ 语义分析失败，退出码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n❌ 运行语义分析器时出错: {e}")
        return False

def display_main_menu():
    """显示主菜单"""
    print("\n" + "="*50)
    print("📚 Story Flow - AI故事视频生成器")
    print("="*50)
    print("请选择要执行的操作:")
    print("  1. 🚀 一键生成")
    print("  2. ✍️  故事创作 ")
    print("  3. 🔍 角色识别")
    print("  4. 📊 生成分镜")
    print("  5. 🖼️  SD生图")
    print("  6. 🎨 F1生图")
    print("  7. 🎵 生成音频")
    print("  8. 🎥 合成视频")
    print("  9. 🎬 爆款文案")
    print("  10. 🧹 清理文件")
    print("  11. ❓ 显示帮助")
    print("  0. 🚪 退出程序")
    print("")
    print("-"*60)

def show_help():
    """显示帮助信息"""
    print("\n" + "="*60)
    print("📖 Story Flow 使用帮助")
    print("="*60)
    print("")
    print("🔄 流程说明:")
    print("  1. 文本分割: 将输入的故事文本分割成章节")
    print("  2. 生成故事板: 分析文本内容，生成详细的故事板CSV文件")
    print("  3. 生成图像: 根据故事板生成对应的图像")
    print("  4. 生成音频: 将文本转换为语音")
    print("  5. 合成视频: 将图像和音频合成为最终视频")
    print("")
    print("📁 文件位置:")
    print(f"  输入文件: {config.input_dir}")
    print(f"  输出目录: {config.output_dir_txt.parent}")
    print(f"    - 文本处理: {config.output_dir_txt}")
    print(f"    - 图像输出: {config.output_dir_image}")
    print(f"    - 音频输出: {config.output_dir_voice}")
    print(f"    - 视频输出: {config.output_dir_video}")
    print("")
    print("💡 使用建议:")
    print("  - 首次使用建议选择 '自动执行所有流程'")
    print("  - 如需调试或重新生成某个步骤，可选择单独执行")
    print("  - 确保输入文件 (input.md 或 input.txt) 存在于输入目录")
    print("  - 确保角色映射文件 (character_mapping.json) 已正确配置")
    print("-"*60)

def get_user_choice():
    """获取用户选择"""
    while True:
        try:
            choice = input("请输入选项编号 (0-11): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']:
                return int(choice)
            else:
                print("❌ 无效选项，请输入 0-11 之间的数字")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ 输入无效，请重新输入")

def run_auto_pipeline():
    """自动执行完整流水线"""
    print("\n🚀 开始自动执行所有流程...")
    
    # 确保输入文件存在
    if not ensure_input_file():
        return False
    
    # 运行完整流水线
    success = run_direct_pipeline()
    if success:
        print("\n🎉 所有流程执行完成！")
        return True
    else:
        print("\n❌ 流程执行失败")
        return False

def run_interactive_mode():
    """交互式菜单模式"""
    while True:
        display_main_menu()
        choice = get_user_choice()
        
        if choice == 0:
            print("\n👋 感谢使用 Story Flow，再见！")
            break
        elif choice == 1:
            run_auto_pipeline()
        elif choice == 2:
            success = story_generator.generate_new_story_force()
            if success:
                print("\n✅ 故事生成完成")
            else:
                print("\n❌ 故事生成失败")
        elif choice == 3:
            success = run_semantic_analyzer()
            if success:
                print("\n✅ 语义分析完成")
            else:
                print("\n❌ 语义分析失败")
        elif choice == 4:
            if ensure_input_file():
                success = run_pipeline_module("text_analyzer")
                if success:
                    print("\n✅ 故事板生成完成")
                else:
                    print("\n❌ 故事板生成失败")
        elif choice == 5:
            if ensure_input_file():
                success = run_image_generator()
                if success:
                    print("\n✅ 图像生成完成")
                else:
                    print("\n❌ 图像生成失败")
        elif choice == 6:
            success = run_liblib_standalone()
            if success:
                print("\n✅ LiblibAI图像生成完成")
            else:
                print("\n❌ LiblibAI图像生成失败")
        elif choice == 7:
            if ensure_input_file():
                success = run_pipeline_module("voice_synthesizer")
                if success:
                    print("\n✅ 音频生成完成")
                else:
                    print("\n❌ 音频生成失败")
        elif choice == 8:
            if ensure_input_file():
                success = run_pipeline_module("video_composer")
                if success:
                    print("\n✅ 视频合成完成")
                else:
                    print("\n❌ 视频合成失败")
        elif choice == 9:
            success = viral_video_generator.generate_complete_workflow()
            if success:
                print("\n✅ 爆款视频大纲和提示词生成完成")
            else:
                print("\n❌ 爆款视频生成失败")
        elif choice == 10:
            clean_output_files()
            print("\n✅ 输出文件清理完成")
        elif choice == 11:
            display_help()
        
        # 如果不是退出，询问是否继续
        if choice != 0:
            print("\n" + "-"*40)
            continue_choice = input("按回车键返回主菜单，或输入 'q' 退出: ").strip().lower()
            if continue_choice == 'q':
                print("\n👋 感谢使用 Story Flow，再见！")
                break
    
    return True

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Story Flow - 自动化视频生成流水线',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py              # 启动交互式菜单
  python main.py --auto       # 自动执行所有流程
  python main.py --generate   # 仅生成新故事
  python main.py --semantic   # 仅执行语义分析
  python main.py --split      # 仅执行文本分割
  python main.py --analyze    # 仅生成故事板
  python main.py --images     # 仅生成图像
  python main.py --liblib     # 使用LiblibAI生成图像
  python main.py --audio      # 仅生成音频
  python main.py --video      # 仅合成视频
  python main.py --viral      # 生成爆款视频大纲和提示词
        """
    )
    
    parser.add_argument('--auto', action='store_true', 
                       help='自动执行所有流程')
    parser.add_argument('--generate', action='store_true', 
                       help='仅生成新故事')
    parser.add_argument('--semantic', action='store_true', 
                       help='仅执行语义分析')
    parser.add_argument('--split', action='store_true', 
                       help='仅执行文本分割')
    parser.add_argument('--analyze', action='store_true', 
                       help='仅生成故事板')
    parser.add_argument('--images', action='store_true', 
                       help='仅生成图像')
    parser.add_argument('--liblib', action='store_true', 
                       help='使用LiblibAI生成图像')
    parser.add_argument('--audio', action='store_true', 
                       help='仅生成音频')
    parser.add_argument('--video', action='store_true', 
                       help='仅合成视频')
    parser.add_argument('--viral', action='store_true', 
                       help='生成爆款视频大纲和提示词')
    parser.add_argument('--help-detailed', action='store_true', 
                       help='显示详细帮助信息')
    
    return parser.parse_args()

def main():
    """主函数"""
    print("🎬 Story Flow 自动化流水线启动...")
    print(f"  项目根目录: {project_root}")
    print(f"  输入目录: {config.input_dir}")
    
    # 确保输入目录存在
    config.input_dir.mkdir(parents=True, exist_ok=True)
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("❌ 配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # 解析命令行参数
    args = parse_arguments()
    
    # 如果没有命令行参数，检查input.md文件是否存在且有效
    if not any([args.auto, args.generate, args.semantic, args.split, args.analyze, args.images, args.liblib, args.audio, args.video, args.viral, args.help_detailed]):
        if not story_generator.check_input_file_exists():
            print("\n📝 检测到没有有效的input.md文件")
            success = story_generator.generate_and_save_story()
            if not success:
                print("❌ 故事生成失败，无法继续")
                return False
            print("\n✅ 故事生成完成，现在进入主菜单")
    
    # 显示详细帮助
    if args.help_detailed:
        show_help()
        return True
    
    # 根据参数执行相应功能
    if args.auto:
        return run_auto_pipeline()
    elif args.generate:
        success = story_generator.generate_and_save_story()
        print("\n✅ 故事生成完成" if success else "\n❌ 故事生成失败")
        return success
    elif args.semantic:
        success = run_semantic_analyzer()
        print("\n✅ 语义分析完成" if success else "\n❌ 语义分析失败")
        return success
    elif args.split:
        success = run_text_splitter()
        print("\n✅ 文本分割完成" if success else "\n❌ 文本分割失败")
        return success
    elif args.analyze:
        success = run_text_analyzer()
        print("\n✅ 故事板生成完成" if success else "\n❌ 故事板生成失败")
        return success
    elif args.images:
        success = run_image_generator()
        print("\n✅ 图像生成完成" if success else "\n❌ 图像生成失败")
        return success
    elif args.liblib:
        success = run_liblib_standalone()
        print("\n✅ LiblibAI图像生成完成" if success else "\n❌ LiblibAI图像生成失败")
        return success
    elif args.audio:
        success = run_voice_synthesizer()
        print("\n✅ 音频生成完成" if success else "\n❌ 音频生成失败")
        return success
    elif args.video:
        success = run_video_composer()
        print("\n✅ 视频合成完成" if success else "\n❌ 视频合成失败")
        return success
    elif args.viral:
        success = viral_video_generator.generate_complete_workflow()
        print("\n✅ 爆款视频大纲和提示词生成完成" if success else "\n❌ 爆款视频生成失败")
        return success
    else:
        # 默认启动交互式模式
        return run_interactive_mode()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
