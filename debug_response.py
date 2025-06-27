#!/usr/bin/env python3
"""
调试API响应格式
"""

import asyncio
import aiohttp
import json

API_BASE_URL = "http://localhost:8050"

async def debug_response():
    """调试API响应"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer xDAN-RAG-Service-Demo-Key"
    }
    
    payload = {
        "content": "如何重置我的密码？",
        "stream": False,
        "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],
        "max_rounds": 2
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 创建会话
            print("📋 创建对话会话...")
            async with session.post(
                f"{API_BASE_URL}/api/v1/chats",
                json={"name": "调试测试"},
                headers=headers
            ) as create_response:
                
                print(f"创建会话状态码: {create_response.status}")
                create_text = await create_response.text()
                print(f"创建会话原始响应: {create_text}")
                
                if create_response.status != 200:
                    return
                
                chat_data = json.loads(create_text)
                chat_id = chat_data["data"]["id"]
                print(f"会话ID: {chat_id}")
            
            # 2. 发送消息
            print(f"\n💬 发送消息...")
            async with session.post(
                f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                print(f"消息状态码: {response.status}")
                response_text = await response.text()
                print(f"消息原始响应: {response_text}")
                
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        print(f"\n🔍 解析后的响应结构:")
                        print(f"- code: {result.get('code')}")
                        print(f"- message: {result.get('message')}")
                        print(f"- data keys: {list(result.get('data', {}).keys())}")
                        
                        data = result.get('data', {})
                        for key, value in data.items():
                            if isinstance(value, str):
                                print(f"- data.{key}: {value[:100]}...")
                            else:
                                print(f"- data.{key}: {type(value)} - {value}")
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON解析失败: {e}")
                
        except Exception as e:
            print(f"❌ 异常: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_response())