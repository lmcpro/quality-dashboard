"""
AI智能分析板块 - AI驱动的质量洞察
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import random

def show_ai_insights(data, ai_analyzer):
    """展示AI智能分析"""
    st.markdown('<div class="section-title">🤖 AI智能分析</div>', unsafe_allow_html=True)

    # AI概览卡片
    st.subheader("📊 AI质量健康度评估")

    # 模拟AI分析结果
    health_score = random.randint(75, 92)
    risk_level = random.choice(["低风险", "中低风险", "中等风险"])
    trend_prediction = random.choice(["向好", "稳定", "需关注"])

    cols = st.columns(4)

    with cols[0]:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "AI健康度评分", 'font': {'size': 16}},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1dd1a1" if health_score >= 85 else "#feca57"},
                'steps': [
                    {'range': [0, 60], 'color': "#ffcccc"},
                    {'range': [60, 75], 'color': "#ffe6cc"},
                    {'range': [75, 85], 'color': "#ffffcc"},
                    {'range': [85, 100], 'color': "#ccffcc"}
                ]
            }
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        st.metric("风险等级", risk_level)
        st.metric("趋势预测", trend_prediction)

    with cols[2]:
        st.metric("需关注问题", random.randint(3, 8))
        st.metric("推荐行动", random.randint(5, 12))

    with cols[3]:
        st.metric("预测下月DI", round(random.uniform(2.5, 5.5), 1))
        st.metric("预测事故数", random.randint(0, 2))

    st.divider()

    # AI预警中心
    st.subheader("⚠️ AI智能预警")

    # 模拟AI生成的预警
    ai_alerts = [
        {
            "level": "🔴 高",
            "type": "趋势异常",
            "content": "检测到近3周缺陷密度持续上升，可能与新功能上线有关",
            "suggestion": "建议加强Code Review，重点关注新增模块",
            "confidence": 87
        },
        {
            "level": "🟡 中",
            "type": "风险预测",
            "content": "根据历史数据，本周有65%概率出现P2级事故",
            "suggestion": "建议提前准备应急预案，加强监控",
            "confidence": 72
        },
        {
            "level": "🟡 中",
            "type": "进度预警",
            "content": "自动化测试覆盖率提升任务进度滞后",
            "suggestion": "建议协调资源或调整里程碑",
            "confidence": 91
        },
        {
            "level": "🟢 低",
            "type": "机会识别",
            "content": "客户A满意度提升明显，建议总结最佳实践",
            "suggestion": "组织经验分享会，推广成功做法",
            "confidence": 85
        }
    ]

    for alert in ai_alerts:
        with st.expander(f"{alert['level']} {alert['type']} (置信度: {alert['confidence']}%)"):
            st.write(f"**洞察:** {alert['content']}")
            st.write(f"**建议:** {alert['suggestion']}")

    st.divider()

    # AI根因分析
    st.subheader("🔍 AI辅助根因分析")

    # 选择分析对象
    analysis_target = st.selectbox(
        "选择分析对象",
        ["接口响应超时问题", "客户C满意度下降", "漏测DI持续超标", "本月事故增加"]
    )

    if analysis_target:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write("**AI分析结果:**")

            # 模拟AI分析输出
            if "接口" in analysis_target:
                root_causes = [
                    ("数据库查询慢", 35),
                    ("缓存策略不当", 28),
                    ("接口设计不合理", 22),
                    ("网络延迟", 15)
                ]
                analysis_text = """
                基于近3个月的数据分析，接口响应超时问题的主要原因分布如上。

                **关键发现:**
                - 85%的超时发生在高峰期(10:00-12:00, 14:00-16:00)
                - 核心问题集中在订单查询接口(占62%)
                - 与数据库慢查询强相关(相关系数0.78)

                **AI建议:**
                1. 优先优化数据库索引
                2. 增加接口限流保护
                3. 优化缓存策略，提高命中率
                """
            elif "客户C" in analysis_target:
                root_causes = [
                    ("交付延期", 40),
                    ("需求理解偏差", 30),
                    ("沟通频率低", 20),
                    ("质量问题", 10)
                ]
                analysis_text = """
                通过NLP分析客户反馈和会议纪要，识别出满意度下降的核心因素。

                **关键发现:**
                - 近2个月交付延期3次，超出SLA承诺
                - 需求评审阶段发现率低，后期变更频繁
                - 客户期望与实际交付存在认知差距

                **AI建议:**
                1. 建立周报机制，提升沟通频率
                2. 加强需求澄清和确认环节
                3. 设置缓冲期，避免承诺过度
                """
            else:
                root_causes = [
                    ("测试覆盖不足", 38),
                    ("需求变更频繁", 25),
                    ("用例设计缺陷", 20),
                    ("环境差异", 17)
                ]
                analysis_text = f"""
                AI模型基于历史数据识别出影响{analysis_target}的主要因素。

                **关键发现:**
                - 回归测试覆盖率低于目标15个百分点
                - 边界条件测试用例占比不足20%
                - 与需求变更频率呈正相关(相关系数0.65)

                **AI建议:**
                1. 增加边界条件测试用例
                2. 引入探索性测试
                3. 建立变更影响分析流程
                """

            st.markdown(analysis_text)

        with col2:
            # 根因分布饼图
            causes, values = zip(*root_causes)
            fig = px.pie(
                values=values,
                names=causes,
                title="根因分布",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # AI预测与建议
    st.subheader("📈 AI预测与智能建议")

    tabs = st.tabs(["趋势预测", "资源优化", "改进建议"])

    with tabs[0]:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**下季度缺陷密度预测**")

            # 预测数据
            months = ['当前', '下月', '+2月', '+3月']
            actual = [5.2, None, None, None]
            predicted = [5.2, 4.8, 4.5, 4.2]
            upper_bound = [5.2, 5.5, 5.3, 5.0]
            lower_bound = [5.2, 4.1, 3.7, 3.4]

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=months, y=upper_bound,
                fill=None, mode='lines',
                line_color='rgba(0,100,80,0.2)',
                showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=months, y=lower_bound,
                fill='tonexty', mode='lines',
                line_color='rgba(0,100,80,0.2)',
                name='置信区间'
            ))

            fig.add_trace(go.Scatter(
                x=months, y=predicted,
                mode='lines+markers',
                line=dict(color='blue', dash='dash'),
                name='AI预测'
            ))

            fig.update_layout(
                height=300,
                yaxis_title='缺陷密度',
                showlegend=True
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.write("**预测说明:**")
            st.info("""
            📊 **模型说明:**
            - 基于LSTM神经网络
            - 训练数据: 24个月历史数据
            - 准确率: 87%

            🔮 **预测结论:**
            - 下季度缺陷密度预计下降19%
            - 主要得益于自动化测试覆盖率提升
            - 建议关注新功能引入的质量风险
            """)

    with tabs[1]:
        st.write("**AI资源优化建议**")

        resource_data = pd.DataFrame({
            '团队': ['测试组A', '测试组B', '研发组C', 'QA组'],
            '当前负载': [95, 78, 88, 72],
            '建议负载': [85, 85, 85, 85],
            '优化建议': ['增加1人', '可承担更多', '保持现状', '可支持其他组']
        })

        st.dataframe(resource_data, use_container_width=True, hide_index=True)

        st.success("""
        💡 **AI分析结果:**
        - 测试组A处于过载状态，建议增加人力
        - 测试组B有20%的产能可调配
        - QA组可支援测试组A的评审工作
        - 预计优化后可提升整体效率15%
        """)

    with tabs[2]:
        st.write("**TOP3 优先改进建议**")

        improvements = [
            {
                "priority": 1,
                "title": "建立接口性能基线监控",
                "impact": "预计减少30%超时问题",
                "effort": "2周",
                "roi": "高"
            },
            {
                "priority": 2,
                "title": "优化需求评审流程",
                "impact": "预计减少40%后期变更",
                "effort": "1个月",
                "roi": "高"
            },
            {
                "priority": 3,
                "title": "引入AI辅助测试用例生成",
                "impact": "预计提升覆盖率20%",
                "effort": "2个月",
                "roi": "中"
            }
        ]

        for imp in improvements:
            with st.container():
                cols = st.columns([1, 3, 2, 1, 1])
                with cols[0]:
                    st.markdown(f"**#{imp['priority']}**")
                with cols[1]:
                    st.write(imp['title'])
                with cols[2]:
                    st.caption(f"预期效果: {imp['impact']}")
                with cols[3]:
                    st.caption(f"投入: {imp['effort']}")
                with cols[4]:
                    st.caption(f"ROI: {imp['roi']}")
                st.divider()

    st.divider()

    # AI问答助手
    st.subheader("💬 质量AI助手")

    st.info("🤖 我是你的质量AI助手，可以帮你分析质量数据、预测趋势、提供改进建议。")

    user_question = st.text_input("输入你的质量问题，例如：'为什么最近缺陷增加了？' 或 '如何提升客户满意度？'")

    if user_question:
        with st.spinner("AI正在分析..."):
            # 模拟AI回答
            responses = {
                "缺陷": """
                **分析结果:**

                基于最近3个月数据分析，缺陷增加的主要原因有：

                1. **新功能上线 (贡献度40%)** - 4月份上线3个新模块，历史数据显示新模块首月缺陷率通常高出40%
                2. **人员变动 (贡献度30%)** - 2名资深开发调岗，新人熟悉期导致代码质量波动
                3. **需求变更 (贡献度30%)** - 本月需求变更次数比上月增加50%

                **建议行动:**
                - 加强新模块Code Review
                - 安排导师帮带新人
                - 建立需求变更影响评估流程
                """,
                "客户": """
                **分析结果:**

                提升客户满意度的关键因素分析：

                1. **准时交付 (权重35%)** - 当前准时率82%，目标90%
                2. **质量稳定 (权重30%)** - 生产事故直接影响满意度评分
                3. **沟通透明 (权重20%)** - 及时同步进展和风险
                4. **响应速度 (权重15%)** - 问题处理时效

                **TOP3 改进建议:**
                1. 建立里程碑预警机制，提前2周识别延期风险
                2. 每周发送项目进展简报给客户
                3. 成立客户成功小组，主动收集反馈
                """,
                "默认": f"""
                **关于"{user_question}"的分析:**

                我已综合分析当前质量数据，主要发现：

                1. **现状评估** - 整体质量指标处于"良好"水平，但有2个领域需关注
                2. **趋势判断** - 下月预计保持稳定，建议重点关注自动化测试覆盖
                3. **风险识别** - 当前识别出3个中等风险点，建议制定缓解措施

                如需更深入分析，建议：
                - 查看"质量工作"板块的具体指标
                - 关注"AI智能预警"中的风险提示
                - 参考"改进建议"中的优化方案
                """
            }

            # 根据关键词选择回答
            answer = responses["默认"]
            for keyword in ["缺陷", "bug", "问题", "质量下降"]:
                if keyword in user_question.lower():
                    answer = responses["缺陷"]
                    break
            for keyword in ["客户", "满意", "反馈"]:
                if keyword in user_question.lower():
                    answer = responses["客户"]
                    break

            st.markdown(answer)
