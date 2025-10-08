#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知发送脚本 - 支持邮件、Webhook等多种方式
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os
import sys
import requests
from datetime import datetime


class NotificationSender:
    def __init__(self, changes_file="data/changes.json"):
        self.changes_file = changes_file
        self.changes = self.load_changes()
    
    def load_changes(self):
        """加载变化数据"""
        if not os.path.exists(self.changes_file):
            print("⚠️  变化文件不存在")
            return None
        
        with open(self.changes_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def has_changes(self):
        """检查是否有变化"""
        if not self.changes:
            return False
        
        return any([
            self.changes.get('new_products', []),
            self.changes.get('price_changes', []),
            self.changes.get('removed_products', [])
        ])
    
    def generate_email_body(self):
        """生成邮件正文"""
        stats = self.changes['statistics']
        
        body = f"""
Arc'teryx Outlet 监控报告
{'=' * 50}

监控时间: {self.changes['timestamp']}

📊 统计信息:
  • 总商品数: {stats['total_products']}
  • 新商品: {stats['new_count']} 🆕
  • 价格变化: {stats['price_changed_count']} 💰
  • 已下架: {stats['removed_count']} 📤

"""
        
        # 新商品
        if self.changes.get('new_products'):
            body += "\n🆕 新增商品:\n" + "=" * 50 + "\n"
            for idx, product in enumerate(self.changes['new_products'][:15], 1):
                body += f"\n{idx}. {product['name']}\n"
                body += f"   价格: {product['price']}\n"
                body += f"   链接: {product['link']}\n"
            
            if len(self.changes['new_products']) > 15:
                body += f"\n... 还有 {len(self.changes['new_products']) - 15} 个新商品\n"
        
        # 价格变化
        if self.changes.get('price_changes'):
            body += "\n\n💰 价格变化:\n" + "=" * 50 + "\n"
            for idx, change in enumerate(self.changes['price_changes'][:10], 1):
                body += f"\n{idx}. {change['name']}\n"
                body += f"   {change['old_price']} → {change['new_price']}\n"
                body += f"   链接: {change['link']}\n"
        
        # 下架商品
        if self.changes.get('removed_products'):
            body += "\n\n📤 已下架商品:\n" + "=" * 50 + "\n"
            for idx, product in enumerate(self.changes['removed_products'][:10], 1):
                body += f"{idx}. {product['name']} ({product['price']})\n"
        
        body += "\n" + "=" * 50 + "\n"
        body += "监控网址: https://outlet.arcteryx.com/ca/zh/c/mens\n"
        
        return body
    
    def send_email(self, sender_email, sender_password, receiver_email):
        """发送邮件通知"""
        if not self.has_changes():
            print("ℹ️  没有变化，跳过邮件通知")
            return False
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = receiver_email
            
            stats = self.changes['statistics']
            subject = f"🏔️ Arc'teryx Outlet 更新 - "
            
            if stats['new_count'] > 0:
                subject += f"{stats['new_count']}个新商品"
            if stats['price_changed_count'] > 0:
                subject += f" | {stats['price_changed_count']}个价格变化"
            
            msg['Subject'] = subject
            
            # 添加正文
            body = self.generate_email_body()
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 发送邮件
            print("正在发送邮件...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✓ 邮件通知发送成功: {receiver_email}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False
    
    def send_webhook(self, webhook_url, webhook_type="slack"):
        """发送 Webhook 通知（Slack/Discord/企业微信）"""
        if not self.has_changes():
            print("ℹ️  没有变化，跳过 Webhook 通知")
            return False
        
        try:
            stats = self.changes['statistics']
            
            if webhook_type == "slack":
                # Slack 格式
                message = {
                    "text": f"🏔️ Arc'teryx Outlet 更新",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": "🏔️ Arc'teryx Outlet 监控报告"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*总商品数:*\n{stats['total_products']}"},
                                {"type": "mrkdwn", "text": f"*新商品:*\n{stats['new_count']} 🆕"},
                                {"type": "mrkdwn", "text": f"*价格变化:*\n{stats['price_changed_count']} 💰"},
                                {"type": "mrkdwn", "text": f"*已下架:*\n{stats['removed_count']} 📤"}
                            ]
                        }
                    ]
                }
                
                # 添加新商品详情
                if self.changes.get('new_products'):
                    products_text = ""
                    for product in self.changes['new_products'][:5]:
                        products_text += f"• <{product['link']}|{product['name']}>\n  {product['price']}\n"
                    
                    message["blocks"].append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*🆕 新增商品:*\n{products_text}"
                        }
                    })
            
            elif webhook_type == "discord":
                # Discord 格式
                message = {
                    "content": "🏔️ Arc'teryx Outlet 更新",
                    "embeds": [{
                        "title": "Arc'teryx Outlet 监控报告",
                        "color": 3066993,
                        "fields": [
                            {"name": "总商品数", "value": str(stats['total_products']), "inline": True},
                            {"name": "新商品 🆕", "value": str(stats['new_count']), "inline": True},
                            {"name": "价格变化 💰", "value": str(stats['price_changed_count']), "inline": True}
                        ],
                        "timestamp": datetime.now().isoformat()
                    }]
                }
            
            elif webhook_type == "wecom":
                # 企业微信格式
                message = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": f"""# 🏔️ Arc'teryx Outlet 更新
                        
> 监控时间: {self.changes['timestamp']}

## 📊 统计信息
- 总商品数: {stats['total_products']}
- 新商品: <font color="info">{stats['new_count']}</font> 🆕
- 价格变化: <font color="warning">{stats['price_changed_count']}</font> 💰
- 已下架: {stats['removed_count']} 📤
                        """
                    }
                }
            
            else:
                # 通用格式
                message = {
                    "text": self.generate_email_body()
                }
            
            # 发送 Webhook
            print(f"正在发送 {webhook_type} Webhook...")
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            print(f"✓ Webhook 通知发送成功")
            return True
            
        except Exception as e:
            print(f"❌ Webhook 发送失败: {e}")
            return False
    
    def send_aws_sns(self, topic_arn, region='us-east-1'):
        """发送 AWS SNS 通知"""
        if not self.has_changes():
            print("ℹ️  没有变化，跳过 SNS 通知")
            return False
        
        try:
            import boto3
            
            sns = boto3.client('sns', region_name=region)
            
            stats = self.changes['statistics']
            subject = f"Arc'teryx Outlet 更新 - {stats['new_count']}个新商品"
            message = self.generate_email_body()
            
            response = sns.publish(
                TopicArn=topic_arn,
                Subject=subject,
                Message=message
            )
            
            print(f"✓ SNS 通知发送成功: {response['MessageId']}")
            return True
            
        except Exception as e:
            print(f"❌ SNS 发送失败: {e}")
            return False


def main():
    """主函数 - 从环境变量读取配置"""
    import argparse
    
    parser = argparse.ArgumentParser(description='发送监控通知')
    parser.add_argument('--email', action='store_true', help='发送邮件通知')
    parser.add_argument('--webhook', type=str, help='Webhook URL')
    parser.add_argument('--webhook-type', type=str, default='slack', 
                       choices=['slack', 'discord', 'wecom', 'generic'],
                       help='Webhook 类型')
    parser.add_argument('--sns', type=str, help='AWS SNS Topic ARN')
    parser.add_argument('--changes-file', type=str, default='data/changes.json',
                       help='变化文件路径')
    
    args = parser.parse_args()
    
    sender = NotificationSender(args.changes_file)
    
    if not sender.changes:
        print("❌ 无法加载变化数据")
        sys.exit(1)
    
    success = False
    
    # 邮件通知
    if args.email:
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        receiver_email = os.getenv('RECEIVER_EMAIL', sender_email)
        
        if not sender_email or not sender_password:
            print("❌ 请设置环境变量: SENDER_EMAIL, SENDER_PASSWORD")
        else:
            success = sender.send_email(sender_email, sender_password, receiver_email) or success
    
    # Webhook 通知
    if args.webhook:
        success = sender.send_webhook(args.webhook, args.webhook_type) or success
    
    # SNS 通知
    if args.sns:
        region = os.getenv('AWS_REGION', 'us-east-1')
        success = sender.send_aws_sns(args.sns, region) or success
    
    # 如果没有指定任何通知方式，显示帮助
    if not any([args.email, args.webhook, args.sns]):
        print("请指定至少一种通知方式:")
        print("  --email              发送邮件")
        print("  --webhook URL        发送 Webhook")
        print("  --sns TOPIC_ARN      发送 SNS")
        print("\n环境变量配置:")
        print("  SENDER_EMAIL         发件人邮箱")
        print("  SENDER_PASSWORD      发件人密码（Gmail App Password）")
        print("  RECEIVER_EMAIL       收件人邮箱")
        print("  AWS_REGION           AWS 区域")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

