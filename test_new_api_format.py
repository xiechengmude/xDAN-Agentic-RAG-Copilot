#!/usr/bin/env python3
"""
测试新的API格式（统一响应格式 + Bearer Token认证）
"""

import requests
import json

# 配置
API_BASE_URL = "http://localhost:8050"
API_KEY = "xDAN-RAG-Service-Demo-Key"

def test_api_with_auth():
    """测试带认证的API"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("🧪 测试新的API格式和认证机制")
    print("=" * 50)
    
    # 1. 测试健康检查（无需认证）
    print("\n1. 测试健康检查")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应格式: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 验证响应格式
        assert "code" in result, "缺少code字段"
        assert "message" in result, "缺少message字段"
        assert "data" in result, "缺少data字段"
        print("✅ 健康检查通过，响应格式正确")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
    
    # 2. 测试根路径（无需认证）
    print("\n2. 测试根路径")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        assert result["code"] == 0, "状态码应为0"
        print("✅ 根路径访问成功")
    except Exception as e:
        print(f"❌ 根路径访问失败: {e}")
    
    # 3. 测试无认证访问（应该失败）
    print("\n3. 测试无认证访问")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/datasets")
        print(f"状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 正确返回401未授权")
        else:
            print("⚠️ 未按预期返回401状态码")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 4. 测试错误的API Key
    print("\n4. 测试错误的API Key")
    try:
        wrong_headers = {
            "Authorization": "Bearer wrong-api-key",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{API_BASE_URL}/api/v1/datasets", headers=wrong_headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 401:
            print("✅ 正确拒绝错误的API Key")
            result = response.json()
            print(f"错误响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print("⚠️ 未按预期拒绝错误的API Key")
    except Exception as e:
        print(f"请求失败: {e}")
    
    # 5. 测试正确的API Key访问
    print("\n5. 测试正确的API Key访问")
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/datasets", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 认证成功，获取数据集列表")
            
            # 验证统一响应格式
            assert "code" in result, "缺少code字段"
            assert "message" in result, "缺少message字段"
            assert "data" in result, "缺少data字段"
            
            print(f"响应格式验证: ✅")
            print(f"数据集数量: {len(result.get('data', []))}")
            
        else:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 6. 测试创建聊天（需要认证）
    print("\n6. 测试创建聊天")
    try:
        chat_data = {
            "name": "API测试聊天",
            "description": "测试统一响应格式",
            "dataset_ids": []
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/chats",
            headers=headers,
            json=chat_data
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 聊天创建成功")
            
            # 验证响应格式
            assert result["code"] == 0, "状态码应为0"
            assert "data" in result, "缺少data字段"
            assert "id" in result["data"], "缺少聊天ID"
            
            chat_id = result["data"]["id"]
            print(f"聊天ID: {chat_id}")
            
            # 7. 测试删除聊天
            print("\n7. 测试删除聊天")
            delete_response = requests.delete(
                f"{API_BASE_URL}/api/v1/chats/{chat_id}",
                headers=headers
            )
            
            if delete_response.status_code == 200:
                delete_result = delete_response.json()
                assert delete_result["code"] == 0, "删除状态码应为0"
                print("✅ 聊天删除成功")
            else:
                print(f"❌ 聊天删除失败: {delete_response.status_code}")
                
        else:
            print(f"❌ 聊天创建失败: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 聊天创建测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API格式和认证测试完成")

if __name__ == "__main__":
    test_api_with_auth()