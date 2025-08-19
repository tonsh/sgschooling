#!/usr/bin/env python3
"""
生成数据采集摘要报告
"""

import json
from pathlib import Path
from collections import Counter

def generate_summary():
    """生成数据摘要"""
    data_dir = Path("data/raw/regions")
    
    total_regions = 0
    total_schools = 0
    total_vacancy = 0
    total_applied = 0
    total_taken = 0
    
    school_names = []
    region_stats = {}
    
    print("📊 SGSchooling 2025年小学报名数据采集摘要")
    print("=" * 50)
    
    for json_file in data_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            region_info = data["region"]
            schools = data["schools"]
            
            total_regions += 1
            total_schools += len(schools)
            
            region_vacancy = region_info["vacancy"]
            region_applied = region_info["applied"] 
            region_taken = region_info["taken"]
            
            total_vacancy += region_vacancy
            total_applied += region_applied
            total_taken += region_taken
            
            region_stats[region_info["name"]] = {
                "schools": len(schools),
                "vacancy": region_vacancy,
                "applied": region_applied,
                "taken": region_taken,
                "competition_ratio": round(region_applied / region_vacancy, 2) if region_vacancy > 0 else 0
            }
            
            # 收集学校名称
            for school in schools:
                school_names.append(school["name"])
                
        except Exception as e:
            print(f"⚠️  处理文件 {json_file} 时出错: {e}")
    
    print(f"📍 总区域数: {total_regions}")
    print(f"🏫 总学校数: {total_schools}")
    print(f"💺 总学位数: {total_vacancy:,}")
    print(f"📝 总申请数: {total_applied:,}")
    print(f"✅ 总录取数: {total_taken:,}")
    print(f"📊 整体竞争比例: {total_applied/total_vacancy:.2f}" if total_vacancy > 0 else "N/A")
    print(f"📈 整体录取率: {total_taken/total_applied:.1%}" if total_applied > 0 else "N/A")
    
    print(f"\n🏆 区域统计排行榜:")
    print("-" * 70)
    print(f"{'区域':<20} {'学校数':<8} {'学位数':<8} {'申请数':<8} {'竞争比例':<10}")
    print("-" * 70)
    
    # 按竞争比例排序
    sorted_regions = sorted(region_stats.items(), key=lambda x: x[1]["competition_ratio"], reverse=True)
    
    for region_name, stats in sorted_regions:
        print(f"{region_name:<20} {stats['schools']:<8} {stats['vacancy']:<8} {stats['applied']:<8} {stats['competition_ratio']:<10}")
    
    print(f"\n🔥 竞争最激烈的区域 (Top 5):")
    for i, (region_name, stats) in enumerate(sorted_regions[:5], 1):
        print(f"{i}. {region_name}: {stats['competition_ratio']} ({stats['applied']}/{stats['vacancy']})")
    
    print(f"\n😌 竞争最温和的区域 (Top 5):")
    for i, (region_name, stats) in enumerate(sorted_regions[-5:], 1):
        print(f"{i}. {region_name}: {stats['competition_ratio']} ({stats['applied']}/{stats['vacancy']})")
    
    # 学校名称统计
    school_counter = Counter(school_names)
    duplicate_schools = [(name, count) for name, count in school_counter.items() if count > 1]
    
    if duplicate_schools:
        print(f"\n⚠️  发现重复的学校名称:")
        for name, count in duplicate_schools[:10]:
            print(f"  - {name}: {count} 次")
    
    print(f"\n✨ 数据采集成功完成！")
    return {
        "total_regions": total_regions,
        "total_schools": total_schools,
        "total_vacancy": total_vacancy,
        "total_applied": total_applied,
        "total_taken": total_taken,
        "region_stats": region_stats
    }

if __name__ == "__main__":
    generate_summary()