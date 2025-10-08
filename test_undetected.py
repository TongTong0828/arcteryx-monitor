#!/usr/bin/env python3
"""
使用 undetected-chromedriver 测试
"""

import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_with_undetected():
    print("=" * 60)
    print("使用 undetected-chromedriver 测试")
    print("=" * 60)
    
    driver = None
    try:
        print("\n1. 启动浏览器（undetected模式）...")
        
        options = uc.ChromeOptions()
        options.headless = True
        options.add_argument('--window-size=1920,1080')
        
        driver = uc.Chrome(options=options, version_main=141)  # 指定Chrome版本
        driver.set_page_load_timeout(60)
        
        print("✓ 浏览器已启动")
        
        print("\n2. 访问网站...")
        driver.get("https://outlet.arcteryx.com/ca/zh/c/mens")
        print("✓ 页面已加载")
        
        print("\n3. 等待 JavaScript 渲染（20秒）...")
        time.sleep(20)
        
        print("\n4. 滚动页面...")
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            print(f"   滚动 {i+1}/3")
        
        print("\n5. 查找产品...")
        
        # 查找产品链接 (正确的选择器是 /shop/mens/)
        product_links = driver.find_elements(By.CSS_SELECTOR, '.qa--product-tile__link, a[href*="/shop/mens/"]')
        
        # 过滤有效产品
        valid_products = []
        seen_urls = set()
        for link in product_links:
            href = link.get_attribute('href')
            if href and '/shop/mens/' in href and href not in seen_urls:
                seen_urls.add(href)
                valid_products.append(link)
        
        print(f"✓ 找到 {len(valid_products)} 个有效产品")
        
        if valid_products:
            print("\n前 5 个产品:")
            for i, link in enumerate(valid_products[:5], 1):
                try:
                    url = link.get_attribute('href')
                    text = link.text.strip()
                    product_id = url.rstrip('/').split('/')[-1] if url else 'unknown'
                    
                    # 尝试获取产品名称
                    try:
                        parent = link.find_element(By.XPATH, '..')
                        name_elem = parent.find_elements(By.CSS_SELECTOR, 'h3, h4, [class*="name"], [class*="Name"]')
                        if name_elem:
                            name = name_elem[0].text.strip()
                        else:
                            name = text or product_id
                    except:
                        name = text or product_id
                    
                    # 尝试获取价格
                    try:
                        parent = link
                        for _ in range(5):
                            parent = parent.find_element(By.XPATH, '..')
                            price_elems = parent.find_elements(By.CSS_SELECTOR, '[class*="price"], [class*="Price"]')
                            if price_elems:
                                price = price_elems[0].text.strip()
                                break
                        else:
                            price = None
                    except:
                        price = None
                    
                    print(f"\n   产品 {i}:")
                    print(f"   ID: {product_id}")
                    print(f"   名称: {name[:50] if name else '(无)'}")
                    print(f"   价格: {price if price else '(无)'}")
                    print(f"   URL: {url}")
                    
                except Exception as e:
                    print(f"   处理产品 {i} 时出错: {e}")
            
            print(f"\n✅ 成功！找到 {len(valid_products)} 个产品")
            return True
        else:
            print("\n❌ 未找到有效产品")
            
            # 保存页面源码
            with open('/Users/at/Desktop/ARC/debug_undetected.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print("页面源码已保存到 debug_undetected.html")
            
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
    success = test_with_undetected()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功！可以部署到 AWS")
    else:
        print("❌ 测试失败")
    print("=" * 60)

