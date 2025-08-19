"""
PrimaryRank 主程序
新加坡小学排名分析系统主入口
"""

from data_collector import SGPrimaryDataCollector
from data_processor import SGPrimaryDataProcessor
from ranking_calculator import SGPrimaryRankingCalculator


def main():
    """主程序入口"""
    print("=" * 50)
    print("PrimaryRank - 新加坡小学排名分析系统")
    print("=" * 50)

    # 第一步：数据采集
    print("\n第一步：数据采集")
    collector = SGPrimaryDataCollector()
    raw_data = collector.collect_school_data(2025)
    collector.save_raw_data(raw_data, "primary_schools_2025.json")

    # 第二步：数据处理
    print("\n第二步：数据处理")
    processor = SGPrimaryDataProcessor()
    raw_data = processor.load_raw_data("primary_schools_2025.json")
    clean_data = processor.clean_data(raw_data)
    processed_data = processor.process_data(clean_data)
    processor.save_processed_data(processed_data, "processed_data_2025.json")

    # 第三步：排名计算
    print("\n第三步：排名计算")
    calculator = SGPrimaryRankingCalculator()
    data = calculator.load_processed_data("processed_data_2025.json")
    school_ranking = calculator.calculate_school_ranking(data)
    region_ranking = calculator.calculate_region_ranking(data)
    calculator.save_rankings(school_ranking, region_ranking)

    print("\n分析完成！")
    print("结果文件：")
    print("- data/school_ranking_2025.json (学校排名)")
    print("- data/region_ranking_2025.json (区域排名)")


if __name__ == "__main__":
    main()
