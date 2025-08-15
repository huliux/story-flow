"""
文本符号优化工具
用于替换Word文档中的特殊符号，为文本处理做准备
"""

import re
import sys
from pathlib import Path
from docx import Document
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# 尝试导入配置文件
try:
    from src.config import config
    USE_CONFIG = True
    print("已加载配置文件")
except ImportError:
    USE_CONFIG = False
    print("未找到配置文件，使用默认设置")

def replace_symbols():
    """执行符号替换操作"""
    # 如果有配置文件，默认打开输入目录
    if USE_CONFIG:
        initial_dir = str(config.input_dir)
    else:
        initial_dir = "."
    
    file_path = filedialog.askopenfilename(
        title="选择要处理的Word文档",
        filetypes=[("Word 文档", "*.docx")],
        initialdir=initial_dir
    )
    
    if not file_path:
        messagebox.showerror("错误", "请选择要替换的文件")
        return

    try:
        # 打开文档
        doc = Document(file_path)

        # 替换符号
        replacements = {
            r'.*第.*章.*\n': '',
            r'……': '。',
            r',': '，',
            r';': '。',
            r':': '，',
            r'：': '，',
            r'“': '，',
            r'”': '，',
            r'「': '',
            r'」': '',
            r'『': '',
            r'』': '',
            r'!': '。',
            r'！': '。',
            r'\?': '。',
            r'？': '。',
            r'。\d+': '。',
            r'。': '。\n\n'
        }
        
        for paragraph in doc.paragraphs:
            # 替换段落中的符号
            for replacement, replacement_value in replacements.items():
                paragraph.text = re.sub(replacement, replacement_value, paragraph.text)

        # 保存修改后的文档
        doc.save(file_path)

        # 如果有配置且保存的文件在输入目录中，提示用户
        if USE_CONFIG and Path(file_path).parent == config.input_dir:
            messagebox.showinfo("提示", f"替换完成！\n文件已保存：{file_path}\n\n文件位于输入目录中，可以被自动化脚本处理。")
        else:
            messagebox.showinfo("提示", f"替换完成！\n文件保存路径：{file_path}")
    except FileNotFoundError:
        messagebox.showerror("错误", "文件未找到，请重新选择文件")
    except PermissionError:
        messagebox.showerror("错误", "无权限访问文件，请检查文件是否被其他程序占用")
    except Exception as e:
        messagebox.showerror("错误！该文档被占用！", str(e))

def exit_application():
    sys.exit(0)

def main():
    # 创建主窗口
    root = tk.Tk()

    # 设置窗口标题
    root.title("Gm测试版")

    # 设置窗口大小
    root.geometry("250x100")

    # 创建一个开始按钮
    start_button = ttk.Button(root, text="选择文件并开始替换", command=replace_symbols)
    start_button.pack()

    # 创建一个结束按钮
    exit_button = ttk.Button(root, text="结束", command=exit_application)
    exit_button.pack()

    # 设置按钮样式
    style = ttk.Style()
    style.configure("Custom.TButton", foreground="white", background="blue", font=("Helvetica", 12, "bold"))

    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main()
