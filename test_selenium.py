#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium 测试脚本 - 验证环境是否正常
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

print("=" * 60)
print("Selenium 环境测试")
print("=" * 60)

# 创建Chrome选项
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')

try:
    print("\n1. 正在启动 Chrome 浏览器...")
    driver = webdriver.Chrome(options=options)
    print("✓ Chrome 浏览器启动成功！")
    
    print("\n2. 正在访问测试网页...")
    driver.get("https://www.google.com")
    print(f"✓ 成功访问，页面标题: {driver.title}")
    
    print("\n3. 正在访问 Arc'teryx Outlet...")
    driver.get("https://outlet.arcteryx.com/ca/zh/c/mens")
    time.sleep(5)
    print(f"✓ 成功访问，页面标题: {driver.title}")
    
    # 保存页面源代码
    with open("data/test_page.html", "w", encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"✓ 页面源代码已保存到 data/test_page.html")
    
    # 尝试查找元素
    print("\n4. 正在查找页面元素...")
    body = driver.find_element("tag name", "body")
    print(f"✓ 找到 body 元素，长度: {len(body.text)} 字符")
    
    # 截图
    driver.save_screenshot("data/screenshot.png")
    print("✓ 截图已保存到 data/screenshot.png")
    
    driver.quit()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！Selenium 环境正常！")
    print("=" * 60)
    print("\n您现在可以运行: ./run.sh")
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    print("\n请检查：")
    print("1. 是否已安装 Google Chrome")
    print("2. 网络连接是否正常")
    print("3. 查看 SETUP_CHROME.md 获取帮助")
    
    try:
        driver.quit()
    except:
        pass

