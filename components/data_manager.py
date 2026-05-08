"""
数据管理后台 - 用于手动更新质量数据
"""
import streamlit as st
import json
from datetime import datetime
import pandas as pd

DATA_FILE = "data/quality_data.json"

def convert_from_serializable(obj):
    """将序列化后的数据转换回原始格式（如DataFrame）"""
    import pandas as pd
    if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
        # 检查是否是DataFrame格式（有month等列）
        if all(col in obj[0] for col in ['month', 'defect_density']):
            return pd.DataFrame(obj)
        # 递归处理列表中的每个元素
        return [convert_from_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_from_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_from_serializable(item) for item in obj]
    return obj

def load_data_from_file():
    """从文件加载数据"""
    import pandas as pd
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # 转换 trend_data 回 DataFrame
        if data and 'quality_work' in data:
            qw = data['quality_work']
            if 'trend_data' in qw and isinstance(qw['trend_data'], list):
                qw['trend_data'] = pd.DataFrame(qw['trend_data'])
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def convert_to_serializable(obj):
    """将对象转换为可JSON序列化的格式"""
    import pandas as pd
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient='records')
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj

def save_data_to_file(data):
    """保存数据到文件"""
    import os
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    # 转换数据中的DataFrame为可序列化格式
    serializable_data = convert_to_serializable(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

def show_data_manager():
    """展示数据管理界面"""
    st.markdown('<div class="section-title">⚙️ 数据管理后台</div>', unsafe_allow_html=True)

    st.info("💡 在此页面可以手动更新各板块的数据，更新后会自动保存到本地文件。")

    # 获取当前数据
    if 'data' not in st.session_state:
        st.error("请先启动应用加载数据")
        return

    data = st.session_state.data

    # 创建标签页
    tabs = st.tabs([
        "📊 年度目标",
        "👥 客户质量",
        "🐛 漏测DI",
        "⚠️ 事故率",
        "🔧 质量改进",
        "💾 数据操作"
    ])

    # ==================== 年度目标 ====================
    with tabs[0]:
        st.subheader("年度目标数据管理")

        qw_data = data.get('quality_work', {})
        annual_goals = qw_data.get('annual_goals', {})
        categories = annual_goals.get('categories', {})

        # 总体达成率
        col1, col2 = st.columns(2)
        with col1:
            new_overall = st.number_input(
                "总体达成率 (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(annual_goals.get('overall_achievement', 90)),
                step=0.1,
                key="annual_overall"
            )
        with col2:
            quarter = st.selectbox(
                "当前季度",
                ["Q1", "Q2", "Q3", "Q4"],
                index=["Q1", "Q2", "Q3", "Q4"].index(annual_goals.get('quarter', 'Q1')),
                key="annual_quarter"
            )

        st.divider()

        # 漏测DI数据
        st.write("**漏测DI数据**")
        base_perf = categories.get('基础业绩', {}).get('items', [])

        di_item = None
        for item in base_perf:
            if item.get('name') == '漏测DI':
                di_item = item
                break

        if di_item:
            targets = di_item.get('targets', [])
            details = di_item.get('details', {})

            cols = st.columns(3)
            with cols[0]:
                shangyong_di = st.number_input(
                    "商用版本漏测DI",
                    min_value=0,
                    value=details.get('比亚迪', {}).get('actual', 194) if isinstance(details.get('比亚迪'), dict) else 194,
                    step=1,
                    key="annual_shangyong_di"
                )
            with cols[1]:
                shangyong_target = st.number_input(
                    "商用版本DI目标",
                    min_value=0,
                    value=217,
                    step=1,
                    key="annual_shangyong_target"
                )
            with cols[2]:
                v5_status = st.selectbox(
                    "V5版本状态",
                    ["暂未发布", "已发布", "开发中"],
                    index=0,
                    key="annual_v5_status"
                )

            # 重点项目DI
            st.write("重点项目DI")
            proj_cols = st.columns(3)
            with proj_cols[0]:
                zhgc_di = st.number_input("ZHGC漏测DI", min_value=0, value=11, step=1, key="annual_zhgc_di")
            with proj_cols[1]:
                byd_di = st.number_input("比亚迪漏测DI", min_value=0, value=21, step=1, key="annual_byd_di")
            with proj_cols[2]:
                cxc_di = st.number_input("长江存储漏测DI", min_value=0, value=7, step=1, key="annual_cxc_di")

        st.divider()

        # 事故率数据
        st.write("**事故率数据**")
        accident_item = None
        for item in base_perf:
            if item.get('name') == '事故率':
                accident_item = item
                break

        if accident_item:
            acc_cols = st.columns(4)
            with acc_cols[0]:
                downtime = st.number_input("业务停机时长(分钟)", min_value=0, value=2, step=1, key="annual_downtime")
            with acc_cols[1]:
                reliability_fail = st.number_input("可靠性不达标套数", min_value=0, value=0, step=1, key="annual_reliability_fail")
            with acc_cols[2]:
                total_systems = st.number_input("G100上线套数", min_value=0, value=3545, step=1, key="annual_total_systems")
            with acc_cols[3]:
                cutover_systems = st.number_input("割接套数", min_value=0, value=155, step=1, key="annual_cutover_systems")

        if st.button("💾 保存年度目标数据", type="primary", use_container_width=True, key="btn_save_annual"):
            # 更新数据
            annual_goals['overall_achievement'] = new_overall
            annual_goals['quarter'] = quarter

            if di_item:
                # 更新目标
                for t in targets:
                    if '商用版本' in t.get('name', ''):
                        t['actual'] = shangyong_di
                # 更新详情
                if 'details' not in di_item:
                    di_item['details'] = {}
                di_item['details']['比亚迪'] = {'actual': byd_di, 'target': '≤100', 'status': '✅ 达标' if byd_di <= 100 else '❌ 超标'}
                di_item['details']['长江存储'] = {'actual': cxc_di, 'target': '<145', 'status': '✅ 达标' if cxc_di < 145 else '❌ 超标'}
                di_item['details']['ZHGC'] = {'actual': zhgc_di, 'target': '≤50', 'status': '✅ 达标' if zhgc_di <= 50 else '❌ 超标'}

            if accident_item:
                accident_item['note'] = f'停机{downtime}分钟为比亚迪2例E100旧版本宕机问题'
                if 'systems' not in accident_item:
                    accident_item['systems'] = {}
                accident_item['systems']['上线'] = total_systems
                accident_item['systems']['割接'] = cutover_systems

            # 同步更新漏测DI和事故率数据
            qw_data['defect_escape']['current_di'] = shangyong_di
            qw_data['defect_escape']['target_di'] = shangyong_target
            qw_data['defect_escape']['project_di'] = {
                '比亚迪': {'actual': byd_di, 'target': 100, 'status': '✅ 达标' if byd_di <= 100 else '❌ 超标'},
                '长江存储': {'actual': cxc_di, 'target': 145, 'status': '✅ 达标' if cxc_di < 145 else '❌ 超标'},
                'ZHGC': {'actual': zhgc_di, 'target': 50, 'status': '✅ 达标' if zhgc_di <= 50 else '❌ 超标'}
            }

            qw_data['accident_rate']['downtime_minutes'] = downtime
            qw_data['accident_rate']['reliability_fail'] = reliability_fail
            qw_data['accident_rate']['total_systems'] = total_systems
            qw_data['accident_rate']['cutover_systems'] = cutover_systems

            save_data_to_file(st.session_state.data)
            st.success("✅ 年度目标数据已保存！")
            st.rerun()

    # ==================== 客户质量 ====================
    with tabs[1]:
        st.subheader("重点客户质量数据管理")

        qw_data = data.get('quality_work', {})
        customer_quality = qw_data.get('customer_quality', {})
        customers = customer_quality.get('customers', [])

        st.write("**客户质量评分 (0-100)**")

        updated_customers = []
        for i, customer in enumerate(customers):
            st.write(f"---")
            cols = st.columns(4)
            with cols[0]:
                name = st.text_input(f"客户名称 {i+1}", value=customer.get('name', ''), key=f"cust_name_{i}")
            with cols[1]:
                score = st.number_input(f"质量评分 {i+1}", min_value=0, max_value=100,
                                       value=customer.get('score', 90), key=f"cust_score_{i}")
            with cols[2]:
                issues = st.number_input(f"本月问题数 {i+1}", min_value=0,
                                        value=customer.get('issues', 0), key=f"cust_issues_{i}")
            with cols[3]:
                trend = st.selectbox(f"趋势 {i+1}", ["up", "stable", "down"],
                                    index=["up", "stable", "down"].index(customer.get('trend', 'stable')),
                                    key=f"cust_trend_{i}")

            # DI数据
            di_cols = st.columns(3)
            with di_cols[0]:
                di = st.number_input(f"漏测DI {i+1}", min_value=0,
                                    value=customer.get('di', 0), key=f"cust_di_{i}")
            with di_cols[1]:
                di_target = st.text_input(f"DI目标 {i+1}", value=customer.get('di_target', ''),
                                         key=f"cust_di_target_{i}")
            with di_cols[2]:
                di_status = st.text_input(f"DI状态 {i+1}", value=customer.get('di_status', ''),
                                         key=f"cust_di_status_{i}")

            updated_customers.append({
                'name': name,
                'score': score,
                'issues': issues,
                'trend': trend,
                'di': di,
                'di_target': di_target,
                'di_status': di_status
            })

        if st.button("💾 保存客户质量数据", type="primary", use_container_width=True, key="btn_save_customer"):
            customer_quality['customers'] = updated_customers
            # 重新计算平均分
            if updated_customers:
                avg_score = sum(c['score'] for c in updated_customers) / len(updated_customers)
                customer_quality['avg_score'] = round(avg_score, 1)

            save_data_to_file(st.session_state.data)
            st.success("✅ 客户质量数据已保存！")
            st.rerun()

    # ==================== 漏测DI ====================
    with tabs[2]:
        st.subheader("漏测DI详细数据管理")

        qw_data = data.get('quality_work', {})
        defect_escape = qw_data.get('defect_escape', {})
        business_lines = defect_escape.get('business_lines', {})

        # 统计日期和自动计算
        st.write("**📅 统计设置**")
        col_date, col_info = st.columns([1, 3])

        with col_date:
            stats_date = st.date_input(
                "统计日期",
                value=datetime.strptime(defect_escape.get('as_of_date', '2026-04-08'), '%Y-%m-%d').date() if 'as_of_date' in defect_escape else datetime(2026, 4, 8).date(),
                key="di_stats_date"
            )

        # 自动计算预期DI（日期占全年的比例）
        year_start = datetime(stats_date.year, 1, 1).date()
        year_end = datetime(stats_date.year, 12, 31).date()
        days_passed = (stats_date - year_start).days + 1
        total_days = (year_end - year_start).days + 1
        progress_ratio = days_passed / total_days

        with col_info:
            st.info(f"📊 年度进度: {days_passed}/{total_days}天 = **{progress_ratio:.1%}** | 预期DI = 目标 × {progress_ratio:.1%}")

        st.divider()

        # 总体数据 - 只有当前DI可编辑
        st.write("**📈 总体数据**")

        # 获取固定目标
        total_target = 870  # 年度固定目标

        # 计算预期值
        total_expected = round(total_target * progress_ratio, 1)

        # 当前DI（唯一可编辑）
        current_di = st.number_input(
            "当前漏测DI（手动填写）",
            min_value=0.0,
            value=float(defect_escape.get('current_di', 194)),
            step=0.1,
            key="di_current",
            help="根据表格填写的当前实际DI值"
        )

        # 自动计算的指标
        cols = st.columns(4)
        with cols[0]:
            st.metric("年度目标（固定）", f"{total_target}")
        with cols[1]:
            st.metric(f"预期DI（{progress_ratio:.1%}）", f"{total_expected:.1f}")
        with cols[2]:
            achievement_rate = round((current_di / total_expected * 100), 1) if total_expected > 0 else 0
            st.metric("达成率", f"{achievement_rate}%", delta=f"{'达标' if achievement_rate <= 100 else '超标'}")
        with cols[3]:
            variance = round(current_di - total_expected, 1)
            st.metric("偏差", f"{variance:+.1f}", delta=f"{variance/total_expected*100:+.1f}%" if total_expected > 0 else "N/A")

        st.divider()

        # 各业务线数据 - 只填写实际DI，其他自动计算
        st.write("**📊 各业务线数据**")

        # 汇总数据
        all_lines_data = []

        # G100老版本内核
        with st.expander("📊 G100老版本内核", expanded=True):
            g100 = business_lines.get('G100老版本内核', {})
            g100_target = 870  # 固定目标
            g100_expected = round(g100_target * progress_ratio, 1)

            # 展示固定和自动计算的指标
            g100_cols = st.columns(4)
            with g100_cols[0]:
                st.markdown(f"**目标: {g100_target}** <span style='color:gray'>(固定)</span>", unsafe_allow_html=True)
            with g100_cols[1]:
                st.markdown(f"**预期: {g100_expected:.1f}** <span style='color:green'>(自动计算)</span>", unsafe_allow_html=True)
            with g100_cols[2]:
                # 实际DI会在下方自动计算后显示
                st.markdown("**实际DI** <span style='color:blue'>(自动合计)</span>", unsafe_allow_html=True)
                st.caption("填写下方各单元后自动计算")
            with g100_cols[3]:
                st.markdown("**偏差/状态**")

            # 子单元 - 只编辑实际值
            st.write("**作战单元明细:**")
            sub_units = g100.get('sub_units', [])
            updated_sub_units = []

            # 表头
            header_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
            header_cols[0].markdown("**作战单元**")
            header_cols[1].markdown("**Owner**")
            header_cols[2].markdown("**目标(固定)**")
            header_cols[3].markdown("**预期(自动)**")
            header_cols[4].markdown("**实际(必填)**")
            header_cols[5].markdown("**偏差/达成率**")

            # 先收集所有子单元的实际值
            sub_unit_actuals = []

            for i, unit in enumerate(sub_units):
                unit_target = unit.get('target', 0)  # 固定
                unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0  # 自动

                unit_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
                with unit_cols[0]:
                    st.markdown(f"{unit.get('name', '')}")
                with unit_cols[1]:
                    st.markdown(f"{unit.get('owner', '')}")
                with unit_cols[2]:
                    st.markdown(f"<span style='color:gray'>{unit_target}</span>", unsafe_allow_html=True)
                with unit_cols[3]:
                    st.markdown(f"<span style='color:green'>{unit_expected:.1f}</span>", unsafe_allow_html=True)
                with unit_cols[4]:
                    unit_actual = st.number_input(
                        f"实际_{i}",
                        min_value=0.0,
                        value=float(unit.get('actual', 0)),
                        step=0.1,
                        key=f"di_g100_unit_actual_{i}",
                        label_visibility="collapsed"
                    )
                with unit_cols[5]:
                    unit_variance = round(unit_actual - unit_expected, 1)
                    # 漏测DI越低越好
                    if unit_expected == 0:
                        # 预期为0时，只要有实际值就算超标
                        if unit_actual > 0:
                            status = "<span style='color:orange'>⚠️ 有漏测</span>"
                        else:
                            status = "<span style='color:green'>✅ 无漏测</span>"
                        variance_str = f"{unit_variance:+.1f}"
                    elif unit_actual <= unit_expected:
                        status = "<span style='color:green'>✅ 达标</span>"
                        variance_str = f"{unit_variance:+.1f}"
                    else:
                        over_pct = round((unit_actual - unit_expected) / unit_expected * 100, 0)
                        status = f"<span style='color:red'>❌ 超标{over_pct:.0f}%</span>"
                        variance_str = f"{unit_variance:+.1f}"
                    st.markdown(f"**{variance_str}** | {status}", unsafe_allow_html=True)

                updated_sub_units.append({
                    'name': unit.get('name', ''),
                    'owner': unit.get('owner', ''),
                    'target': unit_target,
                    'expected': unit_expected,
                    'actual': unit_actual,
                    'variance': variance_str
                })

            # 自动计算G100实际DI（各子单元之和）
            g100_actual = sum(u['actual'] for u in updated_sub_units)
            g100_variance = round(g100_actual - g100_expected, 1)

            # 漏测DI越低越好：实际<=预期为达标，实际>预期为超标
            if g100_expected == 0:
                # 预期为0的情况（如年初第一天）
                if g100_actual > 0:
                    g100_status = f"<span style='color:orange'>⚠️ 有漏测 ({g100_actual:.1f})</span>"
                else:
                    g100_status = f"<span style='color:green'>✅ 无漏测</span>"
            elif g100_actual <= g100_expected:
                g100_status = f"<span style='color:green'>✅ 达标 (低于预期{abs(g100_variance):.1f})</span>"
            else:
                over_pct = round((g100_actual - g100_expected) / g100_expected * 100, 0) if g100_expected > 0 else 0
                g100_status = f"<span style='color:red'>❌ 超标{over_pct:.0f}%</span>"

            # 显示合计行
            st.divider()
            total_cols = st.columns(4)
            with total_cols[0]:
                st.markdown(f"**合计目标: {g100_target}**")
            with total_cols[1]:
                st.markdown(f"**合计预期: {g100_expected:.1f}**")
            with total_cols[2]:
                st.markdown(f"**<span style='color:blue'>合计实际: {g100_actual:.1f}</span>**", unsafe_allow_html=True)
            with total_cols[3]:
                st.markdown(f"**偏差: {g100_variance:+.1f} | {g100_status}**", unsafe_allow_html=True)

        # 重点项目
        with st.expander("📊 重点项目", expanded=True):
            key_projects = business_lines.get('重点项目', {})
            proj_units = key_projects.get('sub_units', [])
            updated_proj_units = []

            # 表头
            header_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
            header_cols[0].markdown("**项目**")
            header_cols[1].markdown("**Owner**")
            header_cols[2].markdown("**目标(固定)**")
            header_cols[3].markdown("**预期(自动)**")
            header_cols[4].markdown("**实际(必填)**")
            header_cols[5].markdown("**偏差/达成率**")

            for i, unit in enumerate(proj_units):
                proj_target = unit.get('target', 0)
                proj_expected = round(proj_target * progress_ratio, 1) if proj_target > 0 else 0

                proj_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
                with proj_cols[0]:
                    st.markdown(f"{unit.get('name', '')}")
                with proj_cols[1]:
                    st.markdown(f"{unit.get('owner', '')}")
                with proj_cols[2]:
                    st.markdown(f"<span style='color:gray'>{proj_target}</span>", unsafe_allow_html=True)
                with proj_cols[3]:
                    st.markdown(f"<span style='color:green'>{proj_expected:.1f}</span>", unsafe_allow_html=True)
                with proj_cols[4]:
                    proj_actual = st.number_input(
                        f"实际_项目_{i}",
                        min_value=0.0,
                        value=float(unit.get('actual', 0)),
                        step=0.1,
                        key=f"di_proj_actual_{i}",
                        label_visibility="collapsed"
                    )
                with proj_cols[5]:
                    proj_variance = round(proj_actual - proj_expected, 1)
                    proj_rate = round((proj_actual / proj_expected * 100), 0) if proj_expected > 0 else 0
                    proj_variance_pct = round(proj_variance / proj_expected * 100, 0) if proj_expected > 0 else 0
                    variance_str = f"{proj_variance:+.1f}({proj_variance_pct:+.0f}%)"
                    st.markdown(f"**{variance_str}** | {proj_rate:.0f}%")

                updated_proj_units.append({
                    'name': unit.get('name', ''),
                    'owner': unit.get('owner', ''),
                    'target': proj_target,
                    'expected': proj_expected,
                    'actual': proj_actual,
                    'variance': variance_str
                })

        # 测试部门 - 自动从内核算出
        with st.expander("📊 测试 (自动计算)", expanded=True):
            st.info("💡 测试部门的值自动从内核算出，无需手动填写")

            # 从内核算出测试值
            # 获取内核各单元的实际值
            kernel_values = {u.get('name', ''): u.get('actual', 0) for u in updated_sub_units}

            # 1. 内核测试 = SQL引擎 + 存储引擎 + PLSQL + 驱动 + CMCC内核
            kernel_test_actual = (
                kernel_values.get('SQL引擎', 0) +
                kernel_values.get('存储引擎', 0) +
                kernel_values.get('PLSQL', 0) +
                kernel_values.get('驱动', 0) +
                kernel_values.get('CMCC内核', 0)
            )

            # 2. 迁移工具测试 = 迁移工具 + DTP
            migrate_test_actual = (
                kernel_values.get('迁移工具', 0) +
                kernel_values.get('DTP', 0)
            )

            # 3. 运维工具测试 = 运维管理工具 + DBOPS
            ops_test_actual = (
                kernel_values.get('运维管理工具', 0) +
                kernel_values.get('DBOPS', 0)
            )

            # 测试部门配置（目标固定，实际自动计算）
            test_configs = [
                {'name': '内核测试', 'owner': '崔响灵、苏动', 'target': 615, 'actual': kernel_test_actual},
                {'name': '迁移工具测试', 'owner': '梁佳琪', 'target': 170, 'actual': migrate_test_actual},
                {'name': '运维工具测试', 'owner': '熊卉', 'target': 85, 'actual': ops_test_actual},
            ]

            updated_test_units = []

            # 表头
            header_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
            header_cols[0].markdown("**单元**")
            header_cols[1].markdown("**Owner**")
            header_cols[2].markdown("**目标(固定)**")
            header_cols[3].markdown("**预期(自动)**")
            header_cols[4].markdown("**实际(自动)**")
            header_cols[5].markdown("**偏差/达成率**")

            for config in test_configs:
                test_target = config['target']
                test_expected = round(test_target * progress_ratio, 1) if test_target > 0 else 0
                test_actual = config['actual']

                test_cols = st.columns([2, 2, 1.5, 1.5, 1.5, 2])
                with test_cols[0]:
                    st.markdown(f"**{config['name']}**")
                with test_cols[1]:
                    st.markdown(f"{config['owner']}")
                with test_cols[2]:
                    st.markdown(f"<span style='color:gray'>{test_target}</span>", unsafe_allow_html=True)
                with test_cols[3]:
                    st.markdown(f"<span style='color:green'>{test_expected:.1f}</span>", unsafe_allow_html=True)
                with test_cols[4]:
                    st.markdown(f"<span style='color:blue'><b>{test_actual:.1f}</b></span>", unsafe_allow_html=True)
                with test_cols[5]:
                    test_variance = round(test_actual - test_expected, 1)
                    # 漏测DI越低越好
                    if test_expected == 0:
                        # 预期为0时，只要有实际值就算超标
                        if test_actual > 0:
                            status = "<span style='color:orange'>⚠️ 有漏测</span>"
                        else:
                            status = "<span style='color:green'>✅ 无漏测</span>"
                        variance_str = f"{test_variance:+.1f}"
                    elif test_actual <= test_expected:
                        status = "<span style='color:green'>✅ 达标</span>"
                        variance_str = f"{test_variance:+.1f}"
                    else:
                        over_pct = round((test_actual - test_expected) / test_expected * 100, 0)
                        status = f"<span style='color:red'>❌ 超标{over_pct:.0f}%</span>"
                        variance_str = f"{test_variance:+.1f}"
                    st.markdown(f"**{variance_str}** | {status}", unsafe_allow_html=True)

                updated_test_units.append({
                    'name': config['name'],
                    'owner': config['owner'],
                    'target': test_target,
                    'expected': test_expected,
                    'actual': test_actual,
                    'variance': variance_str
                })

            st.caption("计算公式：")
            st.caption("• 内核测试 = SQL引擎 + 存储引擎 + PLSQL + 驱动 + CMCC内核")
            st.caption("• 迁移工具测试 = 迁移工具 + DTP")
            st.caption("• 运维工具测试 = 运维管理工具 + DBOPS")

        # V5版本（预留，未上线）
        with st.expander("📊 G100 V5版本（未上线）", expanded=False):
            v5 = business_lines.get('G100_V5版本', {})

            v5_cols = st.columns(4)
            with v5_cols[0]:
                st.markdown(f"**目标: 189** <span style='color:gray'>(固定)</span>", unsafe_allow_html=True)
            with v5_cols[1]:
                st.markdown(f"**预期: 0** <span style='color:green'>(自动)</span>", unsafe_allow_html=True)
            with v5_cols[2]:
                st.markdown(f"**实际: 0** <span style='color:blue'>(未上线)</span>", unsafe_allow_html=True)
            with v5_cols[3]:
                st.markdown(f"**Owner: 陈炳达**")

            st.info("💡 V5版本暂未上线，无漏测数据")

        # 维优部（研发体系整体）
        with st.expander("📊 维优部（研发体系整体）", expanded=True):
            weiyou = business_lines.get('维优部', {})

            weiyou_cols = st.columns(4)
            with weiyou_cols[0]:
                st.markdown(f"**目标: 870** <span style='color:gray'>(固定)</span>", unsafe_allow_html=True)
            with weiyou_cols[1]:
                weiyou_expected = round(870 * progress_ratio, 1)
                st.markdown(f"**预期: {weiyou_expected:.1f}** <span style='color:green'>(自动)</span>", unsafe_allow_html=True)
            with weiyou_cols[2]:
                # 维优部的实际值 = G100老版本内核的实际值，保留1位小数
                st.markdown(f"**实际: {g100_actual:.1f}** <span style='color:blue'>(研发体系)</span>", unsafe_allow_html=True)
            with weiyou_cols[3]:
                st.markdown(f"**Owner: 陈建华**")

            # 漏测DI越低越好：实际<=预期为达标
            weiyou_variance = round(g100_actual - weiyou_expected, 1)
            if weiyou_expected == 0:
                # 预期为0的情况（如年初第一天）
                if g100_actual > 0:
                    st.warning(f"⚠️ 研发体系整体漏测DI: **{g100_actual:.1f}** (实际值，预期为0)")
                else:
                    st.success(f"✅ 研发体系整体漏测DI: 无漏测")
            elif g100_actual <= weiyou_expected:
                st.success(f"✅ 研发体系整体漏测DI: **{g100_actual:.1f}** / {weiyou_expected:.1f} (预期) | 低于预期 {abs(weiyou_variance):.1f} (优秀)")
            else:
                over_pct = round((g100_actual - weiyou_expected) / weiyou_expected * 100, 0) if weiyou_expected > 0 else 0
                st.error(f"❌ 研发体系整体漏测DI: **{g100_actual:.1f}** / {weiyou_expected:.1f} (预期) | 超标 {over_pct}%")

        st.divider()

        if st.button("💾 保存漏测DI数据", type="primary", use_container_width=True, key="btn_save_di"):
            # 保存统计数据
            defect_escape['as_of_date'] = stats_date.strftime('%Y-%m-%d')
            defect_escape['current_di'] = current_di
            defect_escape['target_di'] = total_target
            defect_escape['expected_di'] = total_expected
            defect_escape['achievement_rate'] = f"{achievement_rate}%"

            # 更新业务线数据
            if 'business_lines' not in defect_escape:
                defect_escape['business_lines'] = {}

            # G100老版本内核
            g100_variance_total = round(g100_actual - g100_expected, 1)
            g100_rate_total = round((g100_actual / g100_expected * 100), 0) if g100_expected > 0 else 0
            if 'G100老版本内核' not in defect_escape['business_lines']:
                defect_escape['business_lines']['G100老版本内核'] = {}
            defect_escape['business_lines']['G100老版本内核'].update({
                'total_target': 870,
                'total_expected': g100_expected,
                'total_actual': g100_actual,
                'owner': '陈炳达',
                'achievement_rate': f"{g100_rate_total}%",
                'sub_units': updated_sub_units
            })

            # 重点项目
            if '重点项目' not in defect_escape['business_lines']:
                defect_escape['business_lines']['重点项目'] = {}
            defect_escape['business_lines']['重点项目']['sub_units'] = updated_proj_units

            # 测试
            test_actual_total = sum(u['actual'] for u in updated_test_units)
            test_expected_total = sum(u['expected'] for u in updated_test_units)
            test_rate_total = round((test_actual_total / test_expected_total * 100), 0) if test_expected_total > 0 else 0
            if '测试' not in defect_escape['business_lines']:
                defect_escape['business_lines']['测试'] = {}
            defect_escape['business_lines']['测试'].update({
                'total_target': 870,
                'total_expected': test_expected_total,
                'total_actual': test_actual_total,
                'owner': '郭琦',
                'achievement_rate': f"{test_rate_total}%",
                'sub_units': updated_test_units
            })

            # V5版本（预留）
            if 'G100_V5版本' not in defect_escape['business_lines']:
                defect_escape['business_lines']['G100_V5版本'] = {}
            defect_escape['business_lines']['G100_V5版本'].update({
                'total_target': 189,
                'total_expected': 0,
                'total_actual': 0,
                'owner': '陈炳达',
                'achievement_rate': '100%',
                'sub_units': []
            })

            # 维优部（研发体系整体）
            weiyou_expected = round(870 * progress_ratio, 1)
            weiyou_actual = g100_actual
            weiyou_rate = round((weiyou_actual / weiyou_expected * 100), 0) if weiyou_expected > 0 else 0
            if '维优部' not in defect_escape['business_lines']:
                defect_escape['business_lines']['维优部'] = {}
            defect_escape['business_lines']['维优部'].update({
                'total_target': 870,
                'total_expected': weiyou_expected,
                'total_actual': weiyou_actual,
                'owner': '陈建华',
                'achievement_rate': f"{weiyou_rate}%",
                'sub_units': [
                    {'name': '研发体系', 'owner': '陈建华', 'target': 870, 'expected': weiyou_expected, 'actual': weiyou_actual, 'variance': f"{round(weiyou_actual - weiyou_expected, 1):+.1f}"}
                ]
            })

            # 更新project_di
            defect_escape['project_di'] = {
                '比亚迪': {
                    'actual': next((u['actual'] for u in updated_proj_units if u['name'] == '比亚迪'), 21.1),
                    'target': next((u['target'] for u in updated_proj_units if u['name'] == '比亚迪'), 110),
                    'expected': next((u['expected'] for u in updated_proj_units if u['name'] == '比亚迪'), 30),
                    'status': '✅ 达标' if next((u['actual'] for u in updated_proj_units if u['name'] == '比亚迪'), 21.1) <= 110 else '❌ 超标',
                    'variance': next((u['variance'] for u in updated_proj_units if u['name'] == '比亚迪'), '-29%')
                },
                '长江存储': {
                    'actual': next((u['actual'] for u in updated_proj_units if u['name'] == '长江存储'), 8),
                    'target': next((u['target'] for u in updated_proj_units if u['name'] == '长江存储'), 145),
                    'expected': next((u['expected'] for u in updated_proj_units if u['name'] == '长江存储'), 40),
                    'status': '✅ 达标' if next((u['actual'] for u in updated_proj_units if u['name'] == '长江存储'), 8) < 145 else '❌ 超标',
                    'variance': next((u['variance'] for u in updated_proj_units if u['name'] == '长江存储'), '-80%')
                },
                'ZHGC试点': {
                    'actual': next((u['actual'] for u in updated_proj_units if u['name'] == 'ZHGC试点'), 11.1),
                    'target': next((u['target'] for u in updated_proj_units if u['name'] == 'ZHGC试点'), 50),
                    'expected': next((u['expected'] for u in updated_proj_units if u['name'] == 'ZHGC试点'), 13),
                    'status': '✅ 达标' if next((u['actual'] for u in updated_proj_units if u['name'] == 'ZHGC试点'), 11.1) <= 50 else '❌ 超标',
                    'variance': next((u['variance'] for u in updated_proj_units if u['name'] == 'ZHGC试点'), '-17%')
                }
            }

            save_data_to_file(st.session_state.data)
            st.success("✅ 漏测DI数据已保存！")
            st.rerun()

    # ==================== 事故率 ====================
    with tabs[3]:
        st.subheader("事故率数据管理")

        qw_data = data.get('quality_work', {})
        accident_rate = qw_data.get('accident_rate', {})

        cols = st.columns(4)
        with cols[0]:
            downtime = st.number_input("业务停机时长(分钟)", min_value=0,
                                      value=accident_rate.get('downtime_minutes', 2), step=1, key="acc_downtime")
        with cols[1]:
            reliability_fail = st.number_input("可靠性不达标套数", min_value=0,
                                              value=accident_rate.get('reliability_fail', 0), step=1, key="acc_reliability")
        with cols[2]:
            total_systems = st.number_input("G100上线套数", min_value=0,
                                           value=accident_rate.get('total_systems', 3545), step=1, key="acc_systems")
        with cols[3]:
            cutover_systems = st.number_input("割接套数", min_value=0,
                                             value=accident_rate.get('cutover_systems', 155), step=1, key="acc_cutover")

        st.write("**事故等级分布**")
        severity = accident_rate.get('severity_dist', {})
        sev_cols = st.columns(4)
        updated_severity = {}
        levels = ['P0', 'P1', 'P2', 'P3']
        for i, level in enumerate(levels):
            with sev_cols[i]:
                val = st.number_input(f"{level}级事故", min_value=0,
                                     value=severity.get(level, 0), step=1, key=f"acc_sev_{level}")
                updated_severity[level] = val

        note = st.text_area("说明文字", value=accident_rate.get('note', ''), height=80, key="acc_note")

        if st.button("💾 保存事故率数据", type="primary", use_container_width=True, key="btn_save_accident"):
            accident_rate['downtime_minutes'] = downtime
            accident_rate['reliability_fail'] = reliability_fail
            accident_rate['total_systems'] = total_systems
            accident_rate['cutover_systems'] = cutover_systems
            accident_rate['severity_dist'] = updated_severity
            accident_rate['note'] = note
            accident_rate['accidents_this_month'] = sum(updated_severity.values())
            accident_rate['accidents_ytd'] = sum(updated_severity.values())

            save_data_to_file(st.session_state.data)
            st.success("✅ 事故率数据已保存！")
            st.rerun()

    # ==================== 质量改进 ====================
    with tabs[4]:
        st.subheader("质量改进任务进度管理")

        qi_data = data.get('quality_improvement', {})
        ongoing_tasks = qi_data.get('ongoing_tasks', [])

        st.write("**进行中的任务**")

        updated_tasks = []
        for i, task in enumerate(ongoing_tasks):
            with st.expander(f"📋 {task.get('name', '未命名任务')}", expanded=False):
                name = st.text_input("任务名称", value=task.get('name', ''),
                                   key=f"task_name_{i}")
                owner = st.text_input("负责人", value=task.get('owner', ''),
                                     key=f"task_owner_{i}")
                progress = st.slider("进度 (%)", min_value=0, max_value=100,
                                   value=task.get('progress', 0),
                                   key=f"task_progress_{i}")
                due = st.text_input("截止日期", value=task.get('due', ''),
                                   key=f"task_due_{i}")
                desc = st.text_area("描述", value=task.get('desc', ''),
                                   key=f"task_desc_{i}", height=80)

                updated_tasks.append({
                    'name': name,
                    'owner': owner,
                    'progress': progress,
                    'due': due,
                    'desc': desc
                })

        if st.button("💾 保存质量改进数据", type="primary", use_container_width=True, key="btn_save_qi"):
            qi_data['ongoing_tasks'] = updated_tasks
            save_data_to_file(st.session_state.data)
            st.success("✅ 质量改进数据已保存！")
            st.rerun()

    # ==================== 数据操作 ====================
    with tabs[5]:
        st.subheader("数据导入/导出")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**导出数据**")
            if st.button("📥 下载当前数据为JSON", use_container_width=True, key="btn_export"):
                json_str = json.dumps(st.session_state.data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="点击下载",
                    data=json_str,
                    file_name=f"quality_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

        with col2:
            st.write("**导入数据**")
            uploaded_file = st.file_uploader("选择JSON文件", type=['json'], key="file_import")
            if uploaded_file is not None:
                try:
                    imported_data = json.load(uploaded_file)
                    if st.button("📤 导入数据", use_container_width=True, key="btn_import"):
                        st.session_state.data = imported_data
                        save_data_to_file(imported_data)
                        st.success("✅ 数据导入成功！")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("❌ 无效的JSON文件")

        st.divider()

        st.write("**重置数据**")
        if st.button("🔄 重置为默认数据", use_container_width=True, key="btn_reset"):
            if 'data' in st.session_state:
                del st.session_state.data
            save_data_to_file({})
            st.warning("⚠️ 数据已重置，请刷新页面重新加载")
            st.rerun()
