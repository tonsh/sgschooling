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
    - cn_name: 区域中文名称  
    - school_num: 该区域学校数量
    - vacancy: 该区域所有学校的总学位数量
    - applied: 该区域所有学校的总报名数量
    - taken: 该区域所有学校的总录取数量
    """
    name: str
    cn_name: str
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "cn_name": self.cn_name,
            "school_num": self.school_num,
            "vacancy": self.vacancy,
            "applied": self.applied,
            "taken": self.taken
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegionData':
        """从字典创建对象"""
        return cls(
            name=data["name"],
            cn_name=data["cn_name"],
            school_num=data["school_num"],
            vacancy=data["vacancy"],
            applied=data["applied"],
            taken=data["taken"]
        )
    
    @classmethod
    def from_schools(cls, name: str, cn_name: str, schools: List[SchoolData]) -> 'RegionData':
        """从学校列表创建区域数据"""
        return cls(
            name=name,
            cn_name=cn_name,
            school_num=len(schools),
            vacancy=sum(school.vacancy for school in schools),
            applied=sum(school.total_applied for school in schools),
            taken=sum(school.total_taken for school in schools)
        )