"""
SGSchooling网站数据采集器
负责从sgschooling.com采集新加坡小学P1注册数据
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from ..models.school_data import SchoolData, PhaseData
from ..models.region_data import RegionData
from ..models.crawl_result import CrawlResult, CrawlStats
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from config.playwright_config import PLAYWRIGHT_CONFIG, SCRAPING_CONFIG


class SGSchoolingCollector:
    """SGSchooling网站数据采集器"""
    
    BASE_URL = "https://sgschooling.com"
    YEAR_PATH = "/year/2025/"
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "raw" / "regions").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "processed").mkdir(exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)
    
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
            headless=PLAYWRIGHT_CONFIG["headless"],
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        # 创建页面并配置
        self.page = await self.browser.new_page(
            viewport=PLAYWRIGHT_CONFIG["viewport"],
            user_agent=PLAYWRIGHT_CONFIG["user_agent"]
        )
        
        # 设置超时
        self.page.set_default_timeout(PLAYWRIGHT_CONFIG["timeout"])
    
    async def close_browser(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
    
    async def discover_regions(self) -> List[str]:
        """
        发现所有可用的区域
        
        Returns:
            区域名称列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用start_browser()")
        
        main_url = self.BASE_URL + self.YEAR_PATH
        print(f"正在访问主页面: {main_url}")
        
        try:
            # 访问主页面
            await self.page.goto(main_url, wait_until="networkidle")
            
            # 等待页面加载完成
            await self.page.wait_for_load_state("domcontentloaded")
            
            # 查找所有区域链接
            # 寻找指向各区域的链接
            region_links = await self.page.locator("a[href*='/year/2025/']").all()
            
            regions = []
            for link in region_links:
                href = await link.get_attribute("href")
                if href and href != self.YEAR_PATH and not href.endswith("/all"):
                    # 提取区域名称
                    region_name = href.replace(self.YEAR_PATH, "").strip("/")
                    if region_name and region_name not in regions:
                        regions.append(region_name)
            
            # 如果通过链接找不到，尝试通过文本内容查找
            if not regions:
                print("通过链接未找到区域，尝试通过页面内容查找...")
                regions = await self._extract_regions_from_content()
            
            print(f"发现 {len(regions)} 个区域: {regions[:5]}..." if len(regions) > 5 else f"发现 {len(regions)} 个区域: {regions}")
            return sorted(regions)
            
        except Exception as e:
            print(f"区域发现失败: {e}")
            return []
    
    async def _extract_regions_from_content(self) -> List[str]:
        """从页面内容中提取区域名称"""
        try:
            # 获取页面所有文本内容
            content = await self.page.content()
            
            # 使用正则表达式查找可能的区域名称
            # 新加坡常见的区域名称模式
            singapore_regions = [
                "ang-mo-kio", "bedok", "bishan", "bukit-batok", "bukit-merah",
                "bukit-panjang", "bukit-timah", "central", "choa-chu-kang",
                "clementi", "geylang", "hougang", "jurong-east", "jurong-west",
                "kallang", "marine-parade", "pasir-ris", "punggol", "queenstown",
                "sembawang", "sengkang", "serangoon", "tampines", "toa-payoh",
                "woodlands", "yishun"
            ]
            
            found_regions = []
            for region in singapore_regions:
                # 检查区域是否在页面内容中存在
                if region in content.lower() or region.replace("-", " ") in content.lower():
                    found_regions.append(region)
            
            return found_regions
            
        except Exception as e:
            print(f"从页面内容提取区域失败: {e}")
            return []
    
    async def scrape_region_data(self, region: str) -> Optional[RegionData]:
        """
        采集指定区域的学校数据
        
        Args:
            region: 区域名称
            
        Returns:
            区域数据对象
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用start_browser()")
        
        region_url = f"{self.BASE_URL}{self.YEAR_PATH}{region}"
        print(f"正在采集区域数据: {region} ({region_url})")
        
        try:
            # 访问区域页面
            await self.page.goto(region_url, wait_until="networkidle")
            
            # 等待表格加载
            await self.page.wait_for_selector("table", timeout=10000)
            
            # 提取学校数据
            schools = await self._extract_schools_from_table(region, region_url)
            
            # 创建区域数据对象
            region_data = RegionData(
                region_name=region,
                schools=schools,
                crawl_timestamp=datetime.now(),
                source_url=region_url
            )
            
            print(f"区域 {region} 采集完成，共 {len(schools)} 所学校")
            return region_data
            
        except Exception as e:
            print(f"采集区域 {region} 失败: {e}")
            return None
    
    async def _extract_schools_from_table(self, region: str, source_url: str) -> List[SchoolData]:
        """从表格中提取学校数据"""
        schools = []
        
        try:
            # 查找表格行
            rows = await self.page.locator("table tr").all()
            
            for row in rows:
                try:
                    # 获取行中的所有单元格
                    cells = await row.locator("td").all()
                    
                    if len(cells) < 6:  # 至少需要学校名称 + 5个阶段数据
                        continue
                    
                    # 提取学校名称（通常在第一列）
                    school_name_element = cells[0].locator("a").first
                    if await school_name_element.count() > 0:
                        school_name = await school_name_element.inner_text()
                    else:
                        school_name = await cells[0].inner_text()
                    
                    school_name = school_name.strip()
                    if not school_name or school_name.lower() in ["school", "vacancy", "phase"]:
                        continue
                    
                    # 提取各阶段数据
                    phases_data = []
                    for i in range(1, min(6, len(cells))):  # 提取5个阶段的数据
                        cell_text = await cells[i].inner_text()
                        phase_data = self._parse_phase_data(cell_text)
                        phases_data.append(phase_data)
                    
                    # 确保有5个阶段的数据
                    while len(phases_data) < 5:
                        phases_data.append(PhaseData())
                    
                    # 创建学校数据对象
                    school = SchoolData(
                        school_name=school_name,
                        region=region,
                        phase_1=phases_data[0],
                        phase_2a=phases_data[1],
                        phase_2b=phases_data[2],
                        phase_2c=phases_data[3],
                        phase_2cs=phases_data[4],
                        last_updated=datetime.now(),
                        source_url=source_url
                    )
                    
                    schools.append(school)
                    
                except Exception as e:
                    print(f"解析学校行数据失败: {e}")
                    continue
            
        except Exception as e:
            print(f"提取表格数据失败: {e}")
        
        return schools
    
    def _parse_phase_data(self, cell_text: str) -> PhaseData:
        """解析阶段数据文本"""
        try:
            # 清理文本
            text = cell_text.strip().replace(",", "")
            
            # 尝试提取数字模式: "vacancy / applied / taken"
            numbers = re.findall(r'\d+', text)
            
            if len(numbers) >= 3:
                return PhaseData(
                    vacancy=int(numbers[0]),
                    applied=int(numbers[1]),
                    taken=int(numbers[2])
                )
            elif len(numbers) == 2:
                return PhaseData(
                    vacancy=int(numbers[0]),
                    applied=int(numbers[1]),
                    taken=int(numbers[1])  # 假设applied等于taken
                )
            elif len(numbers) == 1:
                return PhaseData(vacancy=int(numbers[0]))
            else:
                return PhaseData()
                
        except Exception:
            return PhaseData()
    
    async def crawl_all_regions(self) -> CrawlResult:
        """
        爬取所有区域的数据
        
        Returns:
            爬取结果对象
        """
        print("开始爬取所有区域数据...")
        
        # 发现所有区域
        regions = await self.discover_regions()
        
        if not regions:
            print("未发现任何区域，爬取失败")
            result = CrawlResult.create_new(0)
            result.finalize()
            return result
        
        # 创建爬取结果对象
        result = CrawlResult.create_new(len(regions))
        
        # 逐个爬取区域数据
        for region in regions:
            try:
                # 添加延迟以避免过于频繁的请求
                await asyncio.sleep(SCRAPING_CONFIG["request_delay"] / 1000)
                
                region_data = await self.scrape_region_data(region)
                
                if region_data:
                    # 保存区域数据
                    file_path = await self._save_region_data(region_data)
                    result.mark_region_success(region, file_path)
                    result.stats.total_schools += len(region_data.schools)
                else:
                    result.mark_region_failure(region)
                    result.add_error(region, "scraping_failed", "区域数据采集失败")
                
            except Exception as e:
                result.mark_region_failure(region)
                result.add_error(region, "exception", str(e))
                print(f"爬取区域 {region} 时发生异常: {e}")
        
        # 完成爬取
        result.finalize()
        
        # 保存爬取结果
        await self._save_crawl_result(result)
        
        print(f"爬取完成！成功: {result.stats.successful_regions}, 失败: {result.stats.failed_regions}")
        return result
    
    async def _save_region_data(self, region_data: RegionData) -> str:
        """保存区域数据到文件"""
        file_path = self.data_dir / "raw" / "regions" / f"{region_data.region_name}.json"
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(region_data.to_dict(), f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    async def _save_crawl_result(self, result: CrawlResult) -> None:
        """保存爬取结果"""
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        file_path = self.data_dir / "logs" / f"crawl_result_{timestamp}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 同时保存最新的爬取结果
        latest_path = self.data_dir / "logs" / "latest_crawl_result.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)