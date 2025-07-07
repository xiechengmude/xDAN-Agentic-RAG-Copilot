"""
搜索工具提供者
整合 BrightData 和 Tavily 搜索工具
"""

import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool
from .base_provider import BaseToolProvider

import logging
logger = logging.getLogger(__name__)


class SearchProvider(BaseToolProvider):
    """搜索工具提供者"""
    
    def __init__(self):
        super().__init__("Search")
        self.brightdata_client = None
        self.tavily_client = None
        
    async def initialize(self) -> bool:
        """初始化搜索工具"""
        try:
            # 检查环境变量
            brightdata_key = os.getenv("BRIGHTDATA_API_KEY")
            tavily_key = os.getenv("TAVILY_SEARCH_API_KEY") or os.getenv("TAVILY_API_KEY")
            
            # 初始化 BrightData
            if brightdata_key:
                try:
                    import sys
                    from pathlib import Path
                    sys.path.append(str(Path(__file__).parent.parent.parent.parent))
                    from src.core.tools.local.brightdata_client import BrightDataAsyncClient
                    self.brightdata_client = BrightDataAsyncClient(api_key=brightdata_key)
                    logger.info("BrightData client initialized successfully")
                except ImportError as e:
                    logger.warning(f"Failed to import BrightData client: {e}")
                    # Use mock client
                    self.brightdata_client = None
            
            # 初始化 Tavily
            if tavily_key:
                try:
                    from tavily import TavilyClient
                    self.tavily_client = TavilyClient(api_key=tavily_key)
                    logger.info("Tavily client initialized")
                except ImportError as e:
                    logger.warning(f"Failed to import Tavily client: {e}")
                    # Try alternative import
                    try:
                        from tavily import Client as TavilyClient
                        self.tavily_client = TavilyClient(api_key=tavily_key)
                        logger.info("Tavily client initialized with alternative import")
                    except ImportError:
                        logger.warning("Tavily not available - install with: pip install tavily-python")
            
            # 创建工具
            self.tools = await self._create_tools()
            self.initialized = True
            
            logger.info(f"SearchProvider initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SearchProvider: {e}")
            return False
    
    async def _create_tools(self) -> List[BaseTool]:
        """创建搜索工具"""
        tools = []
        
        # BrightData 搜索工具
        if self.brightdata_client:
            @tool
            async def brightdata_search(query: str, search_type: str = "web", num_results: int = 10, time_range: str = "any") -> Dict[str, Any]:
                """
                使用 BrightData 进行时间感知的网络搜索
                
                Args:
                    query: 搜索查询
                    search_type: 搜索类型 (web, news, academic, images, videos)
                    num_results: 结果数量
                    time_range: 时间范围 (latest, today, week, month, any)
                """
                try:
                    # 添加时间感知的查询修饰
                    time_modified_query = query
                    if time_range == "latest":
                        time_modified_query = f"{query} 最新"
                    elif time_range == "today":
                        time_modified_query = f"{query} 今日"
                    elif time_range == "week":
                        time_modified_query = f"{query} 本周"
                    elif time_range == "month":
                        time_modified_query = f"{query} 本月"
                    
                    async with self.brightdata_client as client:
                        result = await client.search(
                            query=time_modified_query,
                            search_type=search_type,
                            num_results=num_results
                        )
                        
                        # 添加时间感知元数据
                        if result.get("success", True):
                            result["time_range"] = time_range
                            result["time_aware_query"] = time_modified_query
                            result["search_timestamp"] = datetime.now().isoformat()
                        
                        return result
                except Exception as e:
                    logger.error(f"BrightData search failed: {e}")
                    return {"success": False, "error": str(e)}
            
            tools.append(brightdata_search)
        
        # Tavily 搜索工具
        if self.tavily_client:
            @tool
            async def tavily_search(query: str, search_depth: str = "basic", max_results: int = 10, time_range: str = "any") -> Dict[str, Any]:
                """
                使用 Tavily 进行时间感知的AI驱动搜索
                
                Args:
                    query: 搜索查询
                    search_depth: 搜索深度 (basic, advanced)
                    max_results: 最大结果数
                    time_range: 时间范围 (latest, today, week, month, any)
                """
                try:
                    # 添加时间感知的查询修饰
                    time_modified_query = query
                    if time_range == "latest":
                        time_modified_query = f"{query} latest news"
                    elif time_range == "today":
                        time_modified_query = f"{query} today"
                    elif time_range == "week":
                        time_modified_query = f"{query} this week"
                    elif time_range == "month":
                        time_modified_query = f"{query} this month"
                    
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: self.tavily_client.search(
                            query=time_modified_query,
                            search_depth=search_depth,
                            max_results=max_results
                        )
                    )
                    
                    return {
                        "success": True,
                        "results": result.get("results", []),
                        "query": query,
                        "time_range": time_range,
                        "time_aware_query": time_modified_query,
                        "search_timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    logger.error(f"Tavily search failed: {e}")
                    return {"success": False, "error": str(e)}
            
            tools.append(tavily_search)
        
        # 如果没有实际工具，创建模拟工具
        if not tools:
            @tool
            async def mock_search(query: str, search_type: str = "web") -> Dict[str, Any]:
                """
                模拟搜索工具（用于测试）
                
                Args:
                    query: 搜索查询
                    search_type: 搜索类型
                """
                return {
                    "success": True,
                    "query": query,
                    "results": [
                        {
                            "title": f"模拟搜索结果 for '{query}'",
                            "url": "https://example.com/mock-result",
                            "snippet": f"这是针对查询 '{query}' 的模拟搜索结果。在实际环境中，这里会显示真实的搜索结果。",
                            "position": 1
                        }
                    ],
                    "mock": True
                }
            
            tools.append(mock_search)
            logger.warning("Using mock search tools - no real search APIs configured")
        
        return tools
    
    async def get_tools(self) -> List[BaseTool]:
        """获取搜索工具列表"""
        if not self.initialized:
            await self.initialize()
        return self.tools
    
    async def cleanup(self):
        """清理搜索客户端"""
        if self.brightdata_client:
            try:
                await self.brightdata_client.__aexit__(None, None, None)
            except:
                pass