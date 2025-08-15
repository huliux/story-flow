#!/usr/bin/env python3
"""
项目清理工具
清理生成的文件、临时文件和示例数据
"""

import os
import shutil
import sys
from pathlib import Path
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config

def get_directory_size(directory):
    """计算目录大小"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, FileNotFoundError):
        pass
    return total_size

def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"

def clean_directory(directory, description, confirm=True):
    """清理指定目录"""
    if not directory.exists():
        print(f"📁 {description}: 目录不存在，跳过")
        return True
    
    # 计算大小
    size = get_directory_size(directory)
    file_count = len([f for f in directory.rglob('*') if f.is_file()])
    
    if file_count == 0:
        print(f"📁 {description}: 目录为空，跳过")
        return True
    
    print(f"📁 {description}: {file_count} 个文件，{format_size(size)}")
    
    if confirm:
        response = input(f"删除 {description} 中的所有文件？(y/n): ")
        if response.lower() != 'y':
            print(f"跳过清理 {description}")
            return False
    
    try:
        # 删除目录内容但保留目录
        for item in directory.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        
        print(f"✅ 已清理 {description}")
        return True
    except Exception as e:
        print(f"❌ 清理 {description} 失败: {e}")
        return False

def clean_specific_files():
    """清理特定的无用文件"""
    files_to_clean = [
        # Excel临时文件
        Path("txt") / "~$txt.xlsx",
        # 可能的临时文件
        Path(".DS_Store"),
        Path("Thumbs.db"),
        # 备份文件
        *Path().glob("*.bak"),
        *Path().glob("*.backup"),
        *Path().glob("*.tmp"),
        *Path().glob("*.temp"),
    ]
    
    cleaned_count = 0
    for file_path in files_to_clean:
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"🗑️  删除临时文件: {file_path}")
                cleaned_count += 1
            except Exception as e:
                print(f"❌ 删除失败 {file_path}: {e}")
    
    if cleaned_count > 0:
        print(f"✅ 清理了 {cleaned_count} 个临时文件")
    else:
        print("📁 未发现临时文件")

def move_input_files():
    """将根目录的输入文件移动到input目录"""
    root_files = [
        Path("input.txt"),
        Path("input.docx")
    ]
    
    input_dir = config.input_dir
    input_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    for file_path in root_files:
        if file_path.exists():
            try:
                target_path = input_dir / file_path.name
                if target_path.exists():
                    print(f"⚠️  目标文件已存在: {target_path}")
                    response = input(f"覆盖 {target_path.name}？(y/n): ")
                    if response.lower() != 'y':
                        continue
                
                shutil.move(str(file_path), str(target_path))
                print(f"📦 移动文件: {file_path} -> {target_path}")
                moved_count += 1
            except Exception as e:
                print(f"❌ 移动失败 {file_path}: {e}")
    
    if moved_count > 0:
        print(f"✅ 移动了 {moved_count} 个输入文件到input目录")

def main():
    """主函数"""
    print("=== 项目清理工具 ===\n")
    
    print("正在分析项目文件...")
    
    # 定义要清理的目录
    directories_to_clean = [
        (config.output_dir_image, "生成的图片文件"),
        (config.output_dir_voice, "生成的语音文件"),
        (config.output_dir_video, "生成的视频文件"),
        (config.output_dir_temp, "临时文件"),
    ]
    
    print("\n📊 文件统计:")
    total_size = 0
    total_files = 0
    
    for directory, description in directories_to_clean:
        size = get_directory_size(directory)
        file_count = len([f for f in directory.rglob('*') if f.is_file()]) if directory.exists() else 0
        total_size += size
        total_files += file_count
        print(f"  {description}: {file_count} 个文件, {format_size(size)}")
    
    print(f"\n📈 总计: {total_files} 个文件, {format_size(total_size)}")
    
    if total_files == 0:
        print("✅ 没有需要清理的生成文件")
    else:
        print(f"\n⚠️  将释放 {format_size(total_size)} 的磁盘空间")
        
        # 选择清理模式
        print("\n清理选项:")
        print("1. 交互式清理 (推荐)")
        print("2. 清理所有生成文件")
        print("3. 只清理临时文件")
        print("4. 取消")
        
        choice = input("\n选择操作 (1-4): ").strip()
        
        if choice == '1':
            # 交互式清理
            for directory, description in directories_to_clean:
                clean_directory(directory, description, confirm=True)
        elif choice == '2':
            # 清理所有
            confirm = input("确认清理所有生成文件？(y/n): ")
            if confirm.lower() == 'y':
                for directory, description in directories_to_clean:
                    clean_directory(directory, description, confirm=False)
        elif choice == '3':
            # 只清理临时文件
            clean_directory(config.output_dir_temp, "临时文件", confirm=False)
        elif choice == '4':
            print("取消清理")
            return
        else:
            print("无效选择")
            return
    
    # 清理特定文件
    print("\n🧹 清理临时文件...")
    clean_specific_files()
    
    # 整理输入文件
    print("\n📦 整理输入文件...")
    move_input_files()
    
    print("\n🎉 清理完成！")
    
    # 显示清理后的状态
    remaining_size = sum(get_directory_size(d) for d, _ in directories_to_clean)
    if remaining_size < total_size:
        freed_size = total_size - remaining_size
        print(f"💾 释放了 {format_size(freed_size)} 磁盘空间")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断清理")
        sys.exit(1)
    except Exception as e:
        print(f"清理过程出错: {e}")
        sys.exit(1)
