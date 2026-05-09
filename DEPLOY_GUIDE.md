# 📋 质量可视化平台 - 数据更新与部署指南

## 🔄 完整工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  本地编辑   │ →  │ 提交到GitHub │ →  │ Streamlit   │ →  │  他人访问   │
│  数据       │    │             │    │ 自动更新    │    │  只读页面   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

---

## 1️⃣ 本地启用编辑模式

### 创建本地配置文件

在项目根目录创建 `.streamlit/secrets.toml`：

```toml
# 启用编辑模式
EDIT_MODE = "true"

# TAPD API 配置（可选）
# TAPD_API_USER = "your_api_user"
# TAPD_API_PASSWORD = "your_api_password"
```

> ⚠️ **注意**：`.streamlit/secrets.toml` 已在 `.gitignore` 中，不会提交到 GitHub

---

## 2️⃣ 本地编辑数据

### 启动本地服务

```bash
streamlit run main.py
```

### 访问数据管理后台

1. 浏览器打开 `http://localhost:8501`
2. 侧边栏会显示 **"✏️ 编辑模式"**
3. 选择 **"⚙️ 数据管理"** 板块
4. 在各个标签页更新数据：
   - 📊 年度目标
   - 👥 客户质量
   - 🐛 漏测DI
   - ⚠️ 事故率
   - 🔧 质量改进
   - 🌐 现网问题（见下方详细说明）

### 数据保存位置

- 本地文件：`data/quality_data.json`
- 每次点击 **"💾 保存"** 按钮后会自动保存

---

## 3️⃣ 提交数据到 GitHub

### 方式一：命令行（推荐）

```bash
# 1. 进入项目目录
cd /Users/lmc/Desktop/quality可视化

# 2. 查看变更
git status

# 3. 添加数据文件
git add data/quality_data.json

# 4. 提交变更（写清楚更新内容）
git commit -m "Update: 2025年5月质量数据

- 更新漏测DI数据
- 更新客户质量评分
- 更新事故率统计"

# 5. 推送到 GitHub
git push origin main
```

### 方式二：VS Code 图形界面

1. 打开 VS Code，进入源代码管理（Ctrl+Shift+G）
2. 找到 `data/quality_data.json` 文件，点击 **"+"** 暂存
3. 在消息框输入提交说明，点击 **"✓ 提交"**
4. 点击 **"..." → "推送"**

---

## 4️⃣ Streamlit Cloud 自动更新

### 自动部署

GitHub 推送后，Streamlit Cloud **会在 1-2 分钟内自动重新部署**。

### 查看部署状态

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 点击你的应用
3. 查看右上角状态：
   - 🟢 **Running** - 运行中
   - 🟡 **Spinning up** - 正在启动
   - 🔴 **Error** - 出错（点击查看日志）

### 手动重启（可选）

如果自动部署失败：
1. 点击应用右上角的 **"☰"**
2. 选择 **"Reboot"**
3. 等待重启完成

---

## 🌐 现网问题模块使用说明

### 数据导入流程

1. **批量导入**
   - 从Excel复制数据（支持格式：产品线 | 问题分类 | 客户名称 | 严重程度 | 问题单号 | 环境 | 版本 | 问题描述 | 影响范围 | 状态 | 举一反三）
   - 粘贴到文本框，选择周次（如：W18）
   - 点击"解析并导入"，导入后会自动切换到该周数据

2. **数据处理规则**
   - 产品线为空时继承上一行（处理Excel合并单元格）
   - 问题分类为空时继承上一行
   - 导入新数据时会自动清除该周旧数据，避免重复

3. **周次格式**
   - 统一使用 Wxx 格式（如：W1, W2, W18）
   - 支持双周格式（如：W7&8）

### 举一反三录入

1. **选择缺陷**
   - 在搜索框输入问题单号（缺陷ID）过滤
   - 从下拉列表选择要录入的缺陷

2. **填写信息**
   - 改进行动、影响范围、负责人、截止日期

3. **查看已录入列表**
   - 页面下方显示所有已录入的举一反三
   - 包含统计信息（总任务数、已完成、进行中）

---

## 5️⃣ 验证在线版本

### 访问在线应用

🔗 **访问地址**：https://quality-dashboard-l.streamlit.app

### 验证要点

1. ✅ 侧边栏显示 **"👁️ 只读模式"**
2. ❌ 没有 **"⚙️ 数据管理"** 选项
3. ✅ 数据已更新为你刚才提交的内容
4. ✅ 其他人只能查看，无法编辑

---

## 📝 完整示例流程

```bash
# ===== 步骤 1: 启动本地编辑 =====
cd /Users/lmc/Desktop/quality可视化
streamlit run main.py

# 在浏览器中编辑数据...

# ===== 步骤 2: 提交到 GitHub =====
git add data/quality_data.json
git commit -m "Update: $(date +%Y-%m-%d) 质量数据更新"
git push origin main

# ===== 步骤 3: 等待自动部署 =====
# 打开 https://share.streamlit.io 查看部署状态

# ===== 步骤 4: 验证在线版本 =====
open https://quality-dashboard-l.streamlit.app
```

---

## 🔧 常见问题

### Q1: Streamlit Cloud 没有自动更新？

**可能原因**：
- GitHub 提交没有包含 `data/quality_data.json`
- Streamlit Cloud 部署失败

**解决方法**：
1. 确认文件已提交：`git log --name-only -1`
2. 手动重启：Streamlit Cloud → 应用 → "☰" → "Reboot"

### Q2: 在线版本显示旧数据？

**检查清单**：
- [ ] 本地是否点击了保存按钮？
- [ ] `data/quality_data.json` 是否有更新？
- [ ] GitHub 上文件是否已更新？
- [ ] Streamlit Cloud 是否已重启？

### Q3: 如何在多台电脑编辑？

**方案**：
1. 电脑 A 编辑后提交到 GitHub
2. 电脑 B 先执行 `git pull` 拉取最新数据
3. 电脑 B 编辑后再次提交

### Q4: 数据文件冲突怎么办？

```bash
# 拉取远程最新版本
git pull origin main

# 如果有冲突，保留你的本地版本
git checkout --ours data/quality_data.json
git add data/quality_data.json
git commit -m "Resolve data conflict"
git push origin main
```

---

## 🎯 最佳实践

1. **定期提交**：每周更新数据后立即提交
2. **写清楚提交信息**：方便追溯历史变更
3. **备份数据**：重要更新前先复制一份 `quality_data.json`
4. **测试在线版本**：每次提交后访问在线链接确认正常

---

## 📞 需要帮助？

- Streamlit Cloud 文档：https://docs.streamlit.io/deploy/streamlit-cloud
- Git 教程：https://www.liaoxuefeng.com/wiki/896043488029600
