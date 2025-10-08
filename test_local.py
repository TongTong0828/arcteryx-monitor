#!/usr/bin/env python3
"""
本地测试脚本 - 简化版
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_arcteryx():
    print("=" * 60)
    print("Arc'teryx Outlet 本地测试")
    print("=" * 60)
    
    # 配置 Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 反检测配置
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = None
    try:
        print("\n1. 启动浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 设置更长的超时时间
        driver.set_page_load_timeout(180)  # 3分钟
        driver.set_script_timeout(60)
        
        # 移除 webdriver 特征
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✓ 浏览器已启动")
        
        print("\n2. 访问网站...")
        driver.get("https://outlet.arcteryx.com/ca/zh/c/mens")
        print("✓ 请求已发送")
        
        print("\n3. 等待页面加载...")
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        print("✓ 页面 body 已加载")
        
        print("\n4. 等待 JavaScript 渲染（30秒）...")
        for i in range(6):
            time.sleep(5)
            print(f"   {(i+1)*5} 秒...")
        
        print("\n5. 滚动页面加载更多内容...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            print(f"   滚动 {i+1}/3")
        
        print("\n6. 查找产品元素...")
        
        # 尝试多种选择器
        selectors_to_try = [
            ('a[href*="/products/"]', '产品链接'),
            ('div[data-testid*="product"]', 'data-testid 产品'),
            ('[class*="ProductCard"]', 'ProductCard 类'),
            ('[class*="product-card"]', 'product-card 类'),
            ('article', 'article 标签'),
        ]
        
        found_products = []
        
        for selector, name in selectors_to_try:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✓ {name}: 找到 {len(elements)} 个元素")
                    
                    # 过滤掉非产品链接
                    if 'href' in selector:
                        valid_elements = []
                        for elem in elements:
                            href = elem.get_attribute('href')
                            if href and '/products/' in href and 'onetrust.com' not in href:
                                valid_elements.append(elem)
                        
                        if valid_elements:
                            print(f"   ✓ 其中有效产品链接: {len(valid_elements)} 个")
                            found_products = valid_elements
                            break
                else:
                    print(f"   ✗ {name}: 未找到")
            except Exception as e:
                print(f"   ✗ {name}: 出错 - {e}")
        
        if found_products:
            print(f"\n7. 成功！找到 {len(found_products)} 个产品")
            print("\n前 5 个产品:")
            for i, elem in enumerate(found_products[:5], 1):
                try:
                    url = elem.get_attribute('href')
                    text = elem.text.strip()
                    product_id = url.rstrip('/').split('/')[-1] if url else 'unknown'
                    print(f"\n   产品 {i}:")
                    print(f"   ID: {product_id}")
                    print(f"   URL: {url}")
                    print(f"   文本: {text[:50] if text else '(无)'}")
                except Exception as e:
                    print(f"   处理产品 {i} 时出错: {e}")
            
            return True
        else:
            print("\n7. 未找到有效产品")
            print("\n调试信息：")
            print(f"   页面标题: {driver.title}")
            print(f"   当前 URL: {driver.current_url}")
            
            # 保存页面源码
            with open('/Users/at/Desktop/ARC/debug_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"   页面源码已保存到: /Users/at/Desktop/ARC/debug_page.html")
            
            return False
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            driver.quit()
            print("\n✓ 浏览器已关闭")

if __name__ == "__main__":
    success = test_arcteryx()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功！可以部署到 AWS")
    else:
        print("❌ 测试失败，需要调整配置")
    print("=" * 60)

