"""
数据清理工具
用于清理和验证采集的原始数据
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..models.school_data import SchoolData, PhaseData
from ..models.region_data import RegionData


class DataCleaner:
    """数据清理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw" / "regions"
        self.cleaned_dir = self.data_dir / "cleaned" / "regions"
        
        # 确保清理后的数据目录存在
        self.cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_data_quality(self) -> Dict[str, Any]:
        """分析数据质量"""
        print("📊 正在分析数据质量...")
        
        analysis_result = {
            "total_files": 0,
            "total_schools": 0,
            "invalid_schools": 0,
            "issues": [],
            "by_region": {}
        }
        
        for json_file in self.raw_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                region_name = data["region"]["name"]
                schools = data["schools"]
                
                analysis_result["total_files"] += 1
                analysis_result["total_schools"] += len(schools)
                
                # 分析该区域的数据
                region_analysis = self._analyze_region_schools(schools)
                analysis_result["by_region"][region_name] = region_analysis
                analysis_result["invalid_schools"] += region_analysis["invalid_count"]
                
                if region_analysis["issues"]:
                    analysis_result["issues"].extend([
                        f"{region_name}: {issue}" for issue in region_analysis["issues"]
                    ])
                
            except Exception as e:
                analysis_result["issues"].append(f"文件 {json_file} 读取失败: {e}")
        
        return analysis_result
    
    def _analyze_region_schools(self, schools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析单个区域的学校数据"""
        result = {
            "total_count": len(schools),
            "valid_schools": [],
            "invalid_schools": [],
            "invalid_count": 0,
            "issues": []
        }
        
        for school in schools:
            school_name = school.get("name", "")
            
            # 识别无效的学校条目
            if self._is_invalid_school(school_name):
                result["invalid_schools"].append(school_name)
                result["invalid_count"] += 1
            else:
                result["valid_schools"].append(school_name)
                
                # 检查数据完整性
                issues = self._check_school_data_integrity(school)
                if issues:
                    result["issues"].extend([f"{school_name}: {issue}" for issue in issues])
        
        return result
    
    def _is_invalid_school(self, school_name: str) -> bool:
        """判断是否为无效的学校条目"""
        invalid_patterns = [
            "↳",  # 网站显示格式标记
            "vacancy",  # 学位信息行
            "applied",  # 申请信息行
            "taken",    # 录取信息行
        ]
        
        name_lower = school_name.lower().strip()
        
        # 检查是否包含无效模式
        for pattern in invalid_patterns:
            if pattern in name_lower:
                return True
        
        # 检查是否为空或过短
        if not name_lower or len(name_lower) < 2:
            return True
        
        return False
    
    def _check_school_data_integrity(self, school_data: Dict[str, Any]) -> List[str]:
        """检查学校数据完整性"""
        issues = []
        
        # 检查必需字段
        required_fields = ["name", "region"]
        for field in required_fields:
            if not school_data.get(field):
                issues.append(f"缺少必需字段: {field}")
        
        # 检查阶段数据
        phase_fields = ["phase_1", "phase_2a", "phase_2b", "phase_2c", "phase_2cs"]
        for phase_field in phase_fields:
            phase_data = school_data.get(phase_field, {})
            if not isinstance(phase_data, dict):
                issues.append(f"阶段数据格式错误: {phase_field}")
                continue
            
            # 检查阶段数据的数值合理性
            vacancy = phase_data.get("vacancy", 0)
            applied = phase_data.get("applied", 0)
            taken = phase_data.get("taken", 0)
            
            if applied < taken:
                issues.append(f"{phase_field}: 申请数({applied}) < 录取数({taken})")
        
        return issues
    
    def clean_region_data(self, region_file: Path) -> Tuple[RegionData, List[SchoolData]]:
        """清理单个区域的数据"""
        with open(region_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        # 过滤出有效的学校数据
        valid_schools = []
        for school_data in raw_data["schools"]:
            if not self._is_invalid_school(school_data.get("name", "")):
                # 转换为SchoolData对象
                try:
                    school = SchoolData.from_dict(school_data)
                    valid_schools.append(school)
                except Exception as e:
                    print(f"⚠️  跳过无效学校数据: {school_data.get('name', 'Unknown')} - {e}")
        
        # 重新计算区域统计数据
        region_data = RegionData.from_schools(
            name=raw_data["region"]["name"],
            cn_name=raw_data["region"].get("cn_name", ""),
            schools=valid_schools
        )
        
        return region_data, valid_schools
    
    def clean_all_data(self) -> Dict[str, Any]:
        """清理所有区域的数据"""
        print("🧹 正在清理所有区域数据...")
        
        cleaned_stats = {
            "regions_processed": 0,
            "schools_before": 0,
            "schools_after": 0,
            "schools_removed": 0,
            "regions_data": {}
        }
        
        for json_file in self.raw_dir.glob("*.json"):
            try:
                region_data, clean_schools = self.clean_region_data(json_file)
                
                # 统计信息
                with open(json_file, 'r', encoding='utf-8') as f:
                    original_data = json.load(f)
                original_school_count = len(original_data["schools"])
                
                cleaned_stats["regions_processed"] += 1
                cleaned_stats["schools_before"] += original_school_count
                cleaned_stats["schools_after"] += len(clean_schools)
                cleaned_stats["schools_removed"] += original_school_count - len(clean_schools)
                
                cleaned_stats["regions_data"][region_data.name] = {
                    "original_schools": original_school_count,
                    "cleaned_schools": len(clean_schools),
                    "removed_schools": original_school_count - len(clean_schools)
                }
                
                # 保存清理后的数据
                cleaned_file = self.cleaned_dir / json_file.name
                self._save_cleaned_data(region_data, clean_schools, cleaned_file, original_data["metadata"])
                
                print(f"✅ {region_data.name}: {original_school_count} → {len(clean_schools)} 学校")
                
            except Exception as e:
                print(f"❌ 清理文件 {json_file} 失败: {e}")
        
        return cleaned_stats
    
    def _save_cleaned_data(self, region_data: RegionData, schools: List[SchoolData], 
                          file_path: Path, original_metadata: Dict[str, Any]) -> None:
        """保存清理后的数据"""
        cleaned_data = {
            "region": region_data.to_dict(),
            "schools": [school.to_dict() for school in schools],
            "metadata": {
                **original_metadata,
                "cleaned": True,
                "cleaning_version": "1.0"
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
    
    def generate_cleaning_report(self) -> None:
        """生成数据清理报告"""
        print("\n" + "="*60)
        print("📋 数据清理报告")
        print("="*60)
        
        # 分析原始数据质量
        quality_analysis = self.analyze_data_quality()
        
        print(f"📁 处理文件数: {quality_analysis['total_files']}")
        print(f"🏫 原始学校条目数: {quality_analysis['total_schools']}")
        print(f"❌ 无效条目数: {quality_analysis['invalid_schools']}")
        print(f"✅ 有效条目数: {quality_analysis['total_schools'] - quality_analysis['invalid_schools']}")
        
        if quality_analysis['issues']:
            print(f"\n⚠️  发现的问题 ({len(quality_analysis['issues'])}):")
            for issue in quality_analysis['issues'][:10]:  # 只显示前10个问题
                print(f"   • {issue}")
            if len(quality_analysis['issues']) > 10:
                print(f"   ... 还有 {len(quality_analysis['issues']) - 10} 个问题")
        
        # 执行数据清理
        cleaning_stats = self.clean_all_data()
        
        print(f"\n🧹 数据清理完成:")
        print(f"   • 处理区域: {cleaning_stats['regions_processed']}")
        print(f"   • 清理前: {cleaning_stats['schools_before']} 条目")
        print(f"   • 清理后: {cleaning_stats['schools_after']} 学校")
        print(f"   • 移除条目: {cleaning_stats['schools_removed']}")
        removal_rate = cleaning_stats['schools_removed'] / cleaning_stats['schools_before'] * 100
        print(f"   • 清理效率: {removal_rate:.1f}% 无效条目被移除")
        
        print(f"\n📁 清理后的数据已保存至: {self.cleaned_dir}")
        print("="*60)


def main():
    """主函数"""
    cleaner = DataCleaner()
    cleaner.generate_cleaning_report()


if __name__ == "__main__":
    main()