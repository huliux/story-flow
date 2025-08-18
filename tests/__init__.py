"""Story Flow 测试包

这个包包含了Story Flow项目的所有测试，包括单元测试、集成测试和端到端测试。

测试结构:
- unit/: 单元测试，测试单个函数和类
- integration/: 集成测试，测试模块间的交互
- fixtures/: 测试数据和共享的测试工具
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))