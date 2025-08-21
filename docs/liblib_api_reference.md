# LiblibAI API 参考文档

本文档提供 LiblibAI API 的核心参考信息，专注于项目实际使用的功能。

## API 基础信息

### 访问地址
- **开放平台域名**: https://openapi.liblibai.cloud
- **API Base URL**: https://www.liblib.art/api

### 认证方式
使用 Access Key 和 Secret Key 进行认证，需要在请求头中包含签名信息。

## 核心 API 接口

### 1. F.1 文生图接口

**接口地址**: `POST /open/f1/text-to-image`

**请求参数**:
```json
{
    "templateUuid": "6f7c4652458d4802969f8d089cf5b91f",
    "generateParams": {
        "prompt": "your prompt here",
        "steps": 20,
        "width": 768,
        "height": 1024,
        "imgCount": 1,
        "seed": -1,
        "restoreFaces": 0,
        "clipSkip": 2,
        "sampler": 15,
        "cfgScale": 7.0,
        "randnSource": 3,
        "negativePrompt": "",
        "additionalNetwork": [
            {
                "modelId": "lora_model_id",
                "weight": 1.0
            }
        ],
        "hiResFixInfo": {
            "hiresSteps": 20,
            "hiresDenosingStrength": 0.75,
            "upscaler": 10,
            "hiresResizedWidth": 1024,
            "hiresResizedHeight": 1536
        }
    }
}
```

**响应示例**:
```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "generateUuid": "uuid-string-here"
    }
}
```

### 2. F.1 图生图接口

**接口地址**: `POST /open/f1/image-to-image`

**请求参数**:
```json
{
    "templateUuid": "6f7c4652458d4802969f8d089cf5b91f",
    "generateParams": {
        "prompt": "your prompt here",
        "sourceImage": "https://example.com/image.jpg",
        "resizeMode": 0,
        "resizedWidth": 768,
        "resizedHeight": 1024,
        "mode": 0,
        "denoisingStrength": 0.75,
        "steps": 20,
        "width": 768,
        "height": 1024,
        "imgCount": 1,
        "seed": -1,
        "restoreFaces": 0
    }
}
```

### 3. 查询生成状态接口

**接口地址**: `GET /open/generate-status/{generateUuid}`

**响应示例**:
```json
{
    "code": 200,
    "msg": "success",
    "data": {
        "status": "SUCCESS",
        "progress": 100,
        "imageUrls": [
            "https://example.com/generated-image.jpg"
        ],
        "pointsCost": 10,
        "accountBalance": 990
    }
}
```

**状态说明**:
- `PENDING`: 排队中
- `PROCESSING`: 生成中
- `SUCCESS`: 生成成功
- `FAILED`: 生成失败

## 参数详细说明

### 基础参数

| 参数 | 类型 | 必填 | 说明 | 取值范围 |
|------|------|------|------|----------|
| `templateUuid` | string | 是 | F.1模板ID | 固定值: `6f7c4652458d4802969f8d089cf5b91f` |
| `prompt` | string | 是 | 提示词 | 最大1000字符 |
| `steps` | int | 否 | 采样步数 | 1-50，推荐20-30 |
| `width` | int | 否 | 图片宽度 | 64-2048，需要是64的倍数 |
| `height` | int | 否 | 图片高度 | 64-2048，需要是64的倍数 |
| `imgCount` | int | 否 | 生成数量 | 1-4 |
| `seed` | int | 否 | 随机种子 | -1表示随机 |
| `restoreFaces` | int | 否 | 面部修复 | 0=关闭，1=开启 |

### 高级参数

| 参数 | 类型 | 必填 | 说明 | 取值范围 |
|------|------|------|------|----------|
| `clipSkip` | int | 否 | Clip跳过层数 | 1-12，推荐2 |
| `sampler` | int | 否 | 采样器 | 见采样器列表 |
| `cfgScale` | float | 否 | CFG引导强度 | 1.0-30.0，推荐7.0 |
| `randnSource` | int | 否 | 随机数源 | 1-4，推荐3 |
| `negativePrompt` | string | 否 | 负向提示词 | 最大1000字符 |

### 采样器列表

| ID | 名称 | 说明 |
|----|------|------|
| 15 | DPM++ 2M Karras | 推荐，速度和质量平衡 |
| 16 | DPM++ SDE Karras | 高质量，速度较慢 |
| 17 | DPM++ 2M SDE Karras | 最高质量，最慢 |
| 18 | Euler a | 快速，适合测试 |
| 19 | Euler | 经典采样器 |

### 放大算法列表

| ID | 名称 | 说明 |
|----|------|------|
| 10 | Latent | 推荐，速度快 |
| 11 | Latent (antialiased) | 抗锯齿版本 |
| 12 | Latent (bicubic) | 双三次插值 |
| 13 | Latent (bicubic antialiased) | 双三次插值抗锯齿 |

### LoRA 模型配置

```json
"additionalNetwork": [
    {
        "modelId": "lora_model_uuid",  // LoRA模型ID
        "weight": 1.0                  // 权重，0.0-2.0
    }
]
```

**注意事项**:
- 最多支持5个LoRA模型
- 权重建议在0.5-1.5之间
- 过高的权重可能导致过拟合

### 高分辨率修复配置

```json
"hiResFixInfo": {
    "hiresSteps": 20,                    // 高分辨率修复步数
    "hiresDenosingStrength": 0.75,      // 重绘强度
    "upscaler": 10,                     // 放大算法
    "hiresResizedWidth": 1024,          // 目标宽度
    "hiresResizedHeight": 1536          // 目标高度
}
```

## 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查请求参数格式和取值范围 |
| 401 | 认证失败 | 检查API密钥配置 |
| 403 | 权限不足 | 检查账户权限和余额 |
| 429 | 请求频率过高 | 降低请求频率或使用队列 |
| 500 | 服务器错误 | 稍后重试或联系技术支持 |

## 常用尺寸推荐

### 标准尺寸
- **方形**: 1024x1024, 768x768, 512x512
- **竖屏**: 768x1024, 576x1024, 512x768
- **横屏**: 1024x768, 1024x576, 768x512

### 高分辨率
- **2K**: 1536x2048, 2048x1536
- **4K**: 2048x2048（需要高分辨率修复）

## 计费说明

### 积分消耗
- **基础生成**: 根据图片尺寸和步数计算
- **高分辨率修复**: 额外消耗积分
- **LoRA模型**: 每个LoRA额外消耗少量积分

### 优化建议
- 合理选择图片尺寸
- 避免过多的生成步数
- 谨慎使用高分辨率修复
- 批量生成时控制并发数

## 最佳实践

### 1. 提示词优化
- 使用英文提示词，效果更好
- 避免过于复杂的描述
- 使用逗号分隔不同元素
- 添加质量词汇如"high quality", "detailed"

### 2. 参数调优
- 从默认参数开始调试
- 逐步调整单个参数
- 记录效果好的参数组合
- 针对不同风格使用不同配置

### 3. 错误处理
- 实现自动重试机制
- 记录详细的错误日志
- 设置合理的超时时间
- 监控API使用情况

### 4. 性能优化
- 使用连接池复用连接
- 实现请求队列避免429错误
- 缓存常用的生成结果
- 异步处理大批量任务

---

**更多信息**
- [LiblibAI 完整使用指南](docs/liblib_ai_complete_guide.md)
- [官方API文档](https://openapi.liblibai.cloud/docs)
- [技术支持](https://www.liblib.art/support)
