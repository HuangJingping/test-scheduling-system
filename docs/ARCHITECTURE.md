# 系统架构文档

## 概述

测试调度系统采用模块化架构设计，将复杂的调度问题分解为独立的、可测试的组件。系统支持两种调度模式：基于时间的精确调度和基于序列的逻辑调度。

## 架构原则

### 1. 单一职责原则
每个模块都有明确的职责边界，避免功能重叠和耦合。

### 2. 开闭原则
对扩展开放，对修改封闭。新的调度算法或约束条件可以通过扩展实现。

### 3. 依赖倒置原则
高层模块不依赖低层模块，都依赖于抽象接口。

### 4. 配置外置原则
所有业务逻辑参数都外置到配置文件，代码与配置分离。

## 系统层次结构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                   │
├─────────────────────────────────────────────────────────┤
│  TestScheduler    │  SequenceScheduler  │  OutputFormatter │
├─────────────────────────────────────────────────────────┤
│                    业务逻辑层 (Business)                   │
├─────────────────────────────────────────────────────────┤
│ SchedulingAlgorithm │ PriorityCalculator │ Constraints    │
├─────────────────────────────────────────────────────────┤
│                    数据层 (Data)                         │
├─────────────────────────────────────────────────────────┤
│    Models         │   ConfigManager    │   TimeManager   │
└─────────────────────────────────────────────────────────┘
```

## 核心模块详解

### 1. 配置管理层 (config.py)

**职责**：
- 统一管理系统配置参数
- 提供类型安全的配置访问
- 支持配置文件热加载

**核心类**：
```python
@dataclass
class SchedulingConfig:
    max_parallel: int = 3
    max_parallel_per_phase: int = 3

@dataclass  
class PriorityWeights:
    dependency: int = 10
    duration: int = 2
    resource: int = 5
    phase: int = 20
    continuity: int = 50
```

**设计亮点**：
- 使用dataclass提供类型检查
- 分层配置结构，便于管理
- 默认值确保系统鲁棒性

### 2. 数据模型层 (models.py)

**职责**：
- 定义核心数据结构
- 提供数据验证机制
- 管理依赖关系图

**核心类**：
```python
@dataclass
class TestItem:
    test_id: int
    test_phase: str
    test_group: str
    test_item: str
    required_equipment: str
    required_instruments: str
    duration: int
```

**依赖关系图**：
```python
class DependencyGraph:
    def build_matrix(self, test_items: List[TestItem])
    def has_cycle(self) -> bool
    def topological_sort(self) -> List[int]
```

### 3. 约束检查层 (constraints.py)

**职责**：
- 资源冲突检测
- 依赖关系验证
- 阶段顺序约束

**算法实现**：
```python
class ResourceMatrix:
    def check_resource_conflict(self, test1: TestItem, test2: TestItem) -> bool
    def get_available_slots(self, time_slot: float) -> Dict[str, int]
    
class ConstraintChecker:
    def check_dependency_constraint(self, test_item: TestItem, 
                                    scheduled_items: List[ScheduledItem]) -> bool
    def check_phase_constraint(self, test_item: TestItem, 
                               current_phase: str) -> bool
```

### 4. 优先级计算层 (priority_calculator.py)

**职责**：
- 多维度优先级计算
- 动态权重调整
- 智能排序算法

**计算公式**：
```
Priority = W_dep × DependencyScore + 
          W_dur × DurationScore + 
          W_res × ResourceScore + 
          W_phase × PhaseScore + 
          W_cont × ContinuityScore
```

**评分维度**：
- **依赖评分**：被依赖次数越多，优先级越高
- **资源评分**：所需资源越复杂，优先级越高
- **阶段评分**：严格按阶段顺序排序
- **连续性评分**：同组测试项保持连续

### 5. 调度算法层 (scheduling_algorithm.py)

**职责**：
- 核心调度逻辑实现
- 并行执行优化
- 冲突解决策略

**算法流程**：
```python
def schedule_tests(self) -> SchedulingResult:
    1. 构建依赖关系图
    2. 计算优先级排序
    3. 检查约束条件
    4. 分配时间槽
    5. 优化并行执行
    6. 生成调度结果
```

**并行优化策略**：
- 识别无依赖冲突的测试组
- 动态调整并行度
- 资源利用率最大化

### 6. 时间管理层 (time_manager.py)

**职责**：
- 工作时间计算
- 时间槽分配
- 休息日处理

**时间计算逻辑**：
```python
class TimeManager:
    def calculate_end_time(self, start_time: float, duration: int) -> float
    def get_next_available_slot(self, current_time: float) -> float
    def is_working_time(self, time_slot: float) -> bool
```

### 7. 输出格式化层 (output_formatter.py)

**职责**：
- 多格式结果输出
- 报表生成
- 可视化支持

**输出格式**：
- **Excel报表**：详细调度表、统计汇总
- **文本计划**：简洁执行指南
- **JSON数据**：程序化接口

## 双调度模式设计

### 时间调度模式 (TestScheduler)

**适用场景**：
- 时间估计相对准确的项目
- 需要精确时间管理的场合
- 资源调度严格的环境

**核心特性**：
- 精确到小时的时间安排
- 甘特图可视化支持
- 详细的资源占用分析

### 序列调度模式 (SequenceScheduler)

**适用场景**：
- 时间估计不准确的项目
- 重视逻辑顺序的场合
- 敏捷开发环境

**核心特性**：
- 关注执行顺序而非时间
- 依赖层级清晰展示
- 并行建议智能生成

## 扩展点设计

### 1. 新增调度算法

```python
class CustomSchedulingAlgorithm(SchedulingAlgorithm):
    def calculate_priority(self, test_item: TestItem) -> float:
        # 自定义优先级计算逻辑
        pass
        
    def resolve_conflicts(self, conflicted_items: List[TestItem]) -> List[TestItem]:
        # 自定义冲突解决策略
        pass
```

### 2. 新增约束条件

```python
class CustomConstraint(ConstraintChecker):
    def check_custom_constraint(self, test_item: TestItem, context: dict) -> bool:
        # 自定义约束检查逻辑
        pass
```

### 3. 新增输出格式

```python
class CustomOutputFormatter(OutputFormatter):
    def format_custom_output(self, result: SchedulingResult) -> str:
        # 自定义输出格式
        pass
```

## 性能优化策略

### 1. 算法复杂度优化
- 依赖关系图：O(V + E) 拓扑排序
- 优先级计算：O(N log N) 排序
- 约束检查：O(N²) 最坏情况，实际优化到 O(N log N)

### 2. 内存使用优化
- 懒加载策略：按需加载测试数据
- 对象池：复用临时对象
- 流式处理：大数据集分批处理

### 3. 并发处理优化
- 并行优先级计算
- 异步约束检查
- 多线程结果生成

## 错误处理策略

### 1. 输入验证
```python
class DataValidator:
    def validate_test_items(self, items: List[dict]) -> List[ValidationError]:
        # 数据格式验证
        # 必填字段检查
        # 数据类型验证
        pass
```

### 2. 循环依赖检测
```python
def detect_circular_dependencies(self) -> List[str]:
    # DFS检测环形依赖
    # 返回形成环的测试项列表
    pass
```

### 3. 资源冲突解决
```python
def resolve_resource_conflicts(self, conflicts: List[Conflict]) -> Resolution:
    # 智能冲突解决
    # 时间调整建议
    # 资源替代方案
    pass
```

## 配置文件设计

### 系统配置 (scheduler_config.json)
```json
{
  "scheduling": {
    "max_parallel": 3,
    "max_parallel_per_phase": 3
  },
  "working_time": {
    "hours_per_day": 8,
    "rest_day_cycle": 7
  },
  "priority_weights": {
    "dependency": 10,
    "duration": 2,
    "resource": 5,
    "phase": 20,
    "continuity": 50
  }
}
```

### 测试数据 (test_data.json)
```json
{
  "test_items": [...],
  "dependencies": {...},
  "instruments": {...}
}
```

## 质量保证

### 1. 单元测试覆盖
- 每个模块都有对应的测试文件
- 测试覆盖率目标：>90%
- 边界条件和异常情况测试

### 2. 集成测试
- 端到端调度流程测试
- 大数据集性能测试
- 并发场景测试

### 3. 代码质量
- Type hints 100%覆盖
- Docstring 完整性
- Code review 流程

## 监控和日志

### 1. 日志策略
```python
import logging

# 配置分层日志
logger = logging.getLogger('test_scheduler')
logger.setLevel(logging.INFO)

# 关键事件记录
logger.info("调度开始执行")
logger.warning("发现资源冲突")
logger.error("调度失败")
```

### 2. 性能监控
- 调度耗时统计
- 内存使用监控
- 算法效率分析

## 部署架构

### 1. 单机部署
```
┌─────────────────┐
│   应用服务器      │
├─────────────────┤
│  调度系统核心     │
│  配置文件        │
│  日志系统        │
└─────────────────┘
```

### 2. 分布式部署
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Web 前端    │    │  API 服务   │    │  调度引擎    │
│             │◄──►│             │◄──►│             │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                            │
                            ▼
                   ┌─────────────┐
                   │  数据存储    │
                   │             │
                   └─────────────┘
```

## 总结

本架构设计实现了：
- ✅ **高内聚低耦合**：模块职责清晰，依赖关系简单
- ✅ **可扩展性**：新功能可通过扩展实现，无需修改核心代码
- ✅ **可测试性**：每个模块都可独立测试
- ✅ **可维护性**：代码结构清晰，文档完整
- ✅ **性能优化**：算法复杂度优化，内存使用高效
- ✅ **错误处理**：完善的异常处理和日志系统

这种架构设计为复杂的测试调度问题提供了一个稳定、高效、可扩展的解决方案。