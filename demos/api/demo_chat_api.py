#!/usr/bin/env python3
"""
Chat API 使用演示
展示如何使用 /v1/chat/completions 端点
"""

import asyncio
import aiohttp
import json


async def demo_basic_chat():
    """基础对话演示"""
    print("\n🤖 基础对话演示")
    print("-" * 50)
    
    api_url = "http://localhost:8000/v1/chat/completions"
    
    # 简单对话请求
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "什么是S3框架？"}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 回答: {result['choices'][0]['message']['content']}")
            else:
                print(f"❌ 错误: {response.status}")


async def demo_s3_search():
    """S3搜索演示"""
    print("\n🔍 S3搜索演示")
    print("-" * 50)
    
    api_url = "http://localhost:8000/v1/chat/completions"
    
    # 启用S3搜索的请求
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "帮我搜索关于深度学习最新进展的信息"}
        ],
        "extra_body": {
            "enable_s3": True,
            "dataset_ids": ["17362cc02a1911efbc2b0242ac120006"]
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print("✅ S3搜索完成")
                
                # 显示搜索信息
                if 'search_info' in result.get('extra_body', {}):
                    search_info = result['extra_body']['search_info']
                    print(f"   搜索轮数: {search_info.get('search_rounds', 0)}")
                    print(f"   检索文档: {search_info.get('total_chunks', 0)}")
            else:
                print(f"❌ 错误: {response.status}")


async def demo_streaming():
    """流式响应演示"""
    print("\n🌊 流式响应演示")
    print("-" * 50)
    
    api_url = "http://localhost:8000/v1/chat/completions"
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "介绍一下Python的异步编程"}
        ],
        "stream": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                print("✅ 流式响应: ", end="", flush=True)
                
                async for line in response.content:
                    if line:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith("data: "):
                            data = line_str[6:]
                            if data != "[DONE]":
                                try:
                                    chunk = json.loads(data)
                                    content = chunk['choices'][0].get('delta', {}).get('content', '')
                                    print(content, end="", flush=True)
                                except:
                                    pass
                print()  # 换行
            else:
                print(f"❌ 错误: {response.status}")


async def demo_conversation():
    """多轮对话演示"""
    print("\n💬 多轮对话演示")
    print("-" * 50)
    
    api_url = "http://localhost:8000/v1/chat/completions"
    
    # 创建对话
    conversation_id = None
    
    # 第一轮对话
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "记住我的名字是小明"}
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        # 第一轮
        async with session.post(api_url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                conversation_id = result.get('conversation_id')
                print(f"第1轮: {result['choices'][0]['message']['content']}")
        
        # 第二轮 - 使用相同的conversation_id
        if conversation_id:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "user", "content": "我叫什么名字？"}
                ],
                "conversation_id": conversation_id
            }
            
            async with session.post(api_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"第2轮: {result['choices'][0]['message']['content']}")


async def main():
    """运行所有演示"""
    print("\n" + "="*60)
    print("🚀 Chat API 演示")
    print("="*60)
    
    # 运行各个演示
    await demo_basic_chat()
    await demo_s3_search()
    await demo_streaming()
    await demo_conversation()
    
    print("\n✅ 所有演示完成！")


if __name__ == "__main__":
    print("\n📌 确保API服务器正在运行: http://localhost:8000")
    print("运行命令: python src/api/server.py")
    
    asyncio.run(main())