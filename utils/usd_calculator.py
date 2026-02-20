#!/usr/bin/env python3
"""
美元囤积计算器
根据汇率和月度支出，动态计算应该囤多少美元
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple


class USDCalculator:
    """
    美元囤积计算器
    
    根据以下因素动态计算：
    1. 当前汇率相对位置（历史均值对比）
    2. 你的月度固定支出
    3. 距离黑五的时间（需要预留礼品卡预算）
    """
    
    # 历史数据（2023-2026年初）
    HISTORICAL_AVERAGE = 7.18  # 近两年均值（中国银行现汇买入价）
    HISTORICAL_HIGH = 7.35     # 近两年最高点
    HISTORICAL_LOW = 6.90      # 近两年最低点
    
    def __init__(self, monthly_cost_usd: float):
        """
        初始化计算器
        
        Args:
            monthly_cost_usd: 你的月度美元支出（如 Mullvad + Cloudflare）
        """
        self.monthly_cost = monthly_cost_usd
    
    def calculate(self, current_rate: float, 
                 enable_blackfriday_buffer: bool = True) -> Dict[str, any]:
        """
        计算建议囤积的美元数量
        
        Args:
            current_rate: 当前汇率（USD/CNY，如 6.92）
            enable_blackfriday_buffer: 是否启用黑五预留
            
        Returns:
            {
                'recommended_usd': 150.0,     # 建议囤积美元数
                'cny_cost': 1038.0,           # 人民币成本
                'base_months': 3,             # 基础囤积月数
                'rate_bonus_months': 2,       # 汇率加成月数
                'blackfriday_bonus': 50,      # 黑五加成美元
                'coverage_months': 6.7,       # 实际能用几个月
                'rate_position': 'excellent', # 汇率位置评级
                'explanation': '...',         # 人类可读的说明
            }
        """
        result = {}
        
        # ① 基础月数（根据月支出决定）
        base_months = self._get_base_months()
        result['base_months'] = base_months
        
        # ② 汇率加成月数
        rate_bonus_months, rate_position = self._get_rate_bonus(current_rate)
        result['rate_bonus_months'] = rate_bonus_months
        result['rate_position'] = rate_position
        
        # ③ 黑五加成
        blackfriday_bonus = 0
        if enable_blackfriday_buffer:
            blackfriday_bonus = self._get_blackfriday_bonus()
        result['blackfriday_bonus'] = blackfriday_bonus
        
        # ④ 计算总囤积金额
        base_usd = self.monthly_cost * (base_months + rate_bonus_months)
        total_usd = base_usd + blackfriday_bonus
        
        # 向上取整到 10 的倍数（方便购汇）
        recommended_usd = round(total_usd / 10) * 10
        
        result['recommended_usd'] = recommended_usd
        result['cny_cost'] = round(recommended_usd * current_rate, 2)
        result['coverage_months'] = round((recommended_usd - blackfriday_bonus) / self.monthly_cost, 1)
        
        # ⑤ 生成人类可读说明
        result['explanation'] = self._generate_explanation(
            current_rate, base_months, rate_bonus_months, 
            blackfriday_bonus, recommended_usd, result['cny_cost']
        )
        
        return result
    
    def _get_base_months(self) -> float:
        """
        计算基础囤积月数
        
        月支出越低，囤的月数越多（因为总额不高，多囤也不贵）
        月支出越高，囤的月数越少（避免一次性投入太多）
        """
        if self.monthly_cost <= 15:
            return 3  # 低支出：囤3个月
        elif self.monthly_cost <= 30:
            return 2  # 中支出：囤2个月
        else:
            return 1.5  # 高支出：囤1.5个月
    
    def _get_rate_bonus(self, current_rate: float) -> Tuple[float, str]:
        """
        根据汇率位置计算加成月数
        
        汇率越便宜（人民币越强），加成越多
        
        Returns:
            (加成月数, 汇率位置评级)
        """
        # 计算汇率偏离度
        deviation = (current_rate - self.HISTORICAL_AVERAGE) / self.HISTORICAL_AVERAGE
        
        if deviation <= -0.04:  # 低于均值 4%+（如 6.89 以下）
            return (3, 'excellent')  # 史低级别，狠狠囤
        elif deviation <= -0.03:  # 低于均值 3%-4%（6.89-6.96）
            return (2, 'very_good')
        elif deviation <= -0.02:  # 低于均值 2%-3%（6.96-7.04）
            return (1, 'good')
        elif deviation <= -0.01:  # 低于均值 1%-2%（7.04-7.11）
            return (0.5, 'fair')
        else:  # 汇率正常或偏高
            return (0, 'normal')
    
    def _get_blackfriday_bonus(self) -> float:
        """
        计算黑五预留金额
        
        距离黑五越近，预留越多
        """
        today = datetime.now().date()
        
        # 计算今年黑五日期（11月第四个周五）
        year = today.year
        nov_1 = datetime(year, 11, 1).date()
        days_until_friday = (4 - nov_1.weekday()) % 7
        first_friday = nov_1 + timedelta(days=days_until_friday)
        black_friday = first_friday + timedelta(weeks=3)
        
        # 如果今年黑五已过，算明年的
        if today > black_friday:
            year += 1
            nov_1 = datetime(year, 11, 1).date()
            days_until_friday = (4 - nov_1.weekday()) % 7
            first_friday = nov_1 + timedelta(days=days_until_friday)
            black_friday = first_friday + timedelta(weeks=3)
        
        days_until = (black_friday - today).days
        
        # 黑五前3个月开始预留
        if days_until <= 90:  # 3个月内
            return 50  # 预留 $50 礼品卡
        elif days_until <= 180:  # 6个月内
            return 30  # 预留 $30
        else:
            return 0
    
    def _generate_explanation(self, current_rate: float, base_months: float,
                             rate_bonus: float, bf_bonus: float,
                             total_usd: float, cny_cost: float) -> str:
        """生成人类可读的说明"""
        lines = []
        
        # 汇率评价
        deviation_pct = ((current_rate - self.HISTORICAL_AVERAGE) / self.HISTORICAL_AVERAGE) * 100
        
        if deviation_pct <= -4:
            rate_comment = f"当前汇率 {current_rate:.4f} 是近两年低点，比均值低 {abs(deviation_pct):.1f}%，**强烈建议多囤**！"
        elif deviation_pct <= -2:
            rate_comment = f"当前汇率 {current_rate:.4f} 处于低位，比均值低 {abs(deviation_pct):.1f}%，适合购汇。"
        elif deviation_pct <= 0:
            rate_comment = f"当前汇率 {current_rate:.4f} 略低于均值 {abs(deviation_pct):.1f}%，可以购汇。"
        else:
            rate_comment = f"当前汇率 {current_rate:.4f} 高于均值 {deviation_pct:.1f}%，建议只囤基础月数，等汇率回落再追加。"
        
        lines.append(rate_comment)
        lines.append("")
        
        # 计算明细
        lines.append("💰 计算明细：")
        lines.append(f"  月度支出: ${self.monthly_cost:.2f}")
        lines.append(f"  基础囤积: {base_months} 个月 = ${self.monthly_cost * base_months:.2f}")
        
        if rate_bonus > 0:
            lines.append(f"  汇率加成: {rate_bonus} 个月 = ${self.monthly_cost * rate_bonus:.2f}")
        
        if bf_bonus > 0:
            lines.append(f"  黑五预留: ${bf_bonus:.2f}")
        
        lines.append(f"  ─────────────────")
        lines.append(f"  **建议囤积: ${total_usd:.2f}**")
        lines.append(f"  **人民币成本: ¥{cny_cost:.2f}**")
        lines.append("")
        
        # 实际能用时长
        actual_months = (total_usd - bf_bonus) / self.monthly_cost
        lines.append(f"📅 能用时长: {actual_months:.1f} 个月（不含黑五预留）")
        
        return "\n".join(lines)
    
    def print_recommendation(self, current_rate: float):
        """打印推荐结果（美化输出）"""
        result = self.calculate(current_rate)
        
        print("=" * 60)
        print("💵 美元囤积建议")
        print("=" * 60)
        print(result['explanation'])
        print("=" * 60)


def main():
    """示例用法"""
    # 你的情况：Mullvad × 2 = $12/月
    calculator = USDCalculator(monthly_cost_usd=12)
    
    # 当前汇率 6.92
    calculator.print_recommendation(current_rate=6.92)
    
    print("\n")
    
    # 对比：如果汇率跌到 6.80（史低）
    print("【如果汇率跌到 6.80】")
    calculator.print_recommendation(current_rate=6.80)


if __name__ == '__main__':
    main()
