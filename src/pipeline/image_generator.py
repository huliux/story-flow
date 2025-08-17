import os
import sys
import json
import base64
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.config import config

# 发送POST请求
def post(url, data):
    """发送POST请求到Stable Diffusion API"""
    try:
        response = requests.post(
            url, 
            data=json.dumps(data), 
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5分钟超时
        )
        return response
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return None

# 图片保存到文件
def save_img(b64_image, path):
    """将base64图像保存到文件"""
    try:
        with open(path, "wb") as file:
            file.write(base64.b64decode(b64_image))
    except Exception as e:
        print(f"保存图片失败 {path}: {e}")
        raise

def get_prompts(path):
    """从CSV文件读取提示词和LoRA参数"""
    try:
        df = pd.read_csv(path)
        
        # 获取提示词列（假设是第3列，索引为2）
        prompts = df.iloc[:, 2].fillna("").tolist()
        
        # 获取LoRA参数列（假设是第5列，索引为4）
        lora_param_nos = df.iloc[:, 4].fillna(0).tolist()
        
        print(f"读取到 {len(prompts)} 个提示词")
        return prompts, lora_param_nos
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return [], []


# 定义生成参数
def generate_data(prompt):
    """生成Stable Diffusion API请求数据"""
    return config.get_sd_generation_data(prompt)

def main():
    """主函数：执行图像生成"""
    print("Step 2: AI图像生成")
    
    # 验证配置
    errors = config.validate_config()
    if errors:
        print("配置错误:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    # 设置API URL
    api_url = config.sd_api_url
    if not api_url.endswith('/'):
        api_url += '/'
    url = api_url + "sdapi/v1/txt2img"
    
    print(f"Stable Diffusion API: {url}")
    
    # 读取提示词
    csv_file = config.output_csv_file
    if not csv_file.exists():
        print(f"错误: CSV文件不存在 - {csv_file}")
        return False
    
    prompts, lora_param_nos = get_prompts(csv_file)
    if not prompts:
        print("错误: 未读取到任何提示词")
        return False
    
    # 确保输出目录存在
    output_dir = config.output_dir_image
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_files = set(os.listdir(output_dir))

    # 获取LoRA模型配置
    lora_param_dict = config.lora_models

    print(f"开始生成 {len(prompts)} 张图片...")
    
    # 确保临时目录存在
    config.output_dir_temp.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    total_count = len(prompts)
    
    for i, (prompt_b, lora_param_no) in tqdm(enumerate(zip(prompts, lora_param_nos)), total=total_count, desc="正在生成图片"):
        # 跳过空提示词
        if not prompt_b or not prompt_b.strip():
            continue
            
        # 获取LoRA参数
        lora_param_no = int(lora_param_no) if lora_param_no else 0
        lora_param = lora_param_dict.get(lora_param_no, "")
        
        # 构建完整提示词
        if lora_param:
            prompt = f"masterpiece,(best quality),{prompt_b},{lora_param}"
        else:
            prompt = f"masterpiece,(best quality),{prompt_b}"
            
        output_file = f'output_{i+1}.png'
        output_path = output_dir / output_file

        # 跳过已存在的文件
        if output_file in existing_files:
            success_count += 1
            continue
            
        # 生成图片
        data = generate_data(prompt)
        response = post(url, data)
        
        if response and response.status_code == 200:
            try:
                response_data = response.json()
                if 'images' in response_data and response_data['images']:
                    save_img(response_data['images'][0], output_path)
                    existing_files.add(output_file)
                    success_count += 1
                    
                    # 保存生成参数
                    params_file = config.params_json_file
                    with open(params_file, 'a', encoding='utf-8') as f:
                        json.dump({output_file: data}, f, ensure_ascii=False)
                        f.write('\n')
                else:
                    print(f'API响应格式错误: 图片 {i+1}')
            except Exception as e:
                print(f'处理响应时出错: 图片 {i+1}, 错误: {e}')
        else:
            error_code = response.status_code if response else "连接失败"
            print(f'生成失败: 图片 {i+1}, 错误码: {error_code}')

    print(f"图片生成完成！成功: {success_count}/{total_count}")
    return success_count > 0

def interactive_regenerate(url, prompts, lora_param_nos, lora_param_dict, existing_files, output_dir):
    """交互式重新生成指定图片"""
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
                            tqdm.write(f"图片编号 {redo_img_no} 超出范围")
                            continue
                            
                        output_file = f'output_{redo_img_no}.png'
                        output_path = output_dir / output_file
                        
                        if output_file not in existing_files:
                            tqdm.write(f"图片 {output_file} 不存在")
                            continue
                            
                        # 删除旧文件
                        output_path.unlink()
                        tqdm.write(f"图片 {output_file} 已删除，开始重绘...")
                        
                        prompt_b = prompts[img_index]
                        redo_lora_param_no = lora_param_nos[img_index]

                        # 用户可选择修改LoRA参数
                        lora_param_change = input("修改LoRA（删除输入'noLora'，直接回车保持默认）：")
                        if lora_param_change.lower() == 'nolora':
                            lora_param = ""
                        elif lora_param_change.strip():
                            lora_param = lora_param_change
                        else:
                            lora_param = lora_param_dict.get(int(redo_lora_param_no), "")
                        
                        # 构建提示词
                        if lora_param:
                            prompt = f"masterpiece,(best quality),{prompt_b},{lora_param}"
                        else:
                            prompt = f"masterpiece,(best quality),{prompt_b}"
                            
                        # 生成图片
                        data = generate_data(prompt)
                        response = post(url, data)
                        
                        if response and response.status_code == 200:
                            save_img(response.json()['images'][0], output_path)
                            
                            # 保存参数
                            params_file = config.params_json_file
                            with open(params_file, 'a', encoding='utf-8') as f:
                                json.dump({output_file: data}, f, ensure_ascii=False)
                                f.write('\n')
                                
                            redo_count += 1
                            pbar.set_description(f"已重绘 {redo_count}/{len(redo_img_nos)} 张")
                        else:
                            error_code = response.status_code if response else "连接失败"
                            tqdm.write(f'重绘失败: {output_file}, 错误: {error_code}')
                            
                        pbar.update(1)
                        
                    except ValueError:
                        tqdm.write(f"无效的图片编号: {redo_img_no}")
                    except Exception as e:
                        tqdm.write(f"处理图片 {redo_img_no} 时出错: {e}")
        except KeyboardInterrupt:
            print("\n用户中断操作")
            break
        except Exception as e:
            print(f"重绘过程出错: {e}")
    
    print(f"重绘完成！共重绘了 {redo_count} 张图片。")
    return redo_count

if __name__ == '__main__':
    try:
        # 检查是否为自动化模式（通过环境变量或命令行参数）
        auto_mode = os.getenv('AUTO_MODE', 'false').lower() == 'true' or '--auto' in sys.argv
        
        success = main()

        if success and not auto_mode:
            print("\n是否需要重绘指定图片？")
            
            csv_file = config.output_csv_file
            prompts, lora_param_nos = get_prompts(csv_file)
            lora_param_dict = config.lora_models
            output_dir = config.output_dir_image
            existing_files = set(os.listdir(output_dir))

            api_url = config.sd_api_url
            if not api_url.endswith('/'):
                api_url += '/'
            url = api_url + "sdapi/v1/txt2img"

            interactive_regenerate(url, prompts, lora_param_nos, lora_param_dict, existing_files, output_dir)
        elif success and auto_mode:
            print("\n✅ 图像生成完成（自动化模式，跳过交互式重绘）")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)



