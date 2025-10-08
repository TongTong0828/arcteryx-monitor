#!/usr/bin/env python3
"""
Arc'teryx Outlet 邮件通知模块
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:
    """邮件通知类"""
    
    def __init__(self):
        """初始化邮件配置"""
        # 从环境变量读取配置（安全起见）
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = os.getenv('SENDER_EMAIL', '')
        self.sender_password = os.getenv('SENDER_PASSWORD', '')
        self.receiver_email = os.getenv('RECEIVER_EMAIL', '')
        
        # 检查配置
        if not all([self.sender_email, self.sender_password, self.receiver_email]):
            logger.warning("邮件配置不完整，将跳过邮件发送")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_notification(self, subject, changes):
        """发送通知邮件"""
        if not self.enabled:
            logger.info("邮件通知未配置，跳过发送")
            return False
        
        try:
            # 构建邮件内容
            html_content = self._build_html_content(changes)
            
            # 创建邮件
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = self.receiver_email
            
            # 添加 HTML 内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"✓ 邮件通知已发送到 {self.receiver_email}")
            return True
            
        except Exception as e:
            logger.error(f"✗ 发送邮件失败: {e}")
            return False
    
    def _build_html_content(self, changes):
        """构建 HTML 邮件内容"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .timestamp {{
                    color: rgba(255,255,255,0.8);
                    font-size: 14px;
                    margin-top: 10px;
                }}
                .section {{
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 20px;
                    margin-bottom: 20px;
                    border-radius: 5px;
                }}
                .section-title {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 15px;
                    color: #667eea;
                }}
                .product {{
                    background: white;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .product-name {{
                    font-size: 16px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 8px;
                }}
                .product-price {{
                    color: #e74c3c;
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }}
                .product-link {{
                    display: inline-block;
                    padding: 8px 16px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                .product-link:hover {{
                    background: #5568d3;
                }}
                .footer {{
                    text-align: center;
                    color: #7f8c8d;
                    font-size: 12px;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                }}
                .emoji {{
                    font-size: 24px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏔️ Arc'teryx Outlet 监控报告</h1>
                <div class="timestamp">📅 {timestamp}</div>
            </div>
        """
        
        # 新增商品
        if changes.get('added'):
            html += f"""
            <div class="section">
                <div class="section-title">
                    <span class="emoji">🆕</span> 新增商品 ({len(changes['added'])} 个)
                </div>
            """
            for product in changes['added'][:10]:
                name = product.get('name', 'N/A')
                price = product.get('price', 'N/A')
                link = product.get('link', '#')
                
                html += f"""
                <div class="product">
                    <div class="product-name">{name}</div>
                    <div class="product-price">💰 {price}</div>
                    <a href="{link}" class="product-link">查看详情 →</a>
                </div>
                """
            
            if len(changes['added']) > 10:
                html += f"<p style='color: #7f8c8d;'>... 还有 {len(changes['added']) - 10} 个商品</p>"
            
            html += "</div>"
        
        # 价格变化
        if changes.get('price_changes'):
            html += f"""
            <div class="section">
                <div class="section-title">
                    <span class="emoji">💰</span> 价格变化 ({len(changes['price_changes'])} 个)
                </div>
            """
            for change in changes['price_changes'][:10]:
                product = change['product']
                name = product.get('name', 'N/A')
                old_price = change['old_price']
                new_price = change['new_price']
                link = product.get('link', '#')
                
                html += f"""
                <div class="product">
                    <div class="product-name">{name}</div>
                    <div class="product-price">
                        📉 <span style="text-decoration: line-through; color: #95a5a6;">{old_price}</span>
                        → {new_price}
                    </div>
                    <a href="{link}" class="product-link">查看详情 →</a>
                </div>
                """
            
            if len(changes['price_changes']) > 10:
                html += f"<p style='color: #7f8c8d;'>... 还有 {len(changes['price_changes']) - 10} 个商品</p>"
            
            html += "</div>"
        
        # 下架商品
        if changes.get('removed'):
            html += f"""
            <div class="section">
                <div class="section-title">
                    <span class="emoji">📦</span> 下架商品 ({len(changes['removed'])} 个)
                </div>
                <p style='color: #7f8c8d;'>以下商品可能已售罄：</p>
            """
            for product in changes['removed'][:10]:
                name = product.get('name', 'N/A')
                html += f"<div class='product'><div class='product-name'>{name}</div></div>"
            
            if len(changes['removed']) > 10:
                html += f"<p style='color: #7f8c8d;'>... 还有 {len(changes['removed']) - 10} 个商品</p>"
            
            html += "</div>"
        
        # 页脚
        html += """
            <div class="footer">
                <p>这是一封自动生成的邮件，来自 Arc'teryx Outlet 监控系统</p>
                <p>如有问题，请检查 EC2 实例日志</p>
            </div>
        </body>
        </html>
        """
        
        return html


def send_change_notification(changes):
    """便捷函数：发送变化通知"""
    notifier = EmailNotifier()
    
    # 统计变化数量
    added_count = len(changes.get('added', []))
    price_count = len(changes.get('price_changes', []))
    removed_count = len(changes.get('removed', []))
    
    # 构建标题
    parts = []
    if added_count > 0:
        parts.append(f"🆕 {added_count}个新品")
    if price_count > 0:
        parts.append(f"💰 {price_count}个降价")
    if removed_count > 0:
        parts.append(f"📦 {removed_count}个下架")
    
    if not parts:
        logger.info("无变化，跳过邮件通知")
        return False
    
    subject = f"Arc'teryx Outlet: {', '.join(parts)}"
    
    return notifier.send_notification(subject, changes)


if __name__ == "__main__":
    # 测试邮件发送
    test_changes = {
        'added': [
            {
                'name': 'Rush夹克 男装',
                'price': 'CA$850.00 → CA$637.50',
                'link': 'https://outlet.arcteryx.com/ca/zh/shop/mens/rush-jacket-7149'
            }
        ],
        'price_changes': [],
        'removed': []
    }
    
    send_change_notification(test_changes)

