"""
全局策略引擎 - 汇率与消费联动
"""
from typing import Dict, Any
from monitors.fx_monitor import FXMonitor


class GlobalStrategy:
    """
    全局策略引擎
    
    核心逻辑：
    1. 汇率高位（人民币贬值）→ 加大京东自营巡检频率
    2. 汇率跌破4%（人民币升值）→ 推送 Amazon/Apple Gift Card
    """
    
    def __init__(self, fx_monitor: FXMonitor):
        """
        Args:
            fx_monitor: 汇率监控器实例
        """
        self.fx_monitor = fx_monitor
        
    def should_increase_jd_frequency(self) -> bool:
        """
        判断是否应该增加京东巡检频率
        
        Returns:
            True 表示人民币贬值，应增加京东巡检
        """
        # 获取 USD/CNY 汇率
        from utils.persistence import PersistenceManager
        persistence = PersistenceManager()
        
        current_rate = self.fx_monitor._fetch_exchange_rate('USD', 'CNY')
        last_rate = persistence.get_last_value('fx_USD_CNY')
        
        if current_rate and last_rate:
            change_percent = ((current_rate - last_rate) / last_rate) * 100
            
            # 人民币贬值（USD/CNY 上升）
            if change_percent > 0:
                return True
        
        return False
    
    def should_recommend_amazon(self) -> bool:
        """
        判断是否应该推荐 Amazon 购物
        
        Returns:
            True 表示人民币升值，适合海淘
        """
        from utils.persistence import PersistenceManager
        persistence = PersistenceManager()
        
        current_rate = self.fx_monitor._fetch_exchange_rate('USD', 'CNY')
        last_rate = persistence.get_last_value('fx_USD_CNY')
        
        if current_rate and last_rate:
            change_percent = ((current_rate - last_rate) / last_rate) * 100
            
            # 人民币升值（USD/CNY 下降）且幅度 >= 4%
            if change_percent <= -4.0:
                return True
        
        return False
    
    def should_exchange_usd(self) -> bool:
        """
        判断是否应该换汇（针对0额度信用卡用户）
        
        Returns:
            True 表示现在是换美元的好时机
        """
        from utils.persistence import PersistenceManager
        persistence = PersistenceManager()
        
        current_rate = self.fx_monitor._fetch_exchange_rate('USD', 'CNY')
        last_rate = persistence.get_last_value('fx_USD_CNY')
        
        if current_rate and last_rate:
            change_percent = ((current_rate - last_rate) / last_rate) * 100
            
            # 人民币升值（USD/CNY 下降）且幅度 >= 4%
            if change_percent <= -4.0:
                return True
        
        return False
    
    def get_strategy_message(self) -> str:
        """
        获取当前策略建议
        
        Returns:
            策略建议文本
        """
        if self.should_exchange_usd():
            return """
<div style="background-color: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50;">
    <h3>🎯 全局策略建议</h3>
    <p><strong>人民币升值，现在是换汇好时机！</strong></p>
    <h4>💳 针对你的两张卡：</h4>
    
    <h5>1️⃣ 工商 Visa 卡（主力）</h5>
    <ul>
        <li>去工商银行柜台</li>
        <li>购汇：¥5000 → $700（根据实际汇率）</li>
        <li>存入 Visa 信用卡</li>
        <li>用途：等黑五买礼品卡</li>
    </ul>
    
    <h5>2️⃣ 中行 Master 卡（保活）</h5>
    <ul>
        <li>去中国银行柜台</li>
        <li>购汇：¥700 → $100（根据实际汇率）</li>
        <li>存入 Master 借记卡美元账户</li>
        <li>用途：给 Cloudflare 付款，防止卡冻结</li>
    </ul>
    
    <p><strong>⚠️ 重要提示：</strong></p>
    <ul>
        <li>两张卡都<strong>不能自动换汇</strong>，需要手动购汇</li>
        <li>Master 卡是双标卡（银联+Mastercard），国际支付走银联通道</li>
        <li>Master 卡半年不用会冻结，建议每月给 CF 付款</li>
    </ul>
    
    <p><strong>💰 收益计算：</strong></p>
    <ul>
        <li>汇率优惠：4%（人民币升值）</li>
        <li>礼品卡折扣：5-10%（黑五）</li>
        <li>综合收益：9-14%</li>
    </ul>
    
    <p><strong>📅 下一步：</strong></p>
    <ol>
        <li>立即去银行购汇（两张卡）</li>
        <li>等待黑五/Prime Day（系统自动监控）</li>
        <li>收到礼品卡折扣通知 → 用 Visa 卡购买</li>
        <li>每月用 Master 卡给 CF 付款（保活）</li>
    </ol>
</div>
            """
        elif self.should_increase_jd_frequency():
            return """
<div style="background-color: #fff3e0; padding: 15px; border-left: 4px solid #ff9800;">
    <h3>🎯 全局策略建议</h3>
    <p><strong>人民币贬值，建议关注国内电商！</strong></p>
    <ul>
        <li>京东自营巡检频率已提升</li>
        <li>暂缓海淘，等待汇率回落</li>
        <li>暂缓换美元（等汇率降低）</li>
        <li>关注京东百亿补贴活动</li>
    </ul>
    <p><em>💡 提示：如果卡里有美元余额，可以等黑五再用</em></p>
</div>
            """
        else:
            return """
<div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196f3;">
    <h3>🎯 全局策略建议</h3>
    <p><strong>汇率稳定，正常监控中</strong></p>
    <p>系统将持续追踪汇率变化，为您推荐最佳换汇和购物时机。</p>
    <p><em>💡 提示：记得每月用 Master 卡给 CF 付款，防止冻结</em></p>
</div>
            """
