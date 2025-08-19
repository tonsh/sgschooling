"""
环境配置测试
验证Playwright和MCP环境是否正确配置
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from playwright.async_api import async_playwright
from config.playwright_config import PLAYWRIGHT_CONFIG, MOE_URLS


async def test_playwright_basic():
    """测试Playwright基础功能"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=PLAYWRIGHT_CONFIG["headless"]
            )
            page = await browser.new_page(
                viewport=PLAYWRIGHT_CONFIG["viewport"],
                user_agent=PLAYWRIGHT_CONFIG["user_agent"]
            )
            
            # 测试访问MOE官网
            await page.goto(MOE_URLS["base"])
            title = await page.title()
            print(f"✅ 成功访问MOE官网，页面标题: {title}")
            
            # 截图测试
            await page.screenshot(path="tests/moe_homepage.png")
            print("✅ 页面截图保存成功")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Playwright测试失败: {e}")
        return False


async def test_moe_p1_page():
    """测试访问MOE P1注册页面"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 访问P1注册页面
            full_url = MOE_URLS["base"] + MOE_URLS["p1_registration"]
            await page.goto(full_url)
            
            # 等待页面加载
            await page.wait_for_load_state("networkidle")
            
            title = await page.title()
            print(f"✅ 成功访问P1注册页面，页面标题: {title}")
            
            # 查找相关内容
            content = await page.content()
            if "Primary 1" in content or "P1" in content:
                print("✅ 页面包含P1相关内容")
            else:
                print("⚠️  页面可能不包含P1相关内容")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ MOE P1页面测试失败: {e}")
        return False


def test_imports():
    """测试重要库的导入"""
    try:
        import playwright
        print(f"✅ Playwright导入成功")
        
        import mcp
        print(f"✅ MCP导入成功")
        
        import requests
        print(f"✅ Requests导入成功")
        
        import json
        print(f"✅ JSON导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 库导入失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 开始环境配置测试...")
    print("=" * 50)
    
    # 测试库导入
    print("\n📚 测试库导入:")
    import_success = test_imports()
    
    # 测试Playwright基础功能
    print("\n🌐 测试Playwright基础功能:")
    playwright_success = await test_playwright_basic()
    
    # 测试MOE网站访问
    print("\n🏫 测试MOE网站访问:")
    moe_success = await test_moe_p1_page()
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"库导入测试: {'✅ 通过' if import_success else '❌ 失败'}")
    print(f"Playwright测试: {'✅ 通过' if playwright_success else '❌ 失败'}")
    print(f"MOE网站测试: {'✅ 通过' if moe_success else '❌ 失败'}")
    
    all_success = import_success and playwright_success and moe_success
    print(f"\n🎯 总体结果: {'✅ 所有测试通过！' if all_success else '❌ 部分测试失败'}")
    
    return all_success


if __name__ == "__main__":
    asyncio.run(main())