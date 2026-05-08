"""
版本质量板块 - 集成TAPD缺陷统计
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 导入TAPD集成
try:
    from utils.tapd_integration import get_tapd_stats_sync, SEVERITY_EMOJI
except ImportError:
    SEVERITY_EMOJI = {'致命': '🔴', '严重': '🟠', '一般': '⚪', '轻微': '⚪', '提示': '⚪'}
    def get_tapd_stats_sync(version_keyword=None, start_date=None, end_date=None):
        return None

def show_version_quality():
    """展示版本质量板块"""
    st.markdown('<div class="section-title">📱 版本质量</div>', unsafe_allow_html=True)

    # TAPD实时数据获取
    st.subheader("📡 TAPD实时缺陷统计")

    # 选择版本
    tapd_version = st.selectbox(
        "选择要查看的版本",
        ["5.0.0 (V5)", "3.0.9 (V3)", "全部版本"],
        index=0,
        key="tapd_version_select"
    )

    version_map = {
        "5.0.0 (V5)": "5.0.0",
        "3.0.9 (V3)": "3.0.9",
        "全部版本": None
    }
    selected_version = version_map[tapd_version]

    # 时间范围选择
    st.write("**📅 时间范围筛选**")

    # 快捷时间选择（放在日期选择器之前）
    quick_select = st.selectbox(
        "快捷选择",
        ["自定义", "今天", "最近7天", "最近30天", "最近90天", "本月", "上月"],
        index=2,
        key="tapd_quick_select"
    )

    # 根据快捷选择更新 session state 中的日期
    today = datetime.now().date()
    if quick_select != "自定义":
        if quick_select == "今天":
            st.session_state['tapd_start_date'] = today
            st.session_state['tapd_end_date'] = today
        elif quick_select == "最近7天":
            st.session_state['tapd_start_date'] = today - timedelta(days=7)
            st.session_state['tapd_end_date'] = today
        elif quick_select == "最近30天":
            st.session_state['tapd_start_date'] = today - timedelta(days=30)
            st.session_state['tapd_end_date'] = today
        elif quick_select == "最近90天":
            st.session_state['tapd_start_date'] = today - timedelta(days=90)
            st.session_state['tapd_end_date'] = today
        elif quick_select == "本月":
            st.session_state['tapd_start_date'] = today.replace(day=1)
            st.session_state['tapd_end_date'] = today
        elif quick_select == "上月":
            first_day_this_month = today.replace(day=1)
            st.session_state['tapd_end_date'] = first_day_this_month - timedelta(days=1)
            st.session_state['tapd_start_date'] = st.session_state['tapd_end_date'].replace(day=1)

    date_cols = st.columns(3)
    with date_cols[0]:
        # 使用 session state 中的值作为默认值
        start_date_default = st.session_state.get('tapd_start_date', today - timedelta(days=30))
        start_date = st.date_input(
            "开始日期",
            value=start_date_default,
            max_value=datetime.now(),
            key="tapd_start_date"
        )
    with date_cols[1]:
        end_date_default = st.session_state.get('tapd_end_date', today)
        end_date = st.date_input(
            "结束日期",
            value=end_date_default,
            max_value=datetime.now(),
            key="tapd_end_date"
        )
    with date_cols[2]:
        st.write("&nbsp;")  # 占位
        st.caption("💡 快捷选择会覆盖日期")

    # 显示当前选择的时间范围
    st.caption(f"📅 当前筛选范围: {start_date} 至 {end_date} (共 {(end_date - start_date).days + 1} 天)")

    # 获取TAPD数据按钮
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        if st.button("🔄 获取TAPD实时数据", use_container_width=True, key="fetch_tapd_btn"):
            with st.spinner("正在从TAPD API获取真实数据，请稍候..."):
                try:
                    tapd_data = get_tapd_stats_sync(
                        selected_version,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d')
                    )
                    if tapd_data:
                        st.session_state['tapd_data'] = tapd_data
                        st.session_state['tapd_date_range'] = {
                            'start': start_date.strftime('%Y-%m-%d'),
                            'end': end_date.strftime('%Y-%m-%d')
                        }
                        st.success(f"✅ 成功获取TAPD实时数据！共 {tapd_data.get('total_bugs', 0)} 条缺陷")
                    else:
                        st.error("❌ API调用失败，请检查网络或API配置")
                except Exception as e:
                    st.error(f"❌ 获取数据失败: {str(e)}")

    with col2:
        if 'tapd_data' in st.session_state and st.session_state['tapd_data']:
            st.caption(f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col3:
        st.caption("💡 点击按钮从TAPD获取真实缺陷数据")

    # 展示TAPD数据
    if 'tapd_data' in st.session_state and st.session_state['tapd_data']:
        show_tapd_stats(st.session_state['tapd_data'])
    else:
        st.info("👆 请点击上方按钮获取TAPD实时数据")

    st.divider()


def show_tapd_stats(tapd_data):
    """展示TAPD缺陷统计"""

    # 数据来源标识
    st.caption("**数据来源: 📊 TAPD实时数据**")

    # 显示时间范围
    if 'tapd_date_range' in st.session_state:
        date_range = st.session_state['tapd_date_range']
        st.info(f"📅 当前数据时间范围: {date_range['start']} 至 {date_range['end']}")

    # 总体统计卡片
    st.write("**📈 总体统计**")
    cols = st.columns(4)
    with cols[0]:
        st.metric("版本总缺陷", tapd_data.get('total_bugs', 0))
    with cols[1]:
        st.metric("未修复缺陷", tapd_data.get('unfixed_bugs', 0), delta_color="inverse")
    with cols[2]:
        daily = tapd_data.get('daily_stats', {})
        net_change = daily.get('net_change', 0)
        st.metric("今日净变化", net_change)
    with cols[3]:
        sev_stats = tapd_data.get('severity_stats', {})
        fatal = sev_stats.get('致命', 0)
        serious = sev_stats.get('严重', 0)
        high_risk = fatal + serious
        st.metric("🔥 高风险缺陷", high_risk,
                 delta=f"致命{fatal}+严重{serious}",
                 delta_color="inverse" if high_risk > 0 else "normal")

    # 内外部缺陷分布 + 研发待处理
    st.write("**📊 内外部缺陷分布 & 研发待处理**")
    dist_cols = st.columns(4)

    with dist_cols[0]:
        customer_count = tapd_data.get('customer_bugs_count', 0)
        st.metric("👥 客户缺陷", customer_count)

    with dist_cols[1]:
        internal_count = tapd_data.get('internal_bugs_count', 0)
        st.metric("🏢 内部缺陷", internal_count)

    with dist_cols[2]:
        dev_pending = tapd_data.get('dev_pending_count', 0)
        st.metric("🔧 研发待处理", dev_pending,
                 delta=f"待修复{dev_pending}",
                 delta_color="inverse" if dev_pending > 0 else "normal")

    with dist_cols[3]:
        # 计算修复率
        total = tapd_data.get('total_bugs', 0)
        unfixed = tapd_data.get('unfixed_bugs', 0)
        fixed_rate = round((total - unfixed) / total * 100, 1) if total > 0 else 0
        st.metric("✅ 修复率", f"{fixed_rate}%")

    # 严重程度分布
    st.write("**📊 未修复缺陷严重程度分布**")
    sev_cols = st.columns(5)
    sev_data = tapd_data.get('severity_stats', {})
    
    for idx, (sev, emoji) in enumerate(SEVERITY_EMOJI.items()):
        with sev_cols[idx]:
            count = sev_data.get(sev, 0)
            st.metric(f"{emoji} {sev}", count)

    # 高风险缺陷列表
    high_risk_bugs = tapd_data.get('high_risk_bugs', [])
    high_risk_count = tapd_data.get('high_risk_count', len(high_risk_bugs))
    
    if high_risk_count > 0:
        st.write(f"**🔥 高风险缺陷列表（共{high_risk_count}个）**")
        
        # 按严重程度分组展示
        for bug in high_risk_bugs:
            severity = bug.get('severity', '')
            emoji = SEVERITY_EMOJI.get(severity, '⚪')
            
            with st.expander(f"{emoji} [{bug.get('id', 'N/A')[-7:]}] {bug.get('title', '无标题')}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**严重程度:** {emoji} {severity}")
                    st.write(f"**所属模块:** {bug.get('module', '未分类')}")
                    st.caption(f"**缺陷描述:** {bug.get('description', '无描述')}")
                with col2:
                    st.write(f"**当前状态:** {bug.get('status', '未知')}")
                    st.write(f"**创建时间:** {bug.get('created', '')[:10]}")
                with col3:
                    # 风险等级标识
                    if severity == '致命':
                        st.error("⚠️ 封板前必须清零")
                    elif severity == '严重':
                        st.warning("⚠️ 优先处理")
                    else:
                        st.info("需关注")
    else:
        st.success("✅ 暂无高风险缺陷（致命/严重）")

    # 模块风险分布
    module_risk = tapd_data.get('module_risk_distribution', {})
    if module_risk:
        st.write("**📦 模块高风险缺陷分布**")
        
        # 转换为表格数据
        module_data = []
        for module, stats in module_risk.items():
            total = stats.get('致命', 0) + stats.get('严重', 0)
            flag = '🔴' if stats.get('致命', 0) > 0 else ('🟠' if stats.get('严重', 0) > 0 else '⚪')
            module_data.append({
                '风险': flag,
                '模块': module,
                '致命': stats.get('致命', 0),
                '严重': stats.get('严重', 0),
                '高风险合计': total
            })
        
        # 按风险数排序
        module_data.sort(key=lambda x: -x['高风险合计'])
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # 柱状图展示
            module_df = pd.DataFrame(module_data)
            fig = px.bar(
                module_df,
                x='模块',
                y=['致命', '严重'],
                title='各模块高风险缺陷分布',
                color_discrete_map={'致命': '#dc3545', '严重': '#ffc107'},
                height=250
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 表格展示
            st.dataframe(
                pd.DataFrame(module_data),
                use_container_width=True,
                hide_index=True
            )

    # 版本风险看板（遗留DI + 新需求转测DI）
    show_version_risk_board(tapd_data)


def show_version_risk_board(tapd_data):
    """展示版本风险看板（遗留DI + 新需求转测DI）"""
    legacy_stats = tapd_data.get('legacy_di_stats', {})
    req_stats = tapd_data.get('requirement_di_stats', {})

    if not legacy_stats:
        return

    st.divider()
    st.subheader("🚨 版本风险看板")

    di_weights = {'致命': 10, '严重': 3, '一般': 1, '轻微': 0.1, '提示': 0.1}
    sev_emojis = {'致命': '🔴', '严重': '🟠', '一般': '⚪', '轻微': '⚪', '提示': '⚪'}

    # ==================== 遗留DI部分 ====================
    st.write("**📊 遗留DI（延期/挂起缺陷）**")

    # 版本节点信息
    milestone = legacy_stats.get('封板日期', '')
    release_date = legacy_stats.get('发布日期', '')
    days_to_deadline = legacy_stats.get('days_to_deadline', 0)
    di_target = legacy_stats.get('di_target', 30)
    di_score = legacy_stats.get('di_score', 0)
    is_over_target = legacy_stats.get('is_over_target', False)

    if milestone:
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("📅 封板日期", milestone)

        with col2:
            if release_date:
                st.metric("🚀 发布日期", release_date)

        with col3:
            if days_to_deadline > 0:
                st.metric("⏰ 距离封板", f"{days_to_deadline}天")
            elif days_to_deadline == 0:
                st.metric("⏰ 距离封板", "今天", delta="⚠️", delta_color="inverse")
            else:
                st.metric("⏰ 已延期", f"{-days_to_deadline}天", delta_color="inverse")

        with col4:
            delta_text = f"超标{round(di_score - di_target, 1)}" if is_over_target else f"剩余{round(di_target - di_score, 1)}"
            st.metric(
                "📊 遗留DI",
                f"{di_score}/{di_target}",
                delta=delta_text,
                delta_color="inverse" if is_over_target else "normal"
            )

        with col5:
            total_legacy = legacy_stats.get('total_legacy', 0)
            st.metric("📦 遗留缺陷", total_legacy)

    # 遗留DI详细分布
    sev_stats = legacy_stats.get('severity_stats', {})
    di_cols = st.columns(5)

    for idx, (sev, emoji) in enumerate(sev_emojis.items()):
        with di_cols[idx]:
            count = sev_stats.get(sev, 0)
            weight = di_weights.get(sev, 0.1)
            di_contribution = round(count * weight, 2)
            st.metric(f"{emoji} {sev}", count, delta=f"DI {di_contribution}")

    # ==================== 新需求转测DI部分 ====================
    st.write("**📈 新需求转测DI（关联需求的缺陷）**")

    if req_stats:
        req_di_score = req_stats.get('di_score', 0)
        total_req_bugs = req_stats.get('total_req_bugs', 0)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("📝 需求缺陷DI", req_di_score)
        with col2:
            st.metric("📦 需求缺陷数", total_req_bugs)

        # 新需求DI详细分布
        req_sev_stats = req_stats.get('severity_stats', {})
        req_di_cols = st.columns(5)

        for idx, (sev, emoji) in enumerate(sev_emojis.items()):
            with req_di_cols[idx]:
                count = req_sev_stats.get(sev, 0)
                weight = di_weights.get(sev, 0.1)
                di_contribution = round(count * weight, 2)
                st.metric(f"{emoji} {sev}", count, delta=f"DI {di_contribution}")

    # 缺陷列表（可选展开）
    with st.expander("🔍 查看缺陷详情"):
        tab1, tab2 = st.tabs(["遗留缺陷", "需求缺陷"])

        with tab1:
            legacy_bugs = legacy_stats.get('legacy_bugs', [])
            if legacy_bugs:
                st.caption(f"共{len(legacy_bugs)}条（custom_field_22为延期到下个迭代或挂起）")
                for bug in legacy_bugs[:10]:
                    severity = bug.get('severity', '')
                    emoji = sev_emojis.get(severity, '⚪')
                    cf22 = bug.get('custom_field_22', '')
                    st.write(f"{emoji} [{bug.get('id', 'N/A')[-7:]}] {bug.get('title', '无标题')[:50]}... ({cf22})")
            else:
                st.info("暂无遗留缺陷")

        with tab2:
            req_bugs = req_stats.get('req_bugs', [])
            if req_bugs:
                st.caption(f"共{len(req_bugs)}条（关联需求不为空，已剔除非问题）")
                for bug in req_bugs[:10]:
                    severity = bug.get('severity', '')
                    emoji = sev_emojis.get(severity, '⚪')
                    story_id = bug.get('story_id', 'N/A')
                    st.write(f"{emoji} [{bug.get('id', 'N/A')[-7:]}] {bug.get('title', '无标题')[:50]}... (需求ID: {story_id})")
            else:
                st.info("暂无需求缺陷")


