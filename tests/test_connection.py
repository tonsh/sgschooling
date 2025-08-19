#!/usr/bin/env python3
"""
测试网站连接性和Playwright配置
"""

import asyncio
from playwright.async_api import async_playwright

async def test_basic_connection():
    """测试基本连接"""
    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        print("创建页面...")
        page = await browser.new_page()
        
        # 设置更长的超时时间
        page.set_default_timeout(60000)  # 60秒
        
        try:
            print("访问SGSchooling网站...")
            response = await page.goto("https://sgschooling.com/year/2025/", wait_until="domcontentloaded")
            
            print(f"响应状态: {response.status}")
            
            # 获取页面标题
            title = await page.title()
            print(f"页面标题: {title}")
            
            # 检查页面内容
            content_length = len(await page.content())
            print(f"页面内容长度: {content_length} 字符")
            
            # 尝试查找一些基本元素
            body = await page.query_selector("body")
            if body:
                print("✅ 成功找到body元素")
            
            # 查找可能的区域链接
            links = await page.query_selector_all("a")
            print(f"页面中的链接数量: {len(links)}")
            
            # 查找包含"primary-school-registration"的链接
            region_links = []
            for link in links[:20]:  # 只检查前20个链接
                href = await link.get_attribute("href")
                text = await link.inner_text()
                if href and "primary-school-registration" in href:
                    region_links.append((text.strip(), href))
            
            print(f"找到 {len(region_links)} 个可能的区域链接:")
            for text, href in region_links:
                print(f"  - {text}: {href}")
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_basic_connection())