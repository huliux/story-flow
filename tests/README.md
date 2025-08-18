# 测试文档

## 概述

本项目采用 pytest 作为测试框架，包含单元测试和集成测试。测试套件支持选择性运行，可以跳过需要外部服务的测试。

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest配置和fixtures
├── fixtures/                # 测试数据和fixtures
│   ├── __init__.py
│   └── data/               # 测试数据文件
├── integration/            # 集成测试
│   ├── __init__.py
│   ├── test_external_services.py
│   └── test_pipeline_integration.py
└── unit/                   # 单元测试
    ├── __init__.py
    ├── test_config.py
    ├── test_image_generator.py
    ├── test_llm_client.py
    ├── test_text_analyzer.py
    ├── test_video_composer.py
    └── test_voice_synthesizer.py
```

## 运行测试

### 运行所有测试
```bash
uv run pytest
```

### 运行特定测试文件
```bash
uv run pytest tests/unit/test_llm_client.py
```

### 运行特定测试方法
```bash
uv run pytest tests/unit/test_llm_client.py::TestLLMClient::test_init_deepseek_provider
```

### 使用标记选择性运行测试

项目配置了以下pytest标记：

- `openai`: 需要OpenAI API的测试
- `deepseek`: 需要DeepSeek API的测试

#### 只运行DeepSeek相关测试
```bash
uv run pytest -k "deepseek"
```

#### 跳过OpenAI相关测试
```bash
uv run pytest -m "not openai"
```

#### 跳过需要外部服务的测试
```bash
uv run pytest -m "not openai" --ignore=tests/unit/test_voice_synthesizer.py --ignore=tests/unit/test_video_composer.py
```

### 显示详细输出
```bash
uv run pytest -v
```

### 显示测试覆盖率
```bash
uv run pytest --cov=src
```

## 测试配置

### pytest.ini

项目根目录的 `pytest.ini` 文件包含以下配置：

- 测试发现路径
- 输出格式设置
- 标记定义
- 警告过滤

### conftest.py

`tests/conftest.py` 文件包含：

- 全局fixtures
- 测试配置
- Mock对象设置

## 测试类型说明

### 单元测试

单元测试位于 `tests/unit/` 目录，测试单个模块或类的功能：

- **test_config.py**: 配置管理测试
- **test_llm_client.py**: LLM客户端测试（支持OpenAI和DeepSeek）
- **test_text_analyzer.py**: 文本分析器测试
- **test_image_generator.py**: 图像生成器测试
- **test_voice_synthesizer.py**: 语音合成器测试
- **test_video_composer.py**: 视频合成器测试

### 集成测试

集成测试位于 `tests/integration/` 目录，测试模块间的交互：

- **test_external_services.py**: 外部服务集成测试
- **test_pipeline_integration.py**: 流水线集成测试

## Mock和Fixtures

### 常用Fixtures

- `mock_config`: 模拟配置对象
- `mock_llm_client`: 模拟LLM客户端
- `sample_text`: 示例文本数据
- `temp_dir`: 临时目录

### Mock策略

- 外部API调用使用mock避免实际网络请求
- 文件系统操作使用临时目录
- 数据库操作使用内存数据库或mock

## 测试最佳实践

### 编写测试

1. **测试命名**: 使用描述性的测试方法名
2. **测试结构**: 遵循 Arrange-Act-Assert 模式
3. **测试隔离**: 每个测试应该独立运行
4. **边界测试**: 测试边界条件和异常情况

### 示例测试

```python
def test_llm_client_deepseek_success(self, mock_config):
    """测试DeepSeek客户端成功调用"""
    # Arrange
    mock_config.llm_provider = "deepseek"
    mock_config.deepseek_api_key = "test_key"
    
    # Act
    with patch('src.llm_client.config', mock_config):
        client = LLMClient()
        result = client.chat_completion([{"role": "user", "content": "test"}])
    
    # Assert
    assert result is not None
```

## 持续集成

### GitHub Actions

项目可以配置GitHub Actions来自动运行测试：

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.12
    - name: Install dependencies
      run: |
        pip install uv
        uv sync
    - name: Run tests
      run: uv run pytest -m "not openai"
```

## 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录在Python路径中
2. **Mock失败**: 检查mock的路径和参数是否正确
3. **异步测试**: 使用 `@pytest.mark.asyncio` 装饰器
4. **依赖缺失**: 运行 `uv sync` 安装所有依赖

### 调试测试

```bash
# 运行单个测试并显示详细输出
uv run pytest tests/unit/test_llm_client.py::test_specific_method -v -s

# 在测试失败时进入调试器
uv run pytest --pdb

# 显示最慢的10个测试
uv run pytest --durations=10
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
uv run pytest --cov=src --cov-report=html

# 生成终端覆盖率报告
uv run pytest --cov=src --cov-report=term-missing
```

### 覆盖率目标

- 单元测试覆盖率目标: >80%
- 核心模块覆盖率目标: >90%
- 关键业务逻辑覆盖率目标: >95%

## 贡献指南

### 添加新测试

1. 在相应的测试目录中创建测试文件
2. 遵循现有的命名约定
3. 添加适当的docstring
4. 使用合适的pytest标记
5. 确保测试可以独立运行

### 测试审查清单

- [ ] 测试名称清晰描述测试内容
- [ ] 测试覆盖正常和异常情况
- [ ] 使用适当的断言
- [ ] Mock外部依赖
- [ ] 测试可以重复运行
- [ ] 添加必要的pytest标记

---

更多信息请参考 [pytest官方文档](https://docs.pytest.org/) 和项目的具体测试文件。