"""
约束检查模块
负责检查各种调度约束：资源约束、依赖关系、阶段约束、测试组约束等
"""
from typing import List, Dict, Tuple, Set
import numpy as np
import re
from models import TestItem, ScheduledTest, DependencyGraph, GroupPhase, SchedulingState
from config import SchedulingConfig


class ResourceMatrix:
    """资源需求矩阵管理器"""
    
    def __init__(self, test_items: List[TestItem], instruments: Dict[str, int]):
        self.test_items = test_items
        self.instruments = instruments
        self.instrument_names = list(instruments.keys())
        self.matrix = self._create_resource_matrix()
    
    def _create_resource_matrix(self) -> np.ndarray:
        """创建资源需求矩阵"""
        n_tests = len(self.test_items)
        n_instruments = len(self.instrument_names)
        matrix = np.zeros((n_tests, n_instruments))
        
        for i, test_item in enumerate(self.test_items):
            if test_item.required_instruments and test_item.required_instruments != '无':
                for item in test_item.required_instruments.split(','):
                    item = item.strip()
                    match = re.match(r'(.*?)×(\d+)', item)
                    if match:
                        resource_name = match.group(1).strip()
                        quantity = int(match.group(2))
                        if resource_name in self.instrument_names:
                            j = self.instrument_names.index(resource_name)
                            matrix[i][j] = quantity
        
        return matrix
    
    def get_resource_usage(self, test_idx: int) -> Dict[str, int]:
        """获取测试项的资源需求"""
        if test_idx >= len(self.test_items):
            return {}
        
        usage = {}
        for j, instrument_name in enumerate(self.instrument_names):
            required = int(self.matrix[test_idx][j])
            if required > 0:
                usage[instrument_name] = required
        
        return usage


class ConstraintChecker:
    """约束检查器"""
    
    def __init__(self, test_items: List[TestItem], instruments: Dict[str, int], 
                 dependency_graph: DependencyGraph, config: SchedulingConfig):
        self.test_items = test_items
        self.instruments = instruments
        self.dependency_graph = dependency_graph
        self.config = config
        self.resource_matrix = ResourceMatrix(test_items, instruments)
        
        # 创建测试项索引映射
        self.test_id_to_index = {item.test_id: i for i, item in enumerate(test_items)}
        
        # 按阶段分组测试项
        self.phase_to_tests = self._group_tests_by_phase()
        self.phase_order = self._determine_phase_order()
    
    def _group_tests_by_phase(self) -> Dict[str, List[int]]:
        """按阶段分组测试项"""
        phase_groups = {}
        for i, test_item in enumerate(self.test_items):
            phase = test_item.test_phase
            if phase not in phase_groups:
                phase_groups[phase] = []
            phase_groups[phase].append(i)
        return phase_groups
    
    def _determine_phase_order(self) -> List[str]:
        """确定阶段顺序"""
        # 根据原代码的阶段顺序
        preferred_order = [
            "专项测试1（资料查询、设备级、单节点测试，小场地）",
            "专项测试2（节点间互联，小场地）", 
            "专项测试3（大场地）",
            "车辆集成测试",
            "系统性能测试",
            "使用及适应性测试",
            "靶场测试"
        ]
        
        # 只包含实际存在的阶段
        actual_phases = set(self.phase_to_tests.keys())
        return [phase for phase in preferred_order if phase in actual_phases]
    
    def check_resource_constraint(self, test_idx: int, current_time: float, 
                                active_tests: List[ScheduledTest]) -> Tuple[bool, str]:
        """
        检查资源约束
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            active_tests: 当前活跃的测试项
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if test_idx >= len(self.test_items):
            return False, "测试项索引超出范围"
        
        # 计算当前资源使用情况
        current_usage = {}
        for instrument_name in self.instruments.keys():
            current_usage[instrument_name] = 0
        
        # 累计活跃测试的资源使用
        for test in active_tests:
            if test.start_time <= current_time < test.end_time:
                test_index = self.test_id_to_index.get(test.test_id)
                if test_index is not None:
                    for j, instrument_name in enumerate(self.resource_matrix.instrument_names):
                        current_usage[instrument_name] += int(self.resource_matrix.matrix[test_index][j])
        
        # 检查新测试项的资源需求
        for j, instrument_name in enumerate(self.resource_matrix.instrument_names):
            required = int(self.resource_matrix.matrix[test_idx][j])
            available = self.instruments[instrument_name]
            
            if current_usage[instrument_name] + required > available:
                return False, f"仪器 {instrument_name} 资源不足 (需要{required}, 可用{available - current_usage[instrument_name]})"
        
        return True, "资源约束满足"
    
    def check_dependency_constraint(self, test_idx: int, current_time: float, 
                                  scheduled_tests: List[ScheduledTest]) -> Tuple[bool, str]:
        """
        检查依赖关系约束
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            scheduled_tests: 已调度的测试项
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if not self.dependency_graph.check_dependencies_satisfied(test_idx, scheduled_tests, current_time):
            test_item = self.test_items[test_idx]
            return False, f"测试项 {test_item.test_item} 的依赖关系未满足"
        
        return True, "依赖关系约束满足"
    
    def check_phase_constraint(self, test_idx: int, current_time: float, 
                             scheduled_tests: List[ScheduledTest]) -> Tuple[bool, str]:
        """
        检查阶段约束（前面阶段必须完成）
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            scheduled_tests: 已调度的测试项
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if test_idx >= len(self.test_items):
            return False, "测试项索引超出范围"
        
        test_phase = self.test_items[test_idx].test_phase
        
        # 获取当前阶段在顺序中的位置
        if test_phase not in self.phase_order:
            return True, "未知阶段，跳过阶段约束检查"
        
        current_phase_idx = self.phase_order.index(test_phase)
        
        # 检查前面所有阶段是否都已完成
        for prev_phase_idx in range(current_phase_idx):
            prev_phase = self.phase_order[prev_phase_idx]
            prev_phase_tests = self.phase_to_tests.get(prev_phase, [])
            
            # 检查前一阶段的测试项是否都已经被调度且完成
            for prev_test_idx in prev_phase_tests:
                prev_test_id = self.test_items[prev_test_idx].test_id
                prev_test = next(
                    (test for test in scheduled_tests if test.test_id == prev_test_id),
                    None
                )
                if not prev_test or prev_test.end_time > current_time:
                    prev_phase_name = prev_phase
                    return False, f"前置阶段 '{prev_phase_name}' 未完成"
        
        return True, "阶段约束满足"
    
    def check_group_constraint(self, test_idx: int, current_time: float, 
                             active_tests: List[ScheduledTest]) -> Tuple[bool, str]:
        """
        检查测试组约束（同组测试项不能同时进行）
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            active_tests: 当前活跃的测试项
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if test_idx >= len(self.test_items):
            return False, "测试项索引超出范围"
        
        test_group = self.test_items[test_idx].test_group
        
        # 如果没有测试组，跳过约束检查
        if not test_group or test_group == '无':
            return True, "无测试组，跳过组约束检查"
        
        # 检查是否有同组的测试项正在进行
        for test in active_tests:
            if test.start_time <= current_time < test.end_time:
                test_index = self.test_id_to_index.get(test.test_id)
                if test_index is not None:
                    active_test_group = self.test_items[test_index].test_group
                    if active_test_group == test_group:
                        return False, f"测试组 '{test_group}' 已有测试项在进行中"
        
        return True, "测试组约束满足"
    
    def check_parallel_constraint(self, current_parallel_count: int) -> Tuple[bool, str]:
        """
        检查并行度约束
        
        Args:
            current_parallel_count: 当前并行测试数量
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if current_parallel_count >= self.config.max_parallel:
            return False, f"已达到最大并行数 {self.config.max_parallel}"
        
        return True, "并行度约束满足"
    
    def check_phase_parallel_constraint(self, test_idx: int, current_time: float,
                                      active_tests: List[ScheduledTest]) -> Tuple[bool, str]:
        """
        检查阶段并行度约束（每个阶段最多允许指定数量的测试组并行）
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            active_tests: 当前活跃的测试项
            
        Returns:
            Tuple[bool, str]: (是否满足约束, 原因)
        """
        if test_idx >= len(self.test_items):
            return False, "测试项索引超出范围"
        
        test_phase = self.test_items[test_idx].test_phase
        test_group = self.test_items[test_idx].test_group
        
        if not test_group or test_group == '无':
            return True, "无测试组，跳过阶段并行约束检查"
        
        # 统计当前阶段活跃的测试组数量
        active_groups_in_phase = set()
        for test in active_tests:
            if test.start_time <= current_time < test.end_time and test.test_phase == test_phase:
                test_index = self.test_id_to_index.get(test.test_id)
                if test_index is not None:
                    active_test_group = self.test_items[test_index].test_group
                    if active_test_group and active_test_group != '无':
                        active_groups_in_phase.add(active_test_group)
        
        # 如果当前组已经在活跃组中，允许添加
        if test_group in active_groups_in_phase:
            return True, "测试组已在当前阶段活跃"
        
        # 检查是否超过每阶段最大并行组数
        if len(active_groups_in_phase) >= self.config.max_parallel_per_phase:
            return False, f"阶段 '{test_phase}' 已达到最大并行组数 {self.config.max_parallel_per_phase}"
        
        return True, "阶段并行约束满足"
    
    def check_all_constraints(self, test_idx: int, current_time: float, 
                            state: SchedulingState) -> Tuple[bool, List[str]]:
        """
        检查所有约束
        
        Args:
            test_idx: 测试项索引
            current_time: 当前时间
            state: 调度状态
            
        Returns:
            Tuple[bool, List[str]]: (是否满足所有约束, 不满足的约束原因列表)
        """
        failed_constraints = []
        
        # 检查并行度约束
        satisfied, reason = self.check_parallel_constraint(len(state.active_tests))
        if not satisfied:
            failed_constraints.append(reason)
        
        # 检查资源约束
        satisfied, reason = self.check_resource_constraint(test_idx, current_time, state.active_tests)
        if not satisfied:
            failed_constraints.append(reason)
        
        # 检查依赖关系约束
        satisfied, reason = self.check_dependency_constraint(test_idx, current_time, state.scheduled_tests)
        if not satisfied:
            failed_constraints.append(reason)
        
        # 检查阶段约束
        satisfied, reason = self.check_phase_constraint(test_idx, current_time, state.scheduled_tests)
        if not satisfied:
            failed_constraints.append(reason)
        
        # 检查测试组约束
        satisfied, reason = self.check_group_constraint(test_idx, current_time, state.active_tests)
        if not satisfied:
            failed_constraints.append(reason)
        
        # 检查阶段并行约束
        satisfied, reason = self.check_phase_parallel_constraint(test_idx, current_time, state.active_tests)
        if not satisfied:
            failed_constraints.append(reason)
        
        return len(failed_constraints) == 0, failed_constraints