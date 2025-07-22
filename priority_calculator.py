"""
优先级计算模块
负责计算测试项的调度优先级，支持多种优先级策略
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict
from models import TestItem, ScheduledTest, DependencyGraph, GroupPhase, PriorityScore
from config import PriorityWeights, SchedulingConfig
from constraints import ResourceMatrix


class PriorityCalculator:
    """优先级计算器"""
    
    def __init__(self, test_items: List[TestItem], dependency_graph: DependencyGraph,
                 resource_matrix: ResourceMatrix, priority_weights: PriorityWeights,
                 config: SchedulingConfig):
        self.test_items = test_items
        self.dependency_graph = dependency_graph
        self.resource_matrix = resource_matrix
        self.weights = priority_weights
        self.config = config
        
        # 创建阶段到索引的映射
        self.phases = list(set(item.test_phase for item in test_items))
        self.phase_to_index = {phase: idx for idx, phase in enumerate(self.phases)}
    
    def calculate_base_priority(self, test_idx: int) -> PriorityScore:
        """
        计算测试项的基础优先级
        
        Args:
            test_idx: 测试项索引
            
        Returns:
            PriorityScore: 优先级评分
        """
        if test_idx >= len(self.test_items):
            return PriorityScore(test_idx, 0, 0, 0, 0, 0)
        
        test_item = self.test_items[test_idx]
        
        # 1. 依赖关系评分（被依赖的测试项优先级更高）
        dependency_score = self.dependency_graph.get_dependencies_count(test_idx) * self.weights.dependency
        
        # 2. 持续时间评分（耗时长的优先级更高）
        duration_score = test_item.duration * self.weights.duration
        
        # 3. 资源需求评分（资源需求多的优先级更高）
        resource_usage = sum(self.resource_matrix.matrix[test_idx])
        resource_score = resource_usage * self.weights.resource
        
        # 4. 阶段评分（前面阶段优先级更高）
        phase_idx = self.phase_to_index.get(test_item.test_phase, len(self.phases))
        phase_score = (len(self.phases) - phase_idx) * self.weights.phase
        
        return PriorityScore(
            test_id=test_item.test_id,
            dependency_score=dependency_score,
            duration_score=duration_score,
            resource_score=resource_score,
            phase_score=phase_score,
            continuity_score=0  # 基础优先级不包含连续性评分
        )
    
    def calculate_continuity_priority(self, test_idx: int, active_group_phases: Set[GroupPhase],
                                    group_phase_priorities: Dict[GroupPhase, int] = None) -> float:
        """
        计算连续性优先级评分
        
        Args:
            test_idx: 测试项索引
            active_group_phases: 当前活跃的组-阶段组合
            group_phase_priorities: 组-阶段优先级排名
            
        Returns:
            float: 连续性评分
        """
        if test_idx >= len(self.test_items):
            return 0.0
        
        test_item = self.test_items[test_idx]
        if not test_item.test_group or test_item.test_group == '无':
            return 0.0
        
        group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
        
        # 如果是活跃的组-阶段，给予连续性加分
        if group_phase in active_group_phases:
            base_continuity = self.weights.continuity
            
            # 如果有组-阶段优先级排名，根据排名进一步调整
            if group_phase_priorities and group_phase in group_phase_priorities:
                priority_rank = group_phase_priorities[group_phase]
                # 优先级排名越低（数值越小），加分越多
                rank_bonus = self.weights.group_phase_boost * (10 - min(priority_rank, 9)) / 10
                return base_continuity + rank_bonus
            
            return base_continuity
        
        return 0.0
    
    def calculate_full_priority(self, test_idx: int, active_group_phases: Set[GroupPhase] = None,
                              group_phase_priorities: Dict[GroupPhase, int] = None,
                              completed_group_phases: Set[GroupPhase] = None) -> PriorityScore:
        """
        计算完整的优先级评分（包含连续性）
        
        Args:
            test_idx: 测试项索引
            active_group_phases: 当前活跃的组-阶段组合
            group_phase_priorities: 组-阶段优先级排名
            completed_group_phases: 已完成的组-阶段组合
            
        Returns:
            PriorityScore: 完整的优先级评分
        """
        # 计算基础优先级
        base_score = self.calculate_base_priority(test_idx)
        
        # 计算连续性优先级
        continuity_score = 0.0
        if active_group_phases:
            continuity_score = self.calculate_continuity_priority(
                test_idx, active_group_phases, group_phase_priorities
            )
        
        # 如果没有获得连续性加分，但有空闲槽位，给新组-阶段一定优先级
        if continuity_score == 0.0 and completed_group_phases:
            test_item = self.test_items[test_idx]
            if test_item.test_group and test_item.test_group != '无':
                group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
                if group_phase not in (active_group_phases or set()):
                    # 给新组-阶段适中的优先级，但低于活跃组-阶段
                    continuity_score = self.weights.continuity * 0.6
                    
                    # 根据组-阶段优先级进一步调整
                    if group_phase_priorities and group_phase in group_phase_priorities:
                        priority_rank = group_phase_priorities[group_phase]
                        rank_bonus = self.weights.group_phase_boost * 0.4 * (10 - min(priority_rank, 9)) / 10
                        continuity_score += rank_bonus
        
        # 更新连续性评分
        base_score.continuity_score = continuity_score
        
        return base_score


class GroupPhaseManager:
    """测试组-阶段管理器"""
    
    def __init__(self, test_items: List[TestItem], config: SchedulingConfig):
        self.test_items = test_items
        self.config = config
        self.group_phase_to_tests = self._build_group_phase_mapping()
    
    def _build_group_phase_mapping(self) -> Dict[GroupPhase, List[int]]:
        """构建组-阶段到测试项的映射"""
        mapping = defaultdict(list)
        for i, test_item in enumerate(self.test_items):
            if test_item.test_group and test_item.test_group != '无':
                group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
                mapping[group_phase].append(i)
        return dict(mapping)
    
    def get_all_group_phases(self) -> Set[GroupPhase]:
        """获取所有测试组-阶段组合"""
        return set(self.group_phase_to_tests.keys())
    
    def get_active_group_phases(self, active_tests: List[ScheduledTest]) -> Set[GroupPhase]:
        """获取当前活跃的测试组-阶段组合"""
        active_group_phases = set()
        for test in active_tests:
            if test.test_group and test.test_group != '无':
                group_phase = GroupPhase(test.test_group, test.test_phase)
                active_group_phases.add(group_phase)
        return active_group_phases
    
    def get_completed_group_phases(self, active_group_phases: Set[GroupPhase], 
                                 unscheduled_test_ids: Set[int]) -> Set[GroupPhase]:
        """获取已完成的测试组-阶段组合"""
        all_group_phases = self.get_all_group_phases()
        
        # 获取未调度测试项的组-阶段
        pending_group_phases = set()
        for test_id in unscheduled_test_ids:
            test_idx = next((i for i, item in enumerate(self.test_items) if item.test_id == test_id), None)
            if test_idx is not None:
                test_item = self.test_items[test_idx]
                if test_item.test_group and test_item.test_group != '无':
                    group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
                    pending_group_phases.add(group_phase)
        
        # 已完成的组-阶段 = 所有组-阶段 - 活跃组-阶段 - 有未调度测试项的组-阶段
        completed_group_phases = all_group_phases - active_group_phases - pending_group_phases
        return completed_group_phases
    
    def get_recently_completed_group_phases(self, scheduled_tests: List[ScheduledTest], 
                                          current_time: float, lookback: float = 8) -> List[Tuple[GroupPhase, float]]:
        """
        获取最近完成的测试组-阶段组合
        
        Args:
            scheduled_tests: 已调度的测试项
            current_time: 当前时间
            lookback: 回溯时间窗口（小时）
            
        Returns:
            List[Tuple[GroupPhase, float]]: 按完成时间排序的组-阶段列表
        """
        time_threshold = max(0, current_time - lookback)
        group_phase_completion_times = {}
        
        # 找出最近完成的测试
        for test in scheduled_tests:
            if (test.end_time > time_threshold and test.end_time <= current_time and
                test.test_group and test.test_group != '无'):
                
                group_phase = GroupPhase(test.test_group, test.test_phase)
                # 记录该组-阶段最大的完成时间
                group_phase_completion_times[group_phase] = max(
                    group_phase_completion_times.get(group_phase, 0),
                    test.end_time
                )
        
        # 按完成时间从最近到最远排序
        sorted_group_phases = sorted(
            group_phase_completion_times.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_group_phases
    
    def get_remaining_tests_by_group_phase(self, unscheduled_test_ids: Set[int]) -> Dict[GroupPhase, int]:
        """获取每个组-阶段的剩余测试项数量"""
        group_phase_remaining = defaultdict(int)
        for test_id in unscheduled_test_ids:
            test_idx = next((i for i, item in enumerate(self.test_items) if item.test_id == test_id), None)
            if test_idx is not None:
                test_item = self.test_items[test_idx]
                if test_item.test_group and test_item.test_group != '无':
                    group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
                    group_phase_remaining[group_phase] += 1
        return dict(group_phase_remaining)
    
    def create_group_phase_priorities(self, active_group_phases: Set[GroupPhase],
                                    completed_group_phases: Set[GroupPhase],
                                    recently_completed: List[Tuple[GroupPhase, float]],
                                    group_phase_remaining: Dict[GroupPhase, int]) -> Dict[GroupPhase, int]:
        """
        创建测试组-阶段组合优先级排序
        
        优先级策略:
        1. 当前活跃的组-阶段优先（保持连续性）
        2. 最近完成测试的组-阶段优先（接近完成的组-阶段）
        3. 已完成的组-阶段比未开始的组-阶段优先级低（避免频繁切换）
        4. 剩余测试项较少的组-阶段优先（更快完成整个组-阶段）
        
        Returns:
            Dict[GroupPhase, int]: 组-阶段优先级映射（数值越小优先级越高）
        """
        group_phase_priorities = {}
        priority_rank = 0
        
        # 1. 当前活跃的组-阶段（最高优先级）
        for group_phase in active_group_phases:
            if group_phase not in group_phase_priorities:
                group_phase_priorities[group_phase] = priority_rank
                priority_rank += 1
        
        # 2. 按最近完成时间排序的组-阶段
        for group_phase, _ in recently_completed:
            if group_phase not in group_phase_priorities:
                group_phase_priorities[group_phase] = priority_rank
                priority_rank += 1
        
        # 3. 已完成的组-阶段（中等优先级，可以开始新的组-阶段）
        for group_phase in completed_group_phases:
            if group_phase not in group_phase_priorities:
                group_phase_priorities[group_phase] = priority_rank
                priority_rank += 1
        
        # 4. 所有剩余组-阶段按剩余测试项数量排序（剩余少的优先）
        remaining_group_phases = sorted(
            [(gp, n) for gp, n in group_phase_remaining.items() if gp not in group_phase_priorities],
            key=lambda x: x[1]
        )
        
        for group_phase, _ in remaining_group_phases:
            group_phase_priorities[group_phase] = priority_rank
            priority_rank += 1
        
        return group_phase_priorities


class PriorityManager:
    """优先级管理器 - 统一管理优先级计算"""
    
    def __init__(self, test_items: List[TestItem], dependency_graph: DependencyGraph,
                 resource_matrix: ResourceMatrix, priority_weights: PriorityWeights,
                 config: SchedulingConfig):
        self.priority_calculator = PriorityCalculator(
            test_items, dependency_graph, resource_matrix, priority_weights, config
        )
        self.group_phase_manager = GroupPhaseManager(test_items, config)
    
    def get_prioritized_tests(self, unscheduled_test_ids: Set[int], 
                            active_tests: List[ScheduledTest],
                            scheduled_tests: List[ScheduledTest],
                            current_time: float) -> List[Tuple[int, PriorityScore]]:
        """
        获取按优先级排序的测试项列表
        
        Args:
            unscheduled_test_ids: 未调度的测试项ID集合
            active_tests: 当前活跃的测试项
            scheduled_tests: 已调度的测试项
            current_time: 当前时间
            
        Returns:
            List[Tuple[int, PriorityScore]]: 按优先级排序的(测试项索引, 优先级评分)列表
        """
        # 获取当前状态
        active_group_phases = self.group_phase_manager.get_active_group_phases(active_tests)
        completed_group_phases = self.group_phase_manager.get_completed_group_phases(
            active_group_phases, unscheduled_test_ids
        )
        recently_completed = self.group_phase_manager.get_recently_completed_group_phases(
            scheduled_tests, current_time
        )
        group_phase_remaining = self.group_phase_manager.get_remaining_tests_by_group_phase(
            unscheduled_test_ids
        )
        
        # 创建组-阶段优先级排序
        group_phase_priorities = self.group_phase_manager.create_group_phase_priorities(
            active_group_phases, completed_group_phases, recently_completed, group_phase_remaining
        )
        
        # 计算每个未调度测试项的优先级
        test_priorities = []
        for test_id in unscheduled_test_ids:
            test_idx = next((i for i, item in enumerate(self.priority_calculator.test_items) 
                           if item.test_id == test_id), None)
            if test_idx is not None:
                priority_score = self.priority_calculator.calculate_full_priority(
                    test_idx, active_group_phases, group_phase_priorities, completed_group_phases
                )
                test_priorities.append((test_idx, priority_score))
        
        # 按总优先级排序（降序）
        test_priorities.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return test_priorities