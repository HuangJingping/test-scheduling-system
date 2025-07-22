"""
序列化测试调度器
生成测试项的执行顺序，不依赖具体时间估计
重点关注：优先级、依赖关系、阶段顺序、资源约束
"""
import sys
import os
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import TestItem, DependencyGraph, DataValidator
from config import ConfigManager
from constraints import ResourceMatrix


@dataclass
class SequenceItem:
    """序列项 - 不包含具体时间"""
    sequence_number: int        # 执行序号
    test_id: int
    test_item: str
    test_group: str
    test_phase: str
    priority_rank: int          # 优先级排名
    dependency_level: int       # 依赖层级
    resource_conflicts: List[str]  # 资源冲突项


@dataclass
class SequenceResult:
    """序列化结果"""
    sequence_items: List[SequenceItem]
    parallel_groups: List[List[int]]  # 可并行执行的测试组
    phase_boundaries: Dict[str, Tuple[int, int]]  # 各阶段的起止序号
    statistics: Dict[str, any]


class SequenceScheduler:
    """序列化调度器"""
    
    def __init__(self, config_file: str = None):
        self.config_manager = ConfigManager(config_file)
        self.test_items: List[TestItem] = []
        self.instruments: Dict[str, int] = {}
        self.dependency_graph = DependencyGraph()
        self.resource_matrix: Optional[ResourceMatrix] = None
    
    def load_data_from_file(self, data_file: str):
        """从文件加载数据"""
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 转换测试项数据
        self.test_items = []
        for item_data in data.get('test_items', []):
            test_item = TestItem(**item_data)
            self.test_items.append(test_item)
        
        self.instruments = data.get('instruments', {})
        
        # 设置依赖关系
        dependencies = data.get('dependencies', {})
        if dependencies:
            self.dependency_graph.dependencies = dependencies.copy()
        
        # 构建依赖关系矩阵
        self.dependency_graph.build_matrix(self.test_items)
        
        # 创建资源矩阵
        self.resource_matrix = ResourceMatrix(self.test_items, self.instruments)
        
        print(f"加载完成: {len(self.test_items)}个测试项")
    
    def calculate_dependency_levels(self) -> Dict[int, int]:
        """计算每个测试项的依赖层级"""
        n = len(self.test_items)
        levels = {}
        visited = set()
        
        def dfs(test_idx: int) -> int:
            if test_idx in visited:
                return levels.get(test_idx, 0)
            
            visited.add(test_idx)
            max_dep_level = 0
            
            # 查找所有依赖项
            for j in range(n):
                if self.dependency_graph.dependency_matrix[test_idx][j] == 1:
                    dep_level = dfs(j)
                    max_dep_level = max(max_dep_level, dep_level + 1)
            
            levels[test_idx] = max_dep_level
            return max_dep_level
        
        # 计算所有测试项的层级
        for i in range(n):
            if i not in levels:
                dfs(i)
        
        return levels
    
    def calculate_priority_scores(self) -> Dict[int, float]:
        """计算优先级评分（不依赖时间）"""
        n = len(self.test_items)
        scores = {}
        
        # 获取阶段顺序
        phases = list(set(item.test_phase for item in self.test_items))
        phase_to_index = {phase: idx for idx, phase in enumerate(phases)}
        
        for i, test_item in enumerate(self.test_items):
            score = 0.0
            
            # 1. 依赖关系评分（被依赖的测试项优先级更高）
            dep_count = sum(self.dependency_graph.dependency_matrix[j][i] for j in range(n))
            score += dep_count * 10
            
            # 2. 资源复杂度评分（资源需求多的优先级更高）
            resource_usage = sum(self.resource_matrix.matrix[i])
            score += resource_usage * 5
            
            # 3. 阶段评分（前面阶段优先级更高）
            phase_idx = phase_to_index.get(test_item.test_phase, len(phases))
            score += (len(phases) - phase_idx) * 20
            
            # 4. 测试组连续性（同组测试项优先级相近）
            if test_item.test_group and test_item.test_group != '无':
                # 给有测试组的项目额外加分，促进组内连续性
                score += 15
            
            scores[i] = score
        
        return scores
    
    def find_resource_conflicts(self) -> Dict[int, List[int]]:
        """找出资源冲突的测试项"""
        n = len(self.test_items)
        conflicts = defaultdict(list)
        
        for i in range(n):
            for j in range(i + 1, n):
                # 检查是否有资源冲突
                has_conflict = False
                for k in range(len(self.resource_matrix.instrument_names)):
                    if (self.resource_matrix.matrix[i][k] > 0 and 
                        self.resource_matrix.matrix[j][k] > 0):
                        # 需要相同资源，检查是否超出容量
                        total_needed = (self.resource_matrix.matrix[i][k] + 
                                      self.resource_matrix.matrix[j][k])
                        available = list(self.instruments.values())[k]
                        if total_needed > available:
                            has_conflict = True
                            break
                
                if has_conflict:
                    conflicts[i].append(j)
                    conflicts[j].append(i)
        
        return dict(conflicts)
    
    def generate_sequence(self) -> SequenceResult:
        """生成测试执行序列"""
        n = len(self.test_items)
        
        # 计算依赖层级和优先级
        dependency_levels = self.calculate_dependency_levels()
        priority_scores = self.calculate_priority_scores()
        resource_conflicts = self.find_resource_conflicts()
        
        # 创建排序用的元组列表: (依赖层级, -优先级分数, 测试索引)
        sort_items = []
        for i in range(n):
            sort_items.append((
                dependency_levels.get(i, 0),    # 依赖层级越低越优先
                -priority_scores.get(i, 0),     # 优先级分数越高越优先
                i                               # 测试索引
            ))
        
        # 排序：先按依赖层级，再按优先级
        sort_items.sort()
        
        # 生成序列项
        sequence_items = []
        for seq_num, (dep_level, neg_priority, test_idx) in enumerate(sort_items, 1):
            test_item = self.test_items[test_idx]
            
            # 获取资源冲突的测试项名称
            conflict_names = []
            for conflict_idx in resource_conflicts.get(test_idx, []):
                conflict_names.append(self.test_items[conflict_idx].test_item)
            
            sequence_item = SequenceItem(
                sequence_number=seq_num,
                test_id=test_item.test_id,
                test_item=test_item.test_item,
                test_group=test_item.test_group,
                test_phase=test_item.test_phase,
                priority_rank=seq_num,
                dependency_level=dep_level,
                resource_conflicts=conflict_names
            )
            
            sequence_items.append(sequence_item)
        
        # 生成并行组（基于资源不冲突的原则）
        parallel_groups = self._generate_parallel_groups(sequence_items, resource_conflicts)
        
        # 计算阶段边界
        phase_boundaries = self._calculate_phase_boundaries(sequence_items)
        
        # 生成统计信息
        statistics = self._calculate_statistics(sequence_items, parallel_groups)
        
        return SequenceResult(
            sequence_items=sequence_items,
            parallel_groups=parallel_groups,
            phase_boundaries=phase_boundaries,
            statistics=statistics
        )
    
    def _generate_parallel_groups(self, sequence_items: List[SequenceItem], 
                                resource_conflicts: Dict[int, List[int]]) -> List[List[int]]:
        """生成可并行执行的测试组"""
        parallel_groups = []
        used_items = set()
        
        for i, item in enumerate(sequence_items):
            if i in used_items:
                continue
            
            # 找出与当前项可并行的项
            current_group = [i]
            used_items.add(i)
            
            # 获取当前项的测试索引
            current_test_idx = next(
                idx for idx, test in enumerate(self.test_items) 
                if test.test_id == item.test_id
            )
            
            for j, other_item in enumerate(sequence_items[i+1:], i+1):
                if j in used_items:
                    continue
                
                # 获取其他项的测试索引
                other_test_idx = next(
                    idx for idx, test in enumerate(self.test_items) 
                    if test.test_id == other_item.test_id
                )
                
                # 检查是否可以并行
                can_parallel = True
                
                # 1. 检查资源冲突
                if other_test_idx in resource_conflicts.get(current_test_idx, []):
                    can_parallel = False
                
                # 2. 检查依赖关系
                if (self.dependency_graph.dependency_matrix[other_test_idx][current_test_idx] == 1 or
                    self.dependency_graph.dependency_matrix[current_test_idx][other_test_idx] == 1):
                    can_parallel = False
                
                # 3. 检查测试组约束（同组不能并行）
                if (item.test_group and other_item.test_group and 
                    item.test_group == other_item.test_group and
                    item.test_group != '无'):
                    can_parallel = False
                
                # 4. 检查与已在组内的其他项是否冲突
                for group_member_idx in current_group:
                    group_member_test_idx = next(
                        idx for idx, test in enumerate(self.test_items) 
                        if test.test_id == sequence_items[group_member_idx].test_id
                    )
                    if other_test_idx in resource_conflicts.get(group_member_test_idx, []):
                        can_parallel = False
                        break
                
                if can_parallel:
                    current_group.append(j)
                    used_items.add(j)
                    
                    # 限制并行组大小
                    if len(current_group) >= self.config_manager.scheduling.max_parallel:
                        break
            
            if current_group:
                parallel_groups.append(current_group)
        
        return parallel_groups
    
    def _calculate_phase_boundaries(self, sequence_items: List[SequenceItem]) -> Dict[str, Tuple[int, int]]:
        """计算各阶段的起止序号"""
        phase_boundaries = {}
        
        for phase in set(item.test_phase for item in sequence_items):
            phase_items = [item for item in sequence_items if item.test_phase == phase]
            if phase_items:
                min_seq = min(item.sequence_number for item in phase_items)
                max_seq = max(item.sequence_number for item in phase_items)
                phase_boundaries[phase] = (min_seq, max_seq)
        
        return phase_boundaries
    
    def _calculate_statistics(self, sequence_items: List[SequenceItem], 
                            parallel_groups: List[List[int]]) -> Dict[str, any]:
        """计算统计信息"""
        stats = {}
        
        # 基本统计
        stats['总测试项数'] = len(sequence_items)
        stats['并行组数'] = len(parallel_groups)
        stats['最大并行度'] = max(len(group) for group in parallel_groups) if parallel_groups else 0
        stats['平均并行度'] = sum(len(group) for group in parallel_groups) / len(parallel_groups) if parallel_groups else 0
        
        # 阶段统计
        phase_stats = defaultdict(int)
        for item in sequence_items:
            phase_stats[item.test_phase] += 1
        stats['各阶段测试数量'] = dict(phase_stats)
        
        # 测试组统计
        group_stats = defaultdict(int)
        for item in sequence_items:
            if item.test_group and item.test_group != '无':
                group_stats[item.test_group] += 1
        stats['各测试组测试数量'] = dict(group_stats)
        
        # 依赖层级统计
        level_stats = defaultdict(int)
        for item in sequence_items:
            level_stats[f"层级{item.dependency_level}"] += 1
        stats['依赖层级分布'] = dict(level_stats)
        
        return stats


class SequenceFormatter:
    """序列结果格式化器"""
    
    def format_sequence_table(self, result: SequenceResult) -> str:
        """格式化序列表格"""
        lines = []
        lines.append("=" * 120)
        lines.append("测试执行序列")
        lines.append("=" * 120)
        
        # 表头
        header = f"{'序号':<4} {'测试ID':<6} {'阶段':<8} {'测试组':<12} {'测试项目':<30} {'依赖层级':<6} {'资源冲突':<20}"
        lines.append(header)
        lines.append("-" * 120)
        
        # 数据行
        for item in result.sequence_items:
            conflicts = ', '.join(item.resource_conflicts[:2])  # 只显示前2个冲突
            if len(item.resource_conflicts) > 2:
                conflicts += "..."
            
            phase_short = item.test_phase.replace("专项测试", "测试").replace("（", "(").replace("）", ")")[:15]
            group_short = item.test_group[:10] if item.test_group else "无"
            item_short = item.test_item[:28]
            
            row = f"{item.sequence_number:<4} {item.test_id:<6} {phase_short:<8} {group_short:<12} {item_short:<30} {item.dependency_level:<6} {conflicts:<20}"
            lines.append(row)
        
        return '\n'.join(lines)
    
    def format_parallel_groups(self, result: SequenceResult) -> str:
        """格式化并行组信息"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("可并行执行的测试组")
        lines.append("=" * 80)
        
        for i, group in enumerate(result.parallel_groups, 1):
            if len(group) > 1:  # 只显示真正并行的组
                lines.append(f"\n并行组 {i} (可同时执行 {len(group)} 项):")
                for item_idx in group:
                    item = result.sequence_items[item_idx]
                    lines.append(f"  - 序号{item.sequence_number}: {item.test_item}")
        
        return '\n'.join(lines)
    
    def format_phase_summary(self, result: SequenceResult) -> str:
        """格式化阶段汇总"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("各阶段执行范围")
        lines.append("=" * 80)
        
        for phase, (start, end) in result.phase_boundaries.items():
            phase_short = phase.replace("专项测试", "测试")
            lines.append(f"{phase_short}: 序号 {start} - {end}")
        
        return '\n'.join(lines)
    
    def format_statistics(self, result: SequenceResult) -> str:
        """格式化统计信息"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("统计信息")
        lines.append("=" * 80)
        
        stats = result.statistics
        lines.append(f"总测试项数: {stats['总测试项数']}")
        lines.append(f"并行组数: {stats['并行组数']}")
        lines.append(f"最大并行度: {stats['最大并行度']}")
        lines.append(f"平均并行度: {stats['平均并行度']:.2f}")
        
        lines.append(f"\n各阶段测试数量:")
        for phase, count in stats['各阶段测试数量'].items():
            phase_short = phase.replace("专项测试", "测试")
            lines.append(f"  {phase_short}: {count}项")
        
        return '\n'.join(lines)


def main():
    """主函数 - 演示序列化调度"""
    print("序列化测试调度器演示")
    print("生成测试执行顺序，不依赖具体时间估计")
    
    try:
        # 创建序列化调度器
        scheduler = SequenceScheduler('scheduler_config.json')
        scheduler.load_data_from_file('test_data.json')
        
        # 生成执行序列
        print("\n正在生成测试执行序列...")
        result = scheduler.generate_sequence()
        
        # 格式化输出
        formatter = SequenceFormatter()
        
        print(formatter.format_sequence_table(result))
        print(formatter.format_parallel_groups(result))
        print(formatter.format_phase_summary(result))
        print(formatter.format_statistics(result))
        
        # 保存结果到文件
        output_file = "test_execution_sequence.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("测试执行序列报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(formatter.format_sequence_table(result))
            f.write(formatter.format_parallel_groups(result))
            f.write(formatter.format_phase_summary(result))
            f.write(formatter.format_statistics(result))
        
        print(f"\n序列化结果已保存到: {output_file}")
        print("\n🎯 优势:")
        print("  ✓ 不依赖时间估计，只关注执行顺序")
        print("  ✓ 严格遵循依赖关系和阶段顺序")
        print("  ✓ 考虑资源冲突，给出并行建议")
        print("  ✓ 实际执行时可根据情况调整具体时间")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()