"""
Brevo 邮件通知模块 - 支持多收件人
"""
import os
import json
import requests
from typing import Dict, Any, List


class BrevoNotifier:
    """
    Brevo (Sendinblue) 邮件通知器
    
    支持：
    1. HTML 邮件
    2. 一键直达按钮
    3. 多级通知（Level 1-3）
    4. 多收件人（从 recipients.json 读取）
    5. 个性化通知（根据每个人的偏好）
    """
    
    def __init__(self, api_key: str = None, sender_email: str = None, 
                 sender_name: str = None):
        """
        Args:
            api_key: Brevo API Key
            sender_email: 发件人邮箱
            sender_name: 发件人名称
        """
        self.api_key = api_key or os.getenv('BREVO_API_KEY')
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL', 'noreply@monitor.com')
        self.sender_name = sender_name or os.getenv('SENDER_NAME', 'Global Asset Monitor')
        
        self.api_url = 'https://api.brevo.com/v3/smtp/email'
        self.recipients = self._load_recipients()
        
    def _load_recipients(self) -> List[Dict[str, Any]]:
        """
        从 recipients.json 加载收件人列表
        
        Returns:
            收件人列表
        """
        try:
            recipients_file = 'recipients.json'
            
            # 如果文件不存在，返回空列表
            if not os.path.exists(recipients_file):
                print(f"⚠️  {recipients_file} 不存在，将只发送给环境变量中的邮箱")
                return []
            
            with open(recipients_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            recipients = data.get('recipients', [])
            
            # 只保留启用的收件人
            enabled_recipients = [r for r in recipients if r.get('enabled', False)]
            
            print(f"✅ 加载了 {len(enabled_recipients)} 个收件人")
            
            return enabled_recipients
            
        except Exception as e:
            print(f"⚠️  加载收件人列表失败: {e}")
            return []
    
    def _filter_recipients_by_notification_type(self, notification_type: str) -> List[Dict[str, Any]]:
        """
        根据通知类型筛选收件人
        
        Args:
            notification_type: 通知类型（fx, jd, amazon, gift_card）
            
        Returns:
            应该接收此类型通知的收件人列表
        """
        if not self.recipients:
            return []
        
        filtered = []
        
        for recipient in self.recipients:
            preferences = recipient.get('preferences', {})
            
            # 检查该收件人是否想接收此类型通知
            notify_key = f'notify_{notification_type}'
            if preferences.get(notify_key, True):  # 默认 True
                filtered.append(recipient)
        
        return filtered
    
    def _detect_notification_type(self, notifications: List[Dict[str, Any]]) -> str:
        """
        检测通知类型
        
        Args:
            notifications: 通知列表
            
        Returns:
            通知类型（fx, jd, amazon, gift_card）
        """
        if not notifications:
            return 'unknown'
        
        # 检查第一个通知的标题
        title = notifications[0].get('title', '').lower()
        
        if 'fx' in title or '汇率' in title or 'usd/cny' in title:
            return 'fx'
        elif 'jd' in title or '京东' in title:
            return 'jd'
        elif 'amazon' in title or 'gift card' in title or '礼品卡' in title:
            if 'gift card' in title or '礼品卡' in title:
                return 'gift_card'
            return 'amazon'
        else:
            return 'unknown'
    
    def send_notification(self, notifications: List[Dict[str, Any]]) -> bool:
        """
        发送通知邮件（支持多收件人）
        
        Args:
            notifications: 通知列表
        
        Returns:
            是否发送成功
        """
        if not self.api_key:
            print("⚠️  邮件配置不完整（缺少 BREVO_API_KEY），跳过发送")
            return False
        
        # 检测通知类型
        notification_type = self._detect_notification_type(notifications)
        
        # 筛选应该接收此类型通知的收件人
        filtered_recipients = self._filter_recipients_by_notification_type(notification_type)
        
        # 如果 recipients.json 没有配置，使用环境变量
        if not filtered_recipients:
            env_email = os.getenv('RECIPIENT_EMAIL')
            if env_email:
                filtered_recipients = [{
                    'name': '用户',
                    'email': env_email,
                    'role': 'owner'
                }]
            else:
                print("⚠️  没有配置收件人，跳过发送")
                return False
        
        print(f"📧 准备发送 {notification_type} 类型通知给 {len(filtered_recipients)} 个收件人")
        
        # 构建 HTML 内容
        html_content = self._build_html(notifications)
        
        # 确定主题
        max_level = max(n.get('level', 1) for n in notifications)
        level_emoji = {1: '📬', 2: '⚠️', 3: '🚨'}
        subject = f"{level_emoji.get(max_level, '📬')} 全球资产监控提醒 - {len(notifications)} 条新消息"
        
        # 发送邮件（每个收件人单独发送，可以个性化）
        success_count = 0
        for recipient in filtered_recipients:
            # 个性化 HTML（添加收件人名字）
            personalized_html = self._personalize_html(html_content, recipient)
            
            # 发送
            if self._send_email(subject, personalized_html, recipient):
                success_count += 1
        
        print(f"✅ 成功发送给 {success_count}/{len(filtered_recipients)} 个收件人")
        
        return success_count > 0
    
    def _personalize_html(self, html: str, recipient: Dict[str, Any]) -> str:
        """
        个性化 HTML 内容
        
        Args:
            html: 原始 HTML
            recipient: 收件人信息
            
        Returns:
            个性化后的 HTML
        """
        name = recipient.get('name', '用户')
        role = recipient.get('role', 'subscriber')
        
        # 在邮件头部添加个性化问候
        greeting = f"""
<div style="background-color: #f5f5f5; padding: 15px; margin-bottom: 20px; border-radius: 5px;">
    <p style="margin: 0; color: #666;">你好，<strong>{name}</strong>！</p>
    {'<p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">系统主人</p>' if role == 'owner' else ''}
</div>
"""
        
        # 在 <body> 后插入问候语
        html = html.replace('<body>', f'<body>{greeting}')
        
        return html
    
    def _build_html(self, notifications: List[Dict[str, Any]]) -> str:
        """
        构建 HTML 邮件内容
        
        Args:
            notifications: 通知列表
            
        Returns:
            HTML 字符串
        """
        # 邮件头部
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }
        .notification {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 20px 0;
            overflow: hidden;
        }
        .notification-header {
            padding: 15px;
            font-weight: bold;
            font-size: 18px;
        }
        .level-1 { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
        .level-2 { background-color: #fff3e0; border-left: 4px solid #ff9800; }
        .level-3 { background-color: #ffebee; border-left: 4px solid #f44336; }
        .notification-body {
            padding: 20px;
            background-color: #fafafa;
        }
        .btn {
            display: inline-block;
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 15px;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌍 全球资产监控系统</h1>
        <p>您有新的价格提醒</p>
    </div>
"""
        
        # 添加每个通知
        for notification in notifications:
            level = notification.get('level', 1)
            html += f"""
    <div class="notification level-{level}">
        <div class="notification-header">
            {notification['title']}
        </div>
        <div class="notification-body">
            {notification['message']}
            <p style="text-align: center;">
                <a href="{notification['url']}" class="btn">🔗 立即查看</a>
            </p>
        </div>
    </div>
"""
        
        # 邮件尾部
        html += """
    <div class="footer">
        <p>本邮件由全球资产监控系统自动发送</p>
        <p>如需调整通知设置，请编辑 recipients.json 文件</p>
    </div>
</body>
</html>
"""
        return html
    
    def _send_email(self, subject: str, html_content: str, recipient: Dict[str, Any]) -> bool:
        """
        发送邮件给单个收件人
        
        Args:
            subject: 邮件主题
            html_content: HTML 内容
            recipient: 收件人信息
            
        Returns:
            是否发送成功
        """
        headers = {
            'accept': 'application/json',
            'api-key': self.api_key,
            'content-type': 'application/json'
        }
        
        payload = {
            'sender': {
                'name': self.sender_name,
                'email': self.sender_email
            },
            'to': [
                {
                    'email': recipient['email'],
                    'name': recipient.get('name', '用户')
                }
            ],
            'subject': subject,
            'htmlContent': html_content
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 201:
                print(f"  ✅ 已发送给: {recipient.get('name', '用户')} ({recipient['email']})")
                return True
            else:
                print(f"  ⚠️  发送失败: {recipient['email']} - {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ⚠️  发送异常: {recipient['email']} - {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        发送测试邮件给所有启用的收件人
        
        Returns:
            是否发送成功
        """
        test_notification = [{
            'title': '🧪 测试通知',
            'message': '<p>这是一封测试邮件，用于验证 Brevo 配置和收件人列表是否正确。</p>',
            'url': 'https://github.com',
            'price_info': 'Test',
            'level': 1
        }]
        
        return self.send_notification(test_notification)
