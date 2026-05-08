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
        st.caption("批量导入、按周管理现网问题，支持举一反三登记")

        qw_data = data.get('quality_work', {})
        if 'production_issues' not in qw_data:
            qw_data['production_issues'] = {'issues': []}
        prod_issues = qw_data['production_issues']
        issues_list = prod_issues.get('issues', [])

        # ========== 1. 批量导入 ==========
        st.markdown("#### 📥 批量导入")
        with st.expander("从Excel复制粘贴导入", expanded=True):
            st.caption("从Excel复制数据，粘贴到下方文本框，格式：产品线 | 问题分类 | 客户名称 | 严重程度 | 环境 | 版本 | 问题描述 | 状态 | 举一反三")
            
            col_paste, col_week = st.columns([3, 1])
            with col_paste:
                paste_data = st.text_area("粘贴数据", height=120, key="prod_issues_paste", 
                                         placeholder="产品线\t问题分类\t客户名称\t严重程度\t环境\t版本\t问题描述\t状态\t举一反三")
            with col_week:
                current_week = f"W{datetime.now().isocalendar()[1]}"
                week_input = st.text_input("周次", value=current_week, key="prod_issues_week")
                st.caption("格式：W18")

            if st.button("📥 解析并导入", type="primary", key="btn_parse_import"):
                if paste_data.strip():
                    lines = paste_data.strip().split('\n')
                    imported_count = 0
                    for line in lines:
                        parts = line.split('\t')
                        if len(parts) >= 8:
                            issue = {
                                '周次': week_input.upper(),
                                '产品线': parts[0].strip(),
                                '问题分类': parts[1].strip(),
                                '客户名称': parts[2].strip(),
                                '严重程度': parts[3].strip(),
                                '环境': parts[4].strip(),
                                '版本': parts[5].strip(),
                                '问题描述': parts[6].strip(),
                                '状态': parts[7].strip() if len(parts) > 7 else '待处理',
                                '举一反三': parts[8].strip() == '是' if len(parts) > 8 else False,
                                '登记时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                            issues_list.append(issue)
                            imported_count += 1

                    qw_data['production_issues'] = prod_issues
                    st.session_state.data['quality_work'] = qw_data
                    save_data_to_file(st.session_state.data)
                    st.success(f"✅ 成功导入 {imported_count} 条现网问题到 {week_input.upper()}！")
                    st.rerun()
                else:
                    st.warning("请先粘贴数据")

        # ========== 2. 刚导入的问题列表（按周筛选、可编辑） ==========
        st.markdown("#### 📊 问题列表（按周筛选编辑）")
        
        # 获取所有周次并排序
        all_weeks = sorted(list(set([i.get('周次', '') for i in issues_list if i.get('周次', '')])), key=lambda x: x)

        if all_weeks:
            # 使用列布局：周次选择 + 统计卡片
            col_week_select, col_stats = st.columns([1, 3])
            
            with col_week_select:
                selected_week = st.selectbox("选择周次", all_weeks, key="week_select")
            
            # 筛选该周的问题
            week_issues = [i for i in issues_list if i.get('周次') == selected_week]
            
            with col_stats:
                if week_issues:
                    total = len(week_issues)
                    key_customer = len([i for i in week_issues if i.get('问题分类') == '重点客户问题'])
                    severe = len([i for i in week_issues if i.get('严重程度') == '严重'])
                    fanyi = len([i for i in week_issues if i.get('举一反三', False)])
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("问题总数", total)
                    c2.metric("重点客户", key_customer)
                    c3.metric("严重问题", severe)
                    c4.metric("需举一反三", fanyi)
            
            if week_issues:
                df_week = pd.DataFrame(week_issues)

                # 定义列配置
                column_config = {
                    '周次': st.column_config.TextColumn('周次', width='small'),
                    '产品线': st.column_config.TextColumn('产品线', width='medium'),
                    '问题分类': st.column_config.SelectboxColumn('问题分类', options=['重点客户问题', '一般问题', '内部问题'], width='medium'),
                    '客户名称': st.column_config.TextColumn('客户名称', width='medium'),
                    '严重程度': st.column_config.SelectboxColumn('严重程度', options=['严重', '一般', '轻微'], width='small'),
                    '环境': st.column_config.SelectboxColumn('环境', options=['生产环境', '准生产环境', '测试环境', '开发环境'], width='small'),
                    '版本': st.column_config.TextColumn('版本', width='small'),
                    '问题描述': st.column_config.TextColumn('问题描述', width='large'),
                    '状态': st.column_config.SelectboxColumn('状态', options=['待处理', '处理中', '已解决', '已关闭'], width='small'),
                    '举一反三': st.column_config.CheckboxColumn('举一反三', width='small'),
                }

                edited_df = st.data_editor(
                    df_week,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key=f"editor_week_issues_{selected_week}"
                )

                col_save, col_del = st.columns([1, 4])
                with col_save:
                    if st.button("💾 保存修改", type="primary", key=f"btn_save_week_{selected_week}"):
                        other_issues = [i for i in issues_list if i.get('周次') != selected_week]
                        updated_issues = edited_df.to_dict('records')
                        issues_list = other_issues + updated_issues
                        prod_issues['issues'] = issues_list
                        qw_data['production_issues'] = prod_issues
                        st.session_state.data['quality_work'] = qw_data
                        save_data_to_file(st.session_state.data)
                        st.success("✅ 已保存！")
                        st.rerun()

                with col_del:
                    if st.button("🗑️ 删除本周所有数据", key=f"btn_del_week_{selected_week}"):
                        other_issues = [i for i in issues_list if i.get('周次') != selected_week]
                        prod_issues['issues'] = other_issues
                        qw_data['production_issues'] = prod_issues
                        st.session_state.data['quality_work'] = qw_data
                        save_data_to_file(st.session_state.data)
                        st.success("✅ 本周数据已删除！")
                        st.rerun()
            else:
                st.info(f"{selected_week} 暂无数据")
        else:
            st.info("暂无现网问题数据，请使用上方批量导入功能添加")

        # ========== 3. 自动汇总分析 ==========
        st.markdown("#### 📈 自动汇总分析")
        
        if issues_list:
            # 统计各周数据
            week_stats = {}
            for issue in issues_list:
                week = issue.get('周次', '未知')
                if week not in week_stats:
                    week_stats[week] = {
                        'total': 0, 'key_customer': 0, 'severe': 0,
                        'prod_env': 0, 'fanyi': 0, 'customers': set()
                    }
                week_stats[week]['total'] += 1
                if issue.get('问题分类') == '重点客户问题':
                    week_stats[week]['key_customer'] += 1
                if issue.get('严重程度') == '严重':
                    week_stats[week]['severe'] += 1
                if '生产' in issue.get('环境', '') or '准生产' in issue.get('环境', ''):
                    week_stats[week]['prod_env'] += 1
                if issue.get('举一反三', False):
                    week_stats[week]['fanyi'] += 1
                if issue.get('客户名称'):
                    week_stats[week]['customers'].add(issue.get('客户名称'))

            # 统计卡片
            total_issues = sum(s['total'] for s in week_stats.values())
            total_key = sum(s['key_customer'] for s in week_stats.values())
            total_severe = sum(s['severe'] for s in week_stats.values())
            total_fanyi = sum(s['fanyi'] for s in week_stats.values())
            
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("📊 问题总数", total_issues)
            col2.metric("👥 重点客户问题", total_key)
            col3.metric("🔴 严重问题", total_severe)
            col4.metric("💡 需举一反三", total_fanyi)
            col5.metric("📅 统计周数", len(week_stats))

            # 图表展示
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # 产品线分布
                product_lines = {}
                for issue in issues_list:
                    pl = issue.get('产品线', '未知')
                    product_lines[pl] = product_lines.get(pl, 0) + 1

                if product_lines:
                    fig_pl = px.pie(
                        values=list(product_lines.values()),
                        names=list(product_lines.keys()),
                        title="产品线分布"
                    )
                    fig_pl.update_layout(height=280, showlegend=True)
                    st.plotly_chart(fig_pl, use_container_width=True, key="chart_pl_dist")
            
            with chart_col2:
                # 严重程度分布
                severity_dist = {}
                for issue in issues_list:
                    sev = issue.get('严重程度', '未知')
                    severity_dist[sev] = severity_dist.get(sev, 0) + 1

                if severity_dist:
                    fig_sev = px.bar(
                        x=list(severity_dist.keys()),
                        y=list(severity_dist.values()),
                        title="严重程度分布",
                        color=list(severity_dist.keys()),
                        color_discrete_map={'严重': '#ff6b6b', '一般': '#feca57', '轻微': '#1dd1a1'}
                    )
                    fig_sev.update_layout(height=280, showlegend=False)
                    st.plotly_chart(fig_sev, use_container_width=True, key="chart_sev_dist")
        else:
            st.info("暂无数据可分析")

        # ========== 4. 举一反三录入 ==========
        st.markdown("#### 💡 举一反三录入")
        
        if issues_list:
            # 获取需要举一反三的问题
            fanyi_candidates = [i for i in issues_list if i.get('举一反三', False)]

            if fanyi_candidates:
                # 创建选项列表
                fanyi_options = []
                for idx, issue in enumerate(fanyi_candidates):
                    display = f"[{idx+1}] {issue.get('客户名称', '未知客户')} - {issue.get('问题描述', '无描述')[:25]}..."
                    fanyi_options.append((idx, display, issue))

                col_select, col_form = st.columns([1, 2])
                
                with col_select:
                    selected_idx = st.selectbox(
                        "选择缺陷ID",
                        options=range(len(fanyi_options)),
                        format_func=lambda x: fanyi_options[x][1],
                        key="fanyi_select"
                    )

                selected_issue = fanyi_options[selected_idx][2]
                
                with col_form:
                    with st.form("fanyi_form"):
                        st.caption(f"选中: {selected_issue.get('客户名称')} - {selected_issue.get('问题描述', '')[:30]}...")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            fanyi_action = st.text_input("改进行动", placeholder="描述改进行动")
                            fanyi_scope = st.text_input("影响范围", placeholder="如：G100全系列")
                        with col_b:
                            fanyi_owner = st.text_input("负责人")
                            fanyi_deadline = st.text_input("截止日期", placeholder="如：2025-06-30")

                        submitted = st.form_submit_button("💾 保存举一反三", use_container_width=True)

                        if submitted:
                            qi_data = data.get('quality_improvement', {})
                            if '举一反三' not in qi_data:
                                qi_data['举一反三'] = {'total': 0, 'completed': 0, 'pending': 0, 'items': []}

                            fanyi_data = qi_data['举一反三']
                            fanyi_data['items'].append({
                                'source': selected_issue.get('客户名称', ''),
                                'action': fanyi_action,
                                'scope': fanyi_scope,
                                'status': '进行中',
                                'progress': 0,
                                'owner': fanyi_owner,
                                'deadline': fanyi_deadline
                            })
                            fanyi_data['total'] += 1
                            fanyi_data['pending'] += 1

                            qi_data['举一反三'] = fanyi_data
                            st.session_state.data['quality_improvement'] = qi_data
                            save_data_to_file(st.session_state.data)
                            st.success("✅ 举一反三已登记！")
                            st.rerun()
            else:
                st.info("暂无需举一反三的问题，请先在问题列表中勾选「举一反三」")
        else:
            st.info("暂无现网问题数据")

        # ========== 5. 现网问题周趋势 ==========
        st.markdown("#### 📊 现网问题周趋势")

        if issues_list:
            week_counts = {}
            for issue in issues_list:
                week = issue.get('周次', '未知')
                week_counts[week] = week_counts.get(week, 0) + 1

            sorted_weeks = sorted(week_counts.keys())
            trend_data = [{'周次': w, '问题数': week_counts[w]} for w in sorted_weeks]
            df_trend = pd.DataFrame(trend_data)

            if not df_trend.empty:
                import plotly.graph_objects as go
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=df_trend['周次'],
                    y=df_trend['问题数'],
                    mode='lines+markers',
                    name='问题数',
                    line=dict(color='#1f77b4', width=2),
                    marker=dict(size=8)
                ))
                fig_trend.update_layout(
                    height=300,
                    template='plotly_white',
                    margin=dict(l=10, r=10, t=30, b=10),
                    yaxis_title='问题数',
                    xaxis_title='周次'
                )
                st.plotly_chart(fig_trend, use_container_width=True, key="chart_week_trend")
        else:
            st.info("暂无趋势数据")

        # ========== 6. 按周汇总表 ==========
        st.markdown("#### 📋 按周汇总表")

        if issues_list and week_stats:
            # 使用表格展示各周汇总
            summary_data = []
            for week in sorted(week_stats.keys()):
                stats = week_stats[week]
                summary_data.append({
                    '周次': week,
                    '问题总数': stats['total'],
                    '重点客户': stats['key_customer'],
                    '严重问题': stats['severe'],
                    '生产环境': stats['prod_env'],
                    '举一反三': stats['fanyi'],
                    '涉及客户': len(stats['customers'])
                })

            df_summary = pd.DataFrame(summary_data)
            
            # 高亮显示
            def highlight_key_customer(val):
                if val > 0:
                    return 'background-color: #fff3cd'
                return ''
            
            def highlight_severe(val):
                if val > 0:
                    return 'background-color: #f8d7da'
                return ''
            
            styled_summary = df_summary.style\
                .applymap(highlight_key_customer, subset=['重点客户'])\
                .applymap(highlight_severe, subset=['严重问题'])
            
            st.dataframe(styled_summary, use_container_width=True, hide_index=True)
        else:
            st.info("暂无汇总数据")

        # ========== 7. 各周明细 ==========
        st.markdown("#### 🔍 各周明细")

        if issues_list:
            # 使用标签页展示各周明细
            all_weeks = sorted(list(set([i.get('周次', '') for i in issues_list if i.get('周次', '')])))
            
            if all_weeks:
                week_tabs = st.tabs(all_weeks)
                
                for tab, week in zip(week_tabs, all_weeks):
                    with tab:
                        week_issues = [i for i in issues_list if i.get('周次') == week]
                        df_week_detail = pd.DataFrame(week_issues)
                        display_cols = ['产品线', '问题分类', '客户名称', '严重程度', '环境', '版本', '状态', '举一反三']
                        available_cols = [c for c in display_cols if c in df_week_detail.columns]
                        st.dataframe(df_week_detail[available_cols], use_container_width=True, hide_index=True)
                        st.caption(f"{week} 共 {len(week_issues)} 个问题")
        else:
            st.info("暂无明细数据")

