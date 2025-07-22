"""
测试调度系统数据模型
定义所有核心数据结构，使用dataclass确保类型安全
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from enum import Enum


class TestPhase(Enum):
    """测试阶段枚举"""
    PHASE_1 = "专项测试1（资料查询、设备级、单节点测试，小场地）"
    PHASE_2 = "专项测试2（节点间互联，小场地）"
    PHASE_3 = "专项测试3（大场地）"
    INTEGRATION = "车辆集成测试"
    SYSTEM_PERFORMANCE = "系统性能测试"
    USABILITY = "使用及适应性测试"
    RANGE_TEST = "靶场测试"


@dataclass
class TestItem:
    """测试项数据模型"""
    test_id: int
    test_phase: str
    test_group: str
    test_item: str
    required_equipment: str
    required_instruments: str
    duration: int  # 小时
    
    def __post_init__(self):
        """数据验证"""
        if self.duration <= 0:
            raise ValueError(f"测试项 {self.test_id} 的持续时间必须大于0")
        if not self.test_item:
            raise ValueError(f"测试项 {self.test_id} 的测试项目不能为空")


@dataclass
class Instrument:
    """仪器设备模型"""
    name: str
    count: int
    
    def __post_init__(self):
        if self.count <= 0:
            raise ValueError(f"仪器 {self.name} 的数量必须大于0")


@dataclass
class ScheduledTest:
    """已调度的测试项模型"""
    test_id: int
    test_item: str
    test_group: str
    test_phase: str
    start_time: float  # 小时
    duration: int      # 小时
    end_time: float    # 小时
    
    def __post_init__(self):
        if self.end_time != self.start_time + self.duration:
            self.end_time = self.start_time + self.duration


@dataclass
class ResourceUsage:
    """资源使用情况模型"""
    instrument_name: str
    required_count: int
    available_count: int
    usage_percentage: float = field(init=False)
    
    def __post_init__(self):
        if self.available_count == 0:
            self.usage_percentage = 100.0 if self.required_count > 0 else 0.0
        else:
            self.usage_percentage = min(100.0, (self.required_count / self.available_count) * 100)


@dataclass
class GroupPhase:
    """测试组-阶段组合模型"""
    group: str
    phase: str
    
    def __hash__(self):
        return hash((self.group, self.phase))
    
    def __eq__(self, other):
        if not isinstance(other, GroupPhase):
            return False
        return self.group == other.group and self.phase == other.phase


@dataclass
class SchedulingState:
    """调度状态模型"""
    current_time: float
    active_tests: List[ScheduledTest] = field(default_factory=list)
    scheduled_tests: List[ScheduledTest] = field(default_factory=list)
    unscheduled_test_ids: Set[int] = field(default_factory=set)
    active_group_phases: Set[GroupPhase] = field(default_factory=set)
    
    def add_scheduled_test(self, test: ScheduledTest):
        """添加已调度的测试"""
        self.scheduled_tests.append(test)
        self.active_tests.append(test)
        self.unscheduled_test_ids.discard(test.test_id)
        
        # 更新活跃组-阶段
        if test.test_group:
            group_phase = GroupPhase(test.test_group, test.test_phase)
            self.active_group_phases.add(group_phase)
    
    def update_active_tests(self, current_time: float):
        """更新活跃测试列表"""
        self.current_time = current_time
        # 移除已完成的测试
        completed_tests = [test for test in self.active_tests if test.end_time <= current_time]
        self.active_tests = [test for test in self.active_tests if test.end_time > current_time]
        
        # 更新活跃组-阶段
        self.active_group_phases = set()
        for test in self.active_tests:
            if test.test_group:
                group_phase = GroupPhase(test.test_group, test.test_phase)
                self.active_group_phases.add(group_phase)
        
        return completed_tests


@dataclass
class SchedulingResult:
    """调度结果模型"""
    scheduled_tests: List[ScheduledTest]
    total_duration: float  # 总完工时间（小时）
    statistics: Dict[str, any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.scheduled_tests:
            self.total_duration = max(test.end_time for test in self.scheduled_tests)
        else:
            self.total_duration = 0.0


@dataclass
class PriorityScore:
    """优先级评分模型"""
    test_id: int
    dependency_score: float = 0.0
    duration_score: float = 0.0
    resource_score: float = 0.0
    phase_score: float = 0.0
    continuity_score: float = 0.0
    total_score: float = field(init=False)
    
    def __post_init__(self):
        self.total_score = (
            self.dependency_score + 
            self.duration_score + 
            self.resource_score + 
            self.phase_score + 
            self.continuity_score
        )


@dataclass
class DependencyGraph:
    """依赖关系图模型"""
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    item_to_index: Dict[str, int] = field(default_factory=dict)
    dependency_matrix: List[List[int]] = field(default_factory=list)
    
    def build_matrix(self, test_items: List[TestItem]):
        """构建依赖关系矩阵"""
        n = len(test_items)
        self.item_to_index = {item.test_item: i for i, item in enumerate(test_items)}
        self.dependency_matrix = [[0] * n for _ in range(n)]
        
        for item, deps in self.dependencies.items():
            if item in self.item_to_index:
                i = self.item_to_index[item]
                for dep in deps:
                    if dep in self.item_to_index:
                        j = self.item_to_index[dep]
                        self.dependency_matrix[i][j] = 1
    
    def get_dependencies_count(self, test_idx: int) -> int:
        """获取测试项的被依赖数量"""
        if test_idx >= len(self.dependency_matrix):
            return 0
        return sum(self.dependency_matrix[i][test_idx] for i in range(len(self.dependency_matrix)))
    
    def check_dependencies_satisfied(self, test_idx: int, scheduled_tests: List[ScheduledTest], current_time: float) -> bool:
        """检查依赖关系是否满足"""
        if test_idx >= len(self.dependency_matrix):
            return True
            
        for j in range(len(self.dependency_matrix)):
            if self.dependency_matrix[test_idx][j] == 1:
                # 查找依赖的测试项是否已完成
                dependent_test = next(
                    (test for test in scheduled_tests if test.test_id == j + 1),  # test_id从1开始
                    None
                )
                if not dependent_test or dependent_test.end_time > current_time:
                    return False
        return True


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def validate_test_items(test_items: List[TestItem]) -> List[str]:
        """验证测试项数据"""
        errors = []
        
        # 检查ID唯一性
        test_ids = [item.test_id for item in test_items]
        if len(test_ids) != len(set(test_ids)):
            errors.append("测试项ID存在重复")
        
        # 检查必填字段
        for item in test_items:
            if not item.test_item.strip():
                errors.append(f"测试项 {item.test_id} 的测试项目名称不能为空")
            if item.duration <= 0:
                errors.append(f"测试项 {item.test_id} 的持续时间必须大于0")
        
        return errors
    
    @staticmethod
    def validate_instruments(instruments: Dict[str, int]) -> List[str]:
        """验证仪器设备数据"""
        errors = []
        
        for name, count in instruments.items():
            if not name.strip():
                errors.append("仪器名称不能为空")
            if count <= 0:
                errors.append(f"仪器 {name} 的数量必须大于0")
        
        return errors
    
    @staticmethod
    def validate_dependencies(dependencies: Dict[str, List[str]], test_items: List[TestItem]) -> List[str]:
        """验证依赖关系数据"""
        errors = []
        test_item_names = {item.test_item for item in test_items}
        
        for item, deps in dependencies.items():
            if item not in test_item_names:
                errors.append(f"依赖关系中的测试项 '{item}' 不存在")
            
            for dep in deps:
                if dep not in test_item_names:
                    errors.append(f"依赖关系中的测试项 '{dep}' 不存在")
        
        return errors