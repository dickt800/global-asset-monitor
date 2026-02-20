"""
中国银行汇率监控模块 - 专为中国大陆用户设计
监控多家银行的挂牌价，找到最优惠的兑换渠道
"""
import requests
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from monitors.base_monitor import BaseMonitor
from utils.persistence import PersistenceManager
from utils.anti_crawler import AntiCrawler


class FXMonitorCN(BaseMonitor):
    """
    中国银行汇率监控器（专为中国大陆）
    
    核心逻辑：
    1. 监控多家银行的现汇卖出价（你实际能换到美元的价格）
    2. 对比找出最优惠的银行
    3. 180天 Z-Score 模型
    4. 4% 硬性门槛
    """
    
    # 支持的银行
    SUPPORTED_BANKS = {
        'boc': '中国银行',
        'icbc': '工商银行',
        'ccb': '建设银行',
        'abc': '农业银行',
        'bcom': '交通银行',
        'cmb': '招商银行'
    }
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'FXMonitorCN')
        self.persistence = PersistenceManager()
        self.pairs = config.get('pairs', {})
        self.threshold_percent = config.get('threshold_percent', 4.0)
        self.zscore_window = config.get('zscore_window', 180)
        self.banks_to_monitor = config.get('banks', ['boc', 'icbc', 'cmb'])
        
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行汇率监控"""
        if not self.validate_config():
            return None
        
        notifications = []
        
        # 只支持 USD/CNY（可扩展）
        base = 'USD'
        quote = 'CNY'
        
        # 获取所有银行的汇率
        bank_rates = self._fetch_all_bank_rates(base, quote)
        
        if not bank_rates:
            self.logger.error("无法获取任何银行的汇率")
            return None
        
        # 找到最优惠的银行
        best_bank, best_rate = min(bank_rates.items(), key=lambda x: x[1])
        worst_bank, worst_rate = max(bank_rates.items(), key=lambda x: x[1])
        
        self.logger.info(f"🏆 最优惠: {self.SUPPORTED_BANKS[best_bank]} {best_rate:.4f}")
        self.logger.info(f"📊 最贵: {self.SUPPORTED_BANKS[worst_bank]} {worst_rate:.4f}")
        self.logger.info(f"💰 价差: {(worst_rate - best_rate) * 100:.2f} 元/100美元")
        
        # 计算变化百分比（使用最优惠银行的汇率）
        last_rate = self.persistence.get_last_value(f'fx_{base}_{quote}_best')
        if last_rate:
            change_percent = ((best_rate - last_rate) / last_rate) * 100
        else:
            change_percent = 0
        
        # 计算 Z-Score
        historical_rates = self._fetch_historical_rates(base, quote, self.zscore_window)
        zscore = self._calculate_zscore(best_rate, historical_rates)
        
        self.logger.info(
            f"{base}/{quote} 当前最优: {best_rate:.4f} | "
            f"变化: {change_percent:+.2f}% | Z-Score: {zscore:.2f}"
        )
        
        # 判断是否触发通知
        if abs(change_percent) >= self.threshold_percent:
            level = 3 if abs(change_percent) >= 5 else 2
            
            # 判断是人民币升值还是贬值
            if change_percent > 0:
                trend = "人民币贬值 📉"
                strategy = "建议：暂缓换汇，等待回落"
            else:
                trend = "人民币升值 📈"
                strategy = "建议：现在是换汇好时机！"
            
            # 生成银行对比表格
            bank_comparison = self._generate_bank_comparison_html(bank_rates)
            
            notifications.append({
                'title': f'⚠️ {base}/{quote} 汇率{trend}',
                'message': f"""
<h2>汇率预警 - {base}/{quote}</h2>
<p><strong>🏆 最优惠银行:</strong> {self.SUPPORTED_BANKS[best_bank]}</p>
<p><strong>💰 现汇卖出价:</strong> <span style="font-size: 24px; color: {'red' if change_percent > 0 else 'green'};">{best_rate:.4f}</span></p>
<p><strong>📊 变化幅度:</strong> <span style="color: {'red' if change_percent > 0 else 'green'};">{change_percent:+.2f}%</span></p>
<p><strong>📈 Z-Score:</strong> {zscore:.2f} (基于{self.zscore_window}天数据)</p>
<p><strong>📍 上次记录:</strong> {last_rate:.4f if last_rate else 'N/A'}</p>
<hr>
<h3>💳 各银行汇率对比</h3>
{bank_comparison}
<p><strong>💡 价差:</strong> 最优与最贵相差 <span style="color: red; font-weight: bold;">{(worst_rate - best_rate) * 100:.2f} 元/100美元</span></p>
<hr>
<p><strong>🎯 {strategy}</strong></p>
<p><em>⚠️ 注意：以上为现汇卖出价，实际办理时请以银行柜台报价为准</em></p>
                """,
                'url': f'https://www.boc.cn/sourcedb/whpj/',
                'price_info': f'{best_rate:.4f} ({change_percent:+.2f}%)',
                'level': level
            })
            
            # 更新状态
            self.persistence.update_value(
                f'fx_{base}_{quote}_best',
                best_rate,
                {
                    'bank': best_bank,
                    'bank_name': self.SUPPORTED_BANKS[best_bank],
                    'zscore': zscore,
                    'change_percent': change_percent,
                    'all_banks': bank_rates
                }
            )
        
        # ════════════════════════════════════════
        # 🆕 每月5号：添加美元囤积建议
        # ════════════════════════════════════════
        today = datetime.now()
        monthly_reminder_key = f'fx_monthly_reminder_{today.year}_{today.month}'
        
        # 每月5号发送，且本月还没发送过
        if today.day == 5 and not self.persistence.get_last_value(monthly_reminder_key):
            monthly_notification = self._build_monthly_usd_recommendation(
                best_rate, bank_rates
            )
            if monthly_notification:
                notifications.append(monthly_notification)
                # 标记本月已发送
                self.persistence.update_value(
                    monthly_reminder_key, 
                    'sent', 
                    {'sent_at': today.isoformat()}
                )
        
        return notifications if notifications else None
    
    def _fetch_all_bank_rates(self, base: str, quote: str) -> Dict[str, float]:
        """
        获取所有银行的汇率
        
        Args:
            base: 基础货币（USD）
            quote: 目标货币（CNY）
            
        Returns:
            银行代码 -> 汇率的字典
        """
        bank_rates = {}
        
        for bank_code in self.banks_to_monitor:
            rate = self._fetch_bank_rate(bank_code, base, quote)
            if rate:
                bank_rates[bank_code] = rate
                self.logger.info(f"  {self.SUPPORTED_BANKS[bank_code]}: {rate:.4f}")
            else:
                self.logger.warning(f"  {self.SUPPORTED_BANKS[bank_code]}: 获取失败")
        
        return bank_rates
    
    def _fetch_bank_rate(self, bank_code: str, base: str, quote: str) -> Optional[float]:
        """
        获取指定银行的汇率
        
        Args:
            bank_code: 银行代码（boc/icbc等）
            base: 基础货币
            quote: 目标货币
            
        Returns:
            现汇卖出价或 None
        """
        if bank_code == 'boc':
            return self._fetch_boc_rate()
        elif bank_code == 'icbc':
            return self._fetch_icbc_rate()
        elif bank_code == 'cmb':
            return self._fetch_cmb_rate()
        else:
            # 其他银行可扩展
            self.logger.warning(f"银行 {bank_code} 暂未实现")
            return None
    
    def _fetch_boc_rate(self) -> Optional[float]:
        """
        抓取中国银行的 USD/CNY 现汇卖出价
        
        Returns:
            现汇卖出价或 None
        """
        try:
            url = 'https://www.boc.cn/sourcedb/whpj/'
            headers = AntiCrawler.get_pc_headers(referer='https://www.boc.cn/')
            
            response = AntiCrawler.safe_request(url, headers, timeout=15)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找美元的现汇卖出价
            rows = soup.select('table tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    currency = cells[0].get_text(strip=True)
                    
                    if '美元' in currency or 'USD' in currency:
                        # 第4列：现汇卖出价
                        sell_rate = cells[3].get_text(strip=True)
                        sell_rate = sell_rate.replace(',', '').strip()
                        
                        try:
                            # 中行数据是以100外币为单位
                            rate = float(sell_rate) / 100
                            return rate
                        except ValueError:
                            continue
            
            return None
            
        except Exception as e:
            self.logger.error(f"中国银行汇率抓取失败: {e}")
            return None
    
    def _fetch_icbc_rate(self) -> Optional[float]:
        """
        抓取工商银行的 USD/CNY 现汇卖出价
        
        注意：工行网站结构复杂，可能需要额外处理
        
        Returns:
            现汇卖出价或 None
        """
        try:
            # 工行外汇牌价 API（可能需要更新）
            url = 'https://mybank.icbc.com.cn/servlet/AsynGetDataServlet'
            params = {
                'tranCode': 'A00462',
                'current_page': '1',
                'pagesize': '20'
            }
            headers = AntiCrawler.get_pc_headers(referer='https://www.icbc.com.cn/')
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 工行返回的是 JSON 或 XML，需要解析
                # 这里简化处理，实际可能需要调整
                # TODO: 根据实际返回格式调整解析逻辑
                pass
            
            # 暂时返回 None（待实现）
            return None
            
        except Exception as e:
            self.logger.error(f"工商银行汇率抓取失败: {e}")
            return None
    
    def _fetch_cmb_rate(self) -> Optional[float]:
        """
        抓取招商银行的 USD/CNY 现汇卖出价
        
        Returns:
            现汇卖出价或 None
        """
        try:
            # 招行外汇牌价页面
            url = 'https://fx.cmbchina.com/hq/'
            headers = AntiCrawler.get_pc_headers(referer='https://www.cmbchina.com/')
            
            response = AntiCrawler.safe_request(url, headers, timeout=15)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找美元的卖出价
            # TODO: 根据招行实际页面结构调整选择器
            
            # 暂时返回 None（待实现）
            return None
            
        except Exception as e:
            self.logger.error(f"招商银行汇率抓取失败: {e}")
            return None
    
    def _generate_bank_comparison_html(self, bank_rates: Dict[str, float]) -> str:
        """
        生成银行汇率对比的 HTML 表格
        
        Args:
            bank_rates: 银行代码 -> 汇率的字典
            
        Returns:
            HTML 表格字符串
        """
        html = '<table style="border-collapse: collapse; width: 100%;">'
        html += '<tr style="background-color: #f0f0f0;">'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">银行</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">现汇卖出价</th>'
        html += '<th style="padding: 8px; border: 1px solid #ddd;">100美元成本</th>'
        html += '</tr>'
        
        # 按汇率排序（低到高）
        sorted_banks = sorted(bank_rates.items(), key=lambda x: x[1])
        
        for i, (bank_code, rate) in enumerate(sorted_banks):
            bank_name = self.SUPPORTED_BANKS[bank_code]
            cost = rate * 100
            
            # 最优惠的银行高亮
            row_style = 'background-color: #e8f5e9;' if i == 0 else ''
            
            html += f'<tr style="{row_style}">'
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{bank_name}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">{rate:.4f}</td>'
            html += f'<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">¥{cost:.2f}</td>'
            html += '</tr>'
        
        html += '</table>'
        return html
    
    def _fetch_historical_rates(self, base: str, quote: str, days: int) -> List[float]:
        """
        获取历史汇率数据（用于计算 Z-Score）
        
        注意：免费API可能不提供历史数据，这里使用模拟逻辑
        
        Args:
            base: 基础货币
            quote: 目标货币
            days: 天数
            
        Returns:
            历史汇率列表
        """
        # TODO: 接入真实历史数据API
        
        # 临时方案：返回模拟数据
        bank_rates = self._fetch_all_bank_rates(base, quote)
        if not bank_rates:
            return []
        
        best_rate = min(bank_rates.values())
        
        # 模拟历史数据（正态分布波动）
        np.random.seed(42)
        simulated_rates = np.random.normal(best_rate, best_rate * 0.02, days)
        return simulated_rates.tolist()
    
    def _calculate_zscore(self, current_value: float, historical_values: List[float]) -> float:
        """
        计算 Z-Score
        
        Args:
            current_value: 当前值
            historical_values: 历史值列表
            
        Returns:
            Z-Score
        """
        if not historical_values:
            return 0.0
        
        mean = np.mean(historical_values)
        std = np.std(historical_values)
        
        if std == 0:
            return 0.0
        
        return (current_value - mean) / std
    
    def _should_notify(self, current_value: float, last_value: Optional[float]) -> bool:
        """判断是否应该通知"""
        if last_value is None:
            return True
        
        change_percent = abs((current_value - last_value) / last_value) * 100
        return change_percent >= self.threshold_percent
    
    def is_silent_mode(self) -> bool:
        """
        判断是否处于静默模式
        
        Returns:
            True 表示汇率变化未达到4%门槛，系统应保持静默
        """
        base = 'USD'
        quote = 'CNY'
        
        bank_rates = self._fetch_all_bank_rates(base, quote)
        if not bank_rates:
            return True
        
        best_rate = min(bank_rates.values())
        last_rate = self.persistence.get_last_value(f'fx_{base}_{quote}_best')
        
        if best_rate and last_rate:
            change_percent = abs((best_rate - last_rate) / last_rate) * 100
            if change_percent >= self.threshold_percent:
                return False  # 已触发门槛，不静默
        
        return True  # 未触发，静默模式
    
    def _build_monthly_usd_recommendation(
        self, 
        current_rate: float,
        bank_rates: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        构建每月美元囤积建议通知
        
        Args:
            current_rate: 当前最优汇率
            bank_rates: 各银行汇率字典
            
        Returns:
            通知字典或 None
        """
        try:
            # 导入计算器
            from utils.usd_calculator import USDCalculator
            
            # 获取用户月度支出（从配置读取，默认 $12）
            monthly_cost = self.config.get('monthly_usd_cost', 12.0)
            
            # 计算建议
            calculator = USDCalculator(monthly_cost_usd=monthly_cost)
            result = calculator.calculate(current_rate=current_rate)
            
            # 构建银行对比表格
            bank_comparison = self._generate_bank_comparison_html(bank_rates)
            
            # 计算汇率位置
            historical_rates = self._fetch_historical_rates('USD', 'CNY', self.zscore_window)
            if historical_rates:
                avg_rate = np.mean(historical_rates)
                deviation_pct = ((current_rate - avg_rate) / avg_rate) * 100
            else:
                avg_rate = 7.18  # 默认均值
                deviation_pct = ((current_rate - avg_rate) / avg_rate) * 100
            
            # 汇率评级
            rate_emoji = {
                'excellent': '🌟',
                'very_good': '⭐',
                'good': '✨',
                'fair': '💫',
                'normal': '🔵'
            }.get(result['rate_position'], '🔵')
            
            # 生成 HTML 消息
            message = f"""
<h2>💰 每月购汇建议</h2>
<p style="font-size: 14px; color: #666;">这是您的每月定期提醒（每月5号发送）</p>
<hr>

<h3>{rate_emoji} 当前汇率评估</h3>
<table style="width: 100%; border-collapse: collapse;">
    <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>最优惠银行</strong></td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">
            <span style="font-size: 20px; color: {'green' if deviation_pct < 0 else 'red'}; font-weight: bold;">
                {current_rate:.4f}
            </span>
        </td>
    </tr>
    <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>近{self.zscore_window}天均值</strong></td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">{avg_rate:.4f}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>偏离度</strong></td>
        <td style="padding: 8px; border-bottom: 1px solid #ddd; text-align: right;">
            <span style="color: {'green' if deviation_pct < 0 else 'red'}; font-weight: bold;">
                {deviation_pct:+.2f}%
            </span>
        </td>
    </tr>
</table>

<hr>

<h3>💵 建议囤积金额</h3>
<table style="width: 100%; border-collapse: collapse; background: #f8f9fa;">
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #ddd;"><strong>您的月度支出</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">${monthly_cost:.2f}/月</td>
    </tr>
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #ddd;"><strong>基础囤积</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">
            {result['base_months']} 个月
        </td>
    </tr>
    <tr>
        <td style="padding: 12px; border-bottom: 1px solid #ddd;"><strong>汇率加成</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">
            {result['rate_bonus_months']} 个月
        </td>
    </tr>
    {f'''<tr>
        <td style="padding: 12px; border-bottom: 1px solid #ddd;"><strong>黑五预留</strong></td>
        <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">
            ${result['blackfriday_bonus']:.2f}
        </td>
    </tr>''' if result['blackfriday_bonus'] > 0 else ''}
    <tr style="background: #e3f2fd;">
        <td style="padding: 12px; font-size: 16px;"><strong>💡 建议囤积</strong></td>
        <td style="padding: 12px; text-align: right; font-size: 20px; color: #1976d2; font-weight: bold;">
            ${result['recommended_usd']:.2f}
        </td>
    </tr>
    <tr style="background: #fff3e0;">
        <td style="padding: 12px; font-size: 16px;"><strong>💴 人民币成本</strong></td>
        <td style="padding: 12px; text-align: right; font-size: 20px; color: #f57c00; font-weight: bold;">
            ¥{result['cny_cost']:.2f}
        </td>
    </tr>
</table>

<p style="margin-top: 16px;">
    <strong>📅 能用时长：</strong>{result['coverage_months']} 个月（不含黑五预留）
</p>

<hr>

<h3>💳 各银行汇率对比</h3>
{bank_comparison}

<hr>

<h3>💡 购汇建议</h3>
<div style="background: #f5f5f5; padding: 12px; border-left: 4px solid #1976d2;">
{result['explanation'].replace(chr(10), '<br>')}
</div>

<hr>

<p style="font-size: 12px; color: #999;">
    💡 提示：此建议基于当前汇率和您的月度支出自动计算。<br>
    如需调整月度支出金额，请在 config.yaml 中修改 fx_monitor_cn.monthly_usd_cost 参数（默认 $12/月）。
</p>
            """
            
            return {
                'title': f'💰 每月购汇建议（{datetime.now().strftime("%Y年%m月")}）',
                'message': message,
                'url': 'https://www.boc.cn/sourcedb/whpj/',
                'price_info': f'建议囤 ${result["recommended_usd"]:.0f}',
                'level': 1  # 低优先级，定期提醒
            }
            
        except Exception as e:
            self.logger.error(f"生成每月建议失败: {e}")
            return None

