#!/usr/bin/env python3
"""
Arc'teryx Outlet 监控工具 - 最终版本
使用 undetected-chromedriver 绕过反爬虫检测
"""

import os
import json
import time
import logging
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# 导入邮件通知模块
try:
    from email_notifier import send_change_notification
    EMAIL_ENABLED = True
except ImportError:
    EMAIL_ENABLED = False
    logging.warning("邮件通知模块未找到，将跳过邮件发送")

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
    """创建 undetected Chrome WebDriver"""
    logger.info("正在初始化 Chrome WebDriver...")
    
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--window-size=1920,1080')
    
    try:
        driver = uc.Chrome(options=options, version_main=141)  # 指定 Chrome 版本
        driver.set_page_load_timeout(90)  # 增加超时时间
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
        logger.info("✓ 页面已加载，等待 JavaScript 渲染...")
        
        # 等待 JavaScript 渲染
        time.sleep(20)
        
        # 滚动页面加载更多产品
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            logger.info(f"滚动 {i+1}/3...")
        
        # 查找产品链接 (Arc'teryx Outlet 使用 /shop/mens/ 而不是 /products/)
        product_links = driver.find_elements(By.CSS_SELECTOR, '.qa--product-tile__link, a[href*="/shop/mens/"]')
        logger.info(f"找到 {len(product_links)} 个产品链接")
        
        # 提取产品信息
        products = []
        seen_urls = set()
        
        for idx, link in enumerate(product_links):
            try:
                href = link.get_attribute('href')
                
                if not href or '/shop/mens/' not in href:
                    continue
                
                # 去重
                if href in seen_urls:
                    continue
                seen_urls.add(href)
                
                # 提取产品 ID (从 URL 末尾)
                product_id = href.rstrip('/').split('/')[-1] if href else f'product_{idx}'
                
                # 尝试获取产品名称
                name = None
                try:
                    # 查找产品名称元素
                    parent = link.find_element(By.XPATH, '..')
                    name_elems = parent.find_elements(By.CSS_SELECTOR, '.product-tile-name, [class*="tile-name"]')
                    if name_elems:
                        name = name_elems[0].text.strip()
                    
                    if not name:
                        # 备用：从链接文本获取
                        name = link.text.strip()
                    
                    if not name:
                        # 再备用：从图片 alt 获取
                        imgs = link.find_elements(By.TAG_NAME, 'img')
                        if imgs:
                            name = imgs[0].get_attribute('alt')
                except Exception as e:
                    logger.debug(f"获取产品名称失败: {e}")
                
                # 尝试获取价格
                price = None
                try:
                    # 向上查找父元素中的价格
                    parent = link
                    for _ in range(5):
                        try:
                            parent = parent.find_element(By.XPATH, '..')
                            price_elems = parent.find_elements(By.CSS_SELECTOR, '.qa--product-tile__prices, [class*="price"]')
                            if price_elems:
                                price_text = price_elems[0].text.strip()
                                # 清理价格文本（可能包含多行）
                                price = ' '.join(price_text.split())
                                if price:
                                    break
                        except:
                            break
                except Exception as e:
                    logger.debug(f"获取价格失败: {e}")
                
                # 保存产品信息
                product = {
                    'id': product_id,
                    'name': name or product_id,
                    'price': price,
                    'link': href,
                    'timestamp': datetime.now().isoformat()
                }
                products.append(product)
                logger.debug(f"✓ 提取产品: {product['name'][:50]}")
                
            except Exception as e:
                logger.warning(f"处理链接 {idx} 失败: {e}")
                continue
        
        logger.info(f"✓ 成功提取 {len(products)} 个商品")
        return products
        
    except Exception as e:
        logger.error(f"获取商品失败: {e}")
        import traceback
        traceback.print_exc()
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
    has_changes = False
    
    if changes['added']:
        has_changes = True
        logger.info(f"\n🆕 新增商品 ({len(changes['added'])}个):")
        for p in changes['added'][:10]:
            logger.info(f"  - {p.get('name', 'N/A')}")
            logger.info(f"    价格: {p.get('price', 'N/A')}")
            logger.info(f"    链接: {p.get('link', 'N/A')}")
        if len(changes['added']) > 10:
            logger.info(f"  ... 还有 {len(changes['added']) - 10} 个")
    
    if changes['removed']:
        has_changes = True
        logger.info(f"\n📦 下架商品 ({len(changes['removed'])}个):")
        for p in changes['removed'][:10]:
            logger.info(f"  - {p.get('name', 'N/A')}")
        if len(changes['removed']) > 10:
            logger.info(f"  ... 还有 {len(changes['removed']) - 10} 个")
    
    if changes['price_changes']:
        has_changes = True
        logger.info(f"\n💰 价格变化 ({len(changes['price_changes'])}个):")
        for c in changes['price_changes'][:10]:
            logger.info(f"  - {c['product'].get('name', 'N/A')}")
            logger.info(f"    {c['old_price']} → {c['new_price']}")
        if len(changes['price_changes']) > 10:
            logger.info(f"  ... 还有 {len(changes['price_changes']) - 10} 个")
    
    if not has_changes:
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
            logger.info(f"\n首次运行，创建基准数据...")
            logger.info(f"基准商品数量: {len(current_products)}")
            save_data(current_products)
            
            # 显示前5个商品
            logger.info("\n前 5 个商品:")
            for i, p in enumerate(current_products[:5], 1):
                logger.info(f"\n{i}. {p.get('name')}")
                logger.info(f"   价格: {p.get('price', 'N/A')}")
                logger.info(f"   ID: {p.get('id')}")
        else:
            # 比较变化
            logger.info(f"\n对比基准数据（{len(baseline_products)} 个商品 vs {len(current_products)} 个商品）...")
            changes = compare_products(baseline_products, current_products)
            print_changes(changes)
            
            # 发送邮件通知（如果有变化）
            if EMAIL_ENABLED:
                has_changes = any([
                    changes.get('added'),
                    changes.get('price_changes'),
                    changes.get('removed')
                ])
                if has_changes:
                    logger.info("\n发送邮件通知...")
                    send_change_notification(changes)
            
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
