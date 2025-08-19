#!/usr/bin/env python3
"""
调试页面结构，查看实际的HTML内容
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_page_structure():
    """调试页面结构"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)  # 显示浏览器
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        try:
            print("访问SGSchooling网站...")
            await page.goto("https://sgschooling.com/year/2025/", wait_until="networkidle")
            
            # 保存页面HTML到文件以便检查
            content = await page.content()
            with open("page_content.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("页面内容已保存到 page_content.html")
            
            # 查找所有链接
            links = await page.query_selector_all("a")
            print(f"\n所有链接 ({len(links)} 个):")
            for i, link in enumerate(links):
                href = await link.get_attribute("href")
                text = (await link.inner_text()).strip()
                if href and text:
                    print(f"{i+1:2d}. {text[:50]:<50} -> {href}")
            
            # 查找可能的区域或学校相关链接
            print(f"\n查找区域相关的链接...")
            region_patterns = [
                "ang-mo-kio", "bedok", "bishan", "bukit-batok", "bukit-merah",
                "bukit-panjang", "bukit-timah", "central", "choa-chu-kang",
                "clementi", "geylang", "hougang", "jurong-east", "jurong-west",
                "kallang", "marine-parade", "pasir-ris", "punggol", "queenstown",
                "sembawang", "sengkang", "serangoon", "tampines", "toa-payoh",
                "woodlands", "yishun"
            ]
            
            for pattern in region_patterns:
                region_links = await page.query_selector_all(f"a[href*='{pattern}']")
                if region_links:
                    print(f"找到 {pattern} 相关链接: {len(region_links)} 个")
                    for link in region_links:
                        href = await link.get_attribute("href")
                        text = (await link.inner_text()).strip()
                        print(f"  - {text}: {href}")
            
            # 等待用户检查页面
            print("\n浏览器窗口已打开，请检查页面结构...")
            print("按 Enter 继续...")
            input()
            
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_page_structure())