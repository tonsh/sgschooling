"""
数据分析器
负责从原始数据生成统计分析和排名
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import logging

from .models.school_data import SchoolData, PhaseData
from .models.region_data import RegionData

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """数据分析器，从原始数据生成分析结果"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.raw_regions_dir = self.data_dir / "raw" / "regions"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def check_raw_data_exists(self) -> bool:
        """检查原始数据是否存在"""
        if not self.raw_regions_dir.exists():
            logger.warning(f"原始数据目录不存在: {self.raw_regions_dir}")
            return False

        json_files = list(self.raw_regions_dir.glob("*.json"))
        if not json_files:
            logger.warning(f"原始数据目录中没有JSON文件: {self.raw_regions_dir}")
            return False

        logger.info(f"找到 {len(json_files)} 个原始数据文件")
        return True

    def load_all_raw_data(self) -> List[SchoolData]:
        """
        从原始数据文件加载所有学校数据

        Returns:
            学校数据列表
        """
        all_schools = []

        if not self.check_raw_data_exists():
            return all_schools

        for json_file in self.raw_regions_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

                # 解析学校信息
                schools_data = raw_data.get("schools", [])
                for school_data in schools_data:
                    try:
                        school = SchoolData(
                            name=school_data.get("name", ""),
                            region=school_data.get("region", ""),
                            phase_1=PhaseData.from_dict(school_data.get("phase_1", {})),
                            phase_2a=PhaseData.from_dict(school_data.get("phase_2a", {})),
                            phase_2b=PhaseData.from_dict(school_data.get("phase_2b", {})),
                            phase_2c=PhaseData.from_dict(school_data.get("phase_2c", {})),
                            phase_2cs=PhaseData.from_dict(school_data.get("phase_2cs", {}))
                        )
                        all_schools.append(school)
                    except Exception as e:
                        logger.error("解析学校数据失败 %s: %s", school_data.get('name', 'Unknown'), e)

                logger.info("加载 %d 所学校", len(schools_data))

            except Exception as e:
                logger.error("加载原始数据文件失败 %s: %s", json_file, e)

        logger.info("总计加载: %d 所学校", len(all_schools))
        return all_schools

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        生成完整的分析报告

        Returns:
            包含所有统计信息和排名的报告
        """
        logger.info("开始生成分析报告...")

        # 加载原始数据
        schools = self.load_all_raw_data()

        if not schools:
            logger.error("无法加载原始数据，无法生成报告")
            return {}

        # 生成排名
        ranked_schools = SchoolData.rank_list(schools)
        ranked_regions = RegionData.rank_list(schools)
        
        # 转换为字典格式并添加排名
        school_rankings = []
        for i, school in enumerate(ranked_schools, 1):
            school_dict = {
                "rank": i,
                "school_name": school.name,
                "region": school.region,
                "remaining": school.remaining,
                "failed": school.failed,
                "vacancy": school.vacancy,
                "applied": school.applied,
                "taken": school.taken,
                "rate": school.rate,
                "characteristic_analysis": school.characteristic_analysis
            }
            school_rankings.append(school_dict)
        
        region_rankings = []
        for i, region in enumerate(ranked_regions, 1):
            region_dict = region.to_dict()
            region_dict["rank"] = i
            region_rankings.append(region_dict)

        # 计算总体统计
        total_schools = len(schools)
        total_vacancy = sum(school.vacancy for school in schools)
        total_applied = sum(school.applied for school in schools)
        total_taken = sum(school.taken for school in schools)
        total_remaining = sum(school.remaining for school in schools)
        total_failed = sum(school.failed for school in schools)

        # 生成报告
        report = {
            "generated_at": "2024-08-20",  # 可以改为动态时间
            "summary": {
                "total_regions": len(region_rankings),
                "total_schools": total_schools,
                "total_vacancy": total_vacancy,
                "total_applied": total_applied,
                "total_taken": total_taken,
                "total_remaining": total_remaining,
                "total_failed": total_failed,
                "overall_success_rate": total_taken / total_applied if total_applied > 0 else 0,
                "overall_vacancy_utilization": (
                    total_taken / total_vacancy if total_vacancy > 0 else 0
                )
            },
            "school_rankings": school_rankings,
            "region_rankings": region_rankings,
            "top_10_hottest_schools": school_rankings[:10],
            "top_10_most_competitive_regions": region_rankings[:10]
        }

        logger.info("分析报告生成完成")
        return report

    def save_analysis_results(self, report: Dict[str, Any]) -> str:
        """
        保存分析结果到文件

        Args:
            report: 分析报告

        Returns:
            保存的文件路径
        """
        filename = "analysis_report.json"
        file_path = self.processed_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info("分析结果已保存至: %s", file_path)
        return str(file_path)

    def run_full_analysis(self) -> str:
        """
        执行完整的数据分析流程

        Returns:
            报告文件路径
        """
        logger.info("开始执行完整的数据分析...")

        # 检查原始数据
        if not self.check_raw_data_exists():
            raise FileNotFoundError("找不到原始数据文件，请先运行数据采集")

        # 生成分析报告
        report = self.generate_summary_report()

        if not report:
            raise ValueError("无法生成分析报告")

        # 保存结果
        report_path = self.save_analysis_results(report)

        logger.info("数据分析完成，报告已保存至: %s", report_path)
        return report_path


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    analyzer = DataAnalyzer()
    try:
        report_path = analyzer.run_full_analysis()
        print(f"✅ 数据分析完成！报告保存在: {report_path}")
    except Exception as e:
        print(f"❌ 数据分析失败: {e}")


if __name__ == "__main__":
    main()
