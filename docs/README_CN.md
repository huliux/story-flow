# 📺 Story Flow - 智能文本到视频生成系统

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/badge/uv-package%20manager-blue.svg)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.0-orange.svg)](https://github.com/story-flow/story-flow)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](#)
[![Code Quality](https://img.shields.io/badge/Code%20Quality-A+-brightgreen.svg)](#)

**🚀 将文字变成视频，让故事活起来！**

*基于AI的自动化视频生成系统，专为内容创作者打造*

**🌍 语言:** [English](../README.md) | [中文](README_CN.md)

</div>

---

## 🌟 为什么选择 Story Flow？

**Story Flow** 是一个革命性的AI文本到视频生成系统，专为解决内容创作者的痛点而生：

- 📝 **告别繁琐制作** - 从文本到视频，一键完成，节省90%制作时间
- 🎨 **专业级视觉效果** - AI生成高质量图像，媲美专业设计师作品
- 🎙️ **真人级语音合成** - Azure TTS技术，自然流畅的中文语音
- 🎬 **电影级视频输出** - 自动字幕、转场特效，专业视频制作水准
- 🔧 **零技术门槛** - 简单配置，小白也能制作专业视频内容

## 🎯 核心优势

<table>
<tr>
<td width="50%">

### 🚀 **极速生成**
- ⚡ **3分钟生成** - 1000字文本3分钟内完成视频
- 🔄 **批量处理** - 支持多章节并行处理
- 📊 **实时进度** - 可视化处理进度追踪

### 🎨 **专业品质**
- 🖼️ **4K高清输出** - 支持多种分辨率
- 🎭 **角色一致性** - LoRA模型确保角色形象统一
- 🎵 **智能配音** - 多种音色，情感丰富

</td>
<td width="50%">

### 🧠 **智能理解**
- 📖 **深度文本分析** - AI理解故事情节和情感
- 👥 **角色识别** - 自动识别和管理多个角色
- 🎬 **场景生成** - 智能生成符合情节的视觉场景

### 🔧 **灵活配置**
- 🎛️ **参数可调** - 200+配置项，满足个性化需求
- 🔌 **模块化设计** - 可独立使用各个功能模块
- 🌐 **多服务支持** - 支持多种AI服务商

</td>
</tr>
</table>

## ✨ 核心特性

### 🧠 智能文本分析
- **语义分析** - 基于大语言模型的深度文本理解
- **角色识别** - 自动识别和映射故事角色，支持自定义角色配置
- **场景提取** - 智能提取场景描述和视觉元素
- **格式支持** - 支持Markdown、TXT等多种输入格式
- **句子优化** - 智能合并短句，确保语义完整性

### 🎨 多平台图像生成
- **Stable Diffusion** - 本地SD WebUI API支持
- **LiblibAI** - 云端AI绘画服务集成
- **ComfyUI** - 专业级图像生成工作流
- **并行处理** - 多线程批量生成，大幅提升效率
- **智能提示词** - 自动优化和风格控制
- **LoRA支持** - 灵活的模型微调和风格定制

### 🎵 专业语音合成
- **Azure TTS** - 微软认知服务高质量语音合成
- **SSML支持** - 完整的语音标记语言支持
- **多维控制** - 语速、音调、音量、情感表达精确控制
- **异步处理** - 高效的并发语音生成
- **静音优化** - 自动检测和移除静音片段

### 🎬 智能视频合成
- **MoviePy引擎** - 专业级视频处理能力
- **自动同步** - 图像、音频、字幕智能同步
- **特效支持** - 多种视觉效果和转场动画
- **字幕系统** - 自动生成和样式定制
- **背景音乐** - 智能音频混合和淡入淡出
- **多格式输出** - 支持多种视频格式和质量选项

### 📚 高级功能
- **多章节处理** - 支持长篇内容的章节化处理
- **语义分析器** - 独立的故事语义分析模块
- **病毒视频生成** - 专门的短视频内容生成器
- **故事生成器** - AI驱动的原创故事创作

## 🚀 快速开始

### 📋 系统要求

<table>
<tr>
<td><strong>💻 操作系统</strong></td>
<td>Windows 10+ / macOS 10.15+ / Ubuntu 18.04+</td>
</tr>
<tr>
<td><strong>🐍 Python版本</strong></td>
<td>3.10+ (推荐 3.11)</td>
</tr>
<tr>
<td><strong>💾 内存要求</strong></td>
<td>8GB+ (推荐 16GB，支持更快的并行处理)</td>
</tr>
<tr>
<td><strong>💿 存储空间</strong></td>
<td>5GB+ (包含模型文件和输出缓存)</td>
</tr>
<tr>
<td><strong>🌐 网络要求</strong></td>
<td>稳定网络连接 (用于AI服务调用)</td>
</tr>
<tr>
<td><strong>🎮 GPU支持</strong></td>
<td>可选 (NVIDIA GPU可加速本地Stable Diffusion)</td>
</tr>
</table>

> **💡 性能提示**: 配置越高，生成速度越快。推荐配置可实现3分钟生成1000字视频。

### 🛠️ 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/story-flow/story-flow.git
cd story-flow
```

#### 2. 环境准备
```bash
# 使用 uv 管理依赖（推荐）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境（可选，uv run 会自动激活）
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

#### 3. 配置API服务
```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件，填入你的API密钥
nano .env  # 或使用你喜欢的编辑器
```

#### 4. 验证安装
```bash
# 运行环境设置脚本（自动检查和配置环境）
./setup.sh

# 测试系统连接
uv run python -m tests.examples.test_liblib_config  # 测试图像生成
uv run python -m src.pipeline.text_analyzer --test  # 测试文本分析
```

> **✅ 安装成功标志**: 看到 "✓ All systems ready!" 表示安装成功
> 
> **🔧 故障排除**: 如遇问题，脚本会提供详细错误信息和解决方案

### 🎬 三步开始创作

#### 🎯 **方式一：一键生成（推荐新手）**

```bash
# 1️⃣ 准备内容文件
cp data/input/input.md.template data/input/input.md
cp data/input/character_mapping.json.template data/input/character_mapping.json

# 2️⃣ 准备故事内容（三选一）
# 📝 手动编辑: 编辑 data/input/input.md 添加故事内容
# 👥 配置角色: 编辑 data/input/character_mapping.json 设置角色映射
# 🚀 智能生成: 使用爆款文案生成工具自动创建内容
#   uv run main.py --viral
# 📖 故事生成: 使用故事生成工具直接生成故事并自动识别角色配置
#   uv run main.py --generate

# 3️⃣ 一键生成视频
uv run main.py --auto
```

#### 🎛️ **方式二：交互式生成（推荐进阶用户）**

```bash
# 启动交互式菜单
uv run main.py

# 菜单功能：
# 📊 1. 查看系统状态
# 🎬 2. 开始生成视频  
# 🔧 3. 配置参数
# 📁 4. 管理文件
# 🧹 5. 清理输出
```

#### 📊 **生成效果预览**

| 输入文本长度 | 预估生成时间 | 输出视频时长 | 文件大小 |
|-------------|-------------|-------------|----------|
| 500字 | 1-2分钟 | 30-60秒 | 10-20MB |
| 1000字 | 2-3分钟 | 1-2分钟 | 20-40MB |
| 2000字 | 4-6分钟 | 2-4分钟 | 40-80MB |
| 5000字+ | 10-15分钟 | 5-10分钟 | 100-200MB |

> **⚡ 性能优化**: 使用多线程并行处理，实际速度可能更快

#### 🎬 **爆款文案智能生成**

- 🎯 **主题定制**: 支持任意视频主题输入，AI智能理解创作意图
- 🎨 **风格多样**: 提供多种视频风格选择（温馨治愈、搞笑幽默、专业严肃等）
- 📊 **场景规划**: 智能规划视频场景数量和内容结构
- ✨ **提示词优化**: 自动生成高质量的Flux1图像生成提示词
- 🚀 **一键生成**: 从创意到成品，全流程自动化处理

```bash
# 启动爆款文案生成器
uv run main.py --viral

# 交互式输入：
# 🎯 视频主题（如：职场励志故事、美食制作教程）
# 🎨 风格提示（如：温馨治愈风格、搞笑幽默风格）
# 📊 场景数量（建议3-8个场景）
```

#### 🎛️ **方式二：交互式生成（推荐进阶用户）**

```bash
# 启动交互式菜单
uv run main.py --generate

# 菜单功能：
# 📊 1. 查看系统状态
# 🎬 2. 开始生成视频  
# 🔧 3. 配置参数
# 📁 4. 管理文件
# 🧹 5. 清理输出
```



#### 方式三：分步执行
```bash
# 1. 文本分析和分段
uv run python -m src.pipeline.text_analyzer

# 2. 生成图像
uv run python -m src.pipeline.image_generator

# 3. 语音合成
uv run python -m src.pipeline.voice_synthesizer

# 4. 视频合成
uv run python -m src.pipeline.video_composer
```



## 📚 完整文档

### 🎯 用户文档
- **[📖 用户指南](docs/user-guide.md)** - 完整的安装和使用教程
- **[🔧 环境配置](docs/environment-setup.md)** - 环境搭建和配置说明

### 🛠️ 开发文档  
- **[🏗️ 开发指南](docs/development-guide.md)** - 代码结构和开发说明
- **[📚 API参考](docs/api-reference.md)** - 配置参数和接口文档

## ⚙️ 配置说明

### 🔑 必需的API服务

#### 1. 大语言模型 (二选一)

**DeepSeek API (推荐)**
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-key
DEEPSEEK_MODEL=deepseek-chat
```

**OpenAI API**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-3.5-turbo-16k
```

#### 2. Azure 语音服务
```env
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=eastasia
AZURE_VOICE_NAME=zh-CN-YunxiNeural
```

#### 3. 图像生成服务 (二选一)

**LiblibAI F.1 模型 (推荐)**
```env
# LiblibAI 基础配置
LIBLIB_ACCESS_KEY=your-liblib-access-key
LIBLIB_SECRET_KEY=your-liblib-secret-key
LIBLIB_ENABLED=true

# F.1 模型默认参数
F1_DEFAULT_WIDTH=768
F1_DEFAULT_HEIGHT=1024
F1_DEFAULT_STEPS=20
F1_DEFAULT_CFG_SCALE=7.0
F1_DEFAULT_SAMPLER=15
F1_DEFAULT_CLIP_SKIP=2
F1_DEFAULT_TEMPLATE_UUID=6f7c4652458d4802969f8d089cf5b91f
```

**Stable Diffusion API**
```env
SD_API_URL=http://127.0.0.1:7860
SD_STEPS=30
SD_CFG_SCALE=7.5
SD_WIDTH=1360
SD_HEIGHT=1024
```

> **💡 提示**: F.1 模型提供更高质量的图像生成效果，支持更多自定义参数。详细配置请参考 [F.1 配置指南](docs/f1_configuration_guide.md)。

### 📝 输入文件配置

#### 角色映射配置

首次使用需要创建角色映射配置文件：

```bash
# 复制模板文件
cp data/input/character_mapping.json.template data/input/character_mapping.json
```

编辑 `character_mapping.json` 配置角色名替换和LoRA编号：

```json
[
  {
    "original_name": "小雨",
    "new_name": "红发女孩",
    "lora_id": "1"
  },
  {
    "original_name": "程宗扬",
    "new_name": "30岁黑发大叔",
    "lora_id": "2"
  }
]
```

#### 故事内容配置

```bash
# 复制模板文件
cp data/input/input.md.template data/input/input.md
```

然后编辑 `input.md` 文件，添加您的故事内容。角色名将根据上述配置自动替换。

### 🎛️ 高级配置

<details>
<summary>点击查看完整配置选项</summary>

```env
# 视频设置
VIDEO_FPS=24
VIDEO_ENABLE_EFFECT=true
VIDEO_EFFECT_TYPE=fade

# 字幕设置
SUBTITLE_FONTSIZE=48
SUBTITLE_FONTCOLOR=white
SUBTITLE_STROKE_COLOR=black
SUBTITLE_STROKE_WIDTH=2

# 性能设置
MAX_WORKERS_IMAGE=3
MAX_WORKERS_VIDEO=2
MAX_WORKERS_TRANSLATION=5
```
</details>

📖 **详细配置指南**: [环境配置文档](docs/environment-setup.md)

## 🏗️ 系统架构

<div align="center">

```mermaid
graph TB
    subgraph "📥 输入层"
        A[📝 文本内容]
        B[👥 角色配置]
        C[⚙️ 生成参数]
    end
    
    subgraph "🧠 AI处理层"
        D[🔍 智能文本分析]
        E[📊 内容理解与分段]
        F[🎨 AI图像生成]
        G[🎙️ 语音合成]
    end
    
    subgraph "🎬 合成层"
        H[🖼️ 图像处理]
        I[🎵 音频处理]
        J[📝 字幕生成]
        K[🎞️ 视频合成]
    end
    
    subgraph "📤 输出层"
        L[📹 高清视频]
        M[📊 处理报告]
        N[📁 资源文件]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    E --> G
    F --> H
    G --> I
    E --> J
    H --> K
    I --> K
    J --> K
    K --> L
    K --> M
    K --> N
    
    style A fill:#e1f5fe
    style L fill:#e8f5e8
    style D fill:#fff3e0
    style K fill:#f3e5f5
```

</div>

### 🔄 **处理流程详解**

1. **📝 智能解析** - AI深度理解文本内容，识别情节、角色、场景
2. **🎨 视觉生成** - 根据内容描述生成高质量配图，保持角色一致性
3. **🎙️ 语音合成** - 将文本转换为自然流畅的中文语音
4. **🎬 智能合成** - 自动同步图像、音频、字幕，生成专业视频
5. **📤 优化输出** - 多格式输出，支持不同平台需求

### 📁 项目结构

```
story-flow/
├── 📁 src/                           # 核心源代码
│   ├── 📁 pipeline/                  # 处理流水线模块
│   │   ├── 📄 text_analyzer.py       # 智能文本分析器
│   │   ├── 📄 image_generator.py      # 多平台图像生成器
│   │   ├── 📄 voice_synthesizer.py    # Azure TTS语音合成
│   │   └── 📄 video_composer.py       # MoviePy视频合成器
│   ├── 📄 config.py                  # 统一配置管理系统
│   ├── 📄 llm_client.py             # LLM客户端（OpenAI/DeepSeek）
│   ├── 📄 semantic_analyzer.py       # 语义分析器
│   ├── 📄 story_generator.py         # AI故事生成器
│   ├── 📄 viral_video_generator.py   # 病毒视频生成器
│   └── 📄 image_to_video.py          # 图像转视频模块
├── 📁 data/                          # 数据目录
│   ├── 📁 input/                     # 输入文件
│   │   ├── 📄 character_mapping.json.template  # 角色映射模板
│   │   └── 📄 input.md.template               # 故事内容模板
│   ├── 📁 output/                    # 输出文件目录
│   │   ├── 📁 txt/                   # 文本分析结果（JSON）
│   │   ├── 📁 images/                # AI生成图像
│   │   ├── 📁 voices/                # TTS语音文件
│   │   ├── 📁 videos/                # 最终视频输出
│   │   ├── 📁 video_clips/           # 视频片段
│   │   └── 📁 temp/                  # 临时文件
│   └── 📁 processed/                 # 处理后的CSV文件
├── 📁 tests/                         # 测试套件
│   ├── 📁 unit/                      # 单元测试
│   ├── 📁 integration/               # 集成测试
│   └── 📁 fixtures/                  # 测试数据
├── 📁 docs/                          # 项目文档
│   └── 📄 用户操作教程.md            # 详细使用教程
├── 📁 workflows/                     # ComfyUI工作流配置
├── 📄 main.py                        # 主程序入口
├── 📄 pyproject.toml                 # 项目配置和依赖
├── 📄 .env.example                   # 环境变量模板
├── 📄 setup.sh                      # 环境设置脚本
└── 📄 cleanup.sh                    # 清理脚本
```

## 🎯 使用场景

### 📚 内容创作
- **故事视频化** - 将小说、童话等文字内容转换为动画视频
- **自媒体制作** - 快速生成YouTube、B站等平台的视频内容
- **有声读物** - 结合图像和语音的沉浸式阅读体验

### 🎓 教育培训
- **课程制作** - 将教学材料转换为多媒体课程
- **知识可视化** - 抽象概念的图像化表达
- **语言学习** - 多语言内容的视听结合学习

### 💼 商业应用
- **产品演示** - 快速生成产品介绍和使用说明视频
- **营销内容** - 品牌故事和广告创意的视频化
- **培训材料** - 企业内训和操作指南视频

### 📱 社交媒体
- **短视频创作** - TikTok、抖音等平台的内容生成
- **故事分享** - 个人经历和创意故事的视频表达
- **病毒营销** - 利用AI生成吸引眼球的创意内容

### 🚀 创新应用
- **原型验证** - 快速测试视频创意和概念
- **个性化内容** - 基于用户偏好的定制化视频生成
- **多语言本地化** - 同一内容的多语言视频版本

## 🔧 技术栈

### 🧠 AI服务集成
- **大语言模型**: OpenAI GPT-4 / DeepSeek Chat
- **图像生成**: Stable Diffusion WebUI / LiblibAI / ComfyUI
- **语音合成**: Azure Cognitive Services TTS
- **语义分析**: 基于Transformer的文本理解

### 💻 核心技术
- **Python 3.10+**: 现代Python特性支持
- **异步编程**: asyncio高并发处理
- **并行计算**: ThreadPoolExecutor多线程优化
- **MoviePy**: 专业级视频处理引擎
- **PIL/Pillow**: 图像处理和特效

### 📦 依赖管理
- **uv**: 现代Python包管理器
- **pyproject.toml**: 标准化项目配置
- **python-dotenv**: 环境变量管理
- **pydantic**: 数据验证和配置管理

### 🔧 开发工具
- **pytest**: 完整的测试框架
- **tqdm**: 进度条和用户体验优化
- **pathlib**: 现代文件路径处理
- **logging**: 结构化日志系统

### 🌐 API集成
- **requests**: HTTP客户端
- **websocket-client**: WebSocket通信
- **azure-cognitiveservices-speech**: Azure TTS SDK
- **openai**: OpenAI官方SDK

<div align="center">

| 技术领域 | 核心技术 | 版本要求 | 说明 |
|---------|---------|---------|------|
| **🐍 核心语言** | Python | 3.10+ | 现代Python特性支持 |
| **📦 包管理** | uv | Latest | 极速依赖管理 |
| **🧠 AI大模型** | OpenAI/DeepSeek | API | 智能文本理解 |
| **🎨 图像生成** | Stable Diffusion/F.1 | API | 高质量AI绘图 |
| **🎙️ 语音合成** | Azure TTS | API | 真人级中文语音 |
| **🎬 视频处理** | MoviePy | 1.0+ | 专业视频编辑 |
| **📊 数据处理** | Pandas/NumPy | Latest | 高效数据操作 |
| **🖼️ 图像处理** | Pillow/OpenCV | Latest | 图像优化处理 |
| **🎵 音频处理** | Pydub/librosa | Latest | 音频编辑合成 |
| **🧪 测试框架** | pytest | Latest | 完整测试覆盖 |

</div>

### 🌟 **技术亮点**

- **⚡ 异步处理**: 基于asyncio的高并发架构
- **🔧 模块化设计**: 松耦合组件，易于扩展和维护  
- **🛡️ 错误恢复**: 完善的异常处理和自动重试机制
- **📊 性能监控**: 内置性能分析和资源使用统计
- **🔒 安全保障**: API密钥加密存储，安全的文件操作

## 🧹 项目维护

### 清理生成文件
```bash
# 运行清理脚本（交互式选择清理内容）
./cleanup.sh

# 清理脚本功能：
# - 清理生成的图片、音频文件
# - 清理临时文件和缓存
# - 整理输入文件到指定目录
# - 显示磁盘空间使用统计
# - 自动保留.gitkeep文件和videos目录中的重要文件
```

**🛡️ 智能清理保护：**
- 程序内置智能清理功能，在处理新章节前自动清理临时文件
- 自动保护重要文件：`.gitkeep`文件和`videos`目录中的视频文件
- 只清理必要的临时文件（图片、音频、CSV），避免误删重要内容
- 清理过程中如遇错误不会中断主流程，确保程序稳定运行

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 🐛 问题反馈

如果您遇到问题或有建议，请：
1. 查看 [常见问题](docs/FAQ.md)
2. 搜索现有的 [Issues](https://github.com/story-flow/story-flow/issues)
3. 创建新的 Issue 并提供详细信息

### 📝 开发计划

#### ✅ **已实现功能** (v0.1.0)

<table>
<tr>
<td width="50%">

**🎯 核心功能**
- [x] 📝 智能文本分析与分段
- [x] 🎨 AI图像生成 (SD/F.1)
- [x] 🎙️ 智能语音合成 (Azure TTS)
- [x] 🎬 自动视频合成
- [x] 👥 多角色管理系统
- [x] 🎬 爆款文案智能生成

</td>
<td width="50%">

**🔧 系统特性**
- [x] 📊 多格式数据支持
- [x] 🧪 完整测试覆盖 (90%+)
- [x] 🧹 智能清理系统
- [x] ⚡ 现代化包管理 (uv)
- [x] 🛡️ 错误恢复机制
- [x] 📈 性能监控统计

</td>
</tr>
</table>

#### 🚀 **开发路线图** (v0.2.0 - v1.0.0)

**🎬 下一版本 (v0.2.0) - 预计2024年Q2**
- [ ] 🎞️ 图生视频功能 - Runway/Pika AI集成
- [ ] 🎙️ GPT-SoVITS语音克隆 - 个性化语音定制
- [ ] 📱 剪映草稿生成 - 一键导入专业剪辑软件
- [ ] 🎵 AI音乐生成 - 智能背景音乐配置

**🌐 中期规划 (v0.5.0) - 预计2024年Q3**
- [ ] 🖥️ Web界面 - 可视化操作界面
- [ ] 🐳 Docker部署 - 一键容器化部署
- [ ] 🔄 实时预览 - 生成过程可视化
- [ ] 📊 数据分析 - 生成效果统计分析

#### 系统优化
- [ ] 🎤 更多语音服务商支持 - 扩展语音合成选择
- [ ] 🎞️ 视频模板系统 - 提供多样化视频风格模板
- [ ] 👀 实时预览功能 - 生成过程可视化预览
- [ ] 🌐 Web界面开发 - 提供友好的网页操作界面
- [ ] 🐳 Docker容器化部署 - 简化部署和分发流程
- [ ] ⚡ 性能优化 - 多线程处理和缓存机制
- [ ] 🔄 增量更新 - 支持部分内容更新而非全量重新生成

**🌟 长期愿景 (v1.0.0+) - 2024年Q4及以后**
- [ ] 🤖 AI Agent系统 - 全自动内容创作代理
- [ ] 🔥 热点内容转化 - 自动抓取网络热点生成视频
- [ ] 🎯 个性化推荐 - 基于用户偏好的智能推荐
- [ ] 🌍 多语言支持 - 全球化内容创作平台
- [ ] 🏢 企业级功能 - 团队协作、权限管理、API服务

> **📈 发展目标**: 成为全球领先的AI视频生成平台，服务百万内容创作者

## 📞 联系方式

如果您在使用过程中遇到问题或有任何建议，欢迎通过以下方式联系我们：

### 🐛 问题反馈
- **GitHub Issues**: [提交Bug报告或功能请求](https://github.com/story-flow/story-flow/issues)
- **问题模板**: 请使用相应的Issue模板，提供详细的问题描述和复现步骤

### 💬 交流讨论
- **GitHub Discussions**: [参与项目讨论](https://github.com/story-flow/story-flow/discussions)
- **功能建议**: 在Discussions中分享您的想法和建议
- **使用经验**: 分享您的使用心得和最佳实践

### 📧 直接联系
- **项目维护者**: [dasenrising@gmail.com](mailto:dasenrising@gmail.com)
- **技术支持**: [dasenrising@gmail.com](mailto:dasenrising@gmail.com)
- **商务合作**: [dasenrising@gmail.com](mailto:dasenrising@gmail.com)

### 🌐 社交媒体
- **微信群**: 扫描下方二维码加入交流群

<div align="center">
  <img src="docs/images/WechatIMG1392.png" alt="微信群二维码" width="200"/>
  <p><em>🎯 扫描加入Story Flow创作者社群</em></p>
  <p><strong>💬 1000+创作者 • 📚 经验分享 • 🔧 技术支持 • 🎁 独家资源</strong></p>
</div>

---

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 详情请查看 LICENSE 文件。

## 🙏 致谢

感谢以下开源项目和服务：
- [OpenAI](https://openai.com/) - GPT模型服务
- [DeepSeek](https://www.deepseek.com/) - 高性价比LLM服务
- [Azure Cognitive Services](https://azure.microsoft.com/services/cognitive-services/) - 语音合成服务
- [Stable Diffusion](https://stability.ai/) - AI图像生成
- [MoviePy](https://zulko.github.io/moviepy/) - 视频处理库
- [uv](https://github.com/astral-sh/uv) - 现代化Python包管理器

---

<div align="center">

## 🌟 **支持项目发展**

如果 Story Flow 帮助您创作出精彩内容，请考虑支持我们：

[![GitHub stars](https://img.shields.io/github/stars/story-flow/story-flow?style=social)](https://github.com/story-flow/story-flow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/story-flow/story-flow?style=social)](https://github.com/story-flow/story-flow/network)
[![GitHub watchers](https://img.shields.io/github/watchers/story-flow/story-flow?style=social)](https://github.com/story-flow/story-flow/watchers)

**⭐ 点个Star** • **🔄 分享给朋友** • **💬 参与讨论** • **🐛 反馈问题**

---

### 📚 **快速导航**

[🏠 项目主页](https://github.com/story-flow/story-flow) • [📖 使用文档](docs/) • [🎬 视频教程](#) • [💬 社群讨论](https://github.com/story-flow/story-flow/discussions)

[🐛 问题反馈](https://github.com/story-flow/story-flow/issues) • [💡 功能建议](https://github.com/story-flow/story-flow/discussions/categories/ideas) • [🤝 参与贡献](CONTRIBUTING.md) • [📄 更新日志](CHANGELOG.md)

---

**💝 让每个人都能成为优秀的内容创作者**

*Story Flow - 用AI点亮创作之光* ✨

</div>
