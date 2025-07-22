"""
调度算法核心模块
实现基于优先级规则的测试调度算法
"""
from typing import List, Set, Tuple, Optional, Dict
import logging
from models import (TestItem, ScheduledTest, SchedulingState, SchedulingResult, 
                   DependencyGraph, GroupPhase)
from config import SchedulingConfig, WorkingTimeConfig
from time_manager import WorkingTimeManager, TimeConstraintChecker
from constraints import ConstraintChecker
from priority_calculator import PriorityManager


class SchedulingAlgorithm:
    """调度算法实现"""
    
    def __init__(self, test_items: List[TestItem], instruments: Dict[str, int],
                 dependency_graph: DependencyGraph, config: SchedulingConfig,
                 working_time_config: WorkingTimeConfig, priority_manager: PriorityManager):
        self.test_items = test_items
        self.instruments = instruments
        self.dependency_graph = dependency_graph
        self.config = config
        self.working_time_config = working_time_config
        self.priority_manager = priority_manager
        
        # 初始化子组件
        self.time_manager = WorkingTimeManager(working_time_config)
        self.time_constraint_checker = TimeConstraintChecker(working_time_config)
        self.constraint_checker = ConstraintChecker(
            test_items, instruments, dependency_graph, config
        )
        
        # 创建测试项ID到索引的映射
        self.test_id_to_index = {item.test_id: i for i, item in enumerate(test_items)}
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
    
    def solve(self) -> SchedulingResult:
        """
        执行调度算法
        
        Returns:
            SchedulingResult: 调度结果
        """
        self.logger.info("开始执行测试调度算法")
        
        # 初始化调度状态
        state = SchedulingState(
            current_time=0.0,
            unscheduled_test_ids={item.test_id for item in self.test_items}
        )
        
        # 主调度循环
        iteration_count = 0
        max_iterations = len(self.test_items) * 100  # 防止无限循环
        
        while state.unscheduled_test_ids and iteration_count < max_iterations:
            iteration_count += 1
            
            # 更新活跃测试列表
            completed_tests = state.update_active_tests(state.current_time)
            if completed_tests:
                self.logger.debug(f"时间 {state.current_time}: 完成了 {len(completed_tests)} 个测试项")
            
            # 如果当前时间是休息日，移动到下一个工作日
            if self.time_manager.is_rest_day(state.current_time):
                state.current_time = self.time_manager.get_next_working_day_start(state.current_time)
                continue
            
            # 尝试调度新的测试项
            scheduled_count = self._schedule_tests_at_current_time(state)
            
            # 如果没有调度任何测试项，移动时间
            if scheduled_count == 0:
                state.current_time = self._get_next_time_point(state)
        
        if iteration_count >= max_iterations:
            self.logger.warning("调度算法达到最大迭代次数，可能存在无法调度的测试项")
        
        # 计算调度结果
        result = self._create_scheduling_result(state)
        self.logger.info(f"调度算法完成，共调度 {len(result.scheduled_tests)} 个测试项")
        
        return result
    
    def _schedule_tests_at_current_time(self, state: SchedulingState) -> int:
        """
        在当前时间点尝试调度测试项
        
        Args:
            state: 调度状态
            
        Returns:
            int: 成功调度的测试项数量
        """
        scheduled_count = 0
        
        # 获取当前工作日剩余时间
        remaining_hours = self.time_manager.get_remaining_hours_in_day(state.current_time)
        
        # 获取按优先级排序的测试项
        prioritized_tests = self.priority_manager.get_prioritized_tests(
            state.unscheduled_test_ids,
            state.active_tests,
            state.scheduled_tests,
            state.current_time
        )
        
        # 将测试项按类型分组
        eligible_groups = self._categorize_eligible_tests(
            prioritized_tests, state.active_tests, remaining_hours
        )
        
        # 按优先级顺序尝试调度
        for test_group in eligible_groups:
            if len(state.active_tests) >= self.config.max_parallel:
                break
            
            scheduled_in_group = self._schedule_test_group(test_group, state)
            scheduled_count += scheduled_in_group
        
        return scheduled_count
    
    def _categorize_eligible_tests(self, prioritized_tests: List[Tuple[int, any]], 
                                 active_tests: List[ScheduledTest], 
                                 remaining_hours: float) -> List[List[Tuple[int, any]]]:
        """
        将测试项按优先级类型分组
        
        Args:
            prioritized_tests: 按优先级排序的测试项
            active_tests: 当前活跃测试项
            remaining_hours: 当前工作日剩余时间
            
        Returns:
            List[List[Tuple[int, any]]]: 分组后的测试项列表
        """
        # 获取当前活跃的组-阶段
        active_group_phases = set()
        for test in active_tests:
            if test.test_group and test.test_group != '无':
                group_phase = GroupPhase(test.test_group, test.test_phase)
                active_group_phases.add(group_phase)
        
        # 分组
        active_group_tests = []      # 活跃组-阶段的测试项（最高优先级）
        new_group_tests = []         # 新组-阶段的测试项（中等优先级）
        other_tests = []             # 其他测试项（最低优先级）
        
        available_slots = self.config.max_parallel - len(active_tests)
        
        for test_idx, priority_score in prioritized_tests:
            test_item = self.test_items[test_idx]
            test_duration = test_item.duration
            
            # 检查测试时长与工作日剩余时间
            is_eligible = True
            if test_duration <= self.working_time_config.short_test_threshold:
                # 短测试项只有在剩余时间足够时才考虑调度
                if test_duration > remaining_hours:
                    is_eligible = False
            
            if not is_eligible:
                continue
            
            # 按组-阶段类型分组
            if test_item.test_group and test_item.test_group != '无':
                group_phase = GroupPhase(test_item.test_group, test_item.test_phase)
                
                if group_phase in active_group_phases:
                    # 活跃组-阶段测试项
                    active_group_tests.append((test_idx, priority_score))
                elif available_slots > 0:
                    # 新组-阶段测试项（需要有空闲槽位）
                    new_group_tests.append((test_idx, priority_score))
                else:
                    # 没有空闲槽位的新组测试项
                    other_tests.append((test_idx, priority_score))
            else:
                # 无组测试项
                other_tests.append((test_idx, priority_score))
        
        # 返回优先级排序的分组
        groups = []
        if active_group_tests:
            groups.append(active_group_tests)
        if new_group_tests:
            groups.append(new_group_tests)
        if other_tests:
            groups.append(other_tests)
        
        return groups
    
    def _schedule_test_group(self, test_group: List[Tuple[int, any]], 
                           state: SchedulingState) -> int:
        """
        调度一组测试项
        
        Args:
            test_group: 测试项组
            state: 调度状态
            
        Returns:
            int: 成功调度的测试项数量
        """
        scheduled_count = 0
        
        for test_idx, priority_score in test_group:
            if len(state.active_tests) >= self.config.max_parallel:
                break
            
            if self._try_schedule_test(test_idx, state):
                scheduled_count += 1
        
        return scheduled_count
    
    def _try_schedule_test(self, test_idx: int, state: SchedulingState) -> bool:
        """
        尝试调度单个测试项
        
        Args:
            test_idx: 测试项索引
            state: 调度状态
            
        Returns:
            bool: 是否成功调度
        """
        test_item = self.test_items[test_idx]
        
        # 检查时间约束
        optimal_start_time = self.time_constraint_checker.get_optimal_start_time(
            state.current_time, test_item.duration
        )
        
        # 如果最优开始时间不是当前时间，跳过
        if optimal_start_time > state.current_time:
            return False
        
        # 检查所有约束
        can_schedule, failed_constraints = self.constraint_checker.check_all_constraints(
            test_idx, state.current_time, state
        )
        
        if not can_schedule:
            self.logger.debug(f"测试项 {test_item.test_item} 无法调度: {failed_constraints}")
            return False
        
        # 创建调度的测试项
        scheduled_test = ScheduledTest(
            test_id=test_item.test_id,
            test_item=test_item.test_item,
            test_group=test_item.test_group,
            test_phase=test_item.test_phase,
            start_time=state.current_time,
            duration=test_item.duration,
            end_time=state.current_time + test_item.duration
        )
        
        # 添加到调度状态
        state.add_scheduled_test(scheduled_test)
        
        self.logger.debug(f"成功调度测试项: {test_item.test_item} "
                         f"(开始时间: {state.current_time}, 持续时间: {test_item.duration})")
        
        return True
    
    def _get_next_time_point(self, state: SchedulingState) -> float:
        """
        获取下一个时间点
        
        Args:
            state: 调度状态
            
        Returns:
            float: 下一个时间点
        """
        if state.active_tests:
            # 如果有活跃测试，移动到最早的结束时间
            next_time = min(test.end_time for test in state.active_tests)
            
            # 确保不跨越休息日
            if self.time_manager.will_cross_rest_day(state.current_time, next_time - state.current_time):
                next_time = self.time_manager.get_next_working_day_start(next_time)
            
            return next_time
        else:
            # 如果没有活跃测试，移动到下一个小时或下一个工作日
            next_time = state.current_time + 1
            
            if self.time_manager.is_rest_day(next_time):
                next_time = self.time_manager.get_next_working_day_start(next_time)
            
            return next_time
    
    def _create_scheduling_result(self, state: SchedulingState) -> SchedulingResult:
        """
        创建调度结果
        
        Args:
            state: 调度状态
            
        Returns:
            SchedulingResult: 调度结果
        """
        # 计算统计信息
        statistics = self._calculate_statistics(state)
        
        return SchedulingResult(
            scheduled_tests=state.scheduled_tests.copy(),
            total_duration=max(test.end_time for test in state.scheduled_tests) if state.scheduled_tests else 0.0,
            statistics=statistics
        )
    
    def _calculate_statistics(self, state: SchedulingState) -> Dict[str, any]:
        """
        计算调度统计信息
        
        Args:
            state: 调度状态
            
        Returns:
            Dict[str, any]: 统计信息
        """
        if not state.scheduled_tests:
            return {}
        
        total_duration = max(test.end_time for test in state.scheduled_tests)
        
        # 按阶段统计
        phase_stats = {}
        for test in state.scheduled_tests:
            phase = test.test_phase
            if phase not in phase_stats:
                phase_stats[phase] = 0
            phase_stats[phase] += 1
        
        # 按测试组统计
        group_stats = {}
        for test in state.scheduled_tests:
            if test.test_group and test.test_group != '无':
                group = test.test_group
                if group not in group_stats:
                    group_stats[group] = 0
                group_stats[group] += 1
        
        # 计算平均并行度
        if total_duration > 0:
            avg_parallelism = len(state.scheduled_tests) / total_duration
        else:
            avg_parallelism = 0.0
        
        # 计算资源利用率
        resource_utilization = self._calculate_resource_utilization(state.scheduled_tests)
        
        return {
            '总测试项数': len(state.scheduled_tests),
            '未调度测试项数': len(state.unscheduled_test_ids),
            '总完工时间（小时）': total_duration,
            '总完工时间（天）': total_duration / self.working_time_config.hours_per_day,
            '平均并行度': round(avg_parallelism, 2),
            '各阶段测试数量': phase_stats,
            '各测试组测试数量': group_stats,
            '资源利用率': resource_utilization
        }
    
    def _calculate_resource_utilization(self, scheduled_tests: List[ScheduledTest]) -> Dict[str, float]:
        """
        计算资源利用率
        
        Args:
            scheduled_tests: 已调度的测试项
            
        Returns:
            Dict[str, float]: 各资源的利用率
        """
        if not scheduled_tests:
            return {}
        
        total_duration = max(test.end_time for test in scheduled_tests)
        resource_usage_time = {instrument: 0.0 for instrument in self.instruments.keys()}
        
        # 计算每个资源的使用时间
        for test in scheduled_tests:
            test_idx = self.test_id_to_index.get(test.test_id)
            if test_idx is not None:
                resource_usage = self.constraint_checker.resource_matrix.get_resource_usage(test_idx)
                for instrument, usage in resource_usage.items():
                    if usage > 0:
                        resource_usage_time[instrument] += test.duration
        
        # 计算利用率
        utilization = {}
        for instrument, total_usage_time in resource_usage_time.items():
            available_time = total_duration * self.instruments[instrument]
            if available_time > 0:
                utilization[instrument] = round((total_usage_time / available_time) * 100, 2)
            else:
                utilization[instrument] = 0.0
        
        return utilization