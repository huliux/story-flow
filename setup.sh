#!/bin/bash
# -*- coding: utf-8 -*-
# Story Flow 环境设置脚本
# 用于初始化项目环境，创建必要的目录和配置文件

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}🚀 $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查uv是否安装
check_uv_installation() {
    if command_exists uv; then
        local uv_version=$(uv --version 2>/dev/null || echo "unknown")
        print_success "uv已安装: $uv_version"
        return 0
    else
        print_error "uv未安装"
        echo "请安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        return 1
    fi
}

# 检查虚拟环境
check_virtual_environment() {
    if [[ -n "$VIRTUAL_ENV" ]] || [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        print_success "检测到虚拟环境"
        return 0
    else
        print_warning "未检测到虚拟环境"
        echo "建议使用虚拟环境: uv venv && source .venv/bin/activate"
        return 1
    fi
}

# 创建.env文件
create_env_file() {
    local env_example=".env.example"
    local env_file=".env"
    
    if [[ -f "$env_example" ]]; then
        if [[ -f "$env_file" ]]; then
            print_warning ".env文件已存在"
            read -p "是否覆盖现有的.env文件? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "跳过.env文件创建"
                return 0
            fi
        fi
        
        cp "$env_example" "$env_file"
        print_success ".env文件已创建"
        print_info "请编辑 .env 文件配置您的API密钥"
    else
        print_error "未找到 .env.example 文件"
        return 1
    fi
}

# 创建必要的目录
setup_directories() {
    local directories=(
        "data/input"
        "data/output/images"
        "data/output/audio"
        "data/output/videos"
        "data/temp"
    )
    
    for dir in "${directories[@]}"; do
        if mkdir -p "$dir" 2>/dev/null; then
            print_success "目录已创建: $dir"
        else
            print_error "无法创建目录: $dir"
            return 1
        fi
    done
}

# 检查Python依赖
check_dependencies() {
    echo
    print_info "检查Python依赖..."
    
    # 首先检查uv是否安装
    if ! check_uv_installation; then
        return 1
    fi
    
    # 检查pyproject.toml是否存在
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "未找到 pyproject.toml 文件"
        return 1
    fi
    
    # 尝试同步依赖
    if uv sync --quiet 2>/dev/null; then
        print_success "依赖同步成功"
    else
        print_error "依赖同步失败"
        echo "请手动运行: uv sync"
        return 1
    fi
    
    # 检查关键包的导入
    local key_packages=(
        "dotenv:python-dotenv"
        "openai:openai"
        "azure.cognitiveservices.speech:azure-cognitiveservices-speech"
        "requests:requests"
        "spacy:spacy"
        "tqdm:tqdm"
        "moviepy:moviepy"
        "PIL:pillow"
        "numpy:numpy"
        "pandas:pandas"
    )
    
    local missing_packages=()
    
    for package_info in "${key_packages[@]}"; do
        local import_name="${package_info%%:*}"
        local package_name="${package_info##*:}"
        
        if uv run python -c "import $import_name" 2>/dev/null; then
            print_success "$package_name"
        else
            print_error "$package_name (未安装)"
            missing_packages+=("$package_name")
        fi
    done
    
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        echo
        print_error "缺少依赖: ${missing_packages[*]}"
        echo "请运行: uv sync"
        echo "或单独安装: uv add ${missing_packages[*]}"
        return 1
    fi
    
    print_success "所有依赖已安装"
    return 0
}

# 检查spaCy模型
check_spacy_model() {
    echo
    print_info "检查spaCy中文模型..."
    
    if uv run python -c "import spacy; nlp = spacy.load('zh_core_web_sm')" 2>/dev/null; then
        print_success "spaCy中文模型已安装"
    else
        print_warning "spaCy中文模型未安装"
        echo "正在安装spaCy中文模型..."
        # 使用uv pip install安装spacy模型包
        if uv pip install https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.7.0/zh_core_web_sm-3.7.0-py3-none-any.whl 2>/dev/null; then
            print_success "spaCy中文模型安装成功"
        else
            print_error "spaCy中文模型安装失败"
            echo "请手动安装: uv pip install https://github.com/explosion/spacy-models/releases/download/zh_core_web_sm-3.7.0/zh_core_web_sm-3.7.0-py3-none-any.whl"
            return 1
        fi
    fi
}

# 验证配置
validate_config() {
    echo
    print_info "验证配置..."
    
    if [[ ! -f ".env" ]]; then
        print_error "请先创建并配置.env文件"
        return 1
    fi
    
    # 检查关键配置项
    local required_vars=("LLM_PROVIDER" "OPENAI_API_KEY" "AZURE_SPEECH_KEY")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" ".env" 2>/dev/null || grep -q "^$var=$" ".env" 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_warning "以下配置项需要设置: ${missing_vars[*]}"
        print_info "请编辑 .env 文件配置这些值"
    else
        print_success "配置验证通过"
    fi
}

# 主函数
main() {
    print_info "Story Flow 环境设置"
    echo "=============================="
    
    # 检查是否在项目根目录
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "请在项目根目录中运行此脚本"
        exit 1
    fi
    
    # 检查虚拟环境
    check_virtual_environment
    
    # 创建.env文件
    echo
    create_env_file
    
    # 创建目录
    echo
    print_info "创建项目目录..."
    setup_directories
    
    # 检查依赖
    if ! check_dependencies; then
        echo
        print_error "环境设置失败"
        echo
        echo "建议操作:"
        echo "1. 确保已安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "2. 同步依赖: uv sync"
        echo "3. 重新运行此脚本: ./setup.sh"
        exit 1
    fi
    
    # 检查spaCy模型
    check_spacy_model
    
    # 验证配置
    validate_config
    
    echo
    print_success "环境设置完成!"
    echo
    echo "下一步:"
    echo "1. 编辑 .env 文件，配置API密钥"
    echo "2. 运行 uv run scripts/test_llm.py 测试配置"
    echo "3. 开始使用: uv run src/main.py"
    
    return 0
}

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi