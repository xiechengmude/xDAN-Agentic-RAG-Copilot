"""
RAG Tool Provider
基于向量检索的智能工具选择提供者
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool, tool

from .base_provider import BaseToolProvider

logger = logging.getLogger(__name__)


class RAGToolProvider(BaseToolProvider):
    """
    RAG工具提供者
    提供基于向量检索的智能工具选择能力
    """
    
    def __init__(self):
        super().__init__("RAG")
        self.rag_service = None
        self.tools_indexed = False
        
    async def initialize(self) -> bool:
        """初始化RAG服务"""
        try:
            # 尝试导入RAG服务
            from ..mcp.rag_mcp_service import RAGMCPService, RAGMCPConfig
            
            # 创建配置
            config = RAGMCPConfig()
            
            # 创建RAG服务
            self.rag_service = RAGMCPService(config)
            
            # 检查健康状态
            health = await self._check_rag_health()
            if not health:
                logger.warning("RAG service health check failed, using fallback mode")
                return await self._initialize_fallback_mode()
            
            # 确保工具已索引
            await self._ensure_tools_indexed()
            
            logger.info("✅ RAG Tool Provider initialized successfully")
            return True
            
        except ImportError as e:
            logger.warning(f"RAG dependencies not available: {e}")
            return await self._initialize_fallback_mode()
        except Exception as e:
            logger.error(f"RAG initialization failed: {e}")
            return await self._initialize_fallback_mode()
    
    async def _check_rag_health(self) -> bool:
        """检查RAG服务健康状态"""
        try:
            if not self.rag_service:
                return False
            
            # 执行健康检查
            health_result = await asyncio.get_event_loop().run_in_executor(
                None, self.rag_service.health_check
            )
            
            # 检查Qdrant和embedding服务状态
            return health_result.get("qdrant", False) and health_result.get("embedding", False)
            
        except Exception as e:
            logger.warning(f"RAG health check failed: {e}")
            return False
    
    async def _ensure_tools_indexed(self):
        """确保工具已被索引"""
        try:
            if self.tools_indexed:
                return
                
            # 检查是否需要创建索引
            from pathlib import Path
            tools_file = Path(__file__).parent.parent / "mcp" / "tools_rag_ready.json"
            
            if tools_file.exists():
                # 异步索引工具
                await asyncio.get_event_loop().run_in_executor(
                    None, self.rag_service.index_tools, str(tools_file)
                )
                self.tools_indexed = True
                logger.info("✅ Tools indexed successfully")
            else:
                logger.warning("⚠️ tools_rag_ready.json not found, using fallback")
                
        except Exception as e:
            logger.error(f"Failed to index tools: {e}")
    
    async def _initialize_fallback_mode(self) -> bool:
        """初始化回退模式"""
        logger.info("Initializing RAG provider in fallback mode")
        self.rag_service = None
        return True
    
    async def get_tools(self) -> List[BaseTool]:
        """获取RAG工具集"""
        tools = []
        
        if self.rag_service:
            # 真实RAG功能
            tools.extend(self._create_rag_tools())
        else:
            # 回退模式
            tools.extend(self._create_fallback_tools())
        
        return tools
    
    def _create_rag_tools(self) -> List[BaseTool]:
        """创建真实的RAG工具"""
        
        @tool
        async def search_relevant_tools(query: str, top_k: int = 10, category: str = None) -> str:
            """
            基于查询意图搜索最相关的工具
            
            Args:
                query: 用户查询或任务描述
                top_k: 返回的工具数量
                category: 可选的工具类别过滤
            """
            try:
                # 异步调用RAG服务
                results = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    self.rag_service.search_tools_by_intent,
                    query, top_k, category
                )
                
                if not results:
                    return f"❌ No relevant tools found for query: {query}"
                
                # 格式化结果
                response = f"🔍 Found {len(results)} relevant tools for: {query}\n\n"
                
                for i, tool in enumerate(results, 1):
                    response += f"{i}. **{tool.tool_name}** (Score: {tool.score:.3f})\n"
                    response += f"   📝 {tool.description}\n"
                    response += f"   🏷️ Category: {tool.category}\n"
                    
                    if tool.related_tools:
                        response += f"   🔗 Related: {', '.join(tool.related_tools[:3])}\n"
                    
                    response += "\n"
                
                return response
                
            except Exception as e:
                logger.error(f"RAG tool search failed: {e}")
                return f"❌ Tool search failed: {str(e)}"
        
        @tool
        async def get_tool_recommendations(task_description: str) -> str:
            """
            基于任务描述获取工具推荐
            
            Args:
                task_description: 详细的任务描述
            """
            try:
                # 搜索相关工具
                results = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.rag_service.search_tools_by_intent,
                    task_description, 5
                )
                
                if not results:
                    return "⚠️ No tool recommendations available"
                
                response = f"💡 Tool recommendations for: {task_description}\n\n"
                
                for tool in results:
                    response += f"🛠️ **{tool.tool_name}**\n"
                    response += f"   Relevance: {tool.score:.1%}\n" 
                    response += f"   Usage: {tool.description}\n\n"
                
                return response
                
            except Exception as e:
                return f"❌ Failed to get recommendations: {str(e)}"
        
        @tool  
        def get_rag_stats() -> str:
            """获取RAG服务统计信息"""
            try:
                health = self.rag_service.health_check()
                
                stats = f"""📊 RAG Service Statistics:
🟢 Status: {health.get('status', 'unknown')}
🛠️ Total tools: {health.get('tool_count', 'N/A')}
🎯 Collections: {health.get('collection_info', 'N/A')}
⚡ Embedding model: {self.rag_service.config.embedding_model}
🔍 Score threshold: {self.rag_service.config.score_threshold}"""
                
                return stats
                
            except Exception as e:
                return f"❌ Stats unavailable: {str(e)}"
        
        return [search_relevant_tools, get_tool_recommendations, get_rag_stats]
    
    def _create_fallback_tools(self) -> List[BaseTool]:
        """创建回退模式工具"""
        
        @tool
        def search_relevant_tools_fallback(query: str, top_k: int = 10, category: str = None) -> str:
            """
            基于关键词的简单工具搜索（回退模式）
            """
            # 简单的关键词匹配
            fallback_tools = {
                "stock": ["股票查询工具", "股价分析工具", "股票基本信息工具"],
                "search": ["网络搜索工具", "文档搜索工具", "信息检索工具"],
                "data": ["数据分析工具", "数据可视化工具", "数据处理工具"],
                "chart": ["图表生成工具", "可视化工具", "报表工具"]
            }
            
            query_lower = query.lower()
            recommended = []
            
            for keyword, tools in fallback_tools.items():
                if keyword in query_lower:
                    recommended.extend(tools)
            
            if not recommended:
                recommended = ["通用分析工具", "基础查询工具", "数据处理工具"]
            
            response = f"🔍 Fallback mode - Found tools for: {query}\n\n"
            for i, tool in enumerate(recommended[:top_k], 1):
                response += f"{i}. {tool} (Fallback mode)\n"
            
            response += "\n⚠️ Note: RAG service unavailable, using simple keyword matching"
            
            return response
        
        @tool
        def get_rag_status() -> str:
            """获取RAG服务状态"""
            return """⚠️ RAG Service Status: Fallback Mode
            
Reason: RAG dependencies not available or service unreachable
Available features:
- ✅ Basic keyword-based tool search
- ❌ Vector similarity search
- ❌ Intelligent tool recommendations
- ❌ Category filtering

To enable full RAG features:
1. Install dependencies: qdrant-client, numpy
2. Configure Qdrant server
3. Set environment variables"""
        
        return [search_relevant_tools_fallback, get_rag_status]
    
    async def cleanup(self):
        """清理资源"""
        if self.rag_service:
            try:
                # RAG服务清理
                pass
            except Exception as e:
                logger.error(f"RAG cleanup error: {e}")
        
        await super().cleanup()