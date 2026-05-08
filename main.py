"""
质量可视化平台 - 快速原型
作者: Claude Code
功能: 质量工作、质量改进、版本质量、QA事项四大板块可视化
"""

import streamlit as st
import os

# 检查是否为编辑模式（本地运行）或只读模式（在线部署）
# 优先级: secrets.toml > 环境变量 > 默认(只读)
try:
    EDIT_MODE = st.secrets.get('EDIT_MODE', 'false').lower() == 'true'
except:
    EDIT_MODE = os.environ.get('EDIT_MODE', 'false').lower() == 'true'

# 自动检测是否在 Streamlit Cloud 上运行
try:
    IS_CLOUD = st.secrets.get('STREAMLIT_SHARING', '') != ''
except:
    IS_CLOUD = os.environ.get('STREAMLIT_SHARING_MODE', '') != ''
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# 设置页面配置
st.set_page_config(
    page_title="质量可视化平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 引入自定义组件
from components.quality_work import show_quality_work
from components.quality_improvement import show_quality_improvement
from components.version_quality import show_version_quality
from components.qa_items import show_qa_items
from components.ai_insights import show_ai_insights
from components.data_manager import show_data_manager, load_data_from_file
from utils.data_generator import generate_all_data
from utils.ai_analyzer import AIAnalyzer

# 初始化会话状态 - 优先从文件加载数据
if 'data' not in st.session_state:
    # 尝试从文件加载，如果不存在则生成默认数据
    file_data = load_data_from_file()
    if file_data:
        st.session_state.data = file_data
    else:
        st.session_state.data = generate_all_data()
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()
if 'ai_analyzer' not in st.session_state:
    st.session_state.ai_analyzer = AIAnalyzer()

# CSS样式美化
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 50%, #f0f2f6 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .status-good {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-danger {
        color: #dc3545;
        font-weight: bold;
    }
    .update-time {
        text-align: right;
        color: #6c757d;
        font-size: 0.8rem;
    }
    .section-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# 侧边栏导航
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/quality.png", width=80)
    st.title("质量可视化平台")

    # 导航菜单 - 综合大盘放在第一位
    menu_items = ["📈 综合大盘", "📊 质量工作", "🔧 质量改进", "📱 版本质量", "✅ QA事项", "🤖 AI智能分析"]

    # 只在编辑模式下显示数据管理
    if EDIT_MODE:
        menu_items.append("⚙️ 数据管理")
        default_index = 0
    else:
        default_index = 0

    selected_section = st.radio(
        "选择板块",
        menu_items,
        index=default_index
    )

    # 显示当前模式
    if EDIT_MODE:
        st.success("✏️ 编辑模式")
    else:
        st.info("👁️ 只读模式")

    st.divider()

    # 数据刷新控制
    st.subheader("⚙️ 控制面板")
    auto_refresh = st.toggle("自动刷新数据", value=False)
    if auto_refresh:
        refresh_interval = st.slider("刷新间隔(秒)", 10, 300, 60)

    if st.button("🔄 立即刷新", use_container_width=True):
        st.session_state.data = generate_all_data()
        st.session_state.last_update = datetime.now()
        st.rerun()

    st.divider()
    st.caption(f"⏱️ 最后更新: {st.session_state.last_update.strftime('%H:%M:%S')}")

# 主标题
st.markdown('<div class="main-header">📊 质量可视化智能平台</div>', unsafe_allow_html=True)

# 自动刷新逻辑
if auto_refresh:
    time.sleep(0.1)  # 防止过于频繁的刷新
    if (datetime.now() - st.session_state.last_update).seconds > refresh_interval:
        st.session_state.data = generate_all_data()
        st.session_state.last_update = datetime.now()
        st.rerun()

# 定义综合大盘函数（必须在调用之前定义）
def show_dashboard(data):
    """综合大盘视图"""
    st.markdown('<div class="section-title">📈 质量综合大盘</div>', unsafe_allow_html=True)

    # 关键指标卡片
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        qw_data = data['quality_work']
        achievement = qw_data['annual_goals']['overall_achievement']
        st.metric(
            label="年度质量目标达成率",
            value=f"{achievement}%",
            delta=f"{achievement - 85:.1f}%" if achievement != 85 else None
        )
        if achievement >= 90:
            st.markdown('<span class="status-good">● 优秀</span>', unsafe_allow_html=True)
        elif achievement >= 80:
            st.markdown('<span class="status-warning">● 良好</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-danger">● 需改进</span>', unsafe_allow_html=True)

    with col2:
        customer_score = qw_data['customer_quality']['avg_score']
        st.metric(
            label="客户质量评分",
            value=f"{customer_score}",
            delta=f"{customer_score - 85:.1f}"
        )
        if customer_score >= 90:
            st.markdown('<span class="status-good">● 优秀</span>', unsafe_allow_html=True)
        elif customer_score >= 80:
            st.markdown('<span class="status-warning">● 良好</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-danger">● 需改进</span>', unsafe_allow_html=True)

    with col3:
        di_rate = qw_data['defect_escape']['current_di']
        di_target = qw_data['defect_escape']['target_di']
        st.metric(
            label="商用版本漏测DI",
            value=f"{di_rate}",
            delta=f"目标<{di_target}",
            delta_color="inverse"
        )
        if di_rate < di_target:
            st.markdown('<span class="status-good">● 达标</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-danger">● 超标</span>', unsafe_allow_html=True)

    with col4:
        downtime = qw_data['accident_rate'].get('downtime_minutes', 0)
        total_systems = qw_data['accident_rate'].get('total_systems', 3545)
        st.metric(
            label="业务停机时长",
            value=f"{downtime}分钟",
            delta="2例P1事故"
        )
        if downtime <= 0:
            st.markdown('<span class="status-good">● 达标</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-warning">● 说明详见板块</span>', unsafe_allow_html=True)

    st.divider()

    # 第二行：现网问题和事故情况
    st.subheader("📊 本周质量动态")
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**🌐 现网问题概况**")
        prod_issues = qw_data.get('production_issues', {})
        issues_list = prod_issues.get('issues', [])

        if issues_list:
            # 获取最新周次
            latest_week = max([i.get('周次', '') for i in issues_list], default='')
            week_issues = [i for i in issues_list if i.get('周次') == latest_week]

            if week_issues:
                total = len(week_issues)
                key_customer = len([i for i in week_issues if i.get('问题分类') == '重点客户问题'])
                severe = len([i for i in week_issues if i.get('严重程度') == '严重'])
                prod_env = len([i for i in week_issues if '生产' in i.get('环境', '') or '准生产' in i.get('环境', '')])

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("新增问题", total)
                with c2:
                    st.metric("重点客户", key_customer)
                with c3:
                    st.metric("严重问题", severe)
                with c4:
                    st.metric("生产环境", prod_env)

                # 重点客户列表
                key_customers = {}
                for i in week_issues:
                    if i.get('问题分类') == '重点客户问题':
                        cust = i.get('客户名称', '')
                        if cust:
                            key_customers[cust] = key_customers.get(cust, 0) + 1

                if key_customers:
                    st.caption(f"重点客户: {', '.join([f'{k}({v})' for k, v in key_customers.items()])}")
            else:
                st.info("暂无本周现网问题数据")
        else:
            st.info("暂无现网问题数据")

    with col_right:
        st.markdown("**⚠️ 事故情况**")
        accident_rate = qw_data.get('accident_rate', {})
        accidents = accident_rate.get('accidents', [])

        if accidents:
            # 获取本月事故
            current_month = datetime.now().strftime('%Y-%m')
            month_accidents = [a for a in accidents if current_month in a.get('发生月份', '')]

            if month_accidents:
                total_accidents = len(month_accidents)
                p0_p1 = len([a for a in month_accidents if a.get('事故等级') in ['P0', 'P1']])
                recovered = len([a for a in month_accidents if a.get('是否恢复') == '已恢复'])
                total_downtime = sum([a.get('业务停机时长', 0) for a in month_accidents])

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("本月事故", total_accidents)
                with c2:
                    st.metric("P0/P1事故", p0_p1)
                with c3:
                    st.metric("已恢复", recovered)
                with c4:
                    st.metric("停机时长", f"{total_downtime}分")

                # 显示最近事故
                recent = month_accidents[-1] if month_accidents else None
                if recent:
                    st.caption(f"最近: {recent.get('客户名称', '')} - {recent.get('事故等级', '')} - {recent.get('是否恢复', '')}")
            else:
                st.info("暂无本月事故数据")
        else:
            st.info("暂无事故数据")

    # 事故汇总表
    st.subheader("📋 事故明细汇总")
    accident_rate = qw_data.get('accident_rate', {})
    accidents = accident_rate.get('accidents', [])

    if accidents:
        # 获取本月事故
        current_month = datetime.now().strftime('%Y-%m')
        month_accidents = [a for a in accidents if current_month in a.get('发生月份', '')]

        if month_accidents:
            # 转换为DataFrame展示
            df_accidents = pd.DataFrame(month_accidents)
            display_cols = ['发生月份', '客户名称', '事故等级', '问题单号', '业务停机时长', '版本', '是否恢复', '事故定性']
            available_cols = [c for c in display_cols if c in df_accidents.columns]
            st.dataframe(df_accidents[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("暂无本月事故明细数据")
    else:
        st.info("暂无事故明细数据")

    st.divider()

    # 趋势图 - 三列布局
    col_prod, col_trend, col_task = st.columns(3)

    with col_prod:
        st.subheader("📊 现网问题周趋势")
        prod_trend = qw_data.get('production_issues_trend', [])
        if prod_trend:
            prod_trend_df = pd.DataFrame(prod_trend)
            if not prod_trend_df.empty and '周次' in prod_trend_df.columns:
                fig_prod = go.Figure()
                fig_prod.add_trace(go.Scatter(
                    x=prod_trend_df['周次'],
                    y=prod_trend_df['问题数'],
                    mode='lines+markers',
                    name='问题数',
                    line=dict(color='#ff6b6b', width=2),
                    marker=dict(size=8)
                ))
                fig_prod.update_layout(
                    height=350,
                    template='plotly_white',
                    margin=dict(l=10, r=10, t=30, b=10),
                    yaxis_title='问题数',
                    xaxis_title='周次'
                )
                st.plotly_chart(fig_prod, use_container_width=True)

                # 显示最新周数据
                latest = prod_trend_df.iloc[-1] if not prod_trend_df.empty else None
                if latest is not None:
                    st.caption(f"最新: {latest.get('周次', '')} 新增 {latest.get('问题数', 0)} 个问题")
            else:
                st.info("暂无趋势数据")
        else:
            st.info("暂无现网问题趋势数据，请在数据管理中导入")

    with col_trend:
        st.subheader("📉 质量指标趋势")
        trend_data = qw_data.get('trend_data', [])
        if isinstance(trend_data, list):
            trend_df = pd.DataFrame(trend_data)
        else:
            trend_df = trend_data

        if not trend_df.empty and 'month' in trend_df.columns:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=trend_df['month'], y=trend_df['defect_density'],
                mode='lines+markers', name='缺陷密度'
            ))
            fig.add_trace(go.Scatter(
                x=trend_df['month'], y=trend_df['test_coverage'],
                mode='lines+markers', name='测试覆盖率'
            ))
            fig.add_trace(go.Scatter(
                x=trend_df['month'], y=trend_df['automation_rate'],
                mode='lines+markers', name='自动化率'
            ))
            fig.update_layout(height=350, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无趋势数据")

    with col_task:
        st.subheader("🎯 TOP质量事项进展")
        qi_data = data.get('quality_improvement', {})
        top_issues = qi_data.get('top_issues', {})

        if isinstance(top_issues, dict) and top_issues:
            # 获取汇总表数据
            summary = top_issues.get('summary', [])
            if summary:
                for item in summary[:3]:
                    st.write(f"**{item.get('事项名称', '')}**")
                    progress_str = item.get('当前进度', '0%').replace('%', '')
                    try:
                        progress = int(progress_str)
                    except:
                        progress = 0
                    st.progress(progress / 100)
                    st.caption(f"进度: {item.get('当前进度', '0%')} | 负责人: {item.get('负责人', '')}")
            else:
                st.info("暂无TOP事项数据")
        else:
            st.info("暂无TOP事项数据")

    st.divider()

    # 风险预警区
    st.subheader("⚠️ 质量风险预警")
    risks = data['version_quality']['risks']

    risk_cols = st.columns(len(risks))
    for idx, (col, risk) in enumerate(zip(risk_cols, risks)):
        with col:
            severity_color = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(risk['severity'], "⚪")
            st.info(f"{severity_color} **{risk['title']}**\n\n风险等级: {risk['severity']}\n\n影响范围: {risk['impact']}")

# 根据选择显示不同板块
data = st.session_state.data

if selected_section == "📈 综合大盘":
    show_dashboard(data)
elif selected_section == "📊 质量工作":
    show_quality_work(data['quality_work'])
elif selected_section == "🔧 质量改进":
    show_quality_improvement(data['quality_improvement'], data.get('quality_work', {}))
elif selected_section == "📱 版本质量":
    show_version_quality()
elif selected_section == "✅ QA事项":
    show_qa_items(data['qa_items'])
elif selected_section == "🤖 AI智能分析":
    show_ai_insights(data, st.session_state.ai_analyzer)
elif selected_section == "⚙️ 数据管理":
    show_data_manager()

# 页脚
st.divider()
st.caption("🤖 本系统由AI辅助生成 | 数据每小时自动刷新 | 质量问题请联系质量部")
