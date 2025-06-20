#!/usr/bin/env python3
"""
测试Chunk对象的属性
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ragflow_sdk import RAGFlow

def test_chunk_attributes():
    """测试Chunk对象的属性"""
    # 配置
    api_url = "http://150.109.16.195:7080"
    api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
    dataset_id = "7e8d9e924cde11f0afc90242ac140006"
    
    print("初始化SDK...")
    rag_flow = RAGFlow(api_key=api_key, base_url=api_url)
    
    print("\n测试retrieve方法...")
    chunks = list(rag_flow.retrieve(
        question="什么是智信平台？",
        dataset_ids=[dataset_id],
        top_k=2,
        similarity_threshold=0.1
    ))
    
    if chunks:
        print(f"\n找到 {len(chunks)} 个chunks")
        chunk = chunks[0]
        
        print(f"\nChunk对象类型: {type(chunk)}")
        print(f"Chunk对象属性: {dir(chunk)}")
        
        # 打印所有属性
        print("\n属性值:")
        for attr in dir(chunk):
            if not attr.startswith('_'):
                try:
                    value = getattr(chunk, attr)
                    if not callable(value):
                        print(f"  {attr}: {value}")
                except Exception as e:
                    print(f"  {attr}: <错误: {e}>")
    else:
        print("没有找到chunks")

if __name__ == "__main__":
    test_chunk_attributes()