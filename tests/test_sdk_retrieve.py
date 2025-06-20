#!/usr/bin/env python3
"""
测试RAGFlow SDK的retrieve功能
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ragflow_sdk import RAGFlow

def test_sdk_retrieve():
    """测试SDK的retrieve方法"""
    # 配置
    api_key = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")
    base_url = "http://150.109.16.195:9380"  # SDK需要9380端口
    dataset_id = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")
    
    print(f"初始化RAGFlow SDK...")
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:20]}...")
    print(f"Dataset ID: {dataset_id}")
    print("-" * 60)
    
    try:
        # 初始化SDK
        rag_object = RAGFlow(api_key=api_key, base_url=base_url)
        
        # 测试1: 列出数据集
        print("\n1. 列出数据集...")
        datasets = rag_object.list_datasets()
        print(f"找到 {len(datasets)} 个数据集:")
        for ds in datasets[:3]:
            print(f"  - {ds.name} (ID: {ds.id})")
        
        # 测试2: 使用retrieve方法检索
        print("\n2. 测试retrieve方法...")
        question = "什么是智信平台？"
        print(f"问题: {question}")
        
        # 根据文档，retrieve方法需要question参数
        chunks_found = 0
        for chunk in rag_object.retrieve(
            question=question,
            dataset_ids=[dataset_id],
            top_k=5,
            similarity_threshold=0.1
        ):
            chunks_found += 1
            if chunks_found <= 3:  # 只显示前3个
                print(f"\nChunk {chunks_found}:")
                print(f"  ID: {chunk.id}")
                print(f"  相似度: {chunk.similarity}")
                content = chunk.content[:200] if hasattr(chunk, 'content') else str(chunk)[:200]
                print(f"  内容: {content}...")
        
        print(f"\n总共找到 {chunks_found} 个相关chunks")
        
        # 测试3: 获取特定数据集并检索
        print("\n3. 通过数据集对象检索...")
        target_dataset = None
        for ds in datasets:
            if ds.id == dataset_id:
                target_dataset = ds
                break
        
        if target_dataset:
            print(f"使用数据集: {target_dataset.name}")
            # 尝试列出文档
            try:
                docs = target_dataset.list_documents()
                print(f"数据集中有 {len(docs)} 个文档")
                if docs:
                    print(f"第一个文档: {docs[0].name}")
            except Exception as e:
                print(f"列出文档失败: {e}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sdk_retrieve()