"""
数据采集模块
负责从新加坡教育部网站获取小学报名数据
"""

import json
from typing import Dict, List

import requests


class SGPrimaryDataCollector:
    """新加坡小学数据采集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def collect_school_data(self, year: int = 2025) -> List[Dict]:
        """
        采集指定年份的小学报名数据

        Args:
            year: 报名年份，默认2025

        Returns:
            学校数据列表
        """
        # TODO: 实现具体的数据采集逻辑
        print(f"开始采集{year}年小学报名数据...")
        return []

    def save_raw_data(self, data: List[Dict], filename: str) -> None:
        """
        保存原始数据到文件

        Args:
            data: 数据列表
            filename: 保存的文件名
        """
        with open(f"data/{filename}", 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 data/{filename}")


if __name__ == "__main__":
    collector = SGPrimaryDataCollector()
    school_data = collector.collect_school_data(2025)
    collector.save_raw_data(school_data, "primary_schools_2025.json")
