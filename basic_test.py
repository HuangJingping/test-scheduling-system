"""
基础测试脚本 - 兼容Windows命令行
测试重构后系统的核心功能
"""
import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试模块导入"""
    print("="*50)
    print("测试模块导入")
    print("="*50)
    
    modules_to_test = [
        ('config', 'ConfigManager'),
        ('models', 'TestItem'),
        ('time_manager', 'WorkingTimeManager'),
    ]
    
    success_count = 0
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            cls = getattr(module, class_name)
            print(f"[OK] {module_name}.{class_name} 导入成功")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {module_name}.{class_name} 导入失败: {e}")
    
    print(f"\n导入测试结果: {success_count}/{len(modules_to_test)} 个模块成功")
    return success_count == len(modules_to_test)


def test_data_models():
    """测试数据模型"""
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
        print(f"[OK] TestItem创建成功: {test_item.test_item}")
        
        # 测试数据验证
        test_items = [test_item]
        errors = DataValidator.validate_test_items(test_items)
        if not errors:
            print("[OK] 数据验证通过")
        else:
            print(f"[WARN] 数据验证发现问题: {errors}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 数据模型测试失败: {e}")
        return False


def test_config():
    """测试配置管理"""
    print("\n" + "="*50)
    print("测试配置管理")
    print("="*50)
    
    try:
        from config import ConfigManager
        
        config = ConfigManager()
        print(f"[OK] 默认配置加载成功")
        print(f"  - 最大并行数: {config.scheduling.max_parallel}")
        print(f"  - 每天工作小时: {config.working_time.hours_per_day}")
        
        config.validate()
        print("[OK] 配置验证通过")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 配置管理测试失败: {e}")
        return False


def test_time_manager():
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
        day1 = time_manager.get_work_day_number(0)
        day2 = time_manager.get_work_day_number(8)
        
        if day1 == 1 and day2 == 2:
            print("[OK] 工作日计算正确")
        else:
            print(f"[FAIL] 工作日计算错误: day1={day1}, day2={day2}")
            return False
        
        # 测试休息日判断
        is_rest_day1 = time_manager.is_rest_day(0)      # 第1天
        is_rest_day7 = time_manager.is_rest_day(6*8)    # 第7天
        
        if not is_rest_day1 and is_rest_day7:
            print("[OK] 休息日判断正确")
        else:
            print(f"[FAIL] 休息日判断错误: day1={is_rest_day1}, day7={is_rest_day7}")
            return False
        
        # 测试时间格式化
        formatter = TimeFormatter(config)
        time_str = formatter.format_time(0)
        print(f"[OK] 时间格式化: {time_str}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 时间管理测试失败: {e}")
        return False


def test_architecture():
    """测试系统架构完整性"""
    print("\n" + "="*50)
    print("测试系统架构")
    print("="*50)
    
    try:
        # 测试核心模块是否存在
        required_files = [
            'config.py',
            'models.py', 
            'time_manager.py',
            'constraints.py',
            'priority_calculator.py',
            'test_data.json',
            'scheduler_config.json'
        ]
        
        missing_files = []
        for filename in required_files:
            if not os.path.exists(filename):
                missing_files.append(filename)
        
        if missing_files:
            print(f"[FAIL] 缺少文件: {missing_files}")
            return False
        else:
            print(f"[OK] 所有核心文件存在 ({len(required_files)} 个)")
        
        # 测试配置文件格式
        import json
        with open('scheduler_config.json', 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        required_config_sections = ['priority_weights', 'working_time', 'scheduling', 'output']
        for section in required_config_sections:
            if section not in config_data:
                print(f"[FAIL] 配置文件缺少section: {section}")
                return False
        
        print("[OK] 配置文件格式正确")
        
        # 测试数据文件格式
        with open('test_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'test_items' in data and 'instruments' in data:
            print(f"[OK] 数据文件格式正确 (测试项: {len(data['test_items'])})")
        else:
            print("[FAIL] 数据文件格式错误")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 架构测试失败: {e}")
        return False


def run_basic_tests():
    """运行基础测试"""
    print("开始运行基础功能测试")
    print("测试时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    tests = [
        ("模块导入", test_imports),
        ("数据模型", test_data_models), 
        ("配置管理", test_config),
        ("时间管理", test_time_manager),
        ("系统架构", test_architecture),
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
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n== 测试成功 ==")
        print("核心功能测试全部通过！")
        print("系统重构成功，架构完整！")
        print("\n提示：要运行完整的调度测试，请先安装依赖:")
        print("pip install pandas numpy xlsxwriter")
    else:
        print(f"\n== 测试失败 ==")
        print(f"有 {total - passed} 个测试失败")
    
    return passed == total


if __name__ == "__main__":
    success = run_basic_tests()
    sys.exit(0 if success else 1)