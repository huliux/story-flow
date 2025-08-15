# 📚 文本到视频生成系统 - 文档中心

欢迎来到文本到视频生成系统的文档中心！这里包含了项目的完整使用指南和技术文档。

## 📖 文档导航

### 🚀 快速入门
- **[用户指南](user-guide.md)** - 完整的安装和使用教程
- **[环境配置](environment-setup.md)** - 环境搭建和配置说明

### 🔧 开发指南  
- **[开发指南](development-guide.md)** - 代码结构和开发说明
- **[API参考](api-reference.md)** - 配置参数和接口文档

### 📋 项目历史
- **[更新日志](CHANGELOG.md)** - 版本更新记录
- **[项目历程](project-history.md)** - 重构和改进历程

## 🏗️ 项目架构

```
文本到视频生成系统
├── 📝 文本处理 (Step 1) - AI分析和翻译
├── 🎨 图像生成 (Step 2) - Stable Diffusion + LoRA
├── 🎙️ 语音合成 (Step 3) - Azure TTS
└── 🎬 视频合成 (Step 4) - MoviePy
```

## ⚡ 快速开始

1. **环境准备**
   ```bash
   ./activate_env.sh
   python setup_env.py
   ```

2. **配置API密钥**
   ```bash
   cp env.example .env
   # 编辑 .env 文件，填入API密钥
   ```

3. **运行系统**
   ```bash
   python Auto.py  # 全自动模式
   ```

## 💡 主要特性

- 🧠 **多LLM支持**: OpenAI GPT / DeepSeek
- 🎨 **高质量图像**: Stable Diffusion + LoRA模型
- 🎙️ **真实语音**: Azure TTS 中文语音
- 🎬 **专业视频**: 支持字幕、特效、高清输出
- 🔧 **高度配置**: 统一配置管理
- 📱 **交互友好**: 逐步引导操作

## 🆘 获取帮助

- 📖 查看 [用户指南](user-guide.md) 了解详细用法
- 🔧 查看 [开发指南](development-guide.md) 了解技术细节
- 🐛 遇到问题请查看各文档的故障排除部分

---

**最后更新**: 2025年1月
**维护状态**: 🟢 积极维护
