"""
数据采集模块
负责从新加坡小学报名数据源获取数据，支持多种数据源
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .collectors.sgschooling_collector import SGSchoolingCollector
from .storage.data_storage import DataStorage
from .collectors.data_validator import DataValidator
from .models.crawl_result import CrawlResult


class SGPrimaryDataCollector:
    """新加坡小学数据采集器 - 升级版"""

    def __init__(self, data_dir: str = "data", use_sgschooling: bool = True):
        """
        初始化数据采集器
        
        Args:
            data_dir: 数据存储目录
            use_sgschooling: 是否使用SGSchooling数据源
        """
        self.data_dir = Path(data_dir)
        self.storage = DataStorage(data_dir)
        self.validator = DataValidator()
        self.use_sgschooling = use_sgschooling
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)

    async def collect_all_data(self, validate: bool = True) -> CrawlResult:
        """
        采集所有区域的学校数据
        
        Args:
            validate: 是否验证数据
            
        Returns:
            爬取结果对象
        """
        print("开始采集新加坡小学P1报名数据...")
        
        if self.use_sgschooling:
            return await self._collect_from_sgschooling(validate)
        else:
            # 保留原有的采集逻辑（占位符）
            return await self._collect_from_moe(validate)
    
    async def _collect_from_sgschooling(self, validate: bool) -> CrawlResult:
        """从SGSchooling网站采集数据"""
        async with SGSchoolingCollector(str(self.data_dir)) as collector:
            # 执行爬取
            result = await collector.crawl_all_regions()
            
            # 验证数据（如果需要）
            if validate and result.successful_regions:
                print("开始验证采集到的数据...")
                validation_results = await self._validate_collected_data(result.successful_regions)
                
                # 将验证结果添加到爬取结果中
                if hasattr(result, 'validation_results'):
                    result.validation_results = validation_results
            
            # 保存爬取结果
            self.storage.save_crawl_result(result)
            
            # 生成汇总报告
            if result.successful_regions:
                regions_data = []
                for region_name in result.successful_regions:
                    region_data = self.storage.load_region_data(region_name)
                    if region_data:
                        regions_data.append(region_data)
                
                if regions_data:
                    # 创建CSV导出
                    csv_path = self.storage.export_to_csv(regions_data)
                    print(f"数据已导出到CSV: {csv_path}")
                    
                    # 创建汇总报告
                    summary_path = self.storage.create_summary_report(regions_data)
                    print(f"汇总报告已生成: {summary_path}")
            
            return result
    
    async def _collect_from_moe(self, validate: bool) -> CrawlResult:
        """从MOE官网采集数据（占位符实现）"""
        print("MOE数据源采集功能待实现...")
        
        # 创建空的爬取结果
        result = CrawlResult.create_new(0)
        result.add_error("moe", "not_implemented", "MOE数据源采集功能待实现")
        result.finalize()
        
        return result
    
    async def _validate_collected_data(self, successful_regions: List[str]) -> Dict[str, Any]:
        """验证采集到的数据"""
        validation_results = {
            'total_regions': len(successful_regions),
            'region_validations': [],
            'overall_valid': True,
            'validation_timestamp': datetime.now().isoformat()
        }
        
        regions_data = []
        for region_name in successful_regions:
            region_data = self.storage.load_region_data(region_name)
            if region_data:
                regions_data.append(region_data)
                
                # 验证单个区域
                region_validation = self.validator.validate_region_data(region_data)
                validation_results['region_validations'].append(region_validation)
                
                if not region_validation['is_valid']:
                    validation_results['overall_valid'] = False
        
        # 验证整体一致性
        if regions_data:
            overall_validation = self.validator.validate_multiple_regions(regions_data)
            validation_results['overall_validation'] = overall_validation
            
            if not overall_validation['is_valid']:
                validation_results['overall_valid'] = False
        
        return validation_results
    
    def collect_school_data(self, year: int = 2025) -> List[Dict]:
        """
        同步方法，保持向后兼容性
        
        Args:
            year: 报名年份，默认2025
            
        Returns:
            学校数据列表
        """
        print(f"开始采集{year}年小学报名数据...")
        
        # 运行异步采集
        result = asyncio.run(self.collect_all_data())
        
        # 转换为旧格式
        schools_data = []
        if result.successful_regions:
            for region_name in result.successful_regions:
                region_data = self.storage.load_region_data(region_name)
                if region_data:
                    for school in region_data.schools:
                        schools_data.append(school.to_dict())
        
        return schools_data
    
    def save_raw_data(self, data: List[Dict], filename: str) -> None:
        """
        保存原始数据到文件（保持向后兼容性）
        
        Args:
            data: 数据列表
            filename: 保存的文件名
        """
        file_path = self.data_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {file_path}")
    
    async def update_data(self, region_names: Optional[List[str]] = None) -> CrawlResult:
        """
        增量更新数据
        
        Args:
            region_names: 要更新的区域列表，如果为None则更新所有区域
            
        Returns:
            更新结果
        """
        print("开始增量更新数据...")
        
        if self.use_sgschooling:
            async with SGSchoolingCollector(str(self.data_dir)) as collector:
                if region_names is None:
                    # 发现所有区域
                    all_regions = await collector.discover_regions()
                    region_names = all_regions
                
                # 创建增量爬取结果
                result = CrawlResult.create_new(len(region_names))
                
                # 逐个更新区域
                for region_name in region_names:
                    try:
                        region_data = await collector.scrape_region_data(region_name)
                        if region_data:
                            file_path = self.storage.save_region_data(region_data)
                            result.mark_region_success(region_name, file_path)
                        else:
                            result.mark_region_failure(region_name)
                            result.add_error(region_name, "scraping_failed", "区域数据采集失败")
                    
                    except Exception as e:
                        result.mark_region_failure(region_name)
                        result.add_error(region_name, "exception", str(e))
                
                result.finalize()
                self.storage.save_crawl_result(result)
                return result
        
        else:
            # MOE数据源的增量更新
            result = CrawlResult.create_new(0)
            result.add_error("moe", "not_implemented", "MOE数据源增量更新功能待实现")
            result.finalize()
            return result
    
    def get_latest_data_summary(self) -> Optional[Dict[str, Any]]:
        """获取最新数据摘要"""
        # 加载所有区域数据
        regions_data = self.storage.load_all_regions_data()
        
        if not regions_data:
            return None
        
        # 计算汇总信息
        total_schools = sum(len(region.schools) for region in regions_data)
        total_regions = len(regions_data)
        
        # 获取最新更新时间
        latest_update = max(
            max(school.last_updated for school in region.schools) 
            for region in regions_data 
            if region.schools
        )
        
        return {
            'total_regions': total_regions,
            'total_schools': total_schools,
            'latest_update': latest_update.isoformat(),
            'data_sources': ['sgschooling.com'] if self.use_sgschooling else ['moe.gov.sg'],
            'regions': [region.region_name for region in regions_data]
        }


# 保持向后兼容的异步函数
async def async_collect_data(data_dir: str = "data") -> CrawlResult:
    """异步采集数据的便捷函数"""
    collector = SGPrimaryDataCollector(data_dir)
    return await collector.collect_all_data()


if __name__ == "__main__":
    # 示例用法
    async def main():
        collector = SGPrimaryDataCollector()
        result = await collector.collect_all_data()
        
        print(f"采集完成!")
        print(f"成功区域: {len(result.successful_regions)}")
        print(f"失败区域: {len(result.failed_regions)}")
        print(f"总学校数: {result.stats.total_schools}")
        
        # 获取数据摘要
        summary = collector.get_latest_data_summary()
        if summary:
            print(f"数据摘要: {summary}")
    
    asyncio.run(main())