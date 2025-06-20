#!/usr/bin/env python3
"""
S3框架RAG服务测试脚本
"""

import requests
import json
import time

# S3 RAG服务配置
S3_RAG_SERVICE_URL = "http://localhost:8002"

def test_s3_health_check():
    """测试S3服务健康检查"""
    print("🔍 测试S3服务健康检查...")
    try:
        response = requests.get(f"{S3_RAG_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ S3服务健康检查通过")
            data = response.json()
            print(f"服务: {data.get('service')}")
            print(f"框架: {data.get('framework')}")
        else:
            print(f"❌ S3服务健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ S3服务健康检查错误: {e}")

def test_s3_rag_ask(question: str):
    """测试S3框架RAG问答"""
    print(f"\n🔍 测试S3-RAG问答: {question}")
    try:
        payload = {
            "question": question,
            "max_search_rounds": 3,
            "top_k": 5,
            "similarity_threshold": 0.05,  # 降低阈值以获得更多结果
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        start_time = time.time()
        response = requests.post(f"{S3_RAG_SERVICE_URL}/v1/s3-rag/ask", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            print("✅ S3-RAG问答成功")
            data = response.json()
            print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
            print(f"📝 问题: {data['question']}")
            print(f"🔄 搜索轮数: {data['search_rounds']}")
            print(f"📚 选中文档数: {len(data['selected_documents'])}")
            print(f"💡 答案: {data['answer']}")
            
            # 显示搜索过程
            if data['search_process']:
                print("\n🔍 搜索过程:")
                for i, process in enumerate(data['search_process'], 1):
                    if process.get('type') == 'initial_search':
                        print(f"  {i}. 初始搜索: '{process.get('query')}' -> {process.get('results_count')} 个结果")
                    elif process.get('type') == 'iterative_search':
                        print(f"  {i}. 迭代搜索: '{process.get('query')}' -> {process.get('results_count')} 个结果")
                    elif process.get('decision') == 'search_complete':
                        selected = process.get('selected_docs', [])
                        print(f"  {i}. 搜索完成，选中文档ID: {selected}")
            
            # 显示选中的文档
            if data['selected_documents']:
                print("\n📖 选中的文档:")
                for i, doc in enumerate(data['selected_documents'][:2], 1):  # 只显示前2个
                    print(f"  {i}. 文档: {doc.get('document_name', '未知')}")
                    print(f"     相似度: {doc.get('similarity', 0):.3f}")
                    print(f"     内容预览: {doc.get('content', '')[:150]}...")
            
            print(f"\n🤖 模型信息: {data['model_info']}")
            
        else:
            print(f"❌ S3-RAG问答失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ S3-RAG问答错误: {e}")

def test_with_knowledge_base_content():
    """测试知识库中实际存在的内容"""
    print("\n🔍 测试知识库实际内容...")
    
    # 基于知识库文档名"智信原子知识.md"，尝试相关问题
    test_questions = [
        "智信",
        "原子知识",
        "什么是智信？",
        "原子知识是什么？",
        "智信原子知识有什么内容？",
        "请介绍一下智信的相关信息"
    ]
    
    for question in test_questions:
        test_s3_rag_ask(question)
        print("\n" + "-" * 50)

def compare_with_simple_rag():
    """对比S3框架与简单RAG的效果"""
    print("\n🔍 对比S3框架与简单RAG...")
    
    test_question = "智信原子知识"
    
    # 测试简单RAG
    print("📊 简单RAG结果:")
    try:
        simple_payload = {
            "question": test_question,
            "top_k": 3,
            "similarity_threshold": 0.05,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        simple_response = requests.post("http://localhost:8001/v1/rag/ask", json=simple_payload)
        if simple_response.status_code == 200:
            simple_data = simple_response.json()
            print(f"  答案: {simple_data['answer'][:200]}...")
            print(f"  来源数: {len(simple_data['sources'])}")
        else:
            print("  简单RAG请求失败")
    except Exception as e:
        print(f"  简单RAG错误: {e}")
    
    print("\n📊 S3框架结果:")
    test_s3_rag_ask(test_question)

def main():
    """主测试函数"""
    print("🚀 开始测试S3框架RAG服务")
    print("=" * 60)
    
    # 测试健康检查
    test_s3_health_check()
    
    # 测试知识库实际内容
    test_with_knowledge_base_content()
    
    # 对比测试
    compare_with_simple_rag()
    
    print("\n🎉 S3框架测试完成!")

if __name__ == "__main__":
    main()
