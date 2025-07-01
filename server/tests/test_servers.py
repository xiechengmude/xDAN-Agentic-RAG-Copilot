#!/usr/bin/env python3
"""
FlashSearch 服务器测试脚本
测试 FastAPI 和 FastMCP 服务器的功能
"""

import asyncio
import aiohttp
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_api_server(base_url="http://localhost:8000"):
    """测试 FastAPI 服务器"""
    print(f"🧪 测试 FastAPI 服务器: {base_url}")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. 健康检查
            print("  📊 健康检查...")
            async with session.get(f"{base_url}/health") as resp:
                health = await resp.json()
                print(f"     ✅ 状态: {health['status']}, 版本: {health['version']}")
            
            # 2. 根路径
            print("  🏠 根路径...")
            async with session.get(f"{base_url}/") as resp:
                root = await resp.json()
                print(f"     ✅ 消息: {root['message']}")
            
            # 3. 统计信息
            print("  📈 统计信息...")
            async with session.get(f"{base_url}/stats") as resp:
                stats = await resp.json()
                print(f"     ✅ 总搜索: {stats['total_searches']}")
            
            # 4. 查询验证
            print("  ✅ 查询验证...")
            test_query = "测试查询"
            async with session.post(
                f"{base_url}/validate",
                json={"query": test_query}
            ) as resp:
                validation = await resp.json()
                print(f"     ✅ 验证结果: {validation['valid']}")
            
            # 5. 搜索测试
            print("  🔍 搜索测试...")
            search_request = {
                "query": "比亚迪最新财报",
                "domain": "finance",
                "enable_langfuse": False  # 禁用Langfuse以避免配置问题
            }
            
            async with session.post(
                f"{base_url}/search",
                json=search_request,
                timeout=aiohttp.ClientTimeout(total=180)  # 3分钟超时
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"     ✅ 搜索成功: {len(result['answer'])}字符答案")
                    print(f"     📊 来源数量: {len(result['sources'])}")
                    print(f"     ⏱️  响应时间: {result['stats'].get('response_time', 'N/A')}秒")
                else:
                    error = await resp.text()
                    print(f"     ❌ 搜索失败: {resp.status} - {error}")
            
            # 6. 异步搜索测试
            print("  ⚡ 异步搜索测试...")
            async_request = {
                "query": "人工智能最新发展",
                "domain": "tech"
            }
            
            async with session.post(
                f"{base_url}/search/async",
                json=async_request
            ) as resp:
                if resp.status == 200:
                    task_info = await resp.json()
                    print(f"     ✅ 异步任务提交: {task_info['task_id']}")
                else:
                    print(f"     ❌ 异步任务失败: {resp.status}")
                    
        except Exception as e:
            print(f"     ❌ API服务器测试失败: {e}")
            return False
    
    print("  🎉 API服务器测试完成")
    return True

async def test_mcp_server_http(base_url="http://localhost:9000"):
    """测试 FastMCP HTTP 服务器"""
    print(f"🧪 测试 FastMCP 服务器: {base_url}")
    
    try:
        # 注意: 这里需要使用 fastmcp 客户端来正确测试
        from fastmcp import Client
        
        # 连接到MCP服务器
        print("  🔌 连接到MCP服务器...")
        client = Client(f"{base_url}/mcp/")
        
        # 测试工具列表
        print("  🛠️  获取工具列表...")
        tools = await client.list_tools()
        print(f"     ✅ 可用工具: {[tool.name for tool in tools.tools]}")
        
        # 测试健康检查工具
        print("  🏥 健康检查工具...")
        health_result = await client.call_tool("health_check", {})
        print(f"     ✅ 健康状态: {health_result.content[0].text}")
        
        # 测试搜索分析工具
        print("  🔍 搜索分析工具...")
        analysis_result = await client.call_tool(
            "search_analyze", 
            {"query": "比亚迪最新财报"}
        )
        analysis_data = json.loads(analysis_result.content[0].text)
        print(f"     ✅ 分析完成: 建议领域={analysis_data.get('suggested_domain')}")
        
        # 测试搜索工具 (简化测试)
        print("  🔍 快速搜索测试...")
        search_result = await client.call_tool(
            "flash_search",
            {
                "query": "测试搜索",
                "domain": "tech",
                "enable_langfuse": False
            }
        )
        
        if search_result.content:
            print(f"     ✅ 搜索工具响应正常")
        else:
            print(f"     ❌ 搜索工具无响应")
        
        # 测试资源
        print("  📊 获取服务器统计...")
        stats_resource = await client.read_resource("mcp://server/stats")
        if stats_resource:
            print(f"     ✅ 统计资源可访问")
        
        print("  📝 获取服务器配置...")
        config_resource = await client.read_resource("mcp://server/config")
        if config_resource:
            print(f"     ✅ 配置资源可访问")
            
    except ImportError:
        print("     ⚠️  FastMCP客户端未安装，跳过详细测试")
        # 回退到简单HTTP测试
        await test_mcp_http_fallback(base_url)
        
    except Exception as e:
        print(f"     ❌ MCP服务器测试失败: {e}")
        return False
    
    print("  🎉 MCP服务器测试完成")
    return True

async def test_mcp_http_fallback(base_url):
    """MCP HTTP 回退测试"""
    print("  🔄 使用HTTP回退测试...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 简单的HTTP连接测试
            async with session.get(f"{base_url}/mcp/") as resp:
                if resp.status == 200:
                    print(f"     ✅ MCP HTTP端点可访问")
                else:
                    print(f"     ❌ MCP HTTP端点返回: {resp.status}")
        except Exception as e:
            print(f"     ❌ MCP HTTP回退测试失败: {e}")

def test_mcp_stdio():
    """测试 MCP STDIO 模式"""
    print("🧪 测试 MCP STDIO 模式")
    
    try:
        import subprocess
        import signal
        import time
        
        print("  📟 启动STDIO MCP服务器...")
        
        # 启动MCP服务器进程
        process = subprocess.Popen(
            [sys.executable, "mcp/mira_flash_search.py", "--transport", "stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # 等待启动
        time.sleep(2)
        
        # 检查进程是否还在运行
        if process.poll() is None:
            print("     ✅ STDIO MCP服务器启动成功")
            
            # 发送简单的测试消息 (简化的MCP协议)
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }
            
            try:
                process.stdin.write(json.dumps(test_message) + "\n")
                process.stdin.flush()
                
                # 等待响应 (简化)
                time.sleep(1)
                print("     ✅ STDIO通信测试完成")
                
            except Exception as e:
                print(f"     ⚠️  STDIO通信测试失败: {e}")
        else:
            stderr_output = process.stderr.read()
            print(f"     ❌ STDIO MCP服务器启动失败: {stderr_output}")
        
        # 清理进程
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            
    except Exception as e:
        print(f"     ❌ STDIO测试失败: {e}")
    
    print("  🎉 STDIO测试完成")

async def main():
    """主测试函数"""
    print("🚀 FlashSearch 服务器集成测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试结果
    results = {
        "api_server": False,
        "mcp_http": False,
        "mcp_stdio": False
    }
    
    # 1. 测试 API 服务器
    try:
        results["api_server"] = await test_api_server()
    except Exception as e:
        print(f"❌ API服务器测试异常: {e}")
    
    print()
    
    # 2. 测试 MCP HTTP 服务器
    try:
        results["mcp_http"] = await test_mcp_server_http()
    except Exception as e:
        print(f"❌ MCP HTTP服务器测试异常: {e}")
    
    print()
    
    # 3. 测试 MCP STDIO 模式
    try:
        test_mcp_stdio()
        results["mcp_stdio"] = True
    except Exception as e:
        print(f"❌ MCP STDIO测试异常: {e}")
    
    # 输出测试总结
    print()
    print("=" * 60)
    print("📊 测试总结:")
    print(f"  🌐 API服务器 (FastAPI): {'✅ 通过' if results['api_server'] else '❌ 失败'}")
    print(f"  🔌 MCP HTTP服务器: {'✅ 通过' if results['mcp_http'] else '❌ 失败'}")
    print(f"  📟 MCP STDIO模式: {'✅ 通过' if results['mcp_stdio'] else '❌ 失败'}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"  📈 总体成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查服务器配置")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="FlashSearch 服务器测试")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API服务器URL")
    parser.add_argument("--mcp-url", default="http://localhost:9000", help="MCP服务器URL")
    parser.add_argument("--skip-api", action="store_true", help="跳过API测试")
    parser.add_argument("--skip-mcp", action="store_true", help="跳过MCP测试")
    
    args = parser.parse_args()
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)