#!/usr/bin/env python3
"""
测试流式接口 /api/v1/chats/{chat_id}/completions
"""

import requests
import json
import time
import sys

API_BASE_URL = "http://150.109.16.195:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def create_test_chat():
    """创建测试对话"""
    print("1. 创建测试对话...")
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats",
        headers=headers,
        json={
            "name": f"测试对话 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "dataset_ids": [],  # 不关联知识库
            "description": "API流式接口测试"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 创建对话失败: {response.status_code}")
        print(f"响应: {response.text}")
        return None
    
    result = response.json()
    if result.get("code") != 0:
        print(f"❌ 创建对话失败: {result.get('message')}")
        return None
    
    chat_id = result["data"]["id"]
    print(f"✅ 对话创建成功，ID: {chat_id}")
    return chat_id

def test_streaming_completions(chat_id):
    """测试流式完成接口"""
    print("\n2. 测试流式响应...")
    print("发送消息: '你好，请介绍一下你自己'")
    
    # 发送流式请求
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
        headers=headers,
        json={
            "content": "你好，请介绍一下你自己",
            "stream": True  # 开启流式响应
        },
        stream=True  # 启用流式读取
    )
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"响应: {response.text}")
        return False
    
    print("\n流式响应内容:")
    print("-" * 50)
    
    # 处理流式响应
    full_answer = ""
    chunk_count = 0
    
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            
            # SSE格式以"data:"开头
            if decoded_line.startswith('data:'):
                json_str = decoded_line[5:].strip()
                if json_str:
                    try:
                        data = json.loads(json_str)
                        chunk_count += 1
                        
                        # 处理不同类型的消息
                        if data.get("code") == 0:
                            if data.get("data") == True:
                                # 流结束
                                print("\n\n[流式响应结束]")
                            elif data.get("data", {}).get("answer"):
                                # 初始响应
                                answer = data["data"]["answer"]
                                full_answer += answer
                                print(f"\n[初始响应] {answer}", end="", flush=True)
                                
                                # 打印引用信息（如果有）
                                if data.get("data", {}).get("reference"):
                                    print(f"\n[引用信息] {json.dumps(data['data']['reference'], ensure_ascii=False, indent=2)}")
                            elif data.get("data", {}).get("answer_delta"):
                                # 增量响应
                                delta = data["data"]["answer_delta"]
                                full_answer += delta
                                print(delta, end="", flush=True)
                        else:
                            print(f"\n[错误] {data.get('message', 'Unknown error')}")
                            
                    except json.JSONDecodeError as e:
                        print(f"\n[JSON解析错误] {e}")
                        print(f"原始数据: {json_str}")
    
    print("-" * 50)
    print(f"\n统计信息:")
    print(f"- 接收到 {chunk_count} 个数据块")
    print(f"- 完整回答长度: {len(full_answer)} 字符")
    print(f"\n完整回答:")
    print(full_answer)
    
    return True

def test_non_streaming_completions(chat_id):
    """测试非流式完成接口"""
    print("\n3. 测试非流式响应...")
    print("发送消息: '1+1等于几？'")
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
        headers=headers,
        json={
            "content": "1+1等于几？",
            "stream": False  # 关闭流式响应
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"响应: {response.text}")
        return False
    
    result = response.json()
    print(f"\n非流式响应:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    if result.get("code") == 0 and result.get("data", {}).get("answer"):
        print(f"\n回答: {result['data']['answer']}")
    
    return True

def main():
    """主函数"""
    print("="*60)
    print("流式接口测试")
    print("="*60)
    print(f"API地址: {API_BASE_URL}")
    print(f"认证令牌: {AUTH_TOKEN[:20]}...")
    
    # 创建测试对话
    chat_id = create_test_chat()
    if not chat_id:
        print("\n❌ 测试失败：无法创建对话")
        return 1
    
    # 测试流式响应
    if not test_streaming_completions(chat_id):
        print("\n❌ 流式接口测试失败")
        return 1
    
    # 测试非流式响应
    time.sleep(1)  # 避免请求过快
    if not test_non_streaming_completions(chat_id):
        print("\n❌ 非流式接口测试失败")
        return 1
    
    print("\n✅ 所有测试通过！")
    return 0

if __name__ == "__main__":
    sys.exit(main())