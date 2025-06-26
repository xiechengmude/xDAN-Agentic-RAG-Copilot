#!/usr/bin/env python3
"""
RAGFlow官方SDK封装类
集成官方ragflow_sdk到我们的S3框架中
"""

import os
import logging
import requests
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv

try:
    from ragflow_sdk import RAGFlow, Agent, DataSet, Document, Chat
    SDK_AVAILABLE = True
except ImportError:
    print("警告: ragflow_sdk 未安装，将使用HTTP客户端模式")
    SDK_AVAILABLE = False

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class RAGFlowSDKWrapper:
    """
    RAGFlow官方SDK封装类
    提供与现有RAGFlowClient兼容的接口，同时支持Agent和Session功能
    """
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        初始化RAGFlow SDK封装
        
        Args:
            api_url: RAGFlow API的基础URL
            api_key: RAGFlow API的认证密钥
        """
        if not SDK_AVAILABLE:
            raise ImportError("ragflow_sdk 未安装，请运行: pip install ragflow-sdk")
        
        self.api_url = api_url or os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not self.api_url:
            raise ValueError("RAGFlow API URL 未设置")
        if not self.api_key:
            raise ValueError("RAGFlow API Key 未设置")
        
        # 初始化官方SDK
        # 使用提供的URL，不强制转换端口
        base_url = self.api_url
        
        self.rag_flow = RAGFlow(api_key=self.api_key, base_url=base_url)
        
        logger.info(f"RAGFlow SDK 初始化成功: {base_url}")
    
    # ==================== 数据集管理 ====================
    
    def list_datasets(self, page: int = 1, page_size: int = 30, **kwargs) -> Dict[str, Any]:
        """列出数据集"""
        try:
            datasets = self.rag_flow.list_datasets(page=page, page_size=page_size, **kwargs)
            # 转换为与HTTP客户端兼容的格式
            return {
                "code": 0,
                "data": [self._dataset_to_dict(ds) for ds in datasets] if datasets else []
            }
        except Exception as e:
            logger.error(f"列出数据集失败: {e}")
            return {"code": 500, "message": str(e)}
    
    def create_dataset(self, name: str, **kwargs) -> Dict[str, Any]:
        """创建数据集"""
        try:
            dataset = self.rag_flow.create_dataset(name=name, **kwargs)
            return {
                "code": 0,
                "data": self._dataset_to_dict(dataset)
            }
        except Exception as e:
            logger.error(f"创建数据集失败: {e}")
            return {"code": 500, "message": str(e)}
    
    def delete_datasets(self, ids: List[str] = None) -> Dict[str, Any]:
        """删除数据集"""
        try:
            if ids:
                for dataset_id in ids:
                    self.rag_flow.delete_dataset(dataset_id)
            else:
                # 删除所有数据集
                datasets = self.rag_flow.list_datasets()
                for dataset in datasets:
                    dataset.delete()
            return {"code": 0, "message": "删除成功"}
        except Exception as e:
            logger.error(f"删除数据集失败: {e}")
            return {"code": 500, "message": str(e)}
    
    # ==================== 检索功能 ====================
    
    def retrieve_chunks(self, question: str, dataset_ids: List[str] = None, 
                       document_ids: List[str] = None, top_k: int = 5,
                       similarity_threshold: float = 0.1, **kwargs) -> Dict[str, Any]:
        """
        检索文本块 - 优先使用HTTP API以获取相似度信息
        """
        try:
            # 直接使用HTTP API，因为SDK的retrieve方法不返回相似度信息
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_url}/api/v1/retrieval"
            
            data = {
                "question": question,
                "dataset_ids": dataset_ids or [],
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            }
            
            if document_ids:
                data["document_ids"] = document_ids
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get("code") == 0:
                chunks_data = result.get("data", {}).get("chunks", [])
                return {
                    "code": 0,
                    "data": {
                        "chunks": chunks_data,
                        "total": len(chunks_data)
                    }
                }
            else:
                return result
                    
        except Exception as e:
            logger.error(f"检索失败: {e}")
            return {"code": 500, "message": str(e)}
    
    # ==================== Agent管理 ====================
    
    def list_agents(self, page: int = 1, page_size: int = 30, **kwargs) -> List[Dict[str, Any]]:
        """列出Agent"""
        try:
            agents = self.rag_flow.list_agents(page=page, page_size=page_size, **kwargs)
            return [self._agent_to_dict(agent) for agent in agents] if agents else []
        except Exception as e:
            logger.error(f"列出Agent失败: {e}")
            return []
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取指定Agent"""
        try:
            agents = self.rag_flow.list_agents(id=agent_id)
            if agents:
                return self._agent_to_dict(agents[0])
            return None
        except Exception as e:
            logger.error(f"获取Agent失败: {e}")
            return None
    
    def create_agent(self, name: str, **kwargs) -> Dict[str, Any]:
        """创建Agent"""
        try:
            agent = self.rag_flow.create_agent(name=name, **kwargs)
            return {
                "code": 0,
                "data": self._agent_to_dict(agent)
            }
        except Exception as e:
            logger.error(f"创建Agent失败: {e}")
            return {"code": 500, "message": str(e)}
    
    # ==================== Session管理 ====================
    
    def create_session(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """为指定Agent创建Session"""
        try:
            agents = self.rag_flow.list_agents(id=agent_id)
            if not agents:
                return {"code": 404, "message": "Agent not found"}
            
            agent = agents[0]
            session = agent.create_session(**kwargs)
            
            return {
                "code": 0,
                "data": {
                    "session_id": getattr(session, 'id', None),
                    "agent_id": agent_id,
                    "created_at": getattr(session, 'created_at', None)
                }
            }
        except Exception as e:
            logger.error(f"创建Session失败: {e}")
            return {"code": 500, "message": str(e)}
    
    def session_ask(self, agent_id: str, question: str, session_id: str = None, 
                   stream: bool = False, **kwargs):
        """通过Session进行对话"""
        try:
            agents = self.rag_flow.list_agents(id=agent_id)
            if not agents:
                raise ValueError("Agent not found")
            
            agent = agents[0]
            
            # 如果没有提供session_id，创建新的session
            if not session_id:
                session = agent.create_session(**kwargs)
            else:
                # 这里需要根据官方SDK的实际API来获取现有session
                session = agent.create_session(**kwargs)  # 临时实现
            
            # 进行对话
            if stream:
                return session.ask(question=question, stream=True, **kwargs)
            else:
                response = session.ask(question=question, stream=False, **kwargs)
                return {
                    "code": 0,
                    "data": {
                        "content": getattr(response, 'content', str(response)),
                        "session_id": getattr(session, 'id', None)
                    }
                }
        except Exception as e:
            logger.error(f"Session对话失败: {e}")
            if stream:
                yield {"error": str(e)}
            else:
                return {"code": 500, "message": str(e)}
    
    # ==================== 辅助方法 ====================
    
    def _dataset_to_dict(self, dataset) -> Dict[str, Any]:
        """将Dataset对象转换为字典"""
        return {
            "id": getattr(dataset, 'id', None),
            "name": getattr(dataset, 'name', None),
            "description": getattr(dataset, 'description', None),
            "created_at": getattr(dataset, 'created_at', None),
            "updated_at": getattr(dataset, 'updated_at', None)
        }
    
    def _agent_to_dict(self, agent) -> Dict[str, Any]:
        """将Agent对象转换为字典"""
        return {
            "id": getattr(agent, 'id', None),
            "name": getattr(agent, 'name', None),
            "description": getattr(agent, 'description', None),
            "created_at": getattr(agent, 'created_at', None),
            "updated_at": getattr(agent, 'updated_at', None)
        }
    
    def _chunk_to_dict(self, chunk) -> Dict[str, Any]:
        """将Chunk对象转换为字典"""
        # 尝试多个可能的相似度字段名
        similarity = getattr(chunk, 'similarity', None)
        if similarity is None:
            similarity = getattr(chunk, 'score', None)
        if similarity is None:
            similarity = getattr(chunk, 'similarity_score', None)
            
        return {
            "id": getattr(chunk, 'id', None),
            "content": getattr(chunk, 'content', str(chunk)),
            "document_id": getattr(chunk, 'document_id', None),
            "dataset_id": getattr(chunk, 'dataset_id', None),
            "similarity": similarity
        }
    
    # ==================== 兼容性方法 ====================
    
    def get_rag_flow_instance(self):
        """获取原始的RAGFlow实例，用于高级操作"""
        return self.rag_flow
