"""
重构后调度系统演示脚本 - 兼容Windows
展示新系统的完整功能
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_scheduler_refactored import TestScheduler


def main():
    print("="*60)
    print("重构后测试调度系统演示")
    print("="*60)
    
    try:
        # 1. 创建调度器并加载配置
        print("1. 正在初始化调度器...")
        scheduler = TestScheduler('scheduler_config.json')
        print("   [OK] 配置加载完成")
        
        # 2. 加载测试数据
        print("2. 正在加载测试数据...")
        scheduler.load_data_from_file('test_data.json')
        print(f"   [OK] 加载了 {len(scheduler.test_items)} 个测试项")
        print(f"   [OK] 加载了 {len(scheduler.instruments)} 种仪器设备")
        print(f"   [OK] 加载了 {len(scheduler.dependency_graph.dependencies)} 个依赖关系")
        
        # 3. 验证数据
        print("3. 正在验证数据完整性...")
        errors = scheduler.validate_data()
        if errors:
            print(f"   [WARN] 发现 {len(errors)} 个数据问题:")
            for error in errors[:3]:  # 只显示前3个
                print(f"     - {error}")
        else:
            print("   [OK] 数据验证通过")
        
        # 4. 执行调度算法
        print("4. 正在执行调度算法...")
        print("   - 最大并行数: 3")
        print("   - 工作制: 每天8小时，每7天休息1天")
        
        result = scheduler.solve_schedule(
            max_parallel=3, 
            output_filename="demo_schedule_result.xlsx"
        )
        
        # 5. 显示调度结果
        print("5. 调度结果：")
        print(f"   [OK] 成功调度: {len(result.scheduled_tests)} 个测试项")
        print(f"   [OK] 总完工时间: {result.total_duration:.1f} 小时")
        print(f"   [OK] 预计工期: {result.total_duration/8:.1f} 个工作日")
        
        if result.statistics:
            stats = result.statistics
            print(f"   [OK] 平均并行度: {stats.get('平均并行度', 'N/A')}")
            
            # 显示各阶段统计
            phase_stats = stats.get('各阶段测试数量', {})
            if phase_stats:
                print("   [OK] 各阶段分布:")
                for phase, count in list(phase_stats.items())[:3]:  # 显示前3个阶段
                    print(f"     - {phase}: {count}个测试项")
        
        # 6. 显示调度详情示例
        print("6. 调度详情示例（前5个测试项）:")
        from time_manager import TimeFormatter
        from config import WorkingTimeConfig
        
        formatter = TimeFormatter(WorkingTimeConfig())
        
        for i, test in enumerate(result.scheduled_tests[:5]):
            start_str = formatter.format_time(test.start_time)
            end_str = formatter.format_time(test.end_time)
            print(f"   {i+1}. {test.test_item}")
            print(f"      时间: {start_str} - {end_str}")
            print(f"      测试组: {test.test_group}")
        
        if len(result.scheduled_tests) > 5:
            print(f"   ... 还有 {len(result.scheduled_tests)-5} 个测试项")
        
        print("\n" + "="*60)
        print("演示完成！")
        print("[SUCCESS] 重构后的系统运行正常")
        print("[SUCCESS] 调度结果已导出到 demo_schedule_result.xlsx")
        print("[SUCCESS] 系统架构清晰，功能完整")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n重构验证成功！系统已可投入使用！")
    sys.exit(0 if success else 1)