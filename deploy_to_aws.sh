#!/bin/bash
# AWS EC2 部署脚本

set -e  # 遇到错误立即退出

echo "============================================"
echo "Arc'teryx Monitor - AWS 部署脚本"
echo "============================================"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "用法: ./deploy_to_aws.sh <EC2_IP_ADDRESS> <KEY_FILE>"
    echo "示例: ./deploy_to_aws.sh 54.123.45.67 ~/mykey.pem"
    exit 1
fi

EC2_IP=$1
KEY_FILE=${2:-~/.ssh/id_rsa}
EC2_USER=${3:-ec2-user}  # 默认 ec2-user，Ubuntu 使用 ubuntu

echo "📋 部署信息:"
echo "  EC2 IP: $EC2_IP"
echo "  密钥文件: $KEY_FILE"
echo "  用户: $EC2_USER"
echo ""

# 检查密钥文件
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 密钥文件不存在: $KEY_FILE"
    exit 1
fi

# 设置密钥权限
chmod 400 "$KEY_FILE"

echo "1️⃣  测试 SSH 连接..."
if ssh -i "$KEY_FILE" -o ConnectTimeout=10 "$EC2_USER@$EC2_IP" "echo '✓ SSH 连接成功'"; then
    echo "✓ SSH 连接正常"
else
    echo "❌ SSH 连接失败，请检查:"
    echo "  - EC2 实例是否运行"
    echo "  - 安全组是否允许 SSH (端口 22)"
    echo "  - 密钥文件是否正确"
    exit 1
fi

echo ""
echo "2️⃣  准备部署文件..."

# 创建临时目录
DEPLOY_DIR=$(mktemp -d)
echo "  临时目录: $DEPLOY_DIR"

# 复制必要文件
cp monitor_selenium.py "$DEPLOY_DIR/"
cp send_notification.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp run.sh "$DEPLOY_DIR/"
cp setup.sh "$DEPLOY_DIR/"
cp README.md "$DEPLOY_DIR/"
cp AWS_DEPLOYMENT.md "$DEPLOY_DIR/"

# 创建 .env.example 文件
cat > "$DEPLOY_DIR/.env.example" << 'EOF'
# 邮件通知配置
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RECEIVER_EMAIL=your-email@gmail.com

# AWS 配置
AWS_REGION=us-east-1
AWS_SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:arcteryx-alerts

# Webhook 配置
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
EOF

echo "✓ 文件准备完成"

echo ""
echo "3️⃣  上传文件到 EC2..."

# 创建远程目录
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" "mkdir -p ~/arcteryx-monitor/logs ~/arcteryx-monitor/data"

# 上传文件
scp -i "$KEY_FILE" -r "$DEPLOY_DIR"/* "$EC2_USER@$EC2_IP:~/arcteryx-monitor/"

echo "✓ 文件上传完成"

echo ""
echo "4️⃣  在 EC2 上安装依赖..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd ~/arcteryx-monitor

# 检测操作系统
if [ -f /etc/redhat-release ]; then
    # Amazon Linux / CentOS / RHEL
    echo "  检测到 Amazon Linux / RHEL"
    
    # 更新系统
    sudo yum update -y
    
    # 安装 Python 3
    sudo yum install -y python3 python3-pip
    
    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        echo "  安装 Google Chrome..."
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
        sudo yum install -y ./google-chrome-stable_current_x86_64.rpm
        rm -f google-chrome-stable_current_x86_64.rpm
    fi
    
    # 安装 Chrome 依赖
    sudo yum install -y libX11 libXcomposite libXcursor libXdamage \
        libXext libXi libXtst cups-libs libXScrnSaver libXrandr \
        alsa-lib pango atk at-spi2-atk gtk3
    
elif [ -f /etc/debian_version ]; then
    # Ubuntu / Debian
    echo "  检测到 Ubuntu / Debian"
    
    # 更新系统
    sudo apt update
    sudo apt upgrade -y
    
    # 安装 Python 3
    sudo apt install -y python3 python3-pip python3-venv
    
    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        echo "  安装 Google Chrome..."
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        sudo apt install -y ./google-chrome-stable_current_amd64.deb
        rm -f google-chrome-stable_current_amd64.deb
    fi
fi

# 创建虚拟环境
echo "  创建 Python 虚拟环境..."
python3 -m venv venv

# 激活虚拟环境并安装依赖
echo "  安装 Python 依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 设置执行权限
chmod +x run.sh
chmod +x monitor_selenium.py
chmod +x send_notification.py

echo "✓ 依赖安装完成"
ENDSSH

echo "✓ EC2 环境配置完成"

echo ""
echo "5️⃣  测试运行..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd ~/arcteryx-monitor
source venv/bin/activate

echo "  运行测试..."
python3 test_selenium.py 2>&1 | head -20

echo ""
echo "  运行首次监控..."
./run.sh
ENDSSH

echo "✓ 测试完成"

echo ""
echo "6️⃣  设置 Cron 定时任务..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
# 备份现有 crontab
crontab -l > /tmp/crontab.bak 2>/dev/null || true

# 删除旧的监控任务（如果存在）
crontab -l 2>/dev/null | grep -v "arcteryx-monitor" > /tmp/crontab.new || true

# 添加新任务（每30分钟运行一次）
echo "*/30 * * * * cd $HOME/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1" >> /tmp/crontab.new

# 安装新 crontab
crontab /tmp/crontab.new

echo "✓ Cron 任务已设置"
crontab -l | grep arcteryx
ENDSSH

echo "✓ Cron 定时任务设置完成"

# 清理临时目录
rm -rf "$DEPLOY_DIR"

echo ""
echo "============================================"
echo "✅ 部署完成！"
echo "============================================"
echo ""
echo "📝 后续步骤:"
echo ""
echo "1. 配置通知（可选）:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   cd ~/arcteryx-monitor"
echo "   nano .env  # 编辑环境变量"
echo ""
echo "2. 查看日志:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   tail -f ~/arcteryx-monitor/logs/monitor.log"
echo ""
echo "3. 查看最新报告:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   ls -lt ~/arcteryx-monitor/data/report_*.txt | head -1 | xargs cat"
echo ""
echo "4. 手动运行测试:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   cd ~/arcteryx-monitor && ./run.sh"
echo ""
echo "监控将每30分钟自动运行一次！"
echo ""

