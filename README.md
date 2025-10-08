# Arc'teryx Outlet 商品监控工具

这是一个用于监控 Arc'teryx Outlet 网站商品更新的 Python 工具。可以自动检测新商品、价格变化和下架商品。

## 功能特性

✨ **核心功能：**
- 🔍 自动抓取 Arc'teryx Outlet 男装商品信息
- 🆕 检测新上架的商品
- 💰 监控商品价格变化
- 📤 追踪已下架的商品
- 📊 生成详细的监控报告
- 💾 保存历史记录供后续分析
- ⏰ 支持单次运行或持续监控模式

## 安装步骤

### 1. 确保已安装 Python 3.7+

```bash
python3 --version
```

### 2. 安装依赖包

```bash
pip3 install -r requirements.txt
```

或者手动安装：

```bash
pip3 install requests beautifulsoup4 lxml
```

## 使用方法

### 运行一次监控

```bash
python3 monitor.py
```

这将执行一次商品检查，与上次保存的数据进行比较，并生成报告。

### 持续监控模式

```bash
# 默认每30分钟检查一次
python3 monitor.py --continuous

# 自定义检查间隔（例如每60分钟）
python3 monitor.py --continuous --interval 60

# 简写形式
python3 monitor.py -c -i 60
```

### 自定义数据目录

```bash
python3 monitor.py --data-dir /path/to/data
```

### 查看帮助信息

```bash
python3 monitor.py --help
```

## 输出文件说明

监控工具会在 `data/` 目录下生成以下文件：

- **`products.json`** - 当前商品数据
- **`history.json`** - 历史变化记录（最近100条）
- **`changes.json`** - 最新一次的变化详情
- **`report_YYYYMMDD_HHMMSS.txt`** - 每次运行的文本报告
- **`page_content.html`** - 网页原始内容（调试用）

## 监控报告示例

```
============================================================
Arc'teryx Outlet 商品监控报告
============================================================
监控时间: 2025-10-08T10:30:00.123456
监控网址: https://outlet.arcteryx.com/ca/zh/c/mens

📊 统计信息:
  总商品数: 45
  新商品: 3
  已下架: 1
  价格变化: 2

🆕 新增商品:
  • Beta AR Jacket Men's
    价格: CAD $399.00
    链接: https://outlet.arcteryx.com/ca/zh/...

💰 价格变化:
  • Atom LT Hoody Men's
    CAD $269.00 → CAD $229.00
    链接: https://outlet.arcteryx.com/ca/zh/...

📤 已下架商品:
  • Gamma MX Hoody Men's (CAD $199.00)

============================================================
```

## 定时任务设置

### 使用 cron（macOS/Linux）

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加定时任务（例如每小时运行一次）：
```bash
0 * * * * cd /Users/at/Desktop/ARC && /usr/bin/python3 monitor.py >> logs/monitor.log 2>&1
```

3. 或者每天早上9点和晚上9点运行：
```bash
0 9,21 * * * cd /Users/at/Desktop/ARC && /usr/bin/python3 monitor.py >> logs/monitor.log 2>&1
```

### 使用 launchd（macOS 推荐）

创建 `~/Library/LaunchAgents/com.arcteryx.monitor.plist` 文件。

## 高级用法

### 作为 Python 模块使用

```python
from monitor import ArcOutletMonitor

# 创建监控器实例
monitor = ArcOutletMonitor(data_dir="my_data")

# 运行一次
monitor.run_once()

# 或持续监控
monitor.run_continuous(interval_minutes=30)
```

### 自定义网页解析

如果网站结构发生变化，您可能需要修改 `parse_products()` 方法中的 CSS 选择器。

## 注意事项

⚠️ **重要提示：**

1. **请遵守网站使用条款**：不要过于频繁地请求网页，建议间隔至少 15-30 分钟
2. **网站结构变化**：如果 Arc'teryx 网站更新了页面结构，可能需要更新解析器
3. **JavaScript 渲染**：某些商品可能需要 JavaScript 才能加载，如遇此情况需使用 Selenium 等工具
4. **网络连接**：确保网络连接稳定，工具会处理常见的网络错误

## 故障排查

### 问题：无法获取商品信息

**解决方案：**
1. 检查网络连接
2. 查看 `data/page_content.html` 文件，确认网页是否正确下载
3. 网站可能需要 JavaScript 渲染，考虑使用 Selenium

### 问题：解析不到商品

**解决方案：**
1. 打开 `data/page_content.html` 查看网页结构
2. 在 `monitor.py` 中调整 `parse_products()` 方法的 CSS 选择器
3. 可以使用浏览器开发者工具查看商品元素的 class 和 id

## 数据隐私

- 所有数据仅保存在本地 `data/` 目录
- 不会上传任何数据到第三方服务器
- 您可以随时删除数据目录清除所有记录

## 监控网址

当前监控的网址：[https://outlet.arcteryx.com/ca/zh/c/mens](https://outlet.arcteryx.com/ca/zh/c/mens)

如需监控其他页面，可以修改 `monitor.py` 中的 `self.url` 参数。

## 许可证

本工具仅供个人学习和研究使用。

## 更新日志

- **v1.0.0** (2025-10-08)
  - 初始版本
  - 支持商品监控、价格追踪
  - 支持单次和持续监控模式
  - 生成详细报告

---

**开始监控您喜欢的 Arc'teryx 商品吧！** 🏔️

