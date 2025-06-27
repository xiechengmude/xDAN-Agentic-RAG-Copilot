#!/usr/bin/env python3
"""
调试流式接口的具体行为
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def create_test_chat():
    """创建测试对话"""
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats",
        headers=headers,
        json={
            "name": f"调试测试 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "dataset_ids": [],
            "description": "调试流式接口"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result["data"]["id"]
    return None

def debug_streaming_response(chat_id):
    """详细调试流式响应"""
    print("发送消息: '请说一个简短的故事'")
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
        headers=headers,
        json={
            "content": "请说一个简短的故事",
            "stream": True
        },
        stream=True
    )
    
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        return False
    
    print("\n=== 流式响应调试 ===")
    chunk_count = 0
    previous_answer = ""
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            
            if decoded_line.startswith('data:'):
                json_str = decoded_line[5:].strip()
                if json_str:
                    try:
                        data = json.loads(json_str)
                        chunk_count += 1
                        
                        print(f"\n--- Chunk {chunk_count} ---")
                        print(f"Code: {data.get('code')}")
                        print(f"Message: {data.get('message')}")
                        
                        if data.get("data") == True:
                            print("Data: [STREAM_END]")
                        elif isinstance(data.get("data"), dict):
                            current_answer = data["data"].get("answer", "")
                            print(f"Answer Length: {len(current_answer)}")
                            
                            if previous_answer:
                                # 计算增量
                                if current_answer.startswith(previous_answer):
                                    delta = current_answer[len(previous_answer):]
                                    print(f"Delta: '{delta}'")
                                else:
                                    print("Delta: [ANSWER_RESET或不连续]")
                            else:
                                print(f"Initial Answer: '{current_answer}'")
                            
                            previous_answer = current_answer
                            
                            # 显示reference信息
                            reference = data["data"].get("reference", {})
                            if reference:
                                print(f"Reference - Total: {reference.get('total', 0)}")
                        else:
                            print(f"Data: {data.get('data')}")
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        print(f"原始数据: {json_str}")
    
    print(f"\n总共接收到 {chunk_count} 个数据块")
    return True

def main():
    print("=== 流式接口调试 ===")
    
    # 创建测试对话
    chat_id = create_test_chat()
    if not chat_id:
        print("❌ 无法创建测试对话")
        return 1
    
    print(f"✅ 测试对话创建成功: {chat_id}")
    
    # 调试流式响应
    if not debug_streaming_response(chat_id):
        print("❌ 调试失败")
        return 1
    
    print("\n✅ 调试完成")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())