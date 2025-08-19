"""
区域数据模型
定义区域级别的数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any
from .school_data import SchoolData


@dataclass
class RegionSummary:
    """区域汇总数据"""
    total_schools: int = 0
    total_vacancies: int = 0
    total_applications: int = 0
    total_taken: int = 0
    
    @property
    def average_success_rate(self) -> float:
        """平均成功率"""
        if self.total_applications == 0:
            return 0.0
        return self.total_taken / self.total_applications
    
    @property
    def vacancy_utilization(self) -> float:
        """空缺利用率"""
        if self.total_vacancies == 0:
            return 0.0
        return self.total_taken / self.total_vacancies


@dataclass
class RegionData:
    """区域数据模型"""
    region_name: str
    schools: List[SchoolData]
    crawl_timestamp: datetime
    source_url: str
    
    @property
    def summary(self) -> RegionSummary:
        """生成区域汇总数据"""
        if not self.schools:
            return RegionSummary()
        
        total_schools = len(self.schools)
        total_vacancies = sum(school.total_vacancy for school in self.schools)
        total_applications = sum(school.total_applied for school in self.schools)
        total_taken = sum(school.total_taken for school in self.schools)
        
        return RegionSummary(
            total_schools=total_schools,
            total_vacancies=total_vacancies,
            total_applications=total_applications,
            total_taken=total_taken
        )
    
    def get_top_schools_by_popularity(self, limit: int = 10) -> List[SchoolData]:
        """按热度排序获取热门学校"""
        return sorted(
            self.schools,
            key=lambda s: s.total_applied,
            reverse=True
        )[:limit]
    
    def get_schools_with_availability(self) -> List[SchoolData]:
        """获取还有空缺的学校"""
        return [
            school for school in self.schools
            if any([
                school.phase_1.available > 0,
                school.phase_2a.available > 0,
                school.phase_2b.available > 0,
                school.phase_2c.available > 0,
                school.phase_2cs.available > 0
            ])
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "region_name": self.region_name,
            "schools": [school.to_dict() for school in self.schools],
            "summary": {
                "total_schools": self.summary.total_schools,
                "total_vacancies": self.summary.total_vacancies,
                "total_applications": self.summary.total_applications,
                "total_taken": self.summary.total_taken,
                "average_success_rate": self.summary.average_success_rate,
                "vacancy_utilization": self.summary.vacancy_utilization
            },
            "crawl_timestamp": self.crawl_timestamp.isoformat(),
            "source_url": self.source_url
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionData':
        """从字典创建对象"""
        schools = [
            SchoolData.from_dict(school_data) 
            for school_data in data.get("schools", [])
        ]
        
        return cls(
            region_name=data["region_name"],
            schools=schools,
            crawl_timestamp=datetime.fromisoformat(data["crawl_timestamp"]),
            source_url=data["source_url"]
        )