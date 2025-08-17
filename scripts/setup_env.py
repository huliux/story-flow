#!/usr/bin/env python3
"""
环境设置脚本
帮助用户快速配置环境变量和初始化项目
"""

import os
import sys
from pathlib import Path
import shutil

def create_env_file():
    """创建.env文件"""
    env_example = Path("env.example")
    env_file = Path(".env")
    
    if env_file.exists():
        response = input(".env文件已存在，是否覆盖？(y/n): ")
        if response.lower() != 'y':
            print("跳过.env文件创建")
            return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print(f"✅ 已创建.env文件（基于{env_example}）")
        print("⚠️  请编辑.env文件，填入您的API密钥和配置")
    else:
        print(f"❌ 未找到{env_example}文件")

def setup_directories():
    """创建必要的目录"""
    directories = [
        "input",
        "txt", 
        "image",
        "voice",
        "video",
        "temp"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ 目录已创建: {dir_name}")

def check_dependencies():
    """检查依赖安装"""
    print("\n检查Python依赖...")
    
    required_packages = [
        "dotenv",
        "openai", 
        "azure.cognitiveservices.speech",
        "requests",
        "spacy",
        "tqdm",
        "moviepy",
        "PIL",
        "numpy",
        "pandas"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "dotenv":
                import dotenv
            elif package == "azure.cognitiveservices.speech":
                import azure.cognitiveservices.speech

            elif package == "PIL":
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("\n✅ 所有依赖已安装")
    return True

def check_spacy_model():
    """检查spaCy中文模型"""
    try:
        import spacy
        nlp = spacy.load('zh_core_web_sm')
        print("✅ spaCy中文模型已安装")
        return True
    except OSError:
        print("❌ spaCy中文模型未安装")
        print("请运行: python -m spacy download zh_core_web_sm")
        return False

def validate_config():
    """验证配置文件"""
    try:
        import sys
        sys.path.append('.')
        from src.config import config
        errors = config.validate_config()
        
        if errors:
            print("\n❌ 配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("\n✅ 配置验证通过")
            config.print_config_summary()
            return True
    except ImportError:
        print("❌ 无法导入config模块")
        return False

def main():
    """主函数"""
    print("=== 文本到视频生成系统环境设置 ===\n")
    
    # 1. 创建.env文件
    print("1. 创建环境配置文件...")
    create_env_file()
    
    # 2. 创建目录
    print("\n2. 创建项目目录...")
    setup_directories()
    
    # 3. 检查依赖
    print("\n3. 检查依赖...")
    deps_ok = check_dependencies()
    
    # 4. 检查spaCy模型
    print("\n4. 检查spaCy模型...")
    spacy_ok = check_spacy_model()
    
    # 5. 验证配置
    print("\n5. 验证配置...")
    if Path(".env").exists():
        config_ok = validate_config()
    else:
        config_ok = False
        print("请先配置.env文件")
    
    # 总结
    print("\n=== 设置总结 ===")
    
    if deps_ok and spacy_ok and config_ok:
        print("🎉 环境设置完成！您可以开始使用系统了。")
        print("\n快速开始:")
        print("1. 将 Markdown 文件放入 data/input/input.md")
        print("2. 运行: python src/pipeline/text_splitter.py")
        print("3. 或者直接运行: python scripts/auto_pipeline.py (全自动模式)")
    else:
        print("⚠️  环境设置未完成，请解决上述问题后重新运行。")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n用户中断设置")
        sys.exit(1)
    except Exception as e:
        print(f"设置过程出错: {e}")
        sys.exit(1)
