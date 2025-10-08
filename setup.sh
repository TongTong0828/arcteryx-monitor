#!/bin/bash
# Arc'teryx Outlet 监控工具 - 安装脚本

echo "================================"
echo "Arc'teryx Outlet 监控工具安装"
echo "================================"
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装 Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ 找到 Python $PYTHON_VERSION"
echo ""

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "✓ 虚拟环境创建成功"
    else
        echo "❌ 虚拟环境创建失败"
        exit 1
    fi
else
    echo "✓ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境并安装依赖
echo "安装 Python 依赖包..."
source venv/bin/activate
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi
echo ""

# 创建必要的目录
echo "创建数据目录..."
mkdir -p data
mkdir -p logs
echo "✓ 目录创建成功"
echo ""

# 设置执行权限
chmod +x monitor.py
echo "✓ 已设置执行权限"
echo ""

echo "================================"
echo "安装完成！"
echo "================================"
echo ""
echo "使用方法："
echo "  1. 运行一次监控："
echo "     ./run.sh"
echo "     或者："
echo "     source venv/bin/activate && python3 monitor.py"
echo ""
echo "  2. 持续监控（每30分钟）："
echo "     ./run.sh --continuous"
echo ""
echo "  3. 设置定时任务（可选）："
echo "     查看 README.md 了解如何使用 cron 或 launchd"
echo ""
echo "首次运行将保存当前商品信息作为基准。"
echo "祝您捕获到心仪的商品！🏔️"
echo ""

