#!/usr/bin/env python3
"""
Arc'teryx Outlet 监控工具 - 最终版
"""

import os
import json
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    """创建优化的 Chrome WebDriver"""
    logger.info("正在初始化 Chrome WebDriver...")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-images')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1280,720')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    chrome_options.page_load_strategy = 'eager'
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(15)
        logger.info("✓ Chrome WebDriver 初始化成功")
        return driver
    except Exception as e:
        logger.error(f"✗ 初始化 WebDriver 失败: {e}")
        raise

def fetch_products(driver, url):
    """获取商品信息"""
    logger.info(f"正在访问 {url}...")
    
    try:
        driver.get(url)
        logger.info("等待页面加载...")
        
        # 等待 body 元素
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        logger.info("✓ 页面已加载，等待 JavaScript 渲染...")
        
        # 等待 JavaScript 渲染
        time.sleep(15)
        
        # 滚动页面加载更多产品
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            logger.info(f"滚动 {i+1}/3...")
        
        # 查找产品链接
        product_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/products/"]')
        logger.info(f"找到 {len(product_links)} 个产品链接")
        
        if not product_links:
            logger.warning("未找到产品链接")
            return []
        
        # 提取产品信息
        products = []
        seen_urls = set()
        
        for idx, link in enumerate(product_links):
            try:
                url = link.get_attribute('href')
                
                if not url:
                    logger.debug(f"链接 {idx} 没有 href 属性")
                    continue
                
                # 只处理产品页面链接
                if '/products/' not in url:
                    continue
                
                # 去重
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                logger.info(f"处理产品链接: {url}")
                
                # 提取产品 ID
                product_id = url.rstrip('/').split('/')[-1] if url else None
                
                # 尝试获取产品名称
                name = None
                try:
                    # 尝试从链接文本获取
                    name = link.text.strip()
                    if not name:
                        # 尝试从 img alt 获取
                        imgs = link.find_elements(By.TAG_NAME, 'img')
                        if imgs:
                            name = imgs[0].get_attribute('alt')
                    if not name:
                        # 尝试从 title 属性获取
                        name = link.get_attribute('title')
                except Exception as e:
                    logger.debug(f"获取名称失败: {e}")
                
                # 尝试获取价格
                price = None
                try:
                    # 查找父元素中的价格
                    parent = link
                    for _ in range(5):  # 向上查找5层
                        try:
                            parent = parent.find_element(By.XPATH, '..')
                            price_elements = parent.find_elements(By.CSS_SELECTOR, '[class*="price"], [class*="Price"], [data-testid*="price"]')
                            if price_elements:
                                price_text = price_elements[0].text.strip()
                                if price_text and ('$' in price_text or '¥' in price_text or price_text.replace('.', '').isdigit()):
                                    price = price_text
                                    break
                        except:
                            break
                except Exception as e:
                    logger.debug(f"获取价格失败: {e}")
                
                # 即使信息不完整也保存
                if product_id or url:
                    product = {
                        'id': product_id or url.split('?')[0],  # 使用完整URL作为后备ID
                        'name': name or product_id or '未知商品',
                        'price': price,
                        'link': url,
                        'timestamp': datetime.now().isoformat()
                    }
                    products.append(product)
                    logger.info(f"✓ 提取商品: {product['name'][:50]}")
            
            except Exception as e:
                logger.warning(f"处理链接 {idx} 失败: {e}")
                continue
        
        logger.info(f"✓ 成功提取 {len(products)} 个商品")
        return products
        
    except Exception as e:
        logger.error(f"获取商品失败: {e}")
        return []

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
    old_ids = {p['id']: p for p in old_products if p.get('id')}
    new_ids = {p['id']: p for p in new_products if p.get('id')}
    
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
            logger.info(f"  - {p.get('name', 'N/A')} ({p.get('price', 'N/A')})")
            if len(changes['added']) > 10:
                logger.info(f"  ... 还有 {len(changes['added']) - 10} 个")
    
    if changes['removed']:
        logger.info(f"\n📦 下架商品 ({len(changes['removed'])}个):")
        for p in changes['removed'][:10]:
            logger.info(f"  - {p.get('name', 'N/A')}")
            if len(changes['removed']) > 10:
                logger.info(f"  ... 还有 {len(changes['removed']) - 10} 个")
    
    if changes['price_changes']:
        logger.info(f"\n💰 价格变化 ({len(changes['price_changes'])}个):")
        for c in changes['price_changes'][:10]:
            logger.info(f"  - {c['product'].get('name', 'N/A')}: {c['old_price']} → {c['new_price']}")
            if len(changes['price_changes']) > 10:
                logger.info(f"  ... 还有 {len(changes['price_changes']) - 10} 个")
    
    if not any([changes['added'], changes['removed'], changes['price_changes']]):
        logger.info("\n✓ 无变化")

def main():
    """主函数"""
    ensure_directories()
    
    logger.info("=" * 60)
    logger.info("Arc'teryx Outlet 监控工具")
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
            logger.info(f"基准数据已创建，包含 {len(current_products)} 个商品")
        else:
            # 比较变化
            logger.info(f"对比基准数据（{len(baseline_products)} 个商品）...")
            changes = compare_products(baseline_products, current_products)
            print_changes(changes)
            
            # 更新基准
            save_data(current_products)
        
        logger.info("\n✓ 监控完成")
        
    except Exception as e:
        logger.error(f"运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✓ 浏览器已关闭")
            except:
                pass

if __name__ == "__main__":
    main()

