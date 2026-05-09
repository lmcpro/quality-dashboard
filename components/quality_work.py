"""
质量工作板块 - 年度目标、客户质量、漏测DI、事故率
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def show_quality_work(data):
    """展示质量工作板块"""
    st.markdown('<div class="section-title">📊 质量工作</div>', unsafe_allow_html=True)

    # 年度质量目标达成情况
    st.subheader("🎯 年度质量目标达成情况")

    goals = data['annual_goals']
    quarter = goals.get('quarter', 'Q1')

    cols = st.columns([1, 3])

    with cols[0]:
        # 总体达成率仪表盘
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=goals['overall_achievement'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"{quarter}总体达成率", 'font': {'size': 20}},
            delta={'reference': 90},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#1dd1a1" if goals['overall_achievement'] >= 90 else "#1f77b4"},
                'steps': [
                    {'range': [0, 60], 'color': "#ffcccc"},
                    {'range': [60, 80], 'color': "#ffe6cc"},
                    {'range': [80, 90], 'color': "#ffffcc"},
                    {'range': [90, 100], 'color': "#ccffcc"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        # 目标分类展示
        categories = goals['categories']

        # 基础业绩
        st.write("**📌 一、基础业绩 (权重90%)**")
        base_performance = categories['基础业绩']['items']

        for item in base_performance:
            if item['name'] == '漏测DI':
                st.write(f"**1. 漏测DI (权重{item['weight']}) - {item['status']}**")
                for target in item['targets']:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.write(f"  • {target['name']}")
                    with col2:
                        st.caption(f"目标: {target['target']}")
                    with col3:
                        st.caption(f"实际: {target['actual']}")
                    with col4:
                        st.write(target['status'])

                # 显示重点项目DI详情
                if 'details' in item:
                    st.caption("**重点项目DI详情:**")
                    detail_cols = st.columns(3)
                    for idx, (project, detail) in enumerate(item['details'].items()):
                        with detail_cols[idx]:
                            st.metric(
                                label=project,
                                value=detail['actual'],
                                delta=f"目标: {detail['target']}"
                            )

            elif item['name'] == '事故率':
                st.write(f"**2. 事故率 (权重{item['weight']}) - {item['status']}**")
                for target in item['targets']:
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    with col1:
                        st.write(f"  • {target['name']}")
                    with col2:
                        st.caption(f"目标: {target['target']}")
                    with col3:
                        st.caption(f"实际: {target['actual']}")
                    with col4:
                        st.write(target['status'])

                # 显示系统数量
                if 'systems' in item:
                    sys_cols = st.columns(2)
                    with sys_cols[0]:
                        st.metric("G100上线套数", item['systems']['上线'])
                    with sys_cols[1]:
                        st.metric("割接套数", item['systems']['割接'])

                # 显示说明
                if 'note' in item:
                    st.info(f"💡 **说明**: {item['note']}")

            elif item['name'] == '重点项目':
                st.write(f"**3. 重点项目 (权重{item['weight']}) - {item['status']}**")
                for project in item['projects']:
                    if isinstance(project, dict) and 'metrics' in project:
                        with st.expander(f"📁 {project['name']} - {project['status']}"):
                            for metric in project['metrics']:
                                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                                with col1:
                                    st.write(f"  • {metric['name']}")
                                with col2:
                                    st.caption(f"目标: {metric['target']}")
                                with col3:
                                    st.caption(f"实际: {metric['actual']}")
                                with col4:
                                    st.write(metric['status'])
                    else:
                        st.caption(f"  • {project['name']}: {project['requirement']} - {project['status']}")

        # 组织成长
        st.write("**📌 二、组织成长 (权重10%)**")
        org_growth = categories['组织成长']['items'][0]
        st.write(f"**质量团队建设 (权重{org_growth['weight']}) - {org_growth['status']}**")
        for target in org_growth['targets']:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.write(f"  • {target['name']}")
            with col2:
                st.caption(f"目标: {target['target']}")
            with col3:
                st.caption(f"实际: {target['actual']}")
            with col4:
                st.write(target['status'])

        # 显示成果
        if 'achievements' in org_growth:
            st.success("**Q1成果:** " + "、".join(org_growth['achievements']))

    st.divider()

    # 重点客户质量情况
    st.subheader("👥 重点客户质量情况")

    customer_data = data['customer_quality']
    customer_df = pd.DataFrame(customer_data['customers'])

    cols = st.columns([2, 3])

    with cols[0]:
        # 客户质量评分
        fig = px.bar(
            customer_df,
            x='name',
            y='score',
            color='score',
            color_continuous_scale=['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1'],
            range_color=[70, 100],
            labels={'name': '客户', 'score': '质量评分'},
            height=300
        )
        fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="目标线")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with cols[1]:
        # 客户详情表格 - 自动从其他模块获取数据
        # 1. 从漏测DI模块获取DI数据
        defect_data = data.get('defect_escape', {})
        project_di = defect_data.get('project_di', {})

        # 2. 从现网问题模块获取问题数
        prod_issues = data.get('production_issues', {})
        issues_list = prod_issues.get('issues', [])

        # 3. 从事故统计模块获取事故数
        accident_data = data.get('accident_rate', {})
        accidents = accident_data.get('accidents', [])

        # 客户名称映射（用于匹配不同数据源中的客户名称）
        customer_mapping = {
            'zhgc': ['zhgc', 'ZHGC'],
            '比亚迪': ['比亚迪', 'BYD', 'byd'],
            '长江存储': ['长江存储', '长存', 'cxc', 'CXC']
        }

        # 构建客户详情数据
        customer_details = []
        for c in customer_data['customers']:
            customer_name = c['name']
            mapping_names = customer_mapping.get(customer_name, [customer_name])

            # 从漏测DI获取数据
            di_info = None
            for di_name, di_data in project_di.items():
                if any(name in di_name or di_name in name for name in mapping_names):
                    di_info = di_data
                    break

            # 从现网问题统计问题数
            issue_count = 0
            for issue in issues_list:
                issue_customer = issue.get('客户名称', '')
                if any(name in issue_customer or issue_customer in name for name in mapping_names):
                    issue_count += 1

            # 从事故统计事故数
            accident_count = 0
            for accident in accidents:
                accident_customer = accident.get('客户名称', '')
                if any(name in accident_customer or accident_customer in name for name in mapping_names):
                    accident_count += 1

            customer_details.append({
                '客户名称': customer_name,
                '质量评分': c['score'],
                '漏测DI': di_info['actual'] if di_info else c.get('di', '-'),
                'DI目标': di_info['target'] if di_info else c.get('di_target', '-'),
                'DI状态': di_info['status'] if di_info else c.get('di_status', '-'),
                '现网问题数': issue_count,
                '事故数': accident_count,
                '趋势': c['trend']
            })

        display_df = pd.DataFrame(customer_details)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 漏测DI情况
    st.subheader("🐛 漏测DI（Defect Index）情况")

    defect_data = data['defect_escape']

    # 第一行：商用版本DI + 重点项目DI
    cols = st.columns(4)

    with cols[0]:
        st.metric(
            label="商用版本漏测DI",
            value=f"{defect_data['current_di']}",
            delta=f"目标<{defect_data['target_di']}",
            delta_color="inverse"
        )
        if defect_data['current_di'] < defect_data['target_di']:
            st.markdown('<span class="status-good">✅ 达标</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-danger">❌ 超标</span>', unsafe_allow_html=True)

    # 重点项目DI详情
    project_di = defect_data.get('project_di', {})
    for idx, (project, info) in enumerate(project_di.items()):
        with cols[idx + 1]:
            st.metric(
                label=f"{project}漏测DI",
                value=info['actual'],
                delta=f"目标{info['target']}",
                delta_color="inverse"
            )
            st.markdown(f"<span class=\"status-good\">{info['status']}</span>", unsafe_allow_html=True)

    # 第二行：趋势图和类型分布
    trend_cols = st.columns(2)

    with trend_cols[0]:
        # DI趋势
        months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=months,
            y=defect_data['monthly_di'],
            mode='lines+markers',
            name='DI值',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.add_hline(y=defect_data['target_di'], line_dash="dash", line_color="green",
                      annotation_text="目标线")
        fig.update_layout(
            title="DI月度趋势",
            xaxis_title="月份",
            yaxis_title="DI值",
            height=250,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with trend_cols[1]:
        # 漏测类型分布
        categories = defect_data['categories']
        fig = px.pie(
            values=list(categories.values()),
            names=list(categories.keys()),
            title="漏测类型分布",
            height=250
        )
        st.plotly_chart(fig, use_container_width=True)

    # 业务线详细数据
    business_lines = defect_data.get('business_lines', {})
    if business_lines:
        st.divider()
        st.write("**📊 研发体系漏测DI明细**")
        st.caption(f"数据截止: {defect_data.get('as_of_date', 'N/A')} | 年度目标: {defect_data.get('target_di', 0)} | 预期(27%): {defect_data.get('expected_di', 0)} | 当前: {defect_data.get('current_di', 0)}")

        # 创建详细数据表格
        all_units = []

        # G100老版本内核
        g100 = business_lines.get('G100老版本内核', {})
        for unit in g100.get('sub_units', []):
            actual = unit.get('actual', 0)
            expected = unit.get('expected', 0)
            # 漏测DI越低越好：实际<=预期为达标
            if expected == 0:
                # 预期为0时，只要有实际值就算超标
                status = "⚠️ 有漏测" if actual > 0 else "✅ 无漏测"
            elif actual <= expected:
                status = "✅ 达标"
            else:
                over_pct = round((actual - expected) / expected * 100, 0) if expected > 0 else 0
                status = f"❌ 超标{over_pct}%"
            all_units.append({
                '业务': 'G100老版本内核',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '目标': unit.get('target', 0),
                '预期': expected,
                '实际': round(actual, 1),
                '偏差': unit.get('variance', ''),
                '状态': status
            })
        # 添加小计
        g100_total_actual = g100.get('total_actual', 0)
        g100_total_expected = g100.get('total_expected', 0)
        if g100_total_expected == 0:
            g100_status = "⚠️ 有漏测" if g100_total_actual > 0 else "✅ 无漏测"
        elif g100_total_actual <= g100_total_expected:
            g100_status = "✅ 达标"
        else:
            over_pct = round((g100_total_actual - g100_total_expected) / g100_total_expected * 100, 0) if g100_total_expected > 0 else 0
            g100_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': 'G100老版本内核',
            '作战单元': '【小计】',
            'Owner': g100.get('owner', ''),
            '目标': 870,
            '预期': g100_total_expected,
            '实际': round(g100_total_actual, 1),
            '偏差': f"{g100_total_actual - g100_total_expected:+.1f}",
            '状态': g100_status
        })

        # G100 V5版本（预留未上线）
        all_units.append({
            '业务': 'G100 V5版本',
            '作战单元': '【预留】未上线',
            'Owner': '陈炳达',
            '目标': 189,
            '预期': 0,
            '实际': 0,
            '偏差': 'N/A',
            '状态': 'N/A'
        })

        # 重点项目
        key_projects = business_lines.get('重点项目', {})
        for unit in key_projects.get('sub_units', []):
            actual = unit.get('actual', 0)
            expected = unit.get('expected', 0)
            # 漏测DI越低越好
            if expected == 0:
                status = "⚠️ 有漏测" if actual > 0 else "✅ 无漏测"
            elif actual <= expected:
                status = "✅ 达标"
            else:
                over_pct = round((actual - expected) / expected * 100, 0) if expected > 0 else 0
                status = f"❌ 超标{over_pct}%"
            all_units.append({
                '业务': '重点项目',
                '作战单元': unit.get('name', ''),
                'Owner': unit.get('owner', ''),
                '目标': unit.get('target', 0),
                '预期': expected,
                '实际': round(actual, 1),
                '偏差': unit.get('variance', ''),
                '状态': status
            })

        # 测试 - 从内核算出
        kernel_units = {u.get('name', ''): u for u in g100.get('sub_units', [])}

        # 1. 内核测试 = SQL引擎 + 存储引擎 + PLSQL + 驱动 + CMCC内核
        kernel_test_actual = (
            kernel_units.get('SQL引擎', {}).get('actual', 0) +
            kernel_units.get('存储引擎', {}).get('actual', 0) +
            kernel_units.get('PLSQL', {}).get('actual', 0) +
            kernel_units.get('驱动', {}).get('actual', 0) +
            kernel_units.get('CMCC内核', {}).get('actual', 0)
        )
        kernel_test_target = 615
        kernel_test_expected = round(234 * kernel_test_target / 870, 1)  # 按目标比例
        kernel_test_variance = f"{kernel_test_actual - kernel_test_expected:+.1f}"

        # 漏测DI越低越好
        if kernel_test_expected == 0:
            kernel_test_status = "⚠️ 有漏测" if kernel_test_actual > 0 else "✅ 无漏测"
        elif kernel_test_actual <= kernel_test_expected:
            kernel_test_status = "✅ 达标"
        else:
            over_pct = round((kernel_test_actual - kernel_test_expected) / kernel_test_expected * 100, 0) if kernel_test_expected > 0 else 0
            kernel_test_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': '测试',
            '作战单元': '内核测试',
            'Owner': '崔响灵、苏动',
            '目标': kernel_test_target,
            '预期': kernel_test_expected,
            '实际': round(kernel_test_actual, 1),
            '偏差': kernel_test_variance,
            '状态': kernel_test_status
        })

        # 2. 迁移工具测试 = 迁移工具 + DTP
        migrate_test_actual = (
            kernel_units.get('迁移工具', {}).get('actual', 0) +
            kernel_units.get('DTP', {}).get('actual', 0)
        )
        migrate_test_target = 170
        migrate_test_expected = round(234 * migrate_test_target / 870, 1)
        migrate_test_variance = f"{migrate_test_actual - migrate_test_expected:+.1f}"

        if migrate_test_expected == 0:
            migrate_test_status = "⚠️ 有漏测" if migrate_test_actual > 0 else "✅ 无漏测"
        elif migrate_test_actual <= migrate_test_expected:
            migrate_test_status = "✅ 达标"
        else:
            over_pct = round((migrate_test_actual - migrate_test_expected) / migrate_test_expected * 100, 0) if migrate_test_expected > 0 else 0
            migrate_test_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': '测试',
            '作战单元': '迁移工具测试',
            'Owner': '梁佳琪',
            '目标': migrate_test_target,
            '预期': migrate_test_expected,
            '实际': round(migrate_test_actual, 1),
            '偏差': migrate_test_variance,
            '状态': migrate_test_status
        })

        # 3. 运维工具测试 = 运维管理工具 + DBOPS
        ops_test_actual = (
            kernel_units.get('运维管理工具', {}).get('actual', 0) +
            kernel_units.get('DBOPS', {}).get('actual', 0)
        )
        ops_test_target = 85
        ops_test_expected = round(234 * ops_test_target / 870, 1)
        ops_test_variance = f"{ops_test_actual - ops_test_expected:+.1f}"

        if ops_test_expected == 0:
            ops_test_status = "⚠️ 有漏测" if ops_test_actual > 0 else "✅ 无漏测"
        elif ops_test_actual <= ops_test_expected:
            ops_test_status = "✅ 达标"
        else:
            over_pct = round((ops_test_actual - ops_test_expected) / ops_test_expected * 100, 0) if ops_test_expected > 0 else 0
            ops_test_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': '测试',
            '作战单元': '运维工具测试',
            'Owner': '熊卉',
            '目标': ops_test_target,
            '预期': ops_test_expected,
            '实际': round(ops_test_actual, 1),
            '偏差': ops_test_variance,
            '状态': ops_test_status
        })

        # 添加测试小计行
        test_total_actual = kernel_test_actual + migrate_test_actual + ops_test_actual
        test_total_target = 870
        test_total_expected = kernel_test_expected + migrate_test_expected + ops_test_expected
        test_total_variance = f"{test_total_actual - test_total_expected:+.1f}"
        if test_total_expected == 0:
            test_total_status = "⚠️ 有漏测" if test_total_actual > 0 else "✅ 无漏测"
        elif test_total_actual <= test_total_expected:
            test_total_status = "✅ 达标"
        else:
            over_pct = round((test_total_actual - test_total_expected) / test_total_expected * 100, 0) if test_total_expected > 0 else 0
            test_total_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': '测试',
            '作战单元': '【小计】',
            'Owner': '郭琦',
            '目标': test_total_target,
            '预期': test_total_expected,
            '实际': round(test_total_actual, 1),
            '偏差': test_total_variance,
            '状态': test_total_status
        })

        # 维优部（研发体系整体）
        expected_ratio = defect_escape.get('expected_di', 234) / defect_escape.get('target_di', 870) if defect_escape.get('target_di', 0) > 0 else 0.27
        weiyou_expected = round(870 * expected_ratio, 1)
        weiyou_actual = g100_total_actual  # 使用已计算的G100实际值
        weiyou_variance = f"{weiyou_actual - weiyou_expected:+.1f}"
        if weiyou_expected == 0:
            weiyou_status = "⚠️ 有漏测" if weiyou_actual > 0 else "✅ 无漏测"
        elif weiyou_actual <= weiyou_expected:
            weiyou_status = "✅ 达标"
        else:
            over_pct = round((weiyou_actual - weiyou_expected) / weiyou_expected * 100, 0) if weiyou_expected > 0 else 0
            weiyou_status = f"❌ 超标{over_pct}%"
        all_units.append({
            '业务': '维优部',
            '作战单元': '【研发体系整体】',
            'Owner': '陈建华',
            '目标': 870,
            '预期': weiyou_expected,
            '实际': round(weiyou_actual, 1),
            '偏差': weiyou_variance,
            '状态': weiyou_status
        })

        df = pd.DataFrame(all_units)

        # 使用颜色标记小计行
        def highlight_subtotal(row):
            if '【' in str(row['作战单元']):
                return ['background-color: #e8f4f8; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df.style.apply(highlight_subtotal, axis=1),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # 事故率
    st.subheader("⚠️ 事故率情况")

    accident_data = data['accident_rate']

    # 第一行：核心指标
    cols = st.columns(4)

    with cols[0]:
        st.metric(
            label="业务停机时长",
            value=f"{accident_data.get('downtime_minutes', '-')}分钟",
            delta=f"目标<{accident_data['target_rate']}分钟*套数",
            delta_color="inverse"
        )
        if accident_data.get('downtime_minutes', 0) <= 0:
            st.markdown('<span class="status-good">✅ 达标</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-warning">⚠️ 说明见下方</span>', unsafe_allow_html=True)

    with cols[1]:
        st.metric(
            label="可靠性不达标套数",
            value=f"{accident_data.get('reliability_fail', '-')}套",
            delta="目标≤5套",
            delta_color="normal" if accident_data.get('reliability_fail', 0) <= 5 else "inverse"
        )
        if accident_data.get('reliability_fail', 0) <= 5:
            st.markdown('<span class="status-good">✅ 达标</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-danger">❌ 超标</span>', unsafe_allow_html=True)

    with cols[2]:
        st.metric(
            label="G100上线套数",
            value=accident_data.get('total_systems', '-')
        )
        st.caption(f"割接套数: {accident_data.get('cutover_systems', '-')}")

    with cols[3]:
        # 事故等级分布
        severity_data = accident_data['severity_dist']
        total_accidents = sum(severity_data.values())
        st.metric(
            label="年度累计事故",
            value=total_accidents
        )
        fig = go.Figure(data=[go.Bar(
            x=list(severity_data.keys()),
            y=list(severity_data.values()),
            marker_color=['#dc3545', '#fd7e14', '#ffc107', '#6c757d']
        )])
        fig.update_layout(
            title="事故等级分布",
            xaxis_title="等级",
            yaxis_title="数量",
            height=150,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    # 说明文字
    if 'note' in accident_data:
        st.info(f"💡 **说明**: {accident_data['note']}")
