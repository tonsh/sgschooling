#!/usr/bin/env python3
"""
简单测试页面访问
"""

import asyncio
from playwright.async_api import async_playwright

async def simple_page_test():
    """简单页面测试"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("访问SGSchooling网站...")
            # 使用更基本的等待条件
            await page.goto("https://sgschooling.com/year/2025/", wait_until="domcontentloaded")
            
            # 等待页面加载完成
            await page.wait_for_timeout(5000)  # 等待5秒
            
            # 获取页面基本信息
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 截图保存（如果需要）
            # await page.screenshot(path="sgschooling_page.png")
            print("页面截图已保存为 sgschooling_page.png")
            
            # 查找常见的页面元素
            print("\n页面元素检查:")
            
            # 检查body
            body = await page.query_selector("body")
            if body:
                print("✅ 找到 body 元素")
            
            # 检查导航菜单
            nav_elements = await page.query_selector_all("nav, .nav, .navbar, .navigation")
            print(f"导航元素: {len(nav_elements)} 个")
            
            # 检查主要内容区域
            main_elements = await page.query_selector_all("main, .main, .content, #content")
            print(f"主要内容区域: {len(main_elements)} 个")
            
            # 检查链接
            all_links = await page.query_selector_all("a[href]")
            print(f"所有链接: {len(all_links)} 个")
            
            # 查找包含新加坡区域名称的链接
            print("\n查找区域链接...")
            singapore_regions = [
                "ang mo kio", "bedok", "bishan", "bukit batok", "bukit merah",
                "bukit panjang", "bukit timah", "central", "choa chu kang",
                "clementi", "geylang", "hougang", "jurong east", "jurong west",
                "kallang", "marine parade", "pasir ris", "punggol", "queenstown",
                "sembawang", "sengkang", "serangoon", "tampines", "toa payoh",
                "woodlands", "yishun"
            ]
            
            found_regions = []
            for link in all_links:
                href = await link.get_attribute("href")
                text = (await link.inner_text() or "").lower().strip()
                
                if href and text:
                    for region in singapore_regions:
                        if region in text or region.replace(" ", "-") in href:
                            found_regions.append((text, href))
                            break
            
            print(f"找到可能的区域链接: {len(found_regions)} 个")
            for text, href in found_regions[:10]:  # 只显示前10个
                print(f"  - {text}: {href}")
            
            # 直接搜索页面文本中的关键信息
            page_text = await page.inner_text("body")
            if "primary school" in page_text.lower():
                print("✅ 页面包含 'primary school' 关键字")
            if "registration" in page_text.lower():
                print("✅ 页面包含 'registration' 关键字")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_page_test())