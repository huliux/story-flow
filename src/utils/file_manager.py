import os
import sys
import shutil
import re
from pathlib import Path

# 尝试导入配置文件
try:
    from src.config import config
    input_path = Path(input("输入源目录路径: ") or "D:\\so-vits-svc\\results")
    output_path = config.output_dir_voice
    print(f"使用配置文件中的输出路径: {output_path}")
except ImportError:
    print("未找到config.py，使用默认路径")
    input_path = Path(input("输入源目录路径: ") or "D:\\so-vits-svc\\results")
    output_path = Path(input("输入目标目录路径: ") or "D:\\txt_to_video\\voice")

print(f"音频文件移动工具")
print(f"源目录: {input_path}")
print(f"目标目录: {output_path}")

def main():
    """主函数：执行音频文件移动和重命名"""
    # 检查源目录
    if not input_path.exists():
        print(f"错误: 源目录不存在 - {input_path}")
        return False
    
    # 确保目标目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 读取输入文件夹中的文件，并获取文件名中的数字，然后按数字排序
    try:
        input_files = [f for f in os.listdir(input_path) if f.endswith('.wav')]
        input_files.sort(key=lambda name: int(re.findall('\d+', name)[0]) if re.findall('\d+', name) else float('inf'))
        
        if not input_files:
            print("错误: 未找到任何.wav文件")
            return False
        
        print(f"找到 {len(input_files)} 个wav文件")
        
        # 对于每个文件
        moved_count = 0
        for i, filename in enumerate(input_files, 1):
            # 获取完整的输入文件路径
            full_input_path = input_path / filename

            # 生成新的文件名
            new_filename = f'output_{i}.wav'
            full_output_path = output_path / new_filename

            try:
                # 如果输出路径中已存在同名文件，则先删除
                if full_output_path.exists():
                    full_output_path.unlink()

                # 将文件重命名并移动到输出文件夹
                shutil.move(str(full_input_path), str(full_output_path))
                moved_count += 1
                print(f"移动: {filename} -> {new_filename}")
                
            except Exception as e:
                print(f"移动文件失败 {filename}: {e}")

        print(f'文件重命名和移动操作完成。成功移动 {moved_count} 个文件。')
        return True
        
    except Exception as e:
        print(f"处理过程出错: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)
