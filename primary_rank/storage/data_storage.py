"""
数据存储管理器
负责数据的保存、加载和管理
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil

from ..models.school_data import SchoolData
from ..models.region_data import RegionData
from ..models.crawl_result import CrawlResult


class DataStorage:
    """数据存储管理器"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self._setup_directories()
    
    def _setup_directories(self) -> None:
        """设置目录结构"""
        directories = [
            "raw/regions",
            "raw/backup",
            "processed",
            "exports",
            "logs",
            "cache"
        ]
        
        for directory in directories:
            (self.base_dir / directory).mkdir(parents=True, exist_ok=True)
    
    def save_region_data(self, region_data: RegionData, backup: bool = True) -> str:
        """
        保存区域数据
        
        Args:
            region_data: 区域数据对象
            backup: 是否创建备份
            
        Returns:
            保存的文件路径
        """
        filename = f"{region_data.region_name}.json"
        file_path = self.base_dir / "raw" / "regions" / filename
        
        # 如果文件已存在且需要备份，先备份
        if backup and file_path.exists():
            self._backup_file(file_path)
        
        # 保存数据
        data = region_data.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def load_region_data(self, region_name: str) -> Optional[RegionData]:
        """
        加载区域数据
        
        Args:
            region_name: 区域名称
            
        Returns:
            区域数据对象，如果不存在则返回None
        """
        filename = f"{region_name}.json"
        file_path = self.base_dir / "raw" / "regions" / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return RegionData.from_dict(data)
        except Exception as e:
            print(f"加载区域数据失败 {region_name}: {e}")
            return None
    
    def save_all_regions_data(self, regions: List[RegionData]) -> Dict[str, str]:
        """
        批量保存区域数据
        
        Args:
            regions: 区域数据列表
            
        Returns:
            保存结果字典 {region_name: file_path}
        """
        results = {}
        
        for region_data in regions:
            try:
                file_path = self.save_region_data(region_data)
                results[region_data.region_name] = file_path
            except Exception as e:
                print(f"保存区域数据失败 {region_data.region_name}: {e}")
                results[region_data.region_name] = f"ERROR: {e}"
        
        return results
    
    def load_all_regions_data(self) -> List[RegionData]:
        """
        加载所有区域数据
        
        Returns:
            区域数据列表
        """
        regions = []
        regions_dir = self.base_dir / "raw" / "regions"
        
        for file_path in regions_dir.glob("*.json"):
            region_name = file_path.stem
            region_data = self.load_region_data(region_name)
            if region_data:
                regions.append(region_data)
        
        return regions
    
    def save_crawl_result(self, result: CrawlResult) -> str:
        """
        保存爬取结果
        
        Args:
            result: 爬取结果对象
            
        Returns:
            保存的文件路径
        """
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"crawl_result_{timestamp}.json"
        file_path = self.base_dir / "logs" / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 同时保存为最新结果
        latest_path = self.base_dir / "logs" / "latest_crawl_result.json"
        shutil.copy2(file_path, latest_path)
        
        return str(file_path)
    
    def get_latest_crawl_result(self) -> Optional[CrawlResult]:
        """
        获取最新的爬取结果
        
        Returns:
            最新爬取结果对象
        """
        latest_path = self.base_dir / "logs" / "latest_crawl_result.json"
        
        if not latest_path.exists():
            return None
        
        try:
            with open(latest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 简单重构，因为CrawlResult没有from_dict方法
            # 这里只是基本的数据验证
            return data
        except Exception as e:
            print(f"加载最新爬取结果失败: {e}")
            return None
    
    def export_to_csv(self, regions: List[RegionData], filename: str = None) -> str:
        """
        导出数据到CSV文件
        
        Args:
            regions: 区域数据列表
            filename: 输出文件名，如果为None则自动生成
            
        Returns:
            导出文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"school_data_{timestamp}.csv"
        
        file_path = self.base_dir / "exports" / filename
        
        # 准备CSV数据
        headers = [
            'Region', 'School Name', 
            'Phase1_Vacancy', 'Phase1_Applied', 'Phase1_Taken',
            'Phase2A_Vacancy', 'Phase2A_Applied', 'Phase2A_Taken',
            'Phase2B_Vacancy', 'Phase2B_Applied', 'Phase2B_Taken',
            'Phase2C_Vacancy', 'Phase2C_Applied', 'Phase2C_Taken',
            'Phase2CS_Vacancy', 'Phase2CS_Applied', 'Phase2CS_Taken',
            'Total_Vacancy', 'Total_Applied', 'Total_Taken',
            'Success_Rate', 'Last_Updated', 'Source_URL'
        ]
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for region in regions:
                for school in region.schools:
                    row = [
                        school.region,
                        school.school_name,
                        school.phase_1.vacancy, school.phase_1.applied, school.phase_1.taken,
                        school.phase_2a.vacancy, school.phase_2a.applied, school.phase_2a.taken,
                        school.phase_2b.vacancy, school.phase_2b.applied, school.phase_2b.taken,
                        school.phase_2c.vacancy, school.phase_2c.applied, school.phase_2c.taken,
                        school.phase_2cs.vacancy, school.phase_2cs.applied, school.phase_2cs.taken,
                        school.total_vacancy,
                        school.total_applied,
                        school.total_taken,
                        f"{school.overall_success_rate:.2%}",
                        school.last_updated.isoformat(),
                        school.source_url
                    ]
                    writer.writerow(row)
        
        return str(file_path)
    
    def create_summary_report(self, regions: List[RegionData]) -> str:
        """
        创建汇总报告
        
        Args:
            regions: 区域数据列表
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}.json"
        file_path = self.base_dir / "processed" / filename
        
        # 计算汇总统计
        total_schools = sum(len(region.schools) for region in regions)
        total_vacancies = sum(school.total_vacancy for region in regions for school in region.schools)
        total_applications = sum(school.total_applied for region in regions for school in region.schools)
        total_taken = sum(school.total_taken for region in regions for school in region.schools)
        
        # 按区域统计
        region_stats = []
        for region in regions:
            region_summary = region.summary
            region_stats.append({
                'region_name': region.region_name,
                'school_count': len(region.schools),
                'total_vacancies': region_summary.total_vacancies,
                'total_applications': region_summary.total_applications,
                'total_taken': region_summary.total_taken,
                'success_rate': region_summary.average_success_rate,
                'vacancy_utilization': region_summary.vacancy_utilization
            })
        
        # 创建报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_regions': len(regions),
                'total_schools': total_schools,
                'total_vacancies': total_vacancies,
                'total_applications': total_applications,
                'total_taken': total_taken,
                'overall_success_rate': total_taken / total_applications if total_applications > 0 else 0,
                'overall_vacancy_utilization': total_taken / total_vacancies if total_vacancies > 0 else 0
            },
            'region_statistics': region_stats,
            'top_popular_schools': self._get_top_schools_by_applications(regions, 10),
            'top_competitive_schools': self._get_most_competitive_schools(regions, 10)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def _backup_file(self, file_path: Path) -> None:
        """备份文件"""
        if not file_path.exists():
            return
        
        backup_dir = self.base_dir / "raw" / "backup"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
    
    def _get_top_schools_by_applications(self, regions: List[RegionData], limit: int) -> List[Dict]:
        """获取申请人数最多的学校"""
        all_schools = []
        for region in regions:
            for school in region.schools:
                all_schools.append({
                    'school_name': school.school_name,
                    'region': school.region,
                    'total_applications': school.total_applied,
                    'total_vacancies': school.total_vacancy,
                    'success_rate': school.overall_success_rate
                })
        
        # 按申请人数排序
        sorted_schools = sorted(all_schools, key=lambda x: x['total_applications'], reverse=True)
        return sorted_schools[:limit]
    
    def _get_most_competitive_schools(self, regions: List[RegionData], limit: int) -> List[Dict]:
        """获取竞争最激烈的学校（申请人数/空缺数比例最高）"""
        competitive_schools = []
        
        for region in regions:
            for school in region.schools:
                if school.total_vacancy > 0:
                    competition_ratio = school.total_applied / school.total_vacancy
                    competitive_schools.append({
                        'school_name': school.school_name,
                        'region': school.region,
                        'competition_ratio': competition_ratio,
                        'total_applications': school.total_applied,
                        'total_vacancies': school.total_vacancy,
                        'success_rate': school.overall_success_rate
                    })
        
        # 按竞争比例排序
        sorted_schools = sorted(competitive_schools, key=lambda x: x['competition_ratio'], reverse=True)
        return sorted_schools[:limit]
    
    def cleanup_old_files(self, days: int = 30) -> None:
        """清理旧文件"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        # 清理旧的备份文件
        backup_dir = self.base_dir / "raw" / "backup"
        self._cleanup_directory(backup_dir, cutoff_date)
        
        # 清理旧的日志文件
        logs_dir = self.base_dir / "logs"
        self._cleanup_directory(logs_dir, cutoff_date, exclude=["latest_crawl_result.json"])
    
    def _cleanup_directory(self, directory: Path, cutoff_timestamp: float, exclude: List[str] = None) -> None:
        """清理指定目录的旧文件"""
        if not directory.exists():
            return
        
        exclude = exclude or []
        
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name not in exclude:
                if file_path.stat().st_mtime < cutoff_timestamp:
                    try:
                        file_path.unlink()
                        print(f"删除旧文件: {file_path}")
                    except Exception as e:
                        print(f"删除文件失败 {file_path}: {e}")