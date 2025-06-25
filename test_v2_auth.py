#!/usr/bin/env python3
"""
测试 V2 API 的认证机制
验证第三方调用者无需提供 RAGFlow API key
"""

import requests
import json
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:8050"
TEST_API_KEYS = [
    ("xdan-demo-key-123456", "Demo Client"),
    ("xdan-prod-key-789012", "Production Client"),
    ("invalid-key-999999", "Invalid Client"),
    (None, "No Auth")
]

def test_auth_methods():
    """测试不同的认证方式"""
    print("=" * 60)
    print("测试 API V2 认证机制")
    print("=" * 60)
    print()
    
    # 测试健康检查（无需认证）
    print("1. 测试健康检查接口（无需认证）")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
    print()
    
    # 测试不同的 API Key
    print("2. 测试不同的 API Key")
    for api_key, client_name in TEST_API_KEYS:
        print(f"\n   测试 {client_name}:")
        headers = {}
        if api_key:
            headers["X-API-Key"] = api_key
            
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/datasets",
                headers=headers
            )
            print(f"   - API Key: {api_key}")
            print(f"   - 状态码: {response.status_code}")
            if response.status_code == 200:
                print("   - ✅ 认证成功")
            else:
                print(f"   - ❌ 认证失败: {response.json()}")
        except Exception as e:
            print(f"   - ❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)
    
    # 测试 Bearer Token 方式
    print("\n3. 测试 Bearer Token 认证方式")
    headers = {
        "Authorization": "Bearer xdan-demo-key-123456"
    }
    response = requests.get(
        f"{API_BASE_URL}/api/v1/datasets",
        headers=headers
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Bearer Token 认证成功")
    else:
        print(f"   ❌ 认证失败: {response.json()}")
    
    print("\n" + "=" * 60)

def test_api_operations():
    """测试实际的 API 操作"""
    print("\n4. 测试 API 操作（使用有效的 API Key）")
    
    session = requests.Session()
    session.headers.update({
        "X-API-Key": "xdan-demo-key-123456",
        "Content-Type": "application/json"
    })
    
    # 创建数据集
    print("\n   a) 创建数据集")
    dataset_data = {
        "name": f"测试知识库_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "V2 API 认证测试创建的知识库"
    }
    
    try:
        response = session.post(
            f"{API_BASE_URL}/api/v1/datasets",
            json=dataset_data
        )
        print(f"      状态码: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print("      ✅ 创建成功")
            print(f"      响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 如果创建成功，尝试获取数据集列表
            print("\n   b) 获取数据集列表")
            response = session.get(f"{API_BASE_URL}/api/v1/datasets")
            if response.status_code == 200:
                print("      ✅ 获取成功")
                data = response.json()
                print(f"      数据集数量: {len(data.get('data', []))}")
        else:
            print(f"      ❌ 创建失败: {response.json()}")
    except Exception as e:
        print(f"      ❌ 请求失败: {e}")
    
    print("\n" + "=" * 60)

def main():
    """主函数"""
    print("\n🔐 xDAN RAG Copilot API V2 认证测试\n")
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API 服务未响应，请先启动服务")
            print("   运行: python xdan_api_proxy_server_v2.py")
            return
    except:
        print("❌ 无法连接到 API 服务")
        print(f"   请确保服务运行在 {API_BASE_URL}")
        return
    
    # 运行测试
    test_auth_methods()
    test_api_operations()
    
    print("\n✅ 测试完成！")
    print("\n重要说明：")
    print("1. 第三方调用者使用自己的 API Key（如 xdan-demo-key-123456）")
    print("2. 无需提供 RAGFlow 的 API Key")
    print("3. RAGFlow 认证由代理服务器在后端处理")
    print("4. 支持 X-API-Key header 和 Bearer Token 两种方式")

if __name__ == "__main__":
    main()