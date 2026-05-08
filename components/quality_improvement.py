"""
质量改进板块 - TOP问题、事故复盘、举一反三
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_quality_improvement(data):
    """展示质量改进板块"""
    st.markdown('<div class="section-title">🔧 质量改进</div>', unsafe_allow_html=True)

    # TOP质量问题
    st.subheader("🔝 TOP质量问题")

    for issue in data['top_issues']:
        with st.expander(f"#{issue['rank']} {issue['issue']} - {issue['status']} ({issue['progress']}%)"):
            cols = st.columns([2, 1, 1])
            with cols[0]:
                st.write(f"**负责人:** {issue['owner']}")
                if 'note' in issue:
                    st.info(f"💡 {issue['note']}")
            with cols[1]:
                st.metric("整体进度", f"{issue['progress']}%")
            with cols[2]:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=issue['progress'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#1dd1a1" if issue['progress'] == 100 else "#1f77b4"},
                        'steps': [
                            {'range': [0, 33], 'color': "#ffcccc"},
                            {'range': [33, 66], 'color': "#ffffcc"},
                            {'range': [66, 100], 'color': "#ccffcc"}
                        ]
                    }
                ))
                fig.update_layout(height=150, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)

            # 子任务
            if 'subtasks' in issue:
                st.write("**子任务进展:**")
                for subtask in issue['subtasks']:
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
                    with col1:
                        st.write(f"• {subtask['name']}")
                        st.caption(subtask['desc'])
                    with col2:
                        st.progress(subtask['progress'] / 100, text=f"进度: {subtask['progress']}%")
                    with col3:
                        st.caption(f"截止: {subtask['deadline']}")
                    with col4:
                        status_color = {
                            '已完成': '🟢',
                            '进行中': '🔵',
                            '待环境部署': '🟡',
                            '环境部署中': '🟡',
                            '已运行': '🟢'
                        }.get(subtask['status'], '⚪')
                        st.write(f"{status_color} {subtask['status']}")
                    st.divider()

    # 问题进度概览
    st.subheader("📊 TOP问题进度概览")
    progress_cols = st.columns(len(data['top_issues']))
    for col, issue in zip(progress_cols, data['top_issues']):
        with col:
            st.write(f"**{issue['issue'][:10]}...**")
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=issue['progress'],
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#1dd1a1" if issue['progress'] >= 90 else "#1f77b4"},
                    'steps': [
                        {'range': [0, 33], 'color': "#ffcccc"},
                        {'range': [33, 66], 'color': "#ffffcc"},
                        {'range': [66, 100], 'color': "#ccffcc"}
                    ]
                }
            ))
            fig.update_layout(height=180, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"负责人: {issue['owner']}")

    st.divider()

    # 事故复盘
    st.subheader("📝 事故复盘闭环跟进")

    for accident in data['accident_reviews']:
        severity_color = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "P3": "🟢"}.get(accident['severity'], "⚪")
        with st.expander(f"{severity_color} {accident['id']}: {accident['title']} - {accident['status']}"):
            cols = st.columns([1, 1, 1, 1])
            with cols[0]:
                st.write(f"**发生时间:** {accident['date']}")
                st.write(f"**严重程度:** {accident['severity']}")
            with cols[1]:
                st.write(f"**影响范围:** {accident['scope']}")
                st.write(f"**经验总结:** {accident['lessons']}条")
            with cols[2]:
                st.metric("闭环进度", f"{accident['progress']}%")
            with cols[3]:
                st.write(f"**预计闭环:** {accident['closure_date']}")

            # 进度条
            st.progress(accident['progress'] / 100, text=f"复盘进度: {accident['progress']}%")

            # 详细复盘事项
            if 'details' in accident:
                st.write("**📋 复盘改进事项:**")
                for detail in accident['details']:
                    with st.container():
                        st.write(f"**{detail['category']}**")
                        for item in detail['items']:
                            col1, col2, col3 = st.columns([6, 1, 1])
                            with col1:
                                st.write(f"  • {item['desc']}")
                            with col2:
                                status_emoji = "✅" if item['status'] == "已完成" else "⏳"
                                st.write(f"{status_emoji} {item['status']}")
                            with col3:
                                st.caption(f"截止: {item['due']}")
                        st.divider()

    # 事故复盘统计
    st.subheader("📈 事故复盘统计")
    accident_df = pd.DataFrame(data['accident_reviews'])

    cols = st.columns(3)
    with cols[0]:
        avg_progress = accident_df['progress'].mean()
        st.metric("平均闭环进度", f"{avg_progress:.0f}%")
    with cols[1]:
        total_lessons = accident_df['lessons'].sum()
        st.metric("经验总结总数", total_lessons)
    with cols[2]:
        pending_count = len([a for a in data['accident_reviews'] if a['progress'] < 100])
        st.metric("待闭环事故", pending_count)

    # 状态分布图
    status_cols = st.columns(2)
    with status_cols[0]:
        status_counts = accident_df['status'].value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="事故复盘状态分布",
            color_discrete_sequence=['#1dd1a1', '#feca57', '#ff6b6b']
        )
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)

    with status_cols[1]:
        fig = px.bar(
            x=accident_df['id'],
            y=accident_df['progress'],
            color=accident_df['progress'],
            color_continuous_scale=['#ff6b6b', '#feca57', '#1dd1a1'],
            labels={'x': '事故编号', 'y': '闭环进度%'},
            title="各事故复盘进度"
        )
        fig.update_layout(height=250, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 举一反三
    st.subheader("💡 举一反三改进行动")

    fanyi_data = data['举一反三']

    # 总体统计
    cols = st.columns(4)
    with cols[0]:
        st.metric("总任务数", fanyi_data['total'])
    with cols[1]:
        st.metric("已完成", fanyi_data['completed'],
                 delta=f"{fanyi_data['completed']/fanyi_data['total']*100:.0f}%")
    with cols[2]:
        st.metric("进行中", fanyi_data['pending'])
    with cols[3]:
        completion_rate = fanyi_data['completed'] / fanyi_data['total'] * 100
        st.metric("整体闭环率", f"{completion_rate:.0f}%")

    # 分项目统计
    st.write("**分项目统计:**")
    if 'by_project' in fanyi_data:
        project_cols = st.columns(len(fanyi_data['by_project']))
        for col, project in zip(project_cols, fanyi_data['by_project']):
            with col:
                st.write(f"**{project['project']}**")
                st.caption(project['desc'])
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=project['rate'],
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"闭环率", 'font': {'size': 14}},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "#1dd1a1" if project['rate'] == 100 else "#1f77b4"},
                        'steps': [
                            {'range': [0, 30], 'color': "#ffcccc"},
                            {'range': [30, 60], 'color': "#ffffcc"},
                            {'range': [60, 100], 'color': "#ccffcc"}
                        ]
                    }
                ))
                fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)
                st.caption(f"{project['completed']}/{project['total']} 完成")

    # 举一反三行动清单
    st.write("**举一反三行动清单:**")
    fanyi_df = pd.DataFrame(fanyi_data['items'])
    st.dataframe(
        fanyi_df[['source', 'action', 'scope', 'status', 'progress']].rename(columns={
            'source': '来源',
            'action': '改进行动',
            'scope': '影响范围',
            'status': '状态',
            'progress': '进度%'
        }),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # 持续改进任务
    st.subheader("🚀 持续改进任务")

    tasks_df = pd.DataFrame(data['ongoing_tasks'])

    for _, task in tasks_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
        with col1:
            st.write(f"**{task['name']}**")
            if 'desc' in task:
                st.caption(task['desc'])
        with col2:
            st.caption(f"负责人: {task['owner']}")
        with col3:
            st.progress(task['progress'] / 100, text=f"进度: {task['progress']}%")
        with col4:
            st.caption(f"截止: {task['due']}")
