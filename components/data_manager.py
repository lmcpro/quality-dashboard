"""
数据管理后台 - 使用表格编辑方式
"""
import streamlit as st
import json
from datetime import datetime
import pandas as pd

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
        "🔧 改进任务",
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
                '预期漏测DI': unit_expected,
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
            '预期漏测DI': g100_old_total_expected,
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
                    '预期漏测DI': unit_expected,
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
                '预期漏测DI': unit_expected,
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 测试
        test_units = business_lines.get('测试', {}).get('sub_units', [])
        for unit in test_units:
            unit_target = unit.get('target', 0)
            unit_expected = round(unit_target * progress_ratio, 1) if unit_target > 0 else 0
            all_rows.append({
                '业务': '测试',
                '业务Owner': '郭琦',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '漏测目标': unit_target,
                '预期漏测DI': unit_expected,
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
                '预期漏测DI': unit_expected,
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
                '预期漏测DI': unit_expected,
                '当前漏测DI': unit.get('actual', 0),
                '超标百分比': f"{((unit.get('actual', 0) - unit_expected) / unit_expected * 100):.0f}%" if unit_expected > 0 else "N/A"
            })

        # 显示表格
        df_all = pd.DataFrame(all_rows)
        if not df_all.empty:
            # 定义列配置
            column_config = {
                '业务': st.column_config.TextColumn('业务', width='small'),
                '业务Owner': st.column_config.TextColumn('业务Owner', width='small'),
                '作战单元': st.column_config.TextColumn('作战单元', width='medium'),
                'Owner': st.column_config.TextColumn('Owner', width='small'),
                '漏测目标': st.column_config.NumberColumn('漏测目标', min_value=0, step=1, width='small'),
                '预期漏测DI': st.column_config.NumberColumn('预期漏测DI', min_value=0, step=0.1, width='small', disabled=True),
                '当前漏测DI': st.column_config.NumberColumn('当前漏测DI', min_value=0, step=0.1, width='small'),
                '超标百分比': st.column_config.TextColumn('超标百分比', width='small', disabled=True),
            }

            edited_df = st.data_editor(
                df_all,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                key="editor_di_all"
            )

            # 超标标红预览
            st.write("**超标预览（超标>0.1%标红）**")

            def highlight_exceed(val):
                """超标百分比>0.1%标红"""
                if isinstance(val, str) and '%' in val:
                    try:
                        num = float(val.replace('%', ''))
                        if num > 0.1:
                            return 'background-color: #ffcccc; color: #cc0000; font-weight: bold'
                    except:
                        pass
                return ''

            # 计算更新后的超标百分比
            preview_df = edited_df.copy()
            for idx, row in preview_df.iterrows():
                target = row.get('漏测目标', 0)
                actual = row.get('当前漏测DI', 0)
                expected = round(target * progress_ratio, 1) if target > 0 else 0
                preview_df.at[idx, '预期漏测DI'] = expected
                if expected > 0:
                    exceed_pct = (actual - expected) / expected * 100
                    preview_df.at[idx, '超标百分比'] = f"{exceed_pct:.0f}%"
                    # 超标标红
                    if exceed_pct > 0.1:
                        preview_df.at[idx, '超标标记'] = '🔴 超标'
                    else:
                        preview_df.at[idx, '超标标记'] = ''
                else:
                    preview_df.at[idx, '超标百分比'] = 'N/A'
                    preview_df.at[idx, '超标标记'] = ''

            # 显示带标红的预览表
            styled_df = preview_df.style.applymap(highlight_exceed, subset=['超标百分比'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            st.caption("💡 编辑「漏测目标」和「当前漏测DI」，上方预览表实时显示超标标红情况")

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

    # ==================== 改进任务 ====================
    with tabs[3]:
        st.subheader("🔧 质量改进任务")
        st.caption("编辑进行中的改进任务")

        qi_data = data.get('quality_improvement', {})
        ongoing_tasks = qi_data.get('ongoing_tasks', [])

        if ongoing_tasks:
            df_tasks = pd.DataFrame(ongoing_tasks)
            column_config = {
                'name': st.column_config.TextColumn('任务名称', width='large'),
                'owner': st.column_config.TextColumn('负责人', width='small'),
                'progress': st.column_config.NumberColumn('进度(%)', min_value=0, max_value=100, step=5, width='small'),
                'due': st.column_config.TextColumn('截止日期', width='small'),
                'desc': st.column_config.TextColumn('描述', width='large'),
            }

            edited_df = st.data_editor(
                df_tasks,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="editor_tasks"
            )

            if st.button("💾 保存改进任务", type="primary", use_container_width=True):
                qi_data['ongoing_tasks'] = edited_df.to_dict('records')
                st.session_state.data['quality_improvement'] = qi_data
                save_data_to_file(st.session_state.data)
                st.success("✅ 改进任务已保存！")
                st.rerun()

    # ==================== 保存/导出 ====================
    with tabs[4]:
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
