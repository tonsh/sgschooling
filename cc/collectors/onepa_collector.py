"""
OnePA 网站 Community Club 数据采集器
负责从 onepa.gov.sg/cc 采集新加坡 Community Club 数据
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright, Page, Browser
from ..models.cc_data import CCData
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.playwright_config import PLAYWRIGHT_CONFIG, SCRAPING_CONFIG


class OnePACollector:
    """OnePA 网站 Community Club 数据采集器"""

    BASE_URL = "https://www.onepa.gov.sg"
    CC_PATH = "/cc"
    RC_PATH = "/rc"

    def __init__(self, url: str, data_dir: str = "data"):
        self.url = url
        self.data_dir = Path(data_dir)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 根据 URL 自动判断数据类型
        self.data_type = self._detect_data_type(url)
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "cc" / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cc" / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cc" / "logs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "rc" / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "rc" / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "rc" / "logs").mkdir(parents=True, exist_ok=True)

    def _detect_data_type(self, url: str) -> str:
        """根据 URL 自动检测数据类型"""
        if "/cc" in url:
            return "cc"
        elif "/rc" in url:
            return "rc"
        else:
            return "unknown"

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_browser()
        return False

    async def start_browser(self) -> None:
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # OnePA网站需要非headless模式
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        )

        # 创建页面并配置
        context = await self.browser.new_context(
            viewport=PLAYWRIGHT_CONFIG["viewport"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
        )

        self.page = await context.new_page()

        # 隐藏webdriver特征
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
        """)

        # 设置超时
        self.page.set_default_timeout(PLAYWRIGHT_CONFIG["timeout"])

    async def close_browser(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()

    async def collect_all_cc_data(self) -> List[CCData]:
        """
        通用数据采集方法，兼容原接口

        Returns:
            数据列表
        """
        return await self.collect_all_data()

    async def collect_all_data(self) -> List[CCData]:
        """
        通用数据采集方法，根据 URL 自动识别数据类型

        Returns:
            数据列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 start_browser()")

        data_type_name = "Community Club" if self.data_type == "cc" else "Residents' Committee"
        print(f"正在访问 OnePA {data_type_name} 页面: {self.url}")

        try:
            # 访问页面
            await self.page.goto(self.url, wait_until="domcontentloaded")

            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle", timeout=30000)

            # 直接使用页面解析方式采集数据
            data_list = await self._collect_via_page_parsing()

            print(f"成功采集到 {len(data_list)} 个 {data_type_name}")
            return data_list

        except Exception as e:
            print(f"采集 {data_type_name} 数据失败: {e}")
            return []

    async def _collect_via_page_parsing(self) -> List[CCData]:
        """通用页面解析方法，支持 CC 和 RC 数据采集"""
        try:
            all_data_list = []
            data_type_name = "CC" if self.data_type == "cc" else "RC"

            # 等待列表加载，尝试不同的选择器
            try:
                await self.page.wait_for_selector(".ccLocatorlist__left__results", timeout=15000)
                results_selector = ".ccLocatorlist__left__results"
            except:
                try:
                    # 尝试其他可能的选择器
                    await self.page.wait_for_selector(".rcLocatorlist__left__results", timeout=15000)
                    results_selector = ".rcLocatorlist__left__results"
                except:
                    # 尝试通用选择器
                    await self.page.wait_for_selector("[class*='results'], .results", timeout=15000)
                    results_selector = "[class*='results']"

            # 使用下一页按钮遍历所有页面
            page_num = 1
            print(f"开始逐页采集{data_type_name}数据...")

            while True:
                print(f"正在采集第 {page_num} 页...")

                # 等待当前页面的列表加载
                await self.page.wait_for_timeout(1000)

                # 获取当前页的数据
                elements = self.page.locator(f"{results_selector} > *")
                current_page_count = await elements.count()
                print(f"第 {page_num} 页找到 {current_page_count} 个{data_type_name}")

                if current_page_count == 0:
                    print(f"当前页无{data_type_name}数据，停止采集")
                    break

                # 解析当前页的数据
                for i in range(current_page_count):
                    try:
                        element = elements.nth(i)
                        text = await element.inner_text()
                        
                        # 获取链接
                        link = await element.locator('a').first.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = self.BASE_URL + link

                        # 解析信息
                        data = self._parse_cc_text_with_url(text, link or "")
                        if data:
                            all_data_list.append(data)

                    except Exception as e:
                        print(f"解析第 {page_num} 页{data_type_name}元素 {i} 失败: {e}")
                        continue

                # 检查是否有下一页
                next_button = self.page.locator('.pagination span.btnNext')
                if await next_button.count() > 0:
                    # 检查下一页按钮是否可用（不是disabled状态）
                    parent_li = self.page.locator('.pagination li:has(.btnNext)')
                    is_disabled = await parent_li.get_attribute('class')

                    if is_disabled and 'disabled' in is_disabled:
                        print("已到达最后一页，停止采集")
                        break
                    else:
                        print("点击下一页...")
                        await next_button.click()
                        await asyncio.sleep(2)  # 等待页面更新
                        page_num += 1
                else:
                    print("未找到下一页按钮，停止采集")
                    break

            print(f"总共采集到 {len(all_data_list)} 个{data_type_name}")
            return all_data_list

        except Exception as e:
            print(f"{data_type_name}页面解析采集失败: {e}")
            return []




    def _parse_cc_text(self, text: str) -> Optional[CCData]:
        """解析CC文本信息"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < 2:
                return None

            # 第一行是CC名称
            name = lines[0]

            # 查找地址（通常包含邮政编码）
            address = ""
            postcode = ""

            for line in lines[1:]:
                if line.startswith("Tel:"):
                    continue

                # 检查是否包含邮政编码
                postcode_match = re.search(r'\b(\d{6})\b', line)
                if postcode_match:
                    postcode = postcode_match.group(1)
                    address = line
                    break

            if not address and len(lines) > 1:
                # 如果没找到包含邮政编码的地址，使用第二行
                address = lines[1]
                postcode_match = re.search(r'\b(\d{6})\b', address)
                if postcode_match:
                    postcode = postcode_match.group(1)

            if name and address:
                return CCData(
                    name=name.strip(),
                    address=address.strip(),
                    postcode=postcode,
                    url=""  # 旧方法无URL
                )

        except Exception as e:
            print(f"解析CC文本失败: {e}")

        return None

    def _parse_cc_text_with_url(self, text: str, url: str) -> Optional[CCData]:
        """解析CC文本信息并包含URL"""
        try:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if len(lines) < 2:
                return None

            # 第一行是CC名称
            name = lines[0]

            # 查找地址（通常包含邮政编码）
            address = ""
            postcode = ""

            for line in lines[1:]:
                if line.startswith("Tel:"):
                    continue

                # 检查是否包含邮政编码
                postcode_match = re.search(r'\b(\d{6})\b', line)
                if postcode_match:
                    postcode = postcode_match.group(1)
                    address = line
                    break

            if not address and len(lines) > 1:
                # 如果没找到包含邮政编码的地址，使用第二行
                address = lines[1]
                postcode_match = re.search(r'\b(\d{6})\b', address)
                if postcode_match:
                    postcode = postcode_match.group(1)

            # 验证URL和CC名称的关系
            url_valid = self._validate_cc_url(name, url)
            if not url_valid:
                print(f"警告: CC '{name}' 的URL验证失败: {url}")

            if name and address:
                return CCData(
                    name=name.strip(),
                    address=address.strip(),
                    postcode=postcode,
                    url=url
                )

        except Exception as e:
            print(f"解析CC文本失败: {e}")

        return None

    def _validate_cc_url(self, cc_name: str, url: str) -> bool:
        """验证CC URL和名称的对应关系"""
        try:
            if not url or not cc_name:
                return False

            # 从URL中提取路径的最后一段
            url_path = url.rstrip('/').split('/')[-1]

            # 将CC名称转换为URL格式：小写并用连字符替换空格
            expected_url_part = cc_name.lower().replace(' ', '-')

            # 验证URL路径是否匹配
            is_valid = url_path == expected_url_part

            if not is_valid:
                print(f"URL验证: '{cc_name}' -> 期望: '{expected_url_part}', 实际: '{url_path}'")

            return is_valid

        except Exception as e:
            print(f"URL验证失败: {e}")
            return False

    async def save_cc_data(self, data_list: List[CCData]) -> str:
        """保存数据到文件（兼容原接口）"""
        return await self.save_data(data_list)

    async def save_data(self, data_list: List[CCData]) -> str:
        """通用数据保存方法，根据数据类型自动选择目录和文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.data_type == "cc":
            file_path = self.data_dir / "cc" / "raw" / f"community_clubs_{timestamp}.json"
            latest_path = self.data_dir / "cc" / "raw" / "latest_community_clubs.json"
            data_key = "community_clubs"
            data_type_name = "CC"
        elif self.data_type == "rc":
            file_path = self.data_dir / "rc" / "raw" / f"residents_committees_{timestamp}.json"
            latest_path = self.data_dir / "rc" / "raw" / "latest_residents_committees.json"
            data_key = "residents_committees"
            data_type_name = "RC"
        else:
            raise ValueError(f"未知的数据类型: {self.data_type}")

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建数据格式
        json_data = {
            data_key: [item.to_dict() for item in data_list],
            "metadata": {
                "total_count": len(data_list),
                "crawl_time": datetime.now().isoformat(),
                "source_url": self.url,
                "data_version": "1.0"
            }
        }

        # 保存数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        # 同时保存最新的数据
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"{data_type_name} 数据已保存到: {file_path}")
        return str(file_path)
