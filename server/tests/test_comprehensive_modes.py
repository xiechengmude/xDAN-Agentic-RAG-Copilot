#!/usr/bin/env python3
"""
Comprehensive Search Mode Testing
全面测试API和MCP在fast/normal/deep三种模式下的表现
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import statistics

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastmcp import Client
except ImportError:
    print("❌ FastMCP未安装，跳过MCP测试")
    Client = None

# 配置
API_URL = "http://127.0.0.1:8060"
MCP_URL = "http://127.0.0.1:9060/sse/"
TEST_QUESTIONS_FILE = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/test_sample_50.json"
TEST_QUESTION_COUNT = 10  # 每种模式测试10个问题

class SearchModeTester:
    def __init__(self):
        self.api_results = {"fast": [], "normal": [], "deep": []}
        self.mcp_results = {"fast": [], "normal": [], "deep": []}
        self.test_questions = []
        
    async def load_test_questions(self):
        """加载测试问题"""
        with open(TEST_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
            # 选择前10个问题
            self.test_questions = all_questions[:TEST_QUESTION_COUNT]
            print(f"📋 加载了 {len(self.test_questions)} 个测试问题")
    
    async def test_api_search(self, session: aiohttp.ClientSession, question: Dict, mode: str) -> Dict[str, Any]:
        """测试API搜索"""
        start_time = time.time()
        
        search_data = {
            "query": question["question"],
            "mode": mode,
            "enable_langfuse": False
        }
        
        try:
            # 根据模式设置不同的超时时间
            timeout_map = {"fast": 30, "normal": 90, "deep": 150}
            timeout = timeout_map.get(mode, 90)
            
            async with session.post(
                f"{API_URL}/search",
                json=search_data,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                result = await response.json()
                elapsed_time = time.time() - start_time
                
                if result.get("success"):
                    return {
                        "question_id": question["id"],
                        "success": True,
                        "mode": mode,
                        "time": elapsed_time,
                        "answer_length": len(result.get("answer", "")),
                        "sources_count": len(result.get("sources", [])),
                        "iterations": result.get("stats", {}).get("iterations", 0),
                        "strategies": result.get("stats", {}).get("search_strategies_used", [])
                    }
                else:
                    return {
                        "question_id": question["id"],
                        "success": False,
                        "mode": mode,
                        "time": elapsed_time,
                        "error": result.get("error", "Unknown error")
                    }
        except asyncio.TimeoutError:
            return {
                "question_id": question["id"],
                "success": False,
                "mode": mode,
                "time": time.time() - start_time,
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "question_id": question["id"],
                "success": False,
                "mode": mode,
                "time": time.time() - start_time,
                "error": str(e)
            }
    
    async def test_mcp_search(self, client: Client, question: Dict, mode: str) -> Dict[str, Any]:
        """测试MCP搜索"""
        if not client:
            return {"success": False, "error": "MCP client not available"}
            
        start_time = time.time()
        
        try:
            result = await client.call_tool("flash_search", {
                "query": question["question"],
                "mode": mode,
                "enable_langfuse": False
            })
            
            elapsed_time = time.time() - start_time
            
            if result and len(result) > 0:
                content = result[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("success"):
                        return {
                            "question_id": question["id"],
                            "success": True,
                            "mode": mode,
                            "time": elapsed_time,
                            "answer_length": len(data.get("answer", "")),
                            "sources_count": data.get("sources_count", 0),
                            "stats": data.get("stats", {})
                        }
            
            return {
                "question_id": question["id"],
                "success": False,
                "mode": mode,
                "time": elapsed_time,
                "error": "Invalid response"
            }
        except Exception as e:
            return {
                "question_id": question["id"],
                "success": False,
                "mode": mode,
                "time": time.time() - start_time,
                "error": str(e)
            }
    
    async def test_api_modes(self):
        """测试所有API模式"""
        print("\n📡 测试API服务...")
        
        async with aiohttp.ClientSession() as session:
            # 健康检查
            try:
                async with session.get(f"{API_URL}/health") as response:
                    health = await response.json()
                    print(f"✅ API服务健康: {health['status']}")
            except:
                print("❌ API服务不可用")
                return
            
            # 测试每种模式
            for mode in ["fast", "normal", "deep"]:
                print(f"\n🔍 测试API {mode.upper()}模式...")
                
                for i, question in enumerate(self.test_questions):
                    print(f"  [{i+1}/{len(self.test_questions)}] {question['id'][:30]}...", end='', flush=True)
                    
                    result = await self.test_api_search(session, question, mode)
                    self.api_results[mode].append(result)
                    
                    if result["success"]:
                        print(f" ✅ {result['time']:.1f}s")
                    else:
                        print(f" ❌ {result['error']}")
                    
                    # 避免过载
                    await asyncio.sleep(1)
    
    async def test_mcp_modes(self):
        """测试所有MCP模式"""
        if not Client:
            print("\n⏭️  跳过MCP测试（未安装FastMCP）")
            return
            
        print("\n🔌 测试MCP服务...")
        
        try:
            async with Client(MCP_URL) as client:
                # 健康检查
                await client.ping()
                print("✅ MCP服务连接成功")
                
                # 测试每种模式
                for mode in ["fast", "normal", "deep"]:
                    print(f"\n🔍 测试MCP {mode.upper()}模式...")
                    
                    for i, question in enumerate(self.test_questions):
                        print(f"  [{i+1}/{len(self.test_questions)}] {question['id'][:30]}...", end='', flush=True)
                        
                        result = await self.test_mcp_search(client, question, mode)
                        self.mcp_results[mode].append(result)
                        
                        if result["success"]:
                            print(f" ✅ {result['time']:.1f}s")
                        else:
                            print(f" ❌ {result.get('error', 'Unknown')}")
                        
                        # 避免过载
                        await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ MCP连接失败: {e}")
    
    def analyze_results(self, results: Dict[str, List], service_type: str) -> Dict[str, Any]:
        """分析测试结果"""
        analysis = {}
        
        for mode, mode_results in results.items():
            successful = [r for r in mode_results if r["success"]]
            failed = [r for r in mode_results if not r["success"]]
            
            if successful:
                times = [r["time"] for r in successful]
                answer_lengths = [r["answer_length"] for r in successful]
                sources_counts = [r["sources_count"] for r in successful]
                
                analysis[mode] = {
                    "success_rate": len(successful) / len(mode_results) * 100,
                    "failed_count": len(failed),
                    "avg_time": statistics.mean(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "std_time": statistics.stdev(times) if len(times) > 1 else 0,
                    "avg_answer_length": statistics.mean(answer_lengths),
                    "avg_sources": statistics.mean(sources_counts),
                    "failures": [{"id": f["question_id"], "error": f.get("error", "Unknown")} for f in failed]
                }
                
                # API特有统计
                if service_type == "API" and "iterations" in successful[0]:
                    iterations = [r["iterations"] for r in successful]
                    analysis[mode]["avg_iterations"] = statistics.mean(iterations)
            else:
                analysis[mode] = {
                    "success_rate": 0,
                    "failed_count": len(failed),
                    "failures": [{"id": f["question_id"], "error": f.get("error", "Unknown")} for f in failed]
                }
        
        return analysis
    
    def generate_report(self):
        """生成测试报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 分析结果
        api_analysis = self.analyze_results(self.api_results, "API")
        mcp_analysis = self.analyze_results(self.mcp_results, "MCP") if Client else {}
        
        # 生成报告
        report = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "question_count": len(self.test_questions),
                "modes_tested": ["fast", "normal", "deep"],
                "api_url": API_URL,
                "mcp_url": MCP_URL if Client else "N/A"
            },
            "api_results": {
                "raw_data": self.api_results,
                "analysis": api_analysis
            },
            "mcp_results": {
                "raw_data": self.mcp_results if Client else {},
                "analysis": mcp_analysis
            }
        }
        
        # 保存详细报告
        report_file = f"mode_test_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        print("\n" + "="*80)
        print("📊 测试报告摘要")
        print("="*80)
        
        # API结果
        print("\n🌐 API测试结果:")
        print(f"{'模式':<10} {'成功率':<10} {'平均时间':<12} {'最快/最慢':<20} {'平均答案长度':<15}")
        print("-"*77)
        
        for mode in ["fast", "normal", "deep"]:
            if mode in api_analysis and api_analysis[mode]["success_rate"] > 0:
                a = api_analysis[mode]
                print(f"{mode:<10} {a['success_rate']:<10.1f}% {a['avg_time']:<12.1f}s "
                      f"{a['min_time']:.1f}s/{a['max_time']:.1f}s{'':<10} {a['avg_answer_length']:<15.0f}")
            else:
                print(f"{mode:<10} {'失败':<10} {'-':<12} {'-':<20} {'-':<15}")
        
        # MCP结果
        if Client and mcp_analysis:
            print("\n🔌 MCP测试结果:")
            print(f"{'模式':<10} {'成功率':<10} {'平均时间':<12} {'最快/最慢':<20} {'平均答案长度':<15}")
            print("-"*77)
            
            for mode in ["fast", "normal", "deep"]:
                if mode in mcp_analysis and mcp_analysis[mode]["success_rate"] > 0:
                    a = mcp_analysis[mode]
                    print(f"{mode:<10} {a['success_rate']:<10.1f}% {a['avg_time']:<12.1f}s "
                          f"{a['min_time']:.1f}s/{a['max_time']:.1f}s{'':<10} {a['avg_answer_length']:<15.0f}")
                else:
                    print(f"{mode:<10} {'失败':<10} {'-':<12} {'-':<20} {'-':<15}")
        
        # 性能对比
        print("\n📈 性能对比分析:")
        
        # Fast vs Normal
        if "fast" in api_analysis and "normal" in api_analysis:
            if api_analysis["fast"]["success_rate"] > 0 and api_analysis["normal"]["success_rate"] > 0:
                speed_ratio = api_analysis["normal"]["avg_time"] / api_analysis["fast"]["avg_time"]
                quality_ratio = api_analysis["fast"]["avg_answer_length"] / api_analysis["normal"]["avg_answer_length"]
                print(f"  • Fast模式比Normal快 {speed_ratio:.1f}x")
                print(f"  • Fast模式答案长度是Normal的 {quality_ratio:.1%}")
        
        # 失败分析
        print("\n❌ 失败分析:")
        for service, analysis in [("API", api_analysis), ("MCP", mcp_analysis)]:
            if analysis:
                for mode, data in analysis.items():
                    if data.get("failed_count", 0) > 0:
                        print(f"  • {service} {mode}模式: {data['failed_count']}个失败")
                        for failure in data["failures"][:3]:  # 只显示前3个
                            print(f"    - {failure['id'][:30]}: {failure['error']}")
        
        print(f"\n💾 详细报告已保存: {report_file}")
        
        return report

async def main():
    """主测试函数"""
    print("🧪 FlashSearch 综合模式测试")
    print("="*80)
    print(f"📋 测试配置:")
    print(f"  • 问题数量: {TEST_QUESTION_COUNT}个/模式")
    print(f"  • 测试模式: fast, normal, deep")
    print(f"  • 测试服务: API + MCP")
    
    tester = SearchModeTester()
    
    # 加载测试问题
    await tester.load_test_questions()
    
    # 测试API
    await tester.test_api_modes()
    
    # 测试MCP
    await tester.test_mcp_modes()
    
    # 生成报告
    report = tester.generate_report()
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚡ 测试被中断")
    except Exception as e:
        print(f"\n💥 测试错误: {e}")
        import traceback
        traceback.print_exc()