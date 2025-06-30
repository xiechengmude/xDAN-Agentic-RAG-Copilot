"""
搜索智能体 - 专门负责信息搜索和检索
"""

import asyncio
from typing import Dict, Any, List, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ..core.base_agent import BaseAgent
from ..core.message import Message, MessageType
from src.clients.brightdata_client import BrightDataAsyncClient
from src.clients.firecrawl_client import FireCrawlAsyncClient
from src.core.config_loader import ConfigLoader


class SearchAgent(BaseAgent):
    """搜索智能体"""
    
    def __init__(self, name: str, description: str = "专门负责信息搜索的智能体"):
        super().__init__(name, description)
        
        # 初始化搜索客户端
        config = ConfigLoader().config
        external_services = config.get('external_services', {})
        
        # BrightData SERP客户端
        brightdata_config = external_services.get('brightdata', {})
        self.serp_client = BrightDataAsyncClient(
            api_key=brightdata_config.get('api_key'),
            zone=brightdata_config.get('zone', 'xdan_search_searp')
        )
        
        # FireCrawl客户端
        firecrawl_config = external_services.get('firecrawl', {})
        self.crawl_client = FireCrawlAsyncClient(
            api_key=firecrawl_config.get('api_key')
        )
        
        # 注册消息处理器
        self.register_handler(MessageType.QUERY, self._handle_search_query)
        self.register_handler(MessageType.TASK, self._handle_task)
        
        # 搜索缓存
        self.search_cache: Dict[str, Any] = {}
        
    async def on_start(self):
        """启动时初始化"""
        self.logger.info(f"SearchAgent {self.name} ready for search tasks")
        self.state["status"] = "ready"
        self.state["searches_performed"] = 0
    
    async def on_stop(self):
        """停止时清理"""
        self.logger.info(f"SearchAgent {self.name} shutting down")
        self.state["status"] = "stopped"
    
    async def _handle_search_query(self, message: Message):
        """处理搜索查询"""
        query = message.content.get("query", "")
        num_results = message.content.get("num_results", 10)
        include_crawl = message.content.get("include_crawl", False)
        
        if not query:
            response = message.create_response(
                content={"error": "Empty query"},
                type=MessageType.ERROR
            )
            await self.send(response)
            return
        
        try:
            # 执行搜索
            search_result = await self._perform_search(query, num_results)
            
            # 如果需要爬取内容
            if include_crawl and search_result.get("success"):
                crawl_results = await self._crawl_top_results(
                    search_result["results"][:3]  # 爬取前3个结果
                )
                search_result["crawl_results"] = crawl_results
            
            # 更新统计
            self.state["searches_performed"] += 1
            
            # 发送响应
            response = message.create_response(
                content=search_result,
                type=MessageType.RESULT
            )
            await self.send(response)
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            response = message.create_response(
                content={"error": str(e)},
                type=MessageType.ERROR
            )
            await self.send(response)
    
    async def _handle_task(self, message: Message):
        """处理任务消息"""
        task_content = message.content
        task_type = task_content.get("task_type")
        task_data = task_content.get("task_data", {})
        
        if task_type == "search":
            # 转换为查询消息处理
            query_message = Message(
                type=MessageType.QUERY,
                content=task_data,
                sender=message.sender,
                receiver=self.name,
                correlation_id=message.correlation_id
            )
            await self._handle_search_query(query_message)
            
        elif task_type == "crawl":
            # 执行爬取任务
            urls = task_data.get("urls", [])
            crawl_results = await self._crawl_urls(urls)
            
            response = message.create_response(
                content={"crawl_results": crawl_results},
                type=MessageType.RESULT
            )
            await self.send(response)
            
        else:
            response = message.create_response(
                content={"error": f"Unknown task type: {task_type}"},
                type=MessageType.ERROR
            )
            await self.send(response)
    
    async def _perform_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """执行搜索"""
        # 检查缓存
        cache_key = f"{query}:{num_results}"
        if cache_key in self.search_cache:
            self.logger.debug(f"Cache hit for query: {query}")
            return self.search_cache[cache_key]
        
        # 执行搜索
        self.logger.info(f"Searching for: {query}")
        result = await self.serp_client.search(query, num_results)
        
        # 缓存结果
        self.search_cache[cache_key] = result
        
        return result
    
    async def _crawl_top_results(self, search_results: List[Dict]) -> List[Dict]:
        """爬取搜索结果的前几个链接"""
        crawl_tasks = []
        
        for result in search_results[:3]:  # 限制爬取数量
            url = result.get("link")
            if url:
                crawl_tasks.append(self._crawl_url(url))
        
        if crawl_tasks:
            crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
            return [r for r in crawl_results if isinstance(r, dict)]
        
        return []
    
    async def _crawl_urls(self, urls: List[str]) -> List[Dict]:
        """爬取指定URL列表"""
        crawl_tasks = [self._crawl_url(url) for url in urls]
        
        if crawl_tasks:
            crawl_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
            return [r for r in crawl_results if isinstance(r, dict)]
        
        return []
    
    async def _crawl_url(self, url: str) -> Dict[str, Any]:
        """爬取单个URL"""
        try:
            self.logger.debug(f"Crawling URL: {url}")
            result = await self.crawl_client.scrape_url(url)
            
            if result.get("success"):
                return {
                    "url": url,
                    "title": result.get("data", {}).get("title", ""),
                    "content": result.get("data", {}).get("content", ""),
                    "success": True
                }
            else:
                return {
                    "url": url,
                    "error": result.get("error", "Unknown error"),
                    "success": False
                }
                
        except Exception as e:
            self.logger.error(f"Failed to crawl {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def search(self, query: str, num_results: int = 10, include_crawl: bool = False) -> Dict[str, Any]:
        """便捷的搜索方法"""
        return await self._perform_search(query, num_results)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """获取搜索统计"""
        return {
            "searches_performed": self.state.get("searches_performed", 0),
            "cache_size": len(self.search_cache),
            "status": self.state.get("status", "unknown")
        }