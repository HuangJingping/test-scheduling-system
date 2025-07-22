"""
重构后的测试调度器主类
整合所有模块，提供简洁的调度接口
"""
import logging
from typing import List, Dict, Optional
import json
import os

from models import TestItem, DependencyGraph, SchedulingResult, DataValidator
from config import ConfigManager
from constraints import ResourceMatrix, ConstraintChecker
from priority_calculator import PriorityManager
from scheduling_algorithm import SchedulingAlgorithm
from output_formatter import OutputManager


class TestScheduler:
    """
    重构后的测试调度器
    
    负责整合各个模块，提供简洁的调度接口
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化调度器
        
        Args:
            config_file: 配置文件路径（可选）
        """
        # 加载配置
        self.config_manager = ConfigManager(config_file)
        self.config_manager.validate()
        
        # 初始化日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 数据容器
        self.test_items: List[TestItem] = []
        self.instruments: Dict[str, int] = {}
        self.dependency_graph = DependencyGraph()
        
        # 核心组件（延迟初始化）
        self.resource_matrix: Optional[ResourceMatrix] = None
        self.constraint_checker: Optional[ConstraintChecker] = None
        self.priority_manager: Optional[PriorityManager] = None
        self.scheduling_algorithm: Optional[SchedulingAlgorithm] = None
        self.output_manager: Optional[OutputManager] = None
        
        self._initialized = False
    
    def load_data_from_dict(self, test_data: List, instruments: Dict[str, int], 
                           dependencies: Dict[str, List[str]] = None):
        """
        从字典数据加载测试项、仪器和依赖关系
        
        Args:
            test_data: 测试项数据列表
            instruments: 仪器字典
            dependencies: 依赖关系字典
        """
        try:
            # 转换测试项数据
            self.test_items = []
            for item_data in test_data:
                if isinstance(item_data, (list, tuple)) and len(item_data) >= 7:
                    # 兼容原有的元组格式
                    test_item = TestItem(
                        test_id=item_data[0],
                        test_phase=item_data[1],
                        test_group=item_data[2],
                        test_item=item_data[3],
                        required_equipment=item_data[4],
                        required_instruments=item_data[5],
                        duration=item_data[6]
                    )
                elif isinstance(item_data, dict):
                    # 字典格式
                    test_item = TestItem(**item_data)
                else:
                    raise ValueError(f"不支持的测试项数据格式: {type(item_data)}")
                
                self.test_items.append(test_item)
            
            self.instruments = instruments.copy()
            
            # 设置依赖关系
            if dependencies:
                self.dependency_graph.dependencies = dependencies.copy()
            
            # 验证数据
            self._validate_data()
            
            # 构建依赖关系矩阵
            self.dependency_graph.build_matrix(self.test_items)
            
            # 标记需要重新初始化组件
            self._initialized = False
            
            self.logger.info(f"成功加载 {len(self.test_items)} 个测试项, "
                           f"{len(self.instruments)} 种仪器, "
                           f"{len(self.dependency_graph.dependencies)} 个依赖关系")
            
        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")
            raise
    
    def load_data_from_file(self, data_file: str):
        """
        从JSON文件加载数据
        
        Args:
            data_file: 数据文件路径
        """
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            test_data = data.get('test_items', [])
            instruments = data.get('instruments', {})
            dependencies = data.get('dependencies', {})
            
            self.load_data_from_dict(test_data, instruments, dependencies)
            
        except Exception as e:
            self.logger.error(f"从文件加载数据失败: {e}")
            raise
    
    def solve_schedule(self, max_parallel: int = None, output_filename: str = None) -> SchedulingResult:
        """
        执行调度算法
        
        Args:
            max_parallel: 最大并行数（覆盖配置文件设置）
            output_filename: 输出文件名（覆盖配置文件设置）
            
        Returns:
            SchedulingResult: 调度结果
        """
        if not self.test_items:
            raise ValueError("没有加载测试项数据")
        
        # 覆盖配置参数
        if max_parallel is not None:
            self.config_manager.scheduling.max_parallel = max_parallel
        
        # 初始化组件
        self._initialize_components()
        
        # 执行调度
        self.logger.info("开始执行调度算法")
        result = self.scheduling_algorithm.solve()
        
        # 输出结果
        self.output_manager.output_results(result, output_filename)
        
        return result
    
    def get_schedule_summary(self, result: SchedulingResult) -> Dict:
        """
        获取调度结果摘要
        
        Args:
            result: 调度结果
            
        Returns:
            Dict: 摘要信息
        """
        if not self.output_manager:
            self._initialize_components()
        
        return {
            'total_tests': len(result.scheduled_tests),
            'total_duration_hours': result.total_duration,
            'total_duration_days': result.total_duration / self.config_manager.working_time.hours_per_day,
            'detailed_table': self.output_manager.get_detailed_table(result),
            'phase_summary': self.output_manager.get_phase_summary(result),
            'group_summary': self.output_manager.get_group_summary(result),
            'statistics': result.statistics
        }
    
    def export_to_excel(self, result: SchedulingResult, filename: str):
        """
        导出结果到Excel文件
        
        Args:
            result: 调度结果
            filename: 输出文件名
        """
        if not self.output_manager:
            self._initialize_components()
        
        self.output_manager.excel_exporter.export_to_excel(
            result, self.output_manager.table_formatter, filename
        )
    
    def validate_data(self) -> List[str]:
        """
        验证当前加载的数据
        
        Returns:
            List[str]: 验证错误列表（空列表表示验证通过）
        """
        return self._validate_data()
    
    def get_config(self) -> ConfigManager:
        """获取配置管理器"""
        return self.config_manager
    
    def save_config(self, config_file: str):
        """
        保存当前配置到文件
        
        Args:
            config_file: 配置文件路径
        """
        self.config_manager.save_to_file(config_file)
    
    def _initialize_components(self):
        """初始化各个组件"""
        if self._initialized:
            return
        
        if not self.test_items:
            raise ValueError("没有加载测试项数据")
        
        # 创建资源矩阵
        self.resource_matrix = ResourceMatrix(self.test_items, self.instruments)
        
        # 创建约束检查器
        self.constraint_checker = ConstraintChecker(
            self.test_items, self.instruments, self.dependency_graph, 
            self.config_manager.scheduling
        )
        
        # 创建优先级管理器
        self.priority_manager = PriorityManager(
            self.test_items, self.dependency_graph, self.resource_matrix,
            self.config_manager.priority_weights, self.config_manager.scheduling
        )
        
        # 创建调度算法
        self.scheduling_algorithm = SchedulingAlgorithm(
            self.test_items, self.instruments, self.dependency_graph,
            self.config_manager.scheduling, self.config_manager.working_time,
            self.priority_manager
        )
        
        # 创建输出管理器
        self.output_manager = OutputManager(
            self.test_items, self.dependency_graph,
            self.config_manager.output, self.config_manager.working_time
        )
        
        self._initialized = True
        self.logger.info("所有组件初始化完成")
    
    def _validate_data(self) -> List[str]:
        """验证数据有效性"""
        errors = []
        
        # 验证测试项
        test_errors = DataValidator.validate_test_items(self.test_items)
        errors.extend(test_errors)
        
        # 验证仪器
        instrument_errors = DataValidator.validate_instruments(self.instruments)
        errors.extend(instrument_errors)
        
        # 验证依赖关系
        dependency_errors = DataValidator.validate_dependencies(
            self.dependency_graph.dependencies, self.test_items
        )
        errors.extend(dependency_errors)
        
        if errors:
            self.logger.warning(f"数据验证发现 {len(errors)} 个问题")
            for error in errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info("数据验证通过")
        
        return errors
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('test_scheduler.log', encoding='utf-8')
            ]
        )


def create_scheduler_from_legacy_data(test_items_data, instruments_data, dependencies_data,
                                    config_file: str = None) -> TestScheduler:
    """
    从原有格式的数据创建调度器（兼容性函数）
    
    Args:
        test_items_data: 测试项数据
        instruments_data: 仪器数据
        dependencies_data: 依赖关系数据
        config_file: 配置文件路径
        
    Returns:
        TestScheduler: 配置好的调度器实例
    """
    scheduler = TestScheduler(config_file)
    scheduler.load_data_from_dict(test_items_data, instruments_data, dependencies_data)
    return scheduler


# 为了保持向后兼容，提供一个简化的接口函数
def solve_test_schedule(test_items, instruments, dependencies, max_parallel=3, 
                       config_file=None, output_filename=None):
    """
    简化的调度接口函数（兼容原有代码）
    
    Args:
        test_items: 测试项数据
        instruments: 仪器数据
        dependencies: 依赖关系数据
        max_parallel: 最大并行数
        config_file: 配置文件路径
        output_filename: 输出文件名
        
    Returns:
        SchedulingResult: 调度结果
    """
    scheduler = create_scheduler_from_legacy_data(
        test_items, instruments, dependencies, config_file
    )
    
    return scheduler.solve_schedule(max_parallel, output_filename)