"""
QA事项板块 - QA检查情况、问题闭环
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_qa_items(data):
    """展示QA事项板块"""
    st.markdown('<div class="section-title">✅ QA事项</div>', unsafe_allow_html=True)

    # QA检查项目
    st.subheader("📋 QA检查情况")

    qa_checks_df = pd.DataFrame(data['qa_checks'])

    cols = st.columns([2, 3])

    with cols[0]:
        # QA评分雷达图
        check_items = data['check_items']
        categories = list(check_items.keys())
        scores = [item['score'] for item in check_items.values()]

        fig = go.Figure(data=go.Scatterpolar(
            r=scores + [scores[0]],  # 闭合
            theta=categories + [categories[0]],
            fill='toself',
            name='当前得分'
        ))

        fig.add_trace(go.Scatterpolar(
            r=[90, 90, 90, 90, 90, 90],
            theta=categories + [categories[0]],
            fill='toself',
            name='目标线',
            line=dict(dash='dash', color='red'),
            fillcolor='rgba(255,0,0,0.1)'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        # 检查详情
        st.dataframe(
            qa_checks_df[['project', 'check_date', 'score', 'status', 'issues']].rename(columns={
                'project': '项目名称',
                'check_date': '检查日期',
                'score': '评分',
                'status': '状态',
                'issues': '问题数'
            }),
            use_container_width=True,
            hide_index=True
        )

    # 各检查项详细
    st.subheader("🔍 检查项详细")

    check_items_df = pd.DataFrame([
        {'检查项': k, '得分': v['score'], '检查数': v['items'], '通过数': v['passed'], '通过率': f"{v['passed']/v['items']*100:.0f}%"}
        for k, v in check_items.items()
    ])

    cols = st.columns([3, 2])

    with cols[0]:
        fig = px.bar(
            check_items_df,
            x='检查项',
            y='得分',
            color='得分',
            color_continuous_scale=['#ff6b6b', '#feca57', '#1dd1a1'],
            range_color=[60, 100],
            text='通过率',
            height=300
        )
        fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="目标线")
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        st.dataframe(
            check_items_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 问题闭环
    st.subheader("🔄 问题闭环情况")

    closure_data = data['issue_closure']

    cols = st.columns(4)

    with cols[0]:
        st.metric("问题总数", closure_data['total_issues'])
    with cols[1]:
        st.metric("已闭环", closure_data['closed'],
                 delta=f"{closure_data['closed']/closure_data['total_issues']*100:.0f}%")
    with cols[2]:
        st.metric("闭环率", f"{closure_data['closing_rate']}%")
    with cols[3]:
        st.metric("平均闭环天数", closure_data['avg_closure_days'])

    # 闭环趋势
    st.write("**问题闭环情况:**")

    closure_fig = go.Figure()

    closure_fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=closure_data['closing_rate'],
        domain={'x': [0, 0.5], 'y': [0, 1]},
        title={'text': "闭环率", 'font': {'size': 20}},
        delta={'reference': 80},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#1dd1a1"},
            'steps': [
                {'range': [0, 60], 'color': "#ffcccc"},
                {'range': [60, 80], 'color': "#ffe6cc"},
                {'range': [80, 90], 'color': "#ffffcc"},
                {'range': [90, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))

    closure_fig.add_trace(go.Indicator(
        mode="number+delta",
        value=closure_data['overdue_issues'],
        domain={'x': [0.6, 1], 'y': [0.5, 1]},
        title={'text': "逾期问题数"},
        delta={'reference': 10}
    ))

    closure_fig.add_trace(go.Indicator(
        mode="number+delta",
        value=closure_data['avg_closure_days'],
        domain={'x': [0.6, 1], 'y': [0, 0.5]},
        title={'text': "平均闭环天数"},
        delta={'reference': 7}
    ))

    closure_fig.update_layout(height=300)
    st.plotly_chart(closure_fig, use_container_width=True)

    st.divider()

    # QA工作计划
    st.subheader("📅 QA工作计划")

    plans_df = pd.DataFrame(data['qa_plans'])

    for _, plan in plans_df.iterrows():
        col1, col2, col3 = st.columns([2, 2, 3])

        with col1:
            st.write(f"**{plan['task']}**")
            st.caption(f"负责人: {plan['owner']}")

        with col2:
            st.caption(f"时间: {plan['start']} 至 {plan['end']}")

        with col3:
            st.progress(plan['progress'] / 100, text=f"进度: {plan['progress']}%")
