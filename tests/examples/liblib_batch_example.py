#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LiblibAI批量生图示例
使用liblib_service读取sd_prompt.json文件并批量生成图片
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.image.liblib_service import LiblibService, LiblibConfig
from src.config import config

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='LiblibAI批量图像生成')
    parser.add_argument('--input', '-i', 
                       default='data/output/processed/sd_prompt.json',
                       help='输入的JSON文件路径（支持新旧格式）')
    parser.add_argument('--output', '-o', 
                       default='data/output/images',
                       help='输出图片目录')
    parser.add_argument('--use-f1', action='store_true', default=True,
                       help='使用F.1模型（默认启用）')
    parser.add_argument('--width', type=int, default=1024,
                       help='图片宽度（默认1024）')
    parser.add_argument('--height', type=int, default=1024,
                       help='图片高度（默认1024）')
    parser.add_argument('--steps', type=int, default=20,
                       help='采样步数（默认20）')
    parser.add_argument('--img-count', type=int, default=1,
                       help='每个提示词生成的图片数量（默认1）')
    parser.add_argument('--seed', type=int, default=-1,
                       help='随机种子（默认-1为随机）')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"错误：输入文件不存在 - {input_file}")
        return False
    
    print(f"输入文件: {input_file}")
    print(f"输出目录: {args.output}")
    print(f"使用F.1模型: {args.use_f1}")
    print(f"图片尺寸: {args.width}x{args.height}")
    print(f"采样步数: {args.steps}")
    print(f"每个提示词生成图片数: {args.img_count}")
    
    try:
        # 创建LiblibConfig
        liblib_config = LiblibConfig(
            access_key=config.liblib_access_key,
            secret_key=config.liblib_secret_key,
            base_url=config.liblib_base_url,
            timeout=config.liblib_timeout,
            max_retries=config.liblib_max_retries,
            retry_delay=config.liblib_retry_delay
        )
        
        # 检查API密钥
        if not liblib_config.access_key or not liblib_config.secret_key:
            print("错误：LiblibAI API密钥未配置")
            print("请设置环境变量 LIBLIB_ACCESS_KEY 和 LIBLIB_SECRET_KEY")
            return False
        
        # 初始化LiblibService
        service = LiblibService(liblib_config, config)
        
        # 执行批量生图
        print("\n开始批量生图...")
        generated_files = service.batch_generate_from_json(
            json_file_path=str(input_file),
            output_dir=args.output,
            use_f1=args.use_f1,
            width=args.width,
            height=args.height,
            steps=args.steps,
            img_count=args.img_count,
            seed=args.seed
        )
        
        print(f"\n✅ 批量生图完成！")
        print(f"生成了 {len(generated_files)} 张图片")
        print(f"图片保存在: {args.output}")
        
        return True
        
    except Exception as e:
        print(f"❌ 批量生图失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
