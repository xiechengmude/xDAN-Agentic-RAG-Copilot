#!/usr/bin/env python3
"""
测试增强版S3 RAG服务
"""

import asyncio
import requests
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8003"
TEST_QUESTION = "什么是人工智能？"

def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    return response.status_code == 200

def test_enhanced_s3_rag():
    """测试增强版S3 RAG"""
    print("\n🤖 测试增强版S3 RAG...")
    
    payload = {
        "question": TEST_QUESTION,
        "max_search_rounds": 2,
        "top_k": 3,
        "similarity_threshold": 0.1,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/enhanced-s3-rag/ask",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"问题: {result['question']}")
            print(f"搜索轮次: {result['search_rounds']}")
            print(f"选中文档数: {len(result['selected_documents'])}")
            print(f"答案: {result['answer'][:200]}...")
            print(f"模型信息: {result['model_info']}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_list_datasets():
    """测试列出数据集"""
    print("\n📚 测试列出数据集...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/datasets")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"数据集数量: {len(result.get('data', []))}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_list_agents():
    """测试列出Agent（需要SDK模式）"""
    print("\n🤖 测试列出Agent...")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/agents")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Agent数量: {len(result.get('data', []))}")
            return True
        elif response.status_code == 501:
            print("Agent功能需要SDK模式（这是正常的，如果SDK未安装）")
            return True
        else:
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"请求失败: {e}")
        return False

def test_enhanced_s3_with_agent():
    """测试带Agent的S3 RAG（需要先创建Agent）"""
    print("\n🤖 测试带Agent的S3 RAG...")
    
    # 首先尝试创建Agent
    agent_payload = {
        "name": "S3-RAG-Agent",
        "description": "用于S3框架的智能Agent"
    }
    
    try:
        # 创建Agent
        agent_response = requests.post(
            f"{BASE_URL}/v1/agents",
            json=agent_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if agent_response.status_code == 200:
            agent_data = agent_response.json()
            agent_id = agent_data.get('data', {}).get('id')
            print(f"创建Agent成功: {agent_id}")
            
            # 使用Agent进行S3 RAG
            rag_payload = {
                "question": TEST_QUESTION,
                "agent_id": agent_id,
                "max_search_rounds": 2,
                "top_k": 3,
                "stream": False
            }
            
            rag_response = requests.post(
                f"{BASE_URL}/v1/enhanced-s3-rag/ask",
                json=rag_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if rag_response.status_code == 200:
                result = rag_response.json()
                print(f"Agent S3 RAG成功")
                print(f"Agent信息: {result.get('agent_info')}")
                print(f"Session信息: {result.get('session_info')}")
                return True
            else:
                print(f"Agent S3 RAG失败: {rag_response.text}")
                return False
                
        elif agent_response.status_code == 501:
            print("Agent功能需要SDK模式（跳过此测试）")
            return True
        else:
            print(f"创建Agent失败: {agent_response.text}")
            return False
            
    except Exception as e:
        print(f"Agent测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("🚀 开始测试增强版S3 RAG服务\n")
    
    tests = [
        ("健康检查", test_health_check),
        ("基础S3 RAG", test_enhanced_s3_rag),
        ("数据集列表", test_list_datasets),
        ("Agent列表", test_list_agents),
        ("Agent S3 RAG", test_enhanced_s3_with_agent)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    print("="*50)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 测试通过")

if __name__ == "__main__":
    main()
