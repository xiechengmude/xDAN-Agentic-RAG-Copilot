#!/usr/bin/env python3
"""
直接测试检索功能
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService
from src.clients.llm_client import LLMClient

def test_direct_retrieve():
    """直接测试检索"""
    # 配置
    api_url = "http://150.109.16.195:7080"
    api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
    dataset_id = "7e8d9e924cde11f0afc90242ac140006"
    
    print("初始化客户端...")
    
    # 使用SDK wrapper
    wrapper = RAGFlowSDKWrapper(api_url=api_url, api_key=api_key)
    
    # 测试问题
    test_questions = [
        "什么是智信平台？",
        "智信",
        "平台",
        "授信",
        "借款"
    ]
    
    for question in test_questions:
        print(f"\n测试问题: {question}")
        print("-" * 50)
        
        # 测试检索
        result = wrapper.retrieve_chunks(
            question=question,
            dataset_ids=[dataset_id],
            top_k=5,
            similarity_threshold=0.1
        )
        
        print(f"响应代码: {result.get('code')}")
        
        if result.get('code') == 0:
            chunks = result.get('data', {}).get('chunks', [])
            print(f"找到 {len(chunks)} 个文档")
            
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"\n文档 {i}:")
                print(f"  相似度: {chunk.get('similarity', 0)}")
                print(f"  内容片段: {chunk.get('content', '')[:100]}...")
        else:
            print(f"错误: {result.get('message')}")
    
    # 测试S3服务的搜索步骤
    print("\n" + "=" * 60)
    print("测试S3服务的搜索步骤")
    print("=" * 60)
    
    llm_client = LLMClient(
        base_url="http://51.159.189.105:7032/v1",
        model_name="xDAN-R2-Qwen3-14b-RagRL-step450-0618"
    )
    
    service = EnhancedS3RAGService(wrapper, llm_client)
    
    chunks, success = service.search_step(
        question="什么是智信平台？",
        dataset_ids=[dataset_id],
        top_k=10,
        similarity_threshold=0.1
    )
    
    print(f"搜索成功: {success}")
    print(f"找到chunks: {len(chunks)}")
    
    if chunks:
        formatted_text, doc_mapping = service.format_search_results(chunks)
        print("\n格式化的搜索结果:")
        print(formatted_text[:500])

if __name__ == "__main__":
    test_direct_retrieve()