"""
学校数据模型
定义学校和报名阶段的数据结构
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PhaseData:
    """报名阶段数据"""
    vacancy: int = 0
    applied: int = 0
    taken: int = 0
    
    @property
    def available(self) -> int:
        """剩余空缺"""
        return max(0, self.vacancy - self.taken)
    
    @property 
    def success_rate(self) -> float:
        """成功率"""
        if self.applied == 0:
            return 0.0
        return self.taken / self.applied


@dataclass
class SchoolData:
    """学校数据模型"""
    school_name: str
    region: str
    phase_1: PhaseData
    phase_2a: PhaseData
    phase_2b: PhaseData
    phase_2c: PhaseData
    phase_2cs: PhaseData
    last_updated: datetime
    source_url: str
    
    @property
    def total_vacancy(self) -> int:
        """总空缺数"""
        return (self.phase_1.vacancy + self.phase_2a.vacancy + 
                self.phase_2b.vacancy + self.phase_2c.vacancy + 
                self.phase_2cs.vacancy)
    
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
    
    @property
    def overall_success_rate(self) -> float:
        """整体成功率"""
        if self.total_applied == 0:
            return 0.0
        return self.total_taken / self.total_applied
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "school_name": self.school_name,
            "region": self.region,
            "phases": {
                "phase_1": {
                    "vacancy": self.phase_1.vacancy,
                    "applied": self.phase_1.applied,
                    "taken": self.phase_1.taken
                },
                "phase_2a": {
                    "vacancy": self.phase_2a.vacancy,
                    "applied": self.phase_2a.applied,
                    "taken": self.phase_2a.taken
                },
                "phase_2b": {
                    "vacancy": self.phase_2b.vacancy,
                    "applied": self.phase_2b.applied,
                    "taken": self.phase_2b.taken
                },
                "phase_2c": {
                    "vacancy": self.phase_2c.vacancy,
                    "applied": self.phase_2c.applied,
                    "taken": self.phase_2c.taken
                },
                "phase_2cs": {
                    "vacancy": self.phase_2cs.vacancy,
                    "applied": self.phase_2cs.applied,
                    "taken": self.phase_2cs.taken
                }
            },
            "total_vacancy": self.total_vacancy,
            "total_applied": self.total_applied,
            "total_taken": self.total_taken,
            "overall_success_rate": self.overall_success_rate,
            "last_updated": self.last_updated.isoformat(),
            "source_url": self.source_url
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SchoolData':
        """从字典创建对象"""
        phases = data.get("phases", {})
        
        return cls(
            school_name=data["school_name"],
            region=data["region"],
            phase_1=PhaseData(**phases.get("phase_1", {})),
            phase_2a=PhaseData(**phases.get("phase_2a", {})),
            phase_2b=PhaseData(**phases.get("phase_2b", {})),
            phase_2c=PhaseData(**phases.get("phase_2c", {})),
            phase_2cs=PhaseData(**phases.get("phase_2cs", {})),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            source_url=data["source_url"]
        )