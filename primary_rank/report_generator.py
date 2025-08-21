"""
报告生成器
生成Markdown格式的分析报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

from .data_analyzer import DataAnalyzer

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Markdown报告生成器"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.analyzer = DataAnalyzer(data_dir)
        self.reports_dir = Path("docs")
        self.reports_dir.mkdir(exist_ok=True)

    def generate_summary_report(self) -> str:
        """
        生成完整的Summary报告

        Returns:
            生成的报告文件路径
        """
        logger.info("开始生成Summary报告...")

        # 获取分析数据
        report_data = self.analyzer.generate_summary_report()

        if not report_data:
            raise ValueError("无法获取分析数据")

        # 生成Markdown内容
        markdown_content = self._generate_markdown_content(report_data)

        # 保存报告
        report_path = self.reports_dir / "SUMMARY_ANALYSIS.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        logger.info(f"Summary报告已生成: {report_path}")
        return str(report_path)

    def _generate_markdown_content(self, data: Dict[str, Any]) -> str:
        """生成Markdown内容"""
        summary = data.get("summary", {})
        school_rankings = data.get("school_rankings", [])
        region_rankings = data.get("region_rankings", [])

        # 构建Markdown内容
        content = f"""# 新加坡小学报名数据分析报告

## 📊 数据概览

**报告生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

### 总体统计

| 指标 | 数值 |
|------|------|
| 总区域数 | {summary.get('total_regions', 0)} |
| 总学校数 | {summary.get('total_schools', 0)} |
| 总学位数 | {summary.get('total_vacancy', 0):,} |
| 总申请数 | {summary.get('total_applied', 0):,} |
| 总录取数 | {summary.get('total_taken', 0):,} |
| 总剩余名额 | {summary.get('total_remaining', 0):,} |
| 总未录取数 | {summary.get('total_failed', 0):,} |
| 整体成功率 | {summary.get('overall_success_rate', 0):.2%} |
| 学位利用率 | {summary.get('overall_vacancy_utilization', 0):.2%} |

## 🏫 学校热度排名 (全部179所学校)

以下是按热度排序的所有学校，热度计算公式为：
**热度 = Σ(各阶段竞争度 × 阶段权重)**
**各阶段竞争度 = (申请数/学位数) × 调节因子**

**阶段权重分配：**
- Phase1 (优先入学): 40%
- Phase2A (校友/理事会): 25%
- Phase2B (社区关系): 15%
- Phase2C (普通申请): 15%
- Phase2CS (补充录取): 5%

| 排名 | 学校名称 | 区域 | 学位数 | 报名数 | 剩余名额 | 特点分析 |
|------|----------|------|--------|--------|----------|----------|
"""

        # 添加学校排名表格 - 显示所有学校
        for i, school in enumerate(school_rankings, 1):
            content += f"| {i} | {school['school_name']} | {school['region']} | {school['vacancy']} | {school['applied']} | {school['remaining']} | {school['characteristic_analysis']} |\n"

        content += f"""

## 🗺️ 区域排名 (全部27个区域)

以下是按超额率排序的所有区域，超额率 = 申请数 / 学位数

| 排名 | 区域 | 学校数 | 学位数 | 报名数 | 剩余名额 | 特点分析 |
|------|------|--------|--------|--------|----------|----------|
"""

        # 添加区域排名表格 - 显示所有区域
        for region in region_rankings:
            content += f"| {region['rank']} | {region['name']} | {region['school_num']} | {region['vacancy']} | {region['applied']} | {region['remaining']} | {region['characteristic_analysis']} |\n"

        content += """

## 📈 关键洞察

### 🔥 最热门学校 (TOP 10)

"""

        # 添加TOP 10最热门学校
        for i, school in enumerate(school_rankings[:10], 1):
            content += f"{i}. **{school['school_name']}** ({school['region']}) - 热度: {school['rate']:.3f}\n"
            content += f"   - 学位数: {school['vacancy']}, 录取数: {school['taken']}, 剩余: {school['remaining']}, 未录取: {school['failed']}\n\n"

        content += """### 🏆 竞争最激烈区域 (TOP 5)

"""

        # 添加TOP 5最竞争激烈区域
        for i, region in enumerate(region_rankings[:5], 1):
            content += f"{i}. **{region['region']}** - 竞争比率: {region['competition_ratio']:.3f}\n"
            content += f"   - 学校数: {region['school_num']}, 学位数: {region['vacancy']}, 录取数: {region['taken']}\n"
            content += f"   - 剩余名额: {region['remaining']}, 未录取数: {region['failed']}\n\n"

        content += f"""

## 📝 数据说明

### 指标定义

- **热度**: 阶段权重综合竞争强度，考虑各报名阶段的竞争激烈程度和重要性，数值越高表示学校越热门难进
- **剩余名额**: 学位数 - 录取数
- **未录取数**: max(申请数 - 学位数, 0)
- **竞争比率**: 申请数 / 学位数，反映区域竞争激烈程度
- **成功率**: 录取数 / 申请数
- **学位利用率**: 录取数 / 学位数

### 数据来源

- 数据来源: 新加坡教育部 (MOE) 官方网站
- 数据时间: 2025年小学一年级报名数据
- 总区域数: {summary.get('total_regions', 0)}
- 总学校数: {summary.get('total_schools', 0)}

### 免责声明

本报告基于公开数据生成，仅供参考。实际报名时请以官方最新数据为准。

---

*报告由 PrimaryRank 数据分析系统自动生成*
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return content

    def generate_json_summary(self) -> str:
        """
        生成JSON格式的摘要数据

        Returns:
            JSON文件路径
        """
        logger.info("生成JSON摘要数据...")

        report_data = self.analyzer.generate_summary_report()

        if not report_data:
            raise ValueError("无法获取分析数据")

        # 保存JSON数据
        json_path = self.data_dir / "processed" / "summary_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        logger.info(f"JSON摘要已保存: {json_path}")
        return str(json_path)

    def run_full_report_generation(self) -> Dict[str, str]:
        """
        运行完整的报告生成流程

        Returns:
            生成的文件路径字典
        """
        logger.info("开始生成完整分析报告...")

        results = {}

        try:
            # 生成Markdown报告
            markdown_path = self.generate_summary_report()
            results['markdown'] = markdown_path

            # 生成JSON摘要
            json_path = self.generate_json_summary()
            results['json'] = json_path

            logger.info("报告生成完成")
            return results

        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            raise


def main():
    """主函数"""
    logging.basicConfig(level=logging.INFO)

    generator = ReportGenerator()
    try:
        results = generator.run_full_report_generation()
        print("✅ 报告生成完成！")
        print(f"📄 Markdown报告: {results['markdown']}")
        print(f"📊 JSON数据: {results['json']}")
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")


if __name__ == "__main__":
    main()