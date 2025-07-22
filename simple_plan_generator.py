"""
简化的测试执行计划生成器
生成基于顺序的测试计划，不依赖时间估计
"""
import sys
import os
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sequence_scheduler import SequenceScheduler


def generate_simple_plan():
    """生成简化的测试执行计划"""
    
    try:
        # 创建调度器
        scheduler = SequenceScheduler('scheduler_config.json')
        scheduler.load_data_from_file('test_data.json')
        
        # 生成序列
        result = scheduler.generate_sequence()
        
        print("=" * 60)
        print("项目验收测试执行计划（基于顺序，不依赖时间）")
        print("=" * 60)
        
        print("\n计划说明：")
        print("1. 按优先级和依赖关系排序")
        print("2. 具体时间由项目组安排")
        print("3. 严格按依赖关系执行")
        print("4. 可参考并行建议提高效率")
        
        print("\n" + "=" * 60)
        print("测试执行顺序")
        print("=" * 60)
        
        # 简化输出格式
        for i, item in enumerate(result.sequence_items, 1):
            phase_short = item.test_phase.replace("专项测试", "阶段").replace("（", "(").replace("）", ")")
            if len(phase_short) > 20:
                phase_short = phase_short[:20] + "..."
            
            group_short = item.test_group[:8] if item.test_group else "其他"
            
            print(f"{i:2d}. [{phase_short}] {group_short} - {item.test_item}")
            
            if item.dependency_level > 0:
                print(f"    依赖层级: {item.dependency_level}")
        
        print("\n" + "=" * 60)
        print("并行执行建议")
        print("=" * 60)
        
        parallel_shown = 0
        for i, group in enumerate(result.parallel_groups):
            if len(group) > 1:  # 只显示真正并行的组
                parallel_shown += 1
                items = [result.sequence_items[idx] for idx in group]
                print(f"\n可并行组 {parallel_shown}（同时进行）：")
                for item in items:
                    seq_num = item.sequence_number
                    print(f"  - 序号{seq_num}: {item.test_item}")
        
        print(f"\n共识别出 {parallel_shown} 个可并行的测试组")
        
        print("\n" + "=" * 60)
        print("关键提醒")
        print("=" * 60)
        print("1. 必须按序号顺序执行")
        print("2. 有依赖的测试需等待前置完成")
        print("3. 并行组内的测试可同时进行")
        print("4. 具体时间安排根据实际情况确定")
        
        # 保存简化版本到文件
        plan_content = []
        plan_content.append("项目验收测试执行顺序计划")
        plan_content.append("=" * 40)
        plan_content.append("")
        plan_content.append("说明：本计划按优先级和依赖关系排序，不依赖具体时间估计")
        plan_content.append("")
        
        for i, item in enumerate(result.sequence_items, 1):
            phase_short = item.test_phase.replace("专项测试", "阶段")
            plan_content.append(f"{i:2d}. {item.test_item}")
            plan_content.append(f"    阶段: {phase_short}")
            plan_content.append(f"    测试组: {item.test_group}")
            if item.dependency_level > 0:
                plan_content.append(f"    依赖层级: {item.dependency_level}")
            plan_content.append("")
        
        plan_content.append("并行执行建议：")
        plan_content.append("-" * 20)
        for i, group in enumerate(result.parallel_groups):
            if len(group) > 1:
                items = [result.sequence_items[idx] for idx in group]
                plan_content.append(f"并行组{i+1}:")
                for item in items:
                    plan_content.append(f"  - {item.test_item}")
                plan_content.append("")
        
        # 写入文件
        with open("test_execution_plan.txt", 'w', encoding='utf-8') as f:
            f.write('\n'.join(plan_content))
        
        print(f"\n详细计划已保存到: test_execution_plan.txt")
        
        return True
        
    except Exception as e:
        print(f"生成计划时发生错误: {e}")
        return False


if __name__ == "__main__":
    print("生成不依赖时间估计的测试执行计划")
    success = generate_simple_plan()
    
    if success:
        print("\n[成功] 测试执行计划生成完成！")
        print("优势:")
        print("  • 不依赖时间估计，实用性强")
        print("  • 严格遵循依赖关系")
        print("  • 提供并行执行建议")
        print("  • 可根据实际情况调整")
    else:
        print("\n[失败] 计划生成过程中出现问题")