"""
美国节日完整配置 - 最终版
"""

HOLIDAYS_CONFIG = {

    # ════════════════════════════════════════════════════
    # ⭐⭐⭐⭐⭐ 一级：必查，每天盯
    # ════════════════════════════════════════════════════

    "black_friday": {
        "name_en": "Black Friday",
        "name_cn": "黑色星期五",
        "importance": 5,
        "rule": "november_fourth_friday",
        "advance_notify_days": 7,
        "search_query": "Black Friday 2026 date",
        "description": "全年最大促销，礼品卡折扣最大",
        "strategy": "提前一周开始，每天查 Amazon + Newegg，一直到 Cyber Monday",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": True,
    },

    "cyber_monday": {
        "name_en": "Cyber Monday",
        "name_cn": "网络星期一",
        "importance": 5,
        "rule": "black_friday_plus_3",
        "advance_notify_days": 3,
        "search_query": "Cyber Monday 2026 date",
        "description": "在线折扣日，黑五没买到的最后机会",
        "strategy": "当天重点查 Amazon + Newegg",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": True,
    },

    "prime_day": {
        "name_en": "Prime Day",
        "name_cn": "Prime Day（亚马逊会员日）",
        "importance": 5,
        "rule": "search_required",
        "date": "",
        "search_start": "06-15",
        "search_query": "Amazon Prime Day 2026 date",
        "fallback_notify_date": "07-01",
        "advance_notify_days": 2,
        "description": "Amazon 专属，Apple 礼品卡可能打折",
        "strategy": "公布日期后提前2天开始每天查",
        "links": [
            "https://www.amazon.com/prime",
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": True,
    },

    # ════════════════════════════════════════════════════
    # ⭐⭐⭐⭐ 二级：重点查
    # ════════════════════════════════════════════════════

    "christmas": {
        "name_en": "Christmas",
        "name_cn": "圣诞节",
        "importance": 4,
        "rule": "fixed_date",
        "month": 12, "day": 25,
        "advance_notify_days": 14,
        "description": "圣诞礼品卡促销高峰，全月都有折扣",
        "strategy": "12月每周末查一次，12月20日后每天查",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/gift-cards/",
        ],
        "notify_friend": True,
    },

    "independence_day": {
        "name_en": "Independence Day",
        "name_cn": "美国独立日",
        "importance": 4,
        "rule": "fixed_date",
        "month": 7, "day": 4,
        "advance_notify_days": 3,
        "description": "7月4日，夏季重要促销节点，礼品卡可能有折扣",
        "strategy": "提前3天开始查，当天重点看",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "back_to_school": {
        "name_en": "Back to School",
        "name_cn": "返校季",
        "importance": 4,
        "rule": "fixed_date",
        "month": 8, "day": 1,
        "advance_notify_days": 0,
        "description": "整个8月，电子产品和礼品卡可能有折扣",
        "strategy": "8月每个周末查一次 Amazon + Newegg",
        "extra_note": "Best Buy 返校季折扣也不错",
        "links": [
            "https://www.amazon.com/b?node=5092709011",
            "https://www.newegg.com/promotions/nepro/index.html",
            "https://www.bestbuy.com/site/back-to-school/",
        ],
        "notify_friend": False,
    },

    "amazon_fall_sale": {
        "name_en": "Amazon Fall Sale / Prime Big Deal Days",
        "name_cn": "亚马逊秋季大促",
        "importance": 4,
        "rule": "search_required",
        "date": "",
        "search_start": "09-15",
        "search_query": "Amazon Prime Big Deal Days 2026 date fall sale October",
        "fallback_notify_date": "10-01",
        "advance_notify_days": 2,
        "description": "Amazon 秋季促销（通常10月），类似第二个 Prime Day",
        "strategy": "等日期公布后，按 Prime Day 策略查价",
        "extra_note": "名字每年可能不同：Prime Big Deal Days / Fall Sale 等",
        "links": [
            "https://www.amazon.com/prime",
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": True,
    },

    # ════════════════════════════════════════════════════
    # ⭐⭐⭐ 三级：顺便查，花5分钟
    # ════════════════════════════════════════════════════

    "thanksgiving": {
        "name_en": "Thanksgiving",
        "name_cn": "感恩节",
        "importance": 3,
        "rule": "november_fourth_thursday",
        "advance_notify_days": 1,
        "description": "黑五前一天，部分商家提前开启黑五促销",
        "strategy": "当天查一次，可能有提前黑五折扣",
        "extra_note": "和黑五一起看，不需要单独花太多时间",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    "labor_day": {
        "name_en": "Labor Day",
        "name_cn": "劳工节",
        "importance": 3,
        "rule": "september_first_monday",
        "advance_notify_days": 3,
        "search_query": "Labor Day 2026 date",
        "description": "9月第一个周一，夏末促销，部分礼品卡有折扣",
        "strategy": "前一个周末查一次，当天再查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "memorial_day": {
        "name_en": "Memorial Day",
        "name_cn": "阵亡将士纪念日",
        "importance": 3,
        "rule": "may_last_monday",
        "advance_notify_days": 2,
        "search_query": "Memorial Day 2026 date",
        "description": "5月末，夏季促销开始信号",
        "strategy": "前一个周末查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "presidents_day": {
        "name_en": "Presidents' Day",
        "name_cn": "总统日",
        "importance": 3,
        "rule": "february_third_monday",
        "advance_notify_days": 2,
        "search_query": "Presidents Day 2026 date",
        "description": "2月第三个周一，电子产品偶有小折扣",
        "strategy": "前两天查一次即可",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "veterans_day": {
        "name_en": "Veterans Day",
        "name_cn": "退伍军人节",
        "importance": 3,
        "rule": "fixed_date",
        "month": 11, "day": 11,
        "advance_notify_days": 2,
        "description": "11月11日，部分商家有促销，正好是黑五前两周热身期",
        "strategy": "提前2天查一次，顺便观察黑五预热折扣",
        "extra_note": "离黑五很近，可以顺便感受一下黑五前的市场",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "new_year_sale": {
        "name_en": "New Year Sale",
        "name_cn": "元旦促销",
        "importance": 3,
        "rule": "fixed_date",
        "month": 1, "day": 1,
        "advance_notify_days": 2,
        "description": "元旦前后，圣诞剩余库存清仓，有时比圣诞折扣更大",
        "strategy": "12月31日和1月1日各查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "halloween": {
        "name_en": "Halloween",
        "name_cn": "万圣节",
        "importance": 3,
        "rule": "fixed_date",
        "month": 10, "day": 31,
        "advance_notify_days": 2,
        "description": "10月31日，亚马逊秋季大促结束后的小尾巴，偶有折扣",
        "strategy": "当天顺便查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    "super_bowl": {
        "name_en": "Super Bowl",
        "name_cn": "超级碗",
        "importance": 3,
        "rule": "search_required",
        "date": "",
        "search_start": "01-10",
        "search_query": "Super Bowl 2026 date",
        "fallback_notify_date": "01-20",
        "advance_notify_days": 3,
        "description": "2月第二个周日，电视/电子产品大促，礼品卡可能连带打折",
        "strategy": "提前3天查一次 Amazon + Newegg 电子产品区",
        "extra_note": "主要是电视机大促销，礼品卡折扣不一定，顺便看看",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    # ════════════════════════════════════════════════════
    # ⭐⭐ 四级：可选，看心情
    # ════════════════════════════════════════════════════

    "valentines_day": {
        "name_en": "Valentine's Day",
        "name_cn": "情人节",
        "importance": 2,
        "rule": "fixed_date",
        "month": 2, "day": 14,
        "advance_notify_days": 2,
        "description": "偶尔有礼品卡小折扣",
        "strategy": "顺便查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    "amazon_spring_sale": {
        "name_en": "Amazon Spring Sale",
        "name_cn": "亚马逊春季大促",
        "importance": 2,
        "rule": "search_required",
        "date": "",
        "search_start": "03-01",
        "search_query": "Amazon Spring Sale 2026 date",
        "fallback_notify_date": "03-20",
        "advance_notify_days": 2,
        "description": "3-4月，Amazon 近年新增的春季促销",
        "strategy": "等日期公布后查一次",
        "extra_note": "规律性不强，有的年份没有",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    # ════════════════════════════════════════════════════
    # 📅 特殊：每周固定提醒
    # ════════════════════════════════════════════════════

    "newegg_weekend": {
        "name_en": "Newegg Weekend Deals",
        "name_cn": "Newegg 周末促销",
        "importance": 3,
        "rule": "every_saturday",
        "description": "Newegg 几乎每周末都有促销，礼品卡偶尔打折",
        "strategy": "每周六花5分钟看一眼，有礼品卡折扣才动手",
        "extra_note": "不需要每次都买，看到礼品卡折扣才动手",
        "links": [
            "https://www.newegg.com/promotions/nepro/index.html",
            "https://www.newegg.com/gift-cards/",
        ],
        "notify_friend": False,
    },
}

        "name_en": "Black Friday",
        "name_cn": "黑色星期五",
        "importance": 5,
        "rule": "november_fourth_friday",
        # 2026年：11月27日
        "advance_notify_days": 7,        # 提前7天开始每天提醒
        "daily_remind_until": 0,         # 一直到当天
        "search_query": "Black Friday 2026 date",
        "description": "全年最大促销，礼品卡折扣最大",
        "strategy": "提前一周开始，每天查 Amazon + Newegg，一直到 Cyber Monday",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": True,           # 也通知朋友
    },

    "cyber_monday": {
        "name_en": "Cyber Monday",
        "name_cn": "网络星期一",
        "importance": 5,
        "rule": "black_friday_plus_3",
        # 2026年：11月30日
        "advance_notify_days": 3,
        "daily_remind_until": 0,
        "search_query": "Cyber Monday 2026 date",
        "description": "在线折扣日，黑五没买到的最后机会",
        "strategy": "当天重点查 Amazon + Newegg",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": True,
    },

    "prime_day": {
        "name_en": "Prime Day",
        "name_cn": "Prime Day（亚马逊会员日）",
        "importance": 5,
        "rule": "search_required",       # 需要Google检索
        "date": "",                       # 等公布后填写或检索自动填写
        "search_start": "06-15",          # 6月15日开始检索
        "search_query": "Amazon Prime Day 2026 date",
        "fallback_notify_date": "07-01",  # 7月1日还没找到，发提醒
        "advance_notify_days": 2,
        "daily_remind_until": 0,
        "description": "Amazon 专属，Apple 礼品卡可能打折",
        "strategy": "公布日期后提前2天开始每天查",
        "links": [
            "https://www.amazon.com/prime",
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": True,
    },

    "christmas": {
        "name_en": "Christmas",
        "name_cn": "圣诞节",
        "importance": 4,
        "rule": "fixed_date",
        "month": 12,
        "day": 25,
        "advance_notify_days": 14,       # 提前两周提醒
        "description": "圣诞礼品卡促销高峰，全月都有折扣",
        "strategy": "12月每周末查一次，12月20日后每天查",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/gift-cards/",
        ],
        "notify_friend": True,
    },

    # ================================================
    # ⭐⭐⭐⭐ 二级：重要（值得专门查价）
    # ================================================

    "independence_day": {
        "name_en": "Independence Day",
        "name_cn": "美国独立日",
        "importance": 4,
        "rule": "fixed_date",
        "month": 7,
        "day": 4,
        "advance_notify_days": 3,
        "description": "7月4日，夏季重要促销节点",
        "strategy": "提前3天开始查，当天重点看",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "back_to_school": {
        "name_en": "Back to School",
        "name_cn": "返校季",
        "importance": 4,
        "rule": "fixed_date",
        "month": 8,
        "day": 1,                        # 整个8月，以8月1日为提醒时间
        "advance_notify_days": 0,
        "description": "整个8月，电子产品和礼品卡可能有折扣",
        "strategy": "8月每个周末查一次 Amazon + Newegg",
        "links": [
            "https://www.amazon.com/b?node=5092709011",  # Amazon 返校季页面
            "https://www.newegg.com/promotions/nepro/index.html",
            "https://www.bestbuy.com/site/back-to-school/",
        ],
        "notify_friend": False,
        "extra_note": "Best Buy 返校季折扣也不错，可以顺便看看",
    },

    "labor_day": {
        "name_en": "Labor Day",
        "name_cn": "劳工节",
        "importance": 3,
        "rule": "september_first_monday",
        # 2026年：9月7日
        "advance_notify_days": 3,
        "search_query": "Labor Day 2026 date",
        "description": "夏末促销，部分电子产品和礼品卡有折扣",
        "strategy": "前一个周末查一次，当天再查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "new_year_sale": {
        "name_en": "New Year Sale",
        "name_cn": "新年促销",
        "importance": 3,
        "rule": "fixed_date",
        "month": 1,
        "day": 1,
        "advance_notify_days": 2,
        "description": "元旦前后，圣诞剩余库存清仓，可能有大折扣",
        "strategy": "12月31日和1月1日各查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
        "extra_note": "很多商家会清仓，有时比圣诞节折扣更大",
    },

    "memorial_day": {
        "name_en": "Memorial Day",
        "name_cn": "阵亡将士纪念日",
        "importance": 3,
        "rule": "may_last_monday",
        # 2026年：5月25日
        "advance_notify_days": 2,
        "search_query": "Memorial Day 2026 date",
        "description": "5月末，夏季促销开始信号，部分商家有折扣",
        "strategy": "前一个周末查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    "presidents_day": {
        "name_en": "Presidents' Day",
        "name_cn": "总统日",
        "importance": 3,
        "rule": "february_third_monday",
        # 2026年：2月16日
        "advance_notify_days": 2,
        "search_query": "Presidents Day 2026 date",
        "description": "2月，电子产品偶有小折扣，礼品卡可能有小优惠",
        "strategy": "前两天查一次即可",
        "links": [
            "https://www.amazon.com/gift-cards",
            "https://www.newegg.com/promotions/nepro/index.html",
        ],
        "notify_friend": False,
    },

    # ================================================
    # ⭐⭐⭐ 三级：补充（小折扣，顺便看看）
    # ================================================

    "thanksgiving": {
        "name_en": "Thanksgiving",
        "name_cn": "感恩节",
        "importance": 3,
        "rule": "november_fourth_thursday",
        # 2026年：11月26日（黑五前一天）
        "advance_notify_days": 1,
        "description": "黑五前一天，部分商家提前开启黑五促销",
        "strategy": "当天查一次，可能有提前黑五折扣",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
        "extra_note": "和黑五一起看，不需要单独花太多时间",
    },

    "amazon_fall_sale": {
        "name_en": "Amazon Fall Sale / Prime Big Deal Days",
        "name_cn": "亚马逊秋季大促",
        "importance": 3,
        "rule": "search_required",
        "date": "",
        "search_start": "09-15",         # 9月中旬开始检索
        "search_query": "Amazon Prime Big Deal Days 2026 date fall sale",
        "fallback_notify_date": "10-01",
        "advance_notify_days": 2,
        "description": "Amazon 近年新增的秋季促销（10月），类似 Prime Day",
        "strategy": "等日期公布后，按 Prime Day 策略查价",
        "links": [
            "https://www.amazon.com/prime",
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": True,
        "extra_note": "2023年叫 Prime Big Deal Days，2024年叫 Fall Sale，名字可能变",
    },

    "halloween_sale": {
        "name_en": "Halloween Sale",
        "name_cn": "万圣节促销",
        "importance": 2,
        "rule": "fixed_date",
        "month": 10,
        "day": 31,
        "advance_notify_days": 3,
        "description": "10月末，部分商家有促销，为黑五热身",
        "strategy": "顺便查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    "valentines_day": {
        "name_en": "Valentine's Day",
        "name_cn": "情人节",
        "importance": 2,
        "rule": "fixed_date",
        "month": 2,
        "day": 14,
        "advance_notify_days": 3,
        "description": "偶尔有礼品卡小折扣，主要是送礼场景",
        "strategy": "顺便查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
    },

    "amazon_spring_sale": {
        "name_en": "Amazon Spring Sale",
        "name_cn": "亚马逊春季促销",
        "importance": 2,
        "rule": "search_required",
        "date": "",
        "search_start": "03-01",
        "search_query": "Amazon Spring Sale 2026 date",
        "fallback_notify_date": "03-20",
        "advance_notify_days": 2,
        "description": "Amazon 近年新增的春季促销（3-4月）",
        "strategy": "等日期公布后查一次",
        "links": [
            "https://www.amazon.com/gift-cards",
        ],
        "notify_friend": False,
        "extra_note": "近年 Amazon 促销越来越多，这个规律性不强",
    },

    # ================================================
    # 📅 特殊：Newegg 周末提醒（每周）
    # ================================================

    "newegg_weekend": {
        "name_en": "Newegg Weekend Deals",
        "name_cn": "Newegg 周末促销",
        "importance": 3,
        "rule": "every_saturday",        # 每周六提醒
        "description": "Newegg 几乎每周末都有促销，礼品卡偶尔打折",
        "strategy": "每周六收到提醒，花5分钟看一眼",
        "links": [
            "https://www.newegg.com/promotions/nepro/index.html",
            "https://www.newegg.com/gift-cards/",
        ],
        "notify_friend": False,
        "extra_note": "不需要每次都买，看到礼品卡折扣才动手",
        # 注意：周末提醒会发送给你，不会发给朋友（防止打扰）
    },
}


# ================================================
# 节日重要程度说明
# ================================================

IMPORTANCE_GUIDE = {
    5: {
        "level": "必查",
        "emoji": "🔥",
        "strategy": "提前一周开始，每天查",
        "holidays": ["black_friday", "cyber_monday", "prime_day"],
    },
    4: {
        "level": "重点查",
        "emoji": "⭐",
        "strategy": "提前几天开始，当天重点查",
        "holidays": ["christmas", "independence_day", "back_to_school"],
    },
    3: {
        "level": "顺便查",
        "emoji": "📅",
        "strategy": "提前通知，花5分钟查一次",
        "holidays": [
            "labor_day", "memorial_day", "presidents_day",
            "thanksgiving", "new_year_sale", "amazon_fall_sale",
            "newegg_weekend",
        ],
    },
    2: {
        "level": "可选",
        "emoji": "💡",
        "strategy": "收到通知后，看心情查",
        "holidays": ["halloween_sale", "valentines_day", "amazon_spring_sale"],
    },
}


# ================================================
# 日期计算规则
# ================================================

DATE_RULES = {
    "november_fourth_friday": "11月第四个周五（黑色星期五）",
    "black_friday_plus_3": "黑五后第3天（周一 = Cyber Monday）",
    "september_first_monday": "9月第一个周一（劳工节）",
    "may_last_monday": "5月最后一个周一（阵亡将士纪念日）",
    "february_third_monday": "2月第三个周一（总统日）",
    "november_fourth_thursday": "11月第四个周四（感恩节）",
    "every_saturday": "每周六",
    "fixed_date": "固定日期",
    "search_required": "需要 Google 检索（日期不固定）",
}
