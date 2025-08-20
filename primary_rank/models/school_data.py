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
    - region: 所在区域
    - vacancy: 学校总学位数 = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.vacancy (自动计算)
    - Phase1/2A/2B/2C/2Cs: 各阶段数据(Vacancy, Applied, Taken)
    """
    name: str
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
    def applied(self) -> int:
        """总申请数"""
        return (self.phase_1.applied + self.phase_2a.applied +
                self.phase_2b.applied + self.phase_2c.applied +
                self.phase_2cs.applied)

    @property
    def taken(self) -> int:
        """总录取数"""
        return (self.phase_1.taken + self.phase_2a.taken +
                self.phase_2b.taken + self.phase_2c.taken +
                self.phase_2cs.taken)

    @property
    def rate(self) -> float:
        """
        热度计算公式（阶段权重法）：
        热度 = Σ(各阶段竞争度 × 阶段权重)
        
        权重分配：
        - Phase1: 40% (优先入学权，竞争最激烈)
        - Phase2A: 25% (校友/理事会关系，中等竞争)
        - Phase2B: 15% (社区关系，一般竞争)
        - Phase2C: 15% (普通申请，竞争较高)
        - Phase2CS: 5% (补充录取，竞争最低)
        
        各阶段竞争度 = (申请数/学位数) × 调节因子
        """
        if self.vacancy == 0:
            return 0.0
        
        # 阶段权重
        phase_weights = {
            'phase_1': 0.40,    # Phase1: 优先入学权
            'phase_2a': 0.25,   # Phase2A: 校友/理事会关系
            'phase_2b': 0.15,   # Phase2B: 社区关系
            'phase_2c': 0.15,   # Phase2C: 普通申请
            'phase_2cs': 0.05   # Phase2CS: 补充录取
        }
        
        total_hotness = 0.0
        
        # 计算各阶段的竞争度
        phases = [
            ('phase_1', self.phase_1),
            ('phase_2a', self.phase_2a),
            ('phase_2b', self.phase_2b),
            ('phase_2c', self.phase_2c),
            ('phase_2cs', self.phase_2cs)
        ]
        
        for phase_name, phase_data in phases:
            if phase_data.vacancy == 0:
                continue
                
            # 申请竞争比例
            competition_ratio = phase_data.applied / phase_data.vacancy if phase_data.vacancy > 0 else 0.0
            
            # 调节因子（根据阶段特点调整）
            adjustment_factors = {
                'phase_1': 1.5,    # Phase1最重要，放大系数
                'phase_2a': 1.2,   # Phase2A有一定关系门槛
                'phase_2b': 1.0,   # Phase2B相对平衡
                'phase_2c': 1.3,   # Phase2C普通竞争但人数多
                'phase_2cs': 0.8   # Phase2CS补充录取，降低影响
            }
            
            adjustment_factor = adjustment_factors[phase_name]
            
            # 阶段竞争度（简化版）
            phase_competition = competition_ratio * adjustment_factor
            
            # 加权累加
            total_hotness += phase_competition * phase_weights[phase_name]
        
        return total_hotness

    @property
    def remaining(self) -> int:
        """剩余名额 = 总学位数 - 总录取数"""
        return self.vacancy - self.taken

    @property
    def failed(self) -> int:
        """未报名成功人数 = max(总申请数 - 总学位数, 0)"""
        return max(self.applied - self.vacancy, 0)

    @property
    def characteristic_analysis(self) -> str:
        """学校特点分析"""
        analysis = []
        
        # 热度分析（基于新的阶段权重法）
        if self.rate >= 0.8:
            analysis.append("超高热度")
        elif self.rate >= 0.6:
            analysis.append("高热度")
        elif self.rate >= 0.4:
            analysis.append("中等热度")
        elif self.rate >= 0.2:
            analysis.append("低热度")
        else:
            analysis.append("冷门学校")
            
        # 竞争状况分析
        if self.failed > 0:
            if self.failed / self.applied >= 0.5:
                analysis.append("竞争极其激烈")
            elif self.failed / self.applied >= 0.3:
                analysis.append("竞争激烈")
            else:
                analysis.append("有竞争")
        else:
            analysis.append("无竞争压力")
            
        # 录取情况分析
        if self.remaining > 0:
            if self.remaining / self.vacancy >= 0.3:
                analysis.append("学位充裕")
            elif self.remaining / self.vacancy >= 0.1:
                analysis.append("有剩余学位")
            else:
                analysis.append("少量剩余")
        else:
            analysis.append("学位已满")
            
        # 学校规模
        if self.vacancy >= 300:
            analysis.append("大型学校")
        elif self.vacancy >= 200:
            analysis.append("中型学校")
        else:
            analysis.append("小型学校")
            
        return "、".join(analysis)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "region": self.region,
            "vacancy": self.vacancy,
            "applied": self.applied,
            "taken": self.taken,
            "rate": self.rate,
            "remaining": self.remaining,
            "failed": self.failed,
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
            region=data["region"],
            phase_1=PhaseData.from_dict(data.get("phase_1", {})),
            phase_2a=PhaseData.from_dict(data.get("phase_2a", {})),
            phase_2b=PhaseData.from_dict(data.get("phase_2b", {})),
            phase_2c=PhaseData.from_dict(data.get("phase_2c", {})),
            phase_2cs=PhaseData.from_dict(data.get("phase_2cs", {}))
        )
