#!/usr/bin/env python3
"""
Simplified Mode Testing - 3 questions per mode
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置
API_URL = "http://127.0.0.1:8060"
TEST_QUESTIONS_FILE = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/test_sample_50.json"

async def test_api_mode(session: aiohttp.ClientSession, questions: List[Dict], mode: str):
    """测试API单个模式"""
    print(f"\n🔍 测试API {mode.upper()}模式...")
    results = []
    
    # 根据模式设置超时
    timeout_map = {"fast": 30, "normal": 90, "deep": 150}
    timeout = timeout_map[mode]
    
    for i, question in enumerate(questions[:3]):  # 只测试3个问题
        print(f"  [{i+1}/3] {question['question'][:40]}...", end='', flush=True)
        
        start_time = time.time()
        try:
            async with session.post(
                f"{API_URL}/search",
                json={
                    "query": question["question"],
                    "mode": mode,
                    "enable_langfuse": False
                },
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                result = await response.json()
                elapsed = time.time() - start_time
                
                if result.get("success"):
                    print(f" ✅ {elapsed:.1f}s")
                    results.append({
                        "success": True,
                        "time": elapsed,
                        "answer_length": len(result.get("answer", "")),
                        "sources": len(result.get("sources", []))
                    })
                else:
                    print(f" ❌ {result.get('error', 'Unknown error')}")
                    results.append({"success": False, "error": result.get("error")})
                    
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            print(f" ❌ Timeout ({elapsed:.1f}s)")
            results.append({"success": False, "error": "Timeout"})
        except Exception as e:
            print(f" ❌ {str(e)}")
            results.append({"success": False, "error": str(e)})
        
        # 避免过载
        await asyncio.sleep(2)
    
    return results

async def main():
    """主测试函数"""
    print("🧪 FlashSearch 模式测试（简化版）")
    print("=" * 60)
    
    # 加载测试问题
    with open(TEST_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"📋 加载了 {len(questions)} 个问题，每种模式测试3个")
    
    # 测试API
    async with aiohttp.ClientSession() as session:
        # 健康检查
        try:
            async with session.get(f"{API_URL}/health") as response:
                health = await response.json()
                print(f"✅ API服务健康: {health['status']}")
        except:
            print("❌ API服务不可用")
            return
        
        # 测试结果
        all_results = {}
        
        # 测试每种模式
        for mode in ["fast", "normal", "deep"]:
            mode_results = await test_api_mode(session, questions, mode)
            all_results[mode] = mode_results
            
            # 简单统计
            successful = [r for r in mode_results if r.get("success")]
            if successful:
                avg_time = sum(r["time"] for r in successful) / len(successful)
                avg_answer = sum(r["answer_length"] for r in successful) / len(successful)
                print(f"  📊 成功率: {len(successful)}/3, 平均时间: {avg_time:.1f}s, 平均答案长度: {avg_answer:.0f}")
            else:
                print(f"  📊 全部失败")
    
    # 生成分析报告
    print("\n" + "=" * 60)
    print("📊 性能分析报告")
    print("=" * 60)
    
    # 分析每种模式
    for mode, results in all_results.items():
        print(f"\n{mode.upper()}模式:")
        successful = [r for r in results if r.get("success")]
        
        if successful:
            times = [r["time"] for r in successful]
            print(f"  • 成功率: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.0f}%)")
            print(f"  • 响应时间: 最快{min(times):.1f}s, 最慢{max(times):.1f}s, 平均{sum(times)/len(times):.1f}s")
            print(f"  • 平均答案长度: {sum(r['answer_length'] for r in successful)/len(successful):.0f}字符")
            print(f"  • 平均来源数: {sum(r['sources'] for r in successful)/len(successful):.1f}个")
        else:
            print(f"  • 全部失败")
            for r in results:
                if r.get("error"):
                    print(f"    - 错误: {r['error']}")
    
    # 模式对比
    print("\n📈 模式对比:")
    
    # Fast vs Normal
    fast_success = [r for r in all_results.get("fast", []) if r.get("success")]
    normal_success = [r for r in all_results.get("normal", []) if r.get("success")]
    
    if fast_success and normal_success:
        fast_avg_time = sum(r["time"] for r in fast_success) / len(fast_success)
        normal_avg_time = sum(r["time"] for r in normal_success) / len(normal_success)
        speed_ratio = normal_avg_time / fast_avg_time
        
        fast_avg_answer = sum(r["answer_length"] for r in fast_success) / len(fast_success)
        normal_avg_answer = sum(r["answer_length"] for r in normal_success) / len(normal_success)
        quality_ratio = fast_avg_answer / normal_avg_answer
        
        print(f"  • Fast模式比Normal快 {speed_ratio:.1f}x")
        print(f"  • Fast模式答案长度是Normal的 {quality_ratio:.1%}")
    
    # 保存详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"mode_test_simplified_{timestamp}.json"
    
    report = {
        "test_info": {
            "timestamp": datetime.now().isoformat(),
            "questions_per_mode": 3,
            "modes": ["fast", "normal", "deep"]
        },
        "results": all_results,
        "analysis": {
            mode: {
                "success_rate": len([r for r in results if r.get("success")]) / len(results) * 100,
                "avg_response_time": sum(r["time"] for r in results if r.get("success")) / len([r for r in results if r.get("success")]) if [r for r in results if r.get("success")] else 0
            }
            for mode, results in all_results.items()
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存: {report_file}")
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    asyncio.run(main())