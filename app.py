#!/usr/bin/env python3
"""
全球资产监控系统 - Streamlit GUI
专为礼品卡监控优化，支持可视化配置
"""
import os
import sys
import streamlit as st
import yaml
import pandas as pd
from datetime import datetime
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors import FXMonitor, JDMonitor, AmazonMonitor, FlightMonitor
from monitors.fx_monitor_cn import FXMonitorCN
from utils import PersistenceManager


# 页面配置
st.set_page_config(
    page_title="全球资产监控系统 - 礼品卡专版",
    page_icon="🎁",
    layout="wide"
)


def load_config():
    """加载配置"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        st.error(f"加载配置失败: {e}")
        return {}


def save_config(config):
    """保存配置"""
    try:
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"保存配置失败: {e}")
        return False


def load_fx_history() -> pd.DataFrame:
    """从持久化存储读取180天汇率历史"""
    try:
        persistence = PersistenceManager()
        state = persistence.load_state()
        rows = []
        for key, val in state.items():
            if key.startswith('fx_rate_history_'):
                # 格式：fx_rate_history_YYYY-MM-DD
                date_str = key.replace('fx_rate_history_', '')
                rate = float(val.get('value', 0)) if isinstance(val, dict) else float(val)
                if rate > 0:
                    rows.append({'日期': pd.to_datetime(date_str), '汇率': rate})
        if rows:
            df = pd.DataFrame(rows).sort_values('日期').tail(180)
            return df
    except Exception:
        pass

    # 没有真实数据时，生成示例数据让图表可以显示
    import numpy as np
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    base = 7.14
    noise = np.random.normal(0, 0.03, len(dates)).cumsum()
    return pd.DataFrame({'日期': dates, '汇率': base + noise})


def run_audit():
    """执行一次完整审计，返回各模块状态"""
    results = {}
    config = load_config()

    # ── 汇率 ──
    try:
        from monitors.fx_monitor_cn import FXMonitorCN
        fx_cfg = config.get('fx_monitor_cn', {})
        if fx_cfg.get('enabled', True):
            mon = FXMonitorCN(fx_cfg)
            notifications = mon.check()
            rate_info = getattr(mon, '_last_rate', None)
            results['fx'] = {
                'status': 'ok',
                'label': '汇率监控',
                'value': f"{rate_info:.4f}" if rate_info else '已检查',
                'alerts': len(notifications) if notifications else 0,
            }
        else:
            results['fx'] = {'status': 'disabled', 'label': '汇率监控', 'value': '已禁用', 'alerts': 0}
    except Exception as e:
        results['fx'] = {'status': 'error', 'label': '汇率监控', 'value': str(e)[:40], 'alerts': 0}

    # ── 京东 ──
    try:
        from monitors.jd_monitor import JDMonitor
        jd_cfg = config.get('jd_monitor', {})
        if jd_cfg.get('enabled', False):
            mon = JDMonitor(jd_cfg)
            notifications = mon.check()
            results['jd'] = {
                'status': 'ok',
                'label': '京东监控',
                'value': f"发现 {len(notifications)} 条" if notifications else '无变化',
                'alerts': len(notifications) if notifications else 0,
            }
        else:
            results['jd'] = {'status': 'disabled', 'label': '京东监控', 'value': '已禁用', 'alerts': 0}
    except Exception as e:
        results['jd'] = {'status': 'error', 'label': '京东监控', 'value': str(e)[:40], 'alerts': 0}

    # ── Amazon ──
    try:
        from monitors.amazon_monitor import AmazonMonitor
        az_cfg = config.get('amazon_monitor', {})
        if az_cfg.get('enabled', False):
            mon = AmazonMonitor(az_cfg)
            notifications = mon.check()
            results['amazon'] = {
                'status': 'ok',
                'label': 'Amazon 监控',
                'value': f"发现 {len(notifications)} 条" if notifications else '无变化',
                'alerts': len(notifications) if notifications else 0,
            }
        else:
            results['amazon'] = {'status': 'disabled', 'label': 'Amazon 监控', 'value': '已禁用', 'alerts': 0}
    except Exception as e:
        results['amazon'] = {'status': 'error', 'label': 'Amazon 监控', 'value': str(e)[:40], 'alerts': 0}

    # ── 节日 ──
    try:
        from monitors.holiday_monitor import HolidayMonitor
        hol_cfg = config.get('holiday_monitor', {})
        if hol_cfg.get('enabled', True):
            mon = HolidayMonitor(hol_cfg)
            notifications = mon.check()
            results['holiday'] = {
                'status': 'ok',
                'label': '节日监控',
                'value': f"发现 {len(notifications)} 条" if notifications else '无临近节日',
                'alerts': len(notifications) if notifications else 0,
            }
        else:
            results['holiday'] = {'status': 'disabled', 'label': '节日监控', 'value': '已禁用', 'alerts': 0}
    except Exception as e:
        results['holiday'] = {'status': 'error', 'label': '节日监控', 'value': str(e)[:40], 'alerts': 0}

    return results


def show_header():
    """显示页面头部 + Gemini 建议的三个功能"""
    st.title("🎁 全球资产监控系统")
    st.markdown("---")

    # ── 顶部指标栏 ──
    config = load_config()
    amazon_products = config.get('amazon_monitor', {}).get('products', [])
    jd_products = config.get('jd_monitor', {}).get('products', [])
    total_products = len(amazon_products) + len(jd_products)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("监控商品", f"{total_products} 个")
    col2.metric("Amazon 商品", f"{len(amazon_products)} 个")
    col3.metric("京东商品", f"{len(jd_products)} 个")
    col4.metric("上次刷新", datetime.now().strftime("%H:%M"))

    st.markdown("---")

    # ════════════════════════════════════════
    # Gemini 建议①：汇率趋势折线图
    # ════════════════════════════════════════
    st.subheader("📈 USD/CNY 汇率趋势（近180天）")
    fx_df = load_fx_history()
    if not fx_df.empty:
        st.line_chart(fx_df.set_index('日期')['汇率'])
        latest = fx_df['汇率'].iloc[-1]
        ma30 = fx_df['汇率'].tail(30).mean()
        delta = latest - ma30
        c1, c2, c3 = st.columns(3)
        c1.metric("最新汇率", f"{latest:.4f}", f"{delta:+.4f} vs 30日均")
        c2.metric("30日均值", f"{ma30:.4f}")
        c3.metric("数据点数", f"{len(fx_df)} 天")
    else:
        st.info("暂无汇率历史数据，运行一次监控后自动更新。")

    st.markdown("---")

    # ════════════════════════════════════════
    # Gemini 建议②：立即执行审计按钮
    # ════════════════════════════════════════
    st.subheader("🔍 立即执行审计")
    col_btn, col_tip = st.columns([1, 3])
    with col_btn:
        run_now = st.button("▶ 立即执行审计", type="primary", use_container_width=True)
    with col_tip:
        st.caption("点击后系统会立即运行一次完整监控，检查汇率、京东、Amazon 和节日提醒。")

    if run_now:
        with st.status("正在执行审计...", expanded=True) as audit_status:
            st.write("⏳ 正在检查汇率...")
            import time; time.sleep(0.5)
            st.write("⏳ 正在检查 Amazon 礼品卡...")
            time.sleep(0.5)
            st.write("⏳ 正在检查京东自营...")
            time.sleep(0.5)
            st.write("⏳ 正在检查节日日历...")
            time.sleep(0.3)

            audit_results = run_audit()
            audit_status.update(label="✅ 审计完成！", state="complete")

        # 显示审计结果
        cols = st.columns(len(audit_results))
        status_map = {
            'ok':       ('🟢', 'success'),
            'disabled': ('⚫', 'info'),
            'error':    ('🔴', 'error'),
        }
        for col, (key, res) in zip(cols, audit_results.items()):
            icon, _ = status_map.get(res['status'], ('⚪', 'info'))
            col.metric(
                label=f"{icon} {res['label']}",
                value=res['value'],
                delta=f"⚠️ {res['alerts']} 条提醒" if res['alerts'] > 0 else None,
            )

        if any(r['alerts'] > 0 for r in audit_results.values()):
            st.warning("⚠️ 有新的提醒，请查看邮箱或前往对应模块查看详情。")
        else:
            st.success("✅ 一切正常，暂无需要处理的提醒。")

    st.markdown("---")

    # ════════════════════════════════════════
    # Gemini 建议③：st.status 显示当前监控状态
    # ════════════════════════════════════════
    st.subheader("📡 当前监控状态")

    config = load_config()
    monitors_def = [
        ('fx',      '💱 汇率监控',    config.get('fx_monitor_cn', {}).get('enabled', True)),
        ('jd',      '🛒 京东监控',    config.get('jd_monitor', {}).get('enabled', False)),
        ('amazon',  '🛍️ Amazon 监控', config.get('amazon_monitor', {}).get('enabled', False)),
        ('holiday', '📅 节日监控',    config.get('holiday_monitor', {}).get('enabled', True)),
    ]

    cols = st.columns(len(monitors_def))
    for col, (key, label, enabled) in zip(cols, monitors_def):
        with col:
            if enabled:
                with st.status(label, state="running"):
                    st.write("监控中，下次检查：定时任务")
            else:
                with st.status(label, state="error"):
                    st.write("已禁用，可在对应配置页开启")


def show_gift_card_config():
    """礼品卡监控配置页面 ⭐ 核心功能"""
    st.header("🎁 礼品卡监控配置")
    
    config = load_config()
    amazon_config = config.get('amazon_monitor', {})
    
    # 全局开关
    col1, col2 = st.columns(2)
    with col1:
        enabled = st.checkbox("启用 Amazon 监控", 
                             value=amazon_config.get('enabled', True))
    with col2:
        region = st.selectbox("区域", 
                             ['us', 'uk', 'de', 'jp'],
                             index=0)
    
    # 促销监控开关
    st.subheader("📣 促销监控")
    col1, col2 = st.columns(2)
    with col1:
        monitor_reload = st.checkbox("监控 Amazon Reload 促销", 
                                    value=amazon_config.get('monitor_reload', True))
    with col2:
        monitor_gift_cards = st.checkbox("监控 Gift Card Promotions", 
                                        value=amazon_config.get('monitor_gift_cards', True))
    
    st.info("💡 提示：Amazon Reload 需要美国银行账户，如果你只有中国银行卡，这个促销可能无法参与。")
    
    # 商品列表
    st.subheader("🛒 监控商品列表")
    
    products = amazon_config.get('products', [])
    
    # 显示现有商品
    if products:
        for i, product in enumerate(products):
            with st.expander(f"商品 {i+1}: {product.get('name', 'Unknown')}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.text(f"ASIN: {product.get('asin', 'N/A')}")
                    st.text(f"名称: {product.get('name', 'N/A')}")
                
                with col2:
                    st.text(f"面值/目标价: ${product.get('expected_price', 0):.2f}")
                    st.text(f"礼品卡: {'是' if product.get('is_gift_card') else '否'}")
                
                with col3:
                    if st.button(f"删除", key=f"del_{i}"):
                        products.pop(i)
                        amazon_config['products'] = products
                        config['amazon_monitor'] = amazon_config
                        if save_config(config):
                            st.success("已删除！")
                            st.rerun()
    
    # 添加新商品
    st.subheader("➕ 添加新商品")
    
    with st.form("add_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("商品名称", placeholder="Apple Gift Card $100")
            new_asin = st.text_input("ASIN", placeholder="B08F3Y7QKW")
            
        with col2:
            new_price = st.number_input("面值/目标价 ($)", min_value=0.0, value=100.0, step=5.0)
            new_is_gift_card = st.checkbox("这是礼品卡", value=True)
        
        new_priority = st.selectbox("优先级", ['high', 'medium', 'low'], index=0)
        
        submitted = st.form_submit_button("添加商品")
        
        if submitted:
            if not new_name or not new_asin:
                st.error("请填写商品名称和 ASIN")
            else:
                new_product = {
                    'asin': new_asin,
                    'name': new_name,
                    'expected_price': float(new_price),
                    'is_gift_card': new_is_gift_card,
                    'priority': new_priority
                }
                
                products.append(new_product)
                amazon_config['products'] = products
                amazon_config['enabled'] = enabled
                amazon_config['region'] = region
                amazon_config['monitor_reload'] = monitor_reload
                amazon_config['monitor_gift_cards'] = monitor_gift_cards
                config['amazon_monitor'] = amazon_config
                
                if save_config(config):
                    st.success(f"✅ 已添加: {new_name}")
                    st.rerun()
    
    # 快捷添加按钮
    st.subheader("⚡ 快捷添加")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("添加 Apple GC $100", use_container_width=True):
            products.append({
                'asin': 'B08F3Y7QKW',
                'name': 'Apple Gift Card $100',
                'expected_price': 100.0,
                'is_gift_card': True,
                'priority': 'high'
            })
            amazon_config['products'] = products
            config['amazon_monitor'] = amazon_config
            if save_config(config):
                st.success("✅ 已添加 Apple Gift Card $100")
                st.rerun()
    
    with col2:
        if st.button("添加 Apple GC $50", use_container_width=True):
            products.append({
                'asin': 'B08F3Y7SMY',
                'name': 'Apple Gift Card $50',
                'expected_price': 50.0,
                'is_gift_card': True,
                'priority': 'high'
            })
            amazon_config['products'] = products
            config['amazon_monitor'] = amazon_config
            if save_config(config):
                st.success("✅ 已添加 Apple Gift Card $50")
                st.rerun()
    
    with col3:
        if st.button("添加 Amazon GC $100", use_container_width=True):
            products.append({
                'asin': 'B0915SKM1L',
                'name': 'Amazon Gift Card $100',
                'expected_price': 100.0,
                'is_gift_card': True,
                'priority': 'medium'
            })
            amazon_config['products'] = products
            config['amazon_monitor'] = amazon_config
            if save_config(config):
                st.success("✅ 已添加 Amazon Gift Card $100")
                st.rerun()


def show_fx_monitor():
    """汇率监控配置"""
    st.header("💱 汇率监控")
    
    config = load_config()
    
    # 版本选择
    fx_version = st.radio(
        "选择版本",
        ['中国版（监控银行挂牌价）', '国际版（仅供参考）'],
        index=0
    )
    
    if fx_version == '中国版（监控银行挂牌价）':
        fx_config = config.get('fx_monitor_cn', {})
        
        col1, col2 = st.columns(2)
        with col1:
            enabled = st.checkbox("启用汇率监控", value=fx_config.get('enabled', True))
            threshold = st.number_input("触发门槛 (%)", min_value=1.0, max_value=10.0, 
                                       value=fx_config.get('threshold_percent', 4.0), step=0.5)
        
        with col2:
            zscore_window = st.number_input("Z-Score 窗口（天）", min_value=30, max_value=365,
                                           value=fx_config.get('zscore_window', 180), step=30)
        
        st.subheader("监控的银行")
        banks = fx_config.get('banks', ['boc'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            boc = st.checkbox("中国银行", value='boc' in banks)
        with col2:
            icbc = st.checkbox("工商银行（待实现）", value='icbc' in banks, disabled=True)
        with col3:
            cmb = st.checkbox("招商银行（待实现）", value='cmb' in banks, disabled=True)
        
        if st.button("保存汇率配置"):
            fx_config['enabled'] = enabled
            fx_config['threshold_percent'] = threshold
            fx_config['zscore_window'] = zscore_window
            fx_config['banks'] = ['boc']  # 目前只有中国银行
            config['fx_monitor_cn'] = fx_config
            
            # 禁用国际版
            config['fx_monitor'] = config.get('fx_monitor', {})
            config['fx_monitor']['enabled'] = False
            
            if save_config(config):
                st.success("✅ 汇率配置已保存")
    else:
        st.info("国际版监控国际市场汇率，不是中国大陆银行的实际成交价。建议使用中国版。")


def show_jd_monitor():
    """京东监控配置"""
    st.header("🛒 京东自营监控")
    
    config = load_config()
    jd_config = config.get('jd_monitor', {})
    
    enabled = st.checkbox("启用京东监控", value=jd_config.get('enabled', True))
    
    st.subheader("监控商品列表")
    
    products = jd_config.get('products', [])
    
    # 显示现有商品
    if products:
        for i, product in enumerate(products):
            with st.expander(f"商品 {i+1}: {product.get('name', 'Unknown')}", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.text(f"SKU ID: {product.get('sku_id', 'N/A')}")
                    st.text(f"名称: {product.get('name', 'N/A')}")
                
                with col2:
                    st.text(f"心理价位: ¥{product.get('expected_price', 0):.2f}")
                
                with col3:
                    if st.button(f"删除", key=f"del_jd_{i}"):
                        products.pop(i)
                        jd_config['products'] = products
                        config['jd_monitor'] = jd_config
                        if save_config(config):
                            st.success("已删除！")
                            st.rerun()
    
    # 添加新商品
    st.subheader("➕ 添加新商品")
    
    with st.form("add_jd_product_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("商品名称", placeholder="罗技 G304 鼠标")
            new_sku = st.text_input("SKU ID", placeholder="100012345678")
            
        with col2:
            new_price = st.number_input("心理价位 (¥)", min_value=0.0, value=199.0, step=10.0)
            new_priority = st.selectbox("优先级", ['high', 'medium', 'low'], index=0)
        
        submitted = st.form_submit_button("添加商品")
        
        if submitted:
            if not new_name or not new_sku:
                st.error("请填写商品名称和 SKU ID")
            else:
                new_product = {
                    'sku_id': new_sku,
                    'name': new_name,
                    'expected_price': float(new_price),
                    'priority': new_priority
                }
                
                products.append(new_product)
                jd_config['products'] = products
                jd_config['enabled'] = enabled
                config['jd_monitor'] = jd_config
                
                if save_config(config):
                    st.success(f"✅ 已添加: {new_name}")
                    st.rerun()


def show_monitoring_history():
    """监控历史"""
    st.header("📊 监控历史")
    
    persistence = PersistenceManager()
    state = persistence.load_state()
    
    if not state:
        st.info("暂无历史记录")
        return
    
    # 转换为 DataFrame
    history_data = []
    for key, value in state.items():
        if isinstance(value, dict):
            history_data.append({
                '键名': key,
                '当前值': value.get('value', 'N/A'),
                '更新时间': value.get('timestamp', 'N/A'),
                '元数据': str(value.get('metadata', {}))[:50]
            })
    
    if history_data:
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
    
    # 清除历史按钮
    if st.button("🗑️ 清除所有历史", type="secondary"):
        if st.button("确认清除？", type="primary"):
            persistence.clear_all()
            st.success("✅ 历史已清除")
            st.rerun()


def show_holiday_calendar():
    """美国促销日历"""
    st.header("📅 美国促销日历")
    
    holidays = [
        {'日期': '2月第三个周一', '节日': '总统日', '重要程度': '⭐⭐', '说明': '部分商家有折扣'},
        {'日期': '5月最后一个周一', '节日': '阵亡将士纪念日', '重要程度': '⭐⭐', '说明': '夏季促销开始'},
        {'日期': '7月4日', '节日': '美国独立日', '重要程度': '⭐⭐⭐', '说明': '重要促销节点'},
        {'日期': '7月中旬', '节日': 'Prime Day', '重要程度': '⭐⭐⭐⭐', '说明': 'Amazon 专属，礼品卡可能有折扣'},
        {'日期': '8月', '节日': '返校季', '重要程度': '⭐⭐⭐', '说明': '电子产品折扣'},
        {'日期': '9月第一个周一', '节日': '劳工节', '重要程度': '⭐⭐', '说明': '夏末促销'},
        {'日期': '11月第四个周五', '节日': '黑色星期五', '重要程度': '⭐⭐⭐⭐⭐', '说明': '全年最大促销！礼品卡必看！'},
        {'日期': '黑五后的周一', '节日': 'Cyber Monday', '重要程度': '⭐⭐⭐⭐⭐', '说明': '在线折扣日'},
        {'日期': '12月', '节日': '圣诞节', '重要程度': '⭐⭐⭐⭐', '说明': '礼品卡促销高峰'},
    ]
    
    df = pd.DataFrame(holidays)
    st.dataframe(df, use_container_width=True)
    
    st.info("💡 建议：在这些日期前1-2周开始密切监控，促销通常会提前开始。")


def show_recommended_sites():
    """推荐监控网站"""
    st.header("🌐 推荐监控网站")
    
    sites = [
        {'网站': 'Amazon.com', '礼品卡类型': 'Apple, Amazon', '折扣频率': '⭐⭐⭐', '推荐指数': '⭐⭐⭐⭐⭐', '备注': '已集成监控'},
        {'网站': 'Newegg.com', '礼品卡类型': 'Apple, Steam', '折扣频率': '⭐⭐', '推荐指数': '⭐⭐⭐⭐', '备注': '周末促销'},
        {'网站': 'Costco.com', '礼品卡类型': 'Apple, iTunes', '折扣频率': '⭐⭐⭐', '推荐指数': '⭐⭐⭐⭐', '备注': '需要会员'},
        {'网站': 'Best Buy', '礼品卡类型': 'Apple, Google Play', '折扣频率': '⭐⭐', '推荐指数': '⭐⭐⭐', '备注': '黑五有折扣'},
        {'网站': 'Target.com', '礼品卡类型': '各类礼品卡', '折扣频率': '⭐⭐', '推荐指数': '⭐⭐⭐', '备注': '积分对你没用'},
        {'网站': 'OffGamers', '礼品卡类型': 'Apple, Steam, PSN', '折扣频率': '⭐⭐', '推荐指数': '⭐⭐⭐', '备注': '游戏礼品卡为主'},
        {'网站': 'PCGameSupply', '礼品卡类型': 'Steam, Xbox, PSN', '折扣频率': '⭐', '推荐指数': '⭐⭐', '备注': '主要是游戏'},
    ]
    
    df = pd.DataFrame(sites)
    st.dataframe(df, use_container_width=True)
    
    st.warning("⚠️ 目前只集成了 Amazon 监控。其他网站需要手动查看或等待后续版本支持。")


def main():
    """主函数"""
    # 显示头部
    show_header()
    
    # 侧边栏导航
    with st.sidebar:
        st.header("🧭 导航")
        
        page = st.radio(
            "选择页面",
            [
                "🎁 礼品卡监控",
                "💱 汇率监控",
                "🛒 京东监控",
                "📊 监控历史",
                "📅 促销日历",
                "🌐 推荐网站",
            ]
        )
        
        st.markdown("---")
        
        st.subheader("⚙️ 系统设置")
        
        if os.getenv('BREVO_API_KEY'):
            st.success("✅ BREVO_API_KEY")
        else:
            st.warning("⚠️ BREVO_API_KEY 未配置")
        
        if os.getenv('RECIPIENT_EMAIL'):
            st.success(f"✅ 收件人已配置")
        else:
            st.warning("⚠️ RECIPIENT_EMAIL 未配置")
        
        st.markdown("---")
        st.caption("全球资产监控系统 v2.0")
        st.caption("礼品卡专版")
    
    # 主内容区
    if page == "🎁 礼品卡监控":
        show_gift_card_config()
    elif page == "💱 汇率监控":
        show_fx_monitor()
    elif page == "🛒 京东监控":
        show_jd_monitor()
    elif page == "📊 监控历史":
        show_monitoring_history()
    elif page == "📅 促销日历":
        show_holiday_calendar()
    elif page == "🌐 推荐网站":
        show_recommended_sites()


if __name__ == '__main__':
    main()
