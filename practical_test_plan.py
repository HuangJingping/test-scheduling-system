"""
实用测试计划生成器
生成实际可执行的测试顺序计划，不包含具体时间
重点关注：执行顺序、依赖关系、并行建议
"""
import sys
import os
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sequence_scheduler import SequenceScheduler, SequenceFormatter


class PracticalTestPlanGenerator:
    """实用测试计划生成器"""
    
    def __init__(self):
        self.scheduler = SequenceScheduler('scheduler_config.json')
    
    def generate_plan(self, data_file: str) -> str:
        """生成实用的测试计划"""
        
        # 加载数据并生成序列
        self.scheduler.load_data_from_file(data_file)
        result = self.scheduler.generate_sequence()
        
        # 生成实用格式的计划
        plan_lines = []
        
        # 标题
        plan_lines.append("=" * 80)
        plan_lines.append("项目验收测试执行计划")
        plan_lines.append("=" * 80)
        plan_lines.append("")
        
        # 说明
        plan_lines.append("计划说明：")
        plan_lines.append("1. 本计划按测试项优先级和依赖关系排序")
        plan_lines.append("2. 具体执行时间由项目组根据实际情况安排")
        plan_lines.append("3. 标注了可并行执行的测试组，可提高效率")
        plan_lines.append("4. 必须严格按照依赖关系执行")
        plan_lines.append("")
        
        # 按阶段组织测试项
        phases = {}
        for item in result.sequence_items:
            if item.test_phase not in phases:
                phases[item.test_phase] = []
            phases[item.test_phase].append(item)
        
        # 阶段顺序
        phase_order = [
            "专项测试1（资料查询、设备级、单节点测试，小场地）",
            "专项测试2（节点间互联，小场地）", 
            "专项测试3（大场地）"
        ]
        
        for phase in phase_order:
            if phase not in phases:
                continue
            
            phase_items = sorted(phases[phase], key=lambda x: x.sequence_number)
            
            plan_lines.append(f"【{phase}】")
            plan_lines.append("-" * 60)
            
            # 按测试组分组
            groups = {}
            for item in phase_items:
                group = item.test_group if item.test_group else "其他"
                if group not in groups:
                    groups[group] = []
                groups[group].append(item)
            
            for group_name, group_items in groups.items():
                if group_name != "其他":
                    plan_lines.append(f"\n◆ {group_name}组测试：")
                else:
                    plan_lines.append(f"\n◆ 其他测试项：")
                
                for item in sorted(group_items, key=lambda x: x.sequence_number):
                    # 检查是否可并行
                    parallel_info = self._get_parallel_info(item, result)
                    parallel_text = f" [可与序号{parallel_info}并行]" if parallel_info else ""
                    
                    plan_lines.append(f"  {item.sequence_number:2d}. {item.test_item}{parallel_text}")
                    
                    # 添加依赖信息
                    if item.dependency_level > 0:
                        plan_lines.append(f"      ⚠ 依赖层级{item.dependency_level}，需等待前置测试完成")
                    
                    # 添加资源冲突警告
                    if item.resource_conflicts:
                        conflicts = ', '.join(item.resource_conflicts[:2])
                        plan_lines.append(f"      ⚠ 资源冲突：{conflicts}")
            
            plan_lines.append("")
        
        # 并行执行建议
        plan_lines.append("【并行执行建议】")
        plan_lines.append("-" * 60)
        plan_lines.append("以下测试项可同时进行，提高测试效率：")
        plan_lines.append("")
        
        parallel_count = 0
        for i, group in enumerate(result.parallel_groups, 1):
            if len(group) > 1:  # 只显示真正并行的组
                parallel_count += 1
                items = [result.sequence_items[idx] for idx in group]
                plan_lines.append(f"并行组{parallel_count}：")
                for item in items:
                    plan_lines.append(f"  • {item.test_item}")
                plan_lines.append("")
        
        # 关键提醒
        plan_lines.append("【关键提醒】")
        plan_lines.append("-" * 60)
        plan_lines.append("1. 必须按序号顺序执行，不可跳过")
        plan_lines.append("2. 有依赖关系的测试项必须等待前置测试完成")
        plan_lines.append("3. 存在资源冲突的测试项不能同时进行") 
        plan_lines.append("4. 每个阶段内的测试可根据资源情况灵活安排")
        plan_lines.append("5. 具体时间安排由项目组根据实际情况确定")
        plan_lines.append("")
        
        # 统计信息
        stats = result.statistics
        plan_lines.append("【计划统计】")
        plan_lines.append("-" * 60)
        plan_lines.append(f"总测试项数：{stats['总测试项数']} 项")
        plan_lines.append(f"可并行组数：{parallel_count} 组")
        plan_lines.append(f"最大并行度：{stats['最大并行度']} 项同时进行")
        plan_lines.append("")
        
        for phase, count in stats['各阶段测试数量'].items():
            phase_short = phase.replace("专项测试", "测试")
            plan_lines.append(f"{phase_short}：{count} 项")
        
        return '\n'.join(plan_lines)
    
    def _get_parallel_info(self, item, result):
        """获取并行信息"""
        for group in result.parallel_groups:
            if len(group) > 1:
                # 找到当前项在组中的位置
                item_indices = []
                for idx in group:
                    if result.sequence_items[idx].test_id == item.test_id:
                        continue
                    item_indices.append(str(result.sequence_items[idx].sequence_number))
                
                if item_indices:
                    return ','.join(item_indices[:2])  # 最多显示2个
        return None


def main():
    """主函数"""
    print("实用测试计划生成器")
    print("生成不依赖具体时间的测试执行计划")
    
    try:
        generator = PracticalTestPlanGenerator()
        plan = generator.generate_plan('test_data.json')
        
        # 输出到控制台（部分）
        lines = plan.split('\n')
        print("\n" + "="*60)
        print("测试计划预览（前30行）：")
        print("="*60)
        for line in lines[:30]:
            print(line)
        
        if len(lines) > 30:
            print(f"... 还有 {len(lines)-30} 行内容")
        
        # 保存到文件
        output_file = "项目验收测试执行计划.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(plan)
        
        print(f"\n完整计划已保存到：{output_file}")
        print("\n优势：")
        print("  • 按优先级和依赖关系排序")
        print("  • 明确标注并行执行建议")
        print("  • 不依赖时间估计，实用性强")
        print("  • 可根据实际情况灵活调整时间")
        
    except Exception as e:
        print(f"错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()