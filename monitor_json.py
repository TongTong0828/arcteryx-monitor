#!/usr/bin/env python3
"""
Arc'teryx Outlet 监控工具 - JSON 版（直接提取 Next.js 数据）
"""

import os
import json
import time
import logging
import re
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
    chrome_options.add_argument('--remote-debugging-port=9222')  # 添加调试端口
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 性能优化
    chrome_options.page_load_strategy = 'eager'  # 不等待所有资源加载完成
    
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
    """获取商品信息（通过提取 JSON 数据）"""
    logger.info(f"正在访问 {url}...")
    
    try:
        driver.get(url)
        logger.info("等待页面加载...")
        
        # 等待 body 元素
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        logger.info("✓ 页面已加载")
        
        # 获取页面源码
        page_source = driver.page_source
        
        # 提取 __NEXT_DATA__ JSON
        json_data = extract_next_data(page_source)
        
        if json_data:
            # 解析产品数据
            products = parse_json_products(json_data)
            if products:
                logger.info(f"✓ 成功提取 {len(products)} 个商品")
                return products
        
        logger.warning("未能从 JSON 中提取商品数据")
        return []
        
    except Exception as e:
        logger.error(f"获取商品失败: {e}")
        return []

def extract_next_data(html):
    """从 HTML 中提取 __NEXT_DATA__ JSON"""
    try:
        # 查找 <script id="__NEXT_DATA__" type="application/json">...</script>
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            logger.info("✓ 成功提取 __NEXT_DATA__ JSON")
            return data
        else:
            logger.warning("未找到 __NEXT_DATA__ JSON")
            return None
    except Exception as e:
        logger.error(f"解析 JSON 失败: {e}")
        return None

def parse_json_products(data):
    """从 JSON 数据中解析产品"""
    products = []
    
    try:
        # 尝试多个可能的数据路径
        paths = [
            ['props', 'pageProps', 'products'],
            ['props', 'pageProps', 'productList'],
            ['props', 'pageProps', 'items'],
            ['props', 'pageProps', 'data', 'products'],
            ['props', 'pageProps', 'catalog', 'products'],
        ]
        
        product_list = None
        for path in paths:
            try:
                current = data
                for key in path:
                    current = current[key]
                if current and isinstance(current, list):
                    product_list = current
                    logger.info(f"✓ 在路径 {' -> '.join(path)} 找到产品列表")
                    break
            except (KeyError, TypeError):
                continue
        
        if not product_list:
            # 如果没有找到，保存 JSON 用于调试
            with open('next_data_debug.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("JSON 数据已保存到 next_data_debug.json 用于调试")
            logger.warning("在预定义路径中未找到产品列表")
            return []
        
        # 解析产品
        for item in product_list:
            try:
                product = {
                    'id': item.get('id') or item.get('productId') or item.get('sku'),
                    'name': item.get('name') or item.get('title') or item.get('productName'),
                    'price': item.get('price') or item.get('salePrice') or item.get('currentPrice'),
                    'link': item.get('url') or item.get('link') or item.get('href'),
                    'timestamp': datetime.now().isoformat()
                }
                
                # 确保有基本信息
                if product['id'] or product['name']:
                    products.append(product)
            except Exception as e:
                logger.warning(f"解析单个产品失败: {e}")
                continue
        
        return products
        
    except Exception as e:
        logger.error(f"解析产品列表失败: {e}")
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
    
    if changes['removed']:
        logger.info(f"\n📦 下架商品 ({len(changes['removed'])}个):")
        for p in changes['removed'][:10]:
            logger.info(f"  - {p.get('name', 'N/A')}")
    
    if changes['price_changes']:
        logger.info(f"\n💰 价格变化 ({len(changes['price_changes'])}个):")
        for c in changes['price_changes'][:10]:
            logger.info(f"  - {c['product'].get('name', 'N/A')}: {c['old_price']} → {c['new_price']}")
    
    if not any([changes['added'], changes['removed'], changes['price_changes']]):
        logger.info("\n✓ 无变化")

def main():
    """主函数"""
    ensure_directories()
    
    logger.info("=" * 60)
    logger.info("Arc'teryx Outlet 监控工具 - JSON 版")
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

