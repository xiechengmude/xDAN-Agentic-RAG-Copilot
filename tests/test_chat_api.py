"""
测试对话相关API - 查找正确的接口
"""
import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

kb_id = "7e9fe1de4ce211f09cf90242ac140006"


def test_chat_endpoints():
    """测试不同的对话端点"""
    print(f"\n测试对话相关API")
    print("="*60)
    
    # 1. 创建对话
    print("\n1. 创建对话...")
    chat_data = {
        "name": f"测试_{datetime.now().strftime('%H%M%S')}",
        "dataset_ids": [kb_id]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chats",
        headers=headers,
        json=chat_data
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}")
        
        if result.get('code') == 0:
            chat_id = result['data']['id']
            print(f"\n成功创建对话: {chat_id}")
            
            # 2. 测试不同的消息发送路径
            test_paths = [
                f"/api/v1/chats/{chat_id}/messages",
                f"/api/v1/chats/{chat_id}/message",
                f"/api/v1/chats/{chat_id}/completions",
                f"/api/v1/chats/{chat_id}/completion",
                f"/api/v1/chat/{chat_id}/messages",
                f"/api/v1/chat/{chat_id}/message",
                f"/api/v1/conversations/{chat_id}/messages",
                f"/api/v1/conversations/{chat_id}/message",
                f"/api/v1/chats/{chat_id}/ask",
                f"/api/v1/chats/{chat_id}/chat"
            ]
            
            msg_data = {
                "content": "你好",
                "question": "你好",  # 尝试不同的字段名
                "message": "你好",
                "query": "你好"
            }
            
            print("\n2. 测试消息发送端点...")
            for path in test_paths:
                print(f"\n尝试: {path}")
                try:
                    resp = requests.post(
                        f"{BASE_URL}{path}",
                        headers=headers,
                        json=msg_data
                    )
                    print(f"  状态码: {resp.status_code}")
                    if resp.status_code == 200:
                        print(f"  ✓ 成功！响应: {resp.text[:200]}")
                        # 解析响应
                        try:
                            data = resp.json()
                            if data.get('code') == 0:
                                print(f"  响应数据: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
                        except:
                            pass
                    elif resp.status_code == 404:
                        print(f"  ✗ 404 Not Found")
                    else:
                        print(f"  响应: {resp.text[:100]}")
                except Exception as e:
                    print(f"  错误: {e}")
            
            # 3. 尝试获取对话历史
            print("\n\n3. 测试获取对话历史...")
            history_paths = [
                f"/api/v1/chats/{chat_id}/messages",
                f"/api/v1/chats/{chat_id}/history",
                f"/api/v1/conversations/{chat_id}/messages"
            ]
            
            for path in history_paths:
                print(f"\n尝试GET: {path}")
                try:
                    resp = requests.get(
                        f"{BASE_URL}{path}",
                        headers=headers
                    )
                    print(f"  状态码: {resp.status_code}")
                    if resp.status_code == 200:
                        print(f"  ✓ 成功！")
                except Exception as e:
                    print(f"  错误: {e}")


def test_conversation_api():
    """测试会话API（另一种可能的接口）"""
    print("\n\n4. 测试会话API (conversation)")
    print("="*60)
    
    # 创建会话
    conv_data = {
        "name": f"会话_{datetime.now().strftime('%H%M%S')}"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/conversations",
        headers=headers,
        json=conv_data
    )
    
    print(f"创建会话状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"响应: {response.text[:300]}")


def test_completion_api():
    """测试completion风格的API"""
    print("\n\n5. 测试Completion API")
    print("="*60)
    
    # OpenAI风格的completion API
    completion_data = {
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "dataset_ids": [kb_id]
    }
    
    paths = [
        "/api/v1/completions",
        "/api/v1/chat/completions",
        "/v1/chat/completions"
    ]
    
    for path in paths:
        print(f"\n尝试: {path}")
        try:
            resp = requests.post(
                f"{BASE_URL}{path}",
                headers=headers,
                json=completion_data
            )
            print(f"  状态码: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  ✓ 成功！响应: {resp.text[:200]}")
        except Exception as e:
            print(f"  错误: {e}")


def main():
    print(f"\nRAGFlow 对话API测试")
    print(f"时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}")
    
    test_chat_endpoints()
    test_conversation_api()
    test_completion_api()


if __name__ == "__main__":
    main()