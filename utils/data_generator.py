"""
数据生成器 - 模拟质量数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_all_data():
    """生成所有板块的数据"""
    return {
        'quality_work': generate_quality_work_data(),
        'quality_improvement': generate_quality_improvement_data(),
        'version_quality': generate_version_quality_data(),
        'qa_items': generate_qa_items_data()
    }

def generate_quality_work_data():
    """生成质量工作板块数据"""
    months = pd.date_range(start='2024-01', periods=12, freq='MS').strftime('%Y-%m').tolist()
    
    # 年度目标数据 - Q1实际达标情况
    # Q1实际数据
    shangyong_di = 194  # 商用版本实际DI
    shangyong_target = 217  # Q1季度目标
    v5_di = None  # 暂未发布
    downtime = 2  # 业务停机时长2分钟（比亚迪2例E100旧版本宕机）
    total_systems = 3545  # G100上线套数
    cutover_systems = 155  # 割接套数
    reliability_fail = 0  # 可靠性不达标套数

    # 重点项目实际数据
    byd_di = 21  # 比亚迪漏测DI
    cxc_di = 7   # 长江存储漏测DI
    zhgc_di = 11 # ZHGC漏测DI
    zhgc_byd_complaint = 0  # 比亚迪无重大投诉
    cxc_complaint = 0  # 长江存储重大投诉

    # 计算各项目标达成情况
    di_achievement = 100 if shangyong_di < shangyong_target else 90
    accident_achievement = 95  # 有2分钟停机，但属于旧版本问题，基本达标
    project_achievement = 100  # 全部达标
    team_achievement = 90  # QA虚拟团队运作顺利

    overall = round(di_achievement * 0.3 + accident_achievement * 0.3 + project_achievement * 0.3 + team_achievement * 0.1, 1)

    annual_goals = {
        'overall_achievement': overall,
        'quarter': 'Q1',
        'categories': {
            '基础业绩': {
                'weight': '90%',
                'items': [
                    {
                        'name': '漏测DI',
                        'weight': '30%',
                        'status': '达标',
                        'targets': [
                            {'name': '商用版本漏测DI', 'target': f'<{shangyong_target}(Q1)', 'actual': shangyong_di, 'status': '✅ 达标'},
                            {'name': 'V5版本漏测DI', 'target': '<189', 'actual': '暂未发布', 'status': '⏸️ 不涉及'},
                            {'name': '重点项目漏测DI', 'target': '按项目管控', 'actual': '全部达标', 'status': '✅ 达标'},
                        ],
                        'details': {
                            '比亚迪': {'actual': byd_di, 'target': '≤100', 'status': '✅ 达标'},
                            '长江存储': {'actual': cxc_di, 'target': '<145', 'status': '✅ 达标'},
                            'ZHGC': {'actual': zhgc_di, 'target': '≤50', 'status': '✅ 达标'},
                        }
                    },
                    {
                        'name': '事故率',
                        'weight': '30%',
                        'status': '达标',
                        'targets': [
                            {'name': '业务停机时长', 'target': '<0.5分钟*套数', 'actual': f'{downtime}分钟', 'status': '⚠️ 说明'},
                            {'name': '可靠性不达标套数', 'target': '≤5套', 'actual': f'{reliability_fail}套', 'status': '✅ 达标'},
                        ],
                        'note': '停机2分钟为比亚迪2例E100旧版本宕机问题',
                        'systems': {'上线': total_systems, '割接': cutover_systems}
                    },
                    {
                        'name': '重点项目',
                        'weight': '30%',
                        'status': '全部达标',
                        'projects': [
                            {
                                'name': 'ZHGC',
                                'status': '✅ 全部达标',
                                'metrics': [
                                    {'name': 'ZHGC漏测DI', 'target': '≤50', 'actual': zhgc_di, 'status': '✅ 达标'},
                                    {'name': '比亚迪漏测DI', 'target': '≤100', 'actual': byd_di, 'status': '✅ 达标'},
                                    {'name': '重大客户投诉', 'target': '0', 'actual': zhgc_byd_complaint, 'status': '✅ 无投诉'},
                                ]
                            },
                            {
                                'name': '长江存储',
                                'status': '✅ 全部达标',
                                'metrics': [
                                    {'name': '漏测DI(总计)', 'target': '<145', 'actual': cxc_di, 'status': '✅ 达标'},
                                    {'name': '漏测DI(内核)', 'target': '<115', 'actual': max(0, cxc_di-2), 'status': '✅ 达标'},
                                    {'name': '漏测DI(工具)', 'target': '<30', 'actual': min(cxc_di, 2), 'status': '✅ 达标'},
                                    {'name': '客户重大投诉', 'target': '≤1', 'actual': cxc_complaint, 'status': '✅ 无投诉'},
                                ]
                            },
                            {'name': '其他重点项目', 'requirement': '不出事故', 'status': '✅ 达成'},
                        ]
                    }
                ]
            },
            '组织成长': {
                'weight': '10%',
                'items': [
                    {
                        'name': '质量团队建设',
                        'weight': '10%',
                        'status': '顺利推进',
                        'targets': [
                            {'name': '沟通协调能力', 'target': '达到团队项目经理90%', 'actual': '评估中', 'status': '⏳ 暂不好评估'},
                            {'name': 'QA虚拟团队运作', 'target': '有效运作', 'actual': '运作顺利', 'status': '✅ 顺利'},
                        ],
                        'achievements': [
                            'G100项目顺利发布',
                            'HA项目顺利发布',
                            'DB Driver项目顺利发布',
                            'exBase项目顺利发布',
                            'vem项目顺利发布'
                        ]
                    }
                ]
            }
        }
    }
    
    # 重点客户质量 - zhgc、比亚迪、长江存储
    # 基于Q1实际DI数据计算质量评分（DI越低评分越高）
    zhgc_score = 92  # DI=11，目标≤50，表现优秀
    byd_score = 88   # DI=21，目标≤100，表现良好
    cxc_score = 95   # DI=7，目标<145，表现优秀

    customer_quality = {
        'avg_score': round((zhgc_score + byd_score + cxc_score) / 3, 1),
        'customers': [
            {'name': 'zhgc', 'score': zhgc_score, 'issues': 0, 'trend': 'up',
             'di': zhgc_di, 'di_target': '≤50', 'di_status': '✅ 达标'},
            {'name': '比亚迪', 'score': byd_score, 'issues': 2, 'trend': 'stable',
             'di': byd_di, 'di_target': '≤100', 'di_status': '✅ 达标'},
            {'name': '长江存储', 'score': cxc_score, 'issues': 0, 'trend': 'up',
             'di': cxc_di, 'di_target': '<145', 'di_status': '✅ 达标'},
        ]
    }
    
    # 漏测DI数据 - 2026年研发体系漏测转测DI值统计（截止到04月08日）
    # 年度目标：870，当前实际：194，预期(27%)：234
    defect_escape = {
        'current_di': 194,  # 当前实际DI合计
        'target_di': 870,   # 年度目标
        'expected_di': 234, # 按4/8日占比(约27%)计算的预期DI
        'achievement_rate': '83%', # 194/234 = 83%
        'as_of_date': '2026-04-08',

        # 月度趋势（Q1实际 + Q2预估）
        'monthly_di': [65, 62, 67, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Q1累计194

        # 漏测类型分布
        'categories': {
            '功能遗漏': 78,
            '边界条件': 42,
            '兼容性': 35,
            '性能问题': 24,
            '其他': 15
        },

        # 详细业务线数据（与表格一致）
        'business_lines': {
            'G100老版本内核': {
                'total_actual': 194,
                'total_target': 870,
                'total_expected': 234,
                'achievement_rate': '83%',
                'owner': '陈炳达',
                'sub_units': [
                    {'name': 'SQL引擎', 'owner': '曾祥鑫', 'target': 300, 'expected': 81, 'actual': 72.2, 'variance': '-10%'},
                    {'name': '存储引擎', 'owner': '刘遥', 'target': 210, 'expected': 56, 'actual': 47.1, 'variance': '-16%'},
                    {'name': 'PLSQL', 'owner': '范建琪', 'target': 89, 'expected': 24, 'actual': 24, 'variance': '0%'},
                    {'name': '驱动', 'owner': '王晓阳', 'target': 16, 'expected': 4, 'actual': 1, 'variance': '-77%'},
                    {'name': 'CMCC内核', 'owner': '陈炳达', 'target': 0, 'expected': 0, 'actual': 4, 'variance': 'N/A'},
                    {'name': '迁移工具', 'owner': '高燕', 'target': 170, 'expected': 46, 'actual': 33.3, 'variance': '-25%'},
                    {'name': 'DTP', 'owner': '高燕', 'target': 0, 'expected': 0, 'actual': 1, 'variance': 'N/A'},
                    {'name': '运维管理工具', 'owner': '刘平', 'target': 85, 'expected': 23, 'actual': 11.3, 'variance': '-50%'},
                    {'name': 'DBOPS', 'owner': '刘平', 'target': 0, 'expected': 0, 'actual': 0.1, 'variance': 'N/A'},
                ]
            },
            'G100_V5版本': {
                'total_actual': 0,
                'total_target': 189,
                'total_expected': 0,
                'achievement_rate': '100%',
                'owner': '陈炳达',
                'sub_units': []
            },
            '重点项目': {
                'owner': '各项目经理',
                'sub_units': [
                    {'name': '比亚迪', 'owner': '张文龙', 'target': 110, 'expected': 30, 'actual': 21.1, 'variance': '-29%'},
                    {'name': 'ZHGC试点', 'owner': '张文龙', 'target': 50, 'expected': 13, 'actual': 11.1, 'variance': '-17%'},
                    {'name': '长江存储', 'owner': '董汭荣', 'target': 145, 'expected': 40, 'actual': 8, 'variance': '-80%'},
                ]
            },
            '测试': {
                'total_actual': 194,  # 测试总和等于G100老版本内核
                'total_target': 870,
                'total_expected': 234,
                'achievement_rate': '83%',
                'owner': '郭琦',
                'sub_units': [
                    # 测试值自动从内核算出：
                    # 内核测试 = SQL引擎 + 存储引擎 + PLSQL + 驱动 + CMCC内核 = 72.2+47.1+24+1+4 = 148.3
                    {'name': '内核测试', 'owner': '崔响灵、苏动', 'target': 615, 'expected': 165, 'actual': 148.3, 'variance': '-10%', 'note': 'SQL引擎+存储引擎+PLSQL+驱动+CMCC内核'},
                    # 迁移工具测试 = 迁移工具 + DTP = 33.3+1 = 34.3
                    {'name': '迁移工具测试', 'owner': '梁佳琪', 'target': 170, 'expected': 46, 'actual': 34.3, 'variance': '-25%', 'note': '迁移工具+DTP'},
                    # 运维工具测试 = 运维管理工具 + DBOPS = 11.3+0.1 = 11.4
                    {'name': '运维工具测试', 'owner': '熊卉', 'target': 85, 'expected': 23, 'actual': 11.4, 'variance': '-50%', 'note': '运维管理工具+DBOPS'},
                ]
            },
            '维优部': {
                'total_actual': 194,
                'total_target': 870,
                'total_expected': 234,
                'achievement_rate': '83%',
                'owner': '陈建华',  # 维优部代表研发体系整体
                'sub_units': [
                    {'name': '研发体系', 'owner': '陈建华', 'target': 870, 'expected': 234, 'actual': 194, 'variance': '-17%'}
                ]
            }
        },

        # 重点项目DI汇总（用于展示）
        'project_di': {
            '比亚迪': {'actual': 21.1, 'target': 110, 'expected': 30, 'status': '✅ 达标', 'variance': '-29%'},
            '长江存储': {'actual': 8, 'target': 145, 'expected': 40, 'status': '✅ 达标', 'variance': '-80%'},
            'ZHGC试点': {'actual': 11.1, 'target': 50, 'expected': 13, 'status': '✅ 达标', 'variance': '-17%'}
        }
    }
    
    # 事故率 - Q1实际数据
    # 业务停机时长: 2分钟(比亚迪2例E100旧版本宕机)，可靠性不达标套数: 0套
    # G100上线套数: 3545，割接套数: 155
    accident_rate = {
        'current_rate': round(downtime / total_systems * 100, 4),  # 事故率计算
        'target_rate': 0.5,
        'accidents_this_month': 2,  # 2例宕机
        'accidents_ytd': 2,  # Q1累计2例
        'downtime_minutes': downtime,  # 2分钟
        'total_systems': total_systems,  # 3545套
        'cutover_systems': cutover_systems,  # 155套
        'reliability_fail': reliability_fail,  # 0套
        'severity_dist': {
            'P0': 0,
            'P1': 2,  # 2例P1事故
            'P2': 0,
            'P3': 0
        },
        'note': '停机2分钟为比亚迪2例E100旧版本宕机问题'
    }
    
    # 趋势数据
    trend_data = pd.DataFrame({
        'month': months,
        'defect_density': [random.uniform(3, 7) for _ in range(12)],
        'test_coverage': [random.randint(75, 90) for _ in range(12)],
        'automation_rate': [random.randint(60, 80) for _ in range(12)],
        'customer_score': [random.randint(82, 94) for _ in range(12)]
    })
    
    return {
        'annual_goals': annual_goals,
        'customer_quality': customer_quality,
        'defect_escape': defect_escape,
        'accident_rate': accident_rate,
        'trend_data': trend_data
    }


def generate_quality_improvement_data():
    """生成质量改进板块数据"""

    # TOP质量问题 - 实际Q1数据
    top_issues = [
        {
            'rank': 1,
            'issue': '客户场景仿真&镜像测试',
            'status': '进行中',
            'progress': 65,
            'owner': '测试团队',
            'subtasks': [
                {
                    'name': '长存MES仿真项目',
                    'desc': '数据模型开发和模拟数据生成，涉及模拟数据工具适配和配置调试',
                    'deadline': '2024-04-10',
                    'progress': 70,
                    'status': '进行中'
                },
                {
                    'name': '某KJ项目批量插入能力仿真测试',
                    'desc': '正在进行批量插入能力仿真测试',
                    'deadline': '2024-04-15',
                    'progress': 50,
                    'status': '进行中'
                }
            ]
        },
        {
            'rank': 2,
            'issue': '产品规划负责，清晰需求边界',
            'status': '待评估效果',
            'progress': 90,
            'owner': '产品团队',
            'subtasks': [
                {
                    'name': '产品侧用户需求评审流程',
                    'desc': '产品同研发团队沟通，确定评审流程及宣贯',
                    'deadline': '已完成',
                    'progress': 100,
                    'status': '已完成'
                },
                {
                    'name': '评审用户需求',
                    'desc': '产品团队已完成收集到的33个需求评审',
                    'deadline': '已完成',
                    'progress': 100,
                    'status': '已完成'
                }
            ],
            'note': '上版本已落地方案，待评估效果确认是否闭环'
        },
        {
            'rank': 3,
            'issue': '推进轻量级用例前移与门禁集成',
            'status': '进行中',
            'progress': 80,
            'owner': '研发团队',
            'subtasks': [
                {
                    'name': '专用服务器部署',
                    'desc': '北京服务器寄到广州，物理机已到位，环境部署中',
                    'deadline': '2024-04-08',
                    'progress': 85,
                    'status': '环境部署中'
                },
                {
                    'name': '工程搭建与试运行',
                    'desc': '工程搭建完成，目前10000条用例，会持续增加',
                    'deadline': '待环境部署',
                    'progress': 75,
                    'status': '待环境部署'
                },
                {
                    'name': 'core推送与修复机制',
                    'desc': '轻量化门禁出现core时推送到企微群，专人分析提单，要求当天21点前修复',
                    'deadline': '已运行',
                    'progress': 100,
                    'status': '近一周代码稳定，无core产生'
                },
                {
                    'name': '结果解读指引文档',
                    'desc': '轻量化门禁推送结果解读指引文档',
                    'deadline': '已完成',
                    'progress': 100,
                    'status': '已完成'
                }
            ]
        },
        {
            'rank': 4,
            'issue': '建立转测风险评级与转测标准',
            'status': '待评估效果',
            'progress': 95,
            'owner': '研发团队',
            'subtasks': [
                {
                    'name': '收集需求转测风险点',
                    'desc': '收集了需求转测研发测可能有问题的点',
                    'deadline': '已完成',
                    'progress': 100,
                    'status': '已完成'
                },
                {
                    'name': '转测标准方案落地',
                    'desc': '使用初步方案（tapd需求转测时要求研发提供ci测试通过以及keyuser代码review通过截图）',
                    'deadline': '已完成',
                    'progress': 100,
                    'status': '已完成'
                }
            ],
            'note': '上版本已落地方案，待评估效果确认是否闭环，需要刷新TOP问题'
        },
    ]

    # 事故复盘 - Q1实际复盘数据（含详细复盘事项）
    accident_reviews = [
        {
            'id': 'ACC-Q1-001',
            'title': '301医院逻辑复制问题',
            'date': '2024-Q1',
            'severity': 'P1',
            'status': '举一反三进行中',
            'progress': 40,
            'closure_date': '预计2024-06-30',
            'lessons': 3,
            'scope': '逻辑复制模块',
            'details': [
                {
                    'category': '性能和稳定性测试',
                    'items': [
                        {'desc': '补充发布订阅场景', 'status': '未完成', 'due': '2024-06-30'}
                    ]
                },
                {
                    'category': '高可用',
                    'items': [
                        {'desc': '增加逻辑解码、故障注入等场景，关注数据一致性', 'status': '未完成', 'due': '2024-06-30'}
                    ]
                }
            ]
        },
        {
            'id': 'ACC-Q1-002',
            'title': '比亚迪出包问题',
            'date': '2024-Q1',
            'severity': 'P1',
            'status': '部分闭环',
            'progress': 60,
            'closure_date': '主要问题已闭环(4/6)，剩余预计2024-06-30',
            'lessons': 6,
            'scope': '发布流程',
            'details': [
                {
                    'category': '构建出包标准化（已完成）',
                    'items': [
                        {'desc': '构建出包参数配置标准化，默认设置为NO-MOT，但不禁用MOT，POC可能需要配置成MOT', 'status': '已完成', 'due': '已完成'},
                        {'desc': '检查其他构建参数配置，设置通用的和个性化的构建参数配置文件，构建自动化，减少人的干预', 'status': '已完成', 'due': '已完成'},
                        {'desc': '明确哪些分支是重要客户的？哪些分支用于出生产包？', 'status': '已完成', 'due': '已完成'},
                        {'desc': '包名命名规范，PSU包应添加MOT标志，便于检查', 'status': '已完成', 'due': '已完成'}
                    ]
                },
                {
                    'category': '测试侧改进（已完成）',
                    'items': [
                        {'desc': '测试侧增加对mot版本及其他参数的检查', 'status': '已完成', 'due': '已完成'}
                    ]
                },
                {
                    'category': '交付物标准化（预计630）',
                    'items': [
                        {'desc': '不同项目生产版本的交付物的出口标准化，列出生产版本的checklist', 'status': '未完成', 'due': '2024-06-30'},
                        {'desc': 'QA增加对交付物的检查（依赖第三项）', 'status': '未完成', 'due': '2024-06-30'}
                    ]
                },
                {
                    'category': '沟通与培训（已完成）',
                    'items': [
                        {'desc': '约定默认版本是no_mot版本，如果需要mot版本则明确沟通', 'status': '已完成', 'due': '已完成'},
                        {'desc': '跟构建团队明确mot版本的潜在风险和影响，引起构建团队高度重视', 'status': '已完成', 'due': '已完成'}
                    ]
                }
            ]
        },
        {
            'id': 'ACC-Q1-003',
            'title': 'WDR现场问题',
            'date': '2024-Q1',
            'severity': 'P2',
            'status': '部分闭环',
            'progress': 70,
            'closure_date': '主要问题已闭环(4/7)，剩余预计2024-06-30',
            'lessons': 5,
            'scope': '现场部署',
            'details': [
                {
                    'category': '已完成事项',
                    'items': [
                        {'desc': '梳理现场关键路径：系统收集梳理WDR及其他特性的关键路径', 'status': '已完成', 'due': '已完成'},
                        {'desc': '建立客户关键路径验收清单：基于上述输入，转化为关键路径验收用例与验收标准', 'status': '已完成', 'due': '已完成'},
                        {'desc': '强化代码评审机制：聚焦关键路径代码的改动，谨慎评估AI相关的修改，更新《代码评审规范》', 'status': '已完成', 'due': '已完成'}
                    ]
                },
                {
                    'category': '待完成事项（预计630）',
                    'items': [
                        {'desc': '分支升级可行性：分支连续升级技术方案的可行性与优先级确认', 'status': '未完成', 'due': '2024-06-30'},
                        {'desc': '分支升级落地：推动升级方案落地，配套完善升级测试方案', 'status': '未完成', 'due': '2024-06-30'}
                    ]
                }
            ]
        },
        {
            'id': 'ACC-Q1-004',
            'title': 'VDS现网问题',
            'date': '2024-Q1',
            'severity': 'P1',
            'status': '大部分闭环',
            'progress': 80,
            'closure_date': '80%已闭环，剩余预计2024-06-30',
            'lessons': 6,
            'scope': '现网运维',
            'details': [
                {
                    'category': '已完成事项',
                    'items': [
                        {'desc': '梳理编辑数据开发逻辑及测试场景：系统梳理VDS编辑数据功能的开发逻辑（含ctid定位、条件拼接、二次校验等），并基于此整理完整的测试场景矩阵（含AND、OR、混合条件、子查询等）', 'status': '已完成', 'due': '已完成'},
                        {'desc': '代码review与测试用例场景覆盖借助AI', 'status': '已完成', 'due': '已完成'},
                        {'desc': '增加风险对齐环节：开发侧强制输出"测试重点关注场景清单"、测试侧强制输出"测试计划表"与开发对齐', 'status': '已完成', 'due': '已完成'},
                        {'desc': '建立"风险库+常识库"的知识沉淀机制：建立团队级风险库（历史缺陷特征标签）和常识库（SQL陷阱、边界场景等），定期更新，作为测试设计输入', 'status': '已完成', 'due': '已完成'}
                    ]
                },
                {
                    'category': '待完成事项（预计630）',
                    'items': [
                        {'desc': '建立技术实现串讲机制：对重要功能，强制要求开发进行技术实现串讲，测试根据串讲内容设计测试用例', 'status': '未完成', 'due': '2024-06-30'}
                    ]
                }
            ]
        },
    ]

    # 举一反三 - 实际Q1数据
    fanyi_data = {
        'total': 32,
        'completed': 19,
        'pending': 13,
        'by_project': [
            {
                'project': 'exBase举一反三',
                'total': 29,
                'completed': 29,
                'rate': 100,
                'status': '已完成',
                'desc': '完成了29个现网问题的举一反三'
            },
            {
                'project': '内核举一反三',
                'total': 3,
                'completed': 1,
                'rate': 30,
                'status': '进行中',
                'desc': '进行了3个专题的举一反三'
            }
        ],
        'items': [
            {'source': 'exBase举一反三', 'action': '29个现网问题改进', 'scope': 'exBase项目', 'status': '已完成', 'progress': 100},
            {'source': '内核举一反三', 'action': '专题1改进措施', 'scope': '内核模块', 'status': '进行中', 'progress': 30},
            {'source': '内核举一反三', 'action': '专题2改进措施', 'scope': '内核模块', 'status': '计划中', 'progress': 10},
            {'source': '内核举一反三', 'action': '专题3改进措施', 'scope': '内核模块', 'status': '计划中', 'progress': 0},
        ]
    }

    # 持续改进任务
    ongoing_tasks = [
        {
            'name': '客户场景仿真&镜像测试推进',
            'owner': '测试团队',
            'progress': 65,
            'due': '2024-04-15',
            'desc': '长存MES仿真和KJ项目批量插入能力测试'
        },
        {
            'name': '轻量级用例前移与门禁集成',
            'owner': '研发团队',
            'progress': 80,
            'due': '2024-04-30',
            'desc': '服务器部署、工程搭建、core推送机制'
        },
        {
            'name': '产品需求边界清晰化评估',
            'owner': '产品团队',
            'progress': 90,
            'due': '2024-04-30',
            'desc': '待评估效果确认是否闭环'
        },
        {
            'name': '转测风险评级与标准评估',
            'owner': '研发团队',
            'progress': 95,
            'due': '2024-04-30',
            'desc': '待评估效果确认是否闭环，需要刷新TOP问题'
        },
        {
            'name': '事故复盘闭环跟进',
            'owner': '质量团队',
            'progress': 65,
            'due': '2024-06-30',
            'desc': '4个事故复盘，预计630全部闭环'
        },
    ]

    return {
        'top_issues': top_issues,
        'accident_reviews': accident_reviews,
        '举一反三': fanyi_data,
        'ongoing_tasks': ongoing_tasks
    }
def generate_version_quality_data():
    """生成版本质量板块数据 - 实际V3和V5版本数据"""

    # V3项目版本质量 - 309psu2
    v3_project = {
        'name': 'V3项目',
        'current_version': 'V309PSU2',
        'current_status': '迭代1 需求开发中',
        'next_milestone': '需求转测（4月13日）',
        'defects': {
            'new_this_week': 10,
            'fixed_this_week': 1,
            'total_open': 303,
            'history': [12, 15, 8, 10, 11, 9, 10]  # 近7周新增缺陷趋势
        },
        'quality_goals': {
            'new_code_defects': {
                'name': '新代码引入缺陷清零',
                'target': '回归缺陷清零',
                'status': '持续关注中',
                'current': '待标记'
            },
            'legacy_defects': {
                'name': '存量缺陷降低',
                'target': '待标记存量必解缺陷',
                'status': '待标记',
                'current': '待标记'
            },
            'online_defects': {
                'name': '现网缺陷降低',
                'target': '待标记维优必解缺陷',
                'status': '待标记',
                'current': '待标记'
            }
        },
        'risk_level': '中',
        'risks': [
            '存量缺陷303个，修复进展较慢',
            '近一周新增缺陷(10)远大于修复缺陷(1)'
        ]
    }

    # V5项目版本质量 - V5.0.0
    v5_project = {
        'name': 'V5项目',
        'current_version': 'V5.0.0',
        'current_status': '当日封板（4月8日）',
        'next_milestone': '版本发布（4月15日）',
        'defects': {
            'new_this_week': 29,
            'fixed_this_week': 50,
            'total_open': 23,
            'history': [35, 42, 38, 29, 31, 27, 29]  # 近7周新增缺陷趋势
        },
        'quality_goals': {
            'legacy_di': {
                'name': '遗留DI值',
                'target': '< 30',
                'actual': 15,
                'status': '✅ 达标',
                'current': '15'
            },
            'new_feature_di': {
                'name': '新需求转测DI值',
                'target': '≤ 98',
                'actual': 170,
                'status': '❌ 超标',
                'current': '170'
            }
        },
        'risk_level': '高',
        'risks': [
            '封板缺陷未修复完成（23个待修复）',
            '转测DI值超标（170 > 98）',
            '距离发布仅7天，风险较高'
        ],
        'block_issues': [
            '封板缺陷23个未修复',
            '转测DI超标72',
        ]
    }

    # 版本质量日报 - V5封板日数据
    daily_report = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'version': 'V5.0.0',
        'build_status': '封板中',
        'new_bugs': 29,
        'fixed_bugs': 50,
        'open_bugs': 23,
        'block_issues': 2,
        'test_progress': 75,
        'v3_summary': {
            'version': 'V309PSU2',
            'new_bugs': 10,
            'fixed_bugs': 1,
            'open_bugs': 303
        }
    }

    # 版本质量周报
    weekly_report = {
        'week': '2024年第14周',
        'versions': [
            {
                'version': 'V309PSU2',
                'status': '迭代1开发中',
                'quality_score': 75,
                'defects': 303,
                'risk': '中',
                'next_milestone': '4月13日转测'
            },
            {
                'version': 'V5.0.0',
                'status': '4月8日封板',
                'quality_score': 65,
                'defects': 23,
                'risk': '高',
                'next_milestone': '4月15日发布'
            }
        ]
    }

    # 质量风险 - 基于实际版本情况
    risks = [
        {
            'title': 'V5版本封板风险',
            'severity': '高',
            'probability': '高',
            'impact': '发布延期或质量风险',
            'mitigation': '集中资源修复封板缺陷，每日跟踪进展',
            'version': 'V5.0.0'
        },
        {
            'title': 'V5转测DI超标',
            'severity': '高',
            'probability': '已发生',
            'impact': '新需求质量不达标',
            'mitigation': '分析DI超标原因，加强需求评审',
            'version': 'V5.0.0'
        },
        {
            'title': 'V3存量缺陷累积',
            'severity': '中',
            'probability': '高',
            'impact': '版本质量持续下降',
            'mitigation': '制定存量缺陷清理计划，分类处理',
            'version': 'V309PSU2'
        },
    ]

    # 新需求质量 - V5转测数据
    new_requirements = {
        'total': 45,
        'reviewed': 40,
        'defects_found': 170,
        'avg_review_time': 3.5,
        'requirement_clarity': 75,
        'di_per_requirement': 4.25,
        'target_di': 98,
        'actual_di': 170,
        'status': '超标'
    }

    # 迭代回顾
    iteration_retrospectives = [
        {
            'sprint': 'V5封板冲刺',
            'good': ['缺陷修复效率高(50个/周)', '封板按时进行'],
            'improve': ['转测DI超标', '封板缺陷未清零'],
            'actions': 4,
            'completed': 2
        },
        {
            'sprint': 'V309PSU2迭代1',
            'good': ['需求开发按计划进行'],
            'improve': ['新增缺陷大于修复缺陷', '存量缺陷积累'],
            'actions': 3,
            'completed': 1
        },
    ]

    return {
        'daily_report': daily_report,
        'weekly_report': weekly_report,
        'risks': risks,
        'new_requirements': new_requirements,
        'iteration_retrospectives': iteration_retrospectives,
        'v3_project': v3_project,
        'v5_project': v5_project
    }

def generate_qa_items_data():
    """生成QA事项板块数据"""
    
    # QA检查项目
    qa_checks = [
        {'project': '项目A', 'check_date': '2024-04-01', 'score': random.randint(85, 95), 'status': '通过', 'issues': random.randint(0, 3)},
        {'project': '项目B', 'check_date': '2024-03-28', 'score': random.randint(75, 88), 'status': '有条件通过', 'issues': random.randint(3, 8)},
        {'project': '项目C', 'check_date': '2024-03-25', 'score': random.randint(88, 98), 'status': '通过', 'issues': random.randint(0, 2)},
        {'project': '项目D', 'check_date': '2024-03-20', 'score': random.randint(70, 85), 'status': '需整改', 'issues': random.randint(8, 15)},
    ]
    
    # 检查项详细
    check_items = {
        '需求管理': {'score': random.randint(80, 95), 'items': 12, 'passed': random.randint(10, 12)},
        '代码质量': {'score': random.randint(75, 90), 'items': 15, 'passed': random.randint(12, 15)},
        '测试管理': {'score': random.randint(85, 95), 'items': 10, 'passed': random.randint(8, 10)},
        '发布管理': {'score': random.randint(80, 92), 'items': 8, 'passed': random.randint(6, 8)},
        '文档管理': {'score': random.randint(70, 88), 'items': 10, 'passed': random.randint(7, 10)},
    }
    
    # 问题闭环
    issue_closure = {
        'total_issues': random.randint(50, 100),
        'closed': random.randint(40, 80),
        'closing_rate': random.randint(75, 95),
        'avg_closure_days': round(random.uniform(3, 10), 1),
        'overdue_issues': random.randint(5, 20)
    }
    
    # QA工作计划
    qa_plans = [
        {'task': 'Q2质量审计', 'start': '2024-04-15', 'end': '2024-05-15', 'progress': random.randint(20, 40), 'owner': 'QA组'},
        {'task': '流程优化专项', 'start': '2024-04-01', 'end': '2024-06-30', 'progress': random.randint(30, 50), 'owner': '流程组'},
        {'task': '工具平台建设', 'start': '2024-03-01', 'end': '2024-08-01', 'progress': random.randint(40, 60), 'owner': '工具组'},
    ]
    
    return {
        'qa_checks': qa_checks,
        'check_items': check_items,
        'issue_closure': issue_closure,
        'qa_plans': qa_plans
    }
