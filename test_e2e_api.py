#!/usr/bin/env python3
"""
端到端API测试
测试完整的API调用链
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 清除代理
for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if var in os.environ:
        del os.environ[var]

# 加载环境变量
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'
load_dotenv(env_path)

# 添加项目路径
sys.path.append(str(project_root))

from src.clients.xdan_rag_client import XDANRagClient
from config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID

def test_s3_search_api():
    """测试S3智能搜索API"""
    print("\n=== 测试S3智能搜索API ===")
    
    url = "http://localhost:8050/api/search/stream"
    payload = {
        "question": "什么是RAGFlow？它的主要功能有哪些？",
        "max_rounds": 2,
        "top_k": 5,
        "similarity_threshold": 0.3
    }
    
    print(f"发送请求到: {url}")
    print(f"问题: {payload['question']}")
    
    response = requests.post(url, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        return False
    
    print("✅ 收到流式响应")
    
    events_count = 0
    answer_found = False
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    print("✅ 流式响应完成")
                    break
                elif data:
                    try:
                        event = json.loads(data)
                        events_count += 1
                        event_type = event.get('event_type')
                        
                        if event_type == 'search_start':
                            print(f"  🚀 搜索开始")
                        elif event_type == 'documents_retrieved':
                            count = event.get('data', {}).get('count', 0)
                            print(f"  📄 检索到 {count} 个文档")
                        elif event_type == 'answer_generated':
                            answer = event.get('data', {}).get('answer', '')
                            print(f"  📝 生成答案（长度: {len(answer)} 字符）")
                            answer_found = True
                            
                    except json.JSONDecodeError:
                        pass
    
    print(f"\n总计收到 {events_count} 个事件")
    return answer_found

def test_chat_api():
    """测试对话API"""
    print("\n=== 测试对话API ===")
    
    # 创建新对话
    url = "http://localhost:8050/api/chat/stream"
    payload = {
        "question": "你好，请介绍一下自己",
        "chat_id": None
    }
    
    print(f"发送请求到: {url}")
    print(f"问题: {payload['question']}")
    
    response = requests.post(url, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        return False
    
    print("✅ 收到流式响应")
    
    chat_id = None
    response_received = False
    
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data = line[6:]
                if data:
                    try:
                        event = json.loads(data)
                        event_type = event.get('event_type')
                        
                        if event_type == 'chat_created':
                            chat_id = event.get('data', {}).get('chat_id')
                            print(f"  💬 创建对话: {chat_id}")
                        elif event_type == 'chat_response':
                            content = event.get('data', {}).get('content', '')
                            if content:
                                print(f"  💬 收到回复（长度: {len(content)} 字符）")
                                response_received = True
                        elif event_type == 'complete':
                            print("  ✅ 对话完成")
                            
                    except json.JSONDecodeError:
                        pass
    
    return response_received and chat_id is not None

def test_health_check():
    """测试健康检查API"""
    print("\n=== 测试健康检查API ===")
    
    url = "http://localhost:8050/api/health"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 健康检查成功")
        print(f"  状态: {data['status']}")
        print(f"  API连接: {data['api_connected']}")
        return data['status'] == 'healthy'
    else:
        print(f"❌ 健康检查失败: {response.status_code}")
        return False

def test_direct_api_call():
    """直接测试RAGFlow API调用"""
    print("\n=== 直接测试RAGFlow API ===")
    
    try:
        client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        
        # 测试检索
        result = client.retrieve_chunks(
            question="什么是知识库？",
            dataset_ids=[DEFAULT_DATASET_ID],
            page_size=3
        )
        
        chunks = result.get('chunks', [])
        print(f"✅ 直接API调用成功")
        print(f"  检索到 {len(chunks)} 个文档片段")
        
        for i, chunk in enumerate(chunks[:2]):
            print(f"\n  片段{i+1}:")
            print(f"    相似度: {chunk.get('similarity', 'N/A')}")
            print(f"    内容预览: {chunk.get('content', '')[:50]}...")
        
        return len(chunks) > 0
        
    except Exception as e:
        print(f"❌ 直接API调用失败: {e}")
        return False

def main():
    print("=" * 60)
    print("端到端API测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 确保代理已清除
    print("\n代理状态:")
    for var in ['http_proxy', 'https_proxy']:
        value = os.environ.get(var, "未设置")
        print(f"  {var}: {value}")
    
    tests = [
        ("健康检查", test_health_check),
        ("直接RAGFlow API", test_direct_api_call),
        ("S3智能搜索", test_s3_search_api),
        ("对话功能", test_chat_api),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\n总计: {total} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    
    if passed == total:
        print("\n🎉 所有API测试通过！")
        print("✅ API接口层运行正常")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())