# 📖 用户使用指南

## 🎯 系统概览

文本到视频生成系统是一个端到端的AI内容创作工具，能够将小说文本自动转换为包含图像、语音和字幕的视频。

### 核心功能
- 📝 **智能文本分析**: 使用AI提取关键词、翻译文本
- 🎨 **自动图像生成**: 基于Stable Diffusion生成高质量场景图
- 🎙️ **语音合成**: Azure TTS生成自然中文配音
- 🎬 **视频制作**: 自动合成图像、音频、字幕为完整视频

## 🚀 快速开始

### 第一步：环境准备

1. **激活虚拟环境**
   ```bash
   ./activate_env.sh
   ```

2. **验证环境**
   ```bash
   python setup_env.py
   ```

### 第二步：配置服务

1. **复制配置模板**
   ```bash
   cp env.example .env
   ```

2. **编辑配置文件**
   ```bash
   nano .env  # 或使用其他编辑器
   ```

3. **必需配置项**
   ```env
   # LLM服务商选择 (openai 或 deepseek)
   LLM_PROVIDER=deepseek
   
   # DeepSeek API密钥 (推荐，性价比高)
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   
   # Azure语音服务
   AZURE_SPEECH_KEY=your_azure_speech_key
   AZURE_SPEECH_REGION=eastasia
   
   # Stable Diffusion API地址
   SD_API_URL=http://your-stable-diffusion-server:7860
   ```

4. **测试服务连接**
   ```bash
   python test_llm.py  # 测试LLM服务
   ```

### 第三步：准备文本

1. **准备小说文本**
   - 将文本保存为 `input.txt`
   - 确保章节标题格式为 "第X章"
   - 建议单次处理1000-3000字

2. **文本格式示例**
   ```
   第一章 初遇
   
   在一个风和日丽的下午，李明走在熟悉的小径上。阳光透过茂密的树叶洒下斑驳的光影，鸟儿在枝头欢快地歌唱。
   
   突然，他听到了一阵悠扬的琴声从不远处传来...
   ```

## 🎮 使用方式

### 方式一：全自动模式（推荐）

```bash
python Auto.py
```

系统将自动执行所有步骤，只在需要时提示用户交互。

### 方式二：分步执行

```bash
# Step 0: 分割文本
python step0_split_txt_to_docx.py

# Step 1: AI文本分析 (⚠️ 需要交互)
python step1_extract_keywords-rolev1.1.py

# Step 2: 生成图像
python step2_txt_to_image-cloud-addlorav1.1.py

# Step 3: 合成语音
python step3_txt_to_voice-mstts-repairv1.0.py

# Step 4: 生成视频
python step4_output_video.py
```

## 🔄 Step 1 交互指南

Step 1 是唯一需要用户交互的步骤，用于优化文本质量。

### 交互流程

1. **系统提示**
   ```
   请输入要被替换的文字和需要绑定的数字（格式："原文 新文 数字"，n/N结束）:
   ```

2. **输入格式**: `原文 新文 数字`

3. **实用示例**
   ```
   他 李明 1        # 将"他"替换为"李明"，角色编号1
   她 小红 2        # 将"她"替换为"小红"，角色编号2  
   那把剑 倚天剑 10   # 将"那把剑"替换为"倚天剑"，物品编号10
   那个地方 森林 20   # 将"那个地方"替换为"森林"，场景编号20
   n               # 输入n结束替换
   ```

4. **编号建议**
   - 人物角色: 1-10
   - 物品道具: 11-20  
   - 场景环境: 21-30

### 交互技巧

✅ **推荐做法**:
- 替换模糊代词为具体姓名
- 为重要角色分配固定编号
- 统一物品和场景的命名
- 保持语句自然通顺

❌ **避免做法**:
- 过度替换导致语句不自然
- 使用相同编号给不同角色
- 替换后语法错误

## 📊 输出文件说明

### Step 1 输出
- `txt/txt.xlsx`: 包含原文、翻译、提示词等5列数据

### Step 2 输出  
- `image/`: 生成的场景图像文件

### Step 3 输出
- `voice/`: 合成的语音文件

### Step 4 输出
- `video/`: 最终生成的视频文件

## 🛠️ 高级配置

### LLM服务商切换

**使用DeepSeek（推荐）**:
```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_key
DEEPSEEK_MODEL=deepseek-chat
```

**使用OpenAI**:
```env
LLM_PROVIDER=openai  
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-3.5-turbo-16k
```

### 图像生成配置

```env
# Stable Diffusion设置
SD_STEPS=30
SD_CFG_SCALE=7.5
SD_WIDTH=1360
SD_HEIGHT=1024

# LoRA模型选择
SD_LORA_MODELS=优秀偶像男01,富家男02,古惑男01
```

### 语音设置

```env
# Azure TTS配置
AZURE_VOICE_NAME=zh-CN-YunxiNeural  # 成熟男声
AZURE_VOICE_STYLE=calm               # 冷静风格
AZURE_VOICE_RATE=+40%               # 语速
AZURE_VOICE_VOLUME=+30%             # 音量
```

### 视频设置

```env
# 视频参数
VIDEO_FPS=30
VIDEO_SUBTITLE=true
VIDEO_EFFECTS=true
SUBTITLE_FONT=SimHei
SUBTITLE_SIZE=36
```

## 🚨 故障排除

### 常见问题

**1. API密钥错误**
```bash
错误: 401 - Incorrect API key provided
解决: 检查.env文件中的API密钥是否正确
```

**2. spaCy模型缺失**
```bash
错误: OSError: [E050] Can't find model 'zh_core_web_sm'
解决: python -m spacy download zh_core_web_sm
```

**3. Stable Diffusion连接失败**
```bash
错误: Connection refused
解决: 检查SD_API_URL设置和服务状态
```

**4. Azure TTS错误**
```bash
错误: Unauthorized
解决: 检查AZURE_SPEECH_KEY和AZURE_SPEECH_REGION
```

### 性能优化

**1. 提高处理速度**
- 调整 `MAX_WORKERS_TRANSLATION=8`
- 减少 `SD_STEPS=20`
- 使用更快的LLM模型

**2. 降低成本**
- 使用DeepSeek替代OpenAI
- 调整 `LLM_MAX_TOKENS=300`
- 批量处理文本

**3. 提高质量**
- 增加 `SD_STEPS=50`
- 使用高质量LoRA模型
- 仔细进行Step 1文本替换

## 🔧 工具命令

### 环境管理
```bash
./activate_env.sh     # 激活环境
python setup_env.py   # 验证配置
python test_llm.py    # 测试LLM服务
```

### 项目维护
```bash
python cleanup.py     # 清理生成文件
python text_optimizer.py  # 文本优化GUI工具
```

## 💡 最佳实践

### 文本准备
1. 控制单次处理的文本长度（1000-3000字）
2. 确保文本格式清晰，章节分明
3. 提前规划主要角色和场景

### 交互优化
1. 为主要角色建立角色档案
2. 保持命名的一致性
3. 测试少量文本后再批量处理

### 质量控制
1. 分步骤验证每个环节的输出
2. 根据需要调整配置参数
3. 保存成功的配置模板

---

**需要更多帮助？** 查看 [开发指南](development-guide.md) 了解技术细节，或查看 [API参考](api-reference.md) 了解配置选项。
