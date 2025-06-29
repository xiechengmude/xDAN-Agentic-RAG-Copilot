#!/usr/bin/env python3
"""
验证多轮搜索修复效果
"""

import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.deepsearch_framework import DeepSearchFramework

# 测试extract_deepsearch_decision修复
def test_extract_fix():
    framework = DeepSearchFramework(None, {})
    
    # 测试v1.2格式的响应（使用<next_query>）
    test_response_v12 = """
<evaluation>
候选网页评估完成。
</evaluation>

<important_urls>[1, 3, 5]</important_urls>

<search_complete>False</search_complete>

<next_query>{"query": "Apple Q4 2024 earnings revenue profit iPhone sales official report"}</next_query>
"""
    
    # 测试旧格式的响应（使用<query>）
    test_response_old = """
<thinking>
需要更精确的搜索。
</thinking>

<query>{"query": "苹果公司2024年第四季度财报官方报告"}</query>

<search_complete>False</search_complete>

<important_urls>[1, 2]</important_urls>
"""
    
    print("测试extract_deepsearch_decision修复...")
    print("="*60)
    
    # 测试v1.2格式
    print("\n1. 测试v1.2格式（<next_query>标签）:")
    decision_v12 = framework.extract_deepsearch_decision(test_response_v12)
    print(f"   search_complete: {decision_v12['search_complete']}")
    print(f"   next_query: {decision_v12['next_query']}")
    print(f"   important_urls: {decision_v12['important_urls']}")
    
    # 测试旧格式
    print("\n2. 测试旧格式（<query>标签）:")
    decision_old = framework.extract_deepsearch_decision(test_response_old)
    print(f"   search_complete: {decision_old['search_complete']}")
    print(f"   next_query: {decision_old['next_query']}")
    print(f"   important_urls: {decision_old['important_urls']}")
    
    # 验证修复是否成功
    print("\n" + "="*60)
    if decision_v12['next_query'] and decision_old['next_query']:
        print("✅ 修复成功！两种格式的next_query都能正确提取")
    else:
        print("❌ 修复失败！")
        if not decision_v12['next_query']:
            print("   - v1.2格式的next_query提取失败")
        if not decision_old['next_query']:
            print("   - 旧格式的next_query提取失败")

if __name__ == "__main__":
    test_extract_fix()