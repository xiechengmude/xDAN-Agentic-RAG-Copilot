#!/usr/bin/env python3
"""
测试FlashSearch的URL修复和过滤功能
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import FlashSearchEngine


async def test_url_processing():
    """测试URL处理功能"""
    print("🔧 测试FlashSearch URL处理功能")
    print("=" * 50)
    
    try:
        engine = FlashSearchEngine()
        
        # 测试URL修复功能
        print("\n1. 测试URL修复功能:")
        test_urls = [
            "/search?q=test",  # 相对路径
            "example.com",     # 缺少协议
            "https://valid.com/page",  # 正常URL
            "",  # 空URL
        ]
        
        for url in test_urls:
            fixed = engine._fix_relative_url(url)
            print(f"   {url:<25} → {fixed}")
        
        # 测试URL验证功能
        print("\n2. 测试URL验证功能:")
        test_validation_urls = [
            "https://www.example.com/article",  # 有效
            "https://google.com/search?q=test",  # 无效-搜索页
            "https://site.com/page;jsessionid=ABC123",  # 无效-session
            "javascript:void(0)",  # 无效-JS
            "mailto:test@example.com",  # 无效-邮件
            "https://valid.com/page",  # 有效
        ]
        
        for url in test_validation_urls:
            is_valid = engine._is_valid_crawl_url(url)
            status = "✅" if is_valid else "❌"
            print(f"   {status} {url}")
        
        # 测试URL清理功能
        print("\n3. 测试URL清理功能:")
        test_clean_urls = [
            "https://site.com/page;jsessionid=1234567890ABCDEF",
            "https://normal.com/page",
            "https://site.com/page;jsessionid=XYZ?param=value",
        ]
        
        for url in test_clean_urls:
            cleaned = engine._clean_url(url)
            print(f"   {url}")
            print(f"   → {cleaned}")
            print()
        
        # 测试真实搜索中的URL处理
        print("4. 测试真实搜索中的URL处理:")
        question = "Python教程"
        print(f"   问题: {question}")
        
        search_results = await engine.search(question)
        print(f"   搜索结果: {len(search_results)}个")
        
        if search_results:
            print("   前3个URL:")
            for i, result in enumerate(search_results[:3]):
                print(f"   {i+1}. {result['url']}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_url_processing())