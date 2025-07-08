#!/usr/bin/env python3
"""
FlashSearch API Python调用示例
展示如何使用Python调用各个API接口
"""

import asyncio
import json
import aiohttp
import time
from typing import Dict, Any, AsyncGenerator

# API配置
API_HOST = "localhost"
API_PORT = 8050
API_BASE = f"http://{API_HOST}:{API_PORT}"


class FlashSearchClient:
    """FlashSearch API 客户端"""
    
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as resp:
                return await resp.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/stats") as resp:
                return await resp.json()
    
    async def get_modes(self) -> Dict[str, Any]:
        """获取搜索模式"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/modes") as resp:
                return await resp.json()
    
    async def search(self, query: str, mode: str = "fast", domain: str = None) -> Dict[str, Any]:
        """同步搜索"""
        payload = {
            "query": query,
            "mode": mode
        }
        if domain:
            payload["domain"] = domain
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                return await resp.json()
    
    async def search_async(self, query: str, mode: str = "normal") -> Dict[str, Any]:
        """异步搜索"""
        payload = {
            "query": query,
            "mode": mode
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search/async",
                json=payload
            ) as resp:
                return await resp.json()
    
    async def search_stream(self, query: str, mode: str = "fast") -> AsyncGenerator[Dict[str, Any], None]:
        """SSE流式搜索"""
        payload = {
            "query": query,
            "mode": mode
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/search/stream",
                json=payload,
                headers={"Accept": "text/event-stream"},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                async for line in resp.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
    
    async def validate(self, query: str) -> Dict[str, Any]:
        """验证查询"""
        payload = {"query": query}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/validate",
                json=payload
            ) as resp:
                return await resp.json()


async def example_basic():
    """基础功能示例"""
    client = FlashSearchClient()
    
    print("=== 1. 健康检查 ===")
    health = await client.health_check()
    print(f"状态: {health['status']}, 版本: {health['version']}")
    
    print("\n=== 2. 获取统计信息 ===")
    stats = await client.get_stats()
    print(f"总搜索数: {stats.get('total_searches', 0)}")
    print(f"成功率: {stats.get('successful_searches', 0)}/{stats.get('total_searches', 0)}")
    
    print("\n=== 3. 获取搜索模式 ===")
    modes = await client.get_modes()
    print(f"默认模式: {modes['default']}")
    print(f"可用模式: {list(modes['modes'].keys())}")


async def example_search():
    """搜索功能示例"""
    client = FlashSearchClient()
    
    print("=== 同步搜索示例 ===")
    
    # Fast模式
    print("\n1️⃣ Fast模式搜索")
    start = time.time()
    result = await client.search("什么是机器学习？", mode="fast")
    elapsed = time.time() - start
    
    if result.get("success"):
        print(f"✅ 搜索成功")
        print(f"⏱️  耗时: {elapsed:.2f}秒")
        print(f"📝 答案长度: {len(result.get('answer', ''))}字符")
        print(f"📚 来源数量: {len(result.get('sources', []))}")
        print(f"💬 答案预览: {result.get('answer', '')[:100]}...")
    else:
        print(f"❌ 搜索失败: {result.get('error')}")
    
    # Normal模式（带领域）
    print("\n2️⃣ Normal模式搜索（技术领域）")
    result = await client.search(
        "Python异步编程最佳实践",
        mode="normal",
        domain="tech"
    )
    if result.get("success"):
        print(f"✅ 搜索成功")
        stats = result.get("stats", {})
        print(f"📊 统计: 迭代{stats.get('iterations', 0)}轮, "
              f"搜索{stats.get('total_searches', 0)}次, "
              f"置信度{stats.get('final_confidence', 0)}")


async def example_async_search():
    """异步搜索示例"""
    client = FlashSearchClient()
    
    print("=== 异步搜索示例 ===")
    result = await client.search_async("深度学习在医疗影像中的应用", mode="deep")
    
    print(f"任务ID: {result['task_id']}")
    print(f"状态: {result['status']}")
    print(f"消息: {result['message']}")


async def example_stream_search():
    """流式搜索示例"""
    client = FlashSearchClient()
    
    print("=== SSE流式搜索示例 ===")
    print("🔍 搜索: AI发展趋势")
    
    event_count = 0
    async for event in client.search_stream("AI发展趋势", mode="fast"):
        event_count += 1
        event_type = event.get("type")
        
        if event_type == "start":
            print(f"🚀 {event['message']}")
        elif event_type == "progress":
            print(f"📊 进度: {event['progress']}% - {event['message']}")
        elif event_type == "answer_chunk":
            print(f"📝 答案片段: {event['content'][:50]}...")
        elif event_type == "source":
            print(f"📚 来源{event['index']}: {event['source']['title']}")
        elif event_type == "done":
            print(f"✅ 完成! 耗时: {event['response_time']}秒")
        elif event_type == "error":
            print(f"❌ 错误: {event['error']}")
            
        # 限制显示事件数
        if event_count > 10:
            print("... (更多事件省略)")
            break


async def example_validate():
    """查询验证示例"""
    client = FlashSearchClient()
    
    print("=== 查询验证示例 ===")
    
    # 有效查询
    result = await client.validate("什么是区块链技术？")
    print(f"查询: '什么是区块链技术？' -> {result}")
    
    # 无效查询（太短）
    result = await client.validate("AI")
    print(f"查询: 'AI' -> {result}")
    
    # 无效查询（无字母数字）
    result = await client.validate("？？？")
    print(f"查询: '？？？' -> {result}")


async def example_batch_search():
    """批量搜索示例"""
    client = FlashSearchClient()
    
    print("=== 批量搜索示例 ===")
    questions = [
        "什么是深度学习？",
        "量子计算的应用",
        "区块链技术原理"
    ]
    
    # 并发搜索
    tasks = [client.search(q, mode="fast") for q in questions]
    results = await asyncio.gather(*tasks)
    
    for i, (question, result) in enumerate(zip(questions, results), 1):
        success = "✅" if result.get("success") else "❌"
        answer_len = len(result.get("answer", "")) if result.get("success") else 0
        print(f"{i}. {question} -> {success} ({answer_len}字符)")


async def main():
    """运行所有示例"""
    print("🚀 FlashSearch API Python示例")
    print("=" * 50)
    
    # 基础功能
    await example_basic()
    
    print("\n" + "=" * 50 + "\n")
    
    # 搜索功能
    await example_search()
    
    print("\n" + "=" * 50 + "\n")
    
    # 异步搜索
    await example_async_search()
    
    print("\n" + "=" * 50 + "\n")
    
    # 流式搜索
    await example_stream_search()
    
    print("\n" + "=" * 50 + "\n")
    
    # 查询验证
    await example_validate()
    
    print("\n" + "=" * 50 + "\n")
    
    # 批量搜索
    await example_batch_search()
    
    print("\n✨ 所有示例完成!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())