#!/usr/bin/env python3
"""
LiblibAI独立图像生成脚本

这个脚本允许用户独立运行LiblibAI服务来生成图片，支持：
1. 从JSON文件批量生成图片
2. 单个提示词生成图片
3. F.1模型和传统模型
4. 图生图功能

使用示例：
    # 从JSON文件批量生成
    python liblib_standalone.py --json-file prompts.json --output-dir ./output
    
    # 单个提示词生成
    python liblib_standalone.py --prompt "一只可爱的小猫" --output-dir ./output
    
    # 使用F.1模型
    python liblib_standalone.py --prompt "美丽的风景" --use-f1 --output-dir ./output
    
    # 图生图
    python liblib_standalone.py --prompt "改成卡通风格" --input-image ./input.jpg --output-dir ./output
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm

# 添加项目根目录和src目录到Python路径
project_root = Path(__file__).parent.parent  # 项目根目录
src_dir = Path(__file__).parent  # src目录

# 添加路径到sys.path
for path in [str(project_root), str(src_dir)]:
    if path not in sys.path:
        sys.path.insert(0, path)

try:
    # 尝试从src目录导入
    from config import config
    from services.image.liblib_service import LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork, HiResFixInfo
except ImportError as e1:
    try:
        # 尝试从项目根目录导入
        from src.config import config
        from src.services.image.liblib_service import LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork, HiResFixInfo
    except ImportError as e2:
        try:
            # 尝试相对导入
            from .config import config
            from .services.image.liblib_service import LiblibService, LiblibConfig, F1GenerationParams, AdditionalNetwork, HiResFixInfo
        except ImportError as e3:
            print("错误: 无法导入必要的模块，请确保在正确的目录中运行脚本")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"脚本路径: {Path(__file__).parent}")
            print(f"项目根目录: {project_root}")
            print(f"sys.path: {sys.path[:5]}...")  # 显示前5个路径
            print(f"导入错误1: {e1}")
            print(f"导入错误2: {e2}")
            print(f"导入错误3: {e3}")
            sys.exit(1)


def create_liblib_service() -> LiblibService:
    """创建LiblibAI服务实例"""
    liblib_config = LiblibConfig(
        access_key=config.liblib_access_key,
        secret_key=config.liblib_secret_key,
        base_url=config.liblib_base_url,
        timeout=config.liblib_timeout,
        max_retries=config.liblib_max_retries,
        retry_delay=config.liblib_retry_delay
    )
    
    if not liblib_config.access_key or not liblib_config.secret_key:
        print("错误: 请在环境变量中设置LIBLIB_ACCESS_KEY和LIBLIB_SECRET_KEY")
        sys.exit(1)
    
    return LiblibService(liblib_config, config)


def generate_single_image(
    service: LiblibService,
    prompt: str,
    output_dir: Path,
    use_f1: bool = False,
    input_image: Optional[Path] = None,
    output_filename: Optional[str] = None,  # 新增参数，允许指定输出文件名
    **kwargs
) -> bool:
    """生成单张图片，参考image_generator.py的逻辑"""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 添加触发词到prompt前面
        trigger_words = config.liblib_trigger_words
        if trigger_words and trigger_words.strip():
            # 如果prompt已经包含触发词，则不重复添加
            if not prompt.startswith(trigger_words.strip()):
                prompt = f"{trigger_words.strip()}, {prompt}"
        
        if input_image and input_image.exists():
            # 图生图模式暂不支持
            print("错误: 当前版本暂不支持图生图功能")
            return False
        else:
            # 文生图模式
            if use_f1:
                # 使用from_config方法创建参数，这样会自动包含hiResFixInfo
                params = F1GenerationParams.from_config(prompt, config)
                
                # 更新用户指定的参数
                params.prompt = prompt
                if 'width' in kwargs:
                    params.width = kwargs['width']
                if 'height' in kwargs:
                    params.height = kwargs['height']
                if 'steps' in kwargs:
                    params.steps = kwargs['steps']
                if 'img_count' in kwargs:
                    params.img_count = kwargs['img_count']
                if 'seed' in kwargs:
                    params.seed = kwargs['seed']
                if 'restore_faces' in kwargs:
                    params.restore_faces = kwargs['restore_faces']
                if 'template_uuid' in kwargs:
                    params.template_uuid = kwargs['template_uuid']
                if 'negative_prompt' in kwargs:
                    params.negative_prompt = kwargs['negative_prompt']
                elif config.liblib_negative_prompt:
                    params.negative_prompt = config.liblib_negative_prompt
                if 'cfg_scale' in kwargs:
                    params.cfg_scale = kwargs['cfg_scale']
                if 'randn_source' in kwargs:
                    params.randn_source = kwargs['randn_source']
                if 'clip_skip' in kwargs:
                    params.clip_skip = kwargs['clip_skip']
                if 'sampler' in kwargs:
                    params.sampler = kwargs['sampler']
                
                # 处理AdditionalNetwork - 如果用户提供了lora参数，则覆盖默认配置
                if 'lora_model_id' in kwargs or 'lora_weight' in kwargs:
                    lora_model_id = kwargs.get('lora_model_id')
                    lora_weight = kwargs.get('lora_weight', 1.0)
                    if lora_model_id:
                        params.additional_network = [AdditionalNetwork(
                            model_id=lora_model_id,
                            weight=lora_weight
                        )]
                    else:
                        params.additional_network = []
                
                # 如果用户提供了高分辨率修复参数，则覆盖默认值
                if any(key in kwargs for key in ['hires_steps', 'hires_denoising_strength', 'upscaler', 'resized_width', 'resized_height']):
                    if params.hi_res_fix_info is None:
                        params.hi_res_fix_info = HiResFixInfo(
                            hires_steps=20,
                            hires_denoising_strength=0.75,
                            upscaler=10,
                            resized_width=1024,
                            resized_height=1536
                        )
                    
                    if 'hires_steps' in kwargs:
                        params.hi_res_fix_info.hires_steps = kwargs['hires_steps']
                    if 'hires_denoising_strength' in kwargs:
                        params.hi_res_fix_info.hires_denoising_strength = kwargs['hires_denoising_strength']
                    if 'upscaler' in kwargs:
                        params.hi_res_fix_info.upscaler = kwargs['upscaler']
                    if 'resized_width' in kwargs:
                        params.hi_res_fix_info.resized_width = kwargs['resized_width']
                    if 'resized_height' in kwargs:
                        params.hi_res_fix_info.resized_height = kwargs['resized_height']
                
                result = service.f1_text_to_image(params)
            else:
                # 使用F1 API（因为传统text_to_image方法未实现）
                # 使用from_config方法创建参数，这样会自动包含hiResFixInfo
                params = F1GenerationParams.from_config(prompt, config)
                
                # 更新用户指定的参数
                params.prompt = prompt
                if 'width' in kwargs:
                    params.width = kwargs['width']
                else:
                    params.width = 512  # 非F1模式的默认宽度
                if 'height' in kwargs:
                    params.height = kwargs['height']
                else:
                    params.height = 512  # 非F1模式的默认高度
                if 'steps' in kwargs:
                    params.steps = kwargs['steps']
                else:
                    params.steps = config.liblib_default_steps
                if 'img_count' in kwargs:
                    params.img_count = kwargs['img_count']
                else:
                    params.img_count = 1
                if 'restore_faces' in kwargs:
                    params.restore_faces = kwargs['restore_faces']
                else:
                    params.restore_faces = False
                if 'seed' in kwargs:
                    params.seed = kwargs['seed']
                else:
                    params.seed = -1
                if 'negative_prompt' in kwargs:
                    params.negative_prompt = kwargs['negative_prompt']
                elif config.liblib_negative_prompt:
                    params.negative_prompt = config.liblib_negative_prompt
                if 'cfg_scale' in kwargs:
                    params.cfg_scale = kwargs['cfg_scale']
                if 'randn_source' in kwargs:
                    params.randn_source = kwargs['randn_source']
                if 'clip_skip' in kwargs:
                    params.clip_skip = kwargs['clip_skip']
                if 'sampler' in kwargs:
                    params.sampler = kwargs['sampler']
                
                # 处理AdditionalNetwork - 如果用户提供了lora参数，则覆盖默认配置
                if 'lora_model_id' in kwargs or 'lora_weight' in kwargs:
                    lora_model_id = kwargs.get('lora_model_id')
                    lora_weight = kwargs.get('lora_weight', 1.0)
                    if lora_model_id:
                        params.additional_network = [AdditionalNetwork(
                            model_id=lora_model_id,
                            weight=lora_weight
                        )]
                    else:
                        params.additional_network = []
                
                # 如果用户提供了高分辨率修复参数，则覆盖默认值
                if any(key in kwargs for key in ['hires_steps', 'hires_denoising_strength', 'upscaler', 'resized_width', 'resized_height']):
                    if params.hi_res_fix_info is None:
                        params.hi_res_fix_info = HiResFixInfo(
                            hires_steps=20,
                            hires_denoising_strength=0.75,
                            upscaler=10,
                            resized_width=1024,
                            resized_height=1536
                        )
                    
                    if 'hires_steps' in kwargs:
                        params.hi_res_fix_info.hires_steps = kwargs['hires_steps']
                    if 'hires_denoising_strength' in kwargs:
                        params.hi_res_fix_info.hires_denoising_strength = kwargs['hires_denoising_strength']
                    if 'upscaler' in kwargs:
                        params.hi_res_fix_info.upscaler = kwargs['upscaler']
                    if 'resized_width' in kwargs:
                        params.hi_res_fix_info.resized_width = kwargs['resized_width']
                    if 'resized_height' in kwargs:
                        params.hi_res_fix_info.resized_height = kwargs['resized_height']
                result = service.f1_text_to_image(params)
        
        if result and result.generate_uuid:
            print(f"任务已提交，UUID: {result.generate_uuid}")
            
            # 等待任务完成并获取结果
            import time
            max_wait_time = 300  # 最大等待5分钟
            check_interval = 5   # 每5秒检查一次
            waited_time = 0
            
            while waited_time < max_wait_time:
                try:
                    status_result = service.get_generate_status(result.generate_uuid)
                    
                    if status_result.status.value == 5:  # SUCCESS
                        if status_result.images:
                            for i, image_data in enumerate(status_result.images):
                                image_url = image_data.get('url') or image_data.get('imageUrl')
                                if image_url:
                                    # 使用指定的文件名或默认命名
                                    if output_filename:
                                        filename = output_filename
                                    else:
                                        filename = f"liblib_{result.generate_uuid}_{i+1}.png"
                                    filepath = output_dir / filename
                                    
                                    # 下载并保存图片
                                    import requests
                                    response = requests.get(image_url)
                                    if response.status_code == 200:
                                        with open(filepath, 'wb') as f:
                                            f.write(response.content)
                                        print(f"图片已保存: {filepath}")
                                    else:
                                        print(f"下载图片失败: {image_url}")
                            return True
                        else:
                            print("任务完成但没有图片")
                            return False
                    elif status_result.status.value == 6:  # FAILED
                        print(f"生成失败: {status_result.message}")
                        return False
                    elif status_result.status.value == 7:  # TIMEOUT
                        print("生成超时")
                        return False
                    else:
                        # 仍在处理中
                        print(f"生成中... 进度: {status_result.progress:.1f}%")
                        time.sleep(check_interval)
                        waited_time += check_interval
                        
                except Exception as e:
                    print(f"检查状态时出错: {e}")
                    time.sleep(check_interval)
                    waited_time += check_interval
            
            print("等待超时")
            return False
        else:
            print("提交任务失败")
            return False
            
    except Exception as e:
        print(f"生成图片时出错: {e}")
        return False





def batch_generate_from_json(
    service: LiblibService,
    json_file: Path,
    output_dir: Path,
    use_f1: bool = False,
    max_concurrent: int = 1  # 不使用并发，保持参数兼容性
) -> None:
    """从JSON文件批量生成图片，参考image_generator.py的逻辑"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理新的标准化JSON格式，支持向后兼容
        prompts = []
        if isinstance(data, dict) and 'storyboards' in data:
            # 新的标准化格式
            for item in data['storyboards']:
                if isinstance(item, dict):
                    prompt = item.get('english_prompt', '')
                    if prompt:
                        prompts.append({
                            'prompt': prompt,
                            'original_data': item
                        })
        elif isinstance(data, list):
            # 向后兼容旧格式
            for item in data:
                if isinstance(item, dict):
                    # 优先使用新字段名，然后是旧字段名
                    prompt = item.get('english_prompt', item.get('故事板提示词', item.get('prompt', '')))
                    if prompt:
                        prompts.append({
                            'prompt': prompt,
                            'original_data': item
                        })
                elif isinstance(item, str):
                    prompts.append({'prompt': item, 'original_data': {}})
        elif isinstance(data, dict) and 'prompts' in data:
            prompts = [{'prompt': p, 'original_data': {}} for p in data['prompts']]
        else:
            print("错误: JSON文件格式不正确")
            print("支持的格式:")
            print("1. 新标准化格式: 包含'storyboards'数组，每个元素有'english_prompt'字段")
            print("2. 旧格式: 包含'故事板提示词'字段的对象数组（向后兼容）")
            print("2. 字符串数组")
            print("3. 包含'prompts'字段的对象")
            return
        
        if not prompts:
            print("错误: 未找到有效的提示词")
            return
        
        print(f"开始生成 {len(prompts)} 张图片...")
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        existing_files = set(os.listdir(output_dir)) if output_dir.exists() else set()
        
        success_count = 0
        total_count = len(prompts)
        
        # 顺序生成图片，参考image_generator.py的逻辑，使用tqdm显示进度
        for i, prompt_data in tqdm(enumerate(prompts, 1), total=total_count, desc="正在生成图片"):
            prompt = prompt_data['prompt']
            
            # 跳过空提示词
            if not prompt or not prompt.strip():
                continue
            
            # 输出文件命名，参考image_generator.py: output_{i}.png
            output_file = f'output_{i}.png'
            output_path = output_dir / output_file
            
            # 跳过已存在的文件
            if output_file in existing_files:
                success_count += 1
                continue
            
            # 打印生成信息，参考image_generator.py的格式
            print(f"\n🎨 图片 {i} prompt: {prompt}")
            
            try:
                # 生成图片
                params = prompt_data['original_data'].copy()
                params.pop('故事板提示词', None)  # 移除已使用的字段
                params.pop('prompt', None)  # 移除已使用的字段
                
                if generate_single_image(service, prompt, output_dir, use_f1, output_filename=output_file, **params):
                    success_count += 1
                    print(f"✅ 图片 {i} 生成成功")
                else:
                    print(f"❌ 图片 {i} 生成失败")
            except Exception as e:
                print(f"❌ 图片 {i} 生成出错: {e}")
            
            # 添加短暂延迟，避免API请求过于频繁
            time.sleep(0.5)
        
        print(f"\n🎉 批量生成完成！成功: {success_count}/{total_count}")
        return success_count > 0
        
    except Exception as e:
        print(f"批量生成时出错: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="LiblibAI独立图像生成脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --json-file prompts.json --output-dir ./output
  %(prog)s --prompt "一只可爱的小猫" --output-dir ./output
  %(prog)s --prompt "美丽的风景" --use-f1 --output-dir ./output
  %(prog)s --prompt "改成卡通风格" --input-image ./input.jpg --output-dir ./output
        """
    )
    
    # 输入选项
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--json-file', type=Path, help='包含提示词的JSON文件路径')
    input_group.add_argument('--prompt', type=str, help='单个提示词')
    
    # 输出选项
    parser.add_argument('--output-dir', type=Path, required=True, help='输出目录路径')
    
    # 模型选项
    parser.add_argument('--use-f1', action='store_true', help='使用F.1模型（默认使用传统模型）')
    
    # 图生图选项
    parser.add_argument('--input-image', type=Path, help='输入图片路径（用于图生图）')
    
    # 生成参数
    parser.add_argument('--width', type=int, help='图片宽度')
    parser.add_argument('--height', type=int, help='图片高度')
    parser.add_argument('--steps', type=int, help='采样步数')
    parser.add_argument('--img-count', type=int, help='生成图片数量')
    parser.add_argument('--seed', type=int, help='随机种子')
    parser.add_argument('--restore-faces', action='store_true', help='启用面部修复')
    parser.add_argument('--negative-prompt', type=str, help='负向提示词')
    
    # 高级参数
    parser.add_argument('--cfg-scale', type=float, help='CFG引导强度')
    parser.add_argument('--randn-source', type=int, help='随机数源')
    parser.add_argument('--clip-skip', type=int, help='CLIP跳过层数')
    parser.add_argument('--sampler', type=int, help='采样器类型')
    
    # 高分辨率修复参数
    parser.add_argument('--hires-steps', type=int, help='高分辨率修复步数')
    parser.add_argument('--hires-denoising-strength', type=float, help='高分辨率去噪强度')
    parser.add_argument('--upscaler', type=int, help='放大器类型')
    parser.add_argument('--resized-width', type=int, help='调整后宽度')
    parser.add_argument('--resized-height', type=int, help='调整后高度')
    
    # 并发控制
    parser.add_argument('--max-concurrent', type=int, default=3, help='最大并发数量（默认3）')
    
    args = parser.parse_args()
    
    # 创建LiblibAI服务
    service = create_liblib_service()
    
    # 准备生成参数
    generation_params = {}
    if args.width:
        generation_params['width'] = args.width
    if args.height:
        generation_params['height'] = args.height
    if args.steps:
        generation_params['steps'] = args.steps
    if args.img_count:
        generation_params['img_count'] = args.img_count
    if args.seed:
        generation_params['seed'] = args.seed
    if args.restore_faces:
        generation_params['restore_faces'] = 1  # 转换为数字
    if args.negative_prompt:
        generation_params['negative_prompt'] = args.negative_prompt
    
    # 高级参数
    if args.cfg_scale:
        generation_params['cfg_scale'] = args.cfg_scale
    if args.randn_source is not None:
        generation_params['randn_source'] = args.randn_source
    if args.clip_skip:
        generation_params['clip_skip'] = args.clip_skip
    if args.sampler:
        generation_params['sampler'] = args.sampler
    
    # 高分辨率修复参数
    if args.hires_steps:
        generation_params['hires_steps'] = args.hires_steps
    if args.hires_denoising_strength:
        generation_params['hires_denoising_strength'] = args.hires_denoising_strength
    if args.upscaler:
        generation_params['upscaler'] = args.upscaler
    if args.resized_width:
        generation_params['resized_width'] = args.resized_width
    if args.resized_height:
        generation_params['resized_height'] = args.resized_height
    
    # 执行生成
    if args.json_file:
        if not args.json_file.exists():
            print(f"错误: JSON文件不存在: {args.json_file}")
            sys.exit(1)
        batch_generate_from_json(service, args.json_file, args.output_dir, args.use_f1, args.max_concurrent)
    else:
        success = generate_single_image(
            service, 
            args.prompt, 
            args.output_dir, 
            args.use_f1, 
            args.input_image,
            **generation_params
        )
        if not success:
            sys.exit(1)


if __name__ == '__main__':
    main()