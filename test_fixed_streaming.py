#!/usr/bin/env python3
"""
测试修复后的流式接口 - 验证增量内容
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
            "name": f"增量测试 - {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "dataset_ids": [],
            "description": "测试增量流式响应"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            return result["data"]["id"]
    return None

def test_incremental_streaming(chat_id):
    """测试增量流式响应"""
    print("发送消息: '请用中文说一个10个字的句子'")
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
        headers=headers,
        json={
            "content": "请用中文说一个10个字的句子",
            "stream": True
        },
        stream=True
    )
    
    if response.status_code != 200:
        print(f"请求失败: {response.status_code}")
        return False
    
    print("\n=== 增量流式响应测试 ===")
    chunk_count = 0
    accumulated_content = ""
    
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
                        
                        if data.get("data") == True:
                            print("Data: [STREAM_END]")
                            break
                        elif isinstance(data.get("data"), dict):
                            # 检查是否有增量内容
                            answer_delta = data["data"].get("answer_delta", "")
                            if answer_delta:
                                print(f"增量内容: '{answer_delta}'")
                                accumulated_content += answer_delta
                                print(f"累加内容: '{accumulated_content}'")
                            
                            # 检查是否还有完整答案（应该没有）
                            answer = data["data"].get("answer", "")
                            if answer:
                                print(f"⚠️  警告：仍然返回完整答案: '{answer}'")
                            
                            reference = data["data"].get("reference", {})
                            if reference:
                                print(f"Reference - Total: {reference.get('total', 0)}")
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON解析错误: {e}")
                        print(f"原始数据: {json_str}")
    
    print(f"\n=== 测试结果 ===")
    print(f"总共接收到 {chunk_count} 个数据块")
    print(f"累加的完整内容: '{accumulated_content}'")
    print(f"内容长度: {len(accumulated_content)} 字符")
    
    return True

def main():
    print("=== 增量流式接口测试 ===")
    
    # 创建测试对话
    chat_id = create_test_chat()
    if not chat_id:
        print("❌ 无法创建测试对话")
        return 1
    
    print(f"✅ 测试对话创建成功: {chat_id}")
    
    # 测试增量流式响应
    if not test_incremental_streaming(chat_id):
        print("❌ 测试失败")
        return 1
    
    print("\n✅ 增量流式测试完成")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main()) 