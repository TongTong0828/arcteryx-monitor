#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arc'teryx Outlet 商品监控脚本 - Selenium 版本
使用浏览器自动化来处理 JavaScript 渲染的页面
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import os
from datetime import datetime
from typing import Dict, List
import time
import hashlib


class ArcOutletMonitorSelenium:
    def __init__(self, data_dir="data", headless=True):
        self.url = "https://outlet.arcteryx.com/ca/zh/c/mens"
        self.data_dir = data_dir
        self.products_file = os.path.join(data_dir, "products.json")
        self.history_file = os.path.join(data_dir, "history.json")
        self.changes_file = os.path.join(data_dir, "changes.json")
        self.headless = headless
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
    
    def create_driver(self):
        """创建 Chrome WebDriver"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        # 常用选项
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # 禁用图片加载以加快速度（可选）
        # prefs = {"profile.managed_default_content_settings.images": 2}
        # options.add_experimental_option("prefs", prefs)
        
        # 增加超时设置
        options.page_load_strategy = 'normal'
        
        try:
            print("正在启动 Chrome 浏览器...")
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)  # 60秒页面加载超时
            driver.set_script_timeout(30)  # 30秒脚本超时
            print("✓ 浏览器启动成功")
            return driver
        except Exception as e:
            print(f"❌ 无法创建 Chrome WebDriver: {e}")
            print("\n请确保：")
            print("1. 已安装 Google Chrome 浏览器")
            print("2. Chrome 版本与 ChromeDriver 兼容")
            print("3. 查看 SETUP_CHROME.md 获取详细指南")
            return None
    
    def fetch_and_parse_products(self) -> Dict[str, dict]:
        """使用 Selenium 获取并解析商品"""
        driver = self.create_driver()
        if not driver:
            return {}
        
        products = {}
        
        try:
            print(f"正在访问: {self.url}")
            try:
                driver.get(self.url)
            except Exception as e:
                print(f"⚠️  页面加载遇到问题: {e}")
                print("尝试继续...")
            
            # 等待页面加载
            print("等待页面加载...")
            time.sleep(5)  # 给页面更多时间来渲染
            
            # 尝试等待商品容器加载
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                print("✓ 页面已加载")
            except TimeoutException:
                print("⚠️  页面加载超时，尝试继续...")
            
            # 再等待一会儿让 JavaScript 执行
            time.sleep(3)
            
            # 滚动页面以加载更多商品（如果有懒加载）
            self.scroll_page(driver)
            
            # 多种商品选择器
            selectors = [
                "div[id*='mens-']",  # 商品容器以 mens- 开头的 id
                ".qa--grid-product-tile",
                "[data-testid='product-tile']",
                ".product-tile",
                "article",
            ]
            
            product_elements = []
            for selector in selectors:
                try:
                    product_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if product_elements:
                        print(f"✓ 使用选择器找到 {len(product_elements)} 个元素: {selector}")
                        break
                except:
                    continue
            
            if not product_elements:
                print("⚠️  未找到商品元素")
                # 保存页面源代码用于调试
                with open(os.path.join(self.data_dir, "page_source.html"), "w", encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"已保存页面源代码到 {self.data_dir}/page_source.html")
                return products
            
            print(f"正在解析 {len(product_elements)} 个商品...")
            
            for idx, element in enumerate(product_elements, 1):
                try:
                    product_data = self.parse_product_element(element, idx)
                    if product_data and product_data.get('name') != "未知商品":
                        product_id = product_data['id']
                        products[product_id] = product_data
                        if idx <= 3:  # 打印前3个用于调试
                            print(f"  {idx}. {product_data['name']} - {product_data['price']}")
                except Exception as e:
                    print(f"⚠️  解析商品 {idx} 时出错: {e}")
                    continue
            
            print(f"✓ 成功解析 {len(products)} 个商品")
            
        except Exception as e:
            print(f"❌ 发生错误: {e}")
        finally:
            driver.quit()
        
        return products
    
    def scroll_page(self, driver):
        """滚动页面以触发懒加载"""
        try:
            # 滚动到页面底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            # 滚动到中间
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            # 再次滚动到底部
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        except:
            pass
    
    def parse_product_element(self, element, idx) -> dict:
        """解析单个商品元素"""
        # 从 ID 属性获取产品 ID
        element_id = element.get_attribute('id') or f"product_{idx}"
        product_id = element_id
        
        # 商品名称
        name = "未知商品"
        name_selectors = [
            ".product-tile-name",  # 主要选择器
            "[class*='product-tile-name']",
            "[data-component='body3']",
            ".product-name",
            "h2",
            "h3",
        ]
        
        for selector in name_selectors:
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, selector)
                name_text = name_elem.text.strip()
                if name_text and len(name_text) > 3 and not name_text.startswith('CA'):
                    name = name_text
                    break
            except:
                continue
        
        # 价格 - 原价和折扣价
        price = "价格未知"
        price_selectors = [
            ".qa--product-tile__prices",  # 价格容器
            ".qa--product-tile__minRange-price",  # 折扣价
            "[class*='price']",
        ]
        
        for selector in price_selectors:
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and 'CA$' in price_text:
                    price = price_text.replace('\n', ' ')
                    break
            except:
                continue
        
        # 链接
        link = ""
        try:
            link_elem = element.find_element(By.CSS_SELECTOR, "a")
            link = link_elem.get_attribute('href') or ""
        except:
            pass
        
        # 图片
        image_url = ""
        try:
            img_elem = element.find_element(By.CSS_SELECTOR, "img")
            image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ""
        except:
            pass
        
        return {
            'id': f"product_{idx}_{product_id}",
            'name': name,
            'price': price,
            'link': link,
            'image': image_url,
            'last_seen': datetime.now().isoformat()
        }
    
    def load_previous_data(self) -> Dict[str, dict]:
        """加载之前保存的数据"""
        if os.path.exists(self.products_file):
            try:
                with open(self.products_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载历史数据失败: {e}")
                return {}
        return {}
    
    def save_current_data(self, products: Dict[str, dict]):
        """保存当前数据"""
        try:
            with open(self.products_file, 'w', encoding='utf-8') as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
            print(f"✓ 已保存商品数据")
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
    
    def compare_and_detect_changes(self, old_products: Dict, new_products: Dict) -> Dict:
        """比较并检测变化"""
        changes = {
            'timestamp': datetime.now().isoformat(),
            'new_products': [],
            'removed_products': [],
            'price_changes': [],
            'statistics': {
                'total_products': len(new_products),
                'new_count': 0,
                'removed_count': 0,
                'price_changed_count': 0
            }
        }
        
        # 按名称建立映射以便更好地匹配
        old_by_name = {p['name']: p for p in old_products.values()}
        new_by_name = {p['name']: p for p in new_products.values()}
        
        old_names = set(old_by_name.keys())
        new_names = set(new_by_name.keys())
        
        # 检测新商品
        for name in new_names - old_names:
            if name != "未知商品":
                product = new_by_name[name]
                changes['new_products'].append(product)
                changes['statistics']['new_count'] += 1
                print(f"🆕 新商品: {product['name']} - {product['price']}")
        
        # 检测下架商品
        for name in old_names - new_names:
            if name != "未知商品":
                product = old_by_name[name]
                changes['removed_products'].append(product)
                changes['statistics']['removed_count'] += 1
                print(f"📤 已下架: {product['name']}")
        
        # 检测价格变化
        for name in old_names & new_names:
            if name == "未知商品":
                continue
            old_product = old_by_name[name]
            new_product = new_by_name[name]
            
            if old_product['price'] != new_product['price']:
                change_info = {
                    'name': name,
                    'old_price': old_product['price'],
                    'new_price': new_product['price'],
                    'link': new_product['link']
                }
                changes['price_changes'].append(change_info)
                changes['statistics']['price_changed_count'] += 1
                print(f"💰 价格变化: {name}")
                print(f"   {old_product['price']} → {new_product['price']}")
        
        return changes
    
    def save_changes(self, changes: Dict):
        """保存变化记录"""
        history = []
        
        # 加载历史记录
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        # 添加新记录
        history.append(changes)
        
        # 只保留最近 100 条记录
        history = history[-100:]
        
        # 保存历史
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            # 同时保存最新变化到单独文件
            with open(self.changes_file, 'w', encoding='utf-8') as f:
                json.dump(changes, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 已保存变化记录")
        except Exception as e:
            print(f"❌ 保存变化记录失败: {e}")
    
    def generate_report(self, changes: Dict) -> str:
        """生成监控报告"""
        report = []
        report.append("=" * 60)
        report.append("Arc'teryx Outlet 商品监控报告")
        report.append("=" * 60)
        report.append(f"监控时间: {changes['timestamp']}")
        report.append(f"监控网址: {self.url}")
        report.append("")
        
        stats = changes['statistics']
        report.append("📊 统计信息:")
        report.append(f"  总商品数: {stats['total_products']}")
        report.append(f"  新商品: {stats['new_count']}")
        report.append(f"  已下架: {stats['removed_count']}")
        report.append(f"  价格变化: {stats['price_changed_count']}")
        report.append("")
        
        # 新商品详情
        if changes['new_products']:
            report.append("🆕 新增商品:")
            for product in changes['new_products'][:10]:  # 最多显示10个
                report.append(f"  • {product['name']}")
                report.append(f"    价格: {product['price']}")
                if product['link']:
                    report.append(f"    链接: {product['link']}")
            if len(changes['new_products']) > 10:
                report.append(f"  ... 还有 {len(changes['new_products']) - 10} 个新商品")
            report.append("")
        
        # 价格变化详情
        if changes['price_changes']:
            report.append("💰 价格变化:")
            for change in changes['price_changes'][:10]:
                report.append(f"  • {change['name']}")
                report.append(f"    {change['old_price']} → {change['new_price']}")
                if change['link']:
                    report.append(f"    链接: {change['link']}")
            if len(changes['price_changes']) > 10:
                report.append(f"  ... 还有 {len(changes['price_changes']) - 10} 个价格变化")
            report.append("")
        
        # 下架商品
        if changes['removed_products']:
            report.append("📤 已下架商品:")
            for product in changes['removed_products'][:10]:
                report.append(f"  • {product['name']} ({product['price']})")
            if len(changes['removed_products']) > 10:
                report.append(f"  ... 还有 {len(changes['removed_products']) - 10} 个下架商品")
            report.append("")
        
        if not any([changes['new_products'], changes['price_changes'], changes['removed_products']]):
            report.append("✅ 暂无变化")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def run_once(self):
        """运行一次监控"""
        print("\n" + "=" * 60)
        print(f"开始监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 获取商品
        current_products = self.fetch_and_parse_products()
        
        if not current_products:
            print("⚠️  未能解析到任何商品")
            return
        
        # 加载历史数据
        previous_products = self.load_previous_data()
        
        # 检测变化
        if previous_products:
            changes = self.compare_and_detect_changes(previous_products, current_products)
            
            # 保存变化记录
            self.save_changes(changes)
            
            # 生成并显示报告
            report = self.generate_report(changes)
            print("\n" + report)
            
            # 保存报告到文件
            report_file = os.path.join(self.data_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 报告已保存到: {report_file}")
        else:
            print("ℹ️  这是首次运行，已保存初始数据")
        
        # 保存当前数据
        self.save_current_data(current_products)
        
        print("\n✓ 监控完成")
    
    def run_continuous(self, interval_minutes=30):
        """持续监控"""
        print(f"开始持续监控，每 {interval_minutes} 分钟检查一次")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                self.run_once()
                print(f"\n等待 {interval_minutes} 分钟后进行下次检查...")
                time.sleep(interval_minutes * 60)
        except KeyboardInterrupt:
            print("\n\n监控已停止")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Arc\'teryx Outlet 商品监控工具 (Selenium 版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python monitor_selenium.py                    # 运行一次监控
  python monitor_selenium.py --continuous       # 持续监控（默认30分钟检查一次）
  python monitor_selenium.py --continuous -i 60 # 持续监控（每60分钟检查一次）
  python monitor_selenium.py --show-browser     # 显示浏览器窗口（调试用）
        """
    )
    
    parser.add_argument(
        '--continuous', '-c',
        action='store_true',
        help='持续监控模式'
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=30,
        help='持续监控的时间间隔（分钟），默认30分钟'
    )
    
    parser.add_argument(
        '--data-dir', '-d',
        type=str,
        default='data',
        help='数据存储目录，默认为 data/'
    )
    
    parser.add_argument(
        '--show-browser',
        action='store_true',
        help='显示浏览器窗口（调试模式）'
    )
    
    args = parser.parse_args()
    
    monitor = ArcOutletMonitorSelenium(
        data_dir=args.data_dir,
        headless=not args.show_browser
    )
    
    if args.continuous:
        monitor.run_continuous(interval_minutes=args.interval)
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()

