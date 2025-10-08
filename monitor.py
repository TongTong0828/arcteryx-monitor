#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arc'teryx Outlet 商品监控脚本
监控 https://outlet.arcteryx.com/ca/zh/c/mens 的商品更新
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from typing import Dict, List, Set
import time
import hashlib


class ArcOutletMonitor:
    def __init__(self, data_dir="data"):
        self.url = "https://outlet.arcteryx.com/ca/zh/c/mens"
        self.data_dir = data_dir
        self.products_file = os.path.join(data_dir, "products.json")
        self.history_file = os.path.join(data_dir, "history.json")
        self.changes_file = os.path.join(data_dir, "changes.json")
        
        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        
        # 请求头，模拟浏览器
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def fetch_page_content(self) -> str:
        """获取网页内容"""
        try:
            print(f"正在访问: {self.url}")
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"❌ 获取网页失败: {e}")
            return None
    
    def parse_products(self, html_content: str) -> Dict[str, dict]:
        """解析商品信息"""
        soup = BeautifulSoup(html_content, 'html.parser')
        products = {}
        
        # 尝试多种可能的选择器来定位商品
        # 根据实际网页结构调整选择器
        product_selectors = [
            '.product-tile',
            '.product-item',
            '[data-product]',
            '.grid-tile',
            'article.product',
            'div[class*="product"]'
        ]
        
        product_elements = []
        for selector in product_selectors:
            product_elements = soup.select(selector)
            if product_elements:
                print(f"✓ 使用选择器找到商品: {selector}")
                break
        
        if not product_elements:
            print("⚠️  未找到商品元素，可能需要调整选择器或网站需要 JavaScript 渲染")
            # 保存 HTML 用于调试
            with open(os.path.join(self.data_dir, "page_content.html"), "w", encoding='utf-8') as f:
                f.write(html_content)
            print(f"已保存网页内容到 {self.data_dir}/page_content.html 用于调试")
        
        for element in product_elements:
            try:
                # 提取商品信息（根据实际网页结构调整）
                product_id = (
                    element.get('data-product-id') or 
                    element.get('data-itemid') or
                    element.get('id') or
                    hashlib.md5(str(element).encode()).hexdigest()[:12]
                )
                
                # 商品名称
                name_element = (
                    element.select_one('.product-name') or
                    element.select_one('.product-title') or
                    element.select_one('h2') or
                    element.select_one('h3') or
                    element.select_one('[class*="name"]') or
                    element.select_one('[class*="title"]')
                )
                name = name_element.get_text(strip=True) if name_element else "未知商品"
                
                # 价格
                price_element = (
                    element.select_one('.price') or
                    element.select_one('[class*="price"]') or
                    element.select_one('.cost')
                )
                price = price_element.get_text(strip=True) if price_element else "价格未知"
                
                # 商品链接
                link_element = element.select_one('a')
                link = link_element.get('href', '') if link_element else ""
                if link and not link.startswith('http'):
                    link = f"https://outlet.arcteryx.com{link}"
                
                # 商品图片
                img_element = element.select_one('img')
                image_url = img_element.get('src', '') or img_element.get('data-src', '') if img_element else ""
                
                products[product_id] = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'link': link,
                    'image': image_url,
                    'last_seen': datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"⚠️  解析商品时出错: {e}")
                continue
        
        print(f"✓ 成功解析 {len(products)} 个商品")
        return products
    
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
            print(f"✓ 已保存商品数据到 {self.products_file}")
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
        
        old_ids = set(old_products.keys())
        new_ids = set(new_products.keys())
        
        # 检测新商品
        for product_id in new_ids - old_ids:
            product = new_products[product_id]
            changes['new_products'].append(product)
            changes['statistics']['new_count'] += 1
            print(f"🆕 新商品: {product['name']} - {product['price']}")
        
        # 检测下架商品
        for product_id in old_ids - new_ids:
            product = old_products[product_id]
            changes['removed_products'].append(product)
            changes['statistics']['removed_count'] += 1
            print(f"📤 已下架: {product['name']}")
        
        # 检测价格变化
        for product_id in old_ids & new_ids:
            old_product = old_products[product_id]
            new_product = new_products[product_id]
            
            if old_product['price'] != new_product['price']:
                change_info = {
                    'id': product_id,
                    'name': new_product['name'],
                    'old_price': old_product['price'],
                    'new_price': new_product['price'],
                    'link': new_product['link']
                }
                changes['price_changes'].append(change_info)
                changes['statistics']['price_changed_count'] += 1
                print(f"💰 价格变化: {new_product['name']}")
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
            for product in changes['new_products']:
                report.append(f"  • {product['name']}")
                report.append(f"    价格: {product['price']}")
                if product['link']:
                    report.append(f"    链接: {product['link']}")
            report.append("")
        
        # 价格变化详情
        if changes['price_changes']:
            report.append("💰 价格变化:")
            for change in changes['price_changes']:
                report.append(f"  • {change['name']}")
                report.append(f"    {change['old_price']} → {change['new_price']}")
                if change['link']:
                    report.append(f"    链接: {change['link']}")
            report.append("")
        
        # 下架商品
        if changes['removed_products']:
            report.append("📤 已下架商品:")
            for product in changes['removed_products']:
                report.append(f"  • {product['name']} ({product['price']})")
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
        
        # 获取网页内容
        html_content = self.fetch_page_content()
        if not html_content:
            print("❌ 无法获取网页内容，本次监控结束")
            return
        
        # 解析商品
        current_products = self.parse_products(html_content)
        
        if not current_products:
            print("⚠️  未能解析到任何商品，可能需要手动调整解析器")
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
        description='Arc\'teryx Outlet 商品监控工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python monitor.py                    # 运行一次监控
  python monitor.py --continuous       # 持续监控（默认30分钟检查一次）
  python monitor.py --continuous -i 60 # 持续监控（每60分钟检查一次）
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
    
    args = parser.parse_args()
    
    monitor = ArcOutletMonitor(data_dir=args.data_dir)
    
    if args.continuous:
        monitor.run_continuous(interval_minutes=args.interval)
    else:
        monitor.run_once()


if __name__ == "__main__":
    main()

