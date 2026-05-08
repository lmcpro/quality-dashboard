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
                'trend': st.column_config.SelectColumn('趋势', options=['up', 'stable', 'down'], width='small'),
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
        st.caption("编辑各业务线的漏测DI数据")

        qw_data = data.get('quality_work', {})
        defect_escape = qw_data.get('defect_escape', {})

        # 总体数据
        st.write("**总体统计**")
        col1, col2, col3 = st.columns(3)
        with col1:
            current_di = st.number_input("当前漏测DI", value=float(defect_escape.get('current_di', 0)), step=0.1)
        with col2:
            target_di = st.number_input("年度目标", value=float(defect_escape.get('target_di', 870)), step=1.0)
        with col3:
            as_of_date = st.date_input("统计日期", value=datetime.strptime(defect_escape.get('as_of_date', '2026-01-01'), '%Y-%m-%d'))

        # 作战单元明细
        st.divider()
        st.write("**作战单元明细**")

        business_lines = defect_escape.get('business_lines', {})
        g100 = business_lines.get('G100老版本内核', {})
        sub_units = g100.get('sub_units', [])

        if sub_units:
            df_units = pd.DataFrame(sub_units)
            column_config = {
                'name': st.column_config.TextColumn('作战单元', width='medium', disabled=True),
                'owner': st.column_config.TextColumn('Owner', width='small'),
                'target': st.column_config.NumberColumn('目标', min_value=0, step=1, width='small'),
                'expected': st.column_config.NumberColumn('预期', min_value=0, step=0.1, width='small'),
                'actual': st.column_config.NumberColumn('实际', min_value=0, step=0.1, width='small'),
                'variance': st.column_config.TextColumn('偏差', width='small'),
            }

            edited_df = st.data_editor(
                df_units,
                column_config=column_config,
                use_container_width=True,
                hide_index=True,
                key="editor_di_units"
            )

            if st.button("💾 保存漏测DI数据", type="primary", use_container_width=True):
                # 更新数据
                business_lines['G100老版本内核']['sub_units'] = edited_df.to_dict('records')
                defect_escape['current_di'] = current_di
                defect_escape['target_di'] = target_di
                defect_escape['as_of_date'] = as_of_date.strftime('%Y-%m-%d')
                defect_escape['business_lines'] = business_lines

                # 计算达成率
                expected = current_di / (target_di * 0.27) * 100 if target_di > 0 else 0
                defect_escape['achievement_rate'] = f"{expected:.0f}%"

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
