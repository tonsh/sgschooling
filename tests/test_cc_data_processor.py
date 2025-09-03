"""
CC 数据处理器测试
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from cc.data_processor import CCDataProcessor
from cc.models.cc_data import CCData, RegionCCData


class TestCCDataProcessor(unittest.TestCase):
    """测试 CC 数据处理器"""

    def setUp(self):
        """测试设置"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
        self.processor = CCDataProcessor(self.temp_dir)
        
        # 创建测试数据
        self.test_cc_list = [
            CCData("Ang Mo Kio CC", "AMK Address", "560123", "Ang Mo Kio"),
            CCData("Bishan CC", "Bishan Address", "570456", "Bishan"),
            CCData("Clementi CC", "Clementi Address", "120789", "Clementi"),
            CCData("Bedok CC", "Bedok Address", "460456", "Bedok"),
            CCData("Jurong East CC", "JE Address", "609123", "Jurong East"),
        ]
        
        # 创建测试数据文件
        self._create_test_data_file()

    def _create_test_data_file(self):
        """创建测试数据文件"""
        # 确保目录存在
        raw_dir = Path(self.temp_dir) / "cc" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试数据
        test_data = {
            "community_clubs": [cc.to_dict() for cc in self.test_cc_list],
            "metadata": {
                "total_count": len(self.test_cc_list),
                "crawl_time": "2025-01-01T00:00:00",
                "source_url": "test://example.com",
                "data_version": "1.0"
            }
        }
        
        # 保存测试数据文件
        latest_file = raw_dir / "latest_community_clubs.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

    def test_load_latest_cc_data(self):
        """测试加载最新 CC 数据"""
        cc_list = self.processor.load_latest_cc_data()
        
        self.assertEqual(len(cc_list), 5)
        self.assertEqual(cc_list[0].name, "Ang Mo Kio CC")
        self.assertEqual(cc_list[1].name, "Bishan CC")

    def test_analyze_cc_by_region(self):
        """测试按区域分析 CC 数据"""
        region_data_list = self.processor.analyze_cc_by_region(self.test_cc_list)
        
        self.assertEqual(len(region_data_list), 5)  # 5个不同区域
        
        # 验证每个区域都有1个CC
        for region_data in region_data_list:
            self.assertEqual(region_data.cc_count, 1)

    def test_analyze_cc_by_region_with_duplicates(self):
        """测试带重复区域的数据分析"""
        test_data = self.test_cc_list + [
            CCData("Ang Mo Kio CC 2", "AMK Address 2", "560789", "Ang Mo Kio"),
            CCData("Bishan CC 2", "Bishan Address 2", "570789", "Bishan"),
        ]
        
        region_data_list = self.processor.analyze_cc_by_region(test_data)
        
        # 应该有5个区域
        self.assertEqual(len(region_data_list), 5)
        
        # 验证 AMK 和 Bishan 区域有2个CC
        amk_region = next(r for r in region_data_list if r.name == "Ang Mo Kio")
        bishan_region = next(r for r in region_data_list if r.name == "Bishan")
        
        self.assertEqual(amk_region.cc_count, 2)
        self.assertEqual(bishan_region.cc_count, 2)

    def test_generate_cc_ranking(self):
        """测试生成 CC 排名"""
        # 创建不同CC数量的区域数据
        regions = [
            RegionCCData("Region A", 3, self.test_cc_list[:3]),
            RegionCCData("Region B", 1, self.test_cc_list[:1]),
            RegionCCData("Region C", 2, self.test_cc_list[:2]),
        ]
        
        ranked_regions = self.processor.generate_cc_ranking(regions)
        
        # 验证排序正确（降序）
        self.assertEqual(ranked_regions[0].cc_count, 3)
        self.assertEqual(ranked_regions[1].cc_count, 2)
        self.assertEqual(ranked_regions[2].cc_count, 1)

    def test_generate_summary_report(self):
        """测试生成总结报告"""
        region_data_list = self.processor.analyze_cc_by_region(self.test_cc_list)
        summary = self.processor.generate_summary_report(self.test_cc_list, region_data_list)
        
        # 验证概览信息
        overview = summary["overview"]
        self.assertEqual(overview["total_community_clubs"], 5)
        self.assertEqual(overview["total_regions"], 5)
        self.assertEqual(overview["average_cc_per_region"], 1.0)
        
        # 验证区域排名
        region_ranking = summary["region_ranking"]
        self.assertEqual(len(region_ranking), 5)
        
        # 验证第一个区域的排名信息
        first_region = region_ranking[0]
        self.assertEqual(first_region["rank"], 1)
        self.assertEqual(first_region["cc_count"], 1)
        
        # 验证亮点信息
        highlights = summary["highlights"]
        self.assertIn("most_cc_region", highlights)
        self.assertIn("least_cc_region", highlights)
        
        # 验证 CC 列表
        cc_list = summary["cc_list"]
        self.assertEqual(len(cc_list), 5)

    def test_generate_markdown_report(self):
        """测试生成 Markdown 报告"""
        region_data_list = self.processor.analyze_cc_by_region(self.test_cc_list)
        summary = self.processor.generate_summary_report(self.test_cc_list, region_data_list)
        
        markdown_content = self.processor.generate_markdown_report(summary)
        
        # 验证 Markdown 内容包含关键信息
        self.assertIn("# 新加坡 Community Club 分析报告", markdown_content)
        self.assertIn("Community Club 总数", markdown_content)
        self.assertIn("覆盖区域数", markdown_content)
        self.assertIn("区域排名", markdown_content)
        self.assertIn("| 排名 | 区域 | CC 数量 | 密度 |", markdown_content)

    def test_empty_data_handling(self):
        """测试空数据处理"""
        # 清空测试数据文件
        raw_dir = Path(self.temp_dir) / "cc" / "raw"
        latest_file = raw_dir / "latest_community_clubs.json"
        
        # 创建空数据文件
        empty_data = {
            "community_clubs": [],
            "metadata": {
                "total_count": 0,
                "crawl_time": "2025-01-01T00:00:00",
                "data_version": "1.0"
            }
        }
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, ensure_ascii=False, indent=2)
        
        # 测试加载空数据
        cc_list = self.processor.load_latest_cc_data()
        self.assertEqual(len(cc_list), 0)
        
        # 测试处理空数据
        region_data_list = self.processor.analyze_cc_by_region(cc_list)
        self.assertEqual(len(region_data_list), 0)
        
        # 测试生成空数据报告
        summary = self.processor.generate_summary_report(cc_list, region_data_list)
        overview = summary["overview"]
        
        self.assertEqual(overview["total_community_clubs"], 0)
        self.assertEqual(overview["total_regions"], 0)
        self.assertEqual(overview["average_cc_per_region"], 0)


if __name__ == "__main__":
    unittest.main()