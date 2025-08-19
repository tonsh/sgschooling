"""
学校数据模型
定义学校和报名阶段的数据结构
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PhaseData:
    """报名阶段数据"""
    vacancy: int = 0
    applied: int = 0
    taken: int = 0

    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "vacancy": self.vacancy,
            "applied": self.applied,
            "taken": self.taken
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'PhaseData':
        """从字典创建对象"""
        return cls(
            vacancy=data.get("vacancy", 0),
            applied=data.get("applied", 0),
            taken=data.get("taken", 0)
        )


@dataclass
class SchoolData:
    """
    学校数据模型

    结构说明：
    - name: 学校英文名称
    - cn_name: 学校中文名称
    - region: 所在区域
    - vacancy: 学校总学位数 = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.vacancy (自动计算)
    - Phase1/2A/2B/2C/2Cs: 各阶段数据(Vacancy, Applied, Taken)
    """
    name: str
    cn_name: str
    region: str
    phase_1: PhaseData
    phase_2a: PhaseData
    phase_2b: PhaseData
    phase_2c: PhaseData
    phase_2cs: PhaseData

    @property
    def vacancy(self) -> int:
        """学校总学位数 = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.vacancy"""
        return (
            self.phase_1.taken + self.phase_2a.taken +
            self.phase_2b.taken + self.phase_2c.taken +
            self.phase_2cs.vacancy
        )

    @property
    def total_applied(self) -> int:
        """总申请数"""
        return (self.phase_1.applied + self.phase_2a.applied +
                self.phase_2b.applied + self.phase_2c.applied +
                self.phase_2cs.applied)

    @property
    def total_taken(self) -> int:
        """总录取数"""
        return (self.phase_1.taken + self.phase_2a.taken +
                self.phase_2b.taken + self.phase_2c.taken +
                self.phase_2cs.taken)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "cn_name": self.cn_name,
            "region": self.region,
            "vacancy": self.vacancy,
            "phase_1": self.phase_1.to_dict(),
            "phase_2a": self.phase_2a.to_dict(),
            "phase_2b": self.phase_2b.to_dict(),
            "phase_2c": self.phase_2c.to_dict(),
            "phase_2cs": self.phase_2cs.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchoolData':
        """从字典创建对象"""
        return cls(
            name=data["name"],
            cn_name=data["cn_name"],
            region=data["region"],
            phase_1=PhaseData.from_dict(data.get("phase_1", {})),
            phase_2a=PhaseData.from_dict(data.get("phase_2a", {})),
            phase_2b=PhaseData.from_dict(data.get("phase_2b", {})),
            phase_2c=PhaseData.from_dict(data.get("phase_2c", {})),
            phase_2cs=PhaseData.from_dict(data.get("phase_2cs", {}))
        )
