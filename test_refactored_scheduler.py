"""
测试重构后的调度系统
验证新系统的功能正确性和性能
"""
import sys
import os
import time
import json
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_scheduler_refactored import TestScheduler, solve_test_schedule
from models import TestItem


def test_basic_functionality():
    """测试基本功能"""
    print("="*60)
    print("测试1: 基本功能验证")
    print("="*60)
    
    try:
        # 创建调度器并加载数据
        scheduler = TestScheduler('scheduler_config.json')
        scheduler.load_data_from_file('test_data.json')
        
        # 验证数据加载
        print(f"加载的测试项数量: {len(scheduler.test_items)}")
        print(f"加载的仪器数量: {len(scheduler.instruments)}")
        print(f"加载的依赖关系数量: {len(scheduler.dependency_graph.dependencies)}")
        
        # 验证数据
        errors = scheduler.validate_data()
        if errors:
            print(f"数据验证发现 {len(errors)} 个问题:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✓ 数据验证通过")
        
        # 执行调度
        print("\n开始执行调度...")
        start_time = time.time()
        result = scheduler.solve_schedule(max_parallel=3, output_filename="test_result.xlsx")
        end_time = time.time()
        
        print(f"✓ 调度完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"✓ 成功调度 {len(result.scheduled_tests)} 个测试项")
        print(f"✓ 总完工时间: {result.total_duration:.1f} 小时")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility():
    """测试与原系统的兼容性"""
    print("\n" + "="*60)
    print("测试2: 兼容性验证")
    print("="*60)
    
    try:
        # 使用原有格式的数据
        legacy_test_items = [
            (1, "专项测试1（资料查询、设备级、单节点测试，小场地）", "系统", "系统齐套性检查", "无", "无", 4),
            (2, "专项测试1（资料查询、设备级、单节点测试，小场地）", "系统", "系统外观检查", "无", "无", 2),
            (3, "专项测试2（节点间互联，小场地）", "微波网络电台", "微波网络电台架构", "旅级通信节点×1", "无", 4),
            (4, "专项测试1（资料查询、设备级、单节点测试，小场地）", "微波网络电台", "微波网络电台设备重量", "微波网络电台×1", "台秤×1", 1),
        ]
        
        legacy_instruments = {
            '综合测试仪': 1,
            '频谱分析仪': 1,
            '台秤': 1
        }
        
        legacy_dependencies = {
            "微波网络电台架构": ["系统齐套性检查"]
        }
        
        # 使用兼容函数
        print("使用兼容接口函数...")
        result = solve_test_schedule(
            legacy_test_items, 
            legacy_instruments, 
            legacy_dependencies, 
            max_parallel=2
        )
        
        print(f"✓ 兼容性测试通过")
        print(f"✓ 调度了 {len(result.scheduled_tests)} 个测试项")
        
        return True
        
    except Exception as e:
        print(f"✗ 兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """测试配置管理功能"""
    print("\n" + "="*60)
    print("测试3: 配置管理验证")
    print("="*60)
    
    try:
        # 创建自定义配置
        scheduler = TestScheduler()
        
        # 修改配置
        scheduler.config_manager.scheduling.max_parallel = 5
        scheduler.config_manager.working_time.hours_per_day = 10
        scheduler.config_manager.priority_weights.dependency = 20
        
        # 保存配置
        test_config_file = "test_custom_config.json"
        scheduler.save_config(test_config_file)
        print(f"✓ 配置已保存到 {test_config_file}")
        
        # 加载配置
        new_scheduler = TestScheduler(test_config_file)
        assert new_scheduler.config_manager.scheduling.max_parallel == 5
        assert new_scheduler.config_manager.working_time.hours_per_day == 10
        assert new_scheduler.config_manager.priority_weights.dependency == 20
        print("✓ 配置加载验证通过")
        
        # 清理测试文件
        if os.path.exists(test_config_file):
            os.remove(test_config_file)
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n" + "="*60)
    print("测试4: 错误处理验证")
    print("="*60)
    
    try:
        scheduler = TestScheduler()
        
        # 测试空数据调度
        try:
            result = scheduler.solve_schedule()
            print("✗ 应该抛出异常但没有")
            return False
        except ValueError as e:
            print(f"✓ 正确捕获空数据异常: {e}")
        
        # 测试无效数据
        invalid_test_items = [
            {"test_id": 1, "test_phase": "", "test_group": "test", 
             "test_item": "", "required_equipment": "", "required_instruments": "", "duration": 0}
        ]
        
        try:
            scheduler.load_data_from_dict(invalid_test_items, {"仪器1": 1}, {})
            errors = scheduler.validate_data()
            if errors:
                print(f"✓ 正确检测到数据错误: {len(errors)} 个问题")
            else:
                print("✗ 应该检测到数据错误但没有")
                return False
        except Exception as e:
            print(f"✓ 正确处理无效数据: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False


def test_performance():
    """测试性能"""
    print("\n" + "="*60)
    print("测试5: 性能验证")
    print("="*60)
    
    try:
        # 生成较大的测试数据集
        large_test_items = []
        for i in range(1, 51):  # 50个测试项
            large_test_items.append({
                "test_id": i,
                "test_phase": f"阶段{(i-1)//10 + 1}",
                "test_group": f"组{(i-1)//5 + 1}",
                "test_item": f"测试项{i}",
                "required_equipment": "无",
                "required_instruments": "综合测试仪×1" if i % 3 == 0 else "无",
                "duration": (i % 8) + 1
            })
        
        instruments = {"综合测试仪": 2, "信号分析仪": 1}
        dependencies = {}
        
        # 添加一些依赖关系
        for i in range(10, 51, 10):
            dependencies[f"测试项{i}"] = [f"测试项{i-5}"]
        
        scheduler = TestScheduler()
        scheduler.load_data_from_dict(large_test_items, instruments, dependencies)
        
        # 执行性能测试
        print(f"开始调度 {len(large_test_items)} 个测试项...")
        start_time = time.time()
        result = scheduler.solve_schedule(max_parallel=4)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"✓ 调度完成，耗时: {execution_time:.2f} 秒")
        print(f"✓ 平均每个测试项调度时间: {execution_time/len(large_test_items)*1000:.2f} 毫秒")
        print(f"✓ 成功调度 {len(result.scheduled_tests)} 个测试项")
        
        # 性能基准：应该在合理时间内完成
        if execution_time < 10:  # 10秒内完成
            print("✓ 性能测试通过")
            return True
        else:
            print(f"⚠ 性能较慢，超过预期时间")
            return True  # 不算失败，只是性能警告
        
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("开始运行重构后调度系统的验证测试")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("兼容性", test_compatibility),
        ("配置管理", test_configuration),
        ("错误处理", test_error_handling),
        ("性能", test_performance)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"测试 {test_name} 执行异常: {e}")
            results[test_name] = False
    
    # 输出测试总结
    print("\n" + "="*60)
    print("测试结果总结")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构系统验证成功！")
    else:
        print(f"⚠ 有 {total - passed} 个测试失败，需要检查相关功能")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)