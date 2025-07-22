#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示视频专用脚本 - 修复版本
"""

import json
import sys
from sequence_scheduler import SequenceScheduler
from test_scheduler_refactored import TestScheduler

def demo_sequence_scheduling():
    """演示序列调度模式"""
    print("=" * 60)
    print("[SEQUENCE MODE] Test Scheduling System Demo")
    print("=" * 60)
    
    # 创建调度器
    scheduler = SequenceScheduler('scheduler_config.json')
    scheduler.load_data_from_file('demo_data_simple.json')
    
    print("\n[LOADED DATA] Test Items:")
    for item in scheduler.test_items:
        print(f"  {item.test_id}. {item.test_item} ({item.test_phase})")
    
    # 获取依赖关系
    dependencies = scheduler.dependency_graph.dependencies
    print(f"\n[DEPENDENCIES] Total: {len(dependencies)}")
    for dependent, prerequisites in dependencies.items():
        print(f"  {dependent} <- {', '.join(prerequisites)}")
    
    print(f"\n[INSTRUMENTS] Total: {len(scheduler.instruments)}")
    for instrument, count in scheduler.instruments.items():
        print(f"  {instrument}: {count}")
    
    # 生成调度序列
    print("\n[SCHEDULING] Generating execution sequence...")
    result = scheduler.generate_sequence()
    
    if result:
        sequence_items = result.sequence_items
        print(f"\n[SUCCESS] Generated {len(sequence_items)} sequence items")
        print("\n[SEQUENCE] Execution order:")
        print("-" * 80)
        print(f"{'No':<4} {'Test Item':<25} {'Phase':<12} {'Priority':<8} {'Level':<6}")
        print("-" * 80)
        
        for item in sequence_items[:8]:  # 显示前8个
            print(f"{item.sequence_number:<4} {item.test_item:<25} {item.test_phase:<12} "
                  f"{item.priority_rank:<8} {item.dependency_level:<6}")
        
        print(f"\n[OUTPUT] File: test_execution_sequence.txt")
    else:
        print("[FAILED] Cannot generate sequence")

def demo_time_scheduling():
    """演示时间调度模式"""
    print("\n" + "=" * 60)
    print("[TIME MODE] Test Scheduling System Demo") 
    print("=" * 60)
    
    # 创建调度器
    scheduler = TestScheduler('scheduler_config.json')
    scheduler.load_data_from_file('demo_data_simple.json')
    
    print(f"\n[CONFIG] System initialized with configuration file")
    
    # 执行调度
    print("\n[SCHEDULING] Executing time-based scheduling...")
    result = scheduler.solve_schedule(max_parallel=3)
    
    if result:
        print(f"\n[SUCCESS] Time scheduling completed successfully")
        print(f"[STATISTICS] Generated detailed schedule with time allocations")
        print(f"[SCHEDULE] All test items scheduled with dependencies resolved")
        print(f"\n[OUTPUT] Files: test_schedule_refactored.xlsx + detailed report")
    else:
        print("[FAILED] Cannot complete time scheduling")

def main():
    """主演示函数"""
    print("[DEMO START] Test Scheduling System Demonstration")
    print("Solving project acceptance testing scheduling problems")
    
    try:
        # 演示序列调度
        demo_sequence_scheduling()
        
        # 演示时间调度  
        demo_time_scheduling()
        
        print("\n" + "=" * 60)
        print("[DEMO COMPLETE] Thank you for watching!")
        print("[PROJECT URL] https://github.com/HuangJingping/test-scheduling-system")
        print("[SUPPORT] Please give us a Star if helpful!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()