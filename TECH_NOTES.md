# 技术说明文档

## 现网问题模块设计决策

### 数据导入

1. **行分割方式**
   - 使用 `\n` 分割行，`\t` 分割列
   - 不处理单元格内的换行（直接切割，保留第一行）
   - 适用于Excel复制粘贴的制表符分隔数据

2. **合并单元格处理**
   - 产品线为空时继承上一行
   - 问题分类为空时继承上一行
   - 解决Excel中合并单元格导致的空值问题

3. **数据去重**
   - 导入新数据时先清除该周旧数据
   - 避免同一周数据重复累积

### 字段选项

1. **问题分类选项**
   - 重点客户问题
   - 非重点客户严重问题
   - 非重点客户一般问题
   - 一般问题
   - 内部问题

2. **环境选项**
   - 生产、生产环境
   - 准生产
   - 测试
   - POC、poc
   - 生态适配、适配
   - 未知

### 举一反三录入

1. **缺陷选择方式**
   - 支持问题单号搜索过滤
   - 下拉列表显示：问题单号 | 客户名称 | 问题描述
   - 显示所有缺陷（不仅限于勾选举一反三的）

2. **数据存储**
   - 存储字段：defect_id（缺陷ID）、source（来源客户）、action（改进行动）、scope（影响范围）、status（状态）、progress（进度）、owner（负责人）、deadline（截止日期）

## 周次格式规范

- 统一使用 `Wxx` 格式
- 示例：W1, W2, W18, W7&8
- 已清理历史数据中的 `2026-Wxx` 格式

## 数据文件

- 本地路径：`data/quality_data.json`
- 已被 `.gitignore` 排除，需手动提交

## 客户质量数据自动刷新机制

### 数据来源

客户质量模块的数据自动从以下三个数据源实时计算：

1. **漏测DI数据**
   - 来源：`defect_escape['project_di']`
   - 字段：`di`（实际值）、`di_target`（目标值）、`di_status`（状态）

2. **现网问题数**
   - 来源：`production_issues['issues']`
   - 按客户名称统计问题数量

3. **事故数**
   - 来源：`accident_rate['accidents']`
   - 按客户名称统计事故数量

### 客户名称映射

用于匹配不同数据源中的客户名称变体：

```python
customer_mapping = {
    'zhgc': ['zhgc', 'ZHGC'],
    '比亚迪': ['比亚迪', 'BYD', 'byd'],
    '长江存储': ['长江存储', '长存', 'cxc', 'CXC']
}
```

### 实现位置

- **数据管理后台**: `components/data_manager.py` 第60-145行
- **综合大盘展示**: `components/quality_work.py` 第171-225行

### 刷新逻辑

```python
# 1. 获取各数据源数据
defect_data = data.get('defect_escape', {})
project_di = defect_data.get('project_di', {})
prod_issues = data.get('production_issues', {})
issues_list = prod_issues.get('issues', [])
accident_data = data.get('accident_rate', {})
accidents = accident_data.get('accidents', [])

# 2. 统计每个客户的问题数和事故数
customer_issues_count = {}
for issue in issues_list:
    customer_name = issue.get('客户名称', '')
    # 使用customer_mapping匹配标准名称
    ...

# 3. 刷新客户数据
for customer in customers:
    name = customer.get('name', '')
    # 从project_di获取DI数据
    # 从customer_issues_count获取问题数
    # 从customer_accidents_count获取事故数
```

## TOP质量事项进度跟踪设计

### 合并表格设计

1. **统一表格展示**
   - 主项进度和子项进度合并到一个表格中
   - 使用"类型"列区分：主项/子项
   - 子项使用"子项名称"列标识具体内容

2. **列定义**
   - 类型：SelectboxColumn，选项['主项', '子项']
   - 子项名称：TextColumn，主项为空，子项填写名称
   - 日期：TextColumn，支持自动格式转换
   - 进度：TextColumn，如 30%, 50%
   - 状态说明：TextColumn，详细描述
   - 下一步计划：TextColumn
   - 登记人/负责人：TextColumn

3. **数据存储结构**
   - 显示时合并：`all_progress` 列表包含主项和子项
   - 保存时拆分：根据"类型"列分别存入 `progress` 和 `sub_items`

### 日期自动格式化

```python
def normalize_date(date_str):
    """将各种日期格式统一转换为 YYYY-MM-DD"""
    if not date_str or not isinstance(date_str, str):
        return date_str
    import re
    date_str = date_str.strip()
    # 匹配 MM/DD 或 M/D 格式
    match = re.match(r'^(\d{1,2})/(\d{1,2})$', date_str)
    if match:
        month, day = match.groups()
        return f"2026-{int(month):02d}-{int(day):02d}"
    # 匹配 MM-DD 或 M-D 格式
    match = re.match(r'^(\d{1,2})-(\d{1,2})$', date_str)
    if match:
        month, day = match.groups()
        return f"2026-{int(month):02d}-{int(day):02d}"
    # 匹配 YYYY-MM-DD 格式，将2024改为2026
    if date_str.startswith('2024'):
        return '2026' + date_str[4:]
    return date_str
```

### TOP事项编号规则

- 格式：TOP-001, TOP-002, TOP-003, TOP-004
- 起始编号：从1开始（不是0）
- 重新编号条件：仅在ID缺失或重复时执行，避免每次加载都重新分配
- 排除项："事故复盘闭环跟进" 已从TOP事项中移除，改为独立模块

### TOP3名称修正

- 原名：产品需求边界清晰化评估
- 修正为：需求交付质量标准

## 事故级别定义

- **P1**: 紧急事故
- **P2**: 高等级事故
- **P3**: 中等级事故
- **P4**: 低等级事故

注意：事故级别从P1开始，不是P0。

## 质量风险预警规则

### 漏测DI超标检测

1. **作战单元级别**
   - 超标阈值：超过预期值 0.1%
   - 预期DI = 目标DI × 日期比例（今年第几天/365）
   - 展示：最严重的3个超标单元

2. **总体级别**
   - 超标阈值：超过预期值 10%
   - 风险等级：超标>30%为"高"，否则为"中"

### 实现位置

- `main.py` 第470-550行
