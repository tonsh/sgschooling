"""
区域数据模型
定义区域级别的数据结构
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .school_data import SchoolData


@dataclass
class RegionData:
    """
    区域数据模型

    结构说明：
    - name: 区域英文名称
    - school_num: 该区域学校数量
    - vacancy: 该区域所有学校的总学位数量
    - applied: 该区域所有学校的总报名数量
    - taken: 该区域所有学校的总录取数量
    """
    name: str
    school_num: int
    vacancy: int
    applied: int
    taken: int

    @property
    def success_rate(self) -> float:
        """整体成功率"""
        if self.applied == 0:
            return 0.0
        return self.taken / self.applied

    @property
    def competition_ratio(self) -> float:
        """竞争比例 (申请数/学位数)"""
        if self.vacancy == 0:
            return 0.0
        return self.applied / self.vacancy

    @property
    def remaining(self) -> int:
        """剩余名额 = 总学位数 - 总录取数"""
        return self.vacancy - self.taken

    @property
    def failed(self) -> int:
        """未报名成功人数 = max(总申请数 - 总学位数, 0)"""
        return max(self.applied - self.vacancy, 0)

    @property
    def rate(self) -> float:
        """申请率 = 总申请数 / 总录取数"""
        if self.taken == 0:
            return 0.0
        return self.applied / self.taken

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
            "name": self.name,
            "school_num": self.school_num,
            "vacancy": self.vacancy,
            "applied": self.applied,
            "taken": self.taken,
            "success_rate": self.success_rate,
            "competition_ratio": self.competition_ratio,
            "remaining": self.remaining,
            "failed": self.failed,
            "rate": self.rate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionData':
        """从字典创建对象"""
        return cls(
            name=data["name"],
            school_num=data["school_num"],
            vacancy=data["vacancy"],
            applied=data["applied"],
            taken=data["taken"]
        )

    @classmethod
    def from_schools(cls, name: str, schools: List[SchoolData]) -> 'RegionData':
        """从学校列表创建区域数据"""
        return cls(
            name=name,
            school_num=len(schools),
            vacancy=sum(school.vacancy for school in schools),
            applied=sum(school.applied for school in schools),
            taken=sum(school.taken for school in schools)
    )
