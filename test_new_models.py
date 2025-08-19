#!/usr/bin/env python3
"""
测试新的数据模型结构
"""

from primary_rank.models.school_data import SchoolData, PhaseData
from primary_rank.models.region_data import RegionData

def test_school_vacancy_property():
    """测试学校vacancy属性自动计算"""
    print("=== 测试SchoolData.vacancy自动计算 ===")
    
    # 创建测试数据
    school = SchoolData(
        name="Test Primary School",
        cn_name="测试小学",
        region="test",
        phase_1=PhaseData(vacancy=20, applied=18, taken=18),
        phase_2a=PhaseData(vacancy=30, applied=45, taken=30),
        phase_2b=PhaseData(vacancy=25, applied=40, taken=25),
        phase_2c=PhaseData(vacancy=50, applied=35, taken=35),
        phase_2cs=PhaseData(vacancy=37, applied=20, taken=20)
    )
    
    print(f"学校名称: {school.cn_name}")
    print(f"各阶段taken: {school.phase_1.taken}, {school.phase_2a.taken}, {school.phase_2b.taken}, {school.phase_2c.taken}")
    print(f"Phase2Cs vacancy: {school.phase_2cs.vacancy}")
    print(f"计算公式: {school.phase_1.taken} + {school.phase_2a.taken} + {school.phase_2b.taken} + {school.phase_2c.taken} + {school.phase_2cs.vacancy}")
    print(f"自动计算的vacancy: {school.vacancy}")
    print(f"总申请数: {school.total_applied}")
    print(f"总录取数: {school.total_taken}")
    
    # 验证计算正确性
    expected_vacancy = 18 + 30 + 25 + 35 + 37  # = 145
    assert school.vacancy == expected_vacancy, f"vacancy计算错误: {school.vacancy} != {expected_vacancy}"
    print("✅ vacancy计算正确")

def test_region_from_schools():
    """测试从学校列表创建区域数据"""
    print("\n=== 测试RegionData.from_schools ===")
    
    # 创建测试学校
    school1 = SchoolData(
        name="School A",
        cn_name="学校A",
        region="test",
        phase_1=PhaseData(vacancy=20, applied=18, taken=18),
        phase_2a=PhaseData(vacancy=30, applied=45, taken=30),
        phase_2b=PhaseData(vacancy=25, applied=40, taken=25),
        phase_2c=PhaseData(vacancy=50, applied=35, taken=35),
        phase_2cs=PhaseData(vacancy=37, applied=20, taken=20)
    )
    
    school2 = SchoolData(
        name="School B",
        cn_name="学校B", 
        region="test",
        phase_1=PhaseData(vacancy=15, applied=20, taken=15),
        phase_2a=PhaseData(vacancy=25, applied=35, taken=25),
        phase_2b=PhaseData(vacancy=30, applied=45, taken=30),
        phase_2c=PhaseData(vacancy=40, applied=38, taken=38),
        phase_2cs=PhaseData(vacancy=57, applied=20, taken=20)
    )
    
    schools = [school1, school2]
    
    # 创建区域数据
    region = RegionData.from_schools("test", "测试区", schools)
    
    print(f"区域名称: {region.cn_name}")
    print(f"学校数量: {region.school_num}")
    print(f"总vacancy: {region.vacancy}")
    print(f"总applied: {region.applied}")
    print(f"总taken: {region.taken}")
    print(f"成功率: {region.success_rate:.2%}")
    print(f"竞争比例: {region.competition_ratio:.2f}")
    
    # 验证计算
    expected_vacancy = school1.vacancy + school2.vacancy  # 145 + 165 = 310
    expected_applied = school1.total_applied + school2.total_applied  # 158 + 158 = 316
    expected_taken = school1.total_taken + school2.total_taken  # 128 + 128 = 256
    
    assert region.school_num == 2
    assert region.vacancy == expected_vacancy
    assert region.applied == expected_applied
    assert region.taken == expected_taken
    
    print("✅ 区域数据聚合正确")

def test_json_serialization():
    """测试JSON序列化和反序列化"""
    print("\n=== 测试JSON序列化 ===")
    
    # 创建测试数据
    original_school = SchoolData(
        name="Test School",
        cn_name="测试学校",
        region="test",
        phase_1=PhaseData(vacancy=20, applied=18, taken=18),
        phase_2a=PhaseData(vacancy=30, applied=45, taken=30),
        phase_2b=PhaseData(vacancy=25, applied=40, taken=25),
        phase_2c=PhaseData(vacancy=50, applied=35, taken=35),
        phase_2cs=PhaseData(vacancy=37, applied=20, taken=20)
    )
    
    # 序列化为字典
    school_dict = original_school.to_dict()
    print(f"序列化后的vacancy: {school_dict['vacancy']}")
    
    # 反序列化
    restored_school = SchoolData.from_dict(school_dict)
    print(f"反序列化后的vacancy: {restored_school.vacancy}")
    
    # 验证数据一致性
    assert original_school.name == restored_school.name
    assert original_school.cn_name == restored_school.cn_name
    assert original_school.vacancy == restored_school.vacancy
    assert original_school.total_applied == restored_school.total_applied
    assert original_school.total_taken == restored_school.total_taken
    
    print("✅ JSON序列化和反序列化正确")

if __name__ == "__main__":
    test_school_vacancy_property()
    test_region_from_schools()
    test_json_serialization()
    print("\n🎉 所有测试通过！新的数据模型结构工作正常。")