"""
TAPD缺陷统计集成模块
复用"tapd质量统计引用"的过滤规则和方法
"""

import asyncio
import aiohttp
from datetime import datetime, timedelta
from collections import defaultdict
import json

# TAPD API配置
API_USER = 'CRUo6eQB'
API_PASSWORD = 'F2A47197-3998-2FBD-F23C-56C287914813'

# 工作空间ID映射
WORKSPACE_MAP = {
    '5.0.0': '33213704',  # V5项目
    '3.0.9': '60475194',  # V3项目
}

# 发布计划ID映射 (用于筛选特定版本的缺陷)
RELEASE_MAP = {
    '3.0.9': '1160475194001000591',  # V3.0.9.2补丁
}

# 默认工作空间ID
DEFAULT_WORKSPACE_ID = '33213704'

# 未修复状态列表
UNFIXED_STATUSES = ['new', 'unconfirmed', '接受', '处理中', '分析中', 'reopen', '重新打开', 'in_progress', '待确认']

# 研发待处理状态（新、接受处理、分析中、重打开）
DEV_PENDING_STATUSES = ['new', '接受处理', '分析中', '重打开', 'reopen', 'new', 'in_progress', '分析中']

# 严重程度映射
SEVERITY_MAP = {
    'fatal': '致命', 'serious': '严重', 'normal': '一般', 'minor': '轻微', 'suggestion': '提示',
    'prompt': '提示', 'advice': '轻微',  # 添加TAPD英文severity映射
    '1': '致命', '2': '严重', '3': '一般', '4': '轻微', '5': '提示'
}

# 严重程度排序和表情
SEVERITY_ORDER = {'致命': 1, '严重': 2, '一般': 3, '轻微': 4, '提示': 5}
SEVERITY_EMOJI = {'致命': '🔴', '严重': '🟠', '一般': '⚪', '轻微': '⚪', '提示': '⚪'}

# DI分数权重
DI_WEIGHTS = {
    '致命': 10,
    '严重': 3,
    '一般': 1,
    '轻微': 0.1,
    '提示': 0.1
}

# 版本节点配置
VERSION_MILESTONES = {
    '5.0.0': {
        '封板日期': '2026-04-08',
        '发布日期': '2026-04-15',
        '状态': '开发中',
        '遗留DI目标': 30
    },
    '3.0.9': {
        '封板日期': '2024-03-30',
        '发布日期': '2024-04-05',
        '状态': '已封板',
        '遗留DI目标': 20
    }
}


class TapdBugStats:
    """TAPD缺陷统计类"""

    def __init__(self):
        self.bugs = []
        self.last_update = None

    async def fetch_all_bugs(self, use_cache=True, workspace_id=None):
        """获取所有缺陷数据

        Args:
            use_cache: 是否使用缓存
            workspace_id: 工作空间ID，None则使用默认
        """
        if workspace_id is None:
            workspace_id = DEFAULT_WORKSPACE_ID

        if use_cache and self.bugs and self.last_update:
            # 如果数据在5分钟内更新过，使用缓存
            if (datetime.now() - self.last_update).seconds < 300:
                return self.bugs

        url = 'https://api.tapd.cn/bugs'
        auth = aiohttp.BasicAuth(API_USER, API_PASSWORD)
        all_bugs = []
        page = 1

        async with aiohttp.ClientSession() as session:
            while True:
                params = {
                    'workspace_id': workspace_id,
                    'limit': 200,
                    'page': page,
                    'order': 'created desc'
                }
                async with session.get(url, auth=auth, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('status') == 1:
                            bugs_data = data.get('data', [])
                            if not bugs_data:
                                break
                            bugs = [item.get('Bug', {}) for item in bugs_data]
                            all_bugs.extend(bugs)
                            if len(bugs_data) < 200:
                                break
                            page += 1
                        else:
                            break
                    else:
                        break

        self.bugs = all_bugs
        self.last_update = datetime.now()
        return all_bugs

    def is_unfixed_status(self, status):
        """判断是否为未修复状态"""
        if not status:
            return False
        status_lower = str(status).lower()
        return any(s.lower() in status_lower for s in UNFIXED_STATUSES)

    def is_suspended(self, label):
        """判断是否有挂起标签"""
        if not label:
            return False
        return '挂起' in str(label)

    def is_postponed_dev_method(self, bug):
        """判断研发方式是否属于延期到下个迭代或挂起"""
        # custom_field_22字段包含延期方式
        value = bug.get('custom_field_22', '')
        if value and ('延期到下个迭代' in str(value) or '挂起' in str(value)):
            return True
        return False

    def calculate_di_score(self, bugs):
        """计算DI分数

        DI计算方式：
        致命：10分
        严重：3分
        一般：1分
        轻微及以下：0.1分
        """
        total_score = 0
        for bug in bugs:
            severity = self.get_severity_name(bug.get('severity', ''))
            weight = DI_WEIGHTS.get(severity, 0.1)
            total_score += weight
        return round(total_score, 2)

    def filter_legacy_bugs(self, bugs, version_keyword=None):
        """筛选遗留缺陷

        筛选条件：
        - 研发方式(custom_field_22)属于"延期到下个迭代"
        """
        legacy = []
        for bug in bugs:
            # 研发方式属于延期到下个迭代
            if self.is_postponed_dev_method(bug):
                legacy.append(bug)

        return legacy

    def is_requirement_bug(self, bug):
        """判断是否为需求缺陷（关联需求不为空 或 custom_field_10包含新需求测试）"""
        # 标准方式：story_id不为空
        story_id = bug.get('story_id')
        if story_id is not None and str(story_id).strip() != '' and str(story_id) != 'None':
            return True

        # V5项目方式：custom_field_10包含"新需求测试"
        cf10 = bug.get('custom_field_10', '')
        if cf10 and '新需求测试' in str(cf10):
            return True

        return False

    def filter_requirement_bugs(self, bugs):
        """筛选需求缺陷"""
        return [b for b in bugs if self.is_requirement_bug(b)]

    def get_legacy_di_stats(self, version_keyword, bugs=None):
        """获取遗留DI统计

        Args:
            version_keyword: 版本关键词
            bugs: 可选，已过滤的缺陷列表，如果提供则不再进行版本过滤
        """
        # 按版本过滤（包含所有缺陷，不过滤非问题）
        if bugs is None:
            if version_keyword == '3.0.9':
                all_bugs = self.filter_by_version(version_keyword, exclude_duplicate=False,
                                                  exclude_non_issue=False, exclude_copy_label=False)
            else:
                all_bugs = self.filter_by_version(version_keyword, exclude_duplicate=False,
                                                  exclude_non_issue=False)
        else:
            all_bugs = bugs

        # 筛选遗留缺陷
        legacy_bugs = self.filter_legacy_bugs(all_bugs, version_keyword)

        # 计算DI
        di_score = self.calculate_di_score(legacy_bugs)

        # 按严重程度统计
        severity_stats = {}
        for bug in legacy_bugs:
            sev = self.get_severity_name(bug.get('severity', ''))
            severity_stats[sev] = severity_stats.get(sev, 0) + 1

        # 获取版本节点信息
        milestone = VERSION_MILESTONES.get(version_keyword, {})
        milestone_date = milestone.get('封板日期', '')
        release_date = milestone.get('发布日期', '')
        di_target = milestone.get('遗留DI目标', 30)

        # 计算距离封板天数
        days_to_deadline = 0
        if milestone_date:
            from datetime import datetime
            deadline = datetime.strptime(milestone_date, '%Y-%m-%d')
            today = datetime.now()
            days_to_deadline = (deadline - today).days

        return {
            'total_legacy': len(legacy_bugs),
            'di_score': di_score,
            'severity_stats': severity_stats,
            '封板日期': milestone_date,
            '发布日期': release_date,
            'days_to_deadline': days_to_deadline,
            'di_target': di_target,
            'is_over_target': di_score > di_target,
            'legacy_bugs': legacy_bugs[:20]  # 前20条
        }

    def get_requirement_di_stats(self, version_keyword, bugs=None):
        """获取新需求转测DI统计

        Args:
            version_keyword: 版本关键词
            bugs: 可选，已过滤的缺陷列表，如果提供则不再进行版本过滤
        """
        # 按版本过滤
        if bugs is None:
            if version_keyword == '3.0.9':
                all_bugs = self.filter_by_version(version_keyword, exclude_duplicate=False,
                                                  exclude_non_issue=False, exclude_copy_label=False)
            else:
                all_bugs = self.filter_by_version(version_keyword, exclude_duplicate=False,
                                                  exclude_non_issue=False)
        else:
            all_bugs = bugs

        # 筛选需求缺陷（关联需求不为空）
        req_bugs = self.filter_requirement_bugs(all_bugs)

        # 剔除非问题缺陷
        NON_ISSUE_RESOLUTIONS = [
            'ignore', 'external reason', 'duplicated', 'intentional design',
            'unclear description', 'transferred to story', 'feature change'
        ]
        filtered_req_bugs = [b for b in req_bugs
                             if str(b.get('resolution', '')).lower() not in NON_ISSUE_RESOLUTIONS]

        # 计算DI
        di_score = self.calculate_di_score(filtered_req_bugs)

        # 按严重程度统计
        severity_stats = {}
        for bug in filtered_req_bugs:
            sev = self.get_severity_name(bug.get('severity', ''))
            severity_stats[sev] = severity_stats.get(sev, 0) + 1

        return {
            'total_req_bugs': len(filtered_req_bugs),
            'di_score': di_score,
            'severity_stats': severity_stats,
            'req_bugs': filtered_req_bugs[:20]  # 前20条
        }

    def is_rejected_status(self, status):
        """判断是否为已拒绝/关闭状态"""
        if not status:
            return False
        status_lower = str(status).lower()
        rejected_keywords = ['rejected', '已拒绝', '拒绝', 'closed', '已关闭', '关闭']
        return any(kw in status_lower for kw in rejected_keywords)

    # 非问题缺陷的resolution值
    NON_ISSUE_RESOLUTIONS = [
        'ignore',           # 无需解决
        'external reason',  # 外部原因
        'duplicated',       # 重复/复制
        'intentional design',  # 设计如此
        'unclear description', # 问题描述不准确
        'transferred to story', # 已转需求
        'feature change',   # 需求变更
    ]

    def is_duplicate(self, bug):
        """判断是否为复制缺陷"""
        resolution = str(bug.get('resolution', '')).lower()
        return resolution == 'duplicated' or 'duplicated' in resolution

    def is_non_issue(self, bug):
        """判断是否为非问题缺陷"""
        resolution = str(bug.get('resolution', '')).lower()
        return resolution in self.NON_ISSUE_RESOLUTIONS

    def has_copy_label(self, bug):
        """判断是否包含'复制'标签"""
        label = str(bug.get('label', '') or '')
        return '复制' in label

    def is_customer_bug(self, bug):
        """判断是否为客户缺陷（custom_field_one不为空）"""
        cf = bug.get('custom_field_one', '')
        return cf is not None and str(cf).strip() != ''

    def is_internal_bug(self, bug):
        """判断是否为内部缺陷（custom_field_one为空）"""
        return not self.is_customer_bug(bug)

    def is_dev_pending(self, bug):
        """判断是否为研发待处理状态（新、接受处理、分析中、重打开）"""
        status = str(bug.get('status', '')).lower()
        pending_keywords = ['new', '接受', '分析中', '重打开', 'reopen', 'in_progress', 'unconfirmed']
        return any(kw in status for kw in pending_keywords)

    def get_severity_name(self, severity):
        """获取严重程度中文名"""
        return SEVERITY_MAP.get(str(severity).lower(), str(severity))

    def is_version_match(self, bug, version_keyword):
        """检查缺陷的发现版本是否匹配（支持多种格式）"""
        version = bug.get('version_report', '') or bug.get('version', '') or bug.get('found_version', '')
        if not version:
            return False

        version_str = str(version).strip()

        # 标准化版本号：统一去除V前缀，统一处理
        def normalize_ver(v):
            v = v.strip().upper()
            if v.startswith('V'):
                v = v[1:]
            return v

        normalized_keyword = normalize_ver(version_keyword)
        normalized_version = normalize_ver(version_str)

        # 1. 完全匹配（标准化后）
        if normalized_version == normalized_keyword:
            return True

        # 2. 关键字被包含在版本号中（如 3.0.9 匹配 3.0.9.1）
        if normalized_keyword in normalized_version:
            return True

        # 3. 版本号以关键字开头（如 V3.0.9 匹配 V3.0.9.2）
        if normalized_version.startswith(normalized_keyword):
            return True

        return False

    def parse_datetime(self, dt_str):
        """解析日期时间字符串"""
        if not dt_str:
            return None
        try:
            if ' ' in dt_str:
                return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            else:
                return datetime.strptime(dt_str, '%Y-%m-%d')
        except:
            try:
                return datetime.strptime(dt_str[:19], '%Y-%m-%d %H:%M:%S')
            except:
                return None

    def is_today(self, dt_str):
        """判断是否为今天"""
        dt = self.parse_datetime(dt_str)
        if not dt:
            return False
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.date() == today.date()

    def is_in_date_range(self, dt_str, start_date, end_date):
        """判断是否在日期范围内"""
        dt = self.parse_datetime(dt_str)
        if not dt:
            return False
        return start_date <= dt <= end_date

    def filter_by_date_range(self, bugs, start_date=None, end_date=None):
        """按创建日期范围过滤缺陷

        Args:
            bugs: 缺陷列表
            start_date: 开始日期(datetime对象)，包含
            end_date: 结束日期(datetime对象)，包含
        Returns:
            过滤后的缺陷列表
        """
        if not start_date and not end_date:
            return bugs

        filtered = []
        for bug in bugs:
            created_str = bug.get('created', '')
            created_dt = self.parse_datetime(created_str)
            if not created_dt:
                continue

            # 检查是否在范围内
            if start_date and created_dt < start_date:
                continue
            if end_date and created_dt > end_date:
                continue

            filtered.append(bug)

        return filtered

    def get_fixer(self, bug):
        """获取修复人"""
        for field in ['fixed', 'fixer', 'fixed_owner', 'developer', 'current_owner']:
            value = bug.get(field, '')
            if value:
                return value.replace(';', '').strip()
        return '未知'

    def normalize_owner(self, owner):
        """规范化处理人名称"""
        if not owner:
            return '未分配'
        return owner.strip().rstrip(';').strip()

    # ============== 统计方法 ==============

    def filter_unfixed_bugs(self, bugs=None, exclude_suspended=True):
        """过滤未修复缺陷

        Args:
            bugs: 缺陷列表
            exclude_suspended: 是否排除挂起标签的缺陷，默认True
        """
        if bugs is None:
            bugs = self.bugs

        result = [b for b in bugs if self.is_unfixed_status(b.get('status', ''))]

        if exclude_suspended:
            result = [b for b in result if not self.is_suspended(b.get('label', ''))]

        return result

    def filter_by_version(self, version_keyword, bugs=None, exclude_duplicate=True, exclude_non_issue=True, exclude_copy_label=True, use_release_plan=True):
        """按版本过滤缺陷

        Args:
            version_keyword: 版本关键词
            bugs: 缺陷列表，None则使用self.bugs
            exclude_duplicate: 是否剔除复制缺陷（resolution=duplicated），默认True
            exclude_non_issue: 是否剔除非问题缺陷，默认True
            exclude_copy_label: 是否剔除带'复制'标签的缺陷，默认True
            use_release_plan: 3.0.9是否使用发布计划筛选，默认True
        """
        if bugs is None:
            bugs = self.bugs

        # 特殊处理：3.0.9 使用发布计划ID筛选（V3.0.9.2补丁）
        if version_keyword == '3.0.9' and use_release_plan:
            release_id = RELEASE_MAP.get('3.0.9')
            filtered = [b for b in bugs if str(b.get('release_id', '')) == release_id]
        elif version_keyword == '3.0.9':
            # 备用：按发现版本匹配
            filtered = [b for b in bugs if self.is_309_version_match(b)]
        else:
            filtered = [b for b in bugs if self.is_version_match(b, version_keyword)]

        # 剔除带'复制'标签的缺陷
        if exclude_copy_label:
            filtered = [b for b in filtered if not self.has_copy_label(b)]

        # 剔除非问题缺陷
        if exclude_non_issue:
            filtered = [b for b in filtered if not self.is_non_issue(b)]

        # 剔除复制缺陷（resolution=duplicated）- 注意：duplicated已经在NON_ISSUE_RESOLUTIONS中
        if exclude_duplicate:
            filtered = [b for b in filtered if not self.is_duplicate(b)]

        return filtered

    def is_309_version_match(self, bug):
        """检查发现版本是否包含3.0.8或3.0.9（V3.0.8或V3.0.9系列）"""
        version = bug.get('version_report', '') or bug.get('version', '') or ''
        if not version:
            return False
        v = str(version).strip()
        # 匹配包含3.0.8或3.0.9的版本（如V3.0.9、V3.0.8.1、3.0.9.1等）
        if '3.0.8' in v or '3.0.9' in v:
            return True
        return False

    def filter_today_created(self, bugs=None):
        """过滤今日新建的缺陷"""
        if bugs is None:
            bugs = self.bugs
        return [b for b in bugs if self.is_today(b.get('created', ''))]

    def filter_today_fixed(self, bugs=None):
        """过滤今日修复的缺陷"""
        if bugs is None:
            bugs = self.bugs
        return [b for b in bugs if self.is_today(b.get('resolved', ''))]

    def filter_today_rejected(self, bugs=None):
        """过滤今日拒绝/关闭的缺陷"""
        if bugs is None:
            bugs = self.bugs
        return [b for b in bugs
                if self.is_today(b.get('reject_time', ''))
                and self.is_rejected_status(b.get('status', ''))]

    def group_by_severity(self, bugs):
        """按严重程度分组"""
        groups = defaultdict(list)
        for bug in bugs:
            sev = self.get_severity_name(bug.get('severity', '未知'))
            groups[sev].append(bug)
        return dict(groups)

    def group_by_module(self, bugs):
        """按模块分组"""
        groups = defaultdict(list)
        for bug in bugs:
            module = bug.get('module', '未分类') or '未分类'
            groups[module].append(bug)
        return dict(groups)

    def group_by_owner(self, bugs):
        """按处理人分组"""
        groups = defaultdict(list)
        for bug in bugs:
            owner = self.normalize_owner(bug.get('current_owner', ''))
            groups[owner].append(bug)
        return dict(groups)

    def group_by_fixer(self, bugs):
        """按修复人分组"""
        groups = defaultdict(lambda: defaultdict(list))
        for bug in bugs:
            fixer = self.get_fixer(bug)
            severity = self.get_severity_name(bug.get('severity', ''))
            groups[fixer][severity].append(bug)
        return dict(groups)

    def get_severity_stats(self, bugs):
        """获取严重程度统计"""
        groups = self.group_by_severity(bugs)
        stats = {}
        for sev in ['致命', '严重', '一般', '轻微', '提示']:
            stats[sev] = len(groups.get(sev, []))
        return stats

    def get_daily_stats(self, bugs=None):
        """获取今日统计"""
        if bugs is None:
            bugs = self.bugs

        today_created = self.filter_today_created(bugs)
        today_fixed = self.filter_today_fixed(bugs)
        today_rejected = self.filter_today_rejected(bugs)

        return {
            'created': len(today_created),
            'fixed': len(today_fixed),
            'rejected': len(today_rejected),
            'net_change': len(today_created) - len(today_fixed) - len(today_rejected),
            'created_bugs': today_created,
            'fixed_bugs': today_fixed,
            'rejected_bugs': today_rejected
        }

    def get_fixer_leaderboard(self, bugs):
        """获取修复人榜单"""
        fixer_groups = self.group_by_fixer(bugs)

        # 计算每个修复人的总修复数
        fixer_total = {}
        for fixer, sev_groups in fixer_groups.items():
            total = sum(len(bugs) for bugs in sev_groups.values())
            fixer_total[fixer] = total

        # 按修复数排序
        sorted_fixers = sorted(fixer_total.items(), key=lambda x: -x[1])

        leaderboard = []
        for fixer, total in sorted_fixers:
            sev_groups = fixer_groups[fixer]
            sev_stats = {}
            for sev in ['致命', '严重', '一般', '轻微', '提示']:
                sev_stats[sev] = len(sev_groups.get(sev, []))

            leaderboard.append({
                'fixer': fixer,
                'total': total,
                'by_severity': sev_stats
            })

        return leaderboard

    def get_owner_stats(self, bugs):
        """获取处理人统计（按风险排序）"""
        owner_groups = self.group_by_owner(bugs)

        owner_list = []
        for owner, bug_list in owner_groups.items():
            sev_stats = self.get_severity_stats(bug_list)
            fatal = sev_stats.get('致命', 0)
            serious = sev_stats.get('严重', 0)

            # 风险等级
            if fatal > 0:
                risk = '🔴'
                risk_level = '高'
            elif serious >= 3:
                risk = '🟠'
                risk_level = '中高'
            elif serious > 0:
                risk = '🟡'
                risk_level = '中'
            else:
                risk = '🟢'
                risk_level = '低'

            owner_list.append({
                'owner': owner,
                'total': len(bug_list),
                'fatal': fatal,
                'serious': serious,
                'normal': sev_stats.get('一般', 0),
                'risk': risk,
                'risk_level': risk_level
            })

        # 按风险等级排序（致命优先）
        owner_list.sort(key=lambda x: (
            0 if x['risk'] == '🔴' else (1 if x['risk'] == '🟠' else (2 if x['risk'] == '🟡' else 3)),
            -x['fatal'],
            -x['serious'],
            -x['total']
        ))

        return owner_list

    def get_module_stats(self, bugs):
        """获取模块统计"""
        module_groups = self.group_by_module(bugs)

        module_list = []
        for module, bug_list in module_groups.items():
            sev_stats = self.get_severity_stats(bug_list)
            fatal = sev_stats.get('致命', 0)
            serious = sev_stats.get('严重', 0)

            if fatal > 0:
                flag = '🔴'
            elif serious > 0:
                flag = '🟠'
            else:
                flag = '⚪'

            module_list.append({
                'module': module,
                'total': len(bug_list),
                'fatal': fatal,
                'serious': serious,
                'normal': sev_stats.get('一般', 0),
                'flag': flag
            })

        # 按缺陷数排序
        module_list.sort(key=lambda x: -x['total'])

        return module_list

    def get_high_risk_bugs(self, bugs, severity_list=None):
        """获取高风险缺陷（致命、严重）"""
        if severity_list is None:
            severity_list = ['致命', '严重']

        high_risk = []
        for bug in bugs:
            sev = self.get_severity_name(bug.get('severity', ''))
            if sev in severity_list:
                high_risk.append({
                    'id': bug.get('id', ''),
                    'title': bug.get('title', '无标题'),
                    'severity': sev,
                    'module': bug.get('module', '未分类'),
                    'status': bug.get('status', ''),
                    'created': bug.get('created', ''),
                    'modified': bug.get('modified', ''),
                    'description': bug.get('description', '')[:100]  # 前100字符
                })

        # 按严重程度排序
        high_risk.sort(key=lambda x: SEVERITY_ORDER.get(x['severity'], 99))
        return high_risk

    def generate_version_report(self, version_keyword, date_filtered_bugs=None):
        """生成版本质量报告

        Args:
            version_keyword: 版本关键词
            date_filtered_bugs: 已按日期范围过滤的缺陷列表，如果提供则在此基础上进行版本过滤
        """
        # 根据版本关键词获取对应的工作空间ID
        workspace_id = WORKSPACE_MAP.get(version_keyword, DEFAULT_WORKSPACE_ID)

        # 如果是从缓存加载的数据，可能需要重新获取
        if not self.bugs or getattr(self, '_last_workspace_id', None) != workspace_id:
            # 注意：同步方法中不能直接调用异步方法，这里假设bugs已经被正确加载
            pass

        # 确定要使用的缺陷列表
        if date_filtered_bugs is not None:
            # 使用已按日期过滤的缺陷列表
            bugs_to_filter = date_filtered_bugs
        else:
            bugs_to_filter = self.bugs

        # 按版本过滤
        # 3.0.9版本：按发布计划筛选，不过滤复制缺陷，但过滤非问题缺陷
        # 其他版本：保持原有逻辑
        if version_keyword == '3.0.9':
            version_bugs = self.filter_by_version(version_keyword, bugs=bugs_to_filter, exclude_duplicate=False, exclude_non_issue=True, exclude_copy_label=False, use_release_plan=True)
        else:
            version_bugs = self.filter_by_version(version_keyword, bugs=bugs_to_filter, exclude_duplicate=True, exclude_non_issue=True)

        # 未修复缺陷（3.0.9版本不排除挂起标签）
        if version_keyword == '3.0.9':
            unfixed_bugs = self.filter_unfixed_bugs(version_bugs, exclude_suspended=False)
        else:
            unfixed_bugs = self.filter_unfixed_bugs(version_bugs)

        # 今日统计
        daily_stats = self.get_daily_stats(version_bugs)

        # 严重程度统计
        sev_stats = self.get_severity_stats(unfixed_bugs)

        # 模块统计
        module_stats = self.get_module_stats(unfixed_bugs)

        # 高风险缺陷列表（致命、严重）
        high_risk_bugs = self.get_high_risk_bugs(unfixed_bugs, ['致命', '严重'])

        # 按模块统计高风险缺陷
        module_risk_distribution = defaultdict(lambda: {'致命': 0, '严重': 0, 'total': 0})
        for bug in high_risk_bugs:
            module = bug['module']
            sev = bug['severity']
            module_risk_distribution[module][sev] += 1
            module_risk_distribution[module]['total'] += 1

        # 内外部缺陷统计
        customer_bugs = [b for b in version_bugs if self.is_customer_bug(b)]
        internal_bugs = [b for b in version_bugs if self.is_internal_bug(b)]

        # 研发待处理统计（未修复中状态为新、接受处理、分析中、重打开的）
        dev_pending_bugs = [b for b in unfixed_bugs if self.is_dev_pending(b)]

        # 遗留DI统计（版本风险）- 传入已过滤的version_bugs
        legacy_di_stats = self.get_legacy_di_stats(version_keyword, bugs=version_bugs)

        # 新需求转测DI统计 - 传入已过滤的version_bugs
        requirement_di_stats = self.get_requirement_di_stats(version_keyword, bugs=version_bugs)

        return {
            'version': version_keyword,
            'total_bugs': len(version_bugs),
            'unfixed_bugs': len(unfixed_bugs),
            'severity_stats': sev_stats,
            'daily_stats': daily_stats,
            'module_stats': module_stats,
            'high_risk_bugs': high_risk_bugs,
            'high_risk_count': len(high_risk_bugs),
            'module_risk_distribution': dict(module_risk_distribution),
            'unfixed_list': unfixed_bugs,
            # 新增统计
            'customer_bugs_count': len(customer_bugs),
            'internal_bugs_count': len(internal_bugs),
            'dev_pending_count': len(dev_pending_bugs),
            'customer_bugs': customer_bugs[:10],  # 前10条客户缺陷详情
            'internal_bugs': internal_bugs[:10],  # 前10条内部缺陷详情
            'dev_pending_bugs': dev_pending_bugs[:10],  # 前10条研发待处理详情
            # 遗留DI统计
            'legacy_di_stats': legacy_di_stats,
            # 新需求转测DI统计
            'requirement_di_stats': requirement_di_stats,
        }


# 同步包装函数（方便Streamlit调用）
def get_tapd_stats_sync(version_keyword=None, start_date=None, end_date=None):
    """同步获取TAPD统计（用于Streamlit）- 实际调用API

    Args:
        version_keyword: 版本关键词，如 '5.0.0' 或 '3.0.9'
        start_date: 开始日期，格式 'YYYY-MM-DD'，只统计创建时间在此日期之后的缺陷
        end_date: 结束日期，格式 'YYYY-MM-DD'，只统计创建时间在此日期之前的缺陷
    """
    import requests
    from requests.auth import HTTPBasicAuth

    try:
        # 根据版本关键词获取对应的工作空间ID
        workspace_id = WORKSPACE_MAP.get(version_keyword, DEFAULT_WORKSPACE_ID)

        # 使用同步requests直接调用TAPD API
        url = 'https://api.tapd.cn/bugs'
        auth = HTTPBasicAuth(API_USER, API_PASSWORD)
        all_bugs = []
        page = 1

        # 显示进度
        date_range_info = f", 时间范围: {start_date} 至 {end_date}" if start_date and end_date else ""
        print(f"正在从TAPD获取数据 (项目: {version_keyword or '全部'}, 工作空间: {workspace_id}{date_range_info})...")

        # 构建API查询条件 (TAPD API 使用 created 字段进行日期查询)
        # 注意：TAPD API 的 query 参数需要 URL 编码
        import urllib.parse

        # 解析日期范围（用于本地过滤备选）
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
            except:
                pass

        query_conditions = []
        if start_date:
            query_conditions.append(f"created>='{start_date}'")
        if end_date:
            query_conditions.append(f"created<='{end_date}'")

        query_string = " AND ".join(query_conditions) if query_conditions else None
        if query_string:
            print(f"API查询条件: {query_string}")

        while page <= 150:  # 最多150页（30000条），防止无限循环
            params = {
                'workspace_id': workspace_id,
                'limit': 200,
                'page': page,
                'order': 'created desc'
            }

            # 添加日期查询条件 - TAPD API 使用 filter 或 query 参数
            if query_string:
                # TAPD API 使用 filter 参数进行高级查询
                params['filter'] = query_string

            response = requests.get(url, auth=auth, params=params, timeout=30)

            # 打印第一页的请求URL用于调试
            if page == 1:
                print(f"请求URL: {response.url}")

            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 1:
                    bugs_data = data.get('data', [])
                    if not bugs_data:
                        break
                    bugs = [item.get('Bug', {}) for item in bugs_data]

                    # 如果设置了日期筛选，打印第一条缺陷的创建时间进行验证
                    if page == 1 and query_string and bugs:
                        first_bug_created = bugs[0].get('created', 'N/A')
                        last_bug_created = bugs[-1].get('created', 'N/A')
                        print(f"第一条缺陷创建时间: {first_bug_created}")
                        print(f"最后一条缺陷创建时间: {last_bug_created}")

                    all_bugs.extend(bugs)

                    print(f"已获取 {len(all_bugs)} 条缺陷数据...")

                    if len(bugs_data) < 200:
                        break
                    page += 1
                else:
                    print(f"API返回错误: {data.get('info', 'Unknown error')}")
                    break
            else:
                print(f"API请求失败: {response.status_code}, 响应: {response.text[:200]}")
                break

        print(f"总共获取 {len(all_bugs)} 条缺陷数据")

        if not all_bugs:
            return None

        # 使用获取的数据进行统计
        stats = TapdBugStats()
        stats.bugs = all_bugs
        stats.last_update = datetime.now()

        # 本地日期过滤（作为备选，防止API filter不起作用）
        filtered_bugs = all_bugs
        if start_date or end_date:
            filtered_bugs = stats.filter_by_date_range(all_bugs, start_dt, end_dt)
            print(f"本地日期过滤后: {len(filtered_bugs)} 条缺陷")
            # 如果过滤后数据明显减少，说明API filter没有起作用
            if len(filtered_bugs) < len(all_bugs) * 0.8:
                print(f"注意: API filter可能没有生效，已使用本地过滤")

        if version_keyword:
            return stats.generate_version_report(version_keyword, date_filtered_bugs=filtered_bugs)
        else:
            unfixed = stats.filter_unfixed_bugs(filtered_bugs)
            return {
                'version': 'all',
                'total_bugs': len(filtered_bugs),
                'unfixed_bugs': len(unfixed),
                'daily_stats': stats.get_daily_stats(filtered_bugs),
                'severity_stats': stats.get_severity_stats(unfixed),
                'module_stats': stats.get_module_stats(filtered_bugs)[:5],
                'owner_stats': stats.get_owner_stats(unfixed)[:5],
                'fixer_leaderboard': stats.get_fixer_leaderboard(stats.filter_today_fixed(filtered_bugs))[:5]
            }

    except Exception as e:
        print(f"获取TAPD数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None


# 生成模拟数据（当API不可用时）
def generate_mock_tapd_data(version_keyword="5.0.0"):
    """生成TAPD模拟数据 - 根据实际数据纠正"""

    # V5.0.0版本实际数据（发现版本为5.0.0）
    if version_keyword == "5.0.0":
        return {
            'version': version_keyword,
            'total_bugs': 245,
            'unfixed_bugs': 19,  # 0+3+12+4=19
            'severity_stats': {
                '致命': 0,   # 实际数据：致命0个
                '严重': 3,   # 实际数据：严重3个
                '一般': 12,  # 实际数据：一般12个
                '轻微': 0,   # 无轻微
                '提示': 4    # 实际数据：提示/建议4个
            },
            'high_risk_count': 3,  # 严重缺陷3个
            'high_risk_bugs': [
                {
                    'id': '1112001001001002321',
                    'title': '数据库连接池在高并发下出现连接泄漏',
                    'severity': '严重',
                    'module': '连接管理',
                    'status': '处理中',
                    'created': '2024-04-01 10:23:45',
                    'description': '在压测场景下，数据库连接池中的连接无法正常释放，导致连接数持续增长...'
                },
                {
                    'id': '1112001001001002318',
                    'title': '事务回滚机制异常导致数据不一致',
                    'severity': '严重',
                    'module': '事务管理',
                    'status': '接受',
                    'created': '2024-04-02 14:56:12',
                    'description': '在分布式事务场景下，事务回滚时部分节点未能正确回滚，导致数据不一致...'
                },
                {
                    'id': '1112001001001002315',
                    'title': 'SQL执行计划优化器选择错误索引',
                    'severity': '严重',
                    'module': 'SQL引擎',
                    'status': '分析中',
                    'created': '2024-04-03 09:34:28',
                    'description': '对于特定类型的复杂查询，优化器选择了错误的执行计划，导致查询性能下降...'
                }
            ],
            'module_risk_distribution': {
                'SQL引擎': {'致命': 0, '严重': 1, 'total': 1},
                '事务管理': {'致命': 0, '严重': 1, 'total': 1},
                '连接管理': {'致命': 0, '严重': 1, 'total': 1},
            },
            'daily_stats': {
                'created': 5,
                'fixed': 8,
                'rejected': 2,
                'net_change': -5
            },
            'module_stats': [
                {'module': 'SQL引擎', 'total': 8, 'fatal': 0, 'serious': 2, 'normal': 6, 'flag': '🟠'},
                {'module': '存储引擎', 'total': 5, 'fatal': 0, 'serious': 1, 'normal': 3, 'flag': '🟠'},
                {'module': '优化器', 'total': 4, 'fatal': 0, 'serious': 0, 'normal': 3, 'flag': '⚪'},
                {'module': '连接管理', 'total': 2, 'fatal': 0, 'serious': 0, 'normal': 1, 'flag': '⚪'},
            ],
            'owner_stats': [
                {'owner': '张三', 'total': 5, 'fatal': 0, 'serious': 1, 'normal': 4, 'risk': '🟡', 'risk_level': '中'},
                {'owner': '李四', 'total': 4, 'fatal': 0, 'serious': 1, 'normal': 2, 'risk': '🟡', 'risk_level': '中'},
                {'owner': '王五', 'total': 4, 'fatal': 0, 'serious': 1, 'normal': 2, 'risk': '🟡', 'risk_level': '中'},
                {'owner': '赵六', 'total': 3, 'fatal': 0, 'serious': 0, 'normal': 2, 'risk': '⚪', 'risk_level': '低'},
                {'owner': '钱七', 'total': 3, 'fatal': 0, 'serious': 0, 'normal': 2, 'risk': '⚪', 'risk_level': '低'},
            ],
            'fixer_leaderboard': [
                {'fixer': '张三', 'total': 3, 'by_severity': {'致命': 0, '严重': 1, '一般': 2, '轻微': 0, '提示': 0}},
                {'fixer': '李四', 'total': 2, 'by_severity': {'致命': 0, '严重': 1, '一般': 1, '轻微': 0, '提示': 0}},
                {'fixer': '王五', 'total': 2, 'by_severity': {'致命': 0, '严重': 0, '一般': 2, '轻微': 0, '提示': 0}},
            ]
        }

    # 3.0.9版本模拟数据
    if version_keyword == "3.0.9":
        return {
            'version': version_keyword,
            'total_bugs': 156,
            'unfixed_bugs': 12,
            'severity_stats': {
                '致命': 0,
                '严重': 2,
                '一般': 8,
                '轻微': 2,
                '提示': 0
            },
            'high_risk_count': 2,
            'high_risk_bugs': [
                {
                    'id': '1136047519401001021',
                    'title': 'V3版本兼容性问题导致旧数据无法读取',
                    'severity': '严重',
                    'module': '兼容性',
                    'status': '处理中',
                    'created': '2024-03-15 09:23:45',
                    'description': '升级到3.0.9版本后，部分2.x版本创建的数据文件无法正常读取...'
                },
                {
                    'id': '1136047519401001018',
                    'title': 'PSU2补丁安装后性能下降',
                    'severity': '严重',
                    'module': '性能',
                    'status': '分析中',
                    'created': '2024-03-18 14:56:12',
                    'description': '安装PSU2补丁后，某些查询场景性能下降约20%...'
                }
            ],
            'module_risk_distribution': {
                '兼容性': {'致命': 0, '严重': 1, 'total': 1},
                '性能': {'致命': 0, '严重': 1, 'total': 1},
            },
            'daily_stats': {
                'created': 3,
                'fixed': 5,
                'rejected': 1,
                'net_change': -3
            },
            'module_stats': [
                {'module': '兼容性', 'total': 5, 'fatal': 0, 'serious': 1, 'normal': 3, 'flag': '🟠'},
                {'module': '性能', 'total': 4, 'fatal': 0, 'serious': 1, 'normal': 2, 'flag': '🟠'},
                {'module': '存储', 'total': 3, 'fatal': 0, 'serious': 0, 'normal': 2, 'flag': '⚪'},
            ],
        }

    # 其他版本使用默认数据
    return {
        'version': version_keyword,
        'total_bugs': 245,
        'unfixed_bugs': 23,
        'severity_stats': {
            '致命': 2,
            '严重': 8,
            '一般': 10,
            '轻微': 3,
            '提示': 0
        },
        'high_risk_count': 10,
        'high_risk_bugs': [
            {
                'id': '1112001001001002999',
                'title': '示例高风险缺陷',
                'severity': '致命',
                'module': '示例模块',
                'status': '处理中',
                'created': '2024-04-01 10:00:00',
                'description': '这是一个示例高风险缺陷描述...'
            }
        ],
        'module_risk_distribution': {
            '示例模块': {'致命': 1, '严重': 0, 'total': 1},
        },
        'daily_stats': {
            'created': 5,
            'fixed': 8,
            'rejected': 2,
            'net_change': -5
        },
        'module_stats': [
            {'module': 'SQL引擎', 'total': 12, 'fatal': 1, 'serious': 5, 'normal': 6, 'flag': '🔴'},
            {'module': '存储引擎', 'total': 5, 'fatal': 0, 'serious': 2, 'normal': 3, 'flag': '🟠'},
        ],
    }
