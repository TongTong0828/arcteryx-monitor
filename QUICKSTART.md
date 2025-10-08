# 快速开始指南

## 🚀 三步开始监控

### 第一步：安装依赖

```bash
cd /Users/at/Desktop/ARC
./setup.sh
```

这会自动创建虚拟环境并安装所有依赖。

### 第二步：运行第一次监控

```bash
./run.sh
```

第一次运行会保存当前的商品信息作为基准。

### 第三步：开启持续监控

```bash
# 每30分钟检查一次（推荐）
./run.sh --continuous

# 或者每60分钟检查一次
./run.sh --continuous --interval 60
```

## 📊 查看监控结果

所有数据保存在 `data/` 目录：

- 查看最新变化：`cat data/changes.json`
- 查看当前商品：`cat data/products.json`
- 查看历史记录：`cat data/history.json`
- 查看报告：`ls data/report_*.txt`

## 💡 常用命令

```bash
# 查看最新报告
ls -lt data/report_*.txt | head -1 | xargs cat

# 查看有多少新商品
cat data/changes.json | grep -A 5 "new_products"

# 查看价格变化
cat data/changes.json | grep -A 5 "price_changes"
```

## ⏰ 设置定时任务（可选）

### 方式一：使用 launchd（推荐 macOS 用户）

1. 创建日志目录：
```bash
mkdir -p logs
```

2. 复制并编辑配置文件：
```bash
cp example_launchd.plist ~/Library/LaunchAgents/com.arcteryx.monitor.plist
```

3. 加载定时任务：
```bash
launchctl load ~/Library/LaunchAgents/com.arcteryx.monitor.plist
```

4. 查看状态：
```bash
launchctl list | grep arcteryx
```

5. 如需停止：
```bash
launchctl unload ~/Library/LaunchAgents/com.arcteryx.monitor.plist
```

### 方式二：使用 cron

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每小时运行一次）
0 * * * * cd /Users/at/Desktop/ARC && ./run.sh >> logs/monitor.log 2>&1
```

## 🔔 如何获得通知

### macOS 桌面通知

安装 `pync`：
```bash
pip3 install pync
```

在代码中添加通知功能（可在 `generate_report()` 方法后）。

### 邮件通知

可以使用 Python 的 `smtplib` 发送邮件通知。

### Telegram/微信通知

可以集成 Telegram Bot 或企业微信 Webhook。

## ❓ 常见问题

**Q: 首次运行为什么显示"这是首次运行"？**  
A: 这是正常的，首次运行会保存当前商品信息作为基准，之后的运行才会检测变化。

**Q: 如何监控其他页面？**  
A: 修改 `monitor.py` 中的 `self.url` 变量。

**Q: 检测不到商品怎么办？**  
A: 查看 `data/page_content.html` 确认网页内容，可能需要调整 CSS 选择器。

**Q: 多久检查一次比较合适？**  
A: 建议 30-60 分钟，不要太频繁以避免给服务器造成压力。

## 📞 需要帮助？

- 查看详细文档：`cat README.md`
- 查看调试信息：检查 `data/page_content.html` 和 `logs/` 目录
- 修改解析器：编辑 `monitor.py` 中的 `parse_products()` 方法

---

**开始监控，不错过任何折扣！** 🎉

