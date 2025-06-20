#!/usr/bin/env python3
"""
针对特定知识库内容的RAG测试
"""

import requests
import json

RAG_SERVICE_URL = "http://localhost:8001"

def test_with_different_questions():
    """测试不同类型的问题"""
    
    # 更通用的问题，可能在知识库中找到相关内容
    test_questions = [
        "360",
        "安全",
        "产品",
        "技术",
        "服务",
        "公司",
        "业务",
        "用户"
    ]
    
    print("🔍 测试不同关键词的检索效果...")
    
    for question in test_questions:
        print(f"\n测试关键词: '{question}'")
        try:
            payload = {
                "question": question,
                "top_k": 3,
                "similarity_threshold": 0.05,  # 降低阈值
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            response = requests.post(f"{RAG_SERVICE_URL}/v1/rag/ask", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                sources_count = len(data['sources'])
                print(f"  ✅ 找到 {sources_count} 个来源")
                
                if sources_count > 0:
                    print(f"  💡 答案: {data['answer'][:100]}...")
                    print("  📚 来源:")
                    for i, source in enumerate(data['sources'][:2], 1):
                        print(f"    {i}. {source.get('document_name', '未知')} (相似度: {source.get('similarity', 0):.3f})")
                else:
                    print(f"  ❌ 未找到相关内容")
            else:
                print(f"  ❌ 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")

def test_direct_retrieval():
    """直接测试检索功能"""
    print("\n🔍 直接测试检索API...")
    
    try:
        # 测试原始检索API
        response = requests.post("http://localhost:8000/v1/retrieval", json={
            "question": "360",
            "top_k": 5,
            "similarity_threshold": 0.05
        })
        
        if response.status_code == 200:
            data = response.json()
            chunks = data.get('data', {}).get('chunks', [])
            print(f"✅ 原始检索API找到 {len(chunks)} 个文档块")
            
            if chunks:
                for i, chunk in enumerate(chunks[:3], 1):
                    print(f"  {i}. 文档: {chunk.get('document_name', '未知')}")
                    print(f"     相似度: {chunk.get('similarity', 0):.3f}")
                    print(f"     内容预览: {chunk.get('content_with_weight', '')[:100]}...")
        else:
            print(f"❌ 原始检索API失败: {response.status_code}")
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"❌ 原始检索API错误: {e}")

def main():
    print("🚀 开始特定RAG测试")
    print("=" * 50)
    
    # 测试健康检查
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ RAG服务运行正常")
        else:
            print("❌ RAG服务异常")
            return
    except Exception as e:
        print(f"❌ 无法连接RAG服务: {e}")
        return
    
    # 测试直接检索
    test_direct_retrieval()
    
    # 测试不同问题
    test_with_different_questions()
    
    print("\n🎉 特定测试完成!")

if __name__ == "__main__":
    main()
