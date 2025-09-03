"""
Community Club 数据模型
定义 CC 的数据结构
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class CCData:
    """
    Community Club 数据模型

    结构说明：
    - name: CC 名称
    - address: 完整地址
    - postcode: 邮政编码
    - url: CC 详情页面链接
    """
    name: str
    address: str
    postcode: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "address": self.address,
            "postcode": self.postcode,
            "url": self.url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CCData':
        """从字典创建对象"""
        return cls(
            name=data.get("name", ""),
            address=data.get("address", ""),
            postcode=data.get("postcode", ""),
            url=data.get("url", "")
        )

