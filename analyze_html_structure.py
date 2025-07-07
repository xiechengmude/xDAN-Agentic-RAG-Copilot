#!/usr/bin/env python3
"""
分析HTML结构，找出正确的解析方法
"""

import os
import asyncio
from bs4 import BeautifulSoup
from src.core.env_loader import env_loader

# 清除环境变量并重新加载
for var in ['BRIGHTDATA_API_KEY']:
    if var in os.environ:
        del os.environ[var]
env_loader.reload()

from src.clients.brightdata_client import BrightDataAsyncClient

async def analyze_html_structure():
    """分析HTML结构"""
    
    api_key = os.environ.get('BRIGHTDATA_API_KEY')
    
    async with BrightDataAsyncClient(api_key=api_key) as client:
        # 获取HTML
        data = {
            "zone": client.zone,
            "url": client._build_search_url("Python tutorial", {}),
            "format": "raw"
        }
        
        async with client.session.post(
            client.base_url,
            json=data,
            headers=client.headers
        ) as response:
            html = await response.text()
            
            # 保存HTML用于分析
            with open('google_search_response.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("HTML已保存到 google_search_response.html")
            
            soup = BeautifulSoup(html, 'html.parser')
            
            print("=== HTML结构分析 ===")
            
            # 1. 查找所有h3标签
            h3_tags = soup.find_all('h3')
            print(f"\n1. H3标签数量: {len(h3_tags)}")
            
            if h3_tags:
                print("前5个H3标签:")
                for i, h3 in enumerate(h3_tags[:5]):
                    title = h3.get_text(strip=True)
                    print(f"  {i+1}. {title[:80]}...")
                    
                    # 查找父级容器
                    parent = h3.parent
                    print(f"     父级: {parent.name if parent else 'None'} (class: {parent.get('class', []) if parent else 'None'})")
                    
                    # 查找相关链接
                    link = h3.find('a') or h3.find_parent('a')
                    if link:
                        href = link.get('href', '')
                        print(f"     链接: {href[:60]}...")
            
            # 2. 查找所有外部链接
            print(f"\n2. 链接分析:")
            all_links = soup.find_all('a', href=True)
            external_links = []
            
            for link in all_links:
                href = link.get('href', '')
                if href.startswith('http'):
                    external_links.append(link)
            
            print(f"   总链接数: {len(all_links)}")
            print(f"   外部链接数: {len(external_links)}")
            
            if external_links:
                print("前5个外部链接:")
                for i, link in enumerate(external_links[:5]):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"  {i+1}. {href[:60]}...")
                    print(f"     文本: {text[:50]}...")
            
            # 3. 查找可能的摘要文本
            print(f"\n3. 摘要文本分析:")
            
            # 查找包含较长文本的div
            text_divs = []
            for div in soup.find_all('div'):
                text = div.get_text(strip=True)
                if 50 < len(text) < 500:  # 合理的摘要长度
                    # 过滤掉导航和元数据
                    if not any(skip in text.lower() for skip in [
                        'translate', 'cached', 'similar', 'search', 'google',
                        'sign in', 'settings', 'privacy', 'terms'
                    ]):
                        text_divs.append((div, text))
            
            print(f"   找到 {len(text_divs)} 个可能的摘要div")
            
            if text_divs:
                print("前3个摘要示例:")
                for i, (div, text) in enumerate(text_divs[:3]):
                    print(f"  {i+1}. {text[:100]}...")
                    print(f"     div class: {div.get('class', [])}")
            
            # 4. 尝试找到结果容器的模式
            print(f"\n4. 结果容器模式分析:")
            
            # 查找同时包含h3和外部链接的容器
            result_containers = []
            
            for div in soup.find_all('div'):
                h3 = div.find('h3')
                external_link = None
                
                for link in div.find_all('a', href=True):
                    if link.get('href', '').startswith('http'):
                        external_link = link
                        break
                
                if h3 and external_link:
                    result_containers.append({
                        'div': div,
                        'h3': h3,
                        'link': external_link,
                        'classes': div.get('class', [])
                    })
            
            print(f"   找到 {len(result_containers)} 个结果容器")
            
            if result_containers:
                print("容器class统计:")
                class_counts = {}
                for container in result_containers:
                    classes = container['classes']
                    for cls in classes:
                        class_counts[cls] = class_counts.get(cls, 0) + 1
                
                for cls, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   .{cls}: {count} 次")
                
                print(f"\n前3个结果容器示例:")
                for i, container in enumerate(result_containers[:3]):
                    h3_text = container['h3'].get_text(strip=True)
                    link_href = container['link'].get('href', '')
                    div_classes = container['classes']
                    
                    print(f"  {i+1}. 标题: {h3_text[:50]}...")
                    print(f"     URL: {link_href[:60]}...")
                    print(f"     容器class: {div_classes}")

if __name__ == "__main__":
    asyncio.run(analyze_html_structure())