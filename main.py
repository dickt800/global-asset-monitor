#!/usr/bin/env python3
"""
全球资产监控系统 - 主程序
支持定时任务和手动触发
"""
import os
import sys
import yaml
import argparse
from typing import Dict, Any, List
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.fx_monitor_cn import FXMonitorCN
from monitors.fx_monitor_cn import FXMonitorCN
from utils import BrevoNotifier, GlobalStrategy


def load_config(config_path: str = 'config.yaml') -> Dict[str, Any]:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        sys.exit(1)


def run_monitor(force: bool = False, test_email: bool = False):
    """
    运行监控系统
    
    Args:
        force: 是否强制运行（忽略静默模式）
        test_email: 是否发送测试邮件
    """
    print("=" * 60)
    print("🌍 全球资产监控系统启动")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 初始化通知器
    notifier = BrevoNotifier(
        api_key=os.getenv('BREVO_API_KEY'),
        recipient_email=os.getenv('RECIPIENT_EMAIL')
    )
    
    # 测试邮件模式
    if test_email:
        print("\n📧 发送测试邮件...")
        success = notifier.send_test_email()
        print("✅ 测试完成" if success else "❌ 测试失败")
        return
    
    # 收集所有通知
    all_notifications = []
    
    # 1. 汇率监控（优先使用中国版）
    print("\n" + "=" * 60)
    print("💱 汇率监控")
    print("=" * 60)
    
    # 尝试使用中国版监控器（适合中国大陆用户）
    fx_config_cn = config.get('fx_monitor_cn', {})
    if fx_config_cn.get('enabled', False):
        print("📍 使用中国版监控器（监控银行挂牌价）")
        fx_monitor = FXMonitorCN(fx_config_cn)
        fx_notifications = fx_monitor.check()
        
        if fx_notifications:
            all_notifications.extend(fx_notifications)
            print(f"✅ 检测到 {len(fx_notifications)} 条汇率预警")
        else:
            print("✅ 汇率正常，无需提醒")
        
        # 检查是否处于静默模式
        is_silent = fx_monitor.is_silent_mode()
        
        if is_silent and not force:
            print("\n⚠️  静默模式：汇率变化未达到4%门槛，跳过商品监控")
            print("   (如需强制运行，请使用 --force 参数)")
            
            # 只发送汇率通知
            if all_notifications:
                notifier.send_notification(all_notifications)
            return
        
        # 全局策略建议
        if config.get('global_strategy', {}).get('enabled', False):
            strategy = GlobalStrategy(fx_monitor)
            strategy_msg = strategy.get_strategy_message()
            print(f"\n🎯 全局策略: {strategy_msg[:100]}...")
    
    # 备用：使用国际版监控器（仅供参考）
    elif config.get('fx_monitor', {}).get('enabled', False):
        print("📍 使用国际版监控器（国际市场汇率，仅供参考）")
        print("⚠️  提示：如果你在中国大陆换汇，建议使用 fx_monitor_cn")
        
        fx_config = config.get('fx_monitor', {})
        fx_monitor = FXMonitor(fx_config)
        fx_notifications = fx_monitor.check()
        
        if fx_notifications:
            all_notifications.extend(fx_notifications)
            print(f"✅ 检测到 {len(fx_notifications)} 条汇率预警")
        else:
            print("✅ 汇率正常，无需提醒")
        
        # 检查是否处于静默模式
        is_silent = fx_monitor.is_silent_mode()
        
        if is_silent and not force:
            print("\n⚠️  静默模式：汇率变化未达到4%门槛，跳过商品监控")
            print("   (如需强制运行，请使用 --force 参数)")
            
            # 只发送汇率通知
            if all_notifications:
                notifier.send_notification(all_notifications)
            return
        
        # 全局策略建议
        if config.get('global_strategy', {}).get('enabled', False):
            strategy = GlobalStrategy(fx_monitor)
            strategy_msg = strategy.get_strategy_message()
            print(f"\n🎯 全局策略: {strategy_msg[:100]}...")
    else:
        print("⚠️  汇率监控已禁用")
    
    # 2. 京东监控
    print("\n" + "=" * 60)
    print("🛒 京东自营监控")
    print("=" * 60)
    
    jd_config = config.get('jd_monitor', {})
    if jd_config.get('enabled', False):
        jd_monitor = JDMonitor(jd_config)
        jd_notifications = jd_monitor.check()
        
        if jd_notifications:
            all_notifications.extend(jd_notifications)
            print(f"✅ 检测到 {len(jd_notifications)} 条商品提醒")
        else:
            print("✅ 京东商品暂无变化")
    else:
        print("⚠️  京东监控已禁用")
    
    # 3. Amazon 监控
    print("\n" + "=" * 60)
    print("🛍️  Amazon 监控")
    print("=" * 60)
    
    amazon_config = config.get('amazon_monitor', {})
    if amazon_config.get('enabled', False):
        amazon_monitor = AmazonMonitor(amazon_config)
        amazon_notifications = amazon_monitor.check()
        
        if amazon_notifications:
            all_notifications.extend(amazon_notifications)
            print(f"✅ 检测到 {len(amazon_notifications)} 条商品提醒")
        else:
            print("✅ Amazon 商品暂无变化")
    else:
        print("⚠️  Amazon 监控已禁用")
    
    # 4. 机票监控
    print("\n" + "=" * 60)
    print("✈️  机票监控")
    print("=" * 60)
    
    flight_config = config.get('flight_monitor', {})
    if flight_config.get('enabled', False):
        flight_monitor = FlightMonitor(flight_config)
        flight_notifications = flight_monitor.check()
        
        if flight_notifications:
            all_notifications.extend(flight_notifications)
            print(f"✅ 检测到 {len(flight_notifications)} 条机票提醒")
        else:
            print("✅ 机票价格暂无变化")
    else:
        print("⚠️  机票监控已禁用（功能暂未实现）")
    
    # 发送通知
    print("\n" + "=" * 60)
    print("📧 发送通知")
    print("=" * 60)
    
    if all_notifications:
        print(f"📬 共有 {len(all_notifications)} 条通知待发送")
        success = notifier.send_notification(all_notifications)
        if success:
            print("✅ 通知发送成功")
        else:
            print("⚠️  通知发送失败（请检查邮件配置）")
    else:
        print("✅ 无需发送通知")
    
    print("\n" + "=" * 60)
    print("🎉 监控任务完成")
    print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='全球资产监控系统')
    parser.add_argument('--force', action='store_true', 
                       help='强制运行（忽略静默模式）')
    parser.add_argument('--test-email', action='store_true',
                       help='发送测试邮件')
    
    args = parser.parse_args()
    
    try:
        run_monitor(force=args.force, test_email=args.test_email)
    except KeyboardInterrupt:
        print("\n\n⚠️  监控任务已中断")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
