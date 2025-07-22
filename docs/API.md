# API 文档

## 概述

测试调度系统提供了完整的程序化接口，支持两种主要的调度模式和丰富的配置选项。本文档详细描述了所有公开API的使用方法。

## 快速开始

### 基本用法

```python
from test_scheduler_refactored import TestScheduler
from sequence_scheduler import SequenceScheduler

# 时间调度模式
scheduler = TestScheduler('scheduler_config.json')
scheduler.load_data_from_file('test_data.json')
result = scheduler.solve_schedule(max_parallel=3)

# 序列调度模式
seq_scheduler = SequenceScheduler('scheduler_config.json')
seq_scheduler.load_data_from_file('test_data.json')
sequence = seq_scheduler.generate_sequence()
```

## 核心API

### 1. TestScheduler (时间调度器)

#### 构造函数

```python
TestScheduler(config_file: str = None)
```

**参数**：
- `config_file` (str, 可选): 配置文件路径，默认使用内置配置

**示例**：
```python
# 使用默认配置
scheduler = TestScheduler()

# 使用自定义配置
scheduler = TestScheduler('my_config.json')
```

#### 数据加载

```python
load_data_from_file(data_file: str) -> None
```

**参数**：
- `data_file` (str): JSON格式的测试数据文件路径

**数据格式要求**：
```json
{
  "test_items": [
    {
      "test_id": 1,
      "test_phase": "系统测试",
      "test_group": "基础功能",
      "test_item": "系统启动测试",
      "required_equipment": "测试台",
      "required_instruments": "无",
      "duration": 2
    }
  ],
  "dependencies": {
    "测试项B": ["测试项A"]
  },
  "instruments": {
    "仪器名称": 数量
  }
}
```

**异常**：
- `FileNotFoundError`: 文件不存在
- `ValidationError`: 数据格式错误
- `CircularDependencyError`: 检测到循环依赖

#### 执行调度

```python
solve_schedule(max_parallel: int = None) -> SchedulingResult
```

**参数**：
- `max_parallel` (int, 可选): 最大并行执行数，覆盖配置文件设置

**返回值**：
- `SchedulingResult`: 调度结果对象

**示例**：
```python
# 使用配置文件中的并行度
result = scheduler.solve_schedule()

# 指定并行度
result = scheduler.solve_schedule(max_parallel=5)
```

#### 结果数据结构

```python
@dataclass
class SchedulingResult:
    success: bool                          # 调度是否成功
    schedule: List[ScheduledItem]          # 调度项列表
    total_duration: float                  # 总工期（小时）
    parallel_efficiency: float            # 并行效率
    phase_summary: Dict[str, int]          # 各阶段测试数量
    group_summary: Dict[str, int]          # 各测试组数量
    resource_utilization: Dict[str, float] # 资源利用率
    conflicts: List[Conflict]              # 冲突列表
    warnings: List[str]                    # 警告信息
```

```python
@dataclass
class ScheduledItem:
    test_id: int
    test_item: str
    test_phase: str
    test_group: str
    start_time: str                        # 格式："第X天Y.Z时"
    end_time: str
    duration: int
    required_equipment: str
    required_instruments: str
    dependencies: List[str]
    status: str                            # "scheduled" | "conflict" | "pending"
```

### 2. SequenceScheduler (序列调度器)

#### 构造函数

```python
SequenceScheduler(config_file: str = None)
```

参数与TestScheduler相同。

#### 生成执行序列

```python
generate_sequence() -> SequenceResult
```

**返回值**：
- `SequenceResult`: 序列调度结果

**示例**：
```python
result = scheduler.generate_sequence()
for item in result.sequence_items:
    print(f"{item.sequence_number}. {item.test_item}")
```

#### 序列结果数据结构

```python
@dataclass
class SequenceResult:
    sequence_items: List[SequenceItem]      # 序列项列表
    parallel_groups: List[List[int]]        # 可并行执行的测试组
    phase_boundaries: Dict[str, Tuple[int, int]]  # 各阶段的起止序号
    statistics: Dict[str, any]              # 统计信息
```

```python
@dataclass
class SequenceItem:
    sequence_number: int                    # 执行序号
    test_id: int
    test_item: str
    test_group: str
    test_phase: str
    priority_rank: int                      # 优先级排名
    dependency_level: int                   # 依赖层级
    resource_conflicts: List[str]           # 资源冲突项
```

### 3. 配置管理API

#### ConfigManager

```python
from config import ConfigManager

config_manager = ConfigManager('config.json')
config = config_manager.load_config()
```

#### 配置结构

```python
@dataclass
class SystemConfig:
    scheduling: SchedulingConfig
    working_time: WorkingTimeConfig
    priority_weights: PriorityWeights
    output: OutputConfig

@dataclass
class SchedulingConfig:
    max_parallel: int = 3
    max_parallel_per_phase: int = 3
    
@dataclass
class WorkingTimeConfig:
    hours_per_day: int = 8
    rest_day_cycle: int = 7
    
@dataclass
class PriorityWeights:
    dependency: int = 10
    duration: int = 2
    resource: int = 5
    phase: int = 20
    continuity: int = 50
```

### 4. 输出格式化API

#### OutputFormatter

```python
from output_formatter import OutputFormatter

formatter = OutputFormatter()
```

#### Excel输出

```python
export_to_excel(result: SchedulingResult, filename: str) -> bool
```

**参数**：
- `result`: 调度结果对象
- `filename`: 输出文件名

**返回值**：
- `bool`: 导出是否成功

**生成的表格**：
- **详细调度表**: 完整的测试项安排
- **阶段汇总**: 各测试阶段统计
- **测试组汇总**: 各测试组统计
- **统计信息**: 总体指标和效率分析

#### 文本输出

```python
export_to_text(result: SchedulingResult, filename: str) -> bool
```

生成简洁的文本格式执行计划。

#### JSON输出

```python
export_to_json(result: SchedulingResult, filename: str) -> bool
```

生成结构化的JSON数据，便于程序化处理。

### 5. 数据验证API

#### DataValidator

```python
from models import DataValidator

validator = DataValidator()
errors = validator.validate_test_items(test_data)
```

#### 验证方法

```python
validate_test_items(items: List[dict]) -> List[ValidationError]
validate_dependencies(deps: Dict[str, List[str]], items: List[dict]) -> List[ValidationError]
validate_instruments(instruments: Dict[str, int]) -> List[ValidationError]
```

#### 验证错误类型

```python
@dataclass
class ValidationError:
    field: str                             # 错误字段
    value: any                             # 错误值
    message: str                           # 错误描述
    error_type: str                        # 错误类型
```

## 高级用法

### 1. 自定义优先级计算

```python
from priority_calculator import PriorityCalculator

class CustomPriorityCalculator(PriorityCalculator):
    def calculate_priority(self, test_item: TestItem) -> float:
        # 自定义优先级逻辑
        base_priority = super().calculate_priority(test_item)
        
        # 添加自定义权重
        if test_item.test_group == "关键功能":
            base_priority += 100
            
        return base_priority

# 使用自定义计算器
scheduler = TestScheduler()
scheduler.priority_calculator = CustomPriorityCalculator(config)
```

### 2. 自定义约束检查

```python
from constraints import ConstraintChecker

class CustomConstraintChecker(ConstraintChecker):
    def check_custom_constraint(self, test_item: TestItem, 
                                scheduled_items: List[ScheduledItem]) -> bool:
        # 自定义约束逻辑
        # 例如：检查团队可用性
        if test_item.test_group == "性能测试" and self.is_weekend():
            return False
        return True

# 使用自定义约束检查器
scheduler.constraint_checker = CustomConstraintChecker()
```

### 3. 批量处理

```python
def batch_schedule(data_files: List[str], config_file: str) -> List[SchedulingResult]:
    """批量处理多个测试数据文件"""
    results = []
    scheduler = TestScheduler(config_file)
    
    for data_file in data_files:
        scheduler.load_data_from_file(data_file)
        result = scheduler.solve_schedule()
        results.append(result)
        
        # 导出结果
        formatter = OutputFormatter()
        output_file = f"schedule_{Path(data_file).stem}.xlsx"
        formatter.export_to_excel(result, output_file)
        
    return results
```

### 4. 实时监控

```python
class SchedulingMonitor:
    def __init__(self):
        self.callbacks = []
    
    def add_callback(self, callback):
        self.callbacks.append(callback)
    
    def on_schedule_start(self, test_count: int):
        for callback in self.callbacks:
            callback.on_start(test_count)
    
    def on_item_scheduled(self, item: ScheduledItem):
        for callback in self.callbacks:
            callback.on_progress(item)
    
    def on_schedule_complete(self, result: SchedulingResult):
        for callback in self.callbacks:
            callback.on_complete(result)

# 使用监控器
monitor = SchedulingMonitor()
monitor.add_callback(ProgressLogger())
scheduler.set_monitor(monitor)
```

## 异常处理

### 异常类型

```python
class SchedulingError(Exception):
    """调度基础异常"""
    pass

class CircularDependencyError(SchedulingError):
    """循环依赖异常"""
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"检测到循环依赖: {' -> '.join(cycle)}")

class ResourceConflictError(SchedulingError):
    """资源冲突异常"""
    def __init__(self, resource: str, conflicts: List[str]):
        self.resource = resource
        self.conflicts = conflicts
        super().__init__(f"资源 {resource} 冲突: {conflicts}")

class ValidationError(SchedulingError):
    """数据验证异常"""
    def __init__(self, errors: List[dict]):
        self.errors = errors
        super().__init__(f"数据验证失败: {len(errors)} 个错误")
```

### 异常处理示例

```python
try:
    scheduler = TestScheduler('config.json')
    scheduler.load_data_from_file('test_data.json')
    result = scheduler.solve_schedule()
    
except CircularDependencyError as e:
    print(f"依赖关系错误: {e.cycle}")
    # 处理循环依赖
    
except ResourceConflictError as e:
    print(f"资源冲突: {e.resource}")
    # 处理资源冲突
    
except ValidationError as e:
    print("数据验证失败:")
    for error in e.errors:
        print(f"  {error['field']}: {error['message']}")
        
except FileNotFoundError as e:
    print(f"文件不存在: {e.filename}")
    
except Exception as e:
    print(f"未知错误: {str(e)}")
```

## 性能优化

### 1. 大数据集处理

```python
# 对于大数据集，使用流式处理
def process_large_dataset(data_file: str, chunk_size: int = 100):
    scheduler = TestScheduler()
    
    # 分批加载数据
    for chunk in load_data_in_chunks(data_file, chunk_size):
        scheduler.load_data_from_dict(chunk)
        partial_result = scheduler.solve_schedule()
        yield partial_result
```

### 2. 并行处理

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class ParallelScheduler:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.lock = threading.Lock()
    
    def schedule_parallel(self, data_files: List[str]) -> List[SchedulingResult]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for data_file in data_files:
                future = executor.submit(self._schedule_single, data_file)
                futures.append(future)
            
            results = []
            for future in futures:
                results.append(future.result())
            
            return results
    
    def _schedule_single(self, data_file: str) -> SchedulingResult:
        scheduler = TestScheduler()
        scheduler.load_data_from_file(data_file)
        return scheduler.solve_schedule()
```

### 3. 缓存优化

```python
from functools import lru_cache
import hashlib

class CachedScheduler(TestScheduler):
    def __init__(self, config_file: str = None):
        super().__init__(config_file)
        self._cache = {}
    
    def solve_schedule(self, max_parallel: int = None) -> SchedulingResult:
        # 计算数据指纹
        data_hash = self._calculate_data_hash()
        cache_key = f"{data_hash}_{max_parallel}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = super().solve_schedule(max_parallel)
        self._cache[cache_key] = result
        return result
    
    def _calculate_data_hash(self) -> str:
        data_str = json.dumps({
            'test_items': [item.__dict__ for item in self.test_items],
            'dependencies': self.dependency_graph.dependencies,
            'instruments': self.instruments
        }, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
```

## 集成示例

### 1. Web API 集成

```python
from flask import Flask, request, jsonify
import tempfile
import os

app = Flask(__name__)

@app.route('/api/schedule', methods=['POST'])
def api_schedule():
    try:
        data = request.get_json()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_file = f.name
        
        try:
            # 执行调度
            scheduler = TestScheduler()
            scheduler.load_data_from_file(temp_file)
            result = scheduler.solve_schedule()
            
            # 转换为JSON响应
            response = {
                'success': result.success,
                'total_duration': result.total_duration,
                'schedule': [item.__dict__ for item in result.schedule],
                'statistics': {
                    'total_tests': len(result.schedule),
                    'parallel_efficiency': result.parallel_efficiency,
                    'phase_summary': result.phase_summary
                }
            }
            
            return jsonify(response)
            
        finally:
            os.unlink(temp_file)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
```

### 2. 命令行工具

```python
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description='测试调度系统')
    parser.add_argument('data_file', help='测试数据文件')
    parser.add_argument('--config', default='scheduler_config.json', help='配置文件')
    parser.add_argument('--mode', choices=['time', 'sequence'], default='time', help='调度模式')
    parser.add_argument('--parallel', type=int, help='最大并行数')
    parser.add_argument('--output', default='schedule_result.xlsx', help='输出文件')
    parser.add_argument('--format', choices=['excel', 'json', 'text'], default='excel', help='输出格式')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'time':
            scheduler = TestScheduler(args.config)
            scheduler.load_data_from_file(args.data_file)
            result = scheduler.solve_schedule(args.parallel)
        else:
            scheduler = SequenceScheduler(args.config)
            scheduler.load_data_from_file(args.data_file)
            result = scheduler.generate_sequence()
        
        # 输出结果
        formatter = OutputFormatter()
        if args.format == 'excel':
            formatter.export_to_excel(result, args.output)
        elif args.format == 'json':
            formatter.export_to_json(result, args.output)
        else:
            formatter.export_to_text(result, args.output)
        
        print(f"调度完成，结果已保存到 {args.output}")
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

## 最佳实践

### 1. 配置管理
- 将业务参数外置到配置文件
- 使用环境变量管理敏感配置
- 提供配置模板和验证

### 2. 错误处理
- 使用具体的异常类型
- 提供详细的错误信息
- 实现优雅的降级策略

### 3. 性能优化
- 对大数据集使用分批处理
- 缓存重复计算结果
- 使用并行处理提高效率

### 4. 日志记录
- 记录关键操作和决策点
- 使用结构化日志格式
- 实现日志级别控制

### 5. 测试策略
- 编写全面的单元测试
- 使用真实数据进行集成测试
- 实现性能基准测试

这套API设计为测试调度系统提供了完整、灵活、易用的编程接口，支持各种使用场景和集成需求。