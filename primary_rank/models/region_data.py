"""
区域数据模型
定义区域级别的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from functools import cached_property
from .school_data import SchoolData


@dataclass
class RegionData:
    """
    区域数据模型

    结构说明：
    - name: 区域英文名称
    - schools: 该区域的学校列表
    其他属性均从学校列表计算得出
    """
    name: str
    schools: List[SchoolData] = field(default_factory=list)

    @cached_property
    def school_num(self) -> int:
        """该区域学校数量"""
        return len(self.schools)

    @cached_property
    def vacancy(self) -> int:
        """该区域所有学校的总学位数量"""
        return sum(school.vacancy for school in self.schools)

    @cached_property
    def applied(self) -> int:
        """该区域所有学校的总报名数量"""
        return sum(school.applied for school in self.schools)

    @cached_property
    def taken(self) -> int:
        """该区域所有学校的总录取数量"""
        return sum(school.taken for school in self.schools)

    @cached_property
    def success_rate(self) -> float:
        """整体成功率"""
        if self.applied == 0:
            return 0.0
        return self.taken / self.applied

    @cached_property
    def competition_ratio(self) -> float:
        """竞争比例 (申请数/学位数)"""
        if self.vacancy == 0:
            return 0.0
        return self.applied / self.vacancy

    @cached_property
    def remaining(self) -> int:
        """剩余名额 = 总学位数 - 总录取数"""
        return self.vacancy - self.taken

    @cached_property
    def failed(self) -> int:
        """未报名成功人数 = max(总申请数 - 总学位数, 0)"""
        return max(self.applied - self.vacancy, 0)

    @cached_property
    def rate(self) -> float:
        """
        区域热度（基于学校规模的加权平均）
        区域热度 = Σ(学校热度 × 学校学位数) / 总学位数
        """
        if not self.schools or self.vacancy == 0:
            return 0.0

        weighted_hotness = 0.0
        for school in self.schools:
            if school.vacancy > 0:
                weighted_hotness += school.rate * school.vacancy

        return weighted_hotness / self.vacancy

    @property
    def characteristic_analysis(self) -> str:
        """区域特点分析"""
        analysis = []

        # 竞争激烈程度分析
        if self.competition_ratio >= 1.25:
            analysis.append("竞争极其激烈")
        elif self.competition_ratio >= 1.1:
            analysis.append("竞争激烈")
        elif self.competition_ratio >= 1.0:
            analysis.append("供需平衡")
        else:
            analysis.append("学位充足")

        # 区域规模分析
        if self.school_num >= 10:
            analysis.append("大型区域")
        elif self.school_num >= 5:
            analysis.append("中型区域")
        else:
            analysis.append("小型区域")

        # 学位供应分析
        if self.vacancy >= 2000:
            analysis.append("学位供应充足")
        elif self.vacancy >= 1000:
            analysis.append("学位供应适中")
        else:
            analysis.append("学位供应有限")

        # 成功率分析
        if self.success_rate >= 0.9:
            analysis.append("录取率很高")
        elif self.success_rate >= 0.8:
            analysis.append("录取率较高")
        elif self.success_rate >= 0.7:
            analysis.append("录取率中等")
        else:
            analysis.append("录取率较低")

        return "、".join(analysis)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "region": self.name,  # 保持与原有接口兼容
            "school_num": self.school_num,
            "vacancy": self.vacancy,
            "applied": self.applied,
            "taken": self.taken,
            "success_rate": self.success_rate,
            "competition_ratio": self.competition_ratio,
            "remaining": self.remaining,
            "failed": self.failed,
            "rate": self.rate,
            "characteristic_analysis": self.characteristic_analysis
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionData':
        """从字典创建对象（需要单独设置 schools）"""
        return cls(
            name=data["name"],
            schools=[]  # 需要单独设置学校列表
        )

    @classmethod
    def from_schools(cls, name: str, schools: List[SchoolData]) -> 'RegionData':
        """从学校列表创建区域数据"""
        return cls(
            name=name,
            schools=schools
        )

    @classmethod
    def rank_list(cls, schools: List[SchoolData]) -> List['RegionData']:
        """
        生成区域热度排名列表
        
        Args:
            schools: 所有学校数据列表
            
        Returns:
            按热度排序的区域对象列表
        """
        # 按区域分组
        region_schools = {}
        for school in schools:
            if school.region not in region_schools:
                region_schools[school.region] = []
            region_schools[school.region].append(school)
        
        # 创建区域对象
        regions = []
        for region_name, region_school_list in region_schools.items():
            region = cls.from_schools(region_name, region_school_list)
            regions.append(region)
        
        # 按热度排序（降序）
        return sorted(regions, key=lambda x: x.rate, reverse=True)
