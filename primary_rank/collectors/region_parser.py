"""
区域数据解析器
负责解析和验证从网页中提取的区域数据
"""

import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime

from ..models.school_data import SchoolData, PhaseData


class RegionParser:
    """区域数据解析器"""
    
    # 常见的表格列标题模式
    PHASE_HEADERS = {
        'phase_1': ['phase 1', 'phase1', 'p1'],
        'phase_2a': ['phase 2a', 'phase2a', 'p2a'],
        'phase_2b': ['phase 2b', 'phase2b', 'p2b'], 
        'phase_2c': ['phase 2c', 'phase2c', 'p2c'],
        'phase_2cs': ['phase 2c(s)', 'phase2cs', 'p2cs', 'phase 2c (s)']
    }
    
    def __init__(self):
        self.column_mapping: Dict[int, str] = {}
    
    def parse_html_table(self, html_content: str, region: str, source_url: str) -> List[SchoolData]:
        """
        解析HTML表格内容，提取学校数据
        
        Args:
            html_content: HTML内容
            region: 区域名称
            source_url: 数据源URL
            
        Returns:
            学校数据列表
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找表格
        table = soup.find('table')
        if not table:
            return []
        
        # 分析表格结构
        self._analyze_table_structure(table)
        
        # 提取学校数据
        schools = []
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # 跳过表头
            school_data = self._parse_school_row(row, region, source_url)
            if school_data:
                schools.append(school_data)
        
        return schools
    
    def _analyze_table_structure(self, table) -> None:
        """分析表格结构，确定列的含义"""
        header_row = table.find('tr')
        if not header_row:
            return
        
        headers = header_row.find_all(['th', 'td'])
        self.column_mapping = {}
        
        for i, header in enumerate(headers):
            header_text = header.get_text().strip().lower()
            
            # 学校名称列
            if any(keyword in header_text for keyword in ['school', 'name', '学校']):
                self.column_mapping[i] = 'school_name'
                continue
            
            # 匹配各个阶段列
            for phase, keywords in self.PHASE_HEADERS.items():
                if any(keyword in header_text for keyword in keywords):
                    self.column_mapping[i] = phase
                    break
            
            # 如果没有匹配到，根据位置推测
            if i not in self.column_mapping and i > 0:
                phase_order = ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
                mapped_phases = [v for v in self.column_mapping.values() if v in phase_order]
                if len(mapped_phases) < len(phase_order):
                    self.column_mapping[i] = phase_order[len(mapped_phases)]
    
    def _parse_school_row(self, row, region: str, source_url: str) -> Optional[SchoolData]:
        """解析单个学校行"""
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            return None
        
        # 提取学校名称
        school_name = self._extract_school_name(cells[0])
        if not school_name or self._is_header_row(school_name):
            return None
        
        # 提取各阶段数据
        phases = {
            'phase_1': PhaseData(),
            'phase_2a': PhaseData(),
            'phase_2b': PhaseData(),
            'phase_2c': PhaseData(),
            'phase_2cs': PhaseData()
        }
        
        for i, cell in enumerate(cells[1:], 1):
            if i in self.column_mapping:
                phase_name = self.column_mapping[i]
                if phase_name in phases:
                    phases[phase_name] = self._parse_phase_cell(cell)
        
        # 如果没有列映射，按顺序分配
        if not any(v in ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs'] 
                  for v in self.column_mapping.values()):
            phase_names = ['phase_1', 'phase_2a', 'phase_2b', 'phase_2c', 'phase_2cs']
            for i, cell in enumerate(cells[1:]):
                if i < len(phase_names):
                    phases[phase_names[i]] = self._parse_phase_cell(cell)
        
        return SchoolData(
            school_name=school_name,
            region=region,
            phase_1=phases['phase_1'],
            phase_2a=phases['phase_2a'],
            phase_2b=phases['phase_2b'],
            phase_2c=phases['phase_2c'],
            phase_2cs=phases['phase_2cs'],
            last_updated=datetime.now(),
            source_url=source_url
        )
    
    def _extract_school_name(self, cell) -> str:
        """提取学校名称"""
        # 优先查找链接文本
        link = cell.find('a')
        if link:
            name = link.get_text().strip()
            if name:
                return name
        
        # 否则使用单元格文本
        return cell.get_text().strip()
    
    def _is_header_row(self, text: str) -> bool:
        """判断是否为表头行"""
        header_keywords = [
            'school', 'name', 'vacancy', 'phase', 'applied', 'taken',
            '学校', '空缺', '阶段', '申请', '录取'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in header_keywords)
    
    def _parse_phase_cell(self, cell) -> PhaseData:
        """解析阶段数据单元格"""
        text = cell.get_text().strip()
        return self._parse_phase_text(text)
    
    def _parse_phase_text(self, text: str) -> PhaseData:
        """解析阶段数据文本"""
        if not text or text.lower() in ['-', 'n/a', 'na', '']:
            return PhaseData()
        
        try:
            # 清理文本
            cleaned_text = re.sub(r'[^\d\/\-\s]', '', text)
            
            # 模式1: "vacancy/applied/taken" 或 "vacancy-applied-taken"
            if '/' in cleaned_text:
                parts = cleaned_text.split('/')
            elif '-' in cleaned_text:
                parts = cleaned_text.split('-')
            else:
                # 模式2: 只有数字
                numbers = re.findall(r'\d+', text)
                if numbers:
                    if len(numbers) == 1:
                        return PhaseData(vacancy=int(numbers[0]))
                    elif len(numbers) == 2:
                        return PhaseData(vacancy=int(numbers[0]), applied=int(numbers[1]))
                    elif len(numbers) >= 3:
                        return PhaseData(
                            vacancy=int(numbers[0]),
                            applied=int(numbers[1]),
                            taken=int(numbers[2])
                        )
                return PhaseData()
            
            # 解析分割后的部分
            if len(parts) >= 3:
                return PhaseData(
                    vacancy=int(parts[0].strip()) if parts[0].strip().isdigit() else 0,
                    applied=int(parts[1].strip()) if parts[1].strip().isdigit() else 0,
                    taken=int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                )
            elif len(parts) == 2:
                return PhaseData(
                    vacancy=int(parts[0].strip()) if parts[0].strip().isdigit() else 0,
                    applied=int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                )
            elif len(parts) == 1 and parts[0].strip().isdigit():
                return PhaseData(vacancy=int(parts[0].strip()))
            
        except (ValueError, IndexError):
            pass
        
        return PhaseData()
    
    def validate_school_data(self, school: SchoolData) -> List[str]:
        """
        验证学校数据的合理性
        
        Args:
            school: 学校数据对象
            
        Returns:
            验证错误信息列表
        """
        errors = []
        
        # 检查学校名称
        if not school.school_name or len(school.school_name.strip()) < 2:
            errors.append("学校名称无效")
        
        # 检查区域名称
        if not school.region or len(school.region.strip()) < 2:
            errors.append("区域名称无效")
        
        # 检查各阶段数据的合理性
        phases = [
            ('Phase 1', school.phase_1),
            ('Phase 2A', school.phase_2a),
            ('Phase 2B', school.phase_2b),
            ('Phase 2C', school.phase_2c),
            ('Phase 2C(S)', school.phase_2cs)
        ]
        
        for phase_name, phase_data in phases:
            phase_errors = self._validate_phase_data(phase_name, phase_data)
            errors.extend(phase_errors)
        
        return errors
    
    def _validate_phase_data(self, phase_name: str, phase_data: PhaseData) -> List[str]:
        """验证单个阶段数据"""
        errors = []
        
        # 检查数值范围
        if phase_data.vacancy < 0:
            errors.append(f"{phase_name}: 空缺数不能为负数")
        
        if phase_data.applied < 0:
            errors.append(f"{phase_name}: 申请数不能为负数")
        
        if phase_data.taken < 0:
            errors.append(f"{phase_name}: 录取数不能为负数")
        
        # 检查逻辑关系
        if phase_data.taken > phase_data.vacancy and phase_data.vacancy > 0:
            errors.append(f"{phase_name}: 录取数不能超过空缺数")
        
        if phase_data.taken > phase_data.applied and phase_data.applied > 0:
            errors.append(f"{phase_name}: 录取数不能超过申请数")
        
        # 检查极端值
        if phase_data.vacancy > 1000:
            errors.append(f"{phase_name}: 空缺数异常大 ({phase_data.vacancy})")
        
        if phase_data.applied > 5000:
            errors.append(f"{phase_name}: 申请数异常大 ({phase_data.applied})")
        
        return errors