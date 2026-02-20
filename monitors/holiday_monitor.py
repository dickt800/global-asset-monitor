"""
美国节日监控模块 - 完整版
自动检索节日日期并通知用户，支持混合方案
"""
import re
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from monitors.base_monitor import BaseMonitor
from monitors.holidays_config import HOLIDAYS_CONFIG
from utils.persistence import PersistenceManager


class HolidayMonitor(BaseMonitor):
    """
    美国节日监控器（完整版）
    
    支持的节日：
    ⭐⭐⭐⭐⭐ 黑色星期五、Cyber Monday、Prime Day
    ⭐⭐⭐⭐   圣诞节、独立日、返校季
    ⭐⭐⭐     劳工节、阵亡将士纪念日、总统日、感恩节
               元旦促销、亚马逊秋季大促、Newegg周末
    ⭐⭐        万圣节、情人节、亚马逊春季促销
    
    混合方案：
    - 优先：Google Custom Search API 检索真实日期
    - 保底：固定日期 / 算法计算
    - 结果：万无一失
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'HolidayMonitor')
        self.persistence = PersistenceManager()
        self.year = datetime.now().year

        # 从 config.yaml 读取启用的节日（默认全部启用）
        self.enabled_holidays = config.get(
            'holidays', list(HOLIDAYS_CONFIG.keys())
        )

        # Google Search API（可选）
        self.google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.google_cx = os.getenv('GOOGLE_SEARCH_CX')
        self.search_enabled = bool(self.google_api_key and self.google_cx)

    # ──────────────────────────────────────────────
    # 主入口
    # ──────────────────────────────────────────────

    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行所有节日监控"""
        if not self.validate_config():
            return None

        notifications = []
        today = datetime.now()

        for holiday_id, cfg in HOLIDAYS_CONFIG.items():
            if holiday_id not in self.enabled_holidays:
                continue

            result = self._check_holiday(holiday_id, cfg, today)
            if result:
                notifications.append(result)

        return notifications if notifications else None

    # ──────────────────────────────────────────────
    # 节日分发逻辑
    # ──────────────────────────────────────────────

    def _check_holiday(self, holiday_id, cfg, today):
        rule = cfg.get('rule', 'fixed_date')

        if rule == 'every_saturday':
            return self._check_weekly(holiday_id, cfg, today)
        elif rule == 'search_required':
            return self._check_searchable(holiday_id, cfg, today)
        else:
            date = self._resolve_date(rule, cfg, today.year)
            if date:
                return self._check_fixed(holiday_id, cfg, today, date)
        return None

    # ──────────────────────────────────────────────
    # 日期计算
    # ──────────────────────────────────────────────

    def _resolve_date(self, rule: str, cfg: dict, year: int) -> Optional[datetime]:
        """根据规则计算节日日期"""

        if rule == 'fixed_date':
            return datetime(year, cfg['month'], cfg['day'])

        elif rule == 'november_fourth_friday':
            return self._nth_weekday(year, 11, 4, 4)  # 11月，第4个，周五(4)

        elif rule == 'black_friday_plus_3':
            bf = self._nth_weekday(year, 11, 4, 4)
            return bf + timedelta(days=3)

        elif rule == 'september_first_monday':
            return self._nth_weekday(year, 9, 1, 0)  # 9月，第1个，周一(0)

        elif rule == 'may_last_monday':
            return self._last_weekday(year, 5, 0)  # 5月最后一个周一

        elif rule == 'february_third_monday':
            return self._nth_weekday(year, 2, 3, 0)  # 2月，第3个，周一

        elif rule == 'november_fourth_thursday':
            return self._nth_weekday(year, 11, 4, 3)  # 11月，第4个，周四(3)

        return None

    def _nth_weekday(self, year: int, month: int, n: int, weekday: int) -> datetime:
        """计算某月第N个星期X（weekday: 0=周一, 4=周五）"""
        first = datetime(year, month, 1)
        diff = (weekday - first.weekday()) % 7
        first_target = first + timedelta(days=diff)
        return first_target + timedelta(weeks=n - 1)

    def _last_weekday(self, year: int, month: int, weekday: int) -> datetime:
        """计算某月最后一个星期X"""
        # 下个月第一天减一天 = 本月最后一天
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)

        diff = (last_day.weekday() - weekday) % 7
        return last_day - timedelta(days=diff)

    # ──────────────────────────────────────────────
    # 固定日期节日检查
    # ──────────────────────────────────────────────

    def _check_fixed(self, holiday_id, cfg, today, holiday_date) -> Optional[dict]:
        """检查固定日期节日"""
        year = today.year

        # 今年已通知过？跳过
        if self.persistence.get_last_value(f'holiday_notified_{holiday_id}_{year}'):
            return None

        advance = cfg.get('advance_notify_days', 1)
        notify_from = holiday_date - timedelta(days=advance)

        if notify_from.date() <= today.date() < holiday_date.date():
            days_left = (holiday_date.date() - today.date()).days
            notification = self._build_notification(holiday_id, cfg, holiday_date, days_left)

            self.persistence.update_value(
                f'holiday_notified_{holiday_id}_{year}',
                holiday_date.strftime('%Y-%m-%d'),
                {}
            )
            return notification

        return None

    # ──────────────────────────────────────────────
    # 每周提醒（Newegg 周末）
    # ──────────────────────────────────────────────

    def _check_weekly(self, holiday_id, cfg, today) -> Optional[dict]:
        """每周六提醒"""
        if today.weekday() != 5:  # 5 = 周六
            return None

        # 本周是否已发过？
        week_key = f'holiday_weekly_{holiday_id}_{today.strftime("%Y-%W")}'
        if self.persistence.get_last_value(week_key):
            return None

        notification = {
            'title': f'💻 {cfg["name_cn"]} 提醒',
            'message': self._build_weekly_message(cfg),
            'url': cfg['links'][0],
            'price_info': '周末促销',
            'level': 1,
        }

        self.persistence.update_value(week_key, 'sent', {})
        return notification

    # ──────────────────────────────────────────────
    # 需要检索的节日（Prime Day / 亚马逊秋季大促等）
    # ──────────────────────────────────────────────

    def _check_searchable(self, holiday_id, cfg, today) -> Optional[dict]:
        """混合方案：先检索，检索不到用保底"""
        year = today.year

        # 今年已通知过？跳过
        if self.persistence.get_last_value(f'holiday_notified_{holiday_id}_{year}'):
            return None

        # 开始检索的日期
        search_start_str = cfg.get('search_start', '06-15')
        search_start = datetime.strptime(f'{year}-{search_start_str}', '%Y-%m-%d')
        if today < search_start:
            return None  # 还没到开始检索的时间

        # 已经检索到日期了？
        cached_date_str = self.persistence.get_last_value(
            f'holiday_found_{holiday_id}_{year}'
        )
        if cached_date_str:
            holiday_date = datetime.strptime(cached_date_str, '%Y-%m-%d')
            advance = cfg.get('advance_notify_days', 2)
            notify_from = holiday_date - timedelta(days=advance)

            if notify_from.date() <= today.date() < holiday_date.date():
                days_left = (holiday_date.date() - today.date()).days
                notification = self._build_notification(
                    holiday_id, cfg, holiday_date, days_left
                )
                self.persistence.update_value(
                    f'holiday_notified_{holiday_id}_{year}',
                    holiday_date.strftime('%Y-%m-%d'),
                    {}
                )
                return notification
            return None

        # 尝试 Google 检索（每周最多检索一次）
        search_week_key = f'holiday_search_{holiday_id}_{today.strftime("%Y-%W")}'
        if not self.persistence.get_last_value(search_week_key):
            self.persistence.update_value(search_week_key, 'searched', {})
            found_date = self._google_search_date(
                cfg.get('search_query', ''), year
            )

            if found_date:
                self.logger.info(
                    f'✅ 检索到 {cfg["name_cn"]} 日期：{found_date.strftime("%Y-%m-%d")}'
                )
                self.persistence.update_value(
                    f'holiday_found_{holiday_id}_{year}',
                    found_date.strftime('%Y-%m-%d'),
                    {}
                )
                # 立即发一次"日期已公布"通知
                days_left = (found_date.date() - today.date()).days
                return {
                    'title': f'🎉 {cfg["name_cn"]} 日期已公布！',
                    'message': self._build_found_message(cfg, found_date, days_left),
                    'url': cfg['links'][0],
                    'price_info': found_date.strftime('%m月%d日'),
                    'level': 2,
                }
            else:
                self.logger.info(f'⚠️  未检索到 {cfg["name_cn"]} 日期，下周继续')

        # 保底：检索失败截止日期，发手动查提醒
        fallback_str = cfg.get('fallback_notify_date', '07-01')
        fallback_date = datetime.strptime(f'{year}-{fallback_str}', '%Y-%m-%d')
        fallback_key = f'holiday_fallback_{holiday_id}_{year}'

        if today.date() >= fallback_date.date() and \
                not self.persistence.get_last_value(fallback_key):
            self.persistence.update_value(fallback_key, 'sent', {})
            return {
                'title': f'⚠️ {cfg["name_cn"]} 日期未公布，请手动查看',
                'message': self._build_fallback_message(cfg),
                'url': cfg['links'][0],
                'price_info': '请手动确认',
                'level': 2,
            }

        return None

    # ──────────────────────────────────────────────
    # Google Custom Search API
    # ──────────────────────────────────────────────

    def _google_search_date(self, query: str, year: int) -> Optional[datetime]:
        """
        调用 Google Custom Search API 检索节日日期
        配置了 API Key 才会执行，否则直接返回 None（走保底）
        """
        if not self.search_enabled:
            return None

        try:
            resp = requests.get(
                'https://www.googleapis.com/customsearch/v1',
                params={
                    'key': self.google_api_key,
                    'cx': self.google_cx,
                    'q': query,
                    'num': 5,
                },
                timeout=10
            )
            if resp.status_code != 200:
                return None

            items = resp.json().get('items', [])

            for item in items:
                text = item.get('title', '') + ' ' + item.get('snippet', '')
                date = self._extract_date(text, year)
                if date:
                    return date

        except Exception as e:
            self.logger.error(f'Google 检索失败: {e}')

        return None

    def _extract_date(self, text: str, year: int) -> Optional[datetime]:
        """从文本中提取日期"""
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        # 格式1：July 15, 2026 或 July 15-16, 2026
        m = re.search(
            r'(january|february|march|april|may|june|july|august|'
            r'september|october|november|december)\s+(\d{1,2})(?:[-–]\d{1,2})?,?\s+' + str(year),
            text, re.IGNORECASE
        )
        if m:
            month = months[m.group(1).lower()]
            day = int(m.group(2))
            try:
                return datetime(year, month, day)
            except ValueError:
                pass

        # 格式2：2026-07-15
        m2 = re.search(rf'{year}[-/](\d{{1,2}})[-/](\d{{1,2}})', text)
        if m2:
            try:
                return datetime(year, int(m2.group(1)), int(m2.group(2)))
            except ValueError:
                pass

        return None

    # ──────────────────────────────────────────────
    # 邮件内容构建
    # ──────────────────────────────────────────────

    def _build_notification(self, holiday_id, cfg, date, days_left) -> dict:
        importance = cfg.get('importance', 3)
        level = 3 if importance >= 5 else (2 if importance >= 3 else 1)
        emoji = '🔥' if importance >= 5 else ('⭐' if importance >= 4 else '📅')

        return {
            'title': f'{emoji} {cfg["name_cn"]} 还有 {days_left} 天',
            'message': self._build_html_message(cfg, date, days_left),
            'url': cfg['links'][0],
            'price_info': date.strftime('%m月%d日'),
            'level': level,
        }

    def _build_html_message(self, cfg, date, days_left) -> str:
        links_html = ''.join(
            f'<li><a href="{url}">{url}</a></li>'
            for url in cfg.get('links', [])
        )
        extra = f'<p><em>💡 {cfg["extra_note"]}</em></p>' \
            if cfg.get('extra_note') else ''

        return f"""
<h2>{cfg['name_cn']} ({cfg['name_en']})</h2>
<p>📅 <strong>日期：</strong>{date.strftime('%Y年%m月%d日')}</p>
<p>⏰ <strong>距离：</strong>{days_left} 天</p>
<hr>
<p>💡 <strong>节日说明：</strong>{cfg['description']}</p>
<p>🎯 <strong>查价策略：</strong>{cfg['strategy']}</p>
{extra}
<hr>
<h4>🔗 快速链接</h4>
<ul>{links_html}</ul>
"""

    def _build_found_message(self, cfg, date, days_left) -> str:
        return f"""
<h2>🎉 {cfg['name_cn']} 日期已确定！</h2>
<p>系统通过 Google 自动检索到了今年的日期：</p>
<p>📅 <strong>{date.strftime('%Y年%m月%d日')}</strong>（还有 {days_left} 天）</p>
<hr>
<p>🎯 <strong>查价策略：</strong>{cfg['strategy']}</p>
<p>系统将在节日前 {cfg.get('advance_notify_days', 2)} 天再次提醒你。</p>
"""

    def _build_fallback_message(self, cfg) -> str:
        search_url = (
            f"https://www.google.com/search?q="
            f"{cfg.get('search_query','').replace(' ', '+')}"
        )
        return f"""
<h2>⚠️ {cfg['name_cn']} 日期尚未公布</h2>
<p>系统多次检索未能找到今年的确切日期，请手动确认：</p>
<p><a href="{search_url}">👉 点击这里直接搜索</a></p>
<hr>
<p>🎯 <strong>查价策略：</strong>{cfg['strategy']}</p>
<p>找到日期后，你可以在 holidays.yaml 中手动填写，
系统会在日期前 {cfg.get('advance_notify_days', 2)} 天自动提醒你。</p>
"""

    def _build_weekly_message(self, cfg) -> str:
        links_html = ''.join(
            f'<li><a href="{url}">{url}</a></li>'
            for url in cfg.get('links', [])
        )
        return f"""
<h2>💻 {cfg['name_cn']}</h2>
<p>周末到了，花 5 分钟看看有没有礼品卡折扣：</p>
<ul>{links_html}</ul>
<p><em>有折扣就买，没有就算了～</em></p>
"""

    def _should_notify(self, current_value, last_value):
        return True



class HolidayMonitor(BaseMonitor):
    """
    美国节日监控器
    
    功能：
    1. 临近节日时自动 Google 搜索日期
    2. 搜到了 → 通知用户
    3. 没搜到 → 第二天继续搜
    4. 已通知的节日不再重复搜索
    
    支持的节日：
    - Prime Day（7月，日期不固定）
    - Black Friday（11月第四个周五，固定算法）
    - Cyber Monday（黑五后的周一，固定算法）
    - 圣诞节（12月25日，固定）
    - 独立日（7月4日，固定）
    """
    
    # 节日配置
    HOLIDAYS = {
        'prime_day': {
            'name': 'Prime Day',
            'name_cn': 'Prime Day（亚马逊会员日）',
            'search_query': 'Prime Day 2026 date when',
            'month': 7,
            'start_search_day': 1,  # 从 7月1日开始搜索
            'search_keywords': ['july', 'prime day', '2026'],
            'is_fixed': False,  # 日期不固定
            'importance': 5,
            'description': 'Amazon 专属促销，Apple 礼品卡可能打折',
            'strategy': '公布日期后，提前2天开始每天查价'
        },
        'black_friday': {
            'name': 'Black Friday',
            'name_cn': '黑色星期五',
            'search_query': 'Black Friday 2026 date',
            'month': 11,
            'start_search_day': 1,  # 从 11月1日开始搜索
            'search_keywords': ['november', 'black friday', '2026'],
            'is_fixed': True,  # 可以计算（11月第四个周五）
            'importance': 5,
            'description': '全年最大促销，礼品卡必看',
            'strategy': '提前一周（11月20日）开始，每天查价，直到 Cyber Monday'
        },
        'cyber_monday': {
            'name': 'Cyber Monday',
            'name_cn': '网络星期一',
            'search_query': 'Cyber Monday 2026 date',
            'month': 11,
            'start_search_day': 1,  # 从 11月1日开始搜索
            'search_keywords': ['november', 'cyber monday', '2026'],
            'is_fixed': True,  # 黑五后的周一
            'importance': 5,
            'description': '在线折扣日，黑五错过的最后机会',
            'strategy': '当天重点关注'
        },
        'christmas': {
            'name': 'Christmas',
            'name_cn': '圣诞节',
            'search_query': None,  # 不需要搜索，固定日期
            'month': 12,
            'day': 25,
            'is_fixed': True,
            'importance': 4,
            'description': '礼品卡促销高峰',
            'strategy': '12月每周末查一次，圣诞节前一周重点关注'
        },
        'independence_day': {
            'name': 'Independence Day',
            'name_cn': '美国独立日',
            'search_query': None,  # 不需要搜索，固定日期
            'month': 7,
            'day': 4,
            'is_fixed': True,
            'importance': 2,
            'description': '部分商家有小折扣',
            'strategy': '前一天查一次'
        }
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'HolidayMonitor')
        self.persistence = PersistenceManager()
        self.enabled_holidays = config.get('holidays', list(self.HOLIDAYS.keys()))
        
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行节日监控"""
        if not self.validate_config():
            return None
        
        notifications = []
        today = datetime.now()
        current_year = today.year
        
        # 检查每个节日
        for holiday_id, holiday_info in self.HOLIDAYS.items():
            # 跳过未启用的节日
            if holiday_id not in self.enabled_holidays:
                continue
            
            # 检查是否需要搜索/通知
            notification = self._check_holiday(holiday_id, holiday_info, today, current_year)
            if notification:
                notifications.append(notification)
        
        return notifications if notifications else None
    
    def _check_holiday(self, holiday_id: str, holiday_info: Dict[str, Any], 
                      today: datetime, year: int) -> Optional[Dict[str, Any]]:
        """
        检查单个节日
        
        Args:
            holiday_id: 节日ID
            holiday_info: 节日信息
            today: 今天日期
            year: 当前年份
            
        Returns:
            通知数据或 None
        """
        # 检查是否已经通知过今年的这个节日
        notified_key = f'holiday_{holiday_id}_{year}'
        if self.persistence.get_last_value(notified_key):
            return None  # 已通知过，跳过
        
        # 固定日期的节日
        if holiday_info.get('is_fixed') and 'day' in holiday_info:
            return self._check_fixed_holiday(holiday_id, holiday_info, today, year)
        
        # 需要计算的固定节日（如黑五）
        if holiday_info.get('is_fixed') and holiday_id in ['black_friday', 'cyber_monday']:
            return self._check_calculated_holiday(holiday_id, holiday_info, today, year)
        
        # 需要搜索的节日（如 Prime Day）
        if not holiday_info.get('is_fixed'):
            return self._check_searchable_holiday(holiday_id, holiday_info, today, year)
        
        return None
    
    def _check_fixed_holiday(self, holiday_id: str, holiday_info: Dict[str, Any],
                            today: datetime, year: int) -> Optional[Dict[str, Any]]:
        """
        检查固定日期的节日（如圣诞节、独立日）
        
        Args:
            holiday_id: 节日ID
            holiday_info: 节日信息
            today: 今天日期
            year: 当前年份
            
        Returns:
            通知数据或 None
        """
        month = holiday_info['month']
        day = holiday_info['day']
        
        # 构造节日日期
        holiday_date = datetime(year, month, day)
        
        # 计算提前通知时间（根据重要程度）
        importance = holiday_info.get('importance', 3)
        if importance >= 4:
            advance_days = 7  # 提前一周
        elif importance >= 3:
            advance_days = 3  # 提前3天
        else:
            advance_days = 1  # 提前1天
        
        notify_date = holiday_date - timedelta(days=advance_days)
        
        # 检查是否到了通知时间
        if today.date() >= notify_date.date() and today.date() < holiday_date.date():
            # 发送通知
            notification = {
                'title': f'📅 {holiday_info["name_cn"]} 即将到来',
                'message': self._build_holiday_message(holiday_info, holiday_date, advance_days),
                'url': 'https://www.amazon.com/gift-cards',
                'price_info': f'{holiday_date.strftime("%m月%d日")}',
                'level': 2 if importance >= 4 else 1
            }
            
            # 标记为已通知
            self.persistence.update_value(
                f'holiday_{holiday_id}_{year}',
                holiday_date.strftime('%Y-%m-%d'),
                {'notified': True, 'date': holiday_date.strftime('%Y-%m-%d')}
            )
            
            return notification
        
        return None
    
    def _check_calculated_holiday(self, holiday_id: str, holiday_info: Dict[str, Any],
                                  today: datetime, year: int) -> Optional[Dict[str, Any]]:
        """
        检查需要计算的节日（黑五、Cyber Monday）
        
        Args:
            holiday_id: 节日ID
            holiday_info: 节日信息
            today: 今天日期
            year: 当前年份
            
        Returns:
            通知数据或 None
        """
        if holiday_id == 'black_friday':
            # 黑五：11月第四个周五
            holiday_date = self._get_black_friday(year)
        elif holiday_id == 'cyber_monday':
            # Cyber Monday：黑五后的周一
            black_friday = self._get_black_friday(year)
            holiday_date = black_friday + timedelta(days=3)
        else:
            return None
        
        # 提前一周通知（黑五周开始）
        if holiday_id == 'black_friday':
            notify_date = holiday_date - timedelta(days=7)
        else:  # Cyber Monday
            notify_date = holiday_date - timedelta(days=3)
        
        # 检查是否到了通知时间
        if today.date() >= notify_date.date() and today.date() < holiday_date.date():
            notification = {
                'title': f'🔥 {holiday_info["name_cn"]} 即将到来',
                'message': self._build_holiday_message(
                    holiday_info, 
                    holiday_date, 
                    7 if holiday_id == 'black_friday' else 3
                ),
                'url': 'https://www.amazon.com/gift-cards',
                'price_info': f'{holiday_date.strftime("%m月%d日")}',
                'level': 3  # 最高级别
            }
            
            # 标记为已通知
            self.persistence.update_value(
                f'holiday_{holiday_id}_{year}',
                holiday_date.strftime('%Y-%m-%d'),
                {'notified': True, 'date': holiday_date.strftime('%Y-%m-%d')}
            )
            
            return notification
        
        return None
    
    def _check_searchable_holiday(self, holiday_id: str, holiday_info: Dict[str, Any],
                                  today: datetime, year: int) -> Optional[Dict[str, Any]]:
        """
        检查需要搜索的节日（Prime Day）
        
        Args:
            holiday_id: 节日ID
            holiday_info: 节日信息
            today: 今天日期
            year: 当前年份
            
        Returns:
            通知数据或 None
        """
        # 检查是否到了开始搜索的时间
        month = holiday_info['month']
        start_day = holiday_info['start_search_day']
        
        search_start_date = datetime(year, month, start_day)
        
        if today < search_start_date:
            return None  # 还没到搜索时间
        
        # 检查是否已经搜索过并找到了日期
        search_result_key = f'holiday_search_{holiday_id}_{year}'
        cached_result = self.persistence.get_last_value(search_result_key)
        
        if cached_result:
            # 已经搜到了日期
            cached_date = datetime.strptime(cached_result, '%Y-%m-%d')
            
            # 检查是否需要发送提前通知
            notify_date = cached_date - timedelta(days=2)  # 提前2天
            
            if today.date() >= notify_date.date() and today.date() < cached_date.date():
                # 检查是否已经发送过提前通知
                notified_key = f'holiday_{holiday_id}_{year}'
                if not self.persistence.get_last_value(notified_key):
                    notification = {
                        'title': f'📢 {holiday_info["name_cn"]} 日期已确定',
                        'message': self._build_holiday_message(holiday_info, cached_date, 2),
                        'url': 'https://www.amazon.com/',
                        'price_info': f'{cached_date.strftime("%m月%d日")}',
                        'level': 3
                    }
                    
                    # 标记为已通知
                    self.persistence.update_value(
                        notified_key,
                        cached_date.strftime('%Y-%m-%d'),
                        {'notified': True, 'date': cached_date.strftime('%Y-%m-%d')}
                    )
                    
                    return notification
            
            return None
        
        # 需要执行搜索
        self.logger.info(f"开始搜索 {holiday_info['name']} 日期...")
        
        search_query = holiday_info['search_query']
        holiday_date = self._search_holiday_date(search_query, holiday_info['search_keywords'])
        
        if holiday_date:
            self.logger.info(f"✅ 找到 {holiday_info['name']} 日期: {holiday_date.strftime('%Y-%m-%d')}")
            
            # 缓存搜索结果
            self.persistence.update_value(
                search_result_key,
                holiday_date.strftime('%Y-%m-%d'),
                {'found': True, 'date': holiday_date.strftime('%Y-%m-%d')}
            )
            
            # 立即发送通知
            notification = {
                'title': f'📢 {holiday_info["name_cn"]} 日期已公布',
                'message': self._build_holiday_message(holiday_info, holiday_date, 0, just_found=True),
                'url': 'https://www.amazon.com/',
                'price_info': f'{holiday_date.strftime("%m月%d日")}',
                'level': 2
            }
            
            return notification
        else:
            self.logger.info(f"⚠️  未找到 {holiday_info['name']} 日期，明天继续搜索")
            return None
    
    def _search_holiday_date(self, query: str, keywords: List[str]) -> Optional[datetime]:
        """
        使用 Google Custom Search API 搜索节日日期
        
        Args:
            query: 搜索查询
            keywords: 关键词列表
            
        Returns:
            节日日期或 None
        """
        try:
            import os
            import requests
            import re
            from datetime import datetime
            
            # 获取 Google Custom Search API 配置
            api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
            cx = os.getenv('GOOGLE_SEARCH_CX')  # Custom Search Engine ID
            
            if not api_key or not cx:
                self.logger.warning("Google Search API 未配置，跳过搜索")
                return None
            
            # 调用 Google Custom Search API
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cx,
                'q': query,
                'num': 5  # 返回5个结果
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                self.logger.error(f"Google Search API 错误: {response.status_code}")
                return None
            
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                self.logger.info("未找到搜索结果")
                return None
            
            # 从搜索结果中提取日期
            for item in items:
                snippet = item.get('snippet', '')
                title = item.get('title', '')
                text = title + ' ' + snippet
                
                # 尝试匹配日期格式
                # 格式1: July 15, 2026
                match1 = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+2026', text, re.IGNORECASE)
                if match1:
                    month_name = match1.group(1)
                    day = int(match1.group(2))
                    try:
                        date = datetime.strptime(f"{month_name} {day} 2026", "%B %d %Y")
                        self.logger.info(f"找到日期: {date.strftime('%Y-%m-%d')}")
                        return date
                    except:
                        continue
                
                # 格式2: 2026-07-15
                match2 = re.search(r'2026[-/](\d{1,2})[-/](\d{1,2})', text)
                if match2:
                    month = int(match2.group(1))
                    day = int(match2.group(2))
                    try:
                        date = datetime(2026, month, day)
                        self.logger.info(f"找到日期: {date.strftime('%Y-%m-%d')}")
                        return date
                    except:
                        continue
                
                # 格式3: July 15-16, 2026 (Prime Day 可能是两天)
                match3 = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})[-–](\d{1,2}),?\s+2026', text, re.IGNORECASE)
                if match3:
                    month_name = match3.group(1)
                    day = int(match3.group(2))  # 取第一天
                    try:
                        date = datetime.strptime(f"{month_name} {day} 2026", "%B %d %Y")
                        self.logger.info(f"找到日期范围，取第一天: {date.strftime('%Y-%m-%d')}")
                        return date
                    except:
                        continue
            
            self.logger.info("搜索结果中未找到明确日期")
            return None
            
        except Exception as e:
            self.logger.error(f"搜索节日日期失败: {e}")
            return None
    
    def _get_black_friday(self, year: int) -> datetime:
        """
        计算黑色星期五日期（11月第四个周五）
        
        Args:
            year: 年份
            
        Returns:
            黑五日期
        """
        # 11月1日
        nov_1 = datetime(year, 11, 1)
        
        # 找到11月第一个周五
        days_until_friday = (4 - nov_1.weekday()) % 7
        first_friday = nov_1 + timedelta(days=days_until_friday)
        
        # 第四个周五
        black_friday = first_friday + timedelta(weeks=3)
        
        return black_friday
    
    def _build_holiday_message(self, holiday_info: Dict[str, Any], 
                               holiday_date: datetime, 
                               advance_days: int,
                               just_found: bool = False) -> str:
        """
        构建节日通知消息
        
        Args:
            holiday_info: 节日信息
            holiday_date: 节日日期
            advance_days: 提前天数
            just_found: 是否刚刚搜索到
            
        Returns:
            HTML 消息
        """
        name_cn = holiday_info['name_cn']
        name_en = holiday_info['name']
        description = holiday_info['description']
        strategy = holiday_info['strategy']
        
        date_str = holiday_date.strftime('%Y年%m月%d日（%A）')
        days_until = (holiday_date.date() - datetime.now().date()).days
        
        if just_found:
            intro = f"<p><strong>🎉 好消息！</strong>我刚刚搜索到了 {name_cn} 的确切日期！</p>"
        else:
            intro = f"<p><strong>⏰ 提醒！</strong>{name_cn} 即将在 {days_until} 天后到来！</p>"
        
        html = f"""
<h2>{name_cn} ({name_en})</h2>
{intro}
<hr>
<h3>📅 日期信息</h3>
<p><strong>日期：</strong>{date_str}</p>
<p><strong>距离：</strong>{days_until} 天</p>
<hr>
<h3>💡 节日说明</h3>
<p>{description}</p>
<hr>
<h3>🎯 查价策略</h3>
<p>{strategy}</p>
<hr>
<h3>🔗 快速链接</h3>
<ul>
    <li><a href="https://www.amazon.com/gift-cards">Amazon 礼品卡页面</a></li>
    <li><a href="https://www.newegg.com/gift-cards/">Newegg 礼品卡页面</a></li>
</ul>
<p><em>💡 建议：在手机日历中设置提醒，以免错过最佳时机</em></p>
        """
        
        return html
    
    def _should_notify(self, current_value: float, last_value: Optional[float]) -> bool:
        """判断是否应该通知（基类要求实现）"""
        return True
