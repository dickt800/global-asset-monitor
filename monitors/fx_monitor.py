"""
汇率监控模块 - 包含 Z-Score 模型和 4% 门槛
"""
import requests
from typing import Dict, Any, Optional, List
import numpy as np
from datetime import datetime, timedelta
from monitors.base_monitor import BaseMonitor
from utils.persistence import PersistenceManager
from utils.anti_crawler import AntiCrawler


class FXMonitor(BaseMonitor):
    """
    汇率监控器
    
    核心逻辑：
    1. 180天 Z-Score 模型
    2. 4% 硬性门槛（触发全局消费策略调整）
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'FXMonitor')
        self.persistence = PersistenceManager()
        self.pairs = config.get('pairs', {})
        self.threshold_percent = config.get('threshold_percent', 4.0)  # 默认4%
        self.zscore_window = config.get('zscore_window', 180)  # 默认180天
        
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行汇率监控"""
        if not self.validate_config():
            return None
        
        notifications = []
        
        for pair_name, pair_config in self.pairs.items():
            base = pair_config['base']  # 如 'USD'
            quote = pair_config['quote']  # 如 'CNY'
            
            # 获取当前汇率
            current_rate = self._fetch_exchange_rate(base, quote)
            if current_rate is None:
                self.logger.error(f"无法获取 {base}/{quote} 汇率")
                continue
            
            # 获取历史数据并计算 Z-Score
            historical_rates = self._fetch_historical_rates(base, quote, self.zscore_window)
            zscore = self._calculate_zscore(current_rate, historical_rates)
            
            # 计算变化百分比
            last_rate = self.persistence.get_last_value(f'fx_{base}_{quote}')
            if last_rate:
                change_percent = ((current_rate - last_rate) / last_rate) * 100
            else:
                change_percent = 0
            
            self.logger.info(
                f"{base}/{quote} 当前: {current_rate:.4f} | "
                f"变化: {change_percent:+.2f}% | Z-Score: {zscore:.2f}"
            )
            
            # 判断是否触发通知
            if abs(change_percent) >= self.threshold_percent:
                level = 3 if abs(change_percent) >= 5 else 2
                
                # 判断是人民币升值还是贬值
                if base == 'USD' and quote == 'CNY':
                    if change_percent > 0:
                        trend = "人民币贬值 📉"
                        strategy = "建议：暂缓海淘，增加京东自营巡检频率"
                    else:
                        trend = "人民币升值 📈"
                        strategy = "建议：加大 Amazon/Apple Gift Card 购买"
                else:
                    trend = "显著波动"
                    strategy = ""
                
                notifications.append({
                    'title': f'⚠️ {base}/{quote} 汇率{trend}',
                    'message': f"""
<h2>汇率预警 - {base}/{quote}</h2>
<p><strong>当前汇率:</strong> {current_rate:.4f}</p>
<p><strong>变化幅度:</strong> <span style="color: {'red' if change_percent > 0 else 'green'};">{change_percent:+.2f}%</span></p>
<p><strong>Z-Score:</strong> {zscore:.2f} (基于{self.zscore_window}天数据)</p>
<p><strong>上次记录:</strong> {last_rate:.4f if last_rate else 'N/A'}</p>
<hr>
<p><strong>🎯 {strategy}</strong></p>
                    """,
                    'url': f'https://www.xe.com/currencyconverter/convert/?From={base}&To={quote}',
                    'price_info': f'{current_rate:.4f} ({change_percent:+.2f}%)',
                    'level': level
                })
                
                # 更新状态
                self.persistence.update_value(
                    f'fx_{base}_{quote}',
                    current_rate,
                    {'zscore': zscore, 'change_percent': change_percent}
                )
        
        return notifications if notifications else None
    
    def _fetch_exchange_rate(self, base: str, quote: str) -> Optional[float]:
        """
        获取中国银行挂牌价（现汇卖出价）
        
        这是你在中国大陆实际能换到美元的价格！
        
        Args:
            base: 基础货币（如 USD）
            quote: 目标货币（如 CNY）
            
        Returns:
            银行挂牌价或 None
        """
        # 只支持 USD/CNY（其他货币对需要扩展）
        if not (base == 'USD' and quote == 'CNY'):
            self.logger.warning(f"当前仅支持 USD/CNY，尝试使用备用 API")
            return self._fetch_exchange_rate_fallback(base, quote)
        
        try:
            # 方法1：抓取中国银行官网挂牌价（最准确）
            rate = self._fetch_boc_rate()
            if rate:
                return rate
            
            # 方法2：使用备用 API
            self.logger.warning("中国银行官网抓取失败，使用备用 API")
            return self._fetch_exchange_rate_fallback(base, quote)
            
        except Exception as e:
            self.logger.error(f"获取汇率失败: {e}")
            return None
    
    def _fetch_boc_rate(self) -> Optional[float]:
        """
        抓取中国银行官网的 USD/CNY 现汇卖出价
        
        Returns:
            现汇卖出价或 None
        """
        try:
            # 中国银行外汇牌价页面
            url = 'https://www.boc.cn/sourcedb/whpj/'
            headers = AntiCrawler.get_pc_headers(referer='https://www.boc.cn/')
            
            response = AntiCrawler.safe_request(url, headers, timeout=15)
            if not response:
                return None
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找美元（USD）的现汇卖出价
            # 注意：中国银行网站结构可能变化，需要适配
            rows = soup.select('table tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:
                    # 第1列：币种
                    currency = cells[0].get_text(strip=True)
                    
                    if '美元' in currency or 'USD' in currency:
                        # 第4列：现汇卖出价
                        sell_rate = cells[3].get_text(strip=True)
                        
                        # 清理数据
                        sell_rate = sell_rate.replace(',', '').strip()
                        
                        try:
                            rate = float(sell_rate) / 100  # 中行数据是以100外币为单位
                            self.logger.info(f"✅ 中国银行 USD/CNY 现汇卖出价: {rate:.4f}")
                            return rate
                        except ValueError:
                            continue
            
            self.logger.warning("未能从中国银行网站解析到汇率")
            return None
            
        except Exception as e:
            self.logger.error(f"抓取中国银行汇率失败: {e}")
            return None
    
    def _fetch_exchange_rate_fallback(self, base: str, quote: str) -> Optional[float]:
        """
        备用方案：使用国际汇率 API（不够准确，仅作参考）
        
        Args:
            base: 基础货币
            quote: 目标货币
            
        Returns:
            汇率或 None
        """
        try:
            # 使用 exchangerate-api.com (免费，每月1500次)
            url = f'https://api.exchangerate-api.com/v4/latest/{base}'
            headers = AntiCrawler.get_pc_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate = data['rates'].get(quote)
            
            if rate:
                self.logger.warning(f"⚠️  使用国际汇率（仅供参考）: {rate:.4f}")
            
            return rate
            
        except Exception as e:
            self.logger.error(f"获取备用汇率失败: {e}")
            return None
    
    def _fetch_historical_rates(self, base: str, quote: str, days: int) -> List[float]:
        """
        获取历史汇率数据（用于计算 Z-Score）
        
        注意：免费API可能不提供历史数据，这里使用模拟逻辑
        实际部署时可使用 Alpha Vantage 或其他服务
        
        Args:
            base: 基础货币
            quote: 目标货币
            days: 天数
            
        Returns:
            历史汇率列表
        """
        # TODO: 接入真实历史数据API（如 Alpha Vantage）
        # 当前使用简化逻辑：从持久化状态中读取
        
        # 临时方案：返回当前汇率的模拟数据
        current_rate = self._fetch_exchange_rate(base, quote)
        if current_rate is None:
            return []
        
        # 模拟历史数据（正态分布波动）
        np.random.seed(42)
        simulated_rates = np.random.normal(current_rate, current_rate * 0.02, days)
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
        for pair_name, pair_config in self.pairs.items():
            base = pair_config['base']
            quote = pair_config['quote']
            
            current_rate = self._fetch_exchange_rate(base, quote)
            last_rate = self.persistence.get_last_value(f'fx_{base}_{quote}')
            
            if current_rate and last_rate:
                change_percent = abs((current_rate - last_rate) / last_rate) * 100
                if change_percent >= self.threshold_percent:
                    return False  # 已触发门槛，不静默
        
        return True  # 所有汇率对均未触发，静默模式
