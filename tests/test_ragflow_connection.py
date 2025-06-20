#!/usr/bin/env python3
"""
测试RAGFlow连接和基本功能
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.ragflow_client import RAGFlowClient

def test_connection():
    """测试RAGFlow连接"""
    # 从环境变量或使用默认值
    api_url = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
    api_key = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")
    dataset_id = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")
    
    print(f"测试RAGFlow连接...")
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:20]}...")
    print(f"Dataset ID: {dataset_id}")
    print("-" * 60)
    
    # 创建客户端
    client = RAGFlowClient(api_url=api_url, api_key=api_key)
    
    # 测试1: 列出数据集
    print("\n1. 测试列出数据集...")
    try:
        response = client.list_datasets()
        print(f"状态码: {response.get('code')}")
        datasets = response.get('data', [])
        print(f"找到 {len(datasets)} 个数据集")
        for ds in datasets[:3]:  # 只显示前3个
            print(f"  - {ds.get('name')} (ID: {ds.get('id')})")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试2: 检索测试
    print("\n2. 测试检索功能...")
    test_question = "什么是智信平台？"
    try:
        response = client.retrieve_chunks(
            question=test_question,
            dataset_ids=[dataset_id],
            top_k=5,
            similarity_threshold=0.1
        )
        print(f"状态码: {response.get('code')}")
        if response.get('code') == 0:
            chunks = response.get('data', {}).get('chunks', [])
            print(f"找到 {len(chunks)} 个相关文档")
            for i, chunk in enumerate(chunks[:3], 1):
                print(f"\n文档 {i}:")
                print(f"  相似度: {chunk.get('similarity', 0):.3f}")
                content = chunk.get('content', '')[:100]
                print(f"  内容: {content}...")
        else:
            print(f"检索失败: {response.get('message')}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 测试3: 测试具体的数据集
    print("\n3. 查找智信相关数据集...")
    try:
        response = client.list_datasets(page=1, page_size=100)
        if response.get('code') == 0:
            datasets = response.get('data', [])
            zhixin_datasets = [ds for ds in datasets if '智信' in ds.get('name', '') or 'zhixin' in ds.get('name', '').lower()]
            if zhixin_datasets:
                print(f"找到 {len(zhixin_datasets)} 个智信相关数据集:")
                for ds in zhixin_datasets:
                    print(f"  - {ds.get('name')} (ID: {ds.get('id')})")
                    
                # 使用第一个智信数据集进行检索测试
                if zhixin_datasets:
                    zhixin_dataset_id = zhixin_datasets[0].get('id')
                    print(f"\n使用数据集 '{zhixin_datasets[0].get('name')}' 进行检索测试...")
                    response = client.retrieve_chunks(
                        question=test_question,
                        dataset_ids=[zhixin_dataset_id],
                        top_k=5
                    )
                    if response.get('code') == 0:
                        chunks = response.get('data', {}).get('chunks', [])
                        print(f"找到 {len(chunks)} 个相关文档")
            else:
                print("未找到智信相关数据集")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_connection()