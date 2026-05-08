"""
数据管理后台 - 使用表格编辑方式
"""
import streamlit as st
import json
from datetime import datetime
import pandas as pd
import plotly.express as px

DATA_FILE = "data/quality_data.json"

def load_data_from_file():
    """从文件加载数据"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def convert_to_serializable(obj):
    """将对象转换为可JSON序列化的格式"""
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
    serializable_data = convert_to_serializable(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_data, f, ensure_ascii=False, indent=2)

def show_data_manager():
    """展示数据管理界面 - 表格编辑版"""
    st.markdown('<div class="section-title">⚙️ 数据管理后台</div>', unsafe_allow_html=True)

    st.info("💡 在表格中直接编辑数据，修改后点击「保存到本地」按钮。")

    if 'data' not in st.session_state:
        st.error("请先启动应用加载数据")
        return

    data = st.session_state.data

    # 创建标签页
    tabs = st.tabs([
        "👥 客户质量",
        "🐛 漏测DI",
        "⚠️ 事故统计",
        "🎯 研发TOP质量事项",
        "🌐 现网问题",
        "💾 保存/导出"
    ])

    # ==================== 客户质量 ====================
    with tabs[0]:
        st.subheader("👥 客户质量数据")
        st.caption("直接在表格中编辑客户名称、评分、问题数等数据")

        qw_data = data.get('quality_work', {})
        customer_quality = qw_data.get('customer_quality', {})
        customers = customer_quality.get('customers', [])

        # 转换为 DataFrame
        df_customers = pd.DataFrame(customers)
        if not df_customers.empty:
            # 定义列配置
            column_config = {
                'name': st.column_config.TextColumn('客户名称', width='medium', required=True),
                'score': st.column_config.NumberColumn('质量评分', min_value=0, max_value=100, step=1, width='small'),
                'issues': st.column_config.NumberColumn('本月问题数', min_value=0, step=1, width='small'),
                'trend': st.column_config.TextColumn('趋势', width='small', help='输入: up/stable/down'),
                'di': st.column_config.NumberColumn('漏测DI', min_value=0, step=0.1, width='small'),
                'di_target': st.column_config.TextColumn('DI目标', width='small'),
                'di_status': st.column_config.TextColumn('DI状态', width='small'),
            }

            edited_df = st.data_editor(
                df_customers,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_customers"
            )

            # 同步更新到数据
            if st.button("💾 保存客户质量数据", type="primary", use_container_width=True):
                customer_quality['customers'] = edited_df.to_dict('records')
                # 重新计算平均分
                if not edited_df.empty:
                    customer_quality['avg_score'] = round(edited_df['score'].mean(), 1)
                st.session_state.data['quality_work']['customer_quality'] = customer_quality
                save_data_to_file(st.session_state.data)
                st.success("✅ 客户质量数据已保存！")
                st.rerun()

    # ==================== 漏测DI ====================
    with tabs[1]:
        st.subheader("🐛 漏测DI明细")
        st.caption("编辑各业务线的漏测DI数据 | 预期DI根据年度目标按时间比例自动计算")

        qw_data = data.get('quality_work', {})
        defect_escape = qw_data.get('defect_escape', {})

        # 总体数据
        st.write("**总体统计**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            target_di = st.number_input("年度目标", value=float(defect_escape.get('target_di', 870)), step=1.0)
        with col2:
            as_of_date = st.date_input("统计日期", value=datetime.strptime(defect_escape.get('as_of_date', '2026-05-06'), '%Y-%m-%d'))
        with col3:
            # 计算日期比例（今年第几天/365）
            from datetime import date
            year_start = date(as_of_date.year, 1, 1)
            day_of_year = (as_of_date - year_start).days + 1
            year_days = 366 if as_of_date.year % 4 == 0 else 365
            progress_ratio = day_of_year / year_days
            expected_total = round(target_di * progress_ratio, 1)
            st.metric("预期DI", f"{expected_total}", f"{day_of_year}/{year_days}天")
        with col4:
            current_di = st.number_input("当前漏测DI", value=float(defect_escape.get('current_di', 0)), step=0.1)

        st.info(f"📅 日期比例: {progress_ratio:.1%} | 预期DI = {target_di} × {progress_ratio:.1%} = {expected_total}")

        # 获取业务线数据
        business_lines = defect_escape.get('business_lines', {})

        # 准备表格数据 - 按照截图结构
        all_rows = []

        # G100老版本内核（含驱动HAS）
        g100_old = business_lines.get('G100老版本内核', {})
        g100_old_units = g100_old.get('sub_units', [])
        g100_old_owner = g100_old.get('owner', '陈炳达')

        # 添加G100老版本内核明细行
        for unit in g100_old_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': 'G100老版本内核（含驱动HAS）',
                '业务Owner': g100_old_owner,
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': f"{unit_expected:.1f}",
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # G100老版本内核小计
        g100_old_total_target = sum(u.get('target', 0) for u in g100_old_units)
        g100_old_total_expected = round(g100_old_total_target * progress_ratio, 1)
        g100_old_total_actual = sum(u.get('actual', 0) for u in g100_old_units)
        all_rows.append({
            '业务': 'G100老版本内核（含驱动HAS）',
            '业务Owner': '',
            '作战单元': '【G100老版本内核漏测合计】',
            'Owner': '',
            '漏测目标': g100_old_total_target,
            '预期漏测DI': f"{g100_old_total_expected:.1f}",
            '当前漏测DI': round(g100_old_total_actual, 1),
            '超标百分比': f"{((g100_old_total_actual - g100_old_total_expected) / g100_old_total_expected * 100):.0f}%" if g100_old_total_expected > 0 else "N/A"
        })

        # G100 V5版本
        g100_v5 = business_lines.get('G100_V5版本', {})
        g100_v5_units = g100_v5.get('sub_units', [])
        if g100_v5_units:
            for unit in g100_v5_units:
                unit_target = unit.get('target', 0)
                unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
                all_rows.append({
                    '业务': 'G100 V5版本',
                    '业务Owner': '',
                    '作战单元': unit.get('name', ''),
                    'Owner': unit.get('owner', ''),
                    '漏测目标': unit_target,
                    '预期漏测DI': f"{unit_expected:.1f}",
                    '当前漏测DI': unit.get('actual', 0),
                    '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
                })

        # 重点项目
        key_projects = business_lines.get('重点项目', {})
        key_units = key_projects.get('sub_units', [])
        for unit in key_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': '重点项目',
                '业务Owner': unit.get('business_owner', ''),
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': f"{unit_expected:.1f}",
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 测试 - 合并功能测试和系统测试为内核测试
        test_units = business_lines.get('测试', {}).get('sub_units', [])

        # 查找功能测试和系统测试并合并
        kernel_test_target = 0
        kernel_test_actual = 0
        other_test_units = []

        for unit in test_units:
            name = unit.get('name', '')
            if name in ['功能测试', '系统测试', '内核测试']:
                # 合并到内核测试
                kernel_test_target += unit.get('target', 0)
                kernel_test_actual += unit.get('actual', 0)
            else:
                other_test_units.append(unit)

        # 添加合并后的内核测试行
        if kernel_test_target > 0 or kernel_test_actual > 0:
            kernel_expected = round(kernel_test_target * progress_ratio, 1) if kernel_test_target > 0 else 0
            all_rows.append({
                '业务': '测试',
                '业务Owner': '郭琦',
                '作战单元': '内核测试',
                'Owner': '崔响灵/苏动',
                '漏测目标': kernel_test_target,
                '预期漏测DI': f"{kernel_expected:.1f}",
                '当前漏测DI': kernel_test_actual,
                '超标百分比': f"{((kernel_test_actual - kernel_expected) / kernel_expected * 100):.0f}%" if kernel_expected > 0 else "N/A"
            })

        # 添加其他测试单元（迁移工具测试、运维工具测试等）
        for unit in other_test_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': '测试',
                '业务Owner': '郭琦',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': f"{unit_expected:.1f}",
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 维优部
        weiyou = business_lines.get('维优部', {})
        weiyou_units = weiyou.get('sub_units', [])
        for unit in weiyou_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': '维优部',
                '业务Owner': '陈健华',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': f"{unit_expected:.1f}",
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 技术开发部
        tech_units = business_lines.get('技术开发部', {}).get('sub_units', [])
        for unit in tech_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': '技术开发部',
                '业务Owner': '王正侣',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': f"{unit_expected:.1f}",
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 显示表格
        df_all = pd.DataFrame(all_rows)
        if not df_all.empty:
            # 定义列配置（只有漏测目标和当前漏测DI可编辑）
            column_config = {
                '业务': st.column_config.TextColumn('业务', width='small', disabled=True),
                '业务Owner': st.column_config.TextColumn('业务Owner', width='small', disabled=True),
                '作战单元': st.column_config.TextColumn('作战单元', width='medium', disabled=True),
                'Owner': st.column_config.TextColumn('Owner', width='small', disabled=True),
                '漏测目标': st.column_config.NumberColumn('漏测目标', min_value=0, step=1, width='small'),
                '预期漏测DI': st.column_config.TextColumn('预期漏测DI', width='small', disabled=True),
                '当前漏测DI': st.column_config.NumberColumn('当前漏测DI', min_value=0, step=0.1, width='small'),
                '超标百分比': st.column_config.TextColumn('超标百分比', width='small', disabled=True),
                '状态': st.column_config.TextColumn('状态', width='small', disabled=True),
            }

            # 计算超标标记
            df_all['状态'] = ''
            for idx, row in df_all.iterrows():
                target = row.get('漏测目标', 0)
                actual = row.get('当前漏测DI', 0)
                expected = round(target * progress_ratio, 1) if target > 0 else 0
                df_all.at[idx, '预期漏测DI'] = f"{expected:.1f}"
                if expected > 0:
                    exceed_pct = (actual - expected) / expected * 100
                    df_all.at[idx, '超标百分比'] = f"{exceed_pct:.0f}%"
                    if exceed_pct > 0.1:
                        df_all.at[idx, '状态'] = '🔴 超标'
                    else:
                        df_all.at[idx, '状态'] = '✅ 正常'
                else:
                    df_all.at[idx, '超标百分比'] = 'N/A'
                    df_all.at[idx, '状态'] = '-'

            # 编辑表格（可编辑部分）
            st.write("**在表格中直接编辑「漏测目标」和「当前漏测DI」，超标>0.1%自动标红**")

            # 定义业务底色映射
            business_colors = {
                'G100老版本内核（含驱动HAS）': '#e3f2fd',  # 浅蓝
                'G100 V5版本': '#f3e5f5',  # 浅紫
                '重点项目': '#e8f5e9',  # 浅绿
                '测试': '#fff3e0',  # 浅橙
                '维优部': '#fce4ec',  # 浅粉
                '技术开发部': '#e0f2f1',  # 浅青
            }

            def highlight_business(row):
                """根据业务类型设置第一列（业务列）底色"""
                business = row.get('业务', '')
                color = business_colors.get(business, '')
                # 只给第一列（业务列）设置底色
                return [f'background-color: {color}' if idx == 0 else '' for idx, _ in enumerate(row)]

            def highlight_exceed_cell(val):
                """超标百分比>0.1%标红"""
                if isinstance(val, str) and '%' in val:
                    try:
                        num = float(val.replace('%', ''))
                        if num > 0.1:
                            return 'background-color: #ffcccc; color: #cc0000; font-weight: bold'
                    except:
                        pass
                return ''

            # 应用样式
            styled_df = df_all.style\
                .apply(highlight_business, axis=1)\
                .applymap(highlight_exceed_cell, subset=['超标百分比'])

            edited_df = st.data_editor(
                styled_df,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                key="editor_di_all",
                height=600  # 设置高度确保一页展示
            )

            st.caption("💡 直接编辑表格，业务列按类型着色，超标自动标红")

            if st.button("💾 保存漏测DI数据", type="primary", use_container_width=True):
                # 解析编辑后的数据并更新到业务线
                edited_rows = edited_df.to_dict('records')

                # 按业务分组更新
                g100_old_units = []
                g100_v5_units = []
                key_project_units = []
                test_units = []
                weiyou_units = []
                tech_units = []

                for row in edited_rows:
                    business = row.get('业务', '')
                    unit_data = {
                        'name': row.get('作战单元', ''),
                        'owner': row.get('Owner', ''),
                        'target': row.get('漏测目标', 0),
                        'actual': row.get('当前漏测DI', 0),
                    }

                    # 跳过小计行
                    if '【' in str(unit_data['name']) or '合计' in str(unit_data['name']):
                        continue

                    if business == 'G100老版本内核（含驱动HAS）':
                        g100_old_units.append(unit_data)
                    elif business == 'G100 V5版本':
                        g100_v5_units.append(unit_data)
                    elif business == '重点项目':
                        unit_data['business_owner'] = row.get('业务Owner', '')
                        key_project_units.append(unit_data)
                    elif business == '测试':
                        test_units.append(unit_data)
                    elif business == '维优部':
                        weiyou_units.append(unit_data)
                    elif business == '技术开发部':
                        tech_units.append(unit_data)

                # 更新业务线数据
                business_lines['G100老版本内核']['sub_units'] = g100_old_units
                business_lines['G100_V5版本']['sub_units'] = g100_v5_units
                business_lines['重点项目']['sub_units'] = key_project_units
                business_lines['测试']['sub_units'] = test_units
                business_lines['维优部']['sub_units'] = weiyou_units
                business_lines['技术开发部'] = {
                    'total_actual': sum(u.get('actual', 0) for u in tech_units),
                    'total_target': 0,
                    'total_expected': 0,
                    'achievement_rate': 'N/A',
                    'owner': '王正侣',
                    'sub_units': tech_units
                }

                defect_escape['current_di'] = current_di
                defect_escape['target_di'] = target_di
                defect_escape['as_of_date'] = as_of_date.strftime('%Y-%m-%d')
                defect_escape['expected_di'] = expected_total
                defect_escape['achievement_rate'] = f"{(current_di / expected_total * 100):.0f}%" if expected_total > 0 else "N/A"
                defect_escape['business_lines'] = business_lines

                st.session_state.data['quality_work']['defect_escape'] = defect_escape
                save_data_to_file(st.session_state.data)
                st.success("✅ 漏测DI数据已保存！")
                st.rerun()

    # ==================== 事故统计 ====================
    with tabs[2]:
        st.subheader("⚠️ 事故率统计")
        st.caption("编辑事故统计数据")

        qw_data = data.get('quality_work', {})
        accident_rate = qw_data.get('accident_rate', {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            downtime = st.number_input("停机时长(分钟)", value=int(accident_rate.get('downtime_minutes', 0)), step=1)
        with col2:
            reliability_fail = st.number_input("不达标套数", value=int(accident_rate.get('reliability_fail', 0)), step=1)
        with col3:
            total_systems = st.number_input("G100上线套数", value=int(accident_rate.get('total_systems', 3545)), step=1)
        with col4:
            cutover_systems = st.number_input("割接套数", value=int(accident_rate.get('cutover_systems', 155)), step=1)

        st.write("**事故等级分布**")
        severity_dist = accident_rate.get('severity_dist', {'P0': 0, 'P1': 0, 'P2': 0, 'P3': 0})
        df_severity = pd.DataFrame([severity_dist])

        edited_severity = st.data_editor(
            df_severity,
            use_container_width=True,
            hide_index=True,
            key="editor_severity"
        )

        if st.button("💾 保存事故率数据", type="primary", use_container_width=True):
            accident_rate['downtime_minutes'] = downtime
            accident_rate['reliability_fail'] = reliability_fail
            accident_rate['total_systems'] = total_systems
            accident_rate['cutover_systems'] = cutover_systems
            accident_rate['severity_dist'] = edited_severity.to_dict('records')[0] if not edited_severity.empty else severity_dist
            accident_rate['accidents_ytd'] = sum(edited_severity.to_dict('records')[0].values()) if not edited_severity.empty else 0

            st.session_state.data['quality_work']['accident_rate'] = accident_rate
            save_data_to_file(st.session_state.data)
            st.success("✅ 事故率数据已保存！")
            st.rerun()

        st.divider()

        # 事故明细列表
        st.subheader("📋 事故明细")
        st.caption("事故列表管理")

        # 获取事故列表
        if 'accidents' not in accident_rate:
            accident_rate['accidents'] = []
        accidents = accident_rate.get('accidents', [])

        if accidents:
            df_accidents = pd.DataFrame(accidents)
            # 确保所有列都存在
            for col in ['发生月份', '是否重点客户', '客户名称', '事故等级', '问题单号', '业务停机时长', '版本', '事故描述', '客户影响', '研发分析情况', '是否恢复', '事故定性']:
                if col not in df_accidents.columns:
                    df_accidents[col] = ''

            accident_config = {
                '发生月份': st.column_config.TextColumn('发生月份', width='small'),
                '是否重点客户': st.column_config.TextColumn('是否重点客户', width='small', help='输入: 是/否'),
                '客户名称': st.column_config.TextColumn('客户名称', width='medium'),
                '事故等级': st.column_config.TextColumn('事故等级', width='small', help='输入: P0/P1/P2/P3'),
                '问题单号': st.column_config.TextColumn('问题单号', width='small'),
                '业务停机时长': st.column_config.NumberColumn('停机时长(分钟)', min_value=0, step=1, width='small'),
                '版本': st.column_config.TextColumn('版本', width='small'),
                '事故描述': st.column_config.TextColumn('事故描述', width='large'),
                '客户影响': st.column_config.TextColumn('客户影响', width='medium'),
                '研发分析情况': st.column_config.TextColumn('研发分析', width='medium'),
                '是否恢复': st.column_config.TextColumn('是否恢复', width='small', help='输入: 已恢复/处理中/未恢复'),
                '事故定性': st.column_config.TextColumn('事故定性', width='medium', help='可多选，用逗号分隔'),
            }

            edited_accidents = st.data_editor(
                df_accidents,
                column_config=accident_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_accidents",
                height=400
            )

            if st.button("💾 保存事故列表", type="primary", use_container_width=True):
                accident_rate['accidents'] = edited_accidents.to_dict('records')
                st.session_state.data['quality_work']['accident_rate'] = accident_rate
                save_data_to_file(st.session_state.data)
                st.success("✅ 事故列表已保存！")
                st.rerun()
        else:
            st.info("暂无事故记录，请在下方添加")

        st.divider()

        # 新增事故表单
        st.subheader("➕ 新增事故")
        st.caption("填写事故信息并添加到列表")

        with st.form("add_accident_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_month = st.text_input("发生月份", placeholder="如：2025-05")
                new_customer = st.text_input("客户名称")
                new_ticket = st.text_input("问题单号")
            with col2:
                new_is_key = st.selectbox("是否重点客户", ["是", "否"])
                new_level = st.selectbox("事故等级", ["P0", "P1", "P2", "P3"])
                new_version = st.text_input("版本", placeholder="如：E100 3.0.3")
            with col3:
                new_downtime = st.number_input("业务停机时长(分钟)", min_value=0, step=1)
                new_recovered = st.selectbox("是否恢复", ["已恢复", "处理中", "未恢复"])

            new_description = st.text_area("事故描述", placeholder="详细描述事故情况...")
            new_impact = st.text_area("客户影响", placeholder="对客户业务的影响...")
            new_analysis = st.text_area("研发分析情况", placeholder="研发侧的原因分析和解决方案...")
            new_qualification = st.multiselect(
                "事故定性",
                options=["研发产品原因", "客户原因", "交付原因"],
                default=[],
                help="可多选"
            )

            submitted = st.form_submit_button("➕ 添加到事故列表", use_container_width=True)

            if submitted:
                new_accident = {
                    '发生月份': new_month,
                    '是否重点客户': new_is_key,
                    '客户名称': new_customer,
                    '事故等级': new_level,
                    '问题单号': new_ticket,
                    '业务停机时长': new_downtime,
                    '版本': new_version,
                    '事故描述': new_description,
                    '客户影响': new_impact,
                    '研发分析情况': new_analysis,
                    '是否恢复': new_recovered,
                    '事故定性': '、'.join(new_qualification) if new_qualification else ''
                }

                if 'accidents' not in accident_rate:
                    accident_rate['accidents'] = []
                accident_rate['accidents'].append(new_accident)

                st.session_state.data['quality_work']['accident_rate'] = accident_rate
                save_data_to_file(st.session_state.data)
                st.success("✅ 事故已添加！")
                st.rerun()

        st.divider()

        # 事故改进项跟踪
        st.subheader("🔧 事故改进项跟踪")
        st.caption("关联已登记事故，跟踪改进措施闭环情况")

        # 获取事故改进项列表
        if 'accident_improvements' not in accident_rate:
            accident_rate['accident_improvements'] = []
        improvements = accident_rate.get('accident_improvements', [])

        # 获取已登记事故列表（用于下拉选择）
        accident_options = []
        if accidents:
            for acc in accidents:
                label = f"{acc.get('发生月份', '')} - {acc.get('客户名称', '')} - {acc.get('问题单号', '')}"
                accident_options.append(label)

        if improvements:
            df_improvements = pd.DataFrame(improvements)
            # 确保所有列都存在
            for col in ['关联事故', '改进措施说明', '负责人', '预期闭环时间', '状态', '备注']:
                if col not in df_improvements.columns:
                    df_improvements[col] = ''

            improvement_config = {
                '关联事故': st.column_config.TextColumn('关联事故', width='large', help='格式: 月份 - 客户 - 问题单号'),
                '改进措施说明': st.column_config.TextColumn('改进措施说明', width='large'),
                '负责人': st.column_config.TextColumn('负责人', width='small'),
                '预期闭环时间': st.column_config.TextColumn('预期闭环时间', width='small', help='格式: YYYY-MM-DD'),
                '状态': st.column_config.TextColumn('状态', width='small', help='输入: 未开始/进行中/已完成/已闭环'),
                '备注': st.column_config.TextColumn('备注', width='medium'),
            }

            edited_improvements = st.data_editor(
                df_improvements,
                column_config=improvement_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_accident_improvements",
                height=350
            )

            if st.button("💾 保存事故改进项", type="primary", use_container_width=True):
                accident_rate['accident_improvements'] = edited_improvements.to_dict('records')
                st.session_state.data['quality_work']['accident_rate'] = accident_rate
                save_data_to_file(st.session_state.data)
                st.success("✅ 事故改进项已保存！")
                st.rerun()
        else:
            st.info("暂无事故改进项，请在下方添加")

        st.divider()

        # 新增事故改进项表单
        st.subheader("➕ 新增事故改进项")

        with st.form("add_improvement_form"):
            col1, col2 = st.columns(2)
            with col1:
                linked_accident = st.selectbox(
                    "关联事故",
                    options=accident_options if accident_options else ["请先登记事故"],
                    disabled=not accident_options
                )
                owner = st.text_input("负责人")
            with col2:
                close_time = st.text_input("预期闭环时间", placeholder="如：2025-06-30")
                status = st.selectbox("状态", ["未开始", "进行中", "已完成", "已闭环"])

            measure = st.text_area("改进措施说明", placeholder="详细描述改进措施...")
            remark = st.text_area("备注", placeholder="其他备注信息...")

            submitted = st.form_submit_button("➕ 添加到改进项列表", use_container_width=True, disabled=not accident_options)

            if submitted and accident_options:
                new_improvement = {
                    '关联事故': linked_accident,
                    '改进措施说明': measure,
                    '负责人': owner,
                    '预期闭环时间': close_time,
                    '状态': status,
                    '备注': remark
                }

                if 'accident_improvements' not in accident_rate:
                    accident_rate['accident_improvements'] = []
                accident_rate['accident_improvements'].append(new_improvement)

                st.session_state.data['quality_work']['accident_rate'] = accident_rate
                save_data_to_file(st.session_state.data)
                st.success("✅ 事故改进项已添加！")
                st.rerun()

    # ==================== 研发TOP质量事项 ====================
    with tabs[3]:
        st.subheader("🎯 研发TOP质量事项")
        st.caption("管理TOP质量事项的汇总表和详细进度跟踪")

        qi_data = data.get('quality_improvement', {})

        # 获取或初始化TOP事项数据
        if 'top_issues' not in qi_data or not isinstance(qi_data.get('top_issues'), dict):
            qi_data['top_issues'] = {}
        top_issues = qi_data.get('top_issues', {})

        # 数据迁移：将旧的 ongoing_tasks 迁移到新的 top_issues 结构
        if 'ongoing_tasks' in qi_data and qi_data['ongoing_tasks']:
            old_tasks = qi_data['ongoing_tasks']
            for task in old_tasks:
                task_name = task.get('name', '未命名事项')
                # 检查是否已存在
                if task_name not in top_issues:
                    top_issues[task_name] = {
                        'id': f"TOP-{len(top_issues):03d}",
                        'name': task_name,
                        'owner': task.get('owner', ''),
                        'progress': [{
                            '日期': task.get('due', ''),
                            '进度': f"{task.get('progress', 0)}%",
                            '状态说明': task.get('desc', ''),
                            '下一步计划': '',
                            '登记人': task.get('owner', '')
                        }] if task.get('progress', 0) > 0 else []
                    }
            # 清空旧数据（只迁移一次）
            qi_data['ongoing_tasks'] = []
            qi_data['top_issues'] = top_issues
            st.info("🔄 已自动将旧版改进任务数据迁移到新的TOP事项结构")

        # 汇总表数据
        if 'summary' not in top_issues:
            top_issues['summary'] = []
        summary_list = top_issues.get('summary', [])

        st.markdown("**📋 TOP事项汇总表**")
        st.caption("展示所有TOP事项的最新状态")

        if summary_list:
            df_summary = pd.DataFrame(summary_list)
            # 确保所有列都存在
            for col in ['事项编号', '事项名称', '负责人', '当前进度', '最新状态', '更新时间']:
                if col not in df_summary.columns:
                    df_summary[col] = ''

            summary_config = {
                '事项编号': st.column_config.TextColumn('事项编号', width='small', disabled=True),
                '事项名称': st.column_config.TextColumn('事项名称', width='large', disabled=True),
                '负责人': st.column_config.TextColumn('负责人', width='small', disabled=True),
                '当前进度': st.column_config.TextColumn('当前进度', width='small', disabled=True),
                '最新状态': st.column_config.TextColumn('最新状态', width='medium', disabled=True),
                '更新时间': st.column_config.TextColumn('更新时间', width='small', disabled=True),
            }

            st.data_editor(
                df_summary,
                column_config=summary_config,
                use_container_width=True,
                hide_index=True,
                key="editor_top_summary"
            )
        else:
            st.info("暂无TOP事项，请在下方添加")

        st.divider()

        # 每个TOP事项的详细进度表
        st.markdown("**📊 各TOP事项详细进度**")
        st.caption("为每个TOP事项记录详细进度，最新记录会自动同步到汇总表")

        # 获取所有TOP事项名称
        top_names = list(top_issues.keys())
        top_names = [n for n in top_names if n != 'summary']

        if top_names:
            # 为每个TOP事项创建子标签页
            top_tabs = st.tabs([f"📌 {name}" for name in top_names])

            for idx, top_name in enumerate(top_names):
                with top_tabs[idx]:
                    top_data = top_issues.get(top_name, {})
                    if 'progress' not in top_data:
                        top_data['progress'] = []
                    progress_list = top_data.get('progress', [])

                    # 显示基本信息
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**负责人:** {top_data.get('owner', '')}")
                    with col2:
                        st.write(f"**事项编号:** {top_data.get('id', '')}")
                    with col3:
                        latest_progress = progress_list[-1] if progress_list else None
                        if latest_progress:
                            st.write(f"**当前进度:** {latest_progress.get('进度', '0%')}")
                        else:
                            st.write(f"**当前进度:** 0%")

                    # 进度记录表格
                    if progress_list:
                        df_progress = pd.DataFrame(progress_list)
                        # 确保所有列都存在
                        for col in ['日期', '进度', '状态说明', '下一步计划', '登记人']:
                            if col not in df_progress.columns:
                                df_progress[col] = ''

                        progress_config = {
                            '日期': st.column_config.TextColumn('日期', width='small'),
                            '进度': st.column_config.TextColumn('进度', width='small', help='如: 30%, 50%'),
                            '状态说明': st.column_config.TextColumn('状态说明', width='large'),
                            '下一步计划': st.column_config.TextColumn('下一步计划', width='large'),
                            '登记人': st.column_config.TextColumn('登记人', width='small'),
                        }

                        edited_progress = st.data_editor(
                            df_progress,
                            column_config=progress_config,
                            num_rows="dynamic",
                            use_container_width=True,
                            hide_index=True,
                            key=f"editor_progress_{top_name}",
                            height=300
                        )

                        if st.button(f"💾 保存 {top_name} 进度", type="primary", use_container_width=True, key=f"save_progress_{top_name}"):
                            top_issues[top_name]['progress'] = edited_progress.to_dict('records')

                            # 更新汇总表
                            latest = edited_progress.iloc[-1] if not edited_progress.empty else None
                            if latest is not None:
                                # 查找并更新汇总表中的对应项
                                found = False
                                for s in summary_list:
                                    if s.get('事项编号') == top_data.get('id'):
                                        s['当前进度'] = latest.get('进度', '')
                                        s['最新状态'] = latest.get('状态说明', '')
                                        s['更新时间'] = latest.get('日期', '')
                                        found = True
                                        break
                                if not found:
                                    summary_list.append({
                                        '事项编号': top_data.get('id', ''),
                                        '事项名称': top_name,
                                        '负责人': top_data.get('owner', ''),
                                        '当前进度': latest.get('进度', ''),
                                        '最新状态': latest.get('状态说明', ''),
                                        '更新时间': latest.get('日期', '')
                                    })

                            qi_data['top_issues'] = top_issues
                            st.session_state.data['quality_improvement'] = qi_data
                            save_data_to_file(st.session_state.data)
                            st.success(f"✅ {top_name} 进度已保存，汇总表已更新！")
                            st.rerun()
                    else:
                        st.info(f"暂无 {top_name} 的进度记录")

                    # 新增进度记录表单
                    with st.form(f"add_progress_form_{top_name}"):
                        st.write("**➕ 新增进度记录**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            p_date = st.text_input("日期", placeholder="如: 2025-05-08", key=f"p_date_{top_name}")
                        with col2:
                            p_progress = st.text_input("进度", placeholder="如: 50%", key=f"p_progress_{top_name}")
                        with col3:
                            p_reporter = st.text_input("登记人", key=f"p_reporter_{top_name}")
                        p_status = st.text_area("状态说明", placeholder="当前进展状态...", key=f"p_status_{top_name}")
                        p_next = st.text_area("下一步计划", placeholder="下一步工作计划...", key=f"p_next_{top_name}")

                        submitted = st.form_submit_button("➕ 添加进度记录", use_container_width=True)
                        if submitted:
                            new_progress = {
                                '日期': p_date,
                                '进度': p_progress,
                                '状态说明': p_status,
                                '下一步计划': p_next,
                                '登记人': p_reporter
                            }
                            if 'progress' not in top_issues[top_name]:
                                top_issues[top_name]['progress'] = []
                            top_issues[top_name]['progress'].append(new_progress)

                            # 更新汇总表
                            found = False
                            for s in summary_list:
                                if s.get('事项编号') == top_data.get('id'):
                                    s['当前进度'] = p_progress
                                    s['最新状态'] = p_status
                                    s['更新时间'] = p_date
                                    found = True
                                    break
                            if not found:
                                summary_list.append({
                                    '事项编号': top_data.get('id', ''),
                                    '事项名称': top_name,
                                    '负责人': top_data.get('owner', ''),
                                    '当前进度': p_progress,
                                    '最新状态': p_status,
                                    '更新时间': p_date
                                })

                            qi_data['top_issues'] = top_issues
                            st.session_state.data['quality_improvement'] = qi_data
                            save_data_to_file(st.session_state.data)
                            st.success(f"✅ {top_name} 进度已添加，汇总表已更新！")
                            st.rerun()

        else:
            st.info("暂无TOP事项，请在下方添加")

        st.divider()

        # 新增TOP事项
        st.subheader("➕ 新增TOP质量事项")
        st.caption("添加新的TOP质量事项，会自动创建对应的详细进度表")

        with st.form("add_top_issue_form"):
            col1, col2 = st.columns(2)
            with col1:
                top_id = st.text_input("事项编号", placeholder="如: TOP-001")
                top_name = st.text_input("事项名称")
            with col2:
                top_owner = st.text_input("负责人")

            submitted = st.form_submit_button("➕ 创建TOP事项", use_container_width=True)
            if submitted:
                # 创建TOP事项
                top_issues[top_name] = {
                    'id': top_id,
                    'name': top_name,
                    'owner': top_owner,
                    'progress': []
                }
                # 添加到汇总表
                summary_list.append({
                    '事项编号': top_id,
                    '事项名称': top_name,
                    '负责人': top_owner,
                    '当前进度': '0%',
                    '最新状态': '新创建',
                    '更新时间': ''
                })

                qi_data['top_issues'] = top_issues
                st.session_state.data['quality_improvement'] = qi_data
                save_data_to_file(st.session_state.data)
                st.success(f"✅ TOP事项「{top_name}」已创建！")
                st.rerun()

    # ==================== 现网问题 ====================
    with tabs[4]:
        st.subheader("🌐 现网问题管理")
        st.caption("每周登记现网问题，支持批量导入和自动汇总分析")

        qw_data = data.get('quality_work', {})
        if 'production_issues' not in qw_data:
            qw_data['production_issues'] = {}
        prod_issues = qw_data['production_issues']

        # 周次选择
        col1, col2 = st.columns([1, 3])
        with col1:
            current_week = datetime.now().strftime('%Y-W%W')
            week_input = st.text_input("周次", value=prod_issues.get('current_week', current_week), help="格式: YYYY-WW")
        with col2:
            st.caption("💡 支持从Excel复制粘贴批量导入，也可逐行添加")

        # 批量导入区域
        st.markdown("**📋 批量导入（从Excel复制粘贴）**")
        bulk_input = st.text_area(
            "粘贴数据",
            placeholder="从Excel复制数据，格式：产品线\t问题分类\t客户名称\t严重程度\t缺陷ID\t环境\t版本\t缺陷描述\t客户影响\t状态",
            height=150,
            help="复制Excel表格内容，直接粘贴到这里，支持制表符分隔"
        )

        if st.button("📥 解析并导入数据", type="primary", use_container_width=True):
            if bulk_input.strip():
                lines = bulk_input.strip().split('\n')
                imported_count = 0
                last_product_line = ''  # 记录上一行的产品线，用于合并单元格情况
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) >= 8:
                        # 解析产品线（处理合并单元格：空值沿用上一行）
                        product_line = parts[0].strip()
                        if product_line:
                            last_product_line = product_line
                        else:
                            product_line = last_product_line if last_product_line else '未分类'

                        # 解析问题分类（第二列，处理合并单元格）
                        category = parts[1].strip()
                        if not category:
                            category = last_category if 'last_category' in locals() else '非重点客户一般问题'
                        else:
                            last_category = category

                        # 解析客户名称（第三列）
                        customer = parts[2].strip() if len(parts) > 2 else ''

                        # 解析严重程度（第四列）
                        severity = parts[3].strip() if len(parts) > 3 else '一般'

                        # 解析缺陷ID（第五列）
                        defect_id = parts[4].strip() if len(parts) > 4 else ''

                        # 解析环境（第六列）
                        env = parts[5].strip() if len(parts) > 5 else ''

                        # 解析版本（第七列）
                        version = parts[6].strip() if len(parts) > 6 else ''

                        # 解析缺陷描述（第八列）
                        description = parts[7].strip() if len(parts) > 7 else ''

                        # 解析客户影响（第九列）
                        impact = parts[8].strip() if len(parts) > 8 else ''

                        # 解析状态（第十列）
                        status = parts[9].strip() if len(parts) > 9 else '处理中'

                        # 创建问题记录
                        issue = {
                            '产品线': product_line,
                            '问题分类': category,
                            '客户名称': customer,
                            '严重程度': severity,
                            '缺陷ID': defect_id,
                            '环境': env,
                            '版本': version,
                            '缺陷描述': description,
                            '客户影响': impact,
                            '状态': status,
                            '周次': week_input,
                            '举一反三': False  # 是否已进行举一反三
                        }

                        if 'issues' not in prod_issues:
                            prod_issues['issues'] = []
                        prod_issues['issues'].append(issue)
                        imported_count += 1

                prod_issues['current_week'] = week_input
                st.session_state.data['quality_work']['production_issues'] = prod_issues
                save_data_to_file(st.session_state.data)
                st.success(f"✅ 成功导入 {imported_count} 条现网问题！")
                st.rerun()
            else:
                st.warning("请先粘贴数据")

        st.divider()

        # 显示所有现网问题（按周筛选）
        st.markdown("**📊 所有现网问题列表（按周筛选）**")

        # 获取所有周次列表
        def extract_week_num(week_str):
            """提取周次数字用于排序"""
            import re
            match = re.search(r'W(\d+)', week_str)
            if match:
                return int(match.group(1))
            return 0

        all_weeks = sorted(
            list(set([i.get('周次', '') for i in prod_issues.get('issues', []) if i.get('周次', '')])),
            key=extract_week_num
        )

        if all_weeks:
            # 使用session_state来保持周次选择同步
            if 'selected_week' not in st.session_state:
                st.session_state.selected_week = week_input

            # 如果week_input改变，更新selected_week
            if week_input != st.session_state.selected_week and week_input in all_weeks:
                st.session_state.selected_week = week_input

            selected_week = st.selectbox(
                "选择周次",
                options=all_weeks,
                index=all_weeks.index(st.session_state.selected_week) if st.session_state.selected_week in all_weeks else len(all_weeks)-1,
                key='week_selector'
            )

            # 同步到session_state
            st.session_state.selected_week = selected_week

            # 显示该周统计
            week_issues_all = [i for i in prod_issues['issues'] if i.get('周次') == selected_week]
            if week_issues_all:
                st.caption(f"{selected_week} 共 {len(week_issues_all)} 个问题")

            if week_issues_all:
                df_issues = pd.DataFrame(week_issues_all)

                # 列配置
                issue_config = {
                    '产品线': st.column_config.TextColumn('产品线', width='small'),
                    '问题分类': st.column_config.TextColumn('问题分类', width='medium'),
                    '客户名称': st.column_config.TextColumn('客户名称', width='small'),
                    '严重程度': st.column_config.TextColumn('严重程度', width='small', help='严重/一般/提示'),
                    '缺陷ID': st.column_config.TextColumn('缺陷ID', width='small'),
                    '环境': st.column_config.TextColumn('环境', width='small', help='生产/准生产/测试/POC'),
                    '版本': st.column_config.TextColumn('版本', width='small'),
                    '缺陷描述': st.column_config.TextColumn('缺陷描述', width='large'),
                    '客户影响': st.column_config.TextColumn('客户影响', width='medium'),
                    '状态': st.column_config.TextColumn('状态', width='small', help='处理中/已解决/已闭环'),
                    '举一反三': st.column_config.CheckboxColumn('举一反三', width='small'),
                }

                edited_issues = st.data_editor(
                    df_issues,
                    column_config=issue_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key="editor_production_issues",
                    height=400
                )

                col_save, col_delete = st.columns(2)
                with col_save:
                    if st.button("💾 保存现网问题", type="primary", use_container_width=True):
                        # 更新所有问题（保留其他周次的数据）
                        other_week_issues = [i for i in prod_issues['issues'] if i.get('周次') != selected_week]
                        prod_issues['issues'] = other_week_issues + edited_issues.to_dict('records')
                        st.session_state.data['quality_work']['production_issues'] = prod_issues
                        save_data_to_file(st.session_state.data)
                        st.success("✅ 现网问题已保存！")
                        st.rerun()

                with col_delete:
                    if st.button("🗑️ 清空该周数据", use_container_width=True):
                        other_week_issues = [i for i in prod_issues['issues'] if i.get('周次') != selected_week]
                        prod_issues['issues'] = other_week_issues
                        st.session_state.data['quality_work']['production_issues'] = prod_issues
                        save_data_to_file(st.session_state.data)
                        st.success(f"✅ {selected_week} 数据已清空！")
                        st.rerun()
        else:
            st.info("暂无现网问题数据，请通过上方批量导入")

        st.divider()

        # 自动汇总分析
        st.markdown("**📈 自动汇总分析**")

        if 'issues' in prod_issues and prod_issues['issues']:
            # 默认使用当前输入的周次进行分析
            analysis_week = week_input
            week_issues_analysis = [i for i in prod_issues['issues'] if i.get('周次') == analysis_week]

            if week_issues_analysis:
                df_analysis = pd.DataFrame(week_issues_analysis)

                # 统计指标
                total = len(week_issues_analysis)
                key_customer_issues = len([i for i in week_issues_analysis if i.get('问题分类', '') == '重点客户问题'])
                severe_issues = len([i for i in week_issues_analysis if i.get('严重程度') == '严重'])

                # 环境分布
                env_dist = {}
                for i in week_issues_analysis:
                    env = i.get('环境', '未知')
                    if '生产' in env or '准生产' in env:
                        env_dist['生产/准生产'] = env_dist.get('生产/准生产', 0) + 1
                    else:
                        env_dist['测试/其他'] = env_dist.get('测试/其他', 0) + 1

                # 重点客户列表
                key_customers = {}
                for i in week_issues_analysis:
                    if i.get('问题分类', '') == '重点客户问题':
                        cust = i.get('客户名称', '')
                        if cust:
                            key_customers[cust] = key_customers.get(cust, 0) + 1

                # 显示统计卡片
                stat_cols = st.columns(4)
                with stat_cols[0]:
                    st.metric("新增问题总数", total)
                with stat_cols[1]:
                    st.metric("重点客户问题", key_customer_issues)
                with stat_cols[2]:
                    st.metric("严重问题", severe_issues)
                with stat_cols[3]:
                    st.metric("生产/准生产环境", env_dist.get('生产/准生产', 0))

                # 生成分析报告
                st.markdown("**📝 客户问题分析报告**")
                report = f"""客户问题分析{analysis_week.replace('-', '')}：
1、新增{total}个现网问题，{key_customer_issues}个重点客户问题，{severe_issues}个严重问题
2、重点客户涉及{len(key_customers)}个：{', '.join([f"{k}({v})" for k, v in key_customers.items()])}
3、环境分布：测试环境{env_dist.get('测试/其他', 0)}个，生产/准生产环境{env_dist.get('生产/准生产', 0)}个
"""
                st.code(report, language=None)

                # 下载报告按钮
                st.download_button(
                    label="📄 下载分析报告",
                    data=report,
                    file_name=f"客户问题分析_{analysis_week}.txt",
                    mime="text/plain"
                )

                # 可视化图表
                chart_cols = st.columns(2)
                with chart_cols[0]:
                    # 产品线分布
                    if '产品线' in df_analysis.columns:
                        product_dist = df_analysis['产品线'].value_counts()
                        fig = px.pie(
                            values=product_dist.values,
                            names=product_dist.index,
                            title="产品线分布"
                        )
                        fig.update_layout(height=250)
                        st.plotly_chart(fig, use_container_width=True)

                with chart_cols[1]:
                    # 严重程度分布
                    if '严重程度' in df_analysis.columns:
                        severity_dist = df_analysis['严重程度'].value_counts()
                        fig = px.bar(
                            x=severity_dist.index,
                            y=severity_dist.values,
                            title="严重程度分布",
                            color=severity_dist.values,
                            color_continuous_scale=['#1dd1a1', '#feca57', '#ff6b6b']
                        )
                        fig.update_layout(height=250, showlegend=False)
                        st.plotly_chart(fig, use_container_width=True)

                st.success(f"✅ {analysis_week} 数据分析完成")
            else:
                st.info(f"暂无 {analysis_week} 的数据可供分析")
        else:
            st.info("暂无数据可供分析")

        st.divider()

        # 举一反三录入
        st.markdown("**💡 举一反三录入**")
        st.caption("登记需要进行举一反三的问题")

        # 获取所有已登记的问题（用于选择）
        all_issues_fanyi = prod_issues.get('issues', [])

        if all_issues_fanyi:
            # 构建缺陷ID列表（包含描述信息）
            defect_options = []
            defect_map = {}
            for issue in all_issues_fanyi:
                defect_id = issue.get('缺陷ID', '')
                desc = issue.get('缺陷描述', '')[:30] + '...' if len(issue.get('缺陷描述', '')) > 30 else issue.get('缺陷描述', '')
                week = issue.get('周次', '')
                if defect_id:
                    option_label = f"{defect_id} | {week} | {desc}"
                    defect_options.append(option_label)
                    defect_map[option_label] = defect_id

            # 选择缺陷ID
            selected_defect_label = st.selectbox("选择缺陷", options=defect_options, key="fanyi_defect_select")
            selected_defect_id = defect_map.get(selected_defect_label, '')

            # 获取选中的问题详情
            selected_issue = None
            for issue in all_issues_fanyi:
                if issue.get('缺陷ID') == selected_defect_id:
                    selected_issue = issue
                    break

            if selected_issue:
                st.caption(f"缺陷ID: {selected_defect_id}")

                # 显示当前举一反三状态
                col1, col2, col3 = st.columns(3)
                with col1:
                    current_status = selected_issue.get('举一反三状态', '未开始')
                    new_status = st.selectbox("举一反三状态", ["未开始", "进行中", "已完成"], index=["未开始", "进行中", "已完成"].index(current_status) if current_status in ["未开始", "进行中", "已完成"] else 0)
                with col2:
                    current_root = selected_issue.get('根因分类', '代码缺陷')
                    root_options = ["代码缺陷", "设计缺陷", "配置问题", "环境问题", "需求问题", "测试遗漏", "其他"]
                    new_root = st.selectbox("根因分类", root_options, index=root_options.index(current_root) if current_root in root_options else 0)
                with col3:
                    is_fanyi = st.checkbox("需要举一反三", value=selected_issue.get('举一反三', False))

                new_measure = st.text_area("改进措施", value=selected_issue.get('改进措施', ''), height=100)

                if st.button("💾 保存举一反三信息", type="primary", use_container_width=True):
                    # 更新原始数据
                    for issue in prod_issues['issues']:
                        if issue.get('缺陷ID') == selected_defect_id:
                            issue['举一反三'] = is_fanyi
                            issue['举一反三状态'] = new_status
                            issue['根因分类'] = new_root
                            issue['改进措施'] = new_measure
                            break

                    st.session_state.data['quality_work']['production_issues'] = prod_issues
                    save_data_to_file(st.session_state.data)
                    st.success("✅ 举一反三信息已保存！")
                    st.rerun()

            # 显示所有已标记举一反三的问题列表
            st.divider()
            st.markdown("**📋 已登记举一反三的问题列表**")
            fanyi_issues = [i for i in all_issues_fanyi if i.get('举一反三', False)]

            if fanyi_issues:
                df_fanyi_list = pd.DataFrame(fanyi_issues)
                display_cols = ['缺陷ID', '周次', '客户名称', '缺陷描述', '举一反三状态', '根因分类']
                available_cols = [c for c in display_cols if c in df_fanyi_list.columns]
                st.dataframe(df_fanyi_list[available_cols], use_container_width=True, hide_index=True)
            else:
                st.info("暂无已登记举一反三的问题")
        else:
            st.info("暂无现网问题数据，请先导入数据")

        st.divider()

        # 周趋势图
        st.markdown("**📊 现网问题周趋势**")

        if 'issues' in prod_issues and prod_issues['issues']:
            week_issues = [i for i in prod_issues['issues'] if i.get('周次') == week_input]

            if week_issues:
                df_analysis = pd.DataFrame(week_issues)

                # 统计指标
                total = len(week_issues)
                # 只统计"重点客户问题"类别，不包括"非重点客户严重问题"
                key_customer_issues = len([i for i in week_issues if i.get('问题分类', '') == '重点客户问题'])
                severe_issues = len([i for i in week_issues if i.get('严重程度') == '严重'])

                # 环境分布
                env_dist = {}
                for i in week_issues:
                    env = i.get('环境', '未知')
                    if '生产' in env or '准生产' in env:
                        env_dist['生产/准生产'] = env_dist.get('生产/准生产', 0) + 1
                    else:
                        env_dist['测试/其他'] = env_dist.get('测试/其他', 0) + 1

                # 重点客户列表（只统计"重点客户问题"类别）
                key_customers = {}
                for i in week_issues:
                    if i.get('问题分类', '') == '重点客户问题':
                        cust = i.get('客户名称', '')
                        if cust:
                            key_customers[cust] = key_customers.get(cust, 0) + 1

                # 显示统计卡片
                stat_cols = st.columns(4)
                with stat_cols[0]:
                    st.metric("新增问题总数", total)
                with stat_cols[1]:
                    st.metric("重点客户问题", key_customer_issues)
                with stat_cols[2]:
                    st.metric("严重问题", severe_issues)
                with stat_cols[3]:
                    prod_env_count = env_dist.get('生产/准生产', 0)
                    st.metric("生产/准生产环境", prod_env_count)

                # 生成分析报告
                st.markdown("**📝 客户问题分析报告**")

                report = f"""客户问题分析{week_input.replace('-', '')}：
1、新增{total}个现网问题，{key_customer_issues}个重点客户问题，{severe_issues}个严重问题
2、重点客户涉及{len(key_customers)}个：{', '.join([f"{k}({v})" for k, v in key_customers.items()])}
3、环境分布：测试环境{env_dist.get('测试/其他', 0)}个，生产/准生产环境{env_dist.get('生产/准生产', 0)}个
"""

                st.code(report, language=None)

                # 下载报告按钮
                st.download_button(
                    label="📄 下载分析报告",
                    data=report,
                    file_name=f"客户问题分析_{week_input}.txt",
                    mime="text/plain",
                    key=f"download_report_{week_input}"
                )

                # 可视化图表
                chart_cols = st.columns(2)
                with chart_cols[0]:
                    # 产品线分布
                    product_dist = df_analysis['产品线'].value_counts()
                    fig = px.pie(
                        values=product_dist.values,
                        names=product_dist.index,
                        title="产品线分布"
                    )
                    fig.update_layout(height=250)
                    st.plotly_chart(fig, use_container_width=True)

                with chart_cols[1]:
                    # 严重程度分布
                    severity_dist = df_analysis['严重程度'].value_counts()
                    fig = px.bar(
                        x=severity_dist.index,
                        y=severity_dist.values,
                        title="严重程度分布",
                        color=severity_dist.values,
                        color_continuous_scale=['#1dd1a1', '#feca57', '#ff6b6b']
                    )
                    fig.update_layout(height=250, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                # 周趋势图
                st.markdown("**📊 现网问题周趋势**")
                if 'issues' in prod_issues and prod_issues['issues']:
                    # 按周统计
                    week_stats = {}
                    for issue in prod_issues['issues']:
                        week = issue.get('周次', '')
                        if week:
                            week_stats[week] = week_stats.get(week, 0) + 1

                    if week_stats:
                        # 排序周次（处理合并周次如 W7&8）
                        def extract_week_num(week_str):
                            """提取周次数字用于排序"""
                            import re
                            # 匹配 W 后面的数字
                            match = re.search(r'W(\d+)', week_str)
                            if match:
                                return int(match.group(1))
                            return 0

                        sorted_weeks = sorted(week_stats.keys(), key=extract_week_num)
                        trend_df = pd.DataFrame({
                            '周次': sorted_weeks,
                            '问题数': [week_stats[w] for w in sorted_weeks]
                        })

                        fig_trend = px.line(
                            trend_df,
                            x='周次',
                            y='问题数',
                            title='现网问题周趋势',
                            markers=True
                        )
                        fig_trend.update_layout(height=300, template='plotly_white')
                        st.plotly_chart(fig_trend, use_container_width=True)

                        # 保存趋势数据到全局
                        qw_data['production_issues_trend'] = trend_df.to_dict('records')
                        st.session_state.data['quality_work'] = qw_data

                # 所有问题的分布图
                st.markdown("**📊 所有问题分布分析**")

                # 获取所有问题数据
                all_issues = prod_issues['issues']
                if all_issues:
                    df_all = pd.DataFrame(all_issues)

                    chart_cols = st.columns(2)
                    with chart_cols[0]:
                        # 产品线分布
                        if '产品线' in df_all.columns:
                            product_dist = df_all['产品线'].value_counts()
                            fig_product = px.pie(
                                values=product_dist.values,
                                names=product_dist.index,
                                title="产品线分布"
                            )
                            fig_product.update_layout(height=300)
                            st.plotly_chart(fig_product, use_container_width=True)

                    with chart_cols[1]:
                        # 严重程度分布
                        if '严重程度' in df_all.columns:
                            severity_dist = df_all['严重程度'].value_counts()
                            fig_severity = px.bar(
                                x=severity_dist.index,
                                y=severity_dist.values,
                                title="严重程度分布",
                                color=severity_dist.values,
                                color_continuous_scale=['#1dd1a1', '#feca57', '#ff6b6b']
                            )
                            fig_severity.update_layout(height=300, showlegend=False)
                            st.plotly_chart(fig_severity, use_container_width=True)

                    # 问题分类分布
                    if '问题分类' in df_all.columns:
                        category_dist = df_all['问题分类'].value_counts()
                        fig_category = px.bar(
                            x=category_dist.index,
                            y=category_dist.values,
                            title="问题分类分布",
                            color=category_dist.values,
                            color_continuous_scale=['#3498db', '#2ecc71', '#e74c3c']
                        )
                        fig_category.update_layout(height=300, showlegend=False)
                        st.plotly_chart(fig_category, use_container_width=True)

                # 按周汇总表（可编辑）
                st.markdown("**📋 按周汇总表（可编辑）**")
                st.caption("所有周次的现网问题汇总，可直接编辑纠正数据")

                # 按周统计详细信息
                week_summary = {}
                for issue in prod_issues['issues']:
                    week = issue.get('周次', '')
                    if week:
                        if week not in week_summary:
                            week_summary[week] = {
                                '周次': week,
                                '总问题数': 0,
                                '重点客户问题': 0,
                                '严重问题': 0,
                                '生产环境问题': 0,
                                '需举一反三': 0
                            }
                        week_summary[week]['总问题数'] += 1
                        if issue.get('问题分类') == '重点客户问题':
                            week_summary[week]['重点客户问题'] += 1
                        if issue.get('严重程度') == '严重':
                            week_summary[week]['严重问题'] += 1
                        if '生产' in issue.get('环境', '') or '准生产' in issue.get('环境', ''):
                            week_summary[week]['生产环境问题'] += 1
                        if issue.get('举一反三', False):
                            week_summary[week]['需举一反三'] += 1

                if week_summary:
                    # 转换为DataFrame并排序（使用周次数字排序）
                    summary_df = pd.DataFrame(list(week_summary.values()))
                    summary_df['排序'] = summary_df['周次'].apply(extract_week_num)
                    summary_df = summary_df.sort_values('排序').drop('排序', axis=1)

                    # 可编辑的汇总表
                    edited_summary = st.data_editor(
                        summary_df,
                        column_config={
                            '周次': st.column_config.TextColumn('周次', width='small', disabled=True),
                            '总问题数': st.column_config.NumberColumn('总问题数', width='small'),
                            '重点客户问题': st.column_config.NumberColumn('重点客户', width='small'),
                            '严重问题': st.column_config.NumberColumn('严重问题', width='small'),
                            '生产环境问题': st.column_config.NumberColumn('生产环境', width='small'),
                            '需举一反三': st.column_config.NumberColumn('需举一反三', width='small'),
                        },
                        use_container_width=True,
                        hide_index=True,
                        key="editor_week_summary"
                    )

                    if st.button("💾 保存汇总修改", type="primary", use_container_width=True):
                        st.success("✅ 汇总数据已更新！")

                    # 显示各周明细展开
                    st.markdown("**🔍 各周明细（点击展开查看）**")
                    sorted_week_keys = sorted(week_summary.keys(), key=extract_week_num)
                    week_tabs = st.tabs([f"📅 {w}" for w in sorted_week_keys])

                    for idx, week_key in enumerate(sorted_week_keys):
                        with week_tabs[idx]:
                            week_issues_detail = [i for i in prod_issues['issues'] if i.get('周次') == week_key]
                            if week_issues_detail:
                                df_week = pd.DataFrame(week_issues_detail)
                                display_cols = ['产品线', '问题分类', '客户名称', '严重程度', '环境', '版本', '状态', '举一反三']
                                available_cols = [c for c in display_cols if c in df_week.columns]

                                edited_week = st.data_editor(
                                    df_week[available_cols],
                                    column_config={
                                        '产品线': st.column_config.TextColumn('产品线', width='small'),
                                        '问题分类': st.column_config.TextColumn('问题分类', width='medium'),
                                        '客户名称': st.column_config.TextColumn('客户名称', width='small'),
                                        '严重程度': st.column_config.TextColumn('严重程度', width='small'),
                                        '环境': st.column_config.TextColumn('环境', width='small'),
                                        '版本': st.column_config.TextColumn('版本', width='small'),
                                        '状态': st.column_config.TextColumn('状态', width='small'),
                                        '举一反三': st.column_config.CheckboxColumn('举一反三', width='small'),
                                    },
                                    use_container_width=True,
                                    hide_index=True,
                                    key=f"editor_week_detail_{week_key}",
                                    height=300
                                )

                                if st.button(f"💾 保存 {week_key} 修改", type="primary", use_container_width=True, key=f"save_week_{week_key}"):
                                    # 更新原始数据
                                    other_weeks = [i for i in prod_issues['issues'] if i.get('周次') != week_key]
                                    updated_week = edited_week.to_dict('records')
                                    for item in updated_week:
                                        item['周次'] = week_key
                                    prod_issues['issues'] = other_weeks + updated_week
                                    st.session_state.data['quality_work']['production_issues'] = prod_issues
                                    save_data_to_file(st.session_state.data)
                                    st.success(f"✅ {week_key} 数据已保存！")
                                    st.rerun()
            else:
                st.info(f"暂无 {week_input} 周的数据可供分析")
        else:
            st.info("暂无数据可供分析")

    # ==================== 保存/导出 ====================
    with tabs[5]:
        st.subheader("💾 数据操作")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**导出数据**")
            json_str = json.dumps(st.session_state.data, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                label="📥 下载 JSON 备份",
                data=json_str,
                file_name=f"quality_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            st.write("**导入数据**")
            uploaded_file = st.file_uploader("选择 JSON 文件", type=['json'])
            if uploaded_file is not None:
                try:
                    imported_data = json.load(uploaded_file)
                    if st.button("📤 导入并覆盖当前数据", use_container_width=True):
                        st.session_state.data = imported_data
                        save_data_to_file(imported_data)
                        st.success("✅ 数据导入成功！")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("❌ 无效的 JSON 文件")

        st.divider()

        st.write("**推送数据到 GitHub**")
        st.code("""
# 在终端执行以下命令：
git add data/quality_data.json
git commit -m "Update: $(date +%Y-%m-%d) 质量数据"
git push origin main
        """, language='bash')

        st.info("💡 推送后 Streamlit Cloud 会自动更新（约1-2分钟）")
