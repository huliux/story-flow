#!/bin/bash
# -*- coding: utf-8 -*-
# Story Flow 项目清理工具
# 用于清理生成的文件和临时文件

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_clean() {
    echo -e "${PURPLE}🧹 $1${NC}"
}

# 格式化文件大小
format_size() {
    local size=$1
    if [[ $size -lt 1024 ]]; then
        echo "${size}B"
    elif [[ $size -lt 1048576 ]]; then
        echo "$((size / 1024))KB"
    elif [[ $size -lt 1073741824 ]]; then
        echo "$((size / 1048576))MB"
    else
        echo "$((size / 1073741824))GB"
    fi
}

# 计算目录大小（排除.gitkeep文件）
get_directory_size() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        # 计算所有文件大小，但排除.gitkeep文件
        local total_size=0
        while IFS= read -r -d '' file; do
            if [[ "$(basename "$file")" != ".gitkeep" ]]; then
                local file_size=$(stat -f%z "$file" 2>/dev/null || echo "0")
                ((total_size += file_size))
            fi
        done < <(find "$dir" -type f -print0 2>/dev/null)
        echo "$total_size"
    else
        echo "0"
    fi
}

# 计算目录中的文件数量（排除.gitkeep文件）
get_file_count() {
    local dir="$1"
    if [[ -d "$dir" ]]; then
        find "$dir" -type f ! -name ".gitkeep" 2>/dev/null | wc -l || echo "0"
    else
        echo "0"
    fi
}

# 清理指定目录
clean_directory() {
    local directory="$1"
    local description="$2"
    local confirm="${3:-true}"
    
    if [[ ! -d "$directory" ]]; then
        echo "📁 $description: 目录不存在，跳过"
        return 0
    fi
    
    # 计算大小和文件数量
    local size=$(get_directory_size "$directory")
    local file_count=$(get_file_count "$directory")
    
    if [[ $file_count -eq 0 ]]; then
        echo "📁 $description: 目录为空，跳过"
        return 0
    fi
    
    echo "📁 $description: $file_count 个文件, $(format_size $size)"
    
    if [[ "$confirm" == "true" ]]; then
        read -p "确认清理 $description? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "跳过清理 $description"
            return 0
        fi
    fi
    
    # 清理目录内容（保留目录结构）
    local cleaned_files=0
    local errors=0
    
    if [[ -d "$directory" ]]; then
        # 删除文件（但保留目录结构和.gitkeep文件）
        while IFS= read -r -d '' file; do
            # 跳过.gitkeep文件
            if [[ "$(basename "$file")" == ".gitkeep" ]]; then
                continue
            fi
            if rm "$file" 2>/dev/null; then
                ((cleaned_files++))
            else
                ((errors++))
            fi
        done < <(find "$directory" -type f -print0 2>/dev/null)
        
        # 删除空的子目录（但保留主目录）
        while IFS= read -r -d '' dir; do
            # 跳过主目录本身
            if [[ "$dir" != "$directory" ]]; then
                rmdir "$dir" 2>/dev/null || true
            fi
        done < <(find "$directory" -type d -empty -print0 2>/dev/null | sort -r)
        
        if [[ $errors -eq 0 ]]; then
            print_success "已清理 $description (删除 $cleaned_files 个文件，保留目录结构)"
        else
            print_warning "部分清理 $description (删除 $cleaned_files 个文件, $errors 个错误)"
        fi
        
        return 0
    else
        print_error "清理目录失败: $directory"
        return 1
    fi
}

# 清理临时文件
clean_temp_files() {
    print_clean "清理临时文件..."
    
    local temp_patterns=(
        "**/.DS_Store"
        "**/Thumbs.db"
        "**/*~"
        "**/~$*.xlsx"
        "**/~$*.docx"
        "**/*.tmp"
        "**/*.temp"
        "**/*.bak"
        "**/*.backup"
        "**/__pycache__"
        "**/*.pyc"
        "**/*.pyo"
        "**/.pytest_cache"
    )
    
    local total_freed=0
    local files_deleted=0
    local dirs_deleted=0
    local errors=0
    
    # 使用find命令查找和删除文件
    local find_patterns=(
        "-name '.DS_Store'"
        "-name 'Thumbs.db'"
        "-name '*~'"
        "-name '~$*.xlsx'"
        "-name '~$*.docx'"
        "-name '*.tmp'"
        "-name '*.temp'"
        "-name '*.bak'"
        "-name '*.backup'"
        "-name '*.pyc'"
        "-name '*.pyo'"
    )
    
    for pattern in "${find_patterns[@]}"; do
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                local size=$(stat -f%z "$file" 2>/dev/null || echo "0")
                if rm "$file" 2>/dev/null; then
                    echo "  删除文件: $file"
                    ((files_deleted++))
                    ((total_freed += size))
                else
                    echo "  ⚠️  无法删除 $file"
                    ((errors++))
                fi
            fi
        done < <(find . $pattern -type f -print0 2>/dev/null)
    done
    
    # 删除__pycache__和.pytest_cache目录
    local dir_patterns=(
        "-name '__pycache__'"
        "-name '.pytest_cache'"
    )
    
    for pattern in "${dir_patterns[@]}"; do
        while IFS= read -r -d '' dir; do
            if [[ -d "$dir" ]]; then
                local size=$(get_directory_size "$dir")
                if rm -rf "$dir" 2>/dev/null; then
                    echo "  删除目录: $dir"
                    ((dirs_deleted++))
                    ((total_freed += size))
                else
                    echo "  ⚠️  无法删除 $dir"
                    ((errors++))
                fi
            fi
        done < <(find . $pattern -type d -print0 2>/dev/null)
    done
    
    if [[ $total_freed -gt 0 ]]; then
        print_success "临时文件清理完成: 删除 $files_deleted 个文件, $dirs_deleted 个目录"
        echo "   释放空间: $(format_size $total_freed)"
        if [[ $errors -gt 0 ]]; then
            echo "   $errors 个项目清理失败"
        fi
    else
        print_success "没有找到临时文件"
    fi
    
    return $total_freed
}

# 移动输入文件
move_input_files() {
    print_info "整理输入文件..."
    
    local input_patterns=("*.md" "*.txt" "*.docx" "*.pdf")
    local input_dir="data/input"
    local exclude_files=("README.md" "CHANGELOG.md" "LICENSE.md" "CONTRIBUTING.md")
    
    # 确保input目录存在
    mkdir -p "$input_dir" 2>/dev/null || {
        print_error "无法创建input目录"
        return 1
    }
    
    local moved_count=0
    local errors=0
    
    for pattern in "${input_patterns[@]}"; do
        for file in $pattern; do
            # 检查文件是否存在且在根目录
            if [[ -f "$file" && "$(dirname "$file")" == "." ]]; then
                # 检查是否为需要排除的文件
                local should_exclude=false
                for exclude_file in "${exclude_files[@]}"; do
                    if [[ "$(basename "$file")" == "$exclude_file" ]]; then
                        should_exclude=true
                        break
                    fi
                done
                
                if [[ "$should_exclude" == "true" ]]; then
                    continue
                fi
                
                local target_path="$input_dir/$(basename "$file")"
                
                if [[ -f "$target_path" ]]; then
                    print_warning "目标文件已存在: $target_path"
                    read -p "覆盖 $(basename "$file")？(y/n): " -n 1 -r
                    echo
                    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                        continue
                    fi
                fi
                
                if mv "$file" "$target_path" 2>/dev/null; then
                    echo "📦 移动文件: $file -> $target_path"
                    ((moved_count++))
                else
                    print_error "移动失败 $file"
                    ((errors++))
                fi
            fi
        done
    done
    
    if [[ $moved_count -gt 0 ]]; then
        print_success "移动了 $moved_count 个输入文件到input目录"
        if [[ $errors -gt 0 ]]; then
            echo "   $errors 个文件移动失败"
        fi
    elif [[ $errors -gt 0 ]]; then
        print_warning "$errors 个文件移动失败"
    fi
}

# 交互式清理
interactive_cleanup() {
    local directories=(
        "data/output/images:生成的图片文件"
        "data/output/audio:生成的语音文件"
        "data/output/videos:生成的视频文件"
        "data/output/processed:处理后的文件"
        "data/temp:临时文件"
    )
    
    for dir_info in "${directories[@]}"; do
        local dir="${dir_info%%:*}"
        local desc="${dir_info##*:}"
        clean_directory "$dir" "$desc" true
    done
}

# 完全清理
full_cleanup() {
    echo "确认清理所有生成文件？这将删除所有输出目录中的内容。"
    read -p "请输入 'yes' 确认: " -r < /dev/tty
    if [[ $REPLY != "yes" ]]; then
        echo "取消清理"
        return 0
    fi
    
    local directories=(
        "data/output/images:生成的图片文件"
        "data/output/audio:生成的语音文件"
        "data/output/videos:生成的视频文件"
        "data/output/processed:处理后的文件"
        "data/temp:临时文件"
    )
    
    for dir_info in "${directories[@]}"; do
        local dir="${dir_info%%:*}"
        local desc="${dir_info##*:}"
        clean_directory "$dir" "$desc" false
    done
}

# 仅清理临时文件
temp_cleanup() {
    clean_directory "data/temp" "临时文件" false
    clean_temp_files
}

# 显示文件统计
show_statistics() {
    print_info "分析项目文件..."
    
    local directories=(
        "data/output/images:生成的图片文件"
        "data/output/audio:生成的语音文件"
        "data/output/videos:生成的视频文件"
        "data/output/processed:处理后的文件"
        "data/temp:临时文件"
    )
    
    echo
    echo "📊 文件统计:"
    local total_size=0
    local total_files=0
    
    for dir_info in "${directories[@]}"; do
        local dir="${dir_info%%:*}"
        local desc="${dir_info##*:}"
        
        local size=$(get_directory_size "$dir")
        local file_count=$(get_file_count "$dir")
        
        ((total_size += size))
        ((total_files += file_count))
        
        echo "  $desc: $file_count 个文件, $(format_size $size)"
    done
    
    echo
    echo "📈 总计: $total_files 个文件, $(format_size $total_size)"
    
    if [[ $total_files -eq 0 ]]; then
        print_success "没有需要清理的生成文件"
        return 1
    else
        print_warning "将释放 $(format_size $total_size) 的磁盘空间"
        return 0
    fi
}

# 主函数
main() {
    print_info "Story Flow 项目清理工具"
    echo "========================================"
    
    # 检查是否在项目根目录
    if [[ ! -f "pyproject.toml" ]]; then
        print_warning "警告: 未在项目根目录中运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "👋 已取消"
            return 0
        fi
    fi
    
    # 显示文件统计
    if ! show_statistics; then
        # 如果没有文件需要清理，仍然提供临时文件清理选项
        echo
        echo "请选择清理模式:"
        echo "1. 仅清理临时文件"
        echo "0. 退出"
        
        read -p "请输入选择 (0-1): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                temp_cleanup
                ;;
            0)
                echo "👋 再见!"
                return 0
                ;;
            *)
                print_error "无效选择"
                return 1
                ;;
        esac
    else
        # 显示清理选项
        echo
        echo "请选择清理模式:"
        echo "1. 交互式清理 (推荐)"
        echo "2. 完全清理 (删除所有生成文件)"
        echo "3. 仅清理临时文件"
        echo "0. 退出"
        
        read -p "请输入选择 (0-3): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                interactive_cleanup
                ;;
            2)
                full_cleanup
                ;;
            3)
                temp_cleanup
                ;;
            0)
                echo "👋 再见!"
                return 0
                ;;
            *)
                print_error "无效选择"
                return 1
                ;;
        esac
    fi
    
    # 清理临时文件
    echo
    clean_temp_files
    
    # 整理输入文件
    echo
    move_input_files
    
    echo
    print_success "清理完成!"
}

# 错误处理
trap 'echo; print_warning "用户中断操作"; exit 130' INT
trap 'print_error "清理过程中发生错误"; exit 1' ERR

# 运行主函数
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi