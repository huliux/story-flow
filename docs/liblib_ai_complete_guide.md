# LiblibAI 图像生成完整指南

本文档是 LiblibAI 图像生成服务的完整使用指南，整合了 F.1 模型配置、批量生成、参数说明等所有功能。

## 目录

1. [快速开始](#快速开始)
2. [环境配置](#环境配置)
3. [F.1 模型使用](#f1-模型使用)
4. [批量图片生成](#批量图片生成)
5. [参数详细说明](#参数详细说明)
6. [高级功能](#高级功能)
7. [故障排除](#故障排除)
8. [最佳实践](#最佳实践)

## 快速开始

### 基本使用

```bash
# 单张图片生成
uv run src/liblib_standalone.py --prompt "一只可爱的小猫" --use-f1

# 从JSON文件批量生成
uv run src/liblib_standalone.py --json-file data/txt.json --output-dir ./output --use-f1

# 图生图
uv run src/liblib_standalone.py --prompt "改进这张图片" --input-image input.jpg --use-f1
```

### 主要特性

- ✅ **F.1 模型支持**：使用最新的 F.1 文生图模型
- ✅ **批量生成**：支持并发和顺序两种模式
- ✅ **智能提示词提取**：自动从JSON文件提取"故事板提示词"
- ✅ **LoRA 模型支持**：自动配置和自定义LoRA模型
- ✅ **完整参数配置**：通过环境变量灵活配置所有参数
- ✅ **错误处理**：自动重试和详细日志

## 环境配置

### 1. API 密钥配置

在 `.env` 文件中配置 LiblibAI API 密钥：

```bash
# LiblibAI API 配置
LIBLIB_ACCESS_KEY=your_access_key_here
LIBLIB_SECRET_KEY=your_secret_key_here
LIBLIB_BASE_URL=https://www.liblib.art/api
```

### 2. F.1 模型基础配置

```bash
# F.1 模型基础参数
F1_DEFAULT_WIDTH=768                    # 默认图片宽度
F1_DEFAULT_HEIGHT=1024                  # 默认图片高度
F1_DEFAULT_STEPS=20                     # 默认生成步数
F1_DEFAULT_IMG_COUNT=1                  # 默认生成图片数量
F1_DEFAULT_RESTORE_FACES=true           # 是否启用面部修复（支持 true/false/1/0）
F1_DEFAULT_SEED=-1                      # 默认随机种子（-1表示随机）
```

### 3. F.1 模型高级配置

```bash
# F.1 模型高级参数
F1_DEFAULT_TEMPLATE_UUID=6f7c4652458d4802969f8d089cf5b91f  # 参数模板ID
F1_DEFAULT_CHECKPOINT_ID=                # 底模ID（可选）
F1_DEFAULT_VAE_ID=                       # VAE模型ID（可选）
F1_DEFAULT_CLIP_SKIP=2                   # Clip跳过层数
F1_DEFAULT_SAMPLER=15                    # 采样方法
F1_DEFAULT_CFG_SCALE=7.0                 # CFG Scale
F1_DEFAULT_RANDN_SOURCE=3                # 随机数源
F1_DEFAULT_NEGATIVE_PROMPT=              # 默认负向提示词
```

### 4. 高分辨率修复配置

```bash
# 高分辨率修复参数
F1_DEFAULT_HIRES_ENABLED=true            # 是否启用高分辨率修复
F1_DEFAULT_HIRES_STEPS=20                # 高分辨率修复步数
F1_DEFAULT_HIRES_DENOISING_STRENGTH=0.75 # 高分辨率修复重绘幅度
F1_DEFAULT_UPSCALER=10                   # 放大算法
F1_DEFAULT_HIRES_RESIZED_WIDTH=1024      # 高分辨率修复后宽度
F1_DEFAULT_HIRES_RESIZED_HEIGHT=1536     # 高分辨率修复后高度
```

## F.1 模型使用

### 1. 代码中使用

```python
from src.config import Config
from src.pipeline.liblib_service import LiblibService, LiblibConfig, F1GenerationParams

# 加载配置
config = Config()

# 创建服务
liblib_config = LiblibConfig(
    access_key=config.liblib_access_key,
    secret_key=config.liblib_secret_key
)
service = LiblibService(liblib_config, config)

# 使用默认配置创建参数
params = F1GenerationParams.from_config(
    prompt="a beautiful landscape",
    config=config
)

# 覆盖部分参数
params = F1GenerationParams.from_config(
    prompt="a beautiful landscape",
    config=config,
    steps=30,      # 覆盖默认步数
    width=1024,    # 覆盖默认宽度
    cfg_scale=8.0  # 覆盖默认CFG Scale
)

# 生成图片
result = service.f1_text_to_image(params)
print(f"任务UUID: {result.generate_uuid}")
```

### 2. 命令行使用

```bash
# 基础文生图
uv run src/liblib_standalone.py --prompt "your prompt" --use-f1

# 指定LoRA模型
uv run src/liblib_standalone.py --prompt "your prompt" --use-f1 \
    --lora-model-id "10880f7e4a06400e88c059886e9bc363" \
    --lora-weight 1.0

# 自定义参数
uv run src/liblib_standalone.py --prompt "your prompt" --use-f1 \
    --width 768 --height 1024 --steps 20 --restore-faces 1
```

## 批量图片生成

### 1. 并发模式（推荐）

适合大批量生成，速度快但需要注意API限制：

```bash
# 默认并发数为3
uv run src/liblib_standalone.py --json-file data/txt.json --output-dir ./output --use-f1

# 自定义并发数
uv run src/liblib_standalone.py --json-file data/txt.json --output-dir ./output --use-f1 --max-concurrent 2
```

**特性：**
- 默认最大并发数：3张图片同时生成
- 自动延迟机制：每个请求间隔 2-5 秒随机延迟
- 智能重试：遇到429错误自动重试
- 文件命名：`liblib_{uuid}_{index}.png`

### 2. 顺序模式（稳定）

适合对稳定性要求高的场景：

```bash
# 设置并发数为1确保顺序生成
uv run src/liblib_standalone.py --json-file data/txt.json --output-dir ./output --use-f1 --max-concurrent 1
```

**特性：**
- 无并发控制：图片按顺序逐一生成
- 稳定性优先：避免API频率限制
- 文件命名：`output_{i}.png`（从1开始）
- 跳过机制：文件已存在时自动跳过

### 3. JSON 文件格式

系统支持以下JSON格式，会智能提取提示词：

```json
[
  {
    "原始中文": "原始文本内容",
    "故事板提示词": "English prompt for image generation",  // 优先使用
    "prompt": "备选提示词",  // 故事板提示词不存在时使用
    "替换后中文": "处理后的中文内容",
    "LoRA编号": "001"
  }
]
```

## 参数详细说明

### 1. 基础参数

| 参数 | 类型 | 说明 | 默认值 | 环境变量 |
|------|------|------|--------|----------|
| `width` | int | 图片宽度 | 768 | `F1_DEFAULT_WIDTH` |
| `height` | int | 图片高度 | 1024 | `F1_DEFAULT_HEIGHT` |
| `steps` | int | 采样步数 | 20 | `F1_DEFAULT_STEPS` |
| `imgCount` | int | 生成图片数量 | 1 | `F1_DEFAULT_IMG_COUNT` |
| `seed` | int | 随机种子，-1表示随机 | -1 | `F1_DEFAULT_SEED` |
| `restoreFaces` | int | 面部修复，0关闭，1开启 | 0 | `F1_DEFAULT_RESTORE_FACES` |

### 2. 高级参数

| 参数 | 类型 | 说明 | 默认值 | 环境变量 |
|------|------|------|--------|----------|
| `templateUuid` | string | 参数模板ID | `6f7c4652458d4802969f8d089cf5b91f` | `F1_DEFAULT_TEMPLATE_UUID` |
| `clipSkip` | int | Clip跳过层数 | 2 | `F1_DEFAULT_CLIP_SKIP` |
| `sampler` | int | 采样方法 | 15 | `F1_DEFAULT_SAMPLER` |
| `cfgScale` | float | CFG Scale | 7.0 | `F1_DEFAULT_CFG_SCALE` |
| `randnSource` | int | 随机数源 | 3 | `F1_DEFAULT_RANDN_SOURCE` |

### 3. 采样器选项

- `15`: DPM++ 2M Karras（推荐）
- `16`: DPM++ SDE Karras
- `17`: DPM++ 2M SDE Karras

### 4. 放大算法选项

- `10`: Latent（推荐）
- `11`: Latent (antialiased)
- `12`: Latent (bicubic)
- `13`: Latent (bicubic antialiased)

## 高级功能

### 1. LoRA 模型配置

```python
from src.pipeline.liblib_service import AdditionalNetwork

# 单个LoRA
params = F1GenerationParams.from_config(
    prompt="anime style portrait",
    config=config,
    additional_network=[
        AdditionalNetwork(
            model_id="10880f7e4a06400e88c059886e9bc363",
            weight=1.0
        )
    ]
)

# 多个LoRA（最多5个）
params = F1GenerationParams.from_config(
    prompt="complex style",
    config=config,
    additional_network=[
        AdditionalNetwork(model_id="lora1_id", weight=0.8),
        AdditionalNetwork(model_id="lora2_id", weight=0.6)
    ]
)
```

### 2. 图生图功能

```python
from src.pipeline.liblib_service import F1Img2ImgParams

# 创建图生图参数
img2img_params = F1Img2ImgParams.from_config(
    prompt="anime style",
    source_image="https://example.com/image.jpg",
    config=config,
    denoising_strength=0.6  # 重绘幅度
)

# 执行图生图
result = service.f1_image_to_image(img2img_params)
```

### 3. 高分辨率修复

```python
from src.pipeline.liblib_service import HiResFixInfo

# 创建高分辨率修复参数
hires_fix = HiResFixInfo.from_config(
    config,
    hires_steps=30,  # 覆盖默认值
    upscaler=12      # 覆盖默认放大算法
)

# 在生成参数中使用
params = F1GenerationParams.from_config(
    prompt="high quality portrait",
    config=config,
    hi_res_fix_info=hires_fix
)
```

## 故障排除

### 常见问题

1. **API 认证失败**
   ```
   错误：Authentication failed
   解决：检查 .env 文件中的 API 密钥配置
   ```

2. **参数类型错误**
   ```
   错误：Invalid parameter type
   解决：确保环境变量中的数值类型正确，布尔值使用 true/false
   ```

3. **生成失败**
   ```
   错误：Generation failed
   解决：检查提示词是否包含敏感内容，验证模板UUID是否有效
   ```

4. **并发限制**
   ```
   错误：Rate limit exceeded (429)
   解决：降低并发数或使用顺序模式
   ```

### 调试技巧

```python
# 打印当前配置
config = Config()
print(f"当前F.1配置:")
print(f"  模板UUID: {config.f1_default_template_uuid}")
print(f"  步数: {config.f1_default_steps}")
print(f"  尺寸: {config.f1_default_width}x{config.f1_default_height}")

# 验证参数对象
params = F1GenerationParams.from_config(
    prompt="test",
    config=config
)
print(f"参数对象: {params.to_dict()}")
```

## 最佳实践

### 1. 参数调优建议

- **步数 (steps)**: 20-30步通常足够，更多步数收益递减
- **CFG Scale**: 7-12之间效果较好，过高可能过度拟合
- **重绘幅度**: 图生图时0.6-0.8适合大部分场景
- **图片尺寸**: 根据需求选择，避免不必要的高分辨率

### 2. 性能优化

- **并发控制**: 根据API限制调整，通常2-3个并发较稳定
- **批量处理**: 大批量时使用JSON文件而非单个命令
- **错误恢复**: 启用自动重试，设置合理的重试间隔
- **资源管理**: 监控API使用量，避免超出配额

### 3. 成本控制

- 合理设置图片数量和尺寸
- 使用适当的生成步数
- 避免不必要的高分辨率修复
- 定期检查API使用情况

### 4. 环境管理

- 将 `.env` 文件添加到 `.gitignore`
- 使用 `.env.example` 作为配置模板
- 为不同环境创建不同的配置文件

## 更新日志

- **v2.0.0**: 整合所有LiblibAI功能到统一文档
- **v1.5.0**: 添加高分辨率修复开关功能
- **v1.4.0**: 修复restoreFaces参数类型转换问题
- **v1.3.0**: 支持环境变量配置所有F.1参数
- **v1.2.0**: 添加批量生成并发控制
- **v1.1.0**: 支持LoRA模型和图生图功能
- **v1.0.0**: 初始版本，基础F.1文生图功能

---

**相关文档**
- [LiblibAI API 参考](docs/liblib_api_reference.md)
- [项目配置说明](src/config.py)
- [完整示例代码](examples/)
