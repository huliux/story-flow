#!/bin/bash
# 文本到视频生成系统 - 环境激活脚本

echo "🚀 激活文本到视频生成系统环境..."

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 python setup_env.py"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  配置文件 .env 不存在，正在创建..."
    cp env.example .env
    echo "📝 请编辑 .env 文件，填入您的API密钥"
fi

echo "✅ 环境已激活"
echo "📍 当前目录: $(pwd)"
echo "🐍 Python版本: $(python --version)"
echo ""
echo "🎯 快速开始:"
echo "   python setup_env.py    # 验证环境配置"
echo "   python test_llm.py     # 测试LLM服务"
echo "   python Auto.py         # 全自动模式"
echo "   python cleanup.py      # 清理生成文件"
echo ""
echo "📚 查看文档: docs/README.md"
echo ""
echo "💡 使用 'deactivate' 命令退出虚拟环境"

# 保持shell环境激活
exec bash
