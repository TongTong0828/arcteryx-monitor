#!/usr/bin/env python3
"""
使用 requests 测试
"""

import requests
import re
import json

def test_with_requests():
    print("=" * 60)
    print("使用 requests 测试")
    print("=" * 60)
    
    url = "https://outlet.arcteryx.com/ca/zh/c/mens"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"\n请求: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 内容长度: {len(response.text)} 字符")
        
        # 查找 __NEXT_DATA__
        pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
        match = re.search(pattern, response.text, re.DOTALL)
        
        if match:
            print("\n✓ 找到 __NEXT_DATA__")
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # 保存完整数据
            with open('/Users/at/Desktop/ARC/next_data_requests.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("✓ 数据已保存到 next_data_requests.json")
            
            # 分析结构
            print("\n数据结构:")
            if 'props' in data:
                props = data['props']
                if 'pageProps' in props:
                    page_props = props['pageProps']
                    print(f"  pageProps 包含的键: {list(page_props.keys())}")
                    
                    # 查找可能包含产品的字段
                    for key in page_props.keys():
                        value = page_props[key]
                        if isinstance(value, dict):
                            print(f"\n  {key} (字典，包含 {len(value)} 个键):")
                            print(f"    {list(value.keys())}")
                        elif isinstance(value, list) and value:
                            print(f"\n  {key} (列表，包含 {len(value)} 个项目)")
                            if value:
                                print(f"    第一项类型: {type(value[0])}")
            
            return True
        else:
            print("\n✗ 未找到 __NEXT_DATA__")
            
            # 保存HTML用于调试
            with open('/Users/at/Desktop/ARC/page_requests.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML 已保存到 page_requests.html")
            
            return False
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_with_requests()

