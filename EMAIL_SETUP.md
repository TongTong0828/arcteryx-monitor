# 📧 邮件通知配置指南

## 🎯 快速开始

### 步骤 1：选择邮箱服务

推荐使用 **Gmail**（配置最简单）或 **QQ 邮箱**（国内访问快）

---

## 📮 Gmail 配置

### 1. 开启两步验证
1. 访问 https://myaccount.google.com/security
2. 找到"两步验证"并开启

### 2. 生成应用专用密码
1. 访问 https://myaccount.google.com/apppasswords
2. 选择"邮件"和"其他（自定义名称）"
3. 输入名称：`Arc'teryx Monitor`
4. 点击"生成"
5. **复制生成的 16 位密码**（去掉空格）

### 3. 配置文件
```bash
# 在 EC2 上创建配置文件
cd /home/ec2-user/arcteryx-monitor
cat > email_config.sh << 'EOF'
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="生成的16位密码"
export RECEIVER_EMAIL="your-email@gmail.com"
EOF

# 保护配置文件
chmod 600 email_config.sh
```

---

## 📮 QQ 邮箱配置

### 1. 开启 SMTP 服务
1. 登录 QQ 邮箱
2. 点击"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 点击"生成授权码"
6. **复制授权码**（16位字符）

### 2. 配置文件
```bash
cd /home/ec2-user/arcteryx-monitor
cat > email_config.sh << 'EOF'
export SMTP_SERVER="smtp.qq.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-qq@qq.com"
export SENDER_PASSWORD="QQ邮箱授权码"
export RECEIVER_EMAIL="your-qq@qq.com"
EOF

chmod 600 email_config.sh
```

---

## 📮 163 邮箱配置

### 1. 开启 SMTP 服务
1. 登录 163 邮箱
2. 点击"设置" → "POP3/SMTP/IMAP"
3. 开启"IMAP/SMTP服务"
4. 设置授权密码
5. **复制授权密码**

### 2. 配置文件
```bash
cd /home/ec2-user/arcteryx-monitor
cat > email_config.sh << 'EOF'
export SMTP_SERVER="smtp.163.com"
export SMTP_PORT="587"
export SENDER_EMAIL="your-email@163.com"
export SENDER_PASSWORD="163邮箱授权密码"
export RECEIVER_EMAIL="your-email@163.com"
EOF

chmod 600 email_config.sh
```

---

## 🧪 测试邮件发送

### 1. 上传文件到 EC2
```bash
# 在本地 Mac 上
cd /Users/at/Desktop/ARC
scp -i /path/to/your-key.pem email_notifier.py ec2-user@YOUR_EC2_IP:~/arcteryx-monitor/
```

### 2. 在 EC2 上测试
```bash
ssh -i /path/to/your-key.pem ec2-user@YOUR_EC2_IP

cd arcteryx-monitor
source email_config.sh  # 加载配置
source venv/bin/activate  # 激活虚拟环境

# 测试邮件发送
python3 -c "from email_notifier import send_change_notification; send_change_notification({'added': [{'name': '测试商品', 'price': 'CA\$100', 'link': 'https://test.com'}], 'price_changes': [], 'removed': []})"
```

### 3. 检查邮箱
- 查看是否收到标题为 "Arc'teryx Outlet: 🆕 1个新品" 的邮件
- 如果没收到，检查垃圾邮件文件夹

---

## 🔄 更新运行脚本

修改 `run_monitor.sh` 加载配置：

```bash
cd arcteryx-monitor
cat > run_monitor.sh << 'EOF'
#!/bin/bash
# Arc'teryx Outlet 自动监控脚本

cd /home/ec2-user/arcteryx-monitor

# 加载邮件配置（如果存在）
if [ -f email_config.sh ]; then
    source email_config.sh
fi

# 激活虚拟环境
source venv/bin/activate

# 运行监控
python3 monitor.py >> logs/monitor_$(date +%Y%m%d).log 2>&1
EOF

chmod +x run_monitor.sh
```

---

## ✅ 完成！

现在监控系统会：
1. 每 30 分钟自动检查一次
2. 发现新品、降价、下架时自动发邮件
3. 邮件包含：
   - 📸 精美的 HTML 格式
   - 🆕 新品列表（带价格和链接）
   - 💰 降价商品（对比旧价）
   - 📦 下架商品提醒

---

## ❓ 常见问题

### Q1: 收不到邮件？
1. 检查配置文件是否正确
2. 检查垃圾邮件文件夹
3. 确认授权码/应用密码是否正确
4. 查看日志：`tail -100 ~/arcteryx-monitor/logs/monitor_*.log`

### Q2: 邮件太多？
可以修改 `email_notifier.py` 中的逻辑，只在特定条件下发送：
- 只发送新品通知
- 只在折扣超过 30% 时发送
- 每天汇总一次

### Q3: 想要接收多个邮箱？
修改 `RECEIVER_EMAIL`：
```bash
export RECEIVER_EMAIL="email1@gmail.com,email2@qq.com"
```

---

## 📱 下一步建议

1. **添加微信通知**：使用 Server 酱
2. **添加 Telegram 机器人**：更即时
3. **价格阈值过滤**：只通知大折扣
4. **特定商品监控**：只关注某些款式

