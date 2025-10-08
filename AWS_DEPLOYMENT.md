# AWS 部署指南

## 🎯 部署方案选择

### 方案一：EC2 实例（推荐 - 最简单）⭐

**优点**：
- 完全兼容现有代码
- 稳定可靠
- 容易调试
- 成本可预测

**成本**：约 $3-10/月（t3.micro 或 t3.small）

---

### 方案二：AWS Lambda + EventBridge

**优点**：
- 按需付费，成本更低
- 无需管理服务器
- 自动扩展

**缺点**：
- 需要无头浏览器支持（需要使用 Chromium Layer）
- Lambda 超时限制（15分钟）
- 配置稍复杂

**成本**：约 $0.50-2/月

---

## 📋 方案一：EC2 部署（推荐）

### 步骤 1：创建 EC2 实例

1. **登录 AWS Console** → EC2
2. **启动实例**：
   - AMI: Amazon Linux 2 或 Ubuntu 22.04
   - 实例类型: `t3.micro`（免费套餐）或 `t3.small`
   - 存储: 20GB SSD
   - 安全组: 允许 SSH (端口 22)

3. **连接到实例**：
   ```bash
   ssh -i your-key.pem ec2-user@your-instance-ip
   # 或 Ubuntu
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

### 步骤 2：安装依赖

```bash
# 更新系统
sudo yum update -y  # Amazon Linux
# 或
sudo apt update && sudo apt upgrade -y  # Ubuntu

# 安装 Python 3
sudo yum install python3 python3-pip -y  # Amazon Linux
# 或
sudo apt install python3 python3-pip python3-venv -y  # Ubuntu

# 安装 Chrome 和 ChromeDriver
# Amazon Linux 2
sudo yum install -y wget unzip
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm

# Ubuntu
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# 安装 Git
sudo yum install git -y  # Amazon Linux
# 或
sudo apt install git -y  # Ubuntu
```

### 步骤 3：部署代码

```bash
# 创建工作目录
mkdir -p ~/arcteryx-monitor
cd ~/arcteryx-monitor

# 上传代码（从本地）
# 在本地机器上运行：
scp -i your-key.pem -r /Users/at/Desktop/ARC/* ec2-user@your-instance-ip:~/arcteryx-monitor/

# 或使用 Git（如果代码在仓库中）
# git clone your-repo-url .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 4：测试运行

```bash
# 测试 Selenium
python3 test_selenium.py

# 运行一次监控
./run.sh
```

### 步骤 5：设置 Cron 自动运行

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每30分钟运行一次）
*/30 * * * * cd /home/ec2-user/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1

# 或每小时运行
0 * * * * cd /home/ec2-user/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1

# 保存退出
```

### 步骤 6：设置通知

#### 选项 A：邮件通知（推荐）

创建 `send_notification.py`:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

def send_email_notification(changes_file):
    """发送邮件通知"""
    
    # 读取变化
    with open(changes_file, 'r', encoding='utf-8') as f:
        changes = json.load(f)
    
    # 如果没有变化，不发送邮件
    if not any([changes['new_products'], changes['price_changes'], changes['removed_products']]):
        return
    
    # 邮件配置
    sender_email = "your-email@gmail.com"
    sender_password = "your-app-password"  # Gmail App Password
    receiver_email = "your-email@gmail.com"
    
    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"🏔️ Arc'teryx Outlet 更新提醒 - {changes['statistics']['new_count']}个新商品"
    
    # 邮件正文
    body = f"""
Arc'teryx Outlet 监控报告

📊 统计信息:
- 总商品数: {changes['statistics']['total_products']}
- 新商品: {changes['statistics']['new_count']}
- 价格变化: {changes['statistics']['price_changed_count']}
- 已下架: {changes['statistics']['removed_count']}

"""
    
    # 添加新商品详情
    if changes['new_products']:
        body += "\n🆕 新增商品:\n"
        for product in changes['new_products'][:10]:
            body += f"• {product['name']}\n"
            body += f"  价格: {product['price']}\n"
            body += f"  链接: {product['link']}\n\n"
    
    # 添加价格变化
    if changes['price_changes']:
        body += "\n💰 价格变化:\n"
        for change in changes['price_changes'][:10]:
            body += f"• {change['name']}\n"
            body += f"  {change['old_price']} → {change['new_price']}\n"
            body += f"  链接: {change['link']}\n\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    # 发送邮件
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✓ 邮件通知发送成功")
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

if __name__ == "__main__":
    send_email_notification("data/changes.json")
```

修改 `run.sh` 添加通知：

```bash
#!/bin/bash
source venv/bin/activate
python3 monitor_selenium.py "$@"

# 发送通知
python3 send_notification.py
```

#### 选项 B：AWS SNS 通知

```bash
# 安装 AWS CLI
pip install boto3

# 配置 AWS 凭证
aws configure
```

#### 选项 C：Webhook 通知（Slack/Discord/企业微信）

创建 `send_webhook.py` 用于发送 Webhook 通知。

### 步骤 7：监控和维护

```bash
# 查看日志
tail -f logs/monitor.log

# 查看最新报告
ls -lt data/report_*.txt | head -1 | xargs cat

# 查看 Cron 是否运行
grep CRON /var/log/syslog  # Ubuntu
# 或
tail -f /var/log/cron  # Amazon Linux

# 检查磁盘空间
df -h

# 清理旧报告（保留最近30天）
find data/report_*.txt -mtime +30 -delete
```

---

## 📋 方案二：Lambda 部署

### 准备工作

由于 Lambda 默认不包含 Chrome，需要使用 Chromium Layer。

### 步骤 1：创建 Lambda Layer

```bash
# 下载 Chromium for Lambda
mkdir -p lambda-layer/python
cd lambda-layer

# 使用预编译的 Chromium for AWS Lambda
# 下载: https://github.com/shelfio/chrome-aws-lambda-layer
```

### 步骤 2：修改代码

创建 `lambda_function.py`:

```python
import json
import boto3
from monitor_selenium import ArcOutletMonitorSelenium

def lambda_handler(event, context):
    """AWS Lambda 处理函数"""
    
    monitor = ArcOutletMonitorSelenium(
        data_dir='/tmp/data',  # Lambda 只有 /tmp 可写
        headless=True
    )
    
    try:
        monitor.run_once()
        
        # 发送 SNS 通知
        # send_sns_notification()
        
        return {
            'statusCode': 200,
            'body': json.dumps('监控完成')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'错误: {str(e)}')
        }
```

### 步骤 3：创建 EventBridge 规则

在 AWS Console 中：
1. 打开 EventBridge
2. 创建规则
3. 设置 Cron 表达式：`cron(0,30 * * * ? *)` (每30分钟)
4. 目标选择您的 Lambda 函数

---

## 💰 成本估算

### EC2 方案
- **t3.micro** (免费套餐): $0/月（12个月免费）
- **t3.micro** (付费): ~$8/月
- **t3.small**: ~$15/月
- 存储 (20GB): ~$2/月
- 数据传输: 基本免费

**总计**: $0-10/月

### Lambda 方案
- Lambda 执行: ~48次/天 × 30秒 × $0.0000166667/GB-秒 = $0.20/月
- EventBridge: 免费
- 存储 (S3): ~$0.10/月

**总计**: ~$0.30-1/月

---

## 🔒 安全最佳实践

1. **使用 IAM 角色**（不要硬编码密钥）
2. **限制安全组规则**（只允许必要的IP）
3. **定期更新系统和依赖**
4. **使用 AWS Secrets Manager** 存储敏感信息
5. **启用 CloudWatch 日志**

---

## 📊 监控和告警

### CloudWatch 告警设置

```bash
# 监控 EC2 CPU 使用率
# 监控磁盘空间
# 监控脚本执行失败
```

---

## 🚀 一键部署脚本

参见 `deploy_to_aws.sh` 脚本。

---

## 📞 故障排查

### 问题：Chrome 无法启动

**解决方案**：
```bash
# 安装缺失的依赖
sudo yum install -y libX11 libXcomposite libXcursor libXdamage \
  libXext libXi libXtst cups-libs libXScrnSaver libXrandr \
  alsa-lib pango atk at-spi2-atk gtk3
```

### 问题：Cron 没有运行

**解决方案**：
```bash
# 检查 Cron 服务
sudo systemctl status crond  # Amazon Linux
sudo systemctl status cron   # Ubuntu

# 查看 Cron 日志
tail -f /var/log/cron
```

### 问题：磁盘空间不足

**解决方案**：
```bash
# 清理旧数据
find data/report_*.txt -mtime +30 -delete
find data/page_source.html -mtime +7 -delete
```

---

## 📚 参考资源

- [AWS EC2 文档](https://docs.aws.amazon.com/ec2/)
- [AWS Lambda 文档](https://docs.aws.amazon.com/lambda/)
- [Chrome on AWS Lambda](https://github.com/shelfio/chrome-aws-lambda-layer)
- [AWS 免费套餐](https://aws.amazon.com/free/)

