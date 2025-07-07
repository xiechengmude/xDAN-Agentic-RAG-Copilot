"""
RAG MCP 服务 - 独立版本
用于工具的向量检索和智能召回
易于迁移到其他项目的简化版本
"""

import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

# 第三方依赖
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
    import requests
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请安装: pip install qdrant-client requests numpy")
    DEPENDENCIES_AVAILABLE = False

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
    # Embedding服务配置
    embedding_api_url: str = "http://159.54.182.15:8001"
    embedding_model: str = "bge-m3"
    
    # Qdrant配置
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    collection_name: str = "mcp_tools_bge_m3_1024"
    
    # 向量维度（根据模型调整）
    embedding_dim: int = 1024
    
    # 搜索配置
    score_threshold: float = 0.3


class RAGMCPService:
    """RAG MCP服务 - 独立版本"""
    
    # 默认图表工具（检测到图表关键词时自动包含）
    DEFAULT_CHART_TOOLS = [
        "tushareMcp_plot_kline_chart",
        "tushareMcp_plot_line_chart", 
        "tushareMcp_plot_bar_chart",
        "tushareMcp_plot_scatter_chart",
        "tushareMcp_plot_pie_chart"
    ]
    
    def __init__(self, config: Optional[RAGMCPConfig] = None):
        """
        初始化服务
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("必要的依赖未安装")
            
        self.config = config or RAGMCPConfig()
        
        # 初始化Qdrant客户端
        self.qdrant_client = QdrantClient(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port
        )
        
        # 检查集合是否存在
        self._check_collection()
        
        logger.info(f"RAG MCP服务初始化完成")
        
    def _check_collection(self):
        """检查集合是否存在"""
        try:
            info = self.qdrant_client.get_collection(self.config.collection_name)
            logger.info(f"集合 {self.config.collection_name} 已存在，包含 {info.points_count} 个工具")
        except Exception as e:
            logger.warning(f"集合 {self.config.collection_name} 不存在: {e}")
            logger.warning("请先使用 index_tools() 方法创建索引")
            
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        获取文本的向量表示
        
        Args:
            text: 要向量化的文本
            
        Returns:
            向量列表，失败返回None
        """
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
                limit=top_k * 2 if include_chart_tools else top_k,
                query_filter=search_filter,
                score_threshold=score_threshold or self.config.score_threshold
            )
            
            # 转换结果
            tool_results = []
            included_tools = set()
            
            # 如果检测到图表需求，优先添加默认图表工具
            if include_chart_tools:
                for point in results:
                    tool_name = point.payload.get("tool_name", "")
                    if tool_name in self.DEFAULT_CHART_TOOLS and tool_name not in included_tools:
                        tool_results.append(self._point_to_result(point))
                        included_tools.add(tool_name)
                
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
                    
                # 创建点
                point = PointStruct(
                    id=tool["tool_name"],
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


# 示例用法
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建服务
    service = RAGMCPService()
    
    # 健康检查
    health = service.health_check()
    print(f"健康检查: {health}")
    
    # 测试搜索
    results = service.search_tools_by_intent("获取股票信息", top_k=5)
    for i, tool in enumerate(results):
        print(f"{i+1}. {tool.tool_name} (score: {tool.score:.3f})")
        print(f"   类别: {tool.category}")
        print(f"   描述: {tool.description[:50]}...")