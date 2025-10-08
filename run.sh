#!/bin/bash
# Arc'teryx Outlet 监控工具 - 运行脚本

# 激活虚拟环境
source venv/bin/activate

# 运行 Selenium 版本的监控脚本（支持 JavaScript 渲染的网站）
python3 monitor_selenium.py "$@"

