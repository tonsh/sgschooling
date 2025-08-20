"""
主分析器入口
提供完整的数据分析和报告生成功能
"""

import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

from .data_collector import SGPrimaryDataCollector
from .data_analyzer import DataAnalyzer
from .report_generator import ReportGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PrimaryRankAnalyzer:
    """新加坡小学报名数据分析器 - 主控制器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.collector = SGPrimaryDataCollector(data_dir)
        self.analyzer = DataAnalyzer(data_dir)
        self.reporter = ReportGenerator(data_dir)
    
    async def run_full_analysis(self, force_recrawl: bool = False) -> Dict[str, Any]:
        """
        运行完整的数据分析流程
        
        Args:
            force_recrawl: 是否强制重新抓取数据
            
        Returns:
            分析结果和报告路径
        """
        logger.info("🚀 开始运行完整的数据分析流程...")
        
        results = {}
        
        try:
            # 步骤1: 数据收集（优先使用已存在数据）
            logger.info("📊 步骤1: 数据收集...")
            crawl_result = await self.collector.collect_all_data(
                validate=True, 
                force_recrawl=force_recrawl
            )
            results['crawl_result'] = {
                'successful_regions': len(crawl_result.successful_regions),
                'failed_regions': len(crawl_result.failed_regions),
                'total_regions': crawl_result.stats.total_regions
            }
            
            # 步骤2: 数据分析
            logger.info("📈 步骤2: 数据分析...")
            if self.analyzer.check_raw_data_exists():
                analysis_report = self.analyzer.generate_summary_report()
                results['analysis_summary'] = analysis_report.get('summary', {})
                results['school_count'] = len(analysis_report.get('school_rankings', []))
                results['region_count'] = len(analysis_report.get('region_rankings', []))
            else:
                raise FileNotFoundError("原始数据不存在，无法进行分析")
            
            # 步骤3: 报告生成
            logger.info("📄 步骤3: 报告生成...")
            report_paths = self.reporter.run_full_report_generation()
            results['reports'] = report_paths
            
            logger.info("✅ 完整分析流程完成！")
            return results
            
        except Exception as e:
            logger.error(f"❌ 分析流程失败: {e}")
            raise
    
    def print_analysis_summary(self, results: Dict[str, Any]) -> None:
        """打印分析结果摘要"""
        print("\n" + "="*60)
        print("🎯 新加坡小学报名数据分析完成！")
        print("="*60)
        
        # 数据收集摘要
        crawl_info = results.get('crawl_result', {})
        print(f"📊 数据收集: {crawl_info.get('successful_regions', 0)}/{crawl_info.get('total_regions', 0)} 个区域成功")
        
        # 分析摘要
        analysis_info = results.get('analysis_summary', {})
        print(f"🏫 分析结果: {results.get('school_count', 0)} 所学校, {results.get('region_count', 0)} 个区域")
        print(f"📈 总学位数: {analysis_info.get('total_vacancy', 0):,}")
        print(f"📝 总申请数: {analysis_info.get('total_applied', 0):,}")
        print(f"✅ 总录取数: {analysis_info.get('total_taken', 0):,}")
        print(f"💯 整体成功率: {analysis_info.get('overall_success_rate', 0):.2%}")
        
        # 报告文件
        reports = results.get('reports', {})
        print(f"\n📄 报告文件:")
        if 'markdown' in reports:
            print(f"   📋 详细报告: {reports['markdown']}")
        if 'json' in reports:
            print(f"   📊 数据文件: {reports['json']}")
        
        print("="*60)
    
    async def quick_analysis(self) -> None:
        """快速分析（使用已存在数据）"""
        logger.info("⚡ 开始快速分析...")
        
        if not self.analyzer.check_raw_data_exists():
            print("❌ 未找到原始数据，请先运行数据收集")
            return
        
        try:
            # 直接生成报告
            report_paths = self.reporter.run_full_report_generation()
            
            print("✅ 快速分析完成！")
            print(f"📋 报告文件: {report_paths.get('markdown', '')}")
            print(f"📊 数据文件: {report_paths.get('json', '')}")
            
        except Exception as e:
            print(f"❌ 快速分析失败: {e}")


async def main():
    """主函数"""
    print("🏫 新加坡小学报名数据分析系统")
    print("PrimaryRank - Singapore Primary School Analysis")
    print("-" * 50)
    
    analyzer = PrimaryRankAnalyzer()
    
    try:
        # 运行完整分析（优先使用已存在数据）
        results = await analyzer.run_full_analysis(force_recrawl=False)
        
        # 打印摘要
        analyzer.print_analysis_summary(results)
        
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        logger.exception("程序异常")


if __name__ == "__main__":
    asyncio.run(main())