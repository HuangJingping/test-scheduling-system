"""
输出格式化模块
负责将调度结果格式化为各种输出格式：表格、Excel、统计信息等
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import os
from models import ScheduledTest, SchedulingResult, TestItem, DependencyGraph
from config import OutputConfig, WorkingTimeConfig
from time_manager import TimeFormatter


class ScheduleTableFormatter:
    """调度表格格式化器"""
    
    def __init__(self, test_items: List[TestItem], dependency_graph: DependencyGraph,
                 time_formatter: TimeFormatter):
        self.test_items = test_items
        self.dependency_graph = dependency_graph
        self.time_formatter = time_formatter
        
        # 创建测试项映射
        self.test_id_to_item = {item.test_id: item for item in test_items}
    
    def format_detailed_table(self, result: SchedulingResult) -> pd.DataFrame:
        """
        创建详细的调度结果表格
        
        Args:
            result: 调度结果
            
        Returns:
            pd.DataFrame: 格式化的详细表格
        """
        detailed_schedule = []
        
        for test in result.scheduled_tests:
            # 获取测试项的完整信息
            test_item = self.test_id_to_item.get(test.test_id)
            if not test_item:
                continue
            
            # 构建详细信息字典
            detailed_task = {
                '测试ID': test.test_id,
                '测试阶段': test_item.test_phase,
                '测试组': test.test_group if test.test_group else '无',
                '测试项目': test.test_item,
                '所需设备': test_item.required_equipment if test_item.required_equipment else '无',
                '陪试装备': test_item.required_instruments if test_item.required_instruments else '无',
                '持续时间': self.time_formatter.format_duration(test.duration),
                '开始时间': self.time_formatter.format_time(test.start_time),
                '结束时间': self.time_formatter.format_time(test.end_time),
                '原始开始时间': test.start_time  # 用于排序
            }
            
            # 添加依赖项信息
            dependencies = self._get_test_dependencies(test.test_id)
            detailed_task['依赖项目'] = ', '.join(dependencies) if dependencies else '无'
            
            detailed_schedule.append(detailed_task)
        
        # 转换为DataFrame并排序
        if not detailed_schedule:
            return pd.DataFrame()
        
        result_df = pd.DataFrame(detailed_schedule)
        result_df = result_df.sort_values('原始开始时间')
        result_df = result_df.drop('原始开始时间', axis=1)
        
        return result_df
    
    def format_phase_summary(self, result: SchedulingResult) -> pd.DataFrame:
        """
        创建按阶段汇总的表格
        
        Args:
            result: 调度结果
            
        Returns:
            pd.DataFrame: 阶段汇总表格
        """
        phase_stats = {}
        phase_duration = {}
        
        for test in result.scheduled_tests:
            test_item = self.test_id_to_item.get(test.test_id)
            if not test_item:
                continue
            
            phase = test_item.test_phase
            
            # 统计数量
            if phase not in phase_stats:
                phase_stats[phase] = 0
                phase_duration[phase] = {'min_start': float('inf'), 'max_end': 0}
            
            phase_stats[phase] += 1
            phase_duration[phase]['min_start'] = min(phase_duration[phase]['min_start'], test.start_time)
            phase_duration[phase]['max_end'] = max(phase_duration[phase]['max_end'], test.end_time)
        
        # 创建汇总数据
        summary_data = []
        for phase, count in phase_stats.items():
            duration_info = phase_duration[phase]
            start_time = self.time_formatter.format_time(duration_info['min_start'])
            end_time = self.time_formatter.format_time(duration_info['max_end'])
            total_duration = self.time_formatter.format_duration(
                duration_info['max_end'] - duration_info['min_start']
            )
            
            summary_data.append({
                '测试阶段': phase,
                '测试项数量': count,
                '阶段开始时间': start_time,
                '阶段结束时间': end_time,
                '阶段总耗时': total_duration
            })
        
        return pd.DataFrame(summary_data)
    
    def format_group_summary(self, result: SchedulingResult) -> pd.DataFrame:
        """
        创建按测试组汇总的表格
        
        Args:
            result: 调度结果
            
        Returns:
            pd.DataFrame: 测试组汇总表格
        """
        group_stats = {}
        
        for test in result.scheduled_tests:
            if not test.test_group or test.test_group == '无':
                continue
            
            group = test.test_group
            if group not in group_stats:
                group_stats[group] = {
                    'count': 0,
                    'phases': set(),
                    'total_duration': 0,
                    'min_start': float('inf'),
                    'max_end': 0
                }
            
            group_stats[group]['count'] += 1
            group_stats[group]['phases'].add(test.test_phase)
            group_stats[group]['total_duration'] += test.duration
            group_stats[group]['min_start'] = min(group_stats[group]['min_start'], test.start_time)
            group_stats[group]['max_end'] = max(group_stats[group]['max_end'], test.end_time)
        
        # 创建汇总数据
        summary_data = []
        for group, stats in group_stats.items():
            start_time = self.time_formatter.format_time(stats['min_start'])
            end_time = self.time_formatter.format_time(stats['max_end'])
            span_duration = self.time_formatter.format_duration(stats['max_end'] - stats['min_start'])
            work_duration = self.time_formatter.format_duration(stats['total_duration'])
            
            summary_data.append({
                '测试组': group,
                '测试项数量': stats['count'],
                '涉及阶段': ', '.join(sorted(stats['phases'])),
                '组开始时间': start_time,
                '组结束时间': end_time,
                '时间跨度': span_duration,
                '工作时长': work_duration
            })
        
        return pd.DataFrame(summary_data)
    
    def _get_test_dependencies(self, test_id: int) -> List[str]:
        """获取测试项的依赖项目名称列表"""
        dependencies = []
        
        # 在依赖关系矩阵中查找
        test_idx = next((i for i, item in enumerate(self.test_items) if item.test_id == test_id), None)
        if test_idx is not None and test_idx < len(self.dependency_graph.dependency_matrix):
            for j in range(len(self.dependency_graph.dependency_matrix)):
                if (j < len(self.dependency_graph.dependency_matrix[test_idx]) and 
                    self.dependency_graph.dependency_matrix[test_idx][j] == 1):
                    if j < len(self.test_items):
                        dependencies.append(self.test_items[j].test_item)
        
        return dependencies


class ExcelExporter:
    """Excel导出器"""
    
    def __init__(self, config: OutputConfig):
        self.config = config
    
    def export_to_excel(self, result: SchedulingResult, table_formatter: ScheduleTableFormatter,
                       filename: str = None) -> bool:
        """
        导出调度结果到Excel文件
        
        Args:
            result: 调度结果
            table_formatter: 表格格式化器
            filename: 输出文件名
            
        Returns:
            bool: 是否导出成功
        """
        if filename is None:
            filename = self.config.excel_filename
        
        try:
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                workbook = writer.book
                
                # 创建格式
                header_format = workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'valign': 'vcenter',
                    'fg_color': '#D9E1F2',
                    'border': 1
                })
                
                cell_format = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter',
                    'border': 1,
                    'text_wrap': True
                })
                
                # 1. 详细调度表
                detailed_table = table_formatter.format_detailed_table(result)
                if not detailed_table.empty:
                    self._write_formatted_sheet(writer, detailed_table, '详细调度表', 
                                              header_format, cell_format)
                
                # 2. 阶段汇总表
                phase_summary = table_formatter.format_phase_summary(result)
                if not phase_summary.empty:
                    self._write_formatted_sheet(writer, phase_summary, '阶段汇总',
                                              header_format, cell_format)
                
                # 3. 测试组汇总表
                group_summary = table_formatter.format_group_summary(result)
                if not group_summary.empty:
                    self._write_formatted_sheet(writer, group_summary, '测试组汇总',
                                              header_format, cell_format)
                
                # 4. 统计信息表
                if result.statistics:
                    stats_df = self._create_statistics_dataframe(result.statistics)
                    self._write_formatted_sheet(writer, stats_df, '统计信息',
                                              header_format, cell_format)
            
            print(f"调度结果已成功导出到文件：{filename}")
            return True
            
        except Exception as e:
            print(f"导出Excel文件时发生错误：{str(e)}")
            return False
    
    def _write_formatted_sheet(self, writer, dataframe: pd.DataFrame, sheet_name: str,
                             header_format, cell_format):
        """写入格式化的工作表"""
        dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        
        worksheet = writer.sheets[sheet_name]
        
        # 设置列宽
        for col_num in range(len(dataframe.columns)):
            # 根据内容动态调整列宽
            max_length = max(
                dataframe.iloc[:, col_num].astype(str).apply(len).max(),
                len(str(dataframe.columns[col_num]))
            )
            worksheet.set_column(col_num, col_num, min(max_length + 2, 30))
        
        # 设置行高
        worksheet.set_default_row(25)
        
        # 设置标题行格式
        for col_num, value in enumerate(dataframe.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # 设置数据单元格格式
        for row_num in range(len(dataframe)):
            for col_num in range(len(dataframe.columns)):
                cell_value = dataframe.iloc[row_num, col_num]
                # 处理依赖项目列的换行
                if isinstance(cell_value, str) and ',' in cell_value and col_num == len(dataframe.columns) - 1:
                    cell_value = cell_value.replace(', ', ',\n')
                
                worksheet.write(row_num + 1, col_num, cell_value, cell_format)
    
    def _create_statistics_dataframe(self, statistics: Dict[str, Any]) -> pd.DataFrame:
        """创建统计信息的DataFrame"""
        stats_data = []
        
        for key, value in statistics.items():
            if isinstance(value, dict):
                # 字典类型的统计信息（如各阶段测试数量）
                for sub_key, sub_value in value.items():
                    stats_data.append({
                        '统计类别': key,
                        '项目': sub_key,
                        '数值': sub_value
                    })
            else:
                # 简单值类型的统计信息
                stats_data.append({
                    '统计类别': key,
                    '项目': '',
                    '数值': value
                })
        
        return pd.DataFrame(stats_data)


class ConsoleFormatter:
    """控制台输出格式化器"""
    
    def __init__(self, config: OutputConfig):
        self.config = config
    
    def print_summary(self, result: SchedulingResult):
        """打印调度结果摘要"""
        print("\n" + "="*60)
        print("测试调度结果摘要")
        print("="*60)
        
        if not result.scheduled_tests:
            print("没有成功调度的测试项")
            return
        
        print(f"总测试项数: {len(result.scheduled_tests)}")
        print(f"总完工时间: {result.total_duration:.1f} 小时")
        
        if result.statistics:
            self._print_detailed_statistics(result.statistics)
    
    def print_detailed_table(self, detailed_table: pd.DataFrame):
        """打印详细调度表格"""
        if detailed_table.empty:
            print("没有调度结果")
            return
        
        print("\n" + "="*60)
        print("详细调度表格")
        print("="*60)
        
        # 设置pandas显示选项
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        print(detailed_table.to_string(index=False))
    
    def _print_detailed_statistics(self, statistics: Dict[str, Any]):
        """打印详细统计信息"""
        print("\n统计信息:")
        print("-" * 40)
        
        for key, value in statistics.items():
            if key == '各阶段测试数量':
                print(f"\n{key}:")
                for phase, count in value.items():
                    print(f"  {phase}: {count}个测试项")
            elif key == '各测试组测试数量':
                print(f"\n{key}:")
                for group, count in value.items():
                    print(f"  {group}: {count}个测试项")
            elif key == '资源利用率':
                print(f"\n{key}:")
                for resource, utilization in value.items():
                    print(f"  {resource}: {utilization}%")
            else:
                print(f"{key}: {value}")


class OutputManager:
    """输出管理器 - 统一管理所有输出格式"""
    
    def __init__(self, test_items: List[TestItem], dependency_graph: DependencyGraph,
                 output_config: OutputConfig, working_time_config: WorkingTimeConfig):
        self.config = output_config
        self.time_formatter = TimeFormatter(working_time_config)
        self.table_formatter = ScheduleTableFormatter(test_items, dependency_graph, self.time_formatter)
        self.excel_exporter = ExcelExporter(output_config)
        self.console_formatter = ConsoleFormatter(output_config)
    
    def output_results(self, result: SchedulingResult, filename: str = None):
        """
        输出调度结果到各种格式
        
        Args:
            result: 调度结果
            filename: 自定义输出文件名
        """
        # 生成详细表格
        detailed_table = self.table_formatter.format_detailed_table(result)
        
        # 控制台输出
        if self.config.show_detailed_table:
            self.console_formatter.print_detailed_table(detailed_table)
        
        if self.config.show_statistics:
            self.console_formatter.print_summary(result)
        
        # Excel导出
        if self.config.export_to_excel:
            self.excel_exporter.export_to_excel(result, self.table_formatter, filename)
    
    def get_detailed_table(self, result: SchedulingResult) -> pd.DataFrame:
        """获取详细调度表格"""
        return self.table_formatter.format_detailed_table(result)
    
    def get_phase_summary(self, result: SchedulingResult) -> pd.DataFrame:
        """获取阶段汇总表格"""
        return self.table_formatter.format_phase_summary(result)
    
    def get_group_summary(self, result: SchedulingResult) -> pd.DataFrame:
        """获取测试组汇总表格"""
        return self.table_formatter.format_group_summary(result)