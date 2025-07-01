#!/usr/bin/env python3
"""
Quick Test Script for API and MCP
快速测试API和MCP服务
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fastmcp import Client
except ImportError as e:
    print(f"❌ FastMCP Client 未安装: {e}")
    sys.exit(1)

API_URL = "http://127.0.0.1:8060"
MCP_URL = "http://127.0.0.1:9060/sse/"

async def test_api():
    """测试API服务"""
    print("🔗 测试API服务...")
    
    async with aiohttp.ClientSession() as session:
        # 健康检查
        async with session.get(f"{API_URL}/health") as response:
            health = await response.json()
            print(f"✅ API健康: {health['status']}")
        
        # 快速搜索测试
        search_data = {
            "query": "人工智能发展趋势",
            "enable_langfuse": False
        }
        
        print("🔍 执行API搜索测试...")
        async with session.post(
            f"{API_URL}/search",
            json=search_data,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            result = await response.json()
            
            if result.get("success"):
                answer_len = len(result.get("answer", ""))
                sources_count = len(result.get("sources", []))
                response_time = result.get("stats", {}).get("response_time", 0)
                print(f"✅ API搜索成功: {answer_len}字符, {sources_count}来源, {response_time:.1f}s")
                return True
            else:
                print(f"❌ API搜索失败: {result}")
                return False

async def test_mcp():
    """测试MCP服务"""
    print("🔗 测试MCP服务...")
    
    try:
        async with Client(MCP_URL) as client:
            # 健康检查
            await client.ping()
            print("✅ MCP连接成功")
            
            # 列出工具
            tools = await client.list_tools()
            print(f"✅ MCP工具: {len(tools)}个")
            
            # 测试健康检查工具
            health_result = await client.call_tool("health_check", {})
            if health_result:
                print("✅ MCP健康检查工具正常")
            
            # 快速搜索测试
            print("🔍 执行MCP搜索测试...")
            search_result = await client.call_tool("flash_search", {
                "query": "人工智能发展趋势",
                "enable_langfuse": False
            })
            
            if search_result and len(search_result) > 0:
                content = search_result[0]
                if hasattr(content, 'text'):
                    data = json.loads(content.text)
                    if data.get("success"):
                        answer_len = len(data.get("answer", ""))
                        sources_count = data.get("sources_count", 0)
                        response_time = data.get("stats", {}).get("response_time", 0)
                        print(f"✅ MCP搜索成功: {answer_len}字符, {sources_count}来源, {response_time:.1f}s")
                        return True
                    else:
                        print(f"❌ MCP搜索失败: {data.get('error')}")
                        return False
            
            print("❌ MCP搜索无响应")
            return False
            
    except Exception as e:
        print(f"❌ MCP测试失败: {e}")
        return False

async def main():
    """主函数"""
    print("🧪 FlashSearch 快速验证测试")
    print("="*50)
    
    # 测试API
    api_success = await test_api()
    print()
    
    # 测试MCP
    mcp_success = await test_mcp()
    print()
    
    # 结果总结
    print("="*50)
    print("📋 测试结果总结")
    print(f"API服务: {'✅ 通过' if api_success else '❌ 失败'}")
    print(f"MCP服务: {'✅ 通过' if mcp_success else '❌ 失败'}")
    
    if api_success and mcp_success:
        print("🎉 所有服务正常运行！")
        return True
    else:
        print("⚠️ 部分服务存在问题")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚡ 测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试错误: {e}")
        sys.exit(1)