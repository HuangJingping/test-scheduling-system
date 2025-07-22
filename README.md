# 测试调度系统 (Test Scheduling System)

一个专业的项目验收测试调度系统，支持基于时间和基于顺序的两种调度模式。

## 🚀 特性

- **双调度模式**：时间调度 + 序列调度
- **模块化架构**：10个专门模块，职责清晰
- **配置外置**：JSON配置文件，易于定制
- **智能约束**：资源约束、依赖关系、阶段约束
- **并行优化**：自动识别可并行执行的测试组
- **多种输出**：Excel报表、文本计划、控制台输出

## 📁 项目结构

```
acceptance-test-planner/
├── config.py                    # 配置管理模块
├── models.py                     # 数据模型类
├── time_manager.py              # 时间管理模块
├── constraints.py               # 约束检查模块
├── priority_calculator.py       # 优先级计算模块
├── scheduling_algorithm.py      # 调度算法核心
├── output_formatter.py          # 输出格式化模块
├── test_scheduler_refactored.py # 主调度器
├── sequence_scheduler.py        # 序列调度器
├── test_data.json              # 测试数据配置
├── scheduler_config.json        # 系统配置
└── demo_simple.py              # 演示脚本
```

## 🛠️ 安装依赖

```bash
pip install pandas numpy xlsxwriter
```

## 💡 快速开始

### 时间调度模式

```python
from test_scheduler_refactored import TestScheduler

# 创建调度器
scheduler = TestScheduler('scheduler_config.json')
scheduler.load_data_from_file('test_data.json')

# 执行调度
result = scheduler.solve_schedule(max_parallel=3)
```

### 序列调度模式（推荐）

```python
from sequence_scheduler import SequenceScheduler

# 创建序列调度器
scheduler = SequenceScheduler('scheduler_config.json')
scheduler.load_data_from_file('test_data.json')

# 生成执行序列
result = scheduler.generate_sequence()
```

### 快速演示

```bash
python demo_simple.py
```

## 📊 调度算法

### 优先级计算
- **依赖关系权重**：被依赖的测试项优先级更高
- **资源复杂度**：资源需求多的测试项优先
- **阶段顺序**：严格按测试阶段顺序执行
- **组连续性**：同组测试项保持连续性

### 约束检查
- **资源约束**：确保仪器设备不超载
- **依赖约束**：前置测试必须完成
- **阶段约束**：阶段间有严格顺序
- **并行约束**：控制最大并行数量

## 🎯 使用场景

### 1. 时间调度模式
- 适用于：时间估计相对准确的项目
- 输出：具体的时间安排和甘特图
- 特点：精确的时间管理

### 2. 序列调度模式（推荐）
- 适用于：时间估计不准确的项目
- 输出：测试执行顺序和并行建议
- 特点：关注逻辑顺序，不依赖时间估计

## 📈 系统优势

相比传统调度系统：

| 指标 | 传统系统 | 本系统 |
|-----|----------|--------|
| 代码结构 | 单文件1455行 | 模块化10个文件 |
| 重复代码 | 4个重复方法 | 0重复 |
| 配置方式 | 硬编码 | 外部JSON配置 |
| 错误处理 | 基本无 | 完善的日志和异常处理 |
| 测试能力 | 困难 | 每个模块独立测试 |
| 扩展性 | 几乎不可能 | 高度可扩展 |

## 🔧 配置文件

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
  "test_items": [
    {
      "test_id": 1,
      "test_phase": "专项测试1",
      "test_group": "系统",
      "test_item": "系统齐套性检查",
      "required_equipment": "无",
      "required_instruments": "无",
      "duration": 4
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

## 🧪 测试验证

```bash
# 运行基础功能测试
python basic_test.py

# 运行完整演示
python demo_simple.py

# 生成序列化计划
python sequence_scheduler.py
```

## 📝 输出格式

### Excel报表
- 详细调度表
- 阶段汇总
- 测试组汇总
- 统计信息

### 文本计划
- 测试执行顺序
- 并行执行建议
- 依赖关系说明
- 关键提醒事项

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 👨‍💻 作者

- 原始需求：项目验收测试调度优化
- 重构实现：模块化架构设计
- 算法优化：多约束条件下的智能调度

---

**让测试调度更智能，让项目管理更高效！** 🚀