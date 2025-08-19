"""
数据验证模块
负责验证采集到的数据的完整性和准确性
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import statistics
from ..models.school_data import SchoolData, PhaseData
from ..models.region_data import RegionData


class DataValidator:
    """数据验证器"""
    
    # 新加坡小学相关的常识性数据范围
    REASONABLE_RANGES = {
        'max_vacancy_per_phase': 300,  # 单个阶段最大空缺数
        'max_applications_per_phase': 2000,  # 单个阶段最大申请数
        'min_school_name_length': 5,  # 学校名称最小长度
        'max_school_name_length': 100,  # 学校名称最大长度
        'max_success_rate': 1.0,  # 最大成功率
        'min_success_rate': 0.0   # 最小成功率
    }
    
    # 已知的新加坡区域名称
    KNOWN_REGIONS = {
        'ang-mo-kio', 'bedok', 'bishan', 'bukit-batok', 'bukit-merah',
        'bukit-panjang', 'bukit-timah', 'central', 'choa-chu-kang',
        'clementi', 'geylang', 'hougang', 'jurong-east', 'jurong-west',
        'kallang', 'marine-parade', 'pasir-ris', 'punggol', 'queenstown',
        'sembawang', 'sengkang', 'serangoon', 'tampines', 'toa-payoh',
        'woodlands', 'yishun'
    }
    
    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_school_data(self, school: SchoolData) -> Dict[str, Any]:
        """
        验证单个学校数据
        
        Args:
            school: 学校数据对象
            
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        
        # 验证基础信息
        errors.extend(self._validate_basic_info(school))
        
        # 验证各阶段数据
        phase_errors, phase_warnings = self._validate_phases_data(school)
        errors.extend(phase_errors)
        warnings.extend(phase_warnings)
        
        # 验证数据一致性
        consistency_errors = self._validate_data_consistency(school)
        errors.extend(consistency_errors)
        
        # 验证合理性
        reasonableness_warnings = self._validate_reasonableness(school)
        warnings.extend(reasonableness_warnings)
        
        return {
            'school_name': school.school_name,
            'region': school.region,
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
    
    def validate_region_data(self, region_data: RegionData) -> Dict[str, Any]:
        """
        验证区域数据
        
        Args:
            region_data: 区域数据对象
            
        Returns:
            验证结果字典
        """
        errors = []
        warnings = []
        school_validations = []
        
        # 验证区域基础信息
        if not region_data.region_name or len(region_data.region_name.strip()) < 2:
            errors.append("区域名称无效")
        
        # 检查是否为已知区域
        if region_data.region_name not in self.KNOWN_REGIONS:
            warnings.append(f"未知区域名称: {region_data.region_name}")
        
        # 验证学校数量
        if len(region_data.schools) == 0:
            errors.append("区域内没有学校数据")
        elif len(region_data.schools) > 50:
            warnings.append(f"区域内学校数量异常多: {len(region_data.schools)}")
        
        # 验证每个学校的数据
        valid_schools = 0
        for school in region_data.schools:
            school_validation = self.validate_school_data(school)
            school_validations.append(school_validation)
            
            if school_validation['is_valid']:
                valid_schools += 1
        
        # 检查有效学校比例
        valid_ratio = valid_schools / len(region_data.schools) if region_data.schools else 0
        if valid_ratio < 0.5:
            errors.append(f"有效学校数据比例过低: {valid_ratio:.2%}")
        elif valid_ratio < 0.8:
            warnings.append(f"有效学校数据比例偏低: {valid_ratio:.2%}")
        
        # 验证时间戳
        time_warnings = self._validate_timestamp(region_data.crawl_timestamp)
        warnings.extend(time_warnings)
        
        return {
            'region_name': region_data.region_name,
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'school_count': len(region_data.schools),
            'valid_school_count': valid_schools,
            'valid_school_ratio': valid_ratio,
            'school_validations': school_validations,
            'summary': region_data.summary.to_dict() if hasattr(region_data.summary, 'to_dict') else None
        }
    
    def validate_multiple_regions(self, regions: List[RegionData]) -> Dict[str, Any]:
        """
        验证多个区域数据的一致性
        
        Args:
            regions: 区域数据列表
            
        Returns:
            整体验证结果
        """
        errors = []
        warnings = []
        region_validations = []
        
        # 验证每个区域
        valid_regions = 0
        total_schools = 0
        
        for region in regions:
            region_validation = self.validate_region_data(region)
            region_validations.append(region_validation)
            
            if region_validation['is_valid']:
                valid_regions += 1
            
            total_schools += len(region.schools)
        
        # 检查区域覆盖率
        known_regions_found = set()
        for region in regions:
            if region.region_name in self.KNOWN_REGIONS:
                known_regions_found.add(region.region_name)
        
        coverage = len(known_regions_found) / len(self.KNOWN_REGIONS)
        if coverage < 0.5:
            warnings.append(f"区域覆盖率偏低: {coverage:.2%}")
        
        # 检查数据时效性
        if regions:
            timestamps = [r.crawl_timestamp for r in regions]
            time_span = max(timestamps) - min(timestamps)
            if time_span > timedelta(hours=24):
                warnings.append(f"数据采集时间跨度过大: {time_span}")
        
        # 统计分析
        stats = self._calculate_statistics(regions)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'region_count': len(regions),
            'valid_region_count': valid_regions,
            'total_school_count': total_schools,
            'known_regions_coverage': coverage,
            'region_validations': region_validations,
            'statistics': stats
        }
    
    def _validate_basic_info(self, school: SchoolData) -> List[str]:
        """验证学校基础信息"""
        errors = []
        
        # 学校名称验证
        if not school.school_name or not school.school_name.strip():
            errors.append("学校名称为空")
        elif len(school.school_name) < self.REASONABLE_RANGES['min_school_name_length']:
            errors.append(f"学校名称过短: {school.school_name}")
        elif len(school.school_name) > self.REASONABLE_RANGES['max_school_name_length']:
            errors.append(f"学校名称过长: {school.school_name}")
        
        # 区域名称验证
        if not school.region or not school.region.strip():
            errors.append("区域名称为空")
        
        # URL验证
        if not school.source_url or not school.source_url.startswith('http'):
            errors.append("数据源URL无效")
        
        return errors
    
    def _validate_phases_data(self, school: SchoolData) -> tuple[List[str], List[str]]:
        """验证各阶段数据"""
        errors = []
        warnings = []
        
        phases = [
            ('Phase 1', school.phase_1),
            ('Phase 2A', school.phase_2a),
            ('Phase 2B', school.phase_2b),
            ('Phase 2C', school.phase_2c),
            ('Phase 2C(S)', school.phase_2cs)
        ]
        
        for phase_name, phase_data in phases:
            phase_errors, phase_warnings = self._validate_single_phase(phase_name, phase_data)
            errors.extend(phase_errors)
            warnings.extend(phase_warnings)
        
        return errors, warnings
    
    def _validate_single_phase(self, phase_name: str, phase_data: PhaseData) -> tuple[List[str], List[str]]:
        """验证单个阶段数据"""
        errors = []
        warnings = []
        
        # 基本数值验证
        if phase_data.vacancy < 0:
            errors.append(f"{phase_name}: 空缺数为负数 ({phase_data.vacancy})")
        
        if phase_data.applied < 0:
            errors.append(f"{phase_name}: 申请数为负数 ({phase_data.applied})")
        
        if phase_data.taken < 0:
            errors.append(f"{phase_name}: 录取数为负数 ({phase_data.taken})")
        
        # 逻辑关系验证
        if phase_data.taken > phase_data.vacancy and phase_data.vacancy > 0:
            errors.append(f"{phase_name}: 录取数超过空缺数 ({phase_data.taken} > {phase_data.vacancy})")
        
        if phase_data.taken > phase_data.applied and phase_data.applied > 0:
            errors.append(f"{phase_name}: 录取数超过申请数 ({phase_data.taken} > {phase_data.applied})")
        
        # 合理性检查
        if phase_data.vacancy > self.REASONABLE_RANGES['max_vacancy_per_phase']:
            warnings.append(f"{phase_name}: 空缺数异常大 ({phase_data.vacancy})")
        
        if phase_data.applied > self.REASONABLE_RANGES['max_applications_per_phase']:
            warnings.append(f"{phase_name}: 申请数异常大 ({phase_data.applied})")
        
        # 成功率检查
        if phase_data.applied > 0:
            success_rate = phase_data.taken / phase_data.applied
            if success_rate > 1.0:
                errors.append(f"{phase_name}: 成功率超过100% ({success_rate:.2%})")
        
        return errors, warnings
    
    def _validate_data_consistency(self, school: SchoolData) -> List[str]:
        """验证数据一致性"""
        errors = []
        
        # 检查是否所有阶段都没有数据
        phases = [school.phase_1, school.phase_2a, school.phase_2b, school.phase_2c, school.phase_2cs]
        total_vacancy = sum(p.vacancy for p in phases)
        total_applied = sum(p.applied for p in phases)
        total_taken = sum(p.taken for p in phases)
        
        if total_vacancy == 0 and total_applied == 0 and total_taken == 0:
            errors.append("所有阶段都没有数据")
        
        return errors
    
    def _validate_reasonableness(self, school: SchoolData) -> List[str]:
        """验证数据合理性"""
        warnings = []
        
        # 检查Phase 1的数据（通常是最重要的）
        if school.phase_1.vacancy == 0 and school.phase_1.applied == 0:
            warnings.append("Phase 1 没有数据，这可能不正常")
        
        # 检查成功率分布
        phases = [school.phase_1, school.phase_2a, school.phase_2b, school.phase_2c, school.phase_2cs]
        success_rates = []
        
        for phase in phases:
            if phase.applied > 0:
                success_rates.append(phase.taken / phase.applied)
        
        if success_rates:
            avg_success_rate = statistics.mean(success_rates)
            if avg_success_rate > 0.95:
                warnings.append(f"平均成功率异常高: {avg_success_rate:.2%}")
            elif avg_success_rate < 0.1:
                warnings.append(f"平均成功率异常低: {avg_success_rate:.2%}")
        
        return warnings
    
    def _validate_timestamp(self, timestamp: datetime) -> List[str]:
        """验证时间戳"""
        warnings = []
        
        now = datetime.now()
        time_diff = abs((now - timestamp).total_seconds())
        
        # 数据过于陈旧
        if time_diff > 7 * 24 * 3600:  # 7天
            warnings.append(f"数据过于陈旧: {timestamp}")
        
        # 数据来自未来
        if timestamp > now + timedelta(minutes=5):
            warnings.append(f"数据时间戳来自未来: {timestamp}")
        
        return warnings
    
    def _calculate_statistics(self, regions: List[RegionData]) -> Dict[str, Any]:
        """计算统计信息"""
        if not regions:
            return {}
        
        all_schools = []
        for region in regions:
            all_schools.extend(region.schools)
        
        if not all_schools:
            return {}
        
        # 统计各种指标
        total_vacancies = [s.total_vacancy for s in all_schools]
        total_applications = [s.total_applied for s in all_schools]
        success_rates = [s.overall_success_rate for s in all_schools if s.total_applied > 0]
        
        stats = {
            'total_schools': len(all_schools),
            'vacancy_stats': {
                'mean': statistics.mean(total_vacancies) if total_vacancies else 0,
                'median': statistics.median(total_vacancies) if total_vacancies else 0,
                'min': min(total_vacancies) if total_vacancies else 0,
                'max': max(total_vacancies) if total_vacancies else 0
            },
            'application_stats': {
                'mean': statistics.mean(total_applications) if total_applications else 0,
                'median': statistics.median(total_applications) if total_applications else 0,
                'min': min(total_applications) if total_applications else 0,
                'max': max(total_applications) if total_applications else 0
            },
            'success_rate_stats': {
                'mean': statistics.mean(success_rates) if success_rates else 0,
                'median': statistics.median(success_rates) if success_rates else 0,
                'min': min(success_rates) if success_rates else 0,
                'max': max(success_rates) if success_rates else 0
            }
        }
        
        return stats