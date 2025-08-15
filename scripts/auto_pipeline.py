import os
import sys
import subprocess
import glob
import shutil
import time
from pathlib import Path
from tqdm import tqdm
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import config

def print_warning():
    print("自动化流水线运行中...")
    return True

def assert_warning_exists():
    try:
        return print_warning()
    except NameError:
        sys.exit()

if assert_warning_exists():
    pass

# 获取脚本目录和配置
script_dir = Path(__file__).parent.absolute()

# 定义脚本列表（使用实际的文件名）
project_root = script_dir.parent
scripts = [
    project_root / 'src/pipeline/text_splitter.py',
    project_root / 'src/pipeline/text_analyzer.py',
    project_root / 'src/pipeline/image_generator.py',
    project_root / 'src/pipeline/voice_synthesizer.py',
    project_root / 'src/pipeline/video_composer.py'
]

# 使用配置文件中的路径
input_dir = config.input_dir
output_file_path = config.input_docx_file

# 使用配置的Python可执行文件
python_executable = config.python_executable

print(f"自动化脚本配置:")
print(f"  脚本目录: {script_dir}")
print(f"  输入目录: {input_dir}")
print(f"  Python解释器: {python_executable}") 

def run_pipeline():
    """运行完整的处理流水线"""
    try:
        # 检查所有脚本是否存在
        missing_scripts = [script for script in scripts if not script.exists()]
        if missing_scripts:
            print("错误: 以下脚本文件不存在:")
            for script in missing_scripts:
                print(f"  - {script}")
            return False

        # 运行每个步骤
        for i, script in enumerate(scripts, 1):
            print(f'\n=== 步骤 {i}: 运行 {script.name} ===')
            
            try:
                result = subprocess.run(
                    [python_executable, str(script)], 
                    capture_output=False,
                    check=True
                )
                print(f'步骤 {i} 完成')
            except subprocess.CalledProcessError as e:
                print(f'步骤 {i} 失败，退出码: {e.returncode}')
                return False
            except Exception as e:
                print(f'步骤 {i} 执行异常: {e}')
                return False

        print('\n=== 流水线执行完成 ===')
        return True
        
    except Exception as e:
        print(f'流水线执行异常: {e}')
        return False

def main():
    """主函数：自动化处理文档文件"""
    print("开始自动化处理...")
    
    # 确保输入目录存在
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False

    processed_count = 0
    
    while True:
        # 查找待处理的docx文件
        docx_pattern = str(input_dir / '*.docx')
        docx_files = glob.glob(docx_pattern)
        
        if not docx_files:
            print("没有找到待处理的docx文件，等待新文件...")
            time.sleep(10)
            continue
        
        # 按文件名排序，选择最小编号的文件
        try:
            min_file = min(docx_files, key=lambda x: int(Path(x).stem.split('_')[-1]))
        except (ValueError, IndexError):
            # 如果无法解析编号，使用第一个文件
            min_file = docx_files[0]
        
        print(f'\n发现待处理文件: {min_file}')
        
        # 移动文件到标准位置
        try:
            if output_file_path.exists():
                output_file_path.unlink()
            
            shutil.move(min_file, output_file_path)
            print(f'文件已移动到: {output_file_path}')
            
        except Exception as e:
            print(f'移动文件失败: {e}')
            continue

        # 运行处理流水线
        success = run_pipeline()
        
        if success:
            processed_count += 1
            print(f'\n✅ 第 {processed_count} 个文件处理完成')
        else:
            print(f'\n❌ 文件处理失败')
            # 如果处理失败，可以选择是否继续
            response = input("是否继续处理下一个文件？(y/n): ")
            if response.lower() != 'y':
                break

        # 检查是否还有更多文件
        remaining_files = glob.glob(docx_pattern)
        if remaining_files:
            print(f'\n还有 {len(remaining_files)} 个文件待处理')
            print('等待10秒后开始下一轮处理...')
            
            for _ in tqdm(range(10), desc="等待中"):
                time.sleep(1)
        else:
            print('\n所有文件处理完成，等待新文件...')
            time.sleep(10)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)
