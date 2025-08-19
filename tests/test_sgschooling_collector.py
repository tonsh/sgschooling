"""
SGSchooling数据采集器测试
验证数据采集功能是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from primary_rank.collectors.sgschooling_collector import SGSchoolingCollector
from primary_rank.storage.data_storage import DataStorage
from primary_rank.data_collector import SGPrimaryDataCollector


async def test_region_discovery():
    """测试区域发现功能"""
    print("🔍 测试区域发现功能...")
    
    try:
        async with SGSchoolingCollector() as collector:
            regions = await collector.discover_regions()
            
            if regions:
                print(f"✅ 成功发现 {len(regions)} 个区域")
                print(f"前5个区域: {regions[:5]}")
                return True, regions
            else:
                print("❌ 未发现任何区域")
                return False, []
                
    except Exception as e:
        print(f"❌ 区域发现测试失败: {e}")
        return False, []


async def test_single_region_scraping():
    """测试单个区域数据采集"""
    print("\n📊 测试单个区域数据采集...")
    
    # 使用一个已知的区域进行测试
    test_region = "ang-mo-kio"
    
    try:
        async with SGSchoolingCollector() as collector:
            region_data = await collector.scrape_region_data(test_region)
            
            if region_data:
                print(f"✅ 成功采集区域 {test_region}")
                print(f"学校数量: {len(region_data.schools)}")
                
                if region_data.schools:
                    sample_school = region_data.schools[0]
                    print(f"示例学校: {sample_school.school_name}")
                    print(f"Phase 1 空缺: {sample_school.phase_1.vacancy}")
                
                return True, region_data
            else:
                print(f"❌ 采集区域 {test_region} 失败")
                return False, None
                
    except Exception as e:
        print(f"❌ 单区域采集测试失败: {e}")
        return False, None


async def test_data_storage():
    """测试数据存储功能"""
    print("\n💾 测试数据存储功能...")
    
    try:
        storage = DataStorage("test_data")
        
        # 创建测试数据
        from primary_rank.models.school_data import SchoolData, PhaseData
        from primary_rank.models.region_data import RegionData
        from datetime import datetime
        
        test_school = SchoolData(
            name="测试小学",
            region="test-region",
            phase_1=PhaseData(vacancy=100, applied=150, taken=100),
            phase_2a=PhaseData(vacancy=50, applied=75, taken=50),
            phase_2b=PhaseData(vacancy=30, applied=40, taken=30),
            phase_2c=PhaseData(vacancy=20, applied=25, taken=20),
            phase_2cs=PhaseData(vacancy=10, applied=12, taken=10),
            last_updated=datetime.now(),
            source_url="https://test.com"
        )
        
        test_region_data = RegionData.from_schools(
            name="test-region",
            schools=[test_school]
        )
        
        # 测试保存
        file_path = storage.save_region_data(test_region_data)
        print(f"✅ 数据保存成功: {file_path}")
        
        # 测试加载
        loaded_data = storage.load_region_data("test-region")
        if loaded_data:
            print(f"✅ 数据加载成功: {loaded_data.name}")
            print(f"学校数量: {len(loaded_data.schools)}")
            return True
        else:
            print("❌ 数据加载失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据存储测试失败: {e}")
        return False


async def test_full_collector():
    """测试完整的数据采集器"""
    print("\n🚀 测试完整数据采集器...")
    
    try:
        collector = SGPrimaryDataCollector("test_data")
        
        # 测试数据摘要（应该返回None，因为还没有数据）
        summary = collector.get_latest_data_summary()
        if summary is None:
            print("✅ 空数据摘要测试通过")
        else:
            print(f"✅ 现有数据摘要: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整采集器测试失败: {e}")
        return False


async def test_data_validation():
    """测试数据验证功能"""
    print("\n🔍 测试数据验证功能...")
    
    try:
        from primary_rank.collectors.data_validator import DataValidator
        from primary_rank.models.school_data import SchoolData, PhaseData
        from datetime import datetime
        
        validator = DataValidator()
        
        # 创建有效的测试数据
        valid_school = SchoolData(
            name="有效测试小学",
            region="ang-mo-kio",
            phase_1=PhaseData(vacancy=100, applied=150, taken=100),
            phase_2a=PhaseData(vacancy=50, applied=75, taken=50),
            phase_2b=PhaseData(vacancy=30, applied=40, taken=30),
            phase_2c=PhaseData(vacancy=20, applied=25, taken=20),
            phase_2cs=PhaseData(vacancy=10, applied=12, taken=10),
            last_updated=datetime.now(),
            source_url="https://sgschooling.com/test"
        )
        
        # 验证有效数据
        validation_result = validator.validate_school_data(valid_school)
        if validation_result['is_valid']:
            print("✅ 有效数据验证通过")
        else:
            print(f"❌ 有效数据验证失败: {validation_result['errors']}")
        
        # 创建无效的测试数据
        invalid_school = SchoolData(
            name="",  # 空名称
            region="test",
            phase_1=PhaseData(vacancy=-10, applied=150, taken=200),  # 负数空缺，录取超过申请
            phase_2a=PhaseData(vacancy=50, applied=75, taken=50),
            phase_2b=PhaseData(vacancy=30, applied=40, taken=30),
            phase_2c=PhaseData(vacancy=20, applied=25, taken=20),
            phase_2cs=PhaseData(vacancy=10, applied=12, taken=10),
            last_updated=datetime.now(),
            source_url="invalid"  # 无效URL
        )
        
        # 验证无效数据
        invalid_result = validator.validate_school_data(invalid_school)
        if not invalid_result['is_valid']:
            print("✅ 无效数据验证通过")
            print(f"发现错误: {len(invalid_result['errors'])} 个")
        else:
            print("❌ 无效数据验证失败，应该检测出错误")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据验证测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 开始SGSchooling数据采集器测试...")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    tests = [
        ("区域发现", test_region_discovery),
        ("单区域采集", test_single_region_scraping),
        ("数据存储", test_data_storage),
        ("完整采集器", test_full_collector),
        ("数据验证", test_data_validation)
    ]
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            test_results.append((test_name, result))
            
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            test_results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        if isinstance(result, tuple):
            result = result[0]  # 提取布尔结果
        
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！数据采集器已准备就绪")
    else:
        print("⚠️  部分测试失败，请检查相关功能")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())