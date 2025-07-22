"""
时间管理模块
负责处理工作日历、时间格式转换、跨天检查等时间相关逻辑
"""
from typing import Tuple
import math
from config import WorkingTimeConfig


class WorkingTimeManager:
    """工作时间管理器"""
    
    def __init__(self, config: WorkingTimeConfig):
        self.config = config
    
    def is_rest_day(self, hours: float) -> bool:
        """
        判断给定时间是否为休息日
        
        Args:
            hours: 时间（小时）
            
        Returns:
            bool: 是否为休息日
        """
        work_days = self.get_work_day_number(hours)
        return work_days % self.config.rest_day_cycle == 0
    
    def get_work_day_number(self, hours: float) -> int:
        """
        获取工作日天数（从1开始）
        
        Args:
            hours: 时间（小时）
            
        Returns:
            int: 工作日天数
        """
        return int(hours / self.config.hours_per_day) + 1
    
    def get_remaining_hours_in_day(self, hours: float) -> float:
        """
        获取当前时间点到工作日结束还剩余的小时数
        
        Args:
            hours: 当前时间（小时）
            
        Returns:
            float: 剩余小时数
        """
        return self.config.hours_per_day - (hours % self.config.hours_per_day)
    
    def will_cross_day(self, start_hours: float, duration: float) -> bool:
        """
        检查测试是否会跨天
        
        Args:
            start_hours: 开始时间（小时）
            duration: 持续时间（小时）
            
        Returns:
            bool: 是否跨天
        """
        remaining_hours = self.get_remaining_hours_in_day(start_hours)
        return duration > remaining_hours
    
    def will_cross_rest_day(self, start_hours: float, duration: float) -> bool:
        """
        检查测试是否会跨越休息日
        
        Args:
            start_hours: 开始时间（小时）
            duration: 持续时间（小时）
            
        Returns:
            bool: 是否跨越休息日
        """
        end_hours = start_hours + duration
        start_day = self.get_work_day_number(start_hours)
        end_day = self.get_work_day_number(end_hours)
        
        # 检查期间的每一天
        for day in range(start_day, end_day + 1):
            if day % self.config.rest_day_cycle == 0:  # 是休息日
                return True
        return False
    
    def get_next_working_day_start(self, hours: float) -> float:
        """
        获取下一个工作日的开始时间
        
        Args:
            hours: 当前时间（小时）
            
        Returns:
            float: 下一个工作日的开始时间（小时）
        """
        current_day = self.get_work_day_number(hours)
        next_day_start = current_day * self.config.hours_per_day
        
        # 如果下一天是休息日，跳过该天
        if self.is_rest_day(next_day_start):
            next_day_start += self.config.hours_per_day
        
        return next_day_start
    
    def get_next_available_time(self, current_time: float, min_duration: float = 0) -> float:
        """
        获取下一个可用的时间点
        
        Args:
            current_time: 当前时间
            min_duration: 最小持续时间（用于检查是否需要跳到下一天）
            
        Returns:
            float: 下一个可用时间点
        """
        # 如果当前是休息日，移动到下一个工作日
        if self.is_rest_day(current_time):
            return self.get_next_working_day_start(current_time)
        
        # 如果指定了最小持续时间，检查是否需要跳到下一天
        if min_duration > 0 and self.will_cross_day(current_time, min_duration):
            # 计算下一个工作日开始时间
            remaining_hours = self.get_remaining_hours_in_day(current_time)
            next_day_time = current_time + remaining_hours
            
            # 如果下一天是休息日，再跳一天
            if self.is_rest_day(next_day_time):
                next_day_time = self.get_next_working_day_start(next_day_time)
            
            return next_day_time
        
        return current_time
    
    def calculate_working_duration(self, start_hours: float, end_hours: float) -> float:
        """
        计算工作时间内的实际持续时间（排除休息日）
        
        Args:
            start_hours: 开始时间
            end_hours: 结束时间
            
        Returns:
            float: 实际工作时长
        """
        if end_hours <= start_hours:
            return 0.0
        
        total_duration = end_hours - start_hours
        
        # 计算期间包含的休息日数量
        start_day = self.get_work_day_number(start_hours)
        end_day = self.get_work_day_number(end_hours)
        
        rest_days = 0
        for day in range(start_day, end_day + 1):
            if day % self.config.rest_day_cycle == 0:
                rest_days += 1
        
        # 减去休息日的时间
        working_duration = total_duration - (rest_days * self.config.hours_per_day)
        return max(0.0, working_duration)


class TimeFormatter:
    """时间格式化器"""
    
    def __init__(self, config: WorkingTimeConfig):
        self.config = config
        self.time_manager = WorkingTimeManager(config)
    
    def format_time(self, hours: float) -> str:
        """
        将小时数转换为可读格式
        
        Args:
            hours: 小时数
            
        Returns:
            str: 格式化的时间字符串
        """
        work_day = self.time_manager.get_work_day_number(hours)
        hour_in_day = hours % self.config.hours_per_day
        
        # 转换为具体小时（8点开始工作）
        actual_hour = 8 + hour_in_day
        
        return f"第{work_day}天{actual_hour:.1f}点"
    
    def format_duration(self, duration_hours: float) -> str:
        """
        格式化持续时间
        
        Args:
            duration_hours: 持续时间（小时）
            
        Returns:
            str: 格式化的持续时间字符串
        """
        if duration_hours < 1:
            return f"{duration_hours * 60:.0f}分钟"
        elif duration_hours < self.config.hours_per_day:
            return f"{duration_hours:.1f}小时"
        else:
            days = duration_hours / self.config.hours_per_day
            if days == int(days):
                return f"{int(days)}天"
            else:
                return f"{days:.1f}天"
    
    def format_time_range(self, start_hours: float, end_hours: float) -> str:
        """
        格式化时间范围
        
        Args:
            start_hours: 开始时间
            end_hours: 结束时间
            
        Returns:
            str: 格式化的时间范围字符串
        """
        start_str = self.format_time(start_hours)
        end_str = self.format_time(end_hours)
        duration_str = self.format_duration(end_hours - start_hours)
        
        return f"{start_str} - {end_str} (持续{duration_str})"


class TimeConstraintChecker:
    """时间约束检查器"""
    
    def __init__(self, config: WorkingTimeConfig):
        self.config = config
        self.time_manager = WorkingTimeManager(config)
    
    def can_schedule_at_time(self, start_time: float, duration: float) -> Tuple[bool, str]:
        """
        检查是否可以在指定时间调度测试
        
        Args:
            start_time: 开始时间
            duration: 持续时间
            
        Returns:
            Tuple[bool, str]: (是否可以调度, 原因)
        """
        # 检查是否在休息日开始
        if self.time_manager.is_rest_day(start_time):
            return False, "不能在休息日开始测试"
        
        # 检查是否会跨越休息日
        if self.time_manager.will_cross_rest_day(start_time, duration):
            return False, "测试不能跨越休息日"
        
        # 检查短测试项是否跨天
        if (duration <= self.config.short_test_threshold and 
            self.time_manager.will_cross_day(start_time, duration)):
            return False, f"小于{self.config.short_test_threshold}小时的测试不能跨天"
        
        return True, "可以调度"
    
    def get_optimal_start_time(self, current_time: float, duration: float) -> float:
        """
        获取最优的开始时间
        
        Args:
            current_time: 当前时间
            duration: 测试持续时间
            
        Returns:
            float: 最优开始时间
        """
        # 如果当前时间就可以调度，直接返回
        can_schedule, _ = self.can_schedule_at_time(current_time, duration)
        if can_schedule:
            return current_time
        
        # 否则找到下一个可用时间
        if duration <= self.config.short_test_threshold:
            # 短测试项需要在一天内完成
            return self.time_manager.get_next_available_time(current_time, duration)
        else:
            # 长测试项可以跨天，但不能跨休息日
            next_time = self.time_manager.get_next_available_time(current_time)
            
            # 检查是否会跨休息日
            while self.time_manager.will_cross_rest_day(next_time, duration):
                next_time = self.time_manager.get_next_working_day_start(next_time + self.config.hours_per_day)
            
            return next_time