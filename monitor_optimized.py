#!/usr/bin/env python3
"""
Arc'teryx Outlet 监控工具 - 优化版（适用于低内存 EC2 实例）
"""

import os
import json
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
TARGET_URL = "https://outlet.arcteryx.com/ca/zh/c/mens"
DATA_DIR = "data"
LOGS_DIR = "logs"
BASELINE_FILE = os.path.join(DATA_DIR, "baseline.json")

def ensure_directories():
    """确保必要的目录存在"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

def create_driver():
    """创建优化的 Chrome WebDriver（低内存配置）"""
    logger.info("正在初始化 Chrome WebDriver（优化模式）...")
    
    chrome_options = Options()
    
    # 必需的无头模式设置
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # 🚀 内存优化设置
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-plugins')
    chrome_options.add_argument('--disable-images')  # 不加载图片
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-javascript-harmony-shipping')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # 限制内存使用
    chrome_options.add_argument('--max-old-space-size=256')
    chrome_options.add_argument('--memory-pressure-off')
    chrome_options.add_argument('--single-process')  # 单进程模式
    
    # 窗口大小
    chrome_options.add_argument('--window-size=1280,720')
    
    # 用户代理
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 禁用自动化检测
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # 设置超时（缩短以节省资源）
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(20)
        
        # 移除自动化标记
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("✓ Chrome WebDriver 初始化成功（优化模式）")
        return driver
        
    except Exception as e:
        logger.error(f"✗ 初始化 WebDriver 失败: {e}")
        raise

def fetch_products(driver, url, max_retries=2):
    """获取商品信息（简化版）"""
    logger.info(f"正在访问 {url}...")
    
    for attempt in range(max_retries):
        try:
            driver.get(url)
            logger.info(f"页面请求已发送，等待加载... (尝试 {attempt + 1}/{max_retries})")
            
            # 等待页面基本加载完成（等待 body 元素）
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            logger.info("✓ 页面 body 已加载")
            
            # 额外等待 JavaScript 执行
            time.sleep(5)
            logger.info("等待 JavaScript 渲染...")
            
            # 尝试滚动触发懒加载
            driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(3)
            
            # 解析产品（不等待特定元素，直接尝试解析）
            products = parse_products(driver)
            
            if products:
                logger.info(f"✓ 成功获取 {len(products)} 个商品")
                return products
            else:
                logger.warning(f"未找到商品（尝试 {attempt + 1}/{max_retries}）")
                # 保存页面源码用于调试
                if attempt == max_retries - 1:
                    try:
                        with open('page_source.html', 'w', encoding='utf-8') as f:
                            f.write(driver.page_source)
                        logger.info("页面源码已保存到 page_source.html")
                    except:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        except TimeoutException:
            logger.warning(f"页面加载超时（尝试 {attempt + 1}/{max_retries}）")
            if attempt < max_retries - 1:
                time.sleep(5)
        except Exception as e:
            logger.error(f"获取商品失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    return []

def parse_products(driver):
    """解析产品元素"""
    products = []
    
    # 多种选择器
    selectors = [
        'div[data-testid="product-card"]',
        '.product-card',
        '[class*="ProductCard"]',
        'article[class*="product"]'
    ]
    
    product_elements = []
    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                product_elements = elements
                break
        except:
            continue
    
    if not product_elements:
        logger.warning("未找到任何产品元素")
        return []
    
    for element in product_elements[:30]:  # 限制处理数量
        try:
            product_data = parse_product_element(element)
            if product_data:
                products.append(product_data)
        except Exception as e:
            continue
    
    return products

def parse_product_element(element):
    """解析单个产品元素"""
    try:
        # 获取产品 ID
        product_id = None
        try:
            product_id = element.get_attribute('data-product-id') or \
                        element.get_attribute('data-id') or \
                        element.get_attribute('id')
        except:
            pass
        
        # 获取产品名称
        name = None
        name_selectors = [
            'h3', 'h4', '.product-name', '[class*="productName"]',
            '[class*="ProductName"]', '[data-testid*="name"]'
        ]
        for selector in name_selectors:
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, selector)
                name = name_elem.text.strip()
                if name:
                    break
            except:
                continue
        
        # 获取价格
        price = None
        price_selectors = [
            '.price', '[class*="price"]', '[data-testid*="price"]',
            'span[class*="Price"]'
        ]
        for selector in price_selectors:
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('$' in price_text or '¥' in price_text):
                    price = price_text
                    break
            except:
                continue
        
        # 获取链接
        link = None
        try:
            link_elem = element.find_element(By.TAG_NAME, 'a')
            link = link_elem.get_attribute('href')
            if link and not link.startswith('http'):
                link = f"https://outlet.arcteryx.com{link}"
        except:
            pass
        
        # 如果没有 ID，使用链接生成
        if not product_id and link:
            product_id = link.split('/')[-1]
        
        # 至少需要名称或 ID
        if name or product_id:
            return {
                'id': product_id or name,
                'name': name or product_id,
                'price': price,
                'link': link,
                'timestamp': datetime.now().isoformat()
            }
        
    except Exception as e:
        pass
    
    return None

def save_data(products, filename=BASELINE_FILE):
    """保存数据"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'products': products,
                'count': len(products),
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"✓ 数据已保存到 {filename}")
        return True
    except Exception as e:
        logger.error(f"✗ 保存数据失败: {e}")
        return False

def load_baseline():
    """加载基准数据"""
    try:
        if os.path.exists(BASELINE_FILE):
            with open(BASELINE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('products', [])
        return []
    except Exception as e:
        logger.error(f"加载基准数据失败: {e}")
        return []

def compare_products(old_products, new_products):
    """比较商品变化"""
    old_ids = {p['id']: p for p in old_products}
    new_ids = {p['id']: p for p in new_products}
    
    # 新增商品
    added = [p for pid, p in new_ids.items() if pid not in old_ids]
    
    # 下架商品
    removed = [p for pid, p in old_ids.items() if pid not in new_ids]
    
    # 价格变化
    price_changes = []
    for pid in set(old_ids.keys()) & set(new_ids.keys()):
        old_price = old_ids[pid].get('price')
        new_price = new_ids[pid].get('price')
        if old_price and new_price and old_price != new_price:
            price_changes.append({
                'product': new_ids[pid],
                'old_price': old_price,
                'new_price': new_price
            })
    
    return {
        'added': added,
        'removed': removed,
        'price_changes': price_changes
    }

def print_changes(changes):
    """打印变化"""
    if changes['added']:
        logger.info(f"\n🆕 新增商品 ({len(changes['added'])}个):")
        for p in changes['added'][:10]:
            logger.info(f"  - {p['name']} ({p.get('price', 'N/A')})")
    
    if changes['removed']:
        logger.info(f"\n📦 下架商品 ({len(changes['removed'])}个):")
        for p in changes['removed'][:10]:
            logger.info(f"  - {p['name']}")
    
    if changes['price_changes']:
        logger.info(f"\n💰 价格变化 ({len(changes['price_changes'])}个):")
        for c in changes['price_changes'][:10]:
            logger.info(f"  - {c['product']['name']}: {c['old_price']} → {c['new_price']}")
    
    if not any([changes['added'], changes['removed'], changes['price_changes']]):
        logger.info("\n✓ 无变化")

def main():
    """主函数"""
    ensure_directories()
    
    logger.info("=" * 60)
    logger.info("Arc'teryx Outlet 监控工具 - 优化版")
    logger.info("=" * 60)
    
    driver = None
    try:
        # 创建驱动
        driver = create_driver()
        
        # 获取当前商品
        current_products = fetch_products(driver, TARGET_URL)
        
        if not current_products:
            logger.error("未能获取商品数据")
            return
        
        # 加载基准数据
        baseline_products = load_baseline()
        
        if not baseline_products:
            # 首次运行，创建基准
            logger.info("首次运行，创建基准数据...")
            save_data(current_products)
        else:
            # 比较变化
            changes = compare_products(baseline_products, current_products)
            print_changes(changes)
            
            # 更新基准
            save_data(current_products)
        
        logger.info("\n✓ 监控完成")
        
    except Exception as e:
        logger.error(f"运行出错: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✓ 浏览器已关闭")
            except:
                pass

if __name__ == "__main__":
    main()

