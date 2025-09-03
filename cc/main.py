"""
CC 模块主程序
负责 Community Club 数据的采集
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from cc.collectors.onepa_collector import OnePACollector


async def collect_cc_data():
    """采集 Community Club 数据"""
    print("开始采集 Community Club 数据...")

    async with OnePACollector() as collector:
        # 采集所有 CC 数据
        cc_list = await collector.collect_all_cc_data()

        if cc_list:
            # 保存原始数据
            await collector.save_cc_data(cc_list)

            print(f"数据采集完成，共采集到 {len(cc_list)} 个 Community Club")
            return True
        else:
            print("数据采集失败")
            return False


async def main():
    """主程序"""
    print("=== 新加坡 Community Club 数据采集系统 ===")

    # 直接进行数据采集
    success = await collect_cc_data()

    if success:
        print("=== 数据采集完成 ===")
    else:
        print("=== 数据采集失败 ===")


if __name__ == "__main__":
    asyncio.run(main())

