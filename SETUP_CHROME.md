# Chrome 和 ChromeDriver 设置指南

## 自动方式（推荐）⭐

**好消息！** Selenium 4.15+ 版本包含自动驱动管理功能，无需手动安装 ChromeDriver。

只需确保已安装 **Google Chrome 浏览器**，然后直接运行监控脚本即可：

```bash
./run.sh
```

Selenium 会自动下载和管理 ChromeDriver。

## 检查 Chrome 浏览器

确认您已安装 Google Chrome：

```bash
# macOS
open -a "Google Chrome"

# 或检查版本
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

如果没有安装 Chrome，请访问：https://www.google.com/chrome/

## 手动安装 ChromeDriver（可选）

如果自动方式不工作，可以手动安装：

### 方式 1: 使用 Homebrew（可能有兼容性问题）

```bash
brew install chromedriver
```

**注意**：ChromeDriver 在 Homebrew 中已被标记为弃用，可能无法通过 macOS Gatekeeper。

### 方式 2: 手动下载

1. 访问 [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
2. 下载与您的 Chrome 版本匹配的 ChromeDriver
3. 解压并移动到系统路径：

```bash
# 假设下载到 ~/Downloads/chromedriver
chmod +x ~/Downloads/chromedriver
sudo mv ~/Downloads/chromedriver /usr/local/bin/
```

4. 如果遇到安全警告：

```bash
xattr -d com.apple.quarantine /usr/local/bin/chromedriver
```

### 方式 3: 使用 WebDriver Manager（Python 包）

在虚拟环境中安装：

```bash
source venv/bin/activate
pip install webdriver-manager
```

然后修改 `monitor_selenium.py` 使用 WebDriver Manager。

## 故障排查

### 问题：Chrome 版本不匹配

**错误消息**：`session not created: This version of ChromeDriver only supports Chrome version XX`

**解决方案**：
- 更新 Chrome 浏览器到最新版本
- 让 Selenium Manager 自动处理（推荐）

### 问题：权限被拒绝

**错误消息**：`Permission denied` 或 `Gatekeeper blocked`

**解决方案**：

```bash
# 移除隔离属性
xattr -d com.apple.quarantine /path/to/chromedriver

# 或在系统偏好设置中允许
# 系统偏好设置 > 安全性与隐私 > 通用 > 允许
```

### 问题：找不到 Chrome

**错误消息**：`Chrome not found`

**解决方案**：
- 安装 Google Chrome 浏览器
- 或指定 Chrome 二进制文件路径（在代码中配置）

## 测试安装

运行以下命令测试：

```bash
./run.sh
```

如果看到 "正在访问: https://outlet.arcteryx.com/..." 说明配置成功！

## 使用其他浏览器

如果 Chrome 有问题，可以使用 Firefox：

1. 安装 Firefox：
```bash
brew install firefox
```

2. 修改 `monitor_selenium.py` 中的代码：
```python
# 将 webdriver.Chrome() 改为 webdriver.Firefox()
```

Selenium Manager 也会自动处理 GeckoDriver（Firefox 的驱动）。

---

**遇到问题？** 查看 `data/page_source.html` 以调试网页抓取问题。

