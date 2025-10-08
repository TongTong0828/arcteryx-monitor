#!/bin/bash
# Arc'teryx Outlet 监控工具 - 运行脚本

# 激活虚拟环境
source venv/bin/activate

# 运行监控脚本（使用 undetected-chromedriver）
python3 monitor.py "$@"

