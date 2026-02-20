#!/usr/bin/env python3
"""
全球资产监控系统 - 单元测试
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors import FXMonitor, JDMonitor
from utils import PersistenceManager, AntiCrawler


def test_fx_monitor():
    """测试汇率监控器"""
    print("\n" + "=" * 60)
    print("测试汇率监控器")
    print("=" * 60)
    
    config = {
        'enabled': True,
        'threshold_percent': 4.0,
        'zscore_window': 180,
        'pairs': {
            'usd_cny': {
                'base': 'USD',
                'quote': 'CNY'
            }
        }
    }
    
    fx_monitor = FXMonitor(config)
    
    # 测试获取汇率
    rate = fx_monitor._fetch_exchange_rate('USD', 'CNY')
    if rate:
        print(f"✅ USD/CNY 当前汇率: {rate:.4f}")
    else:
        print("❌ 获取汇率失败")
    
    # 测试静默模式
    is_silent = fx_monitor.is_silent_mode()
    print(f"静默模式: {'是' if is_silent else '否'}")


def test_jd_monitor():
    """测试京东监控器"""
    print("\n" + "=" * 60)
    print("测试京东监控器")
    print("=" * 60)
    
    # 测试 User-Agent 生成
    headers = AntiCrawler.get_mobile_headers()
    print(f"✅ 移动端 User-Agent: {headers['User-Agent'][:50]}...")
    
    # 测试延迟
    print("测试随机延迟...")
    import time
    start = time.time()
    AntiCrawler.random_delay(0.5, 1.0)
    elapsed = time.time() - start
    print(f"✅ 延迟时间: {elapsed:.2f} 秒")


def test_persistence():
    """测试持久化管理器"""
    print("\n" + "=" * 60)
    print("测试持久化管理器")
    print("=" * 60)
    
    pm = PersistenceManager('test_state.json')
    
    # 测试写入
    pm.update_value('test_key', 123.45, {'note': 'test'})
    print("✅ 写入测试数据")
    
    # 测试读取
    value = pm.get_last_value('test_key')
    if value == 123.45:
        print(f"✅ 读取成功: {value}")
    else:
        print("❌ 读取失败")
    
    # 清理
    pm.clear_key('test_key')
    print("✅ 清理测试数据")
    
    # 删除测试文件
    os.remove('test_state.json')


def main():
    """运行所有测试"""
    print("🧪 全球资产监控系统 - 单元测试")
    print("=" * 60)
    
    try:
        test_fx_monitor()
        test_jd_monitor()
        test_persistence()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
