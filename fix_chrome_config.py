#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化 Chrome 配置以适配低内存环境
"""

import os
import re

def optimize_chrome_config():
    """优化 Chrome 配置"""
    
    monitor_file = "monitor_selenium.py" 
    
    if not os.path.exists(monitor_file):
        print("❌ monitor_selenium.py 文件不存在")
        return
    
    with open(monitor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加更多 Chrome 优化选项
    old_options = '''        # 常用选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')'''
    
    new_options = '''        # 低内存环境优化选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-sync')
        options.add_argument('--metrics-recording-only')
        options.add_argument('--mute-audio')
        options.add_argument('--no-first-run')
        options.add_argument('--window-size=1280,720')  # 较小窗口
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max-old-space-size=256')  # 限制内存使用
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # 禁用图片和媒体加载以节省内存
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "profile.default_content_settings.popups": 0
        }
        options.add_experimental_option("prefs", prefs)'''
    
    if old_options in content:
        content = content.replace(old_options, new_options)
        print("✓ 已更新 Chrome 配置选项")
    else:
        print("⚠️  未找到需要替换的配置，可能已经是最新版本")
    
    # 修改超时时间
    content = re.sub(
        r'time\.sleep\(5\)  # 给页面更多时间来渲染',
        'time.sleep(8)  # 给页面更多时间来渲染',
        content
    )
    
    content = re.sub(
        r'WebDriverWait\(driver, 20\)',
        'WebDriverWait(driver, 30)',
        content
    )
    
    with open(monitor_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Chrome 配置优化完成")
    print("✓ 增加了低内存环境优化")
    print("✓ 延长了页面加载等待时间")

if __name__ == "__main__":
    optimize_chrome_config()
