#!/usr/bin/env python3
"""
S3服务实现
遵循S3架构设计，提供统一的RAG服务接口
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import os
import logging
from src.core.s3_framework import S3FrameworkAgent
from src.clients.litellm_client import LiteLLMSDKClientV2
from src.clients.ragflow_client import RAGFlowClient

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))

class S3Service:
    """
    S3服务封装
    
    职责：
    1. 初始化客户端
    2. 创建S3框架实例
    3. 提供统一的API接口
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化S3服务
        
        Args:
            config: 配置字典，包含RAGFlow和LiteLLM配置
        """
        # 初始化RAGFlow客户端（知识库检索）
        self.ragflow_client = RAGFlowClient(
            api_url=config.get('ragflow_api_url'),
            api_key=config.get('ragflow_api_key')
        )
        
        # 初始化LiteLLM客户端（统一LLM引擎）
        # 所有LLM操作都通过这个客户端
        self.litellm_client = LiteLLMSDKClientV2()
        
        # 初始化S3框架（核心编排器）
        self.s3_framework = S3FrameworkAgent(
            ragflow_client=self.ragflow_client,
            litellm_sdk_client=self.litellm_client
        )
        
        # 默认数据集
        self.default_dataset_id = config.get('default_dataset_id')
        
        logger.info("S3服务初始化完成")
        logger.info("- RAGFlow: 负责知识库检索")
        logger.info("- LiteLLM: 负责所有LLM操作（Agent决策和答案生成）")
        logger.info("- S3Framework: 负责Search-Select-Synthesize编排")
    
    async def ask(self, 
                  question: str, 
                  dataset_ids: Optional[List[str]] = None,
                  max_rounds: int = 3,
                  stream: bool = False) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行S3问答流程
        
        Args:
            question: 用户问题
            dataset_ids: 数据集ID列表，为空则使用默认数据集
            max_rounds: 最大搜索轮数
            stream: 是否流式返回
            
        Yields:
            包含答案和元数据的字典
        """
        # 使用默认数据集如果未指定
        if not dataset_ids:
            dataset_ids = [self.default_dataset_id] if self.default_dataset_id else []
        
        # 直接委托给S3框架执行完整工作流
        async for result in self.s3_framework.execute_s3_workflow(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=max_rounds,
            stream=stream
        ):
            yield result
    
    async def search_only(self, 
                         question: str, 
                         dataset_ids: Optional[List[str]] = None,
                         top_k: int = 10) -> Dict[str, Any]:
        """
        仅执行搜索阶段（用于测试或特殊场景）
        
        Args:
            question: 搜索查询
            dataset_ids: 数据集ID列表
            top_k: 返回结果数量
            
        Returns:
            搜索结果
        """
        if not dataset_ids:
            dataset_ids = [self.default_dataset_id] if self.default_dataset_id else []
        
        chunks, success = await self.s3_framework.search_phase(
            question=question,
            dataset_ids=dataset_ids,
            top_k=top_k
        )
        
        return {
            "success": success,
            "chunks": chunks,
            "count": len(chunks)
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """
        检查所有依赖服务的健康状态
        
        Returns:
            各服务的健康状态
        """
        health = {
            "ragflow": False,
            "litellm": False,
            "s3_framework": True  # 框架本身总是健康的
        }
        
        # 检查RAGFlow
        try:
            result = self.ragflow_client.list_datasets(page_size=1)
            health["ragflow"] = result.get("code") == 0
        except:
            health["ragflow"] = False
        
        # 检查LiteLLM
        try:
            # 使用简单的completion测试
            response = await self.litellm_client.chat_completion(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            health["litellm"] = bool(response)
        except:
            health["litellm"] = False
        
        return health


# 工厂函数
def create_s3_service(config: Dict[str, Any]) -> S3Service:
    """
    创建S3服务实例的工厂函数
    
    Args:
        config: 服务配置
        
    Returns:
        S3服务实例
    """
    return S3Service(config)