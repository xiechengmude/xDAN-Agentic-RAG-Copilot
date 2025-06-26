#!/usr/bin/env python3
"""
RAGFlow客户端实现
提供S3框架需要的核心检索功能
"""

import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RAGFlowClient:
    """
    RAGFlow客户端
    
    职责：
    - 知识库检索（retrieve_chunks）
    - 数据集列表（list_datasets）
    - 基础的数据集和文档管理
    """
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            api_url: RAGFlow API地址
            api_key: API密钥
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # 设置session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # 代理配置（如果需要）
        self._setup_proxy()
        
        logger.info(f"RAGFlow客户端初始化: {api_url}")
    
    def _setup_proxy(self):
        """设置代理（如果环境变量中有配置）"""
        import os
        if os.getenv('HTTP_PROXY'):
            self.session.proxies = {
                'http': os.getenv('HTTP_PROXY'),
                'https': os.getenv('HTTPS_PROXY', os.getenv('HTTP_PROXY'))
            }
            logger.info("使用代理配置")
    
    def retrieve_chunks(self, 
                       question: str, 
                       dataset_ids: List[str],
                       page_size: int = 10,
                       similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        检索相关文档片段 - S3框架的核心需求
        
        Args:
            question: 检索查询
            dataset_ids: 数据集ID列表
            page_size: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            检索结果，格式：
            {
                "code": 0,
                "data": {
                    "chunks": [
                        {
                            "content": "文档内容",
                            "document_name": "文档名",
                            "dataset_id": "数据集ID",
                            "similarity": 0.95
                        }
                    ]
                }
            }
        """
        url = f"{self.api_url}/api/v1/retrieval"
        
        payload = {
            "question": question,
            "dataset_ids": dataset_ids,
            "page": 1,
            "page_size": page_size,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": 0.7
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"检索失败: {e}")
            return {
                "code": -1,
                "message": str(e),
                "data": {"chunks": []}
            }
    
    def list_datasets(self, page_size: int = 1) -> Dict[str, Any]:
        """
        获取数据集列表 - 主要用于健康检查
        
        Args:
            page_size: 每页数量
            
        Returns:
            数据集列表响应
        """
        url = f"{self.api_url}/api/v1/datasets"
        
        params = {
            "page": 1,
            "page_size": page_size
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取数据集列表失败: {e}")
            return {"code": -1, "message": str(e)}
    
    def __repr__(self):
        return f"RAGFlowClient(api_url='{self.api_url}')"