"""
CC 数据模型测试
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from cc.models.cc_data import CCData, RegionCCData


class TestCCData(unittest.TestCase):
    """测试 CCData 模型"""

    def setUp(self):
        """测试设置"""
        self.cc_data = CCData(
            name="Ang Mo Kio CC",
            address="123 Ang Mo Kio Ave 6, #01-01, Singapore 560123",
            postcode="560123",
            region="Ang Mo Kio"
        )

    def test_cc_data_creation(self):
        """测试 CC 数据创建"""
        self.assertEqual(self.cc_data.name, "Ang Mo Kio CC")
        self.assertEqual(self.cc_data.address, "123 Ang Mo Kio Ave 6, #01-01, Singapore 560123")
        self.assertEqual(self.cc_data.postcode, "560123")
        self.assertEqual(self.cc_data.region, "Ang Mo Kio")

    def test_to_dict(self):
        """测试转换为字典"""
        cc_dict = self.cc_data.to_dict()
        
        expected_dict = {
            "name": "Ang Mo Kio CC",
            "address": "123 Ang Mo Kio Ave 6, #01-01, Singapore 560123",
            "postcode": "560123",
            "region": "Ang Mo Kio"
        }
        
        self.assertEqual(cc_dict, expected_dict)

    def test_from_dict(self):
        """测试从字典创建对象"""
        cc_dict = {
            "name": "Bedok CC",
            "address": "456 Bedok North Street 3, Singapore 460456",
            "postcode": "460456",
            "region": "Bedok"
        }
        
        cc_data = CCData.from_dict(cc_dict)
        
        self.assertEqual(cc_data.name, "Bedok CC")
        self.assertEqual(cc_data.address, "456 Bedok North Street 3, Singapore 460456")
        self.assertEqual(cc_data.postcode, "460456")
        self.assertEqual(cc_data.region, "Bedok")

    def test_from_dict_with_missing_fields(self):
        """测试从不完整字典创建对象"""
        cc_dict = {
            "name": "Test CC",
            "address": "Test Address"
            # 缺少 postcode 和 region
        }
        
        cc_data = CCData.from_dict(cc_dict)
        
        self.assertEqual(cc_data.name, "Test CC")
        self.assertEqual(cc_data.address, "Test Address")
        self.assertEqual(cc_data.postcode, "")
        self.assertEqual(cc_data.region, "")


class TestRegionCCData(unittest.TestCase):
    """测试 RegionCCData 模型"""

    def setUp(self):
        """测试设置"""
        self.cc_list = [
            CCData("Ang Mo Kio CC", "123 AMK Ave 6", "560123", "Ang Mo Kio"),
            CCData("Bishan CC", "456 Bishan St 11", "570456", "Bishan"),
            CCData("Clementi CC", "789 Clementi Ave 2", "120789", "Clementi"),
        ]

    def test_from_ccs(self):
        """测试从 CC 列表创建区域数据"""
        region_data = RegionCCData.from_ccs("Test Region", self.cc_list)
        
        self.assertEqual(region_data.name, "Test Region")
        self.assertEqual(region_data.cc_count, 3)
        self.assertEqual(len(region_data.cc_list), 3)
        self.assertEqual(region_data.density, 3.0)

    def test_to_dict(self):
        """测试转换为字典"""
        region_data = RegionCCData.from_ccs("Test Region", self.cc_list)
        region_dict = region_data.to_dict()
        
        self.assertEqual(region_dict["name"], "Test Region")
        self.assertEqual(region_dict["cc_count"], 3)
        self.assertEqual(region_dict["density"], 3.0)
        self.assertEqual(len(region_dict["cc_list"]), 3)

    def test_from_dict(self):
        """测试从字典创建区域数据"""
        region_dict = {
            "name": "Test Region",
            "cc_count": 2,
            "cc_list": [
                {
                    "name": "CC1",
                    "address": "Address 1",
                    "postcode": "123456",
                    "region": "Test Region"
                },
                {
                    "name": "CC2",
                    "address": "Address 2",
                    "postcode": "654321",
                    "region": "Test Region"
                }
            ]
        }
        
        region_data = RegionCCData.from_dict(region_dict)
        
        self.assertEqual(region_data.name, "Test Region")
        self.assertEqual(region_data.cc_count, 2)
        self.assertEqual(len(region_data.cc_list), 2)

    def test_rank_list(self):
        """测试区域排名功能"""
        region1 = RegionCCData("Region A", 3, self.cc_list[:3])
        region2 = RegionCCData("Region B", 1, self.cc_list[:1])
        region3 = RegionCCData("Region C", 2, self.cc_list[:2])
        
        regions = [region2, region3, region1]  # 故意打乱顺序
        
        ranked_regions = RegionCCData.rank_list(regions)
        
        # 应该按 CC 数量降序排列
        self.assertEqual(ranked_regions[0].name, "Region A")  # 3个CC
        self.assertEqual(ranked_regions[1].name, "Region C")  # 2个CC
        self.assertEqual(ranked_regions[2].name, "Region B")  # 1个CC

    def test_empty_cc_list(self):
        """测试空 CC 列表"""
        region_data = RegionCCData.from_ccs("Empty Region", [])
        
        self.assertEqual(region_data.name, "Empty Region")
        self.assertEqual(region_data.cc_count, 0)
        self.assertEqual(len(region_data.cc_list), 0)
        self.assertEqual(region_data.density, 0.0)


if __name__ == "__main__":
    unittest.main()