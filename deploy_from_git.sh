#!/bin/bash
# 从 Git 仓库部署到 AWS EC2

set -e  # 遇到错误立即退出

echo "============================================"
echo "从 Git 部署 Arc'teryx Monitor 到 AWS"
echo "============================================"
echo ""

# 检查参数
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "用法: ./deploy_from_git.sh <GIT_REPO_URL> <EC2_IP> <KEY_FILE> [EC2_USER]"
    echo ""
    echo "示例:"
    echo "  ./deploy_from_git.sh \\"
    echo "    https://github.com/username/arcteryx-monitor.git \\"
    echo "    54.123.45.67 \\"
    echo "    ~/mykey.pem"
    echo ""
    echo "或使用私有仓库（SSH）:"
    echo "  ./deploy_from_git.sh \\"
    echo "    git@github.com:username/arcteryx-monitor.git \\"
    echo "    54.123.45.67 \\"
    echo "    ~/mykey.pem"
    exit 1
fi

GIT_REPO=$1
EC2_IP=$2
KEY_FILE=${3:-~/.ssh/id_rsa}
EC2_USER=${4:-ec2-user}  # 默认 ec2-user，Ubuntu 使用 ubuntu

echo "📋 部署信息:"
echo "  Git 仓库: $GIT_REPO"
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
echo "2️⃣  在 EC2 上配置 Git 和依赖..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << ENDSSH
# 检测操作系统并安装依赖
if [ -f /etc/redhat-release ]; then
    # Amazon Linux / CentOS / RHEL
    echo "  检测到 Amazon Linux / RHEL"
    
    # 更新系统
    sudo yum update -y
    
    # 安装 Git
    sudo yum install -y git
    
    # 安装 Python 3
    sudo yum install -y python3 python3-pip
    
    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        echo "  安装 Google Chrome..."
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
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
    
    # 安装 Git
    sudo apt install -y git
    
    # 安装 Python 3
    sudo apt install -y python3 python3-pip python3-venv
    
    # 安装 Chrome
    if ! command -v google-chrome &> /dev/null; then
        echo "  安装 Google Chrome..."
        wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
        sudo apt install -y ./google-chrome-stable_current_amd64.deb
        rm -f google-chrome-stable_current_amd64.deb
    fi
fi

echo "✓ 依赖安装完成"
ENDSSH

echo "✓ EC2 环境配置完成"

echo ""
echo "3️⃣  从 Git 克隆代码..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << ENDSSH
# 如果目录已存在，先备份
if [ -d ~/arcteryx-monitor ]; then
    echo "  检测到现有安装，正在备份..."
    mv ~/arcteryx-monitor ~/arcteryx-monitor.backup.\$(date +%Y%m%d_%H%M%S)
fi

# 克隆仓库
echo "  正在克隆仓库..."
if [[ "$GIT_REPO" == git@* ]]; then
    # SSH 方式克隆
    echo "  使用 SSH 克隆（确保已配置 SSH 密钥）"
    GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git clone "$GIT_REPO" ~/arcteryx-monitor
else
    # HTTPS 方式克隆
    git clone "$GIT_REPO" ~/arcteryx-monitor
fi

cd ~/arcteryx-monitor

# 创建必要的目录
mkdir -p data logs

echo "✓ 代码克隆完成"
ENDSSH

echo "✓ 代码克隆成功"

echo ""
echo "4️⃣  配置 Python 环境..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd ~/arcteryx-monitor

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
chmod +x setup.sh

echo "✓ Python 环境配置完成"
ENDSSH

echo "✓ Python 环境配置完成"

echo ""
echo "5️⃣  测试运行..."

ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" << 'ENDSSH'
cd ~/arcteryx-monitor
source venv/bin/activate

echo "  运行测试..."
python3 test_selenium.py 2>&1 | head -30

echo ""
echo "  运行首次监控..."
timeout 300 ./run.sh || echo "  (超时或完成)"
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
echo "*/30 * * * * cd \$HOME/arcteryx-monitor && ./run.sh >> logs/monitor.log 2>&1" >> /tmp/crontab.new

# 安装新 crontab
crontab /tmp/crontab.new

echo "✓ Cron 任务已设置"
echo ""
echo "当前 Cron 任务:"
crontab -l | grep arcteryx
ENDSSH

echo "✓ Cron 定时任务设置完成"

echo ""
echo "============================================"
echo "✅ Git 部署完成！"
echo "============================================"
echo ""
echo "📝 项目信息:"
echo "  Git 仓库: $GIT_REPO"
echo "  EC2 位置: $EC2_USER@$EC2_IP:~/arcteryx-monitor"
echo ""
echo "📝 后续步骤:"
echo ""
echo "1. 配置通知（可选）:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   cd ~/arcteryx-monitor"
echo "   cp .env.example .env"
echo "   nano .env  # 编辑环境变量"
echo ""
echo "2. 查看日志:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   tail -f ~/arcteryx-monitor/logs/monitor.log"
echo ""
echo "3. 手动运行测试:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   cd ~/arcteryx-monitor && ./run.sh"
echo ""
echo "4. 更新代码（当您推送新版本到 Git 后）:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   cd ~/arcteryx-monitor && git pull"
echo ""
echo "5. 配置 SSH 密钥（用于私有仓库，可选）:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo "   ssh-keygen -t ed25519 -C 'your_email@example.com'"
echo "   cat ~/.ssh/id_ed25519.pub  # 添加到 GitHub Deploy Keys"
echo ""
echo "监控将每30分钟自动运行一次！"
echo ""

