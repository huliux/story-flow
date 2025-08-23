import os
import sys
import json
import base64
import requests
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional, Union
import logging

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 发送POST请求
def post(url: str, data: Dict) -> Optional[requests.Response]:
    """发送POST请求到Stable Diffusion API
    
    Args:
        url: API端点URL
        data: 请求数据
        
    Returns:
        响应对象或None（如果请求失败）
    """
    try:
        response = requests.post(
            url, 
            data=json.dumps(data), 
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5分钟超时
        )
        response.raise_for_status()  # 抛出HTTP错误
        return response
    except requests.exceptions.Timeout:
        logging.error("请求超时，请检查网络连接或增加超时时间")
        return None
    except requests.exceptions.ConnectionError:
        logging.error("连接错误，请检查API服务是否正常运行")
        return None
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP错误: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API请求失败: {e}")
        return None

# 图片保存到文件
def save_img(b64_image: str, path: Union[str, Path]) -> bool:
    """将base64图像保存到文件
    
    Args:
        b64_image: base64编码的图像数据
        path: 保存路径
        
    Returns:
        保存是否成功
    """
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        
        with open(path, "wb") as file:
            file.write(base64.b64decode(b64_image))
        return True
    except Exception as e:
        logging.error(f"保存图片失败 {path}: {e}")
        return False

def get_prompts(path: Union[str, Path]) -> Tuple[List[str], List[Optional[str]]]:
    """从JSON文件读取提示词和LoRA参数
    
    Args:
        path: JSON文件路径
        
    Returns:
        (提示词列表, LoRA参数编号列表)
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 处理新的标准化格式
        if isinstance(data, dict) and 'storyboards' in data:
            data_list = data['storyboards']
            logging.info(f"检测到标准化格式，包含 {len(data_list)} 个故事板")
        elif isinstance(data, list):
            # 兼容旧格式
            data_list = data
            logging.info(f"检测到旧格式，包含 {len(data_list)} 个条目")
        else:
            logging.error("不支持的JSON格式")
            return [], []
        
        # 获取提示词列表 - 支持多种字段名
        prompts = []
        lora_param_nos = []
        
        for item in data_list:
            if not isinstance(item, dict):
                logging.warning(f"跳过非字典项: {item}")
                continue
                
            # 尝试多种提示词字段名
            prompt = (
                item.get("english_prompt", "") or 
                item.get("故事板提示词", "") or 
                item.get("processed_chinese", "") or 
                item.get("prompt", "") or 
                ""
            )
            prompts.append(prompt)
            
            # 尝试多种LoRA字段名
            lora_param = (
                item.get("lora_id", "") or 
                item.get("LoRA编号", "") or 
                ""
            )
            lora_param_nos.append(lora_param)
        
        logging.info(f"读取到 {len(prompts)} 个提示词")
        return prompts, lora_param_nos
    except FileNotFoundError:
        logging.error(f"文件未找到: {path}")
        return [], []
    except json.JSONDecodeError as e:
        logging.error(f"JSON解析错误: {e}")
        return [], []
    except Exception as e:
        logging.error(f"读取JSON文件失败: {e}")
        return [], []


# 定义生成参数
def generate_data(prompt: str) -> Dict:
    """生成Stable Diffusion API请求数据
    
    Args:
        prompt: 图像生成提示词
        
    Returns:
        API请求数据字典
    """
    return config.get_sd_generation_data(prompt)

def build_prompt(base_prompt: str, lora_param: str = "", style_param: str = "") -> str:
    """构建完整的提示词
    
    Args:
        base_prompt: 基础提示词
        lora_param: LoRA参数
        style_param: 风格参数
        
    Returns:
        完整的提示词
    """
    prompt_parts = ["masterpiece,(best quality)", base_prompt]
    
    if lora_param:
        prompt_parts.append(lora_param)
    
    if style_param:
        prompt_parts.append(style_param)
    
    return ",".join(prompt_parts)

def save_generation_params(params_file: Union[str, Path], output_file: str, data: Dict) -> bool:
    """保存生成参数到文件
    
    Args:
        params_file: 参数文件路径
        output_file: 输出文件名
        data: 生成参数数据
        
    Returns:
        保存是否成功
    """
    try:
        with open(params_file, 'a', encoding='utf-8') as f:
            json.dump({output_file: data}, f, ensure_ascii=False)
            f.write('\n')
        return True
    except Exception as e:
        logging.error(f"保存参数失败: {e}")
        return False

def main(json_file_path: Optional[str] = None) -> bool:
    """主函数：执行图像生成
    
    Args:
        json_file_path: 可选的JSON文件路径
        
    Returns:
        生成是否成功
    """
    logging.info("Step 2: AI图像生成")
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        logging.error("配置错误:")
        for error in errors:
            logging.error(f"  - {error}")
        return False
    
    # 设置API URL
    api_url = config.sd_api_url
    if not api_url.endswith('/'):
        api_url += '/'
    url = api_url + "sdapi/v1/txt2img"
    
    logging.info(f"Stable Diffusion API: {url}")
    
    # 读取提示词
    if json_file_path:
        json_file = Path(json_file_path)
        if not json_file.exists():
            logging.error(f"指定的JSON文件不存在 - {json_file}")
            return False
    else:
        json_file = config.output_json_file
    if not json_file.exists():
        logging.error(f"JSON文件不存在 - {json_file}")
        return False
    
    prompts, lora_param_nos = get_prompts(json_file)
    if not prompts:
        logging.error("未读取到任何提示词")
        return False
    
    # 确保输出目录存在
    output_dir = config.output_dir_image
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_files = set(os.listdir(output_dir))

    # 获取LoRA模型配置
    lora_param_dict = config.lora_models

    logging.info(f"开始生成 {len(prompts)} 张图片...")
    
    # 确保临时目录存在
    config.output_dir_temp.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = len(prompts)
    
    for i, (prompt_b, lora_param_no) in tqdm(enumerate(zip(prompts, lora_param_nos)), total=total_count, desc="正在生成图片"):
        # 跳过空提示词
        if not prompt_b or not prompt_b.strip():
            logging.warning(f"跳过空提示词: 图片 {i+1}")
            continue
            
        # 获取LoRA参数
        try:
            # 当CSV中没有LoRA编号或为空时，默认使用0（LORA_MODEL_0）
            lora_param_no = int(lora_param_no) if lora_param_no else 0
            lora_param = lora_param_dict.get(lora_param_no, "")
        except (ValueError, TypeError) as e:
            logging.warning(f"无效的LoRA参数编号: {lora_param_no}, 错误: {e}")
            lora_param = ""
        
        # 获取用户自定义风格参数
        style_param = config.sd_style.strip() if config.sd_style else ""
        
        # 构建完整提示词
        prompt = build_prompt(prompt_b, lora_param, style_param)
        
        # 打印最终提示词
        logging.info(f"🎨 图片 {i+1} prompt: {prompt}")
            
        output_file = f'output_{i+1}.png'
        output_path = output_dir / output_file

        # 跳过已存在的文件
        if output_file in existing_files:
            success_count += 1
            logging.info(f"跳过已存在的文件: {output_file}")
            continue
            
        # 生成图片
        data = generate_data(prompt)
        response = post(url, data)
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                if 'images' in response_data and response_data['images']:
                    if save_img(response_data['images'][0], output_path):
                        existing_files.add(output_file)
                        success_count += 1
                        logging.info(f"✅ 图片 {i+1} 生成成功: {output_file}")
                        
                        # 保存生成参数
                        save_generation_params(config.params_json_file, output_file, data)
                    else:
                        logging.error(f"图片 {i+1} 保存失败")
                else:
                    logging.error(f'API响应格式错误: 图片 {i+1}')
            except Exception as e:
                logging.error(f'处理响应时出错: 图片 {i+1}, 错误: {e}')
        else:
            error_code = response.status_code if response else "连接失败"
            logging.error(f'生成失败: 图片 {i+1}, 错误码: {error_code}')

    logging.info(f"图片生成完成！成功: {success_count}/{total_count}")
    return success_count > 0

def interactive_regenerate(url: str, prompts: List[str], lora_param_nos: List[Optional[str]], 
                          lora_param_dict: Dict, existing_files: set, output_dir: Path) -> int:
    """交互式重新生成指定图片
    
    Args:
        url: API端点URL
        prompts: 提示词列表
        lora_param_nos: LoRA参数编号列表
        lora_param_dict: LoRA参数字典
        existing_files: 已存在文件集合
        output_dir: 输出目录
        
    Returns:
        重绘成功的图片数量
    """
    redo_count = 0
    
    while True:
        try:
            redo_img_nos = input("输入要重绘的图片编号，多图用空格分隔。输入n或N结束：")
            if redo_img_nos.lower() == 'n':
                break

            redo_img_nos = redo_img_nos.split()
            if not redo_img_nos:
                continue

            with tqdm(total=len(redo_img_nos), desc="重绘进度") as pbar:
                for redo_img_no in redo_img_nos:
                    try:
                        img_index = int(redo_img_no) - 1
                        if img_index < 0 or img_index >= len(prompts):
                            tqdm.write(f"图片编号 {redo_img_no} 超出范围 (1-{len(prompts)})")
                            continue
                            
                        output_file = f'output_{redo_img_no}.png'
                        output_path = output_dir / output_file
                        
                        if output_file not in existing_files:
                            tqdm.write(f"图片 {output_file} 不存在")
                            continue
                            
                        # 删除旧文件
                        try:
                            output_path.unlink()
                            tqdm.write(f"图片 {output_file} 已删除，开始重绘...")
                        except OSError as e:
                            tqdm.write(f"删除文件失败: {e}")
                            continue
                        
                        prompt_b = prompts[img_index]
                        redo_lora_param_no = lora_param_nos[img_index]

                        # 用户可选择修改LoRA参数
                        lora_param_change = input("修改LoRA（删除输入'n'，数字加载对应配置，直接回车保持默认）：")
                        if lora_param_change.lower() == 'n':
                            lora_param = ""
                        elif lora_param_change.strip():
                            # 检查输入是否为数字，如果是则从配置中加载对应的LoRA
                            if lora_param_change.strip().isdigit():
                                lora_model_no = int(lora_param_change.strip())
                                lora_param = lora_param_dict.get(lora_model_no, "")
                                if lora_param:
                                    tqdm.write(f"已加载LoRA模型 {lora_model_no}: {lora_param}")
                                else:
                                    tqdm.write(f"警告: LoRA模型 {lora_model_no} 未配置")
                            else:
                                # 直接使用用户输入的字符串作为LoRA参数
                                lora_param = lora_param_change
                        else:
                            # 当CSV中没有LoRA编号或为空时，默认使用0（LORA_MODEL_0）
                            try:
                                lora_param_no = int(redo_lora_param_no) if redo_lora_param_no else 0
                                lora_param = lora_param_dict.get(lora_param_no, "")
                            except (ValueError, TypeError):
                                lora_param = ""
                        
                        # 获取用户自定义风格参数
                        style_param = config.sd_style.strip() if config.sd_style else ""
                        
                        # 构建提示词
                        prompt = build_prompt(prompt_b, lora_param, style_param)
                        
                        # 打印最终提示词
                        tqdm.write(f"🎨 重绘图片 {redo_img_no} 最终提示词: {prompt}")
                            
                        # 生成图片
                        data = generate_data(prompt)
                        response = post(url, data)
                        
                        if response and response.status_code == 200:
                            try:
                                response_json = response.json()
                                if 'images' in response_json and response_json['images']:
                                    if save_img(response_json['images'][0], output_path):
                                        # 保存参数
                                        save_generation_params(config.params_json_file, output_file, data)
                                        redo_count += 1
                                        pbar.set_description(f"已重绘 {redo_count}/{len(redo_img_nos)} 张")
                                        tqdm.write(f"✅ 重绘成功: {output_file}")
                                    else:
                                        tqdm.write(f"❌ 重绘保存失败: {output_file}")
                                else:
                                    tqdm.write(f"❌ API响应格式错误: {output_file}")
                            except (KeyError, IndexError, json.JSONDecodeError) as e:
                                tqdm.write(f"❌ 处理响应失败: {output_file}, 错误: {e}")
                        else:
                            error_code = response.status_code if response else "连接失败"
                            tqdm.write(f'❌ 重绘失败: {output_file}, 错误: {error_code}')
                            
                        pbar.update(1)
                        
                    except ValueError:
                        tqdm.write(f"无效的图片编号: {redo_img_no}")
                    except Exception as e:
                        tqdm.write(f"处理图片 {redo_img_no} 时出错: {e}")
                        logging.error(f"重绘图片 {redo_img_no} 异常: {e}")
        except KeyboardInterrupt:
            print("\n用户中断操作")
            break
        except Exception as e:
            print(f"重绘过程出错: {e}")
            logging.error(f"重绘过程异常: {e}")
    
    print(f"重绘完成！共重绘了 {redo_count} 张图片。")
    return redo_count

if __name__ == '__main__':
    try:
        import argparse
        
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='Stable Diffusion图像生成器')
        parser.add_argument('--json-file', type=str, help='指定JSON文件路径')
        parser.add_argument('--auto', action='store_true', help='自动化模式，不进入交互式重绘')
        args = parser.parse_args()
        
        auto_mode: bool = os.getenv('AUTO_MODE', 'false').lower() == 'true' or args.auto
        json_file: Optional[str] = args.json_file
        
        logging.info(f"启动图像生成器 - 自动模式: {auto_mode}, JSON文件: {json_file or '默认'}")
        
        # 调用主函数
        success: bool = main(json_file)

        if success and not auto_mode:
            try:
                print("\n是否需要重绘指定图片？")
                
                # 在交互式重绘中，如果没有指定文件，使用配置中的文件
                target_json_file: Path = Path(json_file) if json_file else config.output_json_file
                prompts, lora_param_nos = get_prompts(target_json_file)
                lora_param_dict: Dict = config.lora_models
                output_dir: Path = config.output_dir_image
                existing_files: set = set(os.listdir(output_dir))

                if existing_files:
                    logging.info(f"发现 {len(existing_files)} 个已生成的图片文件")
                    api_url: str = config.sd_api_url
                    if not api_url.endswith('/'):
                        api_url += '/'
                    url: str = api_url + "sdapi/v1/txt2img"

                    redo_count: int = interactive_regenerate(url, prompts, lora_param_nos, lora_param_dict, existing_files, output_dir)
                    logging.info(f"交互式重绘完成，共重绘 {redo_count} 张图片")
                else:
                    logging.info("未发现已生成的图片文件，跳过交互式重绘")
                    
            except Exception as e:
                logging.error(f"交互式重绘初始化失败: {e}")
                print(f"交互式重绘初始化失败: {e}")
        elif success and auto_mode:
            print("\n✅ 图像生成完成（自动化模式，跳过交互式重绘）")

        exit_code: int = 0 if success else 1
        logging.info(f"程序结束，退出码: {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logging.info("用户中断程序")
        print("\n程序被用户中断")
        sys.exit(130)  # 标准的键盘中断退出码
    except Exception as e:
        logging.error(f"程序异常退出: {e}")
        print(f"程序异常退出: {e}")
        sys.exit(1)



