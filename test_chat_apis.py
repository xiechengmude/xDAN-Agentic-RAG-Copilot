#!/usr/bin/env python3
"""
测试新增的对话管理接口
"""

import requests
import json
import time

# 配置
API_BASE_URL = "http://localhost:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def test_chat_apis():
    """测试对话管理接口"""
    print("="*60)
    print("测试对话管理接口")
    print("="*60)
    
    # 1. 创建测试对话
    print("\n1. 创建测试对话...")
    create_data = {
        "name": "测试对话_" + str(int(time.time())),
        "description": "用于测试GET和PUT接口",
        "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"]
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats",
        headers=headers,
        json=create_data
    )
    
    if response.status_code != 200:
        print(f"❌ 创建对话失败: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    chat_id = result["data"]["id"]
    print(f"✅ 创建成功，对话ID: {chat_id}")
    
    # 2. 测试 GET /api/v1/chats/{chat_id}
    print(f"\n2. 测试 GET /api/v1/chats/{chat_id}...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()["data"]
        print("✅ 获取对话详情成功:")
        print(f"  - 名称: {data['name']}")
        print(f"  - 描述: {data['description']}")
        print(f"  - 创建时间: {data['create_date']}")
    else:
        print(f"❌ 失败: {response.text}")
    
    # 3. 测试 PUT /api/v1/chats/{chat_id}
    print(f"\n3. 测试 PUT /api/v1/chats/{chat_id}...")
    update_data = {
        "name": "更新后的对话名称",
        "description": "更新后的描述 - " + str(int(time.time()))
    }
    
    response = requests.put(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()["data"]
        print("✅ 更新对话成功:")
        print(f"  - 新名称: {data['name']}")
        print(f"  - 新描述: {data['description']}")
        print(f"  - 更新时间: {data.get('update_date', 'N/A')}")
    else:
        print(f"❌ 失败: {response.text}")
    
    # 4. 再次获取确认更新
    print(f"\n4. 再次获取对话确认更新...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()["data"]
        if data["name"] == update_data["name"]:
            print("✅ 确认更新成功")
        else:
            print("❌ 更新验证失败")
    
    # 5. 测试错误情况 - 不存在的对话
    print("\n5. 测试错误情况 - 获取不存在的对话...")
    response = requests.get(
        f"{API_BASE_URL}/api/v1/chats/not_exists_chat_id",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 404:
        print("✅ 正确返回404错误")
    else:
        print(f"❌ 期望404，实际: {response.status_code}")
    
    # 6. 清理 - 删除测试对话
    print(f"\n6. 清理测试数据...")
    response = requests.delete(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ 删除测试对话成功")
    else:
        print(f"⚠️  删除失败: {response.status_code}")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    test_chat_apis()