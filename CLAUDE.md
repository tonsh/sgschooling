# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PrimaryRank 是一个分析新加坡小学报名数据的项目，通过分析 https://sgschooling.com/year/2025/ 的2025年新加坡小学报名数据，统计新加坡所有政府小学及区域的热度排名，为家长择校提供有价值的参数依据。

抓取后的结果可以与 https://sgschooling.com/year/2025/all 页面的数据进行校验。

## 项目目标

- 从 https://sgschooling.com/year/2025/ 抓取新加坡政府小学2025年报名数据
- 统计学校热度排名，生成学校热度排名表格
- 统计区域热度排名，生成区域排名表格
- 为家长择校提供有价值的参数依据
- 提供数据校验功能，确保抓取数据准确性

## 开发环境

- **编程语言**: Python 3.12
- **开发容器**: devcontainer配置
- **IDE**: VS Code with Claude Code extension

## 数据结构定义

### SchoolData 学校数据结构
```
SchoolData(
    name: str,              # 学校英文名称
    region: str,            # 所在区域（使用show name格式：region_name.replace('-', ' ').title()）
    phase_1: PhaseData,     # Phase1 阶段数据(Vacancy, Applied, Taken)
    phase_2a: PhaseData,    # 2A 阶段数据(Vacancy, Applied, Taken)
    phase_2b: PhaseData,    # 2B 阶段数据(Vacancy, Applied, Taken)
    phase_2c: PhaseData,    # 2C 阶段数据(Vacancy, Applied, Taken)
    phase_2cs: PhaseData,   # 2Cs 阶段数据(Vacancy, Applied, Taken)
    phase_3: PhaseData      # Phase3 阶段数据(Vacancy, Applied, Taken)
)
```

**重要计算公式：**
- `SchoolData.vacancy = Phase1.taken + 2A.taken + 2B.taken + 2C.taken + 2Cs.taken + phase3.vacancy`（注意：phase3 使用 vacancy 而非 taken）
- `SchoolData.applied = phase1.taken + 2a.taken + 2b.taken + 2c.taken + 2cs.applied`（总申请数）
- `SchoolData.taken = phase1.taken + 2a.taken + 2b.taken + 2c.taken + 2cs.taken`（总录取数）
- `SchoolData.rate = Σ(phase.applied / phase.vacancy)`（热度 = 各阶段申请率之和）
- `SchoolData.remaining = SchoolData.vacancy - SchoolData.taken`（剩余名额）
- `SchoolData.failed = max(SchoolData.applied - SchoolData.vacancy, 0)`（未报名成功人数）

### RegionData 区域数据结构
```
RegionData(
    name: str,              # 区域名称（使用show name格式：region_name.replace('-', ' ').title()）
    school_num: int,        # 该区域学校数量
    vacancy: int,           # 该区域所有学校的总学位数量
    applied: int,           # 该区域所有学校的总报名数量
    taken: int              # 该区域所有学校的总录取数量
)
```

**重要计算公式：**
- `RegionData.remaining = RegionData.vacancy - RegionData.taken`（剩余名额）
- `RegionData.failed = max(RegionData.applied - RegionData.vacancy, 0)`（未报名成功人数）
- `RegionData.rate = RegionData.applied / RegionData.vacancy`（申请率）

## 数据存储格式

原始数据按以上数据结构保存为 JSON 格式到 `/data/raw/regions/` 目录下，每个区域一个 JSON 文件。

## 统计分析流程要求

1. **检查原始数据存在性**：统计阶段要求检查 `/data/raw/regions/` 所有区域原始数据是否已存在
2. **优先使用现有数据**：若已存在统计分析时直接使用原始数据，不要再执行抓取操作
3. **数据校验**：抓取后的结果需要与 https://sgschooling.com/year/2025/all 页面的数据进行校验

## 报告输出要求

总结文档里需要添加以下表格：

### 学校热度排名表格
| 学校 | 区域 | 学位数 | 报名数 | 剩余学位 | 热度 |
|------|------|--------|--------|----------|------|

### 区域排名表格  
| 区域 | 学校数 | 学位数 | 报名数 | 剩余学位 | 申请率 |
|------|--------|--------|--------|----------|--------|

## 开发指南

在开发此数据分析项目时请注意：
1. 确保数据来源的合法性和准确性
2. 实施适当的数据清洗和验证
3. 提供清晰的数据可视化和排名展示
4. 考虑数据更新的时效性
5. 遵守数据使用相关法规
6. 区域名称统一使用 show name 格式（region_name.replace('-', ' ').title()）

## 重要说明

- 你必须用中文在聊天中回复。
- 你必须用中文编写任何文档。
- 尽量小步频繁提交变更
- 项目使用 pyenv 环境
- 每次有重大改动时生成或更新相应文档
- 所有的文档需放在 docs/ 目录下
- 所有的单元测试相关文件或目录需放在 tests/ 目录下
- 去除行尾空格
- 文件末尾有且仅有一个空行
