#!/usr/bin/env python3
"""
Test Search Modes
测试不同搜索模式的性能和质量
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any

API_URL = "http://127.0.0.1:8060"
TEST_QUERY = "人工智能最新发展趋势"

async def test_search_mode(session: aiohttp.ClientSession, mode: str) -> Dict[str, Any]:
    """测试特定搜索模式"""
    print(f"\n🔍 测试 {mode.upper()} 模式...")
    
    search_data = {
        "query": TEST_QUERY,
        "mode": mode,
        "enable_langfuse": False
    }
    
    start_time = time.time()
    
    try:
        async with session.post(
            f"{API_URL}/search",
            json=search_data,
            timeout=aiohttp.ClientTimeout(total=180)
        ) as response:
            result = await response.json()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            if result.get("success"):
                answer_len = len(result.get("answer", ""))
                sources_count = len(result.get("sources", []))
                iterations = result.get("stats", {}).get("iterations", 0)
                strategies = result.get("stats", {}).get("search_strategies_used", [])
                
                print(f"✅ 成功:")
                print(f"  ⏱️  响应时间: {elapsed_time:.1f}s")
                print(f"  📄 答案长度: {answer_len} 字符")
                print(f"  🔗 来源数量: {sources_count}")
                print(f"  🔄 迭代轮数: {iterations}")
                print(f"  🎯 搜索策略: {strategies}")
                
                return {
                    "mode": mode,
                    "success": True,
                    "time": elapsed_time,
                    "answer_length": answer_len,
                    "sources_count": sources_count,
                    "iterations": iterations,
                    "strategies": strategies
                }
            else:
                print(f"❌ 失败: {result.get('error', 'Unknown error')}")
                return {
                    "mode": mode,
                    "success": False,
                    "time": elapsed_time,
                    "error": result.get("error")
                }
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        return {
            "mode": mode,
            "success": False,
            "time": time.time() - start_time,
            "error": str(e)
        }

async def get_available_modes(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """获取可用的搜索模式"""
    try:
        async with session.get(f"{API_URL}/modes") as response:
            return await response.json()
    except Exception as e:
        print(f"❌ 无法获取搜索模式: {e}")
        return {}

async def main():
    """主测试函数"""
    print("🧪 FlashSearch 搜索模式测试")
    print("=" * 60)
    print(f"📝 测试查询: {TEST_QUERY}")
    
    async with aiohttp.ClientSession() as session:
        # 健康检查
        try:
            async with session.get(f"{API_URL}/health") as response:
                health = await response.json()
                print(f"✅ API健康: {health['status']}")
        except Exception as e:
            print(f"❌ API不可用: {e}")
            return
        
        # 获取可用模式
        modes_info = await get_available_modes(session)
        if modes_info:
            print(f"\n📋 可用搜索模式:")
            for mode, info in modes_info.get("modes", {}).items():
                print(f"  • {mode}: {info['name']} ({info['time_budget']})")
        
        # 测试所有模式
        modes_to_test = ["fast", "normal", "deep"]
        results = []
        
        for mode in modes_to_test:
            result = await test_search_mode(session, mode)
            results.append(result)
            
            # 为了避免过载，模式之间稍作休息
            await asyncio.sleep(2)
        
        # 结果对比
        print(f"\n{'='*60}")
        print("📊 性能对比:")
        print(f"{'模式':<10} {'时间':<10} {'答案长度':<12} {'来源数':<10} {'迭代数':<10}")
        print("-" * 52)
        
        for result in results:
            if result["success"]:
                print(f"{result['mode']:<10} {result['time']:<10.1f} {result['answer_length']:<12} "
                      f"{result['sources_count']:<10} {result['iterations']:<10}")
            else:
                print(f"{result['mode']:<10} {'失败':<10} {'-':<12} {'-':<10} {'-':<10}")
        
        # 性能分析
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            print(f"\n📈 性能分析:")
            
            # Fast vs Normal
            fast_result = next((r for r in successful_results if r["mode"] == "fast"), None)
            normal_result = next((r for r in successful_results if r["mode"] == "normal"), None)
            
            if fast_result and normal_result:
                speed_ratio = normal_result["time"] / fast_result["time"]
                quality_ratio = fast_result["answer_length"] / normal_result["answer_length"]
                
                print(f"  • Fast模式比Normal快 {speed_ratio:.1f}x")
                print(f"  • Fast模式答案长度是Normal的 {quality_ratio:.1%}")
            
            # 推荐
            print(f"\n💡 使用建议:")
            print(f"  • 快速查询、实时交互：使用 fast 模式")
            print(f"  • 一般搜索、平衡需求：使用 normal 模式")
            print(f"  • 深度研究、全面分析：使用 deep 模式")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ 测试被中断")
    except Exception as e:
        print(f"\n💥 测试错误: {e}")