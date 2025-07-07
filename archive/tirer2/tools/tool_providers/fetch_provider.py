"""
网页爬取工具提供者
整合 FireCrawl 爬取工具
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool
from .base_provider import BaseToolProvider

import logging
logger = logging.getLogger(__name__)


class FetchProvider(BaseToolProvider):
    """网页爬取工具提供者"""
    
    def __init__(self):
        super().__init__("Fetch")
        self.firecrawl_client = None
        
    async def initialize(self) -> bool:
        """初始化爬取工具"""
        try:
            # 检查环境变量
            firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
            
            # 初始化 FireCrawl
            if firecrawl_key:
                try:
                    from ....tools.local.firecrawl_client import FireCrawlAsyncClient
                    self.firecrawl_client = FireCrawlAsyncClient(api_key=firecrawl_key)
                    logger.info("FireCrawl client initialized")
                except ImportError as e:
                    logger.warning(f"Failed to import FireCrawl client: {e}")
            
            # 创建工具
            self.tools = await self._create_tools()
            self.initialized = True
            
            logger.info(f"FetchProvider initialized with {len(self.tools)} tools")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize FetchProvider: {e}")
            return False
    
    async def _create_tools(self) -> List[BaseTool]:
        """创建爬取工具"""
        tools = []
        
        # FireCrawl 爬取工具
        if self.firecrawl_client:
            @tool
            async def firecrawl_scrape(url: str, formats: List[str] = None) -> Dict[str, Any]:
                """
                使用 FireCrawl 爬取网页内容
                
                Args:
                    url: 要爬取的URL
                    formats: 返回格式列表 (markdown, html, json)
                """
                if formats is None:
                    formats = ['markdown']
                    
                try:
                    async with self.firecrawl_client as client:
                        result = await client.scrape_url(url, formats=formats)
                        return result
                except Exception as e:
                    logger.error(f"FireCrawl scrape failed: {e}")
                    return {"success": False, "error": str(e), "url": url}
            
            @tool
            async def firecrawl_batch_scrape(urls: List[str], formats: List[str] = None) -> Dict[str, Any]:
                """
                使用 FireCrawl 批量爬取多个网页
                
                Args:
                    urls: 要爬取的URL列表
                    formats: 返回格式列表
                """
                if formats is None:
                    formats = ['markdown']
                    
                try:
                    async with self.firecrawl_client as client:
                        results = await client.batch_scrape(urls, formats=formats)
                        return {
                            "success": True,
                            "results": results,
                            "total_urls": len(urls)
                        }
                except Exception as e:
                    logger.error(f"FireCrawl batch scrape failed: {e}")
                    return {"success": False, "error": str(e), "urls": urls}
            
            tools.extend([firecrawl_scrape, firecrawl_batch_scrape])
        
        # 如果没有实际工具，创建模拟工具
        if not tools:
            @tool
            async def mock_scrape(url: str) -> Dict[str, Any]:
                """
                模拟网页爬取工具（用于测试）
                
                Args:
                    url: 要爬取的URL
                """
                return {
                    "success": True,
                    "url": url,
                    "data": {
                        "markdown": f"# 模拟爬取结果\n\n这是从 {url} 爬取的模拟内容。在实际环境中，这里会显示真实的网页内容。\n\n## 内容摘要\n\n模拟的网页内容，包含了关键信息和结构化数据。",
                        "title": f"模拟页面 - {url}",
                        "description": "这是一个模拟的网页描述"
                    },
                    "mock": True
                }
            
            tools.append(mock_scrape)
            logger.warning("Using mock fetch tools - no real crawling APIs configured")
        
        return tools
    
    async def get_tools(self) -> List[BaseTool]:
        """获取爬取工具列表"""
        if not self.initialized:
            await self.initialize()
        return self.tools
    
    async def cleanup(self):
        """清理爬取客户端"""
        if self.firecrawl_client:
            try:
                await self.firecrawl_client.__aexit__(None, None, None)
            except:
                pass