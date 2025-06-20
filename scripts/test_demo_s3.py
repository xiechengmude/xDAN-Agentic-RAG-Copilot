#!/usr/bin/env python3
"""
S3框架演示版本测试脚本
"""

import requests
import json
import time

# 演示服务配置
DEMO_S3_SERVICE_URL = "http://localhost:8003"

def test_demo_health():
    """测试演示服务健康检查"""
    print("🔍 测试演示S3服务健康检查...")
    try:
        response = requests.get(f"{DEMO_S3_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ 演示S3服务健康检查通过")
            data = response.json()
            print(f"服务: {data.get('service')}")
            print(f"框架: {data.get('framework')}")
            print(f"数据源: {data.get('data_source')}")
        else:
            print(f"❌ 演示S3服务健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 演示S3服务健康检查错误: {e}")

def test_knowledge_base():
    """测试知识库信息"""
    print("\n🔍 测试知识库信息...")
    try:
        response = requests.get(f"{DEMO_S3_SERVICE_URL}/v1/demo-s3-rag/knowledge-base")
        if response.status_code == 200:
            print("✅ 知识库信息获取成功")
            data = response.json()
            print(f"📚 总文档数: {data.get('total_documents')}")
            print(f"🏷️  分类: {', '.join(data.get('categories', []))}")
            
            # 显示每个分类的文档
            kb = data.get('knowledge_base', {})
            for category, docs in kb.items():
                print(f"\n📂 {category} ({len(docs)} 个文档):")
                for doc in docs:
                    print(f"  - {doc.get('document_name')}")
        else:
            print(f"❌ 知识库信息获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 知识库信息获取错误: {e}")

def test_demo_s3_rag(question: str):
    """测试演示S3框架RAG问答"""
    print(f"\n🔍 测试演示S3-RAG问答: {question}")
    try:
        payload = {
            "question": question,
            "max_search_rounds": 3,
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        start_time = time.time()
        response = requests.post(f"{DEMO_S3_SERVICE_URL}/v1/demo-s3-rag/ask", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            print("✅ 演示S3-RAG问答成功")
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
                for i, doc in enumerate(data['selected_documents'], 1):
                    print(f"  {i}. 文档: {doc.get('document_name', '未知')}")
                    print(f"     相似度: {doc.get('similarity', 0):.3f}")
                    print(f"     内容预览: {doc.get('content', '')[:100]}...")
            
            print(f"\n🤖 模型信息: {data['model_info']}")
            
        else:
            print(f"❌ 演示S3-RAG问答失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 演示S3-RAG问答错误: {e}")

def test_various_questions():
    """测试各种类型的问题"""
    print("\n🔍 测试各种类型的问题...")
    
    test_questions = [
        "什么是人工智能？",
        "机器学习有哪些类型？",
        "RAG技术是什么？",
        "S3框架的优势是什么？",
        "深度学习和机器学习的关系？",
        "如何提高AI系统的性能？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*50}")
        print(f"问题 {i}/{len(test_questions)}")
        test_demo_s3_rag(question)
        if i < len(test_questions):
            time.sleep(2)  # 避免请求过快

def main():
    """主测试函数"""
    print("🚀 开始测试S3框架演示服务")
    print("=" * 60)
    
    # 测试健康检查
    test_demo_health()
    
    # 测试知识库信息
    test_knowledge_base()
    
    # 测试各种问题
    test_various_questions()
    
    print("\n🎉 S3框架演示测试完成!")

if __name__ == "__main__":
    main()
