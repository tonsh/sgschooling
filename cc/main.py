"""
OnePA 数据采集模块主程序
负责 Community Club (CC) 和 Residents' Committee (RC) 数据的采集
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from cc.collectors.onepa_collector import OnePACollector


async def collect_data(url: str):
    """通用数据采集方法"""
    data_type = "Community Club" if "/cc" in url else "Residents' Committee"
    print(f"开始采集 {data_type} 数据...")

    async with OnePACollector(url) as collector:
        # 采集所有数据（自动检测类型）
        data_list = await collector.collect_all_data()

        if data_list:
            # 保存原始数据（自动选择目录）
            await collector.save_data(data_list)

            print(f"{data_type} 数据采集完成，共采集到 {len(data_list)} 个 {data_type}")
            return True
        else:
            print(f"{data_type} 数据采集失败")
            return False


async def main():
    """主程序"""
    print("=== 新加坡 OnePA 数据采集系统 ===")

    # 采集 CC 数据
    print("\n1. 采集 Community Club 数据")
    cc_success = await collect_data("https://www.onepa.gov.sg/cc")

    # 采集 RC 数据
    print("\n2. 采集 Residents' Committee 数据")
    rc_success = await collect_data("https://www.onepa.gov.sg/rc")

    # 输出结果
    print("\n=== 采集结果汇总 ===")
    if cc_success:
        print("✅ Community Club 数据采集成功")
    else:
        print("❌ Community Club 数据采集失败")

    if rc_success:
        print("✅ Residents' Committee 数据采集成功")
    else:
        print("❌ Residents' Committee 数据采集失败")

    if cc_success and rc_success:
        print("\n🎉 所有数据采集完成！")
    else:
        print("\n⚠️  部分数据采集失败，请检查日志")


if __name__ == "__main__":
    asyncio.run(main())
