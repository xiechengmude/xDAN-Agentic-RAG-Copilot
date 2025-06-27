#!/usr/bin/env python3
"""
DeepSearch完整演示 - 使用真实搜索结果和爬取数据
"""

import asyncio
import json
from datetime import datetime

from src.clients.firecrawl_client import FireCrawlAsyncClient
from src.core.config_loader import get_config


async def demo_complete_deepsearch():
    """完整的DeepSearch流程演示"""
    config = get_config()
    
    print("\n" + "="*80)
    print("🚀 DeepSearch 完整流程演示 (使用真实数据)")
    print("="*80)
    
    # 使用之前成功获取的真实搜索结果
    print("\n1️⃣ 搜索阶段 - BrightData SERP 真实结果")
    print("-"*80)
    
    # 加载之前保存的真实搜索结果
    with open('search_result_artificial intellige.json', 'r', encoding='utf-8') as f:
        search_data = json.load(f)
    
    search_results = search_data['results']
    print(f"✅ 从BrightData获得 {len(search_results)} 个真实搜索结果")
    print(f"查询: {search_data['query']}")
    print(f"耗时: {search_data['elapsed']:.2f}秒")
    
    print("\n搜索结果候选列表 (前10个):")
    valid_results = [r for r in search_results if r.get('url', '').startswith('http')]
    
    for i, item in enumerate(valid_results[:10], 1):
        print(f"\n{i}. {item.get('title', 'No title')}")
        print(f"   URL: {item['url']}")
        print(f"   站点: {item.get('site', 'Unknown')}")
        if item.get('snippet'):
            print(f"   摘要: {item['snippet'][:100]}...")
    
    # 2. 选择阶段
    print("\n\n2️⃣ 选择阶段 - Agent智能筛选")
    print("-"*80)
    
    # 选择最相关的URL进行爬取
    urls_to_crawl = []
    
    # 优先选择包含特定关键词的结果
    priority_keywords = ['AI 2024', 'artificial intelligence', 'trends', 'developments', 'State of AI']
    
    for item in valid_results:
        title = item.get('title', '').lower()
        url = item.get('url', '')
        
        # 跳过YouTube链接
        if 'youtube.com' in url:
            continue
            
        # 检查是否包含关键词
        if any(keyword.lower() in title for keyword in priority_keywords):
            urls_to_crawl.append({
                'url': url,
                'title': item.get('title', 'No title'),
                'snippet': item.get('snippet', '')
            })
            
        if len(urls_to_crawl) >= 3:
            break
    
    print(f"✅ 选择了 {len(urls_to_crawl)} 个高相关性页面进行深度爬取:")
    for i, item in enumerate(urls_to_crawl, 1):
        print(f"{i}. {item['title']}")
    
    # 3. 爬取阶段
    print("\n\n3️⃣ 爬取阶段 - FireCrawl深度内容提取")
    print("-"*80)
    
    firecrawl = FireCrawlAsyncClient(
        api_key=config.get('firecrawl.api_key')
    )
    
    crawled_content = []
    
    async with firecrawl:
        for i, item in enumerate(urls_to_crawl, 1):
            url = item['url']
            print(f"\n爬取 [{i}/{len(urls_to_crawl)}]: {item['title'][:60]}...")
            print(f"URL: {url}")
            
            try:
                # 使用FireCrawl爬取
                result = await firecrawl.scrape_url(
                    url,
                    formats=['markdown'],
                    options={
                        'only_main_content': True,
                        'timeout': 30000
                    }
                )
                
                if result['success']:
                    data = result['data']
                    content = data.get('markdown', '') or data.get('content', '')
                    
                    if content:
                        print(f"✅ 成功! 获取 {len(content):,} 字符")
                        
                        # 内容预览
                        preview = content[:200].replace('\n', ' ')
                        print(f"预览: {preview}...")
                        
                        crawled_content.append({
                            'url': url,
                            'title': data.get('title') or item['title'],
                            'content': content,
                            'original_search_result': item
                        })
                    else:
                        print("⚠️  没有获取到内容")
                else:
                    print(f"❌ 爬取失败: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ 错误: {str(e)}")
                
            # 避免请求过快
            await asyncio.sleep(1)
    
    # 4. 合成阶段
    print("\n\n4️⃣ 合成阶段 - 信息整合")
    print("-"*80)
    
    if crawled_content:
        print(f"✅ 成功爬取 {len(crawled_content)} 个页面")
        
        total_chars = sum(len(item['content']) for item in crawled_content)
        print(f"\n📊 数据统计:")
        print(f"  - 总字符数: {total_chars:,}")
        print(f"  - 平均每页: {total_chars//len(crawled_content):,} 字符")
        print(f"  - 信息源数: {len(crawled_content)}")
        
        print("\n📝 获取的信息源:")
        for item in crawled_content:
            print(f"\n  标题: {item['title']}")
            print(f"  URL: {item['url']}")
            print(f"  内容长度: {len(item['content']):,} 字符")
            
            # 提取关键信息
            content_lower = item['content'].lower()
            if '2024' in content_lower:
                # 查找2024相关的句子
                sentences = item['content'].split('.')
                relevant_sentences = [s for s in sentences if '2024' in s.lower()][:2]
                if relevant_sentences:
                    print("  关键信息:")
                    for sent in relevant_sentences:
                        print(f"    - {sent.strip()[:150]}...")
    else:
        print("❌ 没有成功爬取任何页面")
    
    # 保存完整结果
    final_result = {
        'timestamp': datetime.now().isoformat(),
        'search_query': search_data['query'],
        'search_results_count': len(search_results),
        'valid_results_count': len(valid_results),
        'crawled_pages': len(crawled_content),
        'total_content_chars': sum(len(item['content']) for item in crawled_content) if crawled_content else 0,
        'sources': [
            {
                'title': item['title'],
                'url': item['url'],
                'content_length': len(item['content'])
            }
            for item in crawled_content
        ]
    }
    
    with open('deepsearch_complete_result.json', 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)
    
    print("\n\n" + "="*80)
    print("✅ DeepSearch演示完成!")
    print(f"搜索结果: {len(valid_results)} 个真实网页")
    print(f"爬取内容: {len(crawled_content)} 个页面, 共 {sum(len(item['content']) for item in crawled_content):,} 字符")
    print("结果已保存到: deepsearch_complete_result.json")
    print("="*80)


if __name__ == "__main__":
    print("\n🔍 DeepSearch 完整流程演示")
    print("展示如何将BrightData搜索结果通过FireCrawl深度爬取")
    print("实现 Search → Select → Crawl → Synthesize 的完整链路")
    
    asyncio.run(demo_complete_deepsearch())