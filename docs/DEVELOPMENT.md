# 开发者指南

## 开发环境搭建

### 环境要求

- Python 3.8+
- pip 20.0+
- Git 2.20+

### 快速开始

```bash
# 克隆项目
git clone https://github.com/HuangJingping/test-scheduling-system.git
cd test-scheduling-system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行测试
python basic_test.py

# 运行演示
python demo_video_fixed.py
```

### 开发依赖安装

```bash
# 安装开发工具
pip install -r requirements-dev.txt

# 或手动安装
pip install pytest pytest-cov black flake8 mypy
```

## 项目结构

```
test-scheduling-system/
├── README.md                    # 项目说明
├── requirements.txt             # 生产依赖
├── requirements-dev.txt         # 开发依赖
├── .gitignore                  # Git忽略文件
├── .github/                    # GitHub配置
│   └── workflows/              # CI/CD流程
├── docs/                       # 文档目录
│   ├── ARCHITECTURE.md         # 架构文档
│   ├── API.md                  # API文档
│   ├── DEVELOPMENT.md          # 开发指南
│   └── DEPLOYMENT.md           # 部署文档
├── tests/                      # 测试目录
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── fixtures/               # 测试数据
├── config/                     # 配置文件
│   ├── scheduler_config.json   # 系统配置
│   └── test_data.json          # 测试数据
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── config.py               # 配置管理
│   ├── models.py               # 数据模型
│   ├── constraints.py          # 约束检查
│   ├── priority_calculator.py  # 优先级计算
│   ├── scheduling_algorithm.py # 调度算法
│   ├── time_manager.py         # 时间管理
│   ├── output_formatter.py     # 输出格式化
│   ├── test_scheduler_refactored.py  # 时间调度器
│   └── sequence_scheduler.py   # 序列调度器
├── examples/                   # 示例代码
│   ├── basic_usage.py          # 基础用法
│   ├── advanced_usage.py       # 高级用法
│   └── custom_scheduler.py     # 自定义调度器
└── scripts/                    # 工具脚本
    ├── setup.py                # 安装脚本
    ├── test.py                 # 测试脚本
    └── benchmark.py            # 性能基准
```

## 代码规范

### Python代码风格

遵循 PEP 8 标准，使用以下工具确保代码质量：

```bash
# 代码格式化
black . --line-length 88

# 代码检查
flake8 . --max-line-length 88

# 类型检查
mypy . --ignore-missing-imports
```

### 命名约定

- **类名**: PascalCase (如 `TestScheduler`)
- **函数名**: snake_case (如 `calculate_priority`)
- **变量名**: snake_case (如 `test_items`)
- **常量**: UPPER_SNAKE_CASE (如 `MAX_PARALLEL`)
- **私有成员**: 前缀下划线 (如 `_internal_method`)

### 文档字符串

使用Google风格的docstring：

```python
def calculate_priority(self, test_item: TestItem) -> float:
    """计算测试项的优先级。
    
    Args:
        test_item: 测试项对象
        
    Returns:
        float: 计算得出的优先级分数
        
    Raises:
        ValueError: 当测试项数据无效时
        
    Examples:
        >>> calculator = PriorityCalculator(config)
        >>> priority = calculator.calculate_priority(test_item)
        >>> print(f"优先级: {priority}")
    """
    pass
```

### 类型提示

所有公共API都必须包含类型提示：

```python
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class TestItem:
    test_id: int
    test_item: str
    duration: int
    dependencies: Optional[List[str]] = None

def schedule_tests(
    test_items: List[TestItem], 
    config: Dict[str, any]
) -> Optional[SchedulingResult]:
    """类型提示示例"""
    pass
```

## 开发工作流

### 分支策略

- `main`: 稳定版本分支
- `develop`: 开发分支
- `feature/*`: 功能开发分支
- `bugfix/*`: 错误修复分支
- `hotfix/*`: 热修复分支

### 开发流程

1. **创建功能分支**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/new-algorithm
```

2. **开发和测试**
```bash
# 编写代码
# 运行测试
python -m pytest tests/
# 代码检查
black . && flake8 . && mypy .
```

3. **提交代码**
```bash
git add .
git commit -m "feat: add new scheduling algorithm

- Implement genetic algorithm for optimization
- Add configuration options for algorithm parameters
- Include comprehensive test coverage"
```

4. **创建Pull Request**
```bash
git push origin feature/new-algorithm
# 在GitHub上创建PR
```

### 提交信息规范

使用约定式提交(Conventional Commits)：

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

**示例**:
```
feat(scheduler): add genetic algorithm support

Implement genetic algorithm as an alternative scheduling method.
This provides better optimization for large test suites.

Closes #123
```

## 测试指南

### 测试结构

```
tests/
├── __init__.py
├── conftest.py                 # pytest配置
├── unit/                       # 单元测试
│   ├── test_config.py
│   ├── test_models.py
│   ├── test_constraints.py
│   ├── test_priority_calculator.py
│   ├── test_scheduling_algorithm.py
│   └── test_time_manager.py
├── integration/                # 集成测试
│   ├── test_test_scheduler.py
│   ├── test_sequence_scheduler.py
│   └── test_end_to_end.py
├── fixtures/                   # 测试数据
│   ├── sample_config.json
│   ├── sample_test_data.json
│   └── large_dataset.json
└── performance/                # 性能测试
    ├── test_benchmark.py
    └── test_memory_usage.py
```

### 编写测试

#### 单元测试示例

```python
import pytest
from unittest.mock import Mock, patch
from models import TestItem
from priority_calculator import PriorityCalculator

class TestPriorityCalculator:
    @pytest.fixture
    def config(self):
        return Mock(priority_weights=Mock(
            dependency=10,
            duration=2,
            resource=5
        ))
    
    @pytest.fixture
    def calculator(self, config):
        return PriorityCalculator(config)
    
    def test_calculate_basic_priority(self, calculator):
        """测试基本优先级计算"""
        test_item = TestItem(
            test_id=1,
            test_item="测试项",
            test_phase="系统测试",
            test_group="基础功能",
            required_equipment="测试台",
            required_instruments="无",
            duration=4
        )
        
        priority = calculator.calculate_priority(test_item)
        assert priority > 0
        assert isinstance(priority, float)
    
    def test_dependency_affects_priority(self, calculator):
        """测试依赖关系对优先级的影响"""
        # 有依赖的测试项
        item_with_deps = TestItem(test_id=1, test_item="A", duration=2)
        item_without_deps = TestItem(test_id=2, test_item="B", duration=2)
        
        # 模拟依赖关系
        with patch.object(calculator, '_get_dependency_count') as mock_deps:
            mock_deps.side_effect = lambda item: 3 if item.test_id == 1 else 0
            
            priority_with_deps = calculator.calculate_priority(item_with_deps)
            priority_without_deps = calculator.calculate_priority(item_without_deps)
            
            assert priority_with_deps > priority_without_deps
    
    @pytest.mark.parametrize("duration,expected_range", [
        (1, (0, 50)),
        (5, (50, 100)),
        (10, (100, 200))
    ])
    def test_duration_priority_scaling(self, calculator, duration, expected_range):
        """测试持续时间对优先级的影响"""
        test_item = TestItem(test_id=1, test_item="测试", duration=duration)
        priority = calculator.calculate_priority(test_item)
        
        assert expected_range[0] <= priority <= expected_range[1]
```

#### 集成测试示例

```python
import pytest
import tempfile
import json
from test_scheduler_refactored import TestScheduler

class TestSchedulerIntegration:
    @pytest.fixture
    def sample_data(self):
        return {
            "test_items": [
                {
                    "test_id": 1,
                    "test_phase": "系统测试",
                    "test_group": "基础功能",
                    "test_item": "系统启动测试",
                    "required_equipment": "测试台",
                    "required_instruments": "无",
                    "duration": 2
                },
                {
                    "test_id": 2,
                    "test_phase": "系统测试",
                    "test_group": "基础功能",
                    "test_item": "用户登录验证",
                    "required_equipment": "测试台",
                    "required_instruments": "无",
                    "duration": 1
                }
            ],
            "dependencies": {
                "用户登录验证": ["系统启动测试"]
            },
            "instruments": {}
        }
    
    def test_end_to_end_scheduling(self, sample_data):
        """端到端调度测试"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            data_file = f.name
        
        try:
            # 执行调度
            scheduler = TestScheduler()
            scheduler.load_data_from_file(data_file)
            result = scheduler.solve_schedule()
            
            # 验证结果
            assert result.success
            assert len(result.schedule) == 2
            assert result.total_duration > 0
            
            # 验证依赖关系
            schedule_dict = {item.test_item: item for item in result.schedule}
            login_item = schedule_dict["用户登录验证"]
            startup_item = schedule_dict["系统启动测试"]
            
            # 登录测试应该在启动测试之后
            assert login_item.start_time > startup_item.start_time
            
        finally:
            import os
            os.unlink(data_file)
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_priority_calculator.py

# 运行特定测试方法
pytest tests/unit/test_priority_calculator.py::TestPriorityCalculator::test_calculate_basic_priority

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 运行性能测试
pytest tests/performance/ -v

# 并行运行测试
pytest -n auto
```

### 测试覆盖率要求

- 单元测试覆盖率 >= 90%
- 分支覆盖率 >= 85%
- 关键业务逻辑覆盖率 = 100%

## 调试指南

### 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 使用日志
logger.debug("调试信息")
logger.info("常规信息")
logger.warning("警告信息")
logger.error("错误信息")
```

### 调试技巧

#### 1. 使用断点调试

```python
import pdb

def complex_calculation():
    result = 0
    for i in range(100):
        pdb.set_trace()  # 设置断点
        result += i * 2
    return result
```

#### 2. 使用装饰器进行函数追踪

```python
from functools import wraps
import time

def debug_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 执行时间: {end - start:.4f}秒")
        return result
    return wrapper

@debug_timer
def slow_function():
    time.sleep(1)
    return "完成"
```

#### 3. 内存使用分析

```python
import tracemalloc
import gc

def analyze_memory():
    tracemalloc.start()
    
    # 你的代码
    scheduler = TestScheduler()
    result = scheduler.solve_schedule()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"当前内存使用: {current / 1024 / 1024:.1f} MB")
    print(f"峰值内存使用: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()
```

### 常见问题解决

#### 1. 循环依赖检测

```python
def debug_circular_dependency(dependencies: Dict[str, List[str]]):
    """调试循环依赖问题"""
    graph = defaultdict(list)
    for item, deps in dependencies.items():
        for dep in deps:
            graph[dep].append(item)
    
    visited = set()
    rec_stack = set()
    
    def dfs(node, path):
        if node in rec_stack:
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            print(f"发现循环依赖: {' -> '.join(cycle)}")
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph[node]:
            if dfs(neighbor, path):
                return True
        
        rec_stack.remove(node)
        path.pop()
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node, []):
                break
```

#### 2. 性能瓶颈分析

```python
import cProfile
import pstats

def profile_scheduling():
    """分析调度性能"""
    scheduler = TestScheduler()
    scheduler.load_data_from_file('large_test_data.json')
    
    # 性能分析
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = scheduler.solve_schedule()
    
    profiler.disable()
    
    # 输出结果
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 显示前20个最耗时的函数
```

## 性能优化

### 算法优化

1. **依赖关系图优化**
```python
# 使用位运算优化依赖检查
class OptimizedDependencyGraph:
    def __init__(self):
        self.adjacency_matrix = {}  # 使用位掩码
    
    def has_dependency(self, test1: int, test2: int) -> bool:
        return bool(self.adjacency_matrix.get(test1, 0) & (1 << test2))
```

2. **优先级计算缓存**
```python
from functools import lru_cache

class CachedPriorityCalculator:
    @lru_cache(maxsize=1000)
    def calculate_priority(self, test_item_hash: str) -> float:
        # 缓存优先级计算结果
        pass
```

### 内存优化

1. **使用生成器**
```python
def process_large_dataset(filename: str):
    """使用生成器处理大数据集"""
    with open(filename, 'r') as f:
        for line in f:
            yield json.loads(line)
```

2. **对象池模式**
```python
class ScheduledItemPool:
    def __init__(self, pool_size: int = 100):
        self._pool = [ScheduledItem() for _ in range(pool_size)]
        self._available = list(range(pool_size))
    
    def get_item(self) -> ScheduledItem:
        if self._available:
            index = self._available.pop()
            return self._pool[index]
        return ScheduledItem()  # 池满时创建新对象
    
    def return_item(self, item: ScheduledItem, index: int):
        item.reset()  # 重置对象状态
        self._available.append(index)
```

## 部署和发布

### 版本管理

使用语义化版本号 (Semantic Versioning):
- MAJOR.MINOR.PATCH (如 1.2.3)
- MAJOR: 不兼容的API修改
- MINOR: 向后兼容的功能性新增
- PATCH: 向后兼容的问题修正

### 发布流程

1. **更新版本号**
```python
# setup.py
setup(
    name="test-scheduling-system",
    version="1.2.3",
    # ...
)
```

2. **创建发布标签**
```bash
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3
```

3. **构建分发包**
```bash
python setup.py sdist bdist_wheel
```

4. **发布到PyPI**
```bash
twine upload dist/*
```

### 持续集成

GitHub Actions配置示例：

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
    
    - name: Type check with mypy
      run: mypy . --ignore-missing-imports
    
    - name: Test with pytest
      run: pytest --cov=src --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 贡献指南

### 如何贡献

1. Fork项目
2. 创建功能分支
3. 编写代码和测试
4. 确保所有测试通过
5. 提交Pull Request

### Pull Request检查清单

- [ ] 代码遵循项目风格指南
- [ ] 添加了必要的测试
- [ ] 所有测试都通过
- [ ] 更新了相关文档
- [ ] 提交信息清晰明确
- [ ] 没有合并冲突

### 代码审查标准

1. **功能性**: 代码是否实现了预期功能
2. **可读性**: 代码是否易于理解和维护
3. **性能**: 是否存在性能问题
4. **安全性**: 是否存在安全漏洞
5. **测试**: 测试覆盖是否充分

## 常见问题 (FAQ)

### Q: 如何添加新的调度算法？

A: 继承`SchedulingAlgorithm`基类，实现必要的方法：

```python
class MyCustomAlgorithm(SchedulingAlgorithm):
    def calculate_schedule(self, test_items: List[TestItem]) -> SchedulingResult:
        # 实现你的算法逻辑
        pass
```

### Q: 如何自定义优先级计算？

A: 继承`PriorityCalculator`类并重写相关方法：

```python
class CustomPriorityCalculator(PriorityCalculator):
    def calculate_priority(self, test_item: TestItem) -> float:
        base_priority = super().calculate_priority(test_item)
        # 添加自定义逻辑
        return base_priority + custom_weight
```

### Q: 如何处理大数据集？

A: 使用分批处理和流式处理：

```python
def process_large_dataset(filename: str, batch_size: int = 100):
    for batch in read_in_batches(filename, batch_size):
        scheduler = TestScheduler()
        scheduler.load_data_from_dict(batch)
        yield scheduler.solve_schedule()
```

### Q: 如何优化调度性能？

A: 几个优化建议：
1. 使用缓存减少重复计算
2. 并行处理独立的测试组
3. 使用更高效的数据结构
4. 启用日志分析性能瓶颈

## 相关资源

- [项目仓库](https://github.com/HuangJingping/test-scheduling-system)
- [在线文档](https://test-scheduling-system.readthedocs.io)
- [问题反馈](https://github.com/HuangJingping/test-scheduling-system/issues)
- [讨论区](https://github.com/HuangJingping/test-scheduling-system/discussions)

---

**开发愉快！如果遇到问题，欢迎提Issue或参与讨论。**