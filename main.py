"""
质量可视化平台 - 快速原型
作者: Claude Code
功能: 质量工作、质量改进、版本质量、QA事项四大板块可视化
"""

import streamlit as st
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

    # 导航菜单
    selected_section = st.radio(
        "选择板块",
        ["📊 质量工作", "🔧 质量改进", "📱 版本质量", "✅ QA事项", "🤖 AI智能分析", "📈 综合大盘", "⚙️ 数据管理"],
        index=5
    )

    st.divider()

    # 数据刷新控制
    st.subheader("⚙️ 控制面板")
    auto_refresh = st.toggle("自动刷新数据", value=True)
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

    # 趋势图
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📉 质量指标趋势")
        trend_df = qw_data['trend_data']
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

    with col_right:
        st.subheader("🎯 本月改进任务进展")
        improvement_data = data['quality_improvement']
        tasks = improvement_data['ongoing_tasks']

        for task in tasks[:3]:
            progress = task['progress']
            st.write(f"**{task['name']}**")
            st.progress(progress / 100)
            st.caption(f"进度: {progress}% | 负责人: {task['owner']}")

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

if selected_section == "📊 质量工作":
    show_quality_work(data['quality_work'])
elif selected_section == "🔧 质量改进":
    show_quality_improvement(data['quality_improvement'])
elif selected_section == "📱 版本质量":
    show_version_quality()
elif selected_section == "✅ QA事项":
    show_qa_items(data['qa_items'])
elif selected_section == "🤖 AI智能分析":
    show_ai_insights(data, st.session_state.ai_analyzer)
elif selected_section == "📈 综合大盘":
    show_dashboard(data)
elif selected_section == "⚙️ 数据管理":
    show_data_manager()

# 页脚
st.divider()
st.caption("🤖 本系统由AI辅助生成 | 数据每小时自动刷新 | 质量问题请联系质量部")
