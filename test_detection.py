#!/usr/bin/env python3
"""
测试不同的反检测配置
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_url(url, label):
    print(f"\n{'='*60}")
    print(f"测试: {label}")
    print(f"URL: {url}")
    print('='*60)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 更强的反检测
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    chrome_options.page_load_strategy = 'eager'
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # 移除 webdriver 标记
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("访问页面...")
        driver.get(url)
        
        # 等待页面加载
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print("✓ 页面已加载")
        
        # 等待 JavaScript
        print("等待 JavaScript 渲染...")
        time.sleep(20)
        
        # 滚动
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        # 查找产品链接
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/products/"]')
        print(f"\n找到 {len(product_links)} 个产品链接")
        
        # 显示前5个链接
        for i, link in enumerate(product_links[:5]):
            try:
                href = link.get_attribute('href')
                text = link.text.strip()[:50]
                if '/products/' in href and 'onetrust.com' not in href:
                    print(f"  {i+1}. {href}")
                    print(f"     文本: {text if text else '(无文本)'}")
            except:
                pass
        
        # 查找所有 a 标签
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        product_count = sum(1 for link in all_links if '/products/' in link.get_attribute('href') and 'onetrust.com' not in link.get_attribute('href'))
        print(f"\n实际产品链接数: {product_count}")
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

# 测试不同的 URL
test_url("https://outlet.arcteryx.com/us/en/c/mens", "美国站点 - 英语 - 男装")
test_url("https://outlet.arcteryx.com/us/en", "美国站点 - 英语 - 所有产品")
test_url("https://outlet.arcteryx.com/ca/en/c/mens", "加拿大站点 - 英语 - 男装")

