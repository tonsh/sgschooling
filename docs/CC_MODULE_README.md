# CC 模块 - 新加坡 Community Club 数据采集系统

## 项目概述

CC 模块是一个专门用于采集和分析新加坡所有 Community Club 数据的独立模块。该模块从 https://www.onepa.gov.sg/cc 获取数据，包含 CC 的名称、地址、邮政编码和区域信息。

## 功能特性

- **数据采集**：从 OnePA 官网自动采集所有 Community Club 信息
- **数据结构**：包含 name, address, postcode, region 四个核心字段
- **区域分析**：按区域统计 CC 数量和密度
- **报告生成**：自动生成 JSON 和 Markdown 格式的分析报告
- **数据存储**：支持原始数据和处理结果的分层存储

## 数据结构

### CCData (Community Club 数据)
```python
@dataclass
class CCData:
    name: str        # CC 名称
    address: str     # 完整地址
    postcode: str    # 邮政编码
    region: str      # 所在区域
```

### RegionCCData (区域统计数据)
```python
@dataclass
class RegionCCData:
    name: str               # 区域名称
    cc_count: int          # 该区域 CC 数量
    cc_list: List[CCData]  # CC 列表
```

## 目录结构

```
cc/
├── __init__.py                    # 模块初始化
├── models/                        # 数据模型
│   ├── __init__.py
│   └── cc_data.py                # CC 数据结构定义
├── collectors/                    # 数据采集器
│   ├── __init__.py
│   └── onepa_collector.py        # OnePA 网站采集器
├── data_processor.py             # 数据处理和分析
└── main.py                       # 主程序入口
```

## 使用方法

### 1. 基本使用

```python
import asyncio
from cc.main import main

# 运行完整的数据采集和分析流程
asyncio.run(main())
```

### 2. 单独采集数据

```python
from cc.collectors.onepa_collector import OnePACollector

async def collect_data():
    async with OnePACollector() as collector:
        cc_list = await collector.collect_all_cc_data()
        await collector.save_cc_data(cc_list)
```

### 3. 单独处理数据

```python
from cc.data_processor import CCDataProcessor

# 处理已采集的数据
processor = CCDataProcessor()
cc_list = processor.load_latest_cc_data()
region_data_list = processor.analyze_cc_by_region(cc_list)
summary = processor.generate_summary_report(cc_list, region_data_list)
processor.save_summary_report(summary)
processor.save_markdown_report(summary)
```

### 4. 手动创建数据

```python
from cc.models.cc_data import CCData, RegionCCData

# 创建 CC 数据
cc = CCData(
    name="Ang Mo Kio CC",
    address="123 Ang Mo Kio Ave 6, Singapore 560123", 
    postcode="560123",
    region="Ang Mo Kio"
)

# 创建区域统计
cc_list = [cc]
region_data = RegionCCData.from_ccs("Ang Mo Kio", cc_list)
```

## 数据采集策略

模块采用多重数据采集策略确保数据获取的稳定性：

1. **API 优先**：尝试通过 OnePA 的内部 API (`/pacesapi/catalogs/outlets`) 获取结构化数据
2. **页面解析**：如果 API 访问失败，回退到页面元素解析
3. **智能推断**：基于邮政编码自动推断区域信息

## 区域映射

系统内置了新加坡邮政编码到区域的映射表，能够根据邮政编码前两位自动识别所属区域：

- `01-16`: Central 区域
- `17-18`: Novena 区域  
- `19-20`: Serangoon 区域
- `21-23`: Ang Mo Kio 区域
- 等等...

## 输出文件

### 原始数据
- `data/cc/raw/community_clubs_YYYYMMDD_HHMMSS.json` - 带时间戳的原始数据
- `data/cc/raw/latest_community_clubs.json` - 最新原始数据

### 处理结果
- `data/cc/processed/cc_summary_report_YYYYMMDD_HHMMSS.json` - 带时间戳的分析报告
- `data/cc/processed/latest_cc_summary_report.json` - 最新分析报告
- `data/cc/processed/cc_report_YYYYMMDD_HHMMSS.md` - 带时间戳的 Markdown 报告
- `data/cc/processed/latest_cc_report.md` - 最新 Markdown 报告

## 报告内容

生成的分析报告包含：

### 概览统计
- Community Club 总数
- 覆盖区域数量
- 平均每区域 CC 数量

### 区域排名表格
| 排名 | 区域 | CC 数量 | 密度 |
|------|------|---------|------|
| 1    | XXX  | XX      | XX   |

### 重点信息
- CC 最多的区域及数量
- CC 最少的区域及数量

## 测试

模块包含完整的单元测试：

```bash
# 测试数据模型
python tests/test_cc_models.py

# 测试数据处理器
python tests/test_cc_data_processor.py
```

## 依赖项

- `playwright` - 用于网页数据采集
- `asyncio` - 异步编程支持
- `dataclasses` - 数据类装饰器
- `pathlib` - 路径处理
- `json` - JSON 数据处理

## 注意事项

1. 首次运行需要有网络连接以采集数据
2. 数据采集过程中会有适当延迟以避免过频访问
3. 系统会优先使用已存在的数据，避免重复采集
4. 支持交互式选择是否重新采集数据

## 开发规范

- 所有代码遵循 Python PEP8 规范
- 使用类型注解提高代码可读性
- 包含完整的文档字符串
- 异常处理覆盖主要失败场景
- 数据文件使用 UTF-8 编码确保中文支持