#!/usr/bin/env python3
"""
测试HTTP API回退机制
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper

def test_http_fallback():
    """测试HTTP API回退"""
    # 配置
    api_url = "http://150.109.16.195:7080"
    api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
    dataset_id = "7e8d9e924cde11f0afc90242ac140006"
    
    print("初始化SDK Wrapper...")
    wrapper = RAGFlowSDKWrapper(api_url=api_url, api_key=api_key)
    
    # 故意让SDK失败，测试HTTP回退
    print("\n测试retrieve_chunks方法...")
    result = wrapper.retrieve_chunks(
        question="什么是智信平台？",
        dataset_ids=[dataset_id],
        top_k=3,
        similarity_threshold=0.1
    )
    
    print(f"\n响应代码: {result.get('code')}")
    
    if result.get('code') == 0:
        chunks = result.get('data', {}).get('chunks', [])
        print(f"找到 {len(chunks)} 个文档")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\n文档 {i}:")
            print(f"  相似度: {chunk.get('similarity', 'N/A')}")
            print(f"  内容片段: {chunk.get('content', '')[:100]}...")
    else:
        print(f"错误: {result.get('message')}")

if __name__ == "__main__":
    test_http_fallback()