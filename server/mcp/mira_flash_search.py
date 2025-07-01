#!/usr/bin/env python3
"""
Mira FlashSearch MCP Server
基于FastMCP构建的FlashSearch v2.5.0 MCP服务器
MCP Name: mira_flash_search
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from fastmcp import FastMCP, Context
    from pydantic import Field
    from typing import Annotated
except ImportError as e:
    print(f"❌ FastMCP 未安装: {e}")
    print("请安装: pip install fastmcp")
    sys.exit(1)

from src.core.flash_s3_enhanced import flash_s3_enhanced
from src.core.enhanced_time_aware import EnhancedTimeAware

# 创建MCP服务器实例
mcp = FastMCP(
    name="mira_flash_search",
    instructions="""
    Mira FlashSearch v2.5.0 - 增强搜索引擎 MCP服务器
    
    提供以下能力:
    - 智能搜索: 使用Google关键词优化和时间感知算子
    - 多领域支持: 新闻、财经、技术、学术、政策等领域
    - 实时搜索: 获取最新信息和数据
    - 时间感知: 理解相对时间词("最近"、"本季度"等)
    - Langfuse追踪: 完整的搜索链路追踪
    
    使用flash_search工具进行搜索，search_analyze工具进行搜索分析。
    """
)

# 全局统计
server_stats = {
    "total_requests": 0,
    "successful_searches": 0,
    "failed_searches": 0,
    "avg_response_time": 0.0,
    "start_time": datetime.now().isoformat()
}

@mcp.tool(
    name="flash_search",
    description="使用FlashSearch v2.5.0引擎进行智能搜索，支持Google关键词优化和时间感知"
)
async def flash_search_tool(
    query: Annotated[str, Field(description="搜索查询，支持中英文混合", min_length=1, max_length=1000)],
    domain: Annotated[Optional[str], Field(description="搜索领域: news, finance, tech, academic, policy")] = None,
    enable_langfuse: Annotated[bool, Field(description="是否启用Langfuse追踪")] = True,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    执行FlashSearch智能搜索
    
    特点:
    - Google关键词优化: 自动提取3-8个核心关键词
    - 时间感知算子: 理解"最近"、"本季度"等相对时间
    - 多领域增强: 针对不同领域优化搜索策略
    - 权威来源: 整合中美英权威媒体和官方网站
    """
    global server_stats
    start_time = asyncio.get_event_loop().time()
    server_stats["total_requests"] += 1
    
    if ctx:
        await ctx.info(f"🔍 开始FlashSearch搜索: {query[:50]}...")
        await ctx.report_progress(progress=10, total=100)
    
    try:
        # 执行搜索
        # 注意：flash_s3_enhanced只接受question参数，domain和langfuse在内部处理
        result = await flash_s3_enhanced(question=query)
        
        if ctx:
            await ctx.report_progress(progress=90, total=100)
        
        # 计算响应时间
        response_time = asyncio.get_event_loop().time() - start_time
        server_stats["successful_searches"] += 1
        server_stats["avg_response_time"] = (
            (server_stats["avg_response_time"] * (server_stats["successful_searches"] - 1) + response_time) 
            / server_stats["successful_searches"]
        )
        
        # 构建返回数据
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        stats = result.get("stats", {})
        
        if ctx:
            await ctx.report_progress(progress=100, total=100)
            await ctx.info(f"✅ 搜索完成: {len(answer)}字符答案, {len(sources)}个来源")
        
        # FastMCP 2.9.2 直接返回结构化数据
        return {
            "success": True,
            "query": query,
            "domain": domain,
            "answer": answer,
            "sources_count": len(sources),
            "sources": sources[:3],  # 只返回前3个来源以减少数据量
            "stats": {
                **stats,
                "response_time": round(response_time, 2),
                "mcp_version": "2.5.0"
            },
            "trace_id": result.get("trace_id"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        server_stats["failed_searches"] += 1
        
        if ctx:
            await ctx.error(f"❌ 搜索失败: {str(e)}")
        
        return {
            "error": str(e),
            "query": query,
            "success": False,
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool(
    name="search_analyze",
    description="分析搜索查询，提供关键词优化和时间感知建议"
)
async def search_analyze_tool(
    query: Annotated[str, Field(description="要分析的搜索查询")],
    ctx: Context = None
) -> Dict[str, Any]:
    """
    分析搜索查询，提供优化建议
    """
    if ctx:
        await ctx.info(f"🔍 分析查询: {query}")
    
    try:
        # 使用时间感知组件分析
        time_aware = EnhancedTimeAware()
        
        # 分析时间相关内容
        time_ranges = time_aware.parse_relative_time(query)
        time_operators = []
        
        if time_ranges:
            time_operators = time_aware.generate_search_operators(time_ranges)
        
        # 分析领域
        suggested_domain = suggest_domain_from_query(query)
        
        # 提取关键词建议
        keywords = extract_keywords_suggestion(query)
        
        analysis = {
            "original_query": query,
            "suggested_domain": suggested_domain,
            "time_awareness": {
                "has_time_references": len(time_ranges) > 0,
                "time_ranges": time_ranges,
                "suggested_operators": time_operators
            },
            "keywords": {
                "extracted": keywords,
                "count": len(keywords)
            },
            "optimization_tips": generate_optimization_tips(query, suggested_domain, time_ranges),
            "timestamp": datetime.now().isoformat()
        }
        
        if ctx:
            await ctx.info(f"✅ 分析完成: 领域={suggested_domain}, 关键词={len(keywords)}个")
        
        return analysis
        
    except Exception as e:
        if ctx:
            await ctx.error(f"❌ 分析失败: {str(e)}")
        
        return {
            "error": str(e),
            "query": query,
            "timestamp": datetime.now().isoformat()
        }

@mcp.resource("mcp://server/stats")
async def get_server_stats(ctx: Context) -> Dict[str, Any]:
    """获取MCP服务器统计信息"""
    await ctx.info("📊 获取服务器统计信息")
    
    current_time = datetime.now()
    uptime = current_time - datetime.fromisoformat(server_stats["start_time"])
    
    return {
        **server_stats,
        "current_time": current_time.isoformat(),
        "uptime_seconds": uptime.total_seconds(),
        "uptime_formatted": str(uptime),
        "success_rate": (
            server_stats["successful_searches"] / max(server_stats["total_requests"], 1) * 100
        ),
        "server_info": {
            "name": "mira_flash_search",
            "version": "2.5.0",
            "features": [
                "Google关键词优化",
                "时间感知算子",
                "多领域搜索",
                "Langfuse集成",
                "实时追踪"
            ]
        }
    }

@mcp.resource("mcp://server/config")
async def get_server_config(ctx: Context) -> Dict[str, Any]:
    """获取服务器配置信息"""
    return {
        "server_name": "mira_flash_search",
        "version": "2.5.0",
        "capabilities": {
            "search_domains": ["news", "finance", "tech", "academic", "policy"],
            "time_awareness": True,
            "google_optimization": True,
            "langfuse_integration": True,
            "multilingual": True
        },
        "limits": {
            "max_query_length": 1000,
            "max_results": 50,
            "timeout_seconds": 1800
        },
        "updated_at": datetime.now().isoformat()
    }

def suggest_domain_from_query(query: str) -> Optional[str]:
    """根据查询建议搜索领域"""
    query_lower = query.lower()
    
    # 新闻关键词
    if any(word in query_lower for word in ["新闻", "最新", "报道", "事件", "突发", "news", "breaking"]):
        return "news"
    
    # 财经关键词  
    if any(word in query_lower for word in ["财报", "股价", "投资", "金融", "经济", "finance", "stock"]):
        return "finance"
    
    # 技术关键词
    if any(word in query_lower for word in ["技术", "编程", "算法", "开发", "api", "tech", "programming"]):
        return "tech"
    
    # 学术关键词
    if any(word in query_lower for word in ["研究", "论文", "学术", "分析", "报告", "research", "paper"]):
        return "academic"
    
    # 政策关键词
    if any(word in query_lower for word in ["政策", "法规", "政府", "官方", "法律", "policy", "government"]):
        return "policy"
    
    return None

def extract_keywords_suggestion(query: str) -> List[str]:
    """提取关键词建议"""
    # 简单的关键词提取逻辑
    import re
    
    # 移除标点符号，分割单词
    words = re.findall(r'\b\w+\b', query.lower())
    
    # 过滤停用词
    stop_words = {"的", "是", "在", "了", "和", "与", "对", "为", "有", "从", "到", "以", 
                  "the", "is", "in", "and", "or", "to", "of", "for", "with", "by"}
    
    keywords = [word for word in words if word not in stop_words and len(word) > 1]
    
    # 返回前8个关键词
    return keywords[:8]

def generate_optimization_tips(query: str, domain: Optional[str], time_ranges: List) -> List[str]:
    """生成优化建议"""
    tips = []
    
    if domain:
        tips.append(f"✅ 已识别领域: {domain}，将应用专门的搜索策略")
    else:
        tips.append("💡 建议在查询中添加领域关键词以获得更精准结果")
    
    if time_ranges:
        tips.append("✅ 检测到时间相关表达，将应用时间感知搜索算子")
    else:
        tips.append("💡 如需特定时间范围的信息，可添加如'最近'、'2024年'等时间词")
    
    if len(query) < 10:
        tips.append("💡 查询较短，建议添加更多描述性关键词")
    
    if not any(c.isalpha() for c in query):
        tips.append("⚠️ 查询中缺少字母，建议添加描述性词汇")
    
    return tips

# 健康检查工具
@mcp.tool(
    name="health_check",
    description="检查MCP服务器健康状态"
)
async def health_check_tool(ctx: Context = None) -> Dict[str, Any]:
    """健康检查"""
    if ctx:
        await ctx.info("🏥 执行健康检查")
    
    return {
        "status": "healthy",
        "server": "mira_flash_search",
        "version": "2.5.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": (datetime.now() - datetime.fromisoformat(server_stats["start_time"])).total_seconds(),
        "stats": server_stats
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mira FlashSearch MCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "http", "sse"], 
                       help="MCP传输协议 (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP传输主机 (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8060, help="HTTP传输端口 (default: 8060)")
    parser.add_argument("--log-level", default="info", help="日志级别 (default: info)")
    
    args = parser.parse_args()
    
    print(f"🚀 启动 Mira FlashSearch MCP Server v2.5.0")
    print(f"📡 传输协议: {args.transport}")
    
    if args.transport == "http":
        print(f"🌐 HTTP地址: http://{args.host}:{args.port}/mcp/")
        mcp.run(
            transport="http",
            host=args.host,
            port=args.port
        )
    elif args.transport == "sse":
        print(f"🌐 SSE地址: http://{args.host}:{args.port}/sse/")
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port
        )
    else:
        print(f"📟 STDIO模式 (适用于本地客户端)")
        mcp.run(transport="stdio")