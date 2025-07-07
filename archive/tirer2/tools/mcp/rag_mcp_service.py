"""
RAG MCP 服务
用于工具的向量检索和智能召回
"""

import os
import json
import hashlib
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import requests
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ToolSearchResult:
    """工具搜索结果"""
    tool_name: str
    description: str
    category: str
    score: float
    related_tools: List[str]
    full_metadata: Dict[str, Any]


@dataclass
class RAGMCPConfig:
    """RAG MCP配置"""
    # 从环境变量读取
    embedding_api_url: str = os.getenv("RAG_EMBEDDING_URL", "http://159.54.182.15:8001")
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "bge-m3")
    qdrant_host: str = os.getenv("MEM0_VECTOR_STORE_HOST", "localhost")
    qdrant_port: int = int(os.getenv("MEM0_VECTOR_STORE_PORT", "6333"))
    collection_name: str = "mcp_tools_bge_m3_1024"  # 工具专用集合
    embedding_dim: int = 1024  # BGE-M3的维度
    score_threshold: float = 0.3
    # Redis缓存配置
    redis_cache_enabled: bool = False  # 工具检索暂时不用缓存
    redis_cache_ttl: int = 3600


class RAGMCPService:
    """RAG MCP服务"""
    
    # 默认图表工具（检测到图表关键词时自动包含）
    DEFAULT_CHART_TOOLS = [
        "tushareMcp_plot_kline_chart",
        "tushareMcp_plot_line_chart", 
        "tushareMcp_plot_bar_chart",
        "tushareMcp_plot_scatter_chart",
        "tushareMcp_plot_pie_chart"
    ]
    
    def __init__(self, config: Optional[RAGMCPConfig] = None):
        """初始化服务"""
        self.config = config or RAGMCPConfig()
        
        # 初始化Qdrant客户端
        self.qdrant_client = QdrantClient(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port
        )
        
        # 检查集合是否存在
        self._check_collection()
        
        logger.info(f"RAG MCP服务初始化完成")
        logger.info(f"Embedding: {self.config.embedding_model} @ {self.config.embedding_api_url}")
        logger.info(f"Qdrant: {self.config.qdrant_host}:{self.config.qdrant_port}")
        
    def _check_collection(self):
        """检查集合是否存在"""
        try:
            info = self.qdrant_client.get_collection(self.config.collection_name)
            logger.info(f"集合 {self.config.collection_name} 已存在，包含 {info.points_count} 个工具")
        except Exception as e:
            logger.warning(f"集合 {self.config.collection_name} 不存在: {e}")
            logger.warning("请先使用 rag_mcp_cli.py index 命令创建索引")
            
    def _get_embedding(self, text: str) -> List[float]:
        """获取文本的向量表示"""
        try:
            response = requests.post(
                f"{self.config.embedding_api_url}/embeddings",
                json={
                    "input": text,
                    "model": self.config.embedding_model
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
                else:
                    logger.error(f"Embedding响应格式错误: {data}")
                    return None
            else:
                logger.error(f"Embedding请求失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取embedding失败: {e}")
            return None
            
    def search_tools_by_intent(
        self,
        query: str,
        top_k: int = 30,
        category_filter: Optional[str] = None,
        score_threshold: Optional[float] = None
    ) -> List[ToolSearchResult]:
        """
        根据意图搜索工具
        
        Args:
            query: 搜索查询
            top_k: 返回数量
            category_filter: 类别过滤
            score_threshold: 分数阈值
            
        Returns:
            工具搜索结果列表
        """
        # 检查是否包含图表关键词
        include_chart_tools = self._contains_chart_keywords(query)
        
        # 获取查询向量
        query_vector = self._get_embedding(query)
        if not query_vector:
            logger.error("无法获取查询向量")
            return []
            
        # 构建过滤条件
        filter_conditions = []
        if category_filter:
            filter_conditions.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category_filter)
                )
            )
            
        search_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # 向量搜索
        try:
            results = self.qdrant_client.search(
                collection_name=self.config.collection_name,
                query_vector=query_vector,
                limit=top_k * 2 if include_chart_tools else top_k,  # 如果需要图表工具，多搜一些
                query_filter=search_filter,
                score_threshold=score_threshold or self.config.score_threshold
            )
            
            # 转换结果
            tool_results = []
            included_tools = set()
            
            # 如果检测到图表需求，优先添加默认图表工具
            if include_chart_tools:
                chart_tools_added = 0
                for point in results:
                    tool_name = point.payload.get("tool_name", "")
                    if tool_name in self.DEFAULT_CHART_TOOLS and tool_name not in included_tools:
                        tool_results.append(self._point_to_result(point))
                        included_tools.add(tool_name)
                        chart_tools_added += 1
                        
                logger.info(f"检测到图表需求，添加了 {chart_tools_added} 个默认图表工具")
                
            # 添加其他相关工具
            for point in results:
                if len(tool_results) >= top_k:
                    break
                    
                tool_name = point.payload.get("tool_name", "")
                if tool_name not in included_tools:
                    tool_results.append(self._point_to_result(point))
                    included_tools.add(tool_name)
                    
            logger.info(f"搜索 '{query}' 返回 {len(tool_results)} 个工具")
            return tool_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
            
    def _contains_chart_keywords(self, query: str) -> bool:
        """检测查询是否包含图表相关关键词"""
        chart_keywords = [
            "图", "图表", "chart", "plot", "绘制", "画", "可视化",
            "K线", "k线", "蜡烛图", "线图", "柱状图", "饼图", "散点图",
            "趋势图", "走势图", "技术分析图"
        ]
        
        query_lower = query.lower()
        return any(keyword.lower() in query_lower for keyword in chart_keywords)
        
    def _point_to_result(self, point) -> ToolSearchResult:
        """将Qdrant点转换为搜索结果"""
        payload = point.payload
        return ToolSearchResult(
            tool_name=payload.get("tool_name", ""),
            description=payload.get("description", ""),
            category=payload.get("category", "其他"),
            score=point.score,
            related_tools=payload.get("related_tools", []),
            full_metadata=payload.get("full_metadata", {})
        )
        
    def _get_tools_by_names(self, tool_names: List[str]) -> List[ToolSearchResult]:
        """根据工具名称获取工具信息"""
        if not tool_names:
            return []
            
        try:
            # 将工具名称转换为UUID
            tool_ids = [str(uuid.uuid5(uuid.NAMESPACE_DNS, name)) for name in tool_names]
            
            # 批量获取
            points = self.qdrant_client.retrieve(
                collection_name=self.config.collection_name,
                ids=tool_ids,
                with_payload=True
            )
            
            results = []
            for point in points:
                results.append(ToolSearchResult(
                    tool_name=point.payload.get("tool_name", ""),
                    description=point.payload.get("description", ""),
                    category=point.payload.get("category", "其他"),
                    score=1.0,  # 精确匹配
                    related_tools=point.payload.get("related_tools", []),
                    full_metadata=point.payload.get("full_metadata", {})
                ))
                
            return results
            
        except Exception as e:
            logger.error(f"获取工具失败: {e}")
            return []
            
    def index_tools(self, data_file: str) -> bool:
        """
        索引工具数据
        
        Args:
            data_file: 工具数据文件路径
            
        Returns:
            是否成功
        """
        try:
            # 读取数据
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            tools = data.get("tools", [])
            logger.info(f"准备索引 {len(tools)} 个工具")
            
            # 创建集合
            self.qdrant_client.recreate_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.config.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            # 批量处理
            batch_size = 50
            points = []
            
            for i, tool in enumerate(tools):
                # 构建索引文本
                index_text = self._build_index_text(tool)
                
                # 获取向量
                embedding = self._get_embedding(index_text)
                if not embedding:
                    logger.warning(f"跳过工具 {tool.get('tool_name')}: 无法获取向量")
                    continue
                    
                # 创建点 - 使用UUID作为ID以兼容Qdrant
                point = PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, tool["tool_name"])),  # 使用UUID作为ID
                    vector=embedding,
                    payload=tool
                )
                points.append(point)
                
                # 批量上传
                if len(points) >= batch_size:
                    self.qdrant_client.upsert(
                        collection_name=self.config.collection_name,
                        points=points
                    )
                    logger.info(f"已索引 {i+1}/{len(tools)} 个工具")
                    points = []
                    
            # 上传剩余的
            if points:
                self.qdrant_client.upsert(
                    collection_name=self.config.collection_name,
                    points=points
                )
                
            logger.info(f"索引完成，共 {len(tools)} 个工具")
            return True
            
        except Exception as e:
            logger.error(f"索引失败: {e}")
            return False
            
    def _build_index_text(self, tool: Dict) -> str:
        """构建用于索引的文本"""
        parts = []
        
        # 工具名
        parts.append(f"工具名: {tool.get('tool_name', '')}")
        
        # 描述
        parts.append(f"描述: {tool.get('description', '')}")
        
        # 类别
        parts.append(f"类别: {tool.get('category', '')}")
        
        # 相关工具
        related = tool.get("related_tools", [])
        if related:
            parts.append(f"相关工具: {', '.join(related)}")
            
        return " ".join(parts)
        
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """获取集合信息"""
        try:
            info = self.qdrant_client.get_collection(self.config.collection_name)
            return {
                "name": self.config.collection_name,
                "points_count": info.points_count,
                "status": info.status,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance
            }
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return None
            
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        status = {
            "qdrant": False,
            "embedding": False,
            "collection": False
        }
        
        # 检查Qdrant
        try:
            self.qdrant_client.get_collections()
            status["qdrant"] = True
        except:
            pass
            
        # 检查Embedding
        try:
            vector = self._get_embedding("test")
            status["embedding"] = vector is not None
        except:
            pass
            
        # 检查集合
        try:
            info = self.get_collection_info()
            status["collection"] = info is not None
        except:
            pass
            
        return status


# 测试函数
async def test_rag_mcp_service():
    """测试RAG MCP服务"""
    service = RAGMCPService()
    
    # 健康检查
    health = service.health_check()
    logger.info(f"健康检查: {health}")
    
    # 测试搜索
    test_queries = [
        "获取股票信息",
        "生成K线图",
        "财务数据分析"
    ]
    
    for query in test_queries:
        logger.info(f"\n搜索: {query}")
        results = service.search_tools_by_intent(query, top_k=5)
        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.tool_name} (score: {result.score:.3f})")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_rag_mcp_service())