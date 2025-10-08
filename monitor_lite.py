#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量级监控 - 使用简单的 HTTP 请求
适用于低内存环境
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time

class LiteMonitor:
    def __init__(self):
        self.url = "https://outlet.arcteryx.com/ca/zh/c/mens"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        })
    
    def check_page_changes(self):
        """检查页面变化（简化版）"""
        try:
            print(f"检查网页: {self.url}")
            response = self.session.get(self.url, timeout=30)
            
            # 简单的变化检测
            content_hash = hash(response.text)
            
            # 保存当前哈希
            hash_file = "data/page_hash.txt"
            os.makedirs("data", exist_ok=True)
            
            previous_hash = None
            if os.path.exists(hash_file):
                with open(hash_file, 'r') as f:
                    previous_hash = f.read().strip()
            
            with open(hash_file, 'w') as f:
                f.write(str(content_hash))
            
            if previous_hash and str(content_hash) != previous_hash:
                print("🔔 页面内容发生变化！")
                # 保存页面用于分析
                with open("data/latest_page.html", "w", encoding='utf-8') as f:
                    f.write(response.text)
                return True
            else:
                print("✓ 页面无变化")
                return False
                
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            return False

def main():
    monitor = LiteMonitor()
    monitor.check_page_changes()

if __name__ == "__main__":
    main()
