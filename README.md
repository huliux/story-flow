# 📺 文本到视频生成系统

一个强大的AI驱动文本到视频生成系统，能够将小说文本自动转换为包含图像、语音和字幕的完整视频。

## ✨ 核心特性

🧠 **多LLM支持** - OpenAI GPT / DeepSeek (性价比更高)  
🎨 **高质量图像** - Stable Diffusion + LoRA模型  
🎙️ **真实语音** - Azure TTS 中文语音合成  
🎬 **专业视频** - 自动字幕、特效、高清输出  
🔧 **高度配置** - 统一配置管理，灵活调整  
📱 **交互友好** - 逐步引导，操作简单  

## 🚀 快速开始

### 1. 环境准备
```bash
# 激活环境（自动安装依赖）
./activate_env.sh

# 验证环境
python setup_env.py
```

### 2. 配置服务
```bash
# 复制配置模板
cp env.example .env

# 编辑配置文件，填入API密钥
nano .env
```

### 3. 开始使用
```bash
# 准备文本文件 input.txt
echo "第一章 初遇..." > input.txt

# 全自动生成
python Auto.py
```

## 📚 完整文档

**完整文档导航**: [docs/README.md](docs/README.md)

### 🎯 用户文档
- **[📖 用户指南](docs/user-guide.md)** - 完整的安装和使用教程
- **[🔧 环境配置](docs/environment-setup.md)** - 环境搭建和配置说明

### 🛠️ 开发文档  
- **[🏗️ 开发指南](docs/development-guide.md)** - 代码结构和开发说明
- **[📚 API参考](docs/api-reference.md)** - 配置参数和接口文档

## 🔧 核心配置

```env
# LLM服务商选择
LLM_PROVIDER=deepseek  # 推荐：性价比高
DEEPSEEK_API_KEY=sk-your-key

# Azure语音服务
AZURE_SPEECH_KEY=your-key
AZURE_SPEECH_REGION=eastasia

# Stable Diffusion API  
SD_API_URL=http://your-server:7860
```

详细配置：[环境配置指南](docs/environment-setup.md)

## 🏗️ 系统架构

```
📝 文本输入 → 🤖 AI分析翻译 → �� 图像生成 → 🎙️ 语音合成 → 🎬 视频合成
```

---

**🌟 如果这个项目对您有帮助，请给我们一个Star！**

**📚 完整使用教程请查看：[docs/README.md](docs/README.md)**
