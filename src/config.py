"""
统一配置管理模块
加载环境变量和配置文件，提供类型安全的配置访问
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Please install it using: pip install python-dotenv")
    print("Falling back to environment variables only.")


class Config:
    """配置管理类，提供类型安全的配置访问"""
    
    def __init__(self):
        # 获取项目根目录
        self.project_root = self._get_project_root()
        
        # 确保所有必需的目录存在
        self._ensure_directories()
    
    def _get_project_root(self) -> Path:
        """获取项目根目录"""
        env_root = os.getenv('PROJECT_ROOT', '').strip()
        if env_root:
            return Path(env_root)
        
        # 默认使用脚本所在目录
        if hasattr(sys, '_getframe'):
            # 获取调用此模块的脚本所在目录
            caller_frame = sys._getframe(1)
            caller_file = caller_frame.f_globals.get('__file__')
            if caller_file:
                return Path(caller_file).parent.absolute()
        
        # 回退到当前工作目录
        return Path.cwd()
    
    def _ensure_directories(self):
        """确保所有必需的目录存在"""
        directories = [
            self.input_dir,
            self.output_dir_txt,
            self.output_dir_image,
            self.output_dir_voice,
            self.output_dir_video,
            self.output_dir_temp,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔值配置"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def _get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def _get_bool_as_int(self, key: str, default: int = 0) -> int:
        """获取布尔值配置并转换为整数（0或1）"""
        value = os.getenv(key, str(default)).lower()
        if value in ('true', '1', 'yes', 'on'):
            return 1
        elif value in ('false', '0', 'no', 'off'):
            return 0
        else:
            # 如果是数字字符串，尝试直接转换
            try:
                return int(value)
            except ValueError:
                return default
    
    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        """获取列表配置（逗号分隔）"""
        if default is None:
            default = []
        value = os.getenv(key, '')
        if not value:
            return default
        return [item.strip() for item in value.split(',') if item.strip()]
    
    # ================================
    # AI服务配置
    # ================================
    
    @property
    def llm_provider(self) -> str:
        """LLM服务提供商: openai, deepseek"""
        return os.getenv('LLM_PROVIDER', 'openai').lower()
    
    # OpenAI配置
    @property
    def openai_api_key(self) -> str:
        return os.getenv('OPENAI_API_KEY', '')
    
    @property
    def openai_base_url(self) -> str:
        return os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    @property
    def openai_model(self) -> str:
        return os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo-16k')
    
    # DeepSeek配置
    @property
    def deepseek_api_key(self) -> str:
        return os.getenv('DEEPSEEK_API_KEY', '')
    
    @property
    def deepseek_base_url(self) -> str:
        return os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    @property
    def deepseek_model(self) -> str:
        return os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    
    @property
    def deepseek_story_model(self) -> str:
        """故事生成专用的DeepSeek模型"""
        return os.getenv('DEEPSEEK_STORY_MODEL', 'deepseek-reasoner')
    
    # 通用LLM配置
    @property
    def llm_max_tokens(self) -> int:
        return self._get_int('LLM_MAX_TOKENS', 500)
    
    @property
    def llm_cooldown_seconds(self) -> int:
        return self._get_int('LLM_COOLDOWN_SECONDS', 60)
    
    @property
    def llm_max_requests(self) -> int:
        return self._get_int('LLM_MAX_REQUESTS', 90)
    
    @property
    def llm_temperature(self) -> float:
        return self._get_float('LLM_TEMPERATURE', 0.7)
    
    # 兼容性属性（向后兼容）
    @property
    def openai_max_tokens(self) -> int:
        return self.llm_max_tokens
    
    @property
    def openai_cooldown_seconds(self) -> int:
        return self.llm_cooldown_seconds
    
    @property
    def openai_max_requests(self) -> int:
        return self.llm_max_requests
    
    # LiblibAI配置
    @property
    def liblib_access_key(self) -> str:
        """LiblibAI访问密钥"""
        return os.getenv('LIBLIB_ACCESS_KEY', '')
    
    @property
    def liblib_secret_key(self) -> str:
        """LiblibAI密钥"""
        return os.getenv('LIBLIB_SECRET_KEY', '')
    
    @property
    def liblib_base_url(self) -> str:
        """LiblibAI API基础URL"""
        return os.getenv('LIBLIB_BASE_URL', 'https://openapi.liblibai.cloud')
    
    @property
    def liblib_enabled(self) -> bool:
        """是否启用LiblibAI服务"""
        return self._get_bool('LIBLIB_ENABLED', False)
    
    @property
    def liblib_priority(self) -> bool:
        """是否优先使用LiblibAI服务"""
        return self._get_bool('LIBLIB_PRIORITY', False)
    
    @property
    def liblib_timeout(self) -> int:
        """LiblibAI请求超时时间(秒)"""
        return self._get_int('LIBLIB_TIMEOUT', 30)
    
    @property
    def liblib_max_retries(self) -> int:
        """LiblibAI最大重试次数"""
        return self._get_int('LIBLIB_MAX_RETRIES', 3)
    
    @property
    def liblib_retry_delay(self) -> float:
        """LiblibAI重试延迟(秒)"""
        return self._get_float('LIBLIB_RETRY_DELAY', 1.0)
    
    @property
    def liblib_max_wait_time(self) -> int:
        """LiblibAI生图最大等待时间(秒)"""
        return self._get_int('LIBLIB_MAX_WAIT_TIME', 300)
    
    @property
    def liblib_check_interval(self) -> int:
        """LiblibAI状态检查间隔(秒)"""
        return self._get_int('LIBLIB_CHECK_INTERVAL', 5)
    
    @property
    def liblib_trigger_words(self) -> str:
        """LiblibAI触发词，会自动添加到提示词前面"""
        return os.getenv('LIBLIB_TRIGGER_WORDS', '')
    
    @property
    def liblib_negative_prompt(self) -> str:
        """LiblibAI负向提示词，用于排除不想要的内容"""
        return os.getenv('LIBLIB_NEGATIVE_PROMPT', '')
    
    @property
    def liblib_default_steps(self) -> int:
        """LiblibAI默认采样步数"""
        return self._get_int('LIBLIB_DEFAULT_STEPS', 30)
    
    @property
    def liblib_default_aspect_ratio(self) -> str:
        """LiblibAI默认宽高比"""
        return os.getenv('LIBLIB_DEFAULT_ASPECT_RATIO', 'square')
    
    # F.1文生图默认配置（仅保留F.1 API支持的参数）
    @property
    def f1_default_width(self) -> int:
        """F.1默认图片宽度"""
        return self._get_int('F1_DEFAULT_WIDTH', 768)
    
    @property
    def f1_default_height(self) -> int:
        """F.1默认图片高度"""
        return self._get_int('F1_DEFAULT_HEIGHT', 1024)
    
    @property
    def f1_default_steps(self) -> int:
        """F.1默认采样步数"""
        return self._get_int('F1_DEFAULT_STEPS', 20)
    
    @property
    def f1_default_img_count(self) -> int:
        """F.1默认生成图片数量"""
        return self._get_int('F1_DEFAULT_IMG_COUNT', 1)
    
    @property
    def f1_default_restore_faces(self) -> int:
        """F.1默认面部修复设置"""
        return self._get_bool_as_int('F1_DEFAULT_RESTORE_FACES', 0)
    
    @property
    def f1_default_seed(self) -> int:
        """F.1默认随机种子（-1表示随机）"""
        return self._get_int('F1_DEFAULT_SEED', -1)
    
    @property
    def f1_default_template_uuid(self) -> str:
        """F.1默认参数模板ID"""
        return os.getenv('F1_DEFAULT_TEMPLATE_UUID', '6f7c4652458d4802969f8d089cf5b91f')
    
    @property
    def f1_default_checkpoint_id(self) -> Optional[str]:
        """F.1默认底模ID"""
        value = os.getenv('F1_DEFAULT_CHECKPOINT_ID', '').strip()
        return value if value else None
    
    @property
    def f1_default_vae_id(self) -> Optional[str]:
        """F.1默认VAE模型ID"""
        value = os.getenv('F1_DEFAULT_VAE_ID', '').strip()
        return value if value else None
    
    # F.1高级参数配置
    @property
    def f1_default_cfg_scale(self) -> float:
        """F.1默认CFG Scale"""
        return self._get_float('F1_DEFAULT_CFG_SCALE', 3.5)
    
    @property
    def f1_default_clip_skip(self) -> int:
        """F.1默认CLIP Skip"""
        return self._get_int('F1_DEFAULT_CLIP_SKIP', 2)
    
    @property
    def f1_default_sampler(self) -> int:
        """F.1默认采样器"""
        return self._get_int('F1_DEFAULT_SAMPLER', 1)
    
    @property
    def f1_default_randn_source(self) -> int:
        """F.1默认随机种子来源"""
        return self._get_int('F1_DEFAULT_RANDN_SOURCE', 0)
    
    # F.1图生图特有参数
    @property
    def f1_default_resize_mode(self) -> int:
        """F.1默认缩放模式"""
        return self._get_int('F1_DEFAULT_RESIZE_MODE', 0)
    
    @property
    def f1_default_resized_width(self) -> int:
        """F.1默认缩放后宽度"""
        return self._get_int('F1_DEFAULT_RESIZED_WIDTH', 1024)
    
    @property
    def f1_default_resized_height(self) -> int:
        """F.1默认缩放后高度"""
        return self._get_int('F1_DEFAULT_RESIZED_HEIGHT', 1024)
    
    @property
    def f1_default_mode(self) -> int:
        """F.1默认模式（0图生图，4蒙版重绘）"""
        return self._get_int('F1_DEFAULT_MODE', 0)
    
    @property
    def f1_default_denoising_strength(self) -> float:
        """F.1默认重绘幅度"""
        return self._get_float('F1_DEFAULT_DENOISING_STRENGTH', 0.75)
    
    # F.1高分辨率修复配置
    @property
    def f1_default_hires_enabled(self) -> bool:
        """F.1默认是否启用高分辨率修复"""
        return self._get_bool('F1_DEFAULT_HIRES_ENABLED', False)
    
    @property
    def f1_default_hires_steps(self) -> int:
        """F.1默认高分辨率修复步数"""
        return self._get_int('F1_DEFAULT_HIRES_STEPS', 20)
    
    @property
    def f1_default_hires_denoising_strength(self) -> float:
        """F.1默认高分辨率修复重绘幅度"""
        return self._get_float('F1_DEFAULT_HIRES_DENOISING_STRENGTH', 0.75)
    
    @property
    def f1_default_upscaler(self) -> int:
        """F.1默认放大算法"""
        return self._get_int('F1_DEFAULT_UPSCALER', 10)
    
    @property
    def f1_default_hires_resized_width(self) -> int:
        """F.1默认高分辨率修复宽度"""
        return self._get_int('F1_DEFAULT_HIRES_RESIZED_WIDTH', 1024)
    
    @property
    def f1_default_hires_resized_height(self) -> int:
        """F.1默认高分辨率修复高度"""
        return self._get_int('F1_DEFAULT_HIRES_RESIZED_HEIGHT', 1536)
    
    # F.1局部重绘配置
    @property
    def f1_default_mask_blur(self) -> int:
        """F.1默认蒙版模糊度"""
        return self._get_int('F1_DEFAULT_MASK_BLUR', 4)
    
    @property
    def f1_default_mask_padding(self) -> int:
        """F.1默认蒙版边缘预留像素"""
        return self._get_int('F1_DEFAULT_MASK_PADDING', 32)
    
    @property
    def f1_default_mask_mode(self) -> int:
        """F.1默认蒙版模式"""
        return self._get_int('F1_DEFAULT_MASK_MODE', 0)
    
    @property
    def f1_default_inpaint_area(self) -> int:
        """F.1默认重绘区域"""
        return self._get_int('F1_DEFAULT_INPAINT_AREA', 0)
    
    @property
    def f1_default_inpainting_fill(self) -> int:
        """F.1默认蒙版内容填充模式"""
        return self._get_int('F1_DEFAULT_INPAINTING_FILL', 1)
    
    # F.1 AdditionalNetwork (LoRA) 配置
    @property
    def f1_default_additional_network_model_id(self) -> str:
        """F.1默认LoRA模型ID"""
        return os.getenv('F1_DEFAULT_ADDITIONAL_NETWORK_MODEL_ID', '')
    
    @property
    def f1_default_additional_network_weight(self) -> float:
        """F.1默认LoRA权重"""
        return self._get_float('F1_DEFAULT_ADDITIONAL_NETWORK_WEIGHT', 1.0)
    
    @property
    def f1_default_additional_network_enabled(self) -> bool:
        """F.1默认是否启用LoRA网络"""
        return self._get_bool('F1_DEFAULT_ADDITIONAL_NETWORK_ENABLED', False)

    # 图像生成服务选择配置
    @property
    def image_generation_service(self) -> str:
        """图像生成服务选择：'stable_diffusion' 或 'liblib'"""
        return os.getenv('IMAGE_GENERATION_SERVICE', 'stable_diffusion')
    
    @property
    def image_service_priority(self) -> str:
        """图像服务优先级：'stable_diffusion_first' 或 'liblib_first'"""
        return os.getenv('IMAGE_SERVICE_PRIORITY', 'stable_diffusion_first')
    
    @property
    def image_service_fallback_enabled(self) -> bool:
        """是否启用图像服务回退机制"""
        return self._get_bool('IMAGE_SERVICE_FALLBACK_ENABLED', True)

    # Azure语音服务配置
    @property
    def azure_speech_key(self) -> str:
        return os.getenv('AZURE_SPEECH_KEY', '')
    
    @property
    def azure_speech_region(self) -> str:
        return os.getenv('AZURE_SPEECH_REGION', 'eastasia')
    
    @property
    def azure_voice_name(self) -> str:
        return os.getenv('AZURE_VOICE_NAME', 'zh-CN-YunxiNeural')
    
    @property
    def azure_voice_style(self) -> str:
        return os.getenv('AZURE_VOICE_STYLE', 'calm')
    
    @property
    def azure_voice_role(self) -> str:
        return os.getenv('AZURE_VOICE_ROLE', 'OlderAdultMale')
    
    @property
    def azure_voice_rate(self) -> str:
        return os.getenv('AZURE_VOICE_RATE', '+40%')
    
    @property
    def azure_voice_pitch(self) -> str:
        return os.getenv('AZURE_VOICE_PITCH', '+0st')
    
    @property
    def azure_voice_volume(self) -> str:
        return os.getenv('AZURE_VOICE_VOLUME', '+30%')
    
    @property
    def azure_voice_emphasis(self) -> str:
        return os.getenv('AZURE_VOICE_EMPHASIS', 'none')
    
    @property
    def azure_voice_style_degree(self) -> str:
        return os.getenv('AZURE_VOICE_STYLE_DEGREE', '1')
    
    # ================================
    # Stable Diffusion配置
    # ================================
    
    @property
    def sd_api_url(self) -> str:
        return os.getenv('SD_API_URL', 'http://127.0.0.1:7860')
    
    @property
    def sd_enable_hr(self) -> bool:
        return self._get_bool('SD_ENABLE_HR', True)
    
    @property
    def sd_denoising_strength(self) -> float:
        return self._get_float('SD_DENOISING_STRENGTH', 0.5)
    
    @property
    def sd_firstphase_width(self) -> int:
        return self._get_int('SD_FIRSTPHASE_WIDTH', 960)
    
    @property
    def sd_firstphase_height(self) -> int:
        return self._get_int('SD_FIRSTPHASE_HEIGHT', 540)
    
    @property
    def sd_hr_scale(self) -> int:
        return self._get_int('SD_HR_SCALE', 2)
    
    @property
    def sd_hr_upscaler(self) -> str:
        return os.getenv('SD_HR_UPSCALER', '4x-UltraSharp')
    
    @property
    def sd_hr_second_pass_steps(self) -> int:
        return self._get_int('SD_HR_SECOND_PASS_STEPS', 10)
    
    @property
    def sd_hr_resize_x(self) -> int:
        return self._get_int('SD_HR_RESIZE_X', 1920)
    
    @property
    def sd_hr_resize_y(self) -> int:
        return self._get_int('SD_HR_RESIZE_Y', 1080)
    
    @property
    def sd_seed(self) -> int:
        return self._get_int('SD_SEED', 333)
    
    @property
    def sd_sampler_name(self) -> str:
        return os.getenv('SD_SAMPLER_NAME', 'DPM++ 2M Karras')
    
    @property
    def sd_batch_size(self) -> int:
        return self._get_int('SD_BATCH_SIZE', 1)
    
    @property
    def sd_steps(self) -> int:
        return self._get_int('SD_STEPS', 20)
    
    @property
    def sd_cfg_scale(self) -> float:
        return self._get_float('SD_CFG_SCALE', 7.5)
    
    @property
    def sd_restore_faces(self) -> bool:
        return self._get_bool('SD_RESTORE_FACES', False)
    
    @property
    def sd_tiling(self) -> bool:
        return self._get_bool('SD_TILING', False)
    
    @property
    def sd_negative_prompt(self) -> str:
        """固定的负面提示词"""
        return os.getenv('SD_NEGATIVE_PROMPT', 
                        "NSFW,extra fingers, ugly, photorealistic, 3d, monochrome, distorted face, bad anatomy, writing, words, blurry, haze, unfocused, cropped, extra limbs, unfinished, jpg artifacts,lowres, bad anatomy, bad hands,mutation,mutated,((text)), (error),(((watermark))),((logo)),(((username))),(((font))),((signature)), missing fingers,extra digit, fewer digits, cropped, worst quality, low quality,normal quality, jpeg artifacts, signature, watermark, username, blurry,book")

    @property
    def sd_style(self) -> str:
        """用户自定义的图像风格参数，将被附加到提示词中"""
        return os.getenv('SD_STYLE', '')
    
    # ================================
    # ADetailer配置
    # ================================
    
    @property
    def sd_adetailer_enabled(self) -> bool:
        """是否启用ADetailer"""
        return self._get_bool('SD_ADETAILER_ENABLED', True)
    
    @property
    def sd_adetailer_face_model(self) -> str:
        """ADetailer面部检测模型"""
        return os.getenv('SD_ADETAILER_FACE_MODEL', 'face_yolov8n.pt')
    
    @property
    def sd_adetailer_hand_model(self) -> str:
        """ADetailer手部检测模型"""
        return os.getenv('SD_ADETAILER_HAND_MODEL', 'hand_yolov8n.pt')
    
    # ================================
    # LoRA模型配置
    # ================================
    
    @property
    def lora_models(self) -> Dict[int, str]:
        """获取LoRA模型配置字典"""
        models = {}
        for i in range(10):  # 支持0-9号模型
            key = f'LORA_MODEL_{i}'
            value = os.getenv(key, '')
            models[i] = value
        return models
    
    # ================================
    # 文件路径配置
    # ================================
    
    @property
    def input_dir(self) -> Path:
        return self.project_root / os.getenv('INPUT_DIR', 'data/input')
    
    @property
    def output_dir_txt(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_DIR_TXT', 'data/output/processed')
    
    @property
    def output_dir_image(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_DIR_IMAGE', 'data/output/images')
    
    @property
    def output_dir_voice(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_DIR_VOICE', 'data/output/audio')
    
    @property
    def output_dir_video(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_DIR_VIDEO', 'data/output/videos')
    
    @property
    def output_dir_temp(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_DIR_TEMP', 'data/temp')
    
    # 具体文件路径
    @property
    def input_md_file(self) -> Path:
        return self.project_root / os.getenv('INPUT_MD_FILE', 'data/input/input.md')
    

    
    @property
    def output_csv_file(self) -> Path:
        return self.project_root / os.getenv('OUTPUT_CSV_FILE', 'data/output/processed/txt.csv')
    
    def get_available_json_file(self) -> Path:
        """
        检测processed文件夹中的JSON文件并自动选择或提示用户选择
        
        Returns:
            Path: 选择的JSON文件路径
            
        Raises:
            FileNotFoundError: 当没有找到任何JSON文件时
        """
        processed_dir = self.project_root / 'data/output/processed'
        sd_prompt_file = processed_dir / 'sd_prompt.json'
        flux1_prompt_file = processed_dir / 'Flux1_prompt.json'
        
        # 检查文件是否存在
        sd_exists = sd_prompt_file.exists()
        flux1_exists = flux1_prompt_file.exists()
        
        if sd_exists and flux1_exists:
            # 两个文件都存在，提示用户选择
            print("\n检测到两个prompt文件:")
            print("1. sd_prompt.json")
            print("2. Flux1_prompt.json")
            
            while True:
                try:
                    choice = input("请选择要使用的文件 (1 或 2): ").strip()
                    if choice == '1':
                        print(f"已选择: {sd_prompt_file}")
                        return sd_prompt_file
                    elif choice == '2':
                        print(f"已选择: {flux1_prompt_file}")
                        return flux1_prompt_file
                    else:
                        print("无效选择，请输入 1 或 2")
                except KeyboardInterrupt:
                    print("\n操作已取消")
                    raise
        elif sd_exists:
            # 只有sd_prompt.json存在
            print(f"自动选择: {sd_prompt_file}")
            return sd_prompt_file
        elif flux1_exists:
            # 只有Flux1_prompt.json存在
            print(f"自动选择: {flux1_prompt_file}")
            return flux1_prompt_file
        else:
            # 没有找到任何文件
            raise FileNotFoundError(
                f"在 {processed_dir} 中未找到 sd_prompt.json 或 Flux1_prompt.json 文件"
            )
    
    @property
    def output_json_file(self) -> Path:
        """
        获取输出JSON文件路径，支持自动选择
        
        如果设置了环境变量OUTPUT_JSON_FILE，则使用该值
        否则使用自动选择逻辑
        """
        env_file = os.getenv('OUTPUT_JSON_FILE')
        if env_file:
            return self.project_root / env_file
        
        # 使用自动选择逻辑
        try:
            return self.get_available_json_file()
        except FileNotFoundError:
            # 如果没有找到文件，返回默认的sd_prompt.json路径
            return self.project_root / 'data/output/processed/sd_prompt.json'
    
    @property
    def params_json_file(self) -> Path:
        return self.project_root / os.getenv('PARAMS_JSON_FILE', 'temp/params.json')
    
    # ================================
    # 文本处理配置
    # ================================
    
    @property
    def min_sentence_length(self) -> int:
        return self._get_int('MIN_SENTENCE_LENGTH', 30)
    
    @property
    def max_workers_translation(self) -> int:
        return self._get_int('MAX_WORKERS_TRANSLATION', 10)
    
    @property
    def max_workers_image(self) -> int:
        return self._get_int('MAX_WORKERS_IMAGE', 5)
    
    @property
    def max_workers_video(self) -> int:
        return self._get_int('MAX_WORKERS_VIDEO', 5)
    
    @property
    def encoding_list(self) -> List[str]:
        """文件编码尝试列表"""
        default_encodings = [
            'utf8', 'gbk', 'gb2312', 'latin1', 'iso-8859-1', 'big5', 'utf16', 'utf32', 'ascii',
            'cp037', 'cp1252', 'cp949', 'cp1133', 'cp437', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213',
            'shift_jis', 'shift_jis_2004', 'shift_jisx0213', 'iso2022_jp', 'iso2022_jp_1',
            'iso2022_jp_2', 'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'hz'
        ]
        return self._get_list('ENCODING_LIST', default_encodings)

    # ================================
    # 文本分割器配置
    # ================================
    
    @property
    def text_splitter_supported_input(self) -> List[str]:
        """文本分割器支持的输入格式"""
        return self._get_list('TEXT_SPLITTER_SUPPORTED_INPUT', ['md'])
    
    @property
    def text_splitter_supported_output(self) -> List[str]:
        """文本分割器支持的输出格式"""
        return self._get_list('TEXT_SPLITTER_SUPPORTED_OUTPUT', ['json'])
    
    @property
    def text_splitter_default_input_format(self) -> str:
        """文本分割器默认输入格式"""
        return os.getenv('TEXT_SPLITTER_DEFAULT_INPUT_FORMAT', 'md')
    
    @property
    def text_splitter_default_output_format(self) -> str:
        """文本分割器默认输出格式"""
        return os.getenv('TEXT_SPLITTER_DEFAULT_OUTPUT_FORMAT', 'json')
    
    @property
    def text_splitter_chapter_patterns(self) -> List[str]:
        """文本分割器章节识别模式"""
        default_patterns = ['# ', '## ', '### ', '第.*章', 'Chapter']
        return self._get_list('TEXT_SPLITTER_CHAPTER_PATTERNS', default_patterns)

    # ================================
    # 视频生成配置
    # ================================
    
    @property
    def video_fps(self) -> int:
        return self._get_int('VIDEO_FPS', 30)
    
    @property
    def video_load_subtitles(self) -> bool:
        # 支持两种配置项名称：VIDEO_SUBTITLE 和 VIDEO_LOAD_SUBTITLES
        return self._get_bool('VIDEO_SUBTITLE', self._get_bool('VIDEO_LOAD_SUBTITLES', False))
    
    @property
    def video_enlarge_background(self) -> bool:
        return self._get_bool('VIDEO_ENLARGE_BACKGROUND', False)
    
    @property
    def video_enable_effect(self) -> bool:
        return self._get_bool('VIDEO_ENABLE_EFFECT', False)
    
    @property
    def video_effect_type(self) -> str:
        return os.getenv('VIDEO_EFFECT_TYPE', 'fade')
    
    # 字幕配置
    @property
    def subtitle_fontsize(self) -> int:
        # 支持两种配置项名称：SUBTITLE_SIZE 和 SUBTITLE_FONTSIZE
        return self._get_int('SUBTITLE_SIZE', self._get_int('SUBTITLE_FONTSIZE', 60))
    
    @property
    def subtitle_fontcolor(self) -> str:
        # 支持两种配置项名称：SUBTITLE_COLOR 和 SUBTITLE_FONTCOLOR
        return os.getenv('SUBTITLE_COLOR', os.getenv('SUBTITLE_FONTCOLOR', 'white'))
    
    @property
    def subtitle_stroke_color(self) -> str:
        return os.getenv('SUBTITLE_STROKE_COLOR', 'black')
    
    @property
    def subtitle_stroke_width(self) -> int:
        return self._get_int('SUBTITLE_STROKE_WIDTH', 2)
    
    @property
    def subtitle_font(self) -> str:
        return os.getenv('SUBTITLE_FONT', 'PingFang SC')
    
    @property
    def subtitle_align(self) -> str:
        return os.getenv('SUBTITLE_ALIGN', 'center')
    
    @property
    def subtitle_pixel_from_bottom(self) -> int:
        # 如果设置了SUBTITLE_POSITION，根据位置计算像素值
        position_str = os.getenv('SUBTITLE_POSITION', '')
        
        # 首先尝试将SUBTITLE_POSITION解析为数字
        if position_str:
            try:
                # 如果是数字，直接返回
                return int(position_str)
            except ValueError:
                # 如果不是数字，按字符串处理
                position = position_str.lower()
                if position == 'bottom':
                    return 50  # 底部位置
                elif position == 'top':
                    return -50  # 顶部位置（负值表示从顶部开始）
                elif position == 'center':
                    return 0   # 中心位置
        
        # 使用原有的SUBTITLE_PIXEL_FROM_BOTTOM配置
        return self._get_int('SUBTITLE_PIXEL_FROM_BOTTOM', 50)
    
    # ================================
    # 系统配置
    # ================================
    
    @property
    def python_executable(self) -> str:
        return os.getenv('PYTHON_EXECUTABLE', 'python')
    
    @property
    def debug_mode(self) -> bool:
        return self._get_bool('DEBUG_MODE', False)
    
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO')
    
    # ================================
    # 辅助方法
    # ================================
    
    def validate_config(self) -> List[str]:
        """验证配置完整性，返回错误信息列表"""
        errors = []
        
        # 检查LLM服务配置
        if self.llm_provider == 'openai':
            if not self.openai_api_key:
                errors.append("OpenAI API key is required (OPENAI_API_KEY)")
        elif self.llm_provider == 'deepseek':
            if not self.deepseek_api_key:
                errors.append("DeepSeek API key is required (DEEPSEEK_API_KEY)")
        else:
            errors.append(f"Unsupported LLM provider: {self.llm_provider} (supported: openai, deepseek)")
        
        if not self.azure_speech_key:
            errors.append("Azure Speech key is required (AZURE_SPEECH_KEY)")
        
        # 检查SD API URL
        if not self.sd_api_url or not self.sd_api_url.startswith('http'):
            errors.append("Valid Stable Diffusion API URL is required (SD_API_URL)")
        
        return errors
    
    def get_sd_generation_data(self, prompt: str) -> Dict:
        """生成Stable Diffusion API请求数据"""
        data = {
            "enable_hr": self.sd_enable_hr,
            "denoising_strength": self.sd_denoising_strength,
            "firstphase_width": self.sd_firstphase_width,
            "firstphase_height": self.sd_firstphase_height,
            "hr_scale": self.sd_hr_scale,
            "hr_upscaler": self.sd_hr_upscaler,
            "hr_second_pass_steps": self.sd_hr_second_pass_steps,
            "hr_resize_x": self.sd_hr_resize_x,
            "hr_resize_y": self.sd_hr_resize_y,
            "prompt": prompt,
            "seed": self.sd_seed,
            "sampler_name": self.sd_sampler_name,
            "batch_size": self.sd_batch_size,
            "steps": self.sd_steps,
            "cfg_scale": self.sd_cfg_scale,
            "restore_faces": self.sd_restore_faces,
            "tiling": self.sd_tiling,
            "negative_prompt": self.sd_negative_prompt
        }
        
        # 添加ADetailer配置
        if self.sd_adetailer_enabled:
            data["alwayson_scripts"] = {
                "ADetailer": {
                    "args": [
                        {"ad_model": self.sd_adetailer_face_model},
                        {"ad_model": self.sd_adetailer_hand_model},
                        {}
                    ]
                }
            }
        
        return data
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("=" * 50)
        print("story-flow Generator Configuration")
        print("=" * 50)
        print(f"Project Root: {self.project_root}")
        print(f"LLM Provider: {self.llm_provider}")
        if self.llm_provider == 'openai':
            print(f"OpenAI Model: {self.openai_model}")
        elif self.llm_provider == 'deepseek':
            print(f"DeepSeek Model: {self.deepseek_model}")
        print(f"Azure Voice: {self.azure_voice_name}")
        print(f"SD API URL: {self.sd_api_url}")
        print(f"Video FPS: {self.video_fps}")
        print(f"Debug Mode: {self.debug_mode}")
        print("=" * 50)


# 全局配置实例
config = Config()

# 验证配置
if __name__ == "__main__":
    errors = config.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
    
    config.print_config_summary()
