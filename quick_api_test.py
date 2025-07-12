#!/usr/bin/env python3
"""
快速API测试脚本
"""

import asyncio
import aiohttp
import json

async def quick_test():
    """快速测试API基本功能"""
    base_url = "http://localhost:8050"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer xDAN-RAG-Service-Demo-Key"
    }
    
    async with aiohttp.ClientSession() as session:
        print("🚀 开始快速API测试\n")
        
        # 1. 健康检查
        print("1️⃣ 健康检查...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ 服务健康")
                    print(f"   状态: {result.get('data', {}).get('status', 'unknown')}")
                else:
                    print(f"❌ 健康检查失败: {response.status}")
                    return
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return
        
        # 2. 获取数据集
        print("\n2️⃣ 获取数据集...")
        try:
            async with session.get(f"{base_url}/api/v1/datasets", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    datasets = result.get('data', {}).get('datasets', [])
                    print(f"✅ 找到 {len(datasets)} 个数据集")
                    if datasets:
                        print(f"   第一个数据集: {datasets[0].get('name', 'Unknown')}")
                else:
                    print(f"❌ 获取数据集失败: {response.status}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")
        
        # 3. 创建聊天会话
        print("\n3️⃣ 创建聊天会话...")
        chat_data = {
            "name": "快速测试会话",
            "dataset_ids": [],
            "description": "API快速测试"
        }
        
        try:
            async with session.post(f"{base_url}/api/v1/chats", 
                                  headers=headers, 
                                  json=chat_data) as response:
                if response.status == 200:
                    result = await response.json()
                    chat_id = result.get('data', {}).get('id')
                    print(f"✅ 会话创建成功: {chat_id[:8]}...")
                    
                    # 4. 发送测试问题
                    print("\n4️⃣ 发送测试问题...")
                    message_data = {
                        "content": "什么是API？",
                        "stream": False
                    }
                    
                    try:
                        async with session.post(f"{base_url}/api/v1/chats/{chat_id}/completions",
                                              headers=headers,
                                              json=message_data,
                                              timeout=aiohttp.ClientTimeout(total=60)) as response:
                            if response.status == 200:
                                result = await response.json()
                                answer = result.get('data', {}).get('answer', '')
                                print(f"✅ 回答成功: {answer[:100]}...")
                                print(f"\n🎉 API测试完成！所有功能正常")
                            else:
                                text = await response.text()
                                print(f"❌ 问答失败: {response.status} - {text}")
                    except asyncio.TimeoutError:
                        print("❌ 请求超时（60秒）")
                    except Exception as e:
                        print(f"❌ 问答请求失败: {e}")
                        
                else:
                    text = await response.text()
                    print(f"❌ 创建会话失败: {response.status} - {text}")
        except Exception as e:
            print(f"❌ 创建会话请求失败: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())