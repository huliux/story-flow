# 📚 API参考文档

## 🔧 配置参数参考

### LLM服务配置

#### 通用配置
```env
# 服务商选择
LLM_PROVIDER=deepseek  # openai | deepseek

# 通用LLM参数
LLM_MAX_TOKENS=500            # 单次生成最大token数
LLM_COOLDOWN_SECONDS=60       # API请求间隔冷却时间
LLM_MAX_REQUESTS=90           # 每分钟最大请求数
LLM_TEMPERATURE=0.7           # 生成随机性 (0.0-2.0)
```

#### OpenAI配置
```env
OPENAI_API_KEY=sk-xxxxx       # OpenAI API密钥
OPENAI_BASE_URL=https://api.openai.com/v1  # API基础URL
OPENAI_MODEL=gpt-3.5-turbo-16k  # 模型名称

# 支持的模型
# - gpt-3.5-turbo
# - gpt-3.5-turbo-16k  
# - gpt-4
# - gpt-4-turbo
```

#### DeepSeek配置
```env
DEEPSEEK_API_KEY=sk-xxxxx     # DeepSeek API密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1  # API基础URL
DEEPSEEK_MODEL=deepseek-chat  # 模型名称

# 支持的模型
# - deepseek-chat
# - deepseek-coder
```

### Azure语音服务配置

```env
# 基础配置
AZURE_SPEECH_KEY=xxxxx        # Azure语音服务密钥
AZURE_SPEECH_REGION=eastasia  # 服务区域

# 语音配置
AZURE_VOICE_NAME=zh-CN-YunxiNeural    # 语音名称
AZURE_VOICE_STYLE=calm                # 语音风格
AZURE_VOICE_ROLE=OlderAdultMale       # 语音角色
AZURE_VOICE_RATE=+40%                 # 语速 (-50% 到 +100%)
AZURE_VOICE_VOLUME=+30%               # 音量 (-50% 到 +50%)
```

#### 支持的中文语音
| 语音名称 | 性别 | 特点 |
|----------|------|------|
| zh-CN-YunxiNeural | 男 | 成熟稳重 |
| zh-CN-XiaoxiaoNeural | 女 | 甜美温柔 |
| zh-CN-YunyangNeural | 男 | 年轻活力 |
| zh-CN-XiaochenNeural | 女 | 清新自然 |

#### 语音风格选项
- `calm` - 冷静
- `cheerful` - 欢快
- `sad` - 悲伤
- `angry` - 愤怒
- `fearful` - 恐惧
- `disgruntled` - 不满

### Stable Diffusion配置

```env
# API连接
SD_API_URL=http://localhost:7860     # SD WebUI API地址

# 生成参数
SD_STEPS=30                          # 生成步数 (1-150)
SD_CFG_SCALE=7.5                     # CFG引导强度 (1-30)
SD_WIDTH=1360                        # 图像宽度
SD_HEIGHT=1024                       # 图像高度
SD_SAMPLER=Euler a                   # 采样器

# LoRA模型
SD_LORA_MODELS=优秀偶像男01,富家男02,古惑男01,lightAndShadow_v10
```

#### 支持的采样器
- `Euler a` - 推荐，速度快
- `DPM++ 2M Karras` - 高质量
- `DDIM` - 稳定
- `LMS` - 传统方法

#### LoRA权重配置
```python
# 在提示词中自动应用
"<lora:优秀偶像男01:0.7>, <lora:富家男02:0.4>"
```

### 项目路径配置

```env
# 基础路径
PROJECT_ROOT=/path/to/project         # 项目根目录

# 输入输出路径
INPUT_TXT_FILE=input.txt              # 输入文本文件
INPUT_DOCX_FILE=input/input.docx      # 分割后的docx文件
OUTPUT_EXCEL_FILE=txt/txt.xlsx        # AI分析结果文件

# 目录配置
OUTPUT_DIR_IMAGE=image                # 图像输出目录
OUTPUT_DIR_VOICE=voice                # 语音输出目录  
OUTPUT_DIR_VIDEO=video                # 视频输出目录
TEMP_DIR=temp                         # 临时文件目录
```

### 视频生成配置

```env
# 视频参数
VIDEO_FPS=30                          # 视频帧率
VIDEO_SUBTITLE=true                   # 是否添加字幕
VIDEO_EFFECTS=true                    # 是否添加特效

# 字幕配置
SUBTITLE_FONT=SimHei                  # 字体名称
SUBTITLE_SIZE=36                      # 字体大小
SUBTITLE_COLOR=#FFFFFF                # 字体颜色
SUBTITLE_POSITION=bottom              # 字幕位置

# 其他视频设置
VIDEO_QUALITY=high                    # 视频质量 (low|medium|high)
VIDEO_BITRATE=5000k                   # 视频比特率
AUDIO_BITRATE=192k                    # 音频比特率
```

### 性能配置

```env
# 并发处理
MAX_WORKERS_TRANSLATION=4            # 翻译并发数
MAX_WORKERS_IMAGE=2                   # 图像生成并发数

# 文本处理
MIN_SENTENCE_LENGTH=10                # 最小句子长度
ENCODING_LIST=utf-8,gb2312,gbk        # 支持的编码格式

# 系统配置
DEBUG=false                           # 调试模式
LOG_LEVEL=INFO                        # 日志级别
```

## 🔌 API接口文档

### 配置管理API

#### `config.Config`

主配置类，提供统一的配置访问接口。

```python
from config import config

# 访问配置
api_key = config.openai_api_key
model = config.llm_model
timeout = config.api_timeout

# 验证配置
errors = config.validate_config()
if errors:
    print("配置错误:", errors)
```

**主要属性**:
- `llm_provider: str` - LLM服务商
- `project_root: Path` - 项目根目录
- `input_txt_file: Path` - 输入文本文件路径
- `output_excel_file: Path` - 输出Excel文件路径

**主要方法**:
- `validate_config() -> List[str]` - 验证配置
- `print_config_summary()` - 打印配置摘要

### LLM客户端API

#### `llm_client.LLMClient`

统一的LLM调用接口，支持多个服务商。

```python
from llm_client import llm_client

# 基础翻译
english_text = llm_client.translate_to_english("你好世界")

# 分镜脚本生成  
storyboard = llm_client.translate_to_storyboard("一个男孩在森林里跑步")

# 自定义对话
messages = [
    {"role": "system", "content": "你是一个翻译助手"},
    {"role": "user", "content": "翻译：你好"}
]
response = llm_client.chat_completion(messages)
```

**主要方法**:

##### `translate_to_english(text: str) -> str`
将中文文本翻译为英文。

**参数**:
- `text` - 需要翻译的中文文本

**返回**:
- 翻译后的英文文本

**异常**:
- `APIError` - API调用失败

##### `translate_to_storyboard(text: str) -> str`
将文本转换为Stable Diffusion提示词。

**参数**:
- `text` - 描述性文本

**返回**:
- SD格式的提示词

##### `chat_completion(messages, max_tokens=None, temperature=None) -> str`
通用的对话完成接口。

**参数**:
- `messages` - 对话消息列表
- `max_tokens` - 最大token数 (可选)
- `temperature` - 随机性参数 (可选)

**返回**:
- 模型响应内容

### 步骤模块API

#### Step 1: 文本分析

```python
from step1_extract_keywords import main

# 执行文本分析
success = main()
```

**输入**: `input/input.docx`
**输出**: `txt/txt.xlsx`

**交互流程**:
1. 系统提示文本替换
2. 用户输入: `原文 新文 数字`
3. 系统处理并生成分析结果

#### Step 2: 图像生成

```python
from step2_txt_to_image import main

# 执行图像生成
success = main()
```

**输入**: `txt/txt.xlsx`
**输出**: `image/*.png`

**生成参数**:
- 分辨率: 1360x1024
- 采样器: Euler a
- 步数: 30
- CFG: 7.5

#### Step 3: 语音合成

```python
from step3_txt_to_voice import main

# 执行语音合成
success = main()
```

**输入**: `txt/txt.xlsx`
**输出**: `voice/*.wav`

**音频格式**:
- 采样率: 24kHz
- 格式: WAV
- 声道: 单声道

#### Step 4: 视频生成

```python
from step4_output_video import main

# 执行视频生成
success = main()
```

**输入**: `image/`, `voice/`
**输出**: `video/*.mp4`

**视频规格**:
- 分辨率: 1360x1024
- 帧率: 30fps
- 编码: H.264

### 工具API

#### 环境设置

```python
from setup_env import setup_environment

# 设置环境
setup_environment()
```

#### LLM测试

```python
from test_llm import run_llm_tests

# 测试LLM连接
run_llm_tests()
```

#### 清理工具

```python
from cleanup import clean_generated_files

# 清理生成文件
clean_generated_files()
```

## 📊 数据格式规范

### Excel文件格式 (txt.xlsx)

| 列 | 名称 | 描述 | 示例 |
|----|------|------|------|
| A | 原始中文 | 分句后的中文文本 | "他走向那把剑" |
| B | 英文翻译 | AI翻译的英文 | "He walks towards the sword" |
| C | SD提示词 | 图像生成提示词 | "1boy, medieval, sword, detailed..." |
| D | 替换后中文 | 用户替换后的文本 | "李明走向倚天剑" |
| E | 角色编号 | 角色/物品编号 | "1" |

### 文件命名规范

#### 图像文件
```
image/
├── 001.png              # 第1句对应图像
├── 002.png              # 第2句对应图像
└── ...
```

#### 语音文件
```
voice/
├── 001.wav              # 第1句对应语音
├── 002.wav              # 第2句对应语音
└── ...
```

#### 视频文件
```
video/
├── output_20250123_143052.mp4    # 时间戳命名
└── final.mp4                     # 最终版本
```

## ⚡ 性能优化参数

### 并发控制

```env
# 翻译并发数 (建议: CPU核心数)
MAX_WORKERS_TRANSLATION=4

# 图像生成并发数 (建议: GPU数量)  
MAX_WORKERS_IMAGE=1

# API请求间隔 (避免速率限制)
LLM_COOLDOWN_SECONDS=1
```

### 内存优化

```env
# 批处理大小
BATCH_SIZE=10

# 图像缓存大小
IMAGE_CACHE_SIZE=100

# 启用内存清理
ENABLE_MEMORY_CLEANUP=true
```

### 网络优化

```env
# 请求超时 (秒)
API_TIMEOUT=300

# 重试次数
RETRY_TIMES=3

# 连接池大小
CONNECTION_POOL_SIZE=10
```

## 🚨 错误码参考

### LLM错误

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 401 | API密钥无效 | 检查API密钥配置 |
| 429 | 请求过于频繁 | 增加冷却时间 |
| 500 | 服务器内部错误 | 稍后重试 |

### Azure TTS错误

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 401 | 认证失败 | 检查密钥和区域 |
| 400 | 语音配置错误 | 检查语音名称 |
| 403 | 配额不足 | 检查服务配额 |

### Stable Diffusion错误

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 404 | 服务未启动 | 启动SD WebUI |
| 500 | 生成失败 | 检查模型和参数 |
| 503 | 服务忙碌 | 等待后重试 |

## 🔍 调试配置

### 调试模式

```env
DEBUG=true                    # 启用调试模式
LOG_LEVEL=DEBUG              # 详细日志
SAVE_INTERMEDIATE_FILES=true # 保存中间文件
```

### 日志配置

```python
import logging

# 配置日志级别
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 测试配置

```env
# 测试模式
TESTING=true
TEST_API_CALLS=false         # 跳过实际API调用
MOCK_RESPONSES=true          # 使用模拟响应
```

---

## 💡 使用建议

### 配置优化建议

1. **开发环境**
   ```env
   DEBUG=true
   LOG_LEVEL=DEBUG
   MAX_WORKERS_TRANSLATION=2
   LLM_MAX_TOKENS=200
   ```

2. **生产环境**
   ```env
   DEBUG=false
   LOG_LEVEL=INFO
   MAX_WORKERS_TRANSLATION=8
   LLM_MAX_TOKENS=500
   ```

3. **高性能环境**
   ```env
   MAX_WORKERS_TRANSLATION=16
   MAX_WORKERS_IMAGE=4
   BATCH_SIZE=20
   CONNECTION_POOL_SIZE=20
   ```

### 成本优化建议

1. **使用DeepSeek** - 相比OpenAI节省70%以上成本
2. **调整token数** - 根据需要设置`LLM_MAX_TOKENS`
3. **批量处理** - 一次处理多个章节
4. **缓存结果** - 避免重复翻译相同文本

---

**需要了解具体使用方法，请查看 [用户指南](user-guide.md)。**
