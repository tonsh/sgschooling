# SGSchooling 数据格式规范

## 概述

本文档定义了新加坡小学报名数据的标准JSON格式，确保数据一致性和可处理性。

## 数据结构

### SchoolData (学校数据)

```json
{
  "name": "Alexandra Primary School",
  "cn_name": "亚历山德拉小学",
  "region": "alexandra",
  "vacancy": 180,
  "phase_1": {
    "vacancy": 20,
    "applied": 18,
    "taken": 18
  },
  "phase_2a": {
    "vacancy": 30,
    "applied": 45,
    "taken": 30
  },
  "phase_2b": {
    "vacancy": 25,
    "applied": 40,
    "taken": 25
  },
  "phase_2c": {
    "vacancy": 50,
    "applied": 35,
    "taken": 35
  },
  "phase_2cs": {
    "vacancy": 52,
    "applied": 20,
    "taken": 20
  }
}
```

**字段说明：**
- `name`: 学校英文名称
- `cn_name`: 学校中文名称
- `region`: 所在区域
- `vacancy`: 学校总学位数 (自动计算 = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.vacancy)
- `phase_1/2a/2b/2c/2cs`: 各阶段数据
  - `vacancy`: 该阶段可用名额
  - `applied`: 该阶段申请人数
  - `taken`: 该阶段录取人数

**注意：** `vacancy` 字段在JSON中是可选的，SchoolData模型会根据各阶段数据自动计算总学位数。

### RegionData (区域数据)

```json
{
  "name": "alexandra",
  "cn_name": "亚历山德拉",
  "school_num": 3,
  "vacancy": 540,
  "applied": 420,
  "taken": 385
}
```

**字段说明：**
- `name`: 区域英文名称
- `cn_name`: 区域中文名称
- `school_num`: 该区域学校数量
- `vacancy`: 该区域所有学校的总学位数量
- `applied`: 该区域所有学校的总报名数量
- `taken`: 该区域所有学校的总录取数量

## 文件组织结构

### 原始数据存储

```
data/
├── raw/
│   ├── regions/
│   │   ├── alexandra.json          # 单个区域数据
│   │   ├── ang-mo-kio.json        # 单个区域数据
│   │   └── ...                    # 其他区域数据
│   └── summary/
│       ├── all_schools.json       # 所有学校数据汇总
│       └── all_regions.json       # 所有区域数据汇总
```

### 区域文件格式 (例: alexandra.json)

```json
{
  "region": {
    "name": "alexandra",
    "cn_name": "亚历山德拉",
    "school_num": 3,
    "vacancy": 540,
    "applied": 420,
    "taken": 385
  },
  "schools": [
    {
      "name": "Alexandra Primary School",
      "cn_name": "亚历山德拉小学", 
      "region": "alexandra",
      "vacancy": 180,
      "phase_1": {
        "vacancy": 20,
        "applied": 18,
        "taken": 18
      },
      "phase_2a": {
        "vacancy": 30,
        "applied": 45,
        "taken": 30
      },
      "phase_2b": {
        "vacancy": 25,
        "applied": 40,
        "taken": 25
      },
      "phase_2c": {
        "vacancy": 50,
        "applied": 35,
        "taken": 35
      },
      "phase_2cs": {
        "vacancy": 52,
        "applied": 20,
        "taken": 20
      }
    }
  ],
  "metadata": {
    "crawl_time": "2025-01-15T10:30:00Z",
    "source_url": "https://sgschooling.com/year/2025/primary-school-registration/alexandra/",
    "data_version": "1.0"
  }
}
```

### 全量汇总文件格式 (all_schools.json)

```json
{
  "schools": [
    {
      "name": "Alexandra Primary School",
      "cn_name": "亚历山德拉小学",
      "region": "alexandra",
      "vacancy": 180,
      "phase_1": { "vacancy": 20, "applied": 18, "taken": 18 },
      "phase_2a": { "vacancy": 30, "applied": 45, "taken": 30 },
      "phase_2b": { "vacancy": 25, "applied": 40, "taken": 25 },
      "phase_2c": { "vacancy": 50, "applied": 35, "taken": 35 },
      "phase_2cs": { "vacancy": 52, "applied": 20, "taken": 20 }
    }
  ],
  "metadata": {
    "total_schools": 150,
    "total_vacancy": 27000,
    "total_applied": 35000,
    "total_taken": 25000,
    "crawl_time": "2025-01-15T10:30:00Z",
    "data_version": "1.0"
  }
}
```

### 全量区域汇总文件格式 (all_regions.json)

```json
{
  "regions": [
    {
      "name": "alexandra",
      "cn_name": "亚历山德拉",
      "school_num": 3,
      "vacancy": 540,
      "applied": 420,
      "taken": 385
    }
  ],
  "metadata": {
    "total_regions": 26,
    "total_schools": 150,
    "total_vacancy": 27000,
    "total_applied": 35000,
    "total_taken": 25000,
    "crawl_time": "2025-01-15T10:30:00Z",
    "data_version": "1.0"
  }
}
```

## 数据验证规则

### SchoolData 验证

1. **vacancy 计算验证**：
   ```python
   vacancy == phase_1.taken + phase_2a.taken + phase_2b.taken + phase_2c.taken + phase_2cs.vacancy
   ```

2. **逻辑一致性验证**：
   - `taken <= applied` (每个阶段)
   - `taken <= vacancy` (每个阶段，允许少量超出)
   - 所有数值 >= 0

### RegionData 验证

1. **聚合一致性验证**：
   ```python
   region.vacancy == sum(school.vacancy for school in schools)
   region.applied == sum(school.total_applied for school in schools)
   region.taken == sum(school.total_taken for school in schools)
   region.school_num == len(schools)
   ```

## 使用示例

### 加载学校数据

```python
from primary_rank.models.school_data import SchoolData
import json

# 加载单个学校
with open('data/raw/regions/alexandra.json', 'r') as f:
    data = json.load(f)
    schools = [SchoolData.from_dict(school) for school in data['schools']]

# 验证数据
for school in schools:
    if not school.validate_vacancy():
        print(f"警告：{school.name} 的 vacancy 计算不正确")
```

### 加载区域数据

```python
from primary_rank.models.region_data import RegionData
import json

# 加载区域数据
with open('data/raw/regions/alexandra.json', 'r') as f:
    data = json.load(f)
    region = RegionData.from_dict(data['region'])

print(f"区域：{region.cn_name}")
print(f"学校数量：{region.school_num}")
print(f"竞争比例：{region.competition_ratio:.2f}")
```

## 注意事项

1. **文件编码**：所有JSON文件使用 UTF-8 编码
2. **时间格式**：使用 ISO 8601 格式 (例: "2025-01-15T10:30:00Z")
3. **命名规范**：
   - 区域名称使用小写英文，连字符分隔 (例: "ang-mo-kio")
   - 学校名称保持原始英文格式
4. **数据更新**：每次爬取都生成新的时间戳，保持数据版本可追踪