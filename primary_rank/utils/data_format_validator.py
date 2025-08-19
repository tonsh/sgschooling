"""
数据格式验证工具

验证JSON数据是否符合SGSchooling数据格式规范
"""

import json
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from ..models.school_data import SchoolData, PhaseData
from ..models.region_data import RegionData


class DataFormatValidator:
    """数据格式验证器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_json_file(self, file_path: str) -> Dict[str, Any]:
        """
        验证JSON文件格式
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            验证结果
        """
        self.errors = []
        self.warnings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.errors.append(f"文件不存在: {file_path}")
            return self._get_result()
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON格式错误: {e}")
            return self._get_result()
        
        # 验证数据结构
        self._validate_region_file_structure(data, file_path)
        
        return self._get_result()
    
    def _validate_region_file_structure(self, data: Dict[str, Any], file_path: str) -> None:
        """验证区域文件结构"""
        # 检查必要的顶层字段
        required_fields = ['region', 'schools', 'metadata']
        for field in required_fields:
            if field not in data:
                self.errors.append(f"缺少必要字段: {field}")
                return
        
        # 验证区域数据
        self._validate_region_data(data['region'])
        
        # 验证学校数据
        self._validate_schools_data(data['schools'])
        
        # 验证元数据
        self._validate_metadata(data['metadata'])
        
        # 验证数据一致性
        self._validate_data_consistency(data)
    
    def _validate_region_data(self, region_data: Dict[str, Any]) -> None:
        """验证区域数据"""
        required_fields = ['name', 'cn_name', 'school_num', 'vacancy', 'applied', 'taken']
        
        for field in required_fields:
            if field not in region_data:
                self.errors.append(f"区域数据缺少字段: {field}")
        
        # 验证数据类型和范围
        if 'school_num' in region_data:
            if not isinstance(region_data['school_num'], int) or region_data['school_num'] < 0:
                self.errors.append("school_num 必须是非负整数")
        
        for field in ['vacancy', 'applied', 'taken']:
            if field in region_data:
                if not isinstance(region_data[field], int) or region_data[field] < 0:
                    self.errors.append(f"{field} 必须是非负整数")
        
        # 验证逻辑关系
        if all(field in region_data for field in ['applied', 'taken']):
            if region_data['taken'] > region_data['applied']:
                self.warnings.append("区域录取数大于申请数，请检查数据")
    
    def _validate_schools_data(self, schools_data: List[Dict[str, Any]]) -> None:
        """验证学校数据列表"""
        if not isinstance(schools_data, list):
            self.errors.append("schools 必须是数组")
            return
        
        if len(schools_data) == 0:
            self.warnings.append("学校列表为空")
            return
        
        for i, school_data in enumerate(schools_data):
            self._validate_single_school(school_data, i)
    
    def _validate_single_school(self, school_data: Dict[str, Any], index: int) -> None:
        """验证单个学校数据"""
        prefix = f"学校[{index}]"
        
        # 检查必要字段 (vacancy现在是可选的，会自动计算)
        required_fields = ['name', 'cn_name', 'region', 
                          'phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
        
        for field in required_fields:
            if field not in school_data:
                self.errors.append(f"{prefix} 缺少字段: {field}")
        
        # 验证可选的vacancy字段类型
        if 'vacancy' in school_data:
            if not isinstance(school_data['vacancy'], int) or school_data['vacancy'] < 0:
                self.errors.append(f"{prefix} vacancy 必须是非负整数")
        
        # 验证各阶段数据
        phase_names = ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
        for phase_name in phase_names:
            if phase_name in school_data:
                self._validate_phase_data(school_data[phase_name], f"{prefix}.{phase_name}")
        
        # 验证vacancy计算公式
        if all(phase_name in school_data for phase_name in phase_names) and 'vacancy' in school_data:
            self._validate_vacancy_calculation(school_data, prefix)
    
    def _validate_phase_data(self, phase_data: Dict[str, Any], prefix: str) -> None:
        """验证阶段数据"""
        required_fields = ['vacancy', 'applied', 'taken']
        
        for field in required_fields:
            if field not in phase_data:
                self.errors.append(f"{prefix} 缺少字段: {field}")
            elif not isinstance(phase_data[field], int) or phase_data[field] < 0:
                self.errors.append(f"{prefix}.{field} 必须是非负整数")
        
        # 验证逻辑关系
        if 'applied' in phase_data and 'taken' in phase_data:
            if phase_data['taken'] > phase_data['applied']:
                self.warnings.append(f"{prefix} 录取数({phase_data['taken']}) > 申请数({phase_data['applied']})")
        
        if 'vacancy' in phase_data and 'taken' in phase_data:
            if phase_data['taken'] > phase_data['vacancy'] + 5:  # 允许少量超出
                self.warnings.append(f"{prefix} 录取数({phase_data['taken']}) 显著超过名额({phase_data['vacancy']})")
    
    def _validate_vacancy_calculation(self, school_data: Dict[str, Any], prefix: str) -> None:
        """验证vacancy计算公式: vacancy = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.vacancy"""
        try:
            calculated_vacancy = (
                school_data['phase_1']['taken'] +
                school_data['phase_2a']['taken'] +
                school_data['phase_2b']['taken'] +
                school_data['phase_2c']['taken'] +
                school_data['phase_2cs']['vacancy']
            )
            
            # 如果JSON中包含vacancy字段，验证其正确性
            if 'vacancy' in school_data:
                if school_data['vacancy'] != calculated_vacancy:
                    self.warnings.append(
                        f"{prefix} JSON中的vacancy字段({school_data['vacancy']}) "
                        f"与计算值({calculated_vacancy})不一致，将使用计算值"
                    )
        except KeyError as e:
            self.errors.append(f"{prefix} vacancy计算失败，缺少字段: {e}")
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """验证元数据"""
        required_fields = ['crawl_time', 'source_url', 'data_version']
        
        for field in required_fields:
            if field not in metadata:
                self.warnings.append(f"元数据缺少字段: {field}")
    
    def _validate_data_consistency(self, data: Dict[str, Any]) -> None:
        """验证数据一致性"""
        region_data = data.get('region', {})
        schools_data = data.get('schools', [])
        
        if not region_data or not schools_data:
            return
        
        # 验证学校数量
        if 'school_num' in region_data:
            if region_data['school_num'] != len(schools_data):
                self.errors.append(
                    f"区域学校数量不一致: region.school_num({region_data['school_num']}) "
                    f"!= 实际学校数({len(schools_data)})"
                )
        
        # 验证汇总数据
        if all(field in region_data for field in ['vacancy', 'applied', 'taken']):
            calculated_vacancy = sum(school.get('vacancy', 0) for school in schools_data)
            calculated_applied = sum(self._calculate_total_applied(school) for school in schools_data)
            calculated_taken = sum(self._calculate_total_taken(school) for school in schools_data)
            
            if region_data['vacancy'] != calculated_vacancy:
                self.errors.append(
                    f"区域总vacancy不一致: {region_data['vacancy']} != {calculated_vacancy}"
                )
            
            if region_data['applied'] != calculated_applied:
                self.errors.append(
                    f"区域总applied不一致: {region_data['applied']} != {calculated_applied}"
                )
            
            if region_data['taken'] != calculated_taken:
                self.errors.append(
                    f"区域总taken不一致: {region_data['taken']} != {calculated_taken}"
                )
    
    def _calculate_total_applied(self, school: Dict[str, Any]) -> int:
        """计算学校总申请数"""
        phases = ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
        return sum(school.get(phase, {}).get('applied', 0) for phase in phases)
    
    def _calculate_total_taken(self, school: Dict[str, Any]) -> int:
        """计算学校总录取数"""
        phases = ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
        return sum(school.get(phase, {}).get('taken', 0) for phase in phases)
    
    def _get_result(self) -> Dict[str, Any]:
        """获取验证结果"""
        return {
            "is_valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }
    
    def validate_and_load_models(self, file_path: str) -> Tuple[Optional[RegionData], List[SchoolData]]:
        """
        验证并加载为数据模型
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            (区域数据, 学校数据列表)
        """
        validation_result = self.validate_json_file(file_path)
        
        if not validation_result["is_valid"]:
            print(f"数据验证失败:")
            for error in validation_result["errors"]:
                print(f"  ❌ {error}")
            return None, []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 加载区域数据
            region = RegionData.from_dict(data['region'])
            
            # 加载学校数据
            schools = [SchoolData.from_dict(school) for school in data['schools']]
            
            return region, schools
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            return None, []


def validate_sample_data():
    """验证示例数据"""
    validator = DataFormatValidator()
    result = validator.validate_json_file("data/sample_data.json")
    
    print("=== 数据格式验证结果 ===")
    print(f"验证通过: {'✅' if result['is_valid'] else '❌'}")
    print(f"错误数量: {result['error_count']}")
    print(f"警告数量: {result['warning_count']}")
    
    if result['errors']:
        print("\n错误:")
        for error in result['errors']:
            print(f"  ❌ {error}")
    
    if result['warnings']:
        print("\n警告:")
        for warning in result['warnings']:
            print(f"  ⚠️  {warning}")
    
    # 尝试加载为模型
    if result['is_valid']:
        print("\n=== 数据模型加载测试 ===")
        region, schools = validator.validate_and_load_models("data/sample_data.json")
        
        if region and schools:
            print(f"✅ 成功加载区域数据: {region.cn_name}")
            print(f"✅ 成功加载学校数据: {len(schools)} 所学校")
            
            # 显示自动计算的vacancy值
            for school in schools:
                print(f"✅ {school.cn_name} vacancy自动计算为: {school.vacancy}")


if __name__ == "__main__":
    validate_sample_data()