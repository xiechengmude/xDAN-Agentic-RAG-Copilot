#!/usr/bin/env python3
"""
快速测试脚本
验证基本连接和功能
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'
load_dotenv(env_path)

# 添加项目路径
sys.path.append(str(project_root))

from src.clients.xdan_rag_client import XDANRagClient, APIError
from src.clients.llm_client import LLMClient
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY, S3_SEARCH_MODEL_NAME,
    S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY, S3_GENERATOR_MODEL_NAME
)

def test_ragflow_connection():
    """测试RAGFlow连接"""
    print("\n1. 测试RAGFlow连接...")
    try:
        client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        result = client.list_datasets(page_size=1)
        print(f"✅ RAGFlow连接成功 - API: {RAGFLOW_API_URL}")
        return True
    except Exception as e:
        print(f"❌ RAGFlow连接失败: {e}")
        return False

def test_search_llm():
    """测试Search LLM"""
    print("\n2. 测试Search LLM...")
    try:
        client = LLMClient(
            base_url=S3_SEARCH_MODEL_URL,
            api_key=S3_SEARCH_API_KEY,
            model_name=S3_SEARCH_MODEL_NAME
        )
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.1
        )
        print(f"✅ Search LLM连接成功 - Model: {S3_SEARCH_MODEL_NAME}")
        return True
    except Exception as e:
        print(f"❌ Search LLM连接失败: {e}")
        return False

def test_generator_llm():
    """测试Generator LLM"""
    print("\n3. 测试Generator LLM...")
    try:
        client = LLMClient(
            base_url=S3_GENERATOR_MODEL_URL,
            api_key=S3_GENERATOR_API_KEY,
            model_name=S3_GENERATOR_MODEL_NAME
        )
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.1
        )
        print(f"✅ Generator LLM连接成功 - Model: {S3_GENERATOR_MODEL_NAME}")
        return True
    except Exception as e:
        print(f"❌ Generator LLM连接失败: {e}")
        return False

def test_local_server():
    """测试本地服务器"""
    print("\n4. 测试本地服务器...")
    try:
        response = requests.get("http://localhost:8050/api/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 本地服务器运行中 - 状态: {data['status']}")
            return True
        else:
            print(f"❌ 本地服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("❌ 本地服务器未运行")
        return False

def main():
    print("=" * 60)
    print("快速连接测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = {
        "RAGFlow": test_ragflow_connection(),
        "Search LLM": test_search_llm(),
        "Generator LLM": test_generator_llm(),
        "Local Server": test_local_server()
    }
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for service, status in results.items():
        status_str = "✅ 正常" if status else "❌ 异常"
        print(f"{service}: {status_str}")
    
    total = len(results)
    passed = sum(1 for status in results.values() if status)
    
    print(f"\n总计: {total} 项服务")
    print(f"正常: {passed} 项")
    print(f"异常: {total - passed} 项")
    
    if passed == total:
        print("\n🎉 所有服务连接正常！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项服务连接异常")
        return 1

if __name__ == "__main__":
    sys.exit(main())