"""
数据模型定义
包含学校、区域等数据结构
"""

from .school_data import SchoolData, PhaseData
from .region_data import RegionData
from .crawl_result import CrawlResult

__all__ = [
    'SchoolData',
    'PhaseData', 
    'RegionData',
    'CrawlResult'
]