"""
爬取结果模型
定义数据采集过程和结果的数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum


class CrawlStatus(Enum):
    """爬取状态枚举"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    IN_PROGRESS = "in_progress"


@dataclass
class CrawlError:
    """爬取错误信息"""
    region: str
    error_type: str
    error_message: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "region": self.region,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class CrawlStats:
    """爬取统计信息"""
    total_regions: int = 0
    successful_regions: int = 0
    failed_regions: int = 0
    total_schools: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_regions == 0:
            return 0.0
        return self.successful_regions / self.total_regions
    
    @property
    def duration_seconds(self) -> float:
        """爬取耗时（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_regions": self.total_regions,
            "successful_regions": self.successful_regions,
            "failed_regions": self.failed_regions,
            "total_schools": self.total_schools,
            "success_rate": self.success_rate,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class CrawlResult:
    """爬取结果模型"""
    status: CrawlStatus
    stats: CrawlStats
    successful_regions: List[str]
    failed_regions: List[str]
    errors: List[CrawlError]
    data_files: Dict[str, str]  # region_name -> file_path
    timestamp: datetime
    
    def add_error(self, region: str, error_type: str, error_message: str) -> None:
        """添加错误信息"""
        error = CrawlError(
            region=region,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now()
        )
        self.errors.append(error)
    
    def mark_region_success(self, region: str, file_path: str) -> None:
        """标记区域爬取成功"""
        if region not in self.successful_regions:
            self.successful_regions.append(region)
        self.data_files[region] = file_path
        self.stats.successful_regions = len(self.successful_regions)
    
    def mark_region_failure(self, region: str) -> None:
        """标记区域爬取失败"""
        if region not in self.failed_regions:
            self.failed_regions.append(region)
        self.stats.failed_regions = len(self.failed_regions)
    
    def finalize(self) -> None:
        """完成爬取，更新最终状态"""
        self.stats.end_time = datetime.now()
        
        if self.stats.failed_regions == 0:
            self.status = CrawlStatus.SUCCESS
        elif self.stats.successful_regions > 0:
            self.status = CrawlStatus.PARTIAL_SUCCESS
        else:
            self.status = CrawlStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "stats": self.stats.to_dict(),
            "successful_regions": self.successful_regions,
            "failed_regions": self.failed_regions,
            "errors": [error.to_dict() for error in self.errors],
            "data_files": self.data_files,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def create_new(cls, total_regions: int) -> 'CrawlResult':
        """创建新的爬取结果"""
        stats = CrawlStats(
            total_regions=total_regions,
            start_time=datetime.now()
        )
        
        return cls(
            status=CrawlStatus.IN_PROGRESS,
            stats=stats,
            successful_regions=[],
            failed_regions=[],
            errors=[],
            data_files={},
            timestamp=datetime.now()
        )