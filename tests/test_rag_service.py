#!/usr/bin/env python3
"""
RAG服务测试脚本
"""

import requests
import json
import time

# RAG服务配置
RAG_SERVICE_URL = "http://localhost:8001"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查错误: {e}")

def test_list_datasets():
    """测试列出数据集"""
    print("\n🔍 测试列出数据集...")
    try:
        response = requests.get(f"{RAG_SERVICE_URL}/v1/rag/datasets")
        if response.status_code == 200:
            print("✅ 数据集列表获取成功")
            data = response.json()
            if 'data' in data and data['data']:
                print(f"找到 {len(data['data'])} 个数据集:")
                for dataset in data['data'][:3]:  # 只显示前3个
                    print(f"  - {dataset.get('name', '未知')} (ID: {dataset.get('id', '未知')})")
            else:
                print("没有找到数据集")
        else:
            print(f"❌ 获取数据集失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 获取数据集错误: {e}")

def test_rag_ask(question: str):
    """测试RAG问答"""
    print(f"\n🔍 测试RAG问答: {question}")
    try:
        payload = {
            "question": question,
            "top_k": 3,
            "similarity_threshold": 0.1,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        start_time = time.time()
        response = requests.post(f"{RAG_SERVICE_URL}/v1/rag/ask", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            print("✅ RAG问答成功")
            data = response.json()
            print(f"⏱️  响应时间: {end_time - start_time:.2f}秒")
            print(f"📝 问题: {data['question']}")
            print(f"💡 答案: {data['answer']}")
            print(f"📚 使用了 {len(data['sources'])} 个来源")
            
            if data['sources']:
                print("📖 来源信息:")
                for i, source in enumerate(data['sources'][:2], 1):  # 只显示前2个来源
                    print(f"  {i}. 文档: {source.get('document_name', '未知')}")
                    print(f"     相似度: {source.get('similarity', 0):.3f}")
                    print(f"     预览: {source.get('content_preview', '')[:100]}...")
            
            print(f"🤖 模型信息: {data['model_info']}")
        else:
            print(f"❌ RAG问答失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ RAG问答错误: {e}")

def test_rag_ask_stream(question: str):
    """测试RAG流式问答"""
    print(f"\n🔍 测试RAG流式问答: {question}")
    try:
        payload = {
            "question": question,
            "top_k": 3,
            "similarity_threshold": 0.1,
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        print("🌊 开始流式响应...")
        response = requests.post(f"{RAG_SERVICE_URL}/v1/rag/ask-stream", json=payload, stream=True)
        
        if response.status_code == 200:
            print("✅ 流式响应开始")
            answer_parts = []
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'sources' in data:
                                print(f"📚 找到 {len(data['sources'])} 个来源")
                            elif 'choices' in data:
                                content = data['choices'][0]['delta'].get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    answer_parts.append(content)
                        except json.JSONDecodeError:
                            # 可能是纯文本内容
                            print(data_str, end='', flush=True)
                            answer_parts.append(data_str)
            
            print(f"\n✅ 流式响应完成，总长度: {len(''.join(answer_parts))} 字符")
        else:
            print(f"❌ 流式问答失败: {response.status_code}")
            print(f"错误: {response.text}")
    except Exception as e:
        print(f"❌ 流式问答错误: {e}")

def main():
    """主测试函数"""
    print("🚀 开始测试RAG知识服务")
    print("=" * 50)
    
    # 测试健康检查
    test_health_check()
    
    # 测试列出数据集
    test_list_datasets()
    
    # 测试问答
    test_questions = [
        "什么是人工智能？",
        "请介绍一下机器学习的基本概念",
        "深度学习有哪些应用？"
    ]
    
    for question in test_questions:
        # 测试普通问答
        test_rag_ask(question)
        
        # 测试流式问答
        test_rag_ask_stream(question)
        
        print("\n" + "-" * 30)
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()
