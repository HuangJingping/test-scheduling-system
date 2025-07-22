"""
简化测试脚本 - 不依赖外部库
仅测试核心调度逻辑
"""
import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 先测试各个模块是否能正常导入
def test_imports():
    """测试模块导入"""
    print("="*50)
    print("测试模块导入")
    print("="*50)
    
    modules_to_test = [
        ('config', 'ConfigManager'),
        ('models', 'TestItem'),
        ('time_manager', 'WorkingTimeManager'),
        ('constraints', 'ConstraintChecker'),
        ('priority_calculator', 'PriorityManager'),
    ]
    
    success_count = 0
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"✗ {module_name}.{class_name} 导入失败: {e}")
    
    print(f"\n导入测试结果: {success_count}/{len(modules_to_test)} 个模块成功")
    return success_count == len(modules_to_test)


def test_basic_data_models():
    """测试基本数据模型"""
    print("\n" + "="*50)
    print("测试数据模型")
    print("="*50)
    
    try:
        from models import TestItem, DependencyGraph, DataValidator
        
        # 测试TestItem创建
        test_item = TestItem(
            test_id=1,
            test_phase="测试阶段1",
            test_group="测试组1", 
            test_item="测试项目1",
            required_equipment="设备1",
            required_instruments="仪器1",
            duration=4
        )
        print(f"✓ TestItem创建成功: {test_item.test_item}")
        
        # 测试数据验证
        test_items = [test_item]
        errors = DataValidator.validate_test_items(test_items)
        if not errors:
            print("✓ 数据验证通过")
        else:
            print(f"⚠ 数据验证发现问题: {errors}")
        
        # 测试依赖关系图
        dependency_graph = DependencyGraph()
        dependency_graph.dependencies = {"测试项目1": []}
        dependency_graph.build_matrix(test_items)
        print("✓ 依赖关系图构建成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_management():
    """测试配置管理"""
    print("\n" + "="*50)
    print("测试配置管理")
    print("="*50)
    
    try:
        from config import ConfigManager
        
        # 测试默认配置
        config = ConfigManager()
        print(f"✓ 默认配置加载成功")
        print(f"  - 最大并行数: {config.scheduling.max_parallel}")
        print(f"  - 每天工作小时: {config.working_time.hours_per_day}")
        print(f"  - 依赖权重: {config.priority_weights.dependency}")
        
        # 测试配置验证
        config.validate()
        print("✓ 配置验证通过")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理测试失败: {e}")
        return False


def test_time_management():
    """测试时间管理"""
    print("\n" + "="*50)
    print("测试时间管理")
    print("="*50)
    
    try:
        from time_manager import WorkingTimeManager, TimeFormatter
        from config import WorkingTimeConfig
        
        config = WorkingTimeConfig()
        time_manager = WorkingTimeManager(config)
        
        # 测试工作日计算
        assert time_manager.get_work_day_number(0) == 1
        assert time_manager.get_work_day_number(8) == 2
        print("✓ 工作日计算正确")
        
        # 测试休息日判断
        assert not time_manager.is_rest_day(0)    # 第1天不是休息日
        assert time_manager.is_rest_day(6*8)      # 第7天是休息日
        print("✓ 休息日判断正确")
        
        # 测试跨天检查
        assert not time_manager.will_cross_day(0, 4)   # 不跨天
        assert time_manager.will_cross_day(6, 4)       # 跨天
        print("✓ 跨天检查正确")
        
        # 测试时间格式化
        formatter = TimeFormatter(config)
        time_str = formatter.format_time(0)
        print(f"✓ 时间格式化: {time_str}")
        
        return True
        
    except Exception as e:
        print(f"✗ 时间管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_constraints():
    """测试约束检查"""
    print("\n" + "="*50)
    print("测试约束检查")
    print("="*50)
    
    try:
        from models import TestItem, DependencyGraph, SchedulingState, ScheduledTest
        from constraints import ConstraintChecker, ResourceMatrix
        from config import SchedulingConfig
        
        # 创建测试数据
        test_items = [
            TestItem(1, "阶段1", "组1", "测试1", "设备1", "仪器1×1", 2),
            TestItem(2, "阶段1", "组2", "测试2", "设备2", "仪器1×1", 3),
        ]
        
        instruments = {"仪器1": 1}
        dependency_graph = DependencyGraph()
        dependency_graph.build_matrix(test_items)
        
        config = SchedulingConfig()
        checker = ConstraintChecker(test_items, instruments, dependency_graph, config)
        
        print("✓ 约束检查器创建成功")
        
        # 测试资源矩阵
        assert hasattr(checker, 'resource_matrix')
        print("✓ 资源矩阵创建成功")
        
        # 测试基本约束检查
        state = SchedulingState(current_time=0)
        can_schedule, reasons = checker.check_all_constraints(0, 0, state)
        print(f"✓ 约束检查完成: {can_schedule}")
        
        return True
        
    except Exception as e:
        print(f"✗ 约束检查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_simple_tests():
    """运行简化测试"""
    print("开始运行简化测试（不依赖外部库）")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    tests = [
        ("模块导入", test_imports),
        ("数据模型", test_basic_data_models), 
        ("配置管理", test_config_management),
        ("时间管理", test_time_management),
        ("约束检查", test_constraints),
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
    print("\n" + "="*50)
    print("测试结果总结")
    print("="*50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 核心功能测试全部通过！")
        print("💡 提示：要运行完整测试，请先安装依赖: pip install pandas numpy")
    else:
        print(f"⚠ 有 {total - passed} 个测试失败，需要检查相关功能")
    
    return passed == total


if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)