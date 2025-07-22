#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示视频专用脚本 - Windows兼容版本
简化的测试调度演示，适合录制演示视频
"""

import json
from sequence_scheduler import SequenceScheduler
from test_scheduler_refactored import TestScheduler

def demo_sequence_scheduling():
    """演示序列调度模式"""
    print("=" * 60)
    print("[序列调度模式] 测试调度系统演示")
    print("=" * 60)
    
    # 创建调度器
    scheduler = SequenceScheduler('scheduler_config.json')
    scheduler.load_data_from_file('demo_data_simple.json')
    
    print("\n[加载数据] 测试项目：")
    for item in scheduler.test_items:
        print(f"  {item.test_id}. {item.test_item} ({item.test_phase})")
    
    print(f"\n[依赖关系] 共{len(scheduler.dependencies)}个")
    for dependent, prerequisites in scheduler.dependencies.items():
        print(f"  {dependent} <- {', '.join(prerequisites)}")
    
    print(f"\n[仪器设备] 共{len(scheduler.instruments)}种")
    for instrument, count in scheduler.instruments.items():
        print(f"  {instrument}: {count}台")
    
    # 生成调度序列
    print("\n[执行调度] 正在生成执行序列...")
    result = scheduler.generate_sequence()
    
    if result:
        print(f"\n[调度成功] 生成了{len(result)}个执行项")
        print("\n[执行序列] 结果如下：")
        print("-" * 80)
        print(f"{'序号':<4} {'测试项':<20} {'阶段':<10} {'优先级':<6} {'依赖层级':<8}")
        print("-" * 80)
        
        for item in result[:10]:  # 只显示前10个，适合演示
            print(f"{item.sequence_number:<4} {item.test_item:<20} {item.test_phase:<10} "
                  f"{item.priority_rank:<6} {item.dependency_level:<8}")
        
        if len(result) > 10:
            print(f"... 还有{len(result)-10}个测试项")
        
        print(f"\n[输出文件] test_execution_sequence.txt")
    else:
        print("[调度失败] 无法生成序列")

def demo_time_scheduling():
    """演示时间调度模式"""
    print("\n" + "=" * 60)
    print("[时间调度模式] 测试调度系统演示") 
    print("=" * 60)
    
    # 创建调度器
    scheduler = TestScheduler('scheduler_config.json')
    scheduler.load_data_from_file('demo_data_simple.json')
    
    print(f"\n[系统配置] 参数设置：")
    print(f"  最大并行数：{scheduler.config.scheduling.max_parallel}")
    print(f"  每日工作时间：{scheduler.config.working_time.hours_per_day}小时")
    
    # 执行调度
    print("\n[执行调度] 正在执行时间调度...")
    result = scheduler.solve_schedule(max_parallel=3)
    
    if result:
        print(f"\n[调度成功] 时间安排完成")
        print(f"[统计信息] 调度结果：")
        print(f"  总测试项：{result.total_tests}")
        print(f"  总工期：{result.total_duration}小时")
        print(f"  并行效率：{result.parallel_efficiency:.1%}")
        
        print(f"\n[调度详情] 前5个调度项：")
        print("-" * 90)
        print(f"{'测试项':<25} {'开始时间':<12} {'持续时间':<8} {'状态':<10}")
        print("-" * 90)
        
        for i, item in enumerate(result.schedule[:5]):
            print(f"{item.test_item:<25} {item.start_time:<12} {item.duration:<8} {item.status:<10}")
        
        print(f"\n[输出文件] demo_schedule_result.xlsx")
    else:
        print("[调度失败] 无法完成时间安排")

def main():
    """主演示函数"""
    print("[演示开始] 欢迎观看测试调度系统演示")
    print("本系统解决项目验收阶段的测试安排问题")
    
    # 演示序列调度
    demo_sequence_scheduling()
    
    # 演示时间调度  
    demo_time_scheduling()
    
    print("\n" + "=" * 60)
    print("[演示完成] 感谢观看！")
    print("[项目地址] https://github.com/HuangJingping/test-scheduling-system")
    print("[请支持] 如果对您有帮助，请给项目点个Star！")
    print("=" * 60)

if __name__ == "__main__":
    main()