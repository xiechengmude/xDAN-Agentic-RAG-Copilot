#!/usr/bin/env python3
"""
URL修复功能测试 - 验证相对路径URL修复和无效URL过滤
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

def test_url_fix_functionality():
    """测试URL修复功能"""
    
    print("测试URL修复和过滤功能")
    print("="*50)
    
    # 创建框架实例
    client = EnhancedLiteLLMClient()
    framework = DeepSearchFramework(client)
    
    # 测试URL列表
    test_urls = [
        # 相对路径URL（需要修复）
        "/search?q=test&tbm=nws",
        "/maps/search?query=location",
        
        # 完整URL（应该保持不变）
        "https://www.example.com/article",
        "http://finance.sina.com.cn/news/",
        
        # 无效的搜索URL（应该被过滤）
        "https://www.google.com/search?q=test&tbm=nws",
        "/search?sca_esv=abc&hl=zh-CN&q=test&udm=2",
        
        # 短域名（需要添加https）
        "example.com/page",
        "finance.sina.com.cn/article/123",
        
        # 空URL
        "",
        None
    ]
    
    print("原始URL -> 修复后URL -> 是否有效")
    print("-" * 60)
    
    for url in test_urls:
        if url is None:
            print(f"None -> None -> False")
            continue
            
        try:
            # 测试URL修复
            fixed_url = framework._fix_relative_url(url)
            
            # 测试URL验证
            is_valid = framework._is_valid_crawl_url(fixed_url)
            
            print(f"{url:<30} -> {fixed_url:<35} -> {is_valid}")
            
        except Exception as e:
            print(f"{url:<30} -> ERROR: {str(e)}")
    
    print("\n" + "="*50)
    print("URL修复功能测试完成!")
    
    # 测试批量URL处理
    print("\n测试批量URL处理:")
    batch_urls = [
        "/search?q=test&tbm=nws",  # 无效
        "https://www.example.com/article",  # 有效
        "/search?invalid=url&udm=2",  # 无效
        "finance.sina.com.cn/news"  # 有效（修复后）
    ]
    
    valid_urls = []
    invalid_urls = []
    
    for url in batch_urls:
        fixed_url = framework._fix_relative_url(url)
        if framework._is_valid_crawl_url(fixed_url):
            valid_urls.append(fixed_url)
        else:
            invalid_urls.append(url)
    
    print(f"有效URL ({len(valid_urls)}个):")
    for url in valid_urls:
        print(f"  ✅ {url}")
    
    print(f"\n无效URL ({len(invalid_urls)}个):")
    for url in invalid_urls:
        print(f"  ❌ {url}")

if __name__ == "__main__":
    test_url_fix_functionality()