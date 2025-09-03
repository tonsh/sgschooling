"""
OnePA 网站 Community Club 数据采集器   
负责从 onepa.gov.sg/cc 采集新加坡 Community Club 数据	
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

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
    API_PATH = "/pacesapi/catalogs/outlets"

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "cc" / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cc" / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "cc" / "logs").mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_browser()

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
        采集所有 Community Club 数据

        Returns:
            CC 数据列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 start_browser()")

        cc_url = self.BASE_URL + self.CC_PATH
        print(f"正在访问 OnePA CC 页面: {cc_url}")

        try:
            # 访问 CC 页面
            await self.page.goto(cc_url, wait_until="domcontentloaded")

            # 等待页面加载完成
            await self.page.wait_for_load_state("networkidle", timeout=30000)

            # 尝试通过 API 获取数据
            cc_data_list = await self._collect_cc_via_api()

            if not cc_data_list:
                # 如果 API 方式失败，尝试页面解析
                print("API 方式失败，尝试页面解析...")
                cc_data_list = await self._collect_cc_via_page_parsing()

            print(f"成功采集到 {len(cc_data_list)} 个 Community Club")
            return cc_data_list

        except Exception as e:
            print(f"采集 CC 数据失败: {e}")
            return []

    async def _collect_cc_via_api(self) -> List[CCData]:
        """通过 API 接口采集 CC 数据"""
        try:
            # 监听网络请求，寻找 API 调用
            api_responses = []

            def handle_response(response):
                if self.API_PATH in response.url and "OutletType=CC" in response.url:
                    print(f"捕获到 API 请求: {response.url}")
                    api_responses.append(response)

            self.page.on("response", handle_response)

            # 尝试触发页面的 API 调用
            try:
                # 等待页面完全加载
                await self.page.wait_for_load_state("networkidle", timeout=10000)

                # 查找并点击可能触发 API 调用的元素
                search_elements = await self.page.locator("input, button, .search").all()
                if search_elements:
                    # 尝试触发搜索或加载
                    await search_elements[0].click()
                    await asyncio.sleep(2)

            except Exception as e:
                print(f"触发页面 API 调用失败: {e}")

            # 等待网络请求完成
            await asyncio.sleep(5)

            # 检查捕获的网络请求
            if api_responses:
                print(f"发现 {len(api_responses)} 个 API 响应")
                for api_response in api_responses:
                    try:
                        response_data = await api_response.json()
                        print(f"API 响应状态: {api_response.status}")
                        result = self._parse_api_response(response_data)
                        if result:
                            return result
                    except Exception as e:
                        print(f"解析 API 响应失败: {e}")

            # 尝试直接调用 API
            api_url = f"{self.BASE_URL}{self.API_PATH}?outletMode=location&OutletType=CC"
            print(f"尝试直接访问 API: {api_url}")

            try:
                # 使用页面的 fetch API
                response = await self.page.evaluate(f"""
                    async () => {{
                        try {{
                            const response = await fetch('{api_url}');
                            if (response.ok) {{
                                return await response.json();
                            }} else {{
                                return {{ error: 'HTTP ' + response.status }};
                            }}
                        }} catch (error) {{
                            return {{ error: error.message }};
                        }}
                    }}
                """)

                if response and isinstance(response, dict) and 'error' not in response:
                    return self._parse_api_response(response)
                else:
                    print(f"API 调用返回错误: {response}")

            except Exception as e:
                print(f"直接 API 调用失败: {e}")

            return []

        except Exception as e:
            print(f"API 采集失败: {e}")
            return []

    def _parse_api_response(self, response_data: Dict[str, Any]) -> List[CCData]:
        """解析 API 响应数据"""
        cc_list = []

        try:
            # API 响应可能包含不同的数据结构，需要适应性解析
            outlets = []
            if isinstance(response_data, dict):
                # 尝试不同的键名
                for key in ['outlets', 'data', 'results', 'items']:
                    if key in response_data:
                        outlets = response_data[key]
                        break

                # 如果直接是列表
                if not outlets and isinstance(response_data, list):
                    outlets = response_data

            for outlet in outlets:
                if isinstance(outlet, dict):
                    cc_data = self._extract_cc_data_from_dict(outlet)
                    if cc_data:
                        cc_list.append(cc_data)

        except Exception as e:
            print(f"解析 API 数据失败: {e}")

        return cc_list

    def _extract_cc_data_from_dict(self, outlet_dict: Dict[str, Any]) -> Optional[CCData]:
        """从字典数据中提取 CC 信息"""
        try:
            # 提取名称
            name = ""
            for name_key in ['name', 'title', 'outlet_name', 'cc_name']:
                if name_key in outlet_dict:
                    name = str(outlet_dict[name_key]).strip()
                    break

            # 提取地址
            address = ""
            for addr_key in ['address', 'full_address', 'street_address']:
                if addr_key in outlet_dict:
                    address = str(outlet_dict[addr_key]).strip()
                    break

            # 提取邮政编码
            postcode = ""
            for pc_key in ['postcode', 'postal_code', 'zip']:
                if pc_key in outlet_dict:
                    postcode = str(outlet_dict[pc_key]).strip()
                    break

            # 如果地址中包含邮政编码，提取出来
            if not postcode and address:
                postcode_match = re.search(r'\b(\d{6})\b', address)
                if postcode_match:
                    postcode = postcode_match.group(1)

            if name and address:
                return CCData(
                    name=name,
                    address=address,
                    postcode=postcode,
                    url=""  # API方式暂时无法获取URL
                )

        except Exception as e:
            print(f"提取 CC 数据失败: {e}")

        return None

    async def _collect_cc_via_page_parsing(self) -> List[CCData]:
        """通过页面解析采集 CC 数据（支持分页）"""
        try:
            all_cc_list = []

            # 等待CC列表加载
            await self.page.wait_for_selector(".ccLocatorlist__left__results", timeout=15000)

            # 使用下一页按钮遍历所有页面
            page_num = 1
            print("开始逐页采集CC数据...")

            while True:
                print(f"正在采集第 {page_num} 页...")

                # 等待当前页面的CC列表加载
                await self.page.wait_for_timeout(1000)

                # 获取当前页的CC数据
                cc_elements = self.page.locator(".ccLocatorlist__left__results > *")
                current_page_count = await cc_elements.count()
                print(f"第 {page_num} 页找到 {current_page_count} 个CC")

                if current_page_count == 0:
                    print("当前页无CC数据，停止采集")
                    break

                # 解析当前页的CC数据
                for i in range(current_page_count):
                    try:
                        element = cc_elements.nth(i)
                        text = await element.inner_text()
                        
                        # 获取CC链接
                        cc_link = await element.locator('a').first.get_attribute('href')
                        if cc_link and not cc_link.startswith('http'):
                            cc_link = self.BASE_URL + cc_link

                        # 解析CC信息
                        cc_data = self._parse_cc_text_with_url(text, cc_link or "")
                        if cc_data:
                            all_cc_list.append(cc_data)

                    except Exception as e:
                        print(f"解析第 {page_num} 页CC元素 {i} 失败: {e}")
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

            print(f"总共采集到 {len(all_cc_list)} 个Community Club")
            return all_cc_list

        except Exception as e:
            print(f"页面解析采集失败: {e}")
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

    async def save_cc_data(self, cc_list: List[CCData]) -> str:
        """保存 CC 数据到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.data_dir / "cc" / "raw" / f"community_clubs_{timestamp}.json"

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 构建数据格式
        cc_json_data = {
            "community_clubs": [cc.to_dict() for cc in cc_list],
            "metadata": {
                "total_count": len(cc_list),
                "crawl_time": datetime.now().isoformat(),
                "source_url": f"{self.BASE_URL}{self.CC_PATH}",
                "data_version": "1.0"
            }
        }

        # 保存数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cc_json_data, f, ensure_ascii=False, indent=2)

        # 同时保存最新的数据
        latest_path = self.data_dir / "cc" / "raw" / "latest_community_clubs.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(cc_json_data, f, ensure_ascii=False, indent=2)

        print(f"CC 数据已保存到: {file_path}")
        return str(file_path)

