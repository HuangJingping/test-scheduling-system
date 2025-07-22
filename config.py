"""
测试调度系统配置管理模块
负责管理所有可配置参数，避免硬编码
"""
from dataclasses import dataclass
from typing import Dict, Any
import json
import os


@dataclass
class PriorityWeights:
    """优先级权重配置"""
    dependency: int = 10      # 依赖关系权重
    duration: int = 2         # 持续时间权重
    resource: int = 5         # 资源需求权重
    phase: int = 20          # 阶段权重
    continuity: int = 50     # 连续性权重
    group_phase_boost: int = 450  # 组-阶段优先级最大加分


@dataclass
class WorkingTimeConfig:
    """工作时间配置"""
    hours_per_day: int = 8           # 每天工作小时数
    rest_day_cycle: int = 7          # 休息日周期（每7天休息1天）
    max_daily_tests: int = 5         # 每天最大测试项数
    short_test_threshold: int = 8    # 短测试项阈值（小时）


@dataclass
class SchedulingConfig:
    """调度配置"""
    max_parallel: int = 3            # 最大并行测试数
    max_parallel_per_phase: int = 3  # 每阶段最大并行组数
    lookback_window: int = 8         # 最近完成项目回溯窗口（小时）
    time_limit_hours: int = None     # 时间限制（None表示无限制）


@dataclass
class OutputConfig:
    """输出配置"""
    excel_filename: str = "test_schedule_result.xlsx"
    show_detailed_table: bool = True
    show_statistics: bool = True
    export_to_excel: bool = True
    date_format: str = "第{day}天{hour}点"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.priority_weights = PriorityWeights()
        self.working_time = WorkingTimeConfig()
        self.scheduling = SchedulingConfig()
        self.output = OutputConfig()
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """从JSON文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新各个配置段
            if 'priority_weights' in config_data:
                self._update_dataclass(self.priority_weights, config_data['priority_weights'])
            
            if 'working_time' in config_data:
                self._update_dataclass(self.working_time, config_data['working_time'])
            
            if 'scheduling' in config_data:
                self._update_dataclass(self.scheduling, config_data['scheduling'])
            
            if 'output' in config_data:
                self._update_dataclass(self.output, config_data['output'])
                
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            print("使用默认配置")
    
    def save_to_file(self, config_file: str):
        """保存配置到JSON文件"""
        config_data = {
            'priority_weights': self._dataclass_to_dict(self.priority_weights),
            'working_time': self._dataclass_to_dict(self.working_time),
            'scheduling': self._dataclass_to_dict(self.scheduling),
            'output': self._dataclass_to_dict(self.output)
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """更新dataclass对象的字段"""
        for key, value in data.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
    
    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """将dataclass转换为字典"""
        return {field.name: getattr(obj, field.name) for field in obj.__dataclass_fields__.values()}
    
    def validate(self) -> bool:
        """验证配置有效性"""
        if self.working_time.hours_per_day <= 0:
            raise ValueError("每天工作小时数必须大于0")
        
        if self.scheduling.max_parallel <= 0:
            raise ValueError("最大并行数必须大于0")
        
        if self.working_time.rest_day_cycle <= 0:
            raise ValueError("休息日周期必须大于0")
        
        return True


# 默认配置实例
default_config = ConfigManager()