# AWS 快速部署指南 🚀

## ⚡ 5分钟快速部署

### 前提条件
- ✅ 有 AWS 账号
- ✅ 创建了 EC2 密钥对（.pem 文件）
- ✅ 在本地 Mac 上完成了基本测试

---

## 📋 步骤一：创建 EC2 实例

### 1. 登录 AWS Console

访问：https://console.aws.amazon.com/ec2/

### 2. 启动实例

点击 **"启动实例"**，配置如下：

| 选项 | 推荐配置 |
|------|---------|
| **名称** | `arcteryx-monitor` |
| **AMI** | Amazon Linux 2023 或 Ubuntu 22.04 |
| **实例类型** | `t3.micro` (免费套餐) 或 `t3.small` |
| **密钥对** | 选择或创建新密钥对 |
| **存储** | 20 GB gp3 |
| **安全组** | 允许 SSH (端口 22) 从您的 IP |

### 3. 启动并等待运行

记下实例的 **公有 IP 地址**，例如：`54.123.45.67`

---

## 📋 步骤二：一键部署

### 方式 A：使用自动部署脚本（推荐）

在本地 Mac 终端运行：

```bash
cd /Users/at/Desktop/ARC

# 运行部署脚本
./deploy_to_aws.sh 54.123.45.67 ~/Downloads/your-key.pem

# 如果是 Ubuntu 系统
./deploy_to_aws.sh 54.123.45.67 ~/Downloads/your-key.pem ubuntu
```

**就这么简单！** 脚本会自动：
1. ✅ 测试 SSH 连接
2. ✅ 上传所有文件
3. ✅ 安装 Chrome 和依赖
4. ✅ 配置 Python 环境
5. ✅ 设置 Cron 定时任务
6. ✅ 运行测试

---

### 方式 B：手动部署

如果自动脚本失败，可以手动部署：

#### 1. SSH 连接到 EC2

```bash
ssh -i ~/Downloads/your-key.pem ec2-user@54.123.45.67
# 或 Ubuntu
ssh -i ~/Downloads/your-key.pem ubuntu@54.123.45.67
```

#### 2. 安装依赖

```bash
# Amazon Linux
sudo yum update -y
sudo yum install -y python3 python3-pip wget

# 安装 Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
rm google-chrome-stable_current_x86_64.rpm

# 安装依赖库
sudo yum install -y libX11 libXcomposite libXcursor libXdamage \
  libXext libXi libXtst cups-libs libXScrnSaver libXrandr \
  alsa-lib pango atk at-spi2-atk gtk3
```

#### 3. 上传代码

在**本地 Mac**运行：

```bash
cd /Users/at/Desktop/ARC
scp -i ~/Downloads/your-key.pem -r ./* ec2-user@54.123.45.67:~/arcteryx-monitor/
```

#### 4. 配置环境

回到 **EC2 SSH 会话**：

```bash
cd ~/arcteryx-monitor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh monitor_selenium.py
```

#### 5. 测试运行

```bash
./run.sh
```

#### 6. 设置 Cron

```bash
crontab -e

# 添加以下行（每30分钟运行）
*/30 * * * * cd $HOME/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1

# 保存并退出
```

---

## 📋 步骤三：配置通知（可选）

### 邮件通知

```bash
cd ~/arcteryx-monitor
nano .env
```

填入配置：

```bash
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECEIVER_EMAIL=your-email@gmail.com
```

**获取 Gmail App Password:**
1. 访问 https://myaccount.google.com/security
2. 启用两步验证
3. 搜索"应用专用密码"并创建

### 修改 run.sh 添加通知

```bash
nano run.sh
```

在最后添加：

```bash
# 发送邮件通知
python3 send_notification.py --email
```

---

## 📊 监控和管理

### 查看实时日志

```bash
ssh -i your-key.pem ec2-user@54.123.45.67
tail -f ~/arcteryx-monitor/logs/monitor.log
```

### 查看最新报告

```bash
ls -lt ~/arcteryx-monitor/data/report_*.txt | head -1 | xargs cat
```

### 查看 Cron 状态

```bash
# 查看已设置的任务
crontab -l

# 查看 Cron 日志
sudo tail -f /var/log/cron
```

### 手动运行测试

```bash
cd ~/arcteryx-monitor
./run.sh
```

### 停止监控

```bash
# 编辑 crontab
crontab -e

# 删除或注释掉监控任务
# */30 * * * * ...

# 或者完全清除
crontab -r
```

---

## 💰 成本估算

| 项目 | 配置 | 月成本 |
|------|------|--------|
| EC2 实例 | t3.micro（免费套餐） | **$0** (首年) |
| EC2 实例 | t3.micro（付费） | ~$7.50 |
| EC2 实例 | t3.small | ~$15 |
| 存储 | 20GB SSD | ~$2 |
| 数据传输 | 少量 | ~$0 |
| **总计** | | **$0-17/月** |

💡 **省钱提示**：使用 AWS 免费套餐，首年完全免费！

---

## 🔧 常见问题

### Chrome 无法启动

```bash
# 安装缺失依赖
sudo yum install -y libX11 libXcomposite libXcursor libXdamage \
  libXext libXi libXtst cups-libs libXScrnSaver libXrandr \
  alsa-lib pango atk at-spi2-atk gtk3
```

### Cron 没有运行

```bash
# 检查 Cron 服务
sudo systemctl status crond

# 启动 Cron
sudo systemctl start crond
```

### 连接超时

```bash
# 检查安全组
# AWS Console > EC2 > 安全组 > 入站规则
# 确保允许您的 IP 访问端口 22
```

### 磁盘空间不足

```bash
# 清理旧报告
find ~/arcteryx-monitor/data/report_*.txt -mtime +30 -delete

# 检查磁盘使用
df -h
```

---

## 📱 通知示例

### Slack 通知

```bash
python3 send_notification.py \
  --webhook "https://hooks.slack.com/services/YOUR/WEBHOOK" \
  --webhook-type slack
```

### Discord 通知

```bash
python3 send_notification.py \
  --webhook "https://discord.com/api/webhooks/YOUR/WEBHOOK" \
  --webhook-type discord
```

### 邮件通知

```bash
export SENDER_EMAIL="your@gmail.com"
export SENDER_PASSWORD="your-app-password"
python3 send_notification.py --email
```

---

## 🎉 完成！

现在您的 Arc'teryx 监控系统已经在 AWS 上运行了！

- ✅ 每30分钟自动检查
- ✅ 发现新商品立即通知
- ✅ 24/7 不间断运行
- ✅ 所有数据保存在云端

---

## 📞 需要帮助？

- 查看完整文档：`cat AWS_DEPLOYMENT.md`
- 查看日志：`tail -f logs/monitor.log`
- 测试通知：`python3 send_notification.py --help`

**开始享受自动化监控吧！** 🏔️✨

