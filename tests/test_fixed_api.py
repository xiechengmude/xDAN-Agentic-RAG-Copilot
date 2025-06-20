#!/usr/bin/env python3
"""
测试修复后的RAGFlow API
"""

import requests
import json
import time

# API服务配置
RAGFLOW_API_URL = "http://localhost:8000"
DEFAULT_DATASET_ID = "7e8d9e924cde11f0afc90242ac140006"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试API健康检查...")
    try:
        response = requests.get(f"{RAGFLOW_API_URL}/health")
        if response.status_code == 200:
            print("✅ API健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ API健康检查错误: {e}")

def test_list_datasets():
    """测试列出数据集"""
    print("\n🔍 测试列出数据集...")
    try:
        response = requests.get(f"{RAGFLOW_API_URL}/v1/datasets")
        if response.status_code == 200:
            print("✅ 列出数据集成功")
            data = response.json()
            if 'data' in data and data['data']:
                datasets = data['data']
                print(f"📚 找到 {len(datasets)} 个数据集:")
                for dataset in datasets[:3]:  # 只显示前3个
                    print(f"  - ID: {dataset.get('id')}")
                    print(f"    名称: {dataset.get('name')}")
                    print(f"    描述: {dataset.get('description', '无')}")
                    print(f"    文档数: {dataset.get('document_amount', 0)}")
                    print(f"    块数: {dataset.get('chunk_amount', 0)}")
                    print()
            else:
                print("📚 没有找到数据集")
        else:
            print(f"❌ 列出数据集失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 列出数据集错误: {e}")

def test_list_documents():
    """测试列出文档"""
    print(f"\n🔍 测试列出数据集 {DEFAULT_DATASET_ID} 中的文档...")
    try:
        response = requests.get(f"{RAGFLOW_API_URL}/v1/datasets/{DEFAULT_DATASET_ID}/documents")
        if response.status_code == 200:
            print("✅ 列出文档成功")
            data = response.json()
            if 'data' in data and data['data']:
                documents = data['data']
                print(f"📄 找到 {len(documents)} 个文档:")
                for doc in documents[:3]:  # 只显示前3个
                    print(f"  - ID: {doc.get('id')}")
                    print(f"    名称: {doc.get('name')}")
                    print(f"    大小: {doc.get('size', 0)} bytes")
                    print(f"    状态: {doc.get('status')}")
                    print(f"    块数: {doc.get('chunk_amount', 0)}")
                    print()
            else:
                print("📄 没有找到文档")
        else:
            print(f"❌ 列出文档失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 列出文档错误: {e}")

def test_retrieval_with_dataset_id():
    """测试使用数据集ID进行检索"""
    print(f"\n🔍 测试使用数据集ID检索...")
    try:
        payload = {
            "question": "智信",
            "dataset_ids": [DEFAULT_DATASET_ID],
            "page": 1,
            "page_size": 5,
            "similarity_threshold": 0.01,  # 降低阈值
            "top_k": 10
        }
        
        response = requests.post(f"{RAGFLOW_API_URL}/v1/retrieval", json=payload)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ 检索成功")
            data = response.json()
            if 'data' in data and 'chunks' in data['data']:
                chunks = data['data']['chunks']
                print(f"📝 找到 {len(chunks)} 个相关块")
                for i, chunk in enumerate(chunks[:2], 1):
                    print(f"  {i}. 相似度: {chunk.get('similarity', 0):.3f}")
                    print(f"     内容: {chunk.get('content', '')[:100]}...")
                    print()
            else:
                print("📝 没有找到相关内容")
        else:
            print(f"❌ 检索失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 检索错误: {e}")

def test_retrieval_without_ids():
    """测试不提供ID时的默认行为"""
    print(f"\n🔍 测试不提供ID时的默认行为...")
    try:
        payload = {
            "question": "人工智能",
            "page": 1,
            "page_size": 5,
            "similarity_threshold": 0.01
        }
        
        response = requests.post(f"{RAGFLOW_API_URL}/v1/retrieval", json=payload)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 默认检索成功")
            data = response.json()
            if 'data' in data and 'chunks' in data['data']:
                chunks = data['data']['chunks']
                print(f"📝 使用默认数据集找到 {len(chunks)} 个相关块")
            else:
                print("📝 没有找到相关内容")
        else:
            print(f"❌ 默认检索失败: {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 默认检索错误: {e}")

def test_retrieval_with_various_queries():
    """测试各种查询"""
    print(f"\n🔍 测试各种查询...")
    
    queries = [
        "智信原子知识",
        "什么是人工智能",
        "机器学习",
        "深度学习",
        "自然语言处理"
    ]
    
    for query in queries:
        print(f"\n查询: '{query}'")
        try:
            payload = {
                "question": query,
                "dataset_ids": [DEFAULT_DATASET_ID],
                "page": 1,
                "page_size": 3,
                "similarity_threshold": 0.01,
                "highlight": True
            }
            
            response = requests.post(f"{RAGFLOW_API_URL}/v1/retrieval", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'chunks' in data['data']:
                    chunks = data['data']['chunks']
                    print(f"  ✅ 找到 {len(chunks)} 个结果")
                    if chunks:
                        best_chunk = chunks[0]
                        print(f"  📝 最佳匹配 (相似度: {best_chunk.get('similarity', 0):.3f})")
                        print(f"     {best_chunk.get('content', '')[:80]}...")
                else:
                    print("  📝 没有找到结果")
            else:
                print(f"  ❌ 查询失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 查询错误: {e}")
        
        time.sleep(0.5)  # 避免请求过快

def main():
    """主测试函数"""
    print("🚀 开始测试修复后的RAGFlow API")
    print("=" * 60)
    
    # 测试健康检查
    test_health_check()
    
    # 测试数据集列表
    test_list_datasets()
    
    # 测试文档列表
    test_list_documents()
    
    # 测试检索功能
    test_retrieval_with_dataset_id()
    test_retrieval_without_ids()
    test_retrieval_with_various_queries()
    
    print("\n🎉 API测试完成!")

if __name__ == "__main__":
    main()
