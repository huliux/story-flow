# 🔧 环境配置指南

## 📋 系统要求

### 基础环境
- **操作系统**: macOS 10.15+ / Windows 10+ / Ubuntu 18.04+
- **Python**: 3.8+ (推荐 3.12)
- **内存**: 8GB+ RAM
- **存储**: 5GB+ 可用空间

### 外部服务
- **LLM服务**: OpenAI API 或 DeepSeek API
- **语音服务**: Azure Cognitive Services
- **图像生成**: Stable Diffusion WebUI API

## 🐍 Python环境设置

### 方案一：使用现有虚拟环境（推荐）

项目已配置独立虚拟环境 `.venv/`，包含所有依赖。

```bash
# 快速启动
./activate_env.sh

# 验证环境
python setup_env.py
```

### 方案二：重新创建虚拟环境

```bash
# 删除现有环境（如需要）
rm -rf .venv

# 创建新的虚拟环境
python -m venv .venv

# 激活环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装spaCy中文模型
python -m spacy download zh_core_web_sm
```

## 🔑 API服务配置

### LLM服务配置

#### 选项1: DeepSeek（推荐 - 性价比高）

1. **注册DeepSeek账号**
   - 访问 https://platform.deepseek.com
   - 注册并获取API密钥

2. **配置示例**
   ```env
   LLM_PROVIDER=deepseek
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
   DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
   DEEPSEEK_MODEL=deepseek-chat
   ```

3. **费用参考**
   - 输入: ¥0.14/万tokens
   - 输出: ¥0.28/万tokens
   - 处理1000字文本约 ¥0.10

#### 选项2: OpenAI

1. **获取OpenAI API密钥**
   - 访问 https://platform.openai.com
   - 创建API密钥

2. **配置示例**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-xxxxxxxxxxxxx
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-3.5-turbo-16k
   ```

### Azure语音服务配置

1. **创建Azure认知服务**
   - 登录 https://portal.azure.com
   - 创建"语音服务"资源
   - 获取密钥和区域

2. **配置示例**
   ```env
   AZURE_SPEECH_KEY=xxxxxxxxxxxxxxxx
   AZURE_SPEECH_REGION=eastasia
   AZURE_VOICE_NAME=zh-CN-YunxiNeural
   ```

3. **费用参考**
   - 标准语音: $4.50/百万字符
   - 神经语音: $16.00/百万字符

### Stable Diffusion服务

#### 方案1: 本地部署

1. **安装Stable Diffusion WebUI**
   ```bash
   git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
   cd stable-diffusion-webui
   ./webui.sh --api --listen
   ```

2. **配置模型**
   - 下载 Stable Diffusion 1.5 基础模型
   - 下载中文LoRA模型（优秀偶像男01、富家男02等）

3. **配置连接**
   ```env
   SD_API_URL=http://localhost:7860
   ```

#### 方案2: 云服务

使用AutoDL、恒源云等GPU云服务器部署。

```env
SD_API_URL=http://your-cloud-server:7860
```

## 📁 项目目录结构

运行 `python setup_env.py` 会自动创建必需目录：

```
txt_to_video_lora/
├── .venv/                    # Python虚拟环境
├── docs/                     # 文档目录
├── input/                    # 输入文件目录
│   └── input.txt            # 文本输入文件
├── txt/                      # 文本处理结果
│   └── txt.xlsx            # AI分析结果
├── image/                    # 生成的图像
├── voice/                    # 语音文件
├── video/                    # 最终视频
├── temp/                     # 临时文件
├── .env                      # 配置文件
├── env.example              # 配置模板
└── [核心模块]
```

## ⚙️ 配置文件详解

### 完整配置模板

```env
# ================================
# AI服务配置
# ================================

# 大语言模型服务商选择: openai, deepseek
LLM_PROVIDER=deepseek

# OpenAI API配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo-16k

# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 通用LLM配置
LLM_MAX_TOKENS=500
LLM_COOLDOWN_SECONDS=60
LLM_MAX_REQUESTS=90
LLM_TEMPERATURE=0.7

# Azure语音服务配置
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastasia
AZURE_VOICE_NAME=zh-CN-YunxiNeural
AZURE_VOICE_STYLE=calm
AZURE_VOICE_ROLE=OlderAdultMale
AZURE_VOICE_RATE=+40%
AZURE_VOICE_VOLUME=+30%

# ================================
# Stable Diffusion配置
# ================================

SD_API_URL=http://192.168.50.80.1:7860
SD_STEPS=30
SD_CFG_SCALE=7.5
SD_WIDTH=1360
SD_HEIGHT=1024
SD_SAMPLER=Euler a
SD_LORA_MODELS=优秀偶像男01,富家男02,古惑男01,lightAndShadow_v10

# ================================
# 项目路径配置
# ================================

PROJECT_ROOT=/Users/forest/txt_to_video_lora
INPUT_TXT_FILE=input.txt
INPUT_DOCX_FILE=input/input.docx
OUTPUT_EXCEL_FILE=txt/txt.xlsx
OUTPUT_DIR_IMAGE=image
OUTPUT_DIR_VOICE=voice
OUTPUT_DIR_VIDEO=video
TEMP_DIR=temp

# ================================
# 视频生成配置
# ================================

VIDEO_FPS=30
VIDEO_SUBTITLE=true
VIDEO_EFFECTS=true
SUBTITLE_FONT=SimHei
SUBTITLE_SIZE=36
SUBTITLE_COLOR=#FFFFFF
SUBTITLE_POSITION=bottom

# ================================
# 高级配置
# ================================

# 并发处理
MAX_WORKERS_TRANSLATION=4
MAX_WORKERS_IMAGE=2

# 文本处理
MIN_SENTENCE_LENGTH=10
ENCODING_LIST=utf-8,gb2312,gbk,gb18030

# 调试模式
DEBUG=false
LOG_LEVEL=INFO
```

### 配置优先级

1. `.env` 文件中的设置
2. 系统环境变量  
3. 代码中的默认值

## 🧪 环境验证

### 自动验证

```bash
# 激活环境并运行验证
./activate_env.sh
python setup_env.py
```

### 手动验证

```bash
# 1. 验证Python环境
python --version
pip list | grep -E "(openai|azure|requests|spacy)"

# 2. 验证spaCy模型
python -c "import spacy; nlp=spacy.load('zh_core_web_sm'); print('✅ spaCy模型正常')"

# 3. 验证配置加载
python -c "from config import config; print(f'✅ 配置正常: {config.llm_provider}')"

# 4. 测试LLM连接
python test_llm.py

# 5. 测试Stable Diffusion连接
curl -X GET "${SD_API_URL}/sdapi/v1/options"
```

## 🔧 故障排除

### Python环境问题

**问题**: `ModuleNotFoundError`
```bash
# 解决方案
source .venv/bin/activate  # 确保激活虚拟环境
pip install -r requirements.txt
```

**问题**: spaCy模型缺失
```bash
# 解决方案
python -m spacy download zh_core_web_sm --user
```

### API连接问题

**问题**: OpenAI API错误
```bash
# 检查网络连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# 检查密钥格式
echo $OPENAI_API_KEY | grep "^sk-"
```

**问题**: Azure TTS错误
```bash
# 验证区域设置
curl -H "Ocp-Apim-Subscription-Key: $AZURE_SPEECH_KEY" \
     "https://${AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/voices/list"
```

**问题**: Stable Diffusion连接失败
```bash
# 检查服务状态
curl -X GET ${SD_API_URL}/sdapi/v1/options
netstat -an | grep 7860
```

### 权限问题

**macOS/Linux**:
```bash
chmod +x activate_env.sh
chmod 755 .venv/bin/activate
```

**Windows**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🔄 环境更新

### 依赖更新

```bash
# 激活环境
source .venv/bin/activate

# 更新所有包
pip install --upgrade -r requirements.txt

# 重新验证
python setup_env.py
```

### 配置迁移

当有新配置项时：
```bash
# 备份现有配置
cp .env .env.backup

# 对比新模板
diff .env env.example

# 手动添加新配置项
```

## 💡 性能优化建议

### 硬件优化
- **GPU**: RTX 3060+ 用于Stable Diffusion
- **CPU**: 8核心+ 用于并发处理
- **内存**: 16GB+ 避免内存不足
- **存储**: SSD 提高I/O性能

### 软件优化
- 使用最新Python版本
- 启用GPU加速（如可用）
- 调整并发工作线程数
- 使用本地模型缓存

---

**环境配置完成后，请查看 [用户指南](user-guide.md) 开始使用系统！**
