#!/usr/bin/env python3
import os
import sys
import yaml
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from monitors.fx_monitor_cn import FXMonitorCN
from utils.notifier import BrevoNotifier


def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_monitor(force=False, test_email=False):
    print(f"🌍 汇率监控启动 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = load_config()

    notifier = BrevoNotifier(
        api_key=os.getenv('BREVO_API_KEY'),
        sender_email=os.getenv('SENDER_EMAIL'),
        sender_name=os.getenv('SENDER_NAME')
    )

    if test_email:
        success = notifier.send_test_email()
        print("✅ 测试邮件发送成功" if success else "❌ 测试邮件失败")
        return

    fx_config = config.get('fx_monitor_cn', {})
    fx_monitor = FXMonitorCN(fx_config)
    notifications = fx_monitor.check()

    if not notifications:
        notifications = [{
            'title': '✅ 汇率监控测试',
            'message': '<p>系统运行正常，汇率未达到提醒门槛。</p>',
            'url': 'https://www.boc.cn/sourcedb/whpj/',
            'price_info': '测试邮件',
            'level': 1
        }]

    notifier.send_notification(notifications)
    print("✅ 邮件发送完成")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--test-email', action='store_true')
    args = parser.parse_args()
    run_monitor(force=args.force, test_email=args.test_email)


if __name__ == '__main__':
    main()