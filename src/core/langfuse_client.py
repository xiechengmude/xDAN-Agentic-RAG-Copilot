#!/usr/bin/env python3
"""
Langfuse可观察性客户端 (最新版本)
用于追踪LLM调用、对话会话和S3框架工作流
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)

try:
    from langfuse import Langfuse
    # Langfuse 3.x 不再有decorators模块
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    logger.warning("Langfuse SDK不可用，请运行: uv pip install langfuse -U")

class LangfuseObservabilityClient:
    """Langfuse可观察性客户端"""
    
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self.config_loader = ConfigLoader()
        self.enabled = False
        self._sessions: Dict[str, str] = {}  # chat_id -> session_id mapping
    
    def initialize(self):
        """初始化Langfuse客户端"""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse SDK不可用，可观察性功能将被禁用")
            return
        
        langfuse_config = self.config_loader.get('observability.langfuse', {})
        
        if not langfuse_config.get('enabled', False):
            logger.info("Langfuse可观察性已禁用")
            return
        
        try:
            self.client = Langfuse(
                public_key=langfuse_config.get('public_key'),
                secret_key=langfuse_config.get('secret_key'),
                host=langfuse_config.get('host', 'https://cloud.langfuse.com'),
                debug=False,
                timeout=60  # 设置60秒超时
            )
            
            # 测试连接
            self.client.auth_check()
            self.enabled = True
            
            logger.info(f"Langfuse客户端已初始化: {langfuse_config.get('host')}")
            
        except Exception as e:
            logger.error(f"Langfuse初始化失败: {e}")
            self.enabled = False
    
    def create_session(self, chat_id: str, user_id: Optional[str] = None) -> str:
        """创建或获取会话"""
        if not self.enabled:
            return chat_id
        
        if chat_id in self._sessions:
            return self._sessions[chat_id]
        
        try:
            session = self.client.create_session(
                id=chat_id,
                user_id=user_id or "anonymous",
                metadata={
                    "chat_id": chat_id,
                    "created_at": datetime.now().isoformat(),
                    "service": "xdan-rag-service"
                }
            )
            
            self._sessions[chat_id] = session.id
            return session.id
            
        except Exception as e:
            logger.error(f"创建Langfuse会话失败: {e}")
            return chat_id
    
    def start_trace(
        self, 
        name: str, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """开始追踪"""
        if not self.enabled:
            return None
        
        try:
            trace = self.client.trace(
                name=name,
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {},
                tags=tags or []
            )
            return trace.id
            
        except Exception as e:
            logger.error(f"开始Langfuse追踪失败: {e}")
            return None
    
    def log_llm_call(
        self,
        trace_id: Optional[str],
        name: str,
        model: str,
        input_messages: List[Dict[str, str]],
        output_message: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ):
        """记录LLM调用 (最新Langfuse API)"""
        if not self.enabled or not trace_id:
            return
        
        try:
            # 使用最新的Langfuse API
            generation = self.client.generation(
                id=str(uuid.uuid4()),
                trace_id=trace_id,
                name=name,
                model=model,
                input=input_messages,
                output=output_message,
                usage=usage,
                metadata=metadata or {},
                tags=tags or []
            )
            
            # 立即结束generation以确保数据完整性
            generation.end()
            
        except Exception as e:
            logger.error(f"记录LLM调用失败: {e}")
    
    def log_s3_search_step(
        self,
        trace_id: Optional[str],
        round_number: int,
        query: str,
        documents_found: int,
        selected_documents: List[Dict[str, Any]],
        agent_decision: Optional[str] = None
    ):
        """记录S3框架搜索步骤"""
        if not self.enabled or not trace_id:
            return
        
        try:
            self.client.span(
                trace_id=trace_id,
                name=f"S3-Search-Round-{round_number}",
                input={
                    "query": query,
                    "round": round_number
                },
                output={
                    "documents_found": documents_found,
                    "selected_documents": selected_documents[:3],  # 只记录前3个
                    "agent_decision": agent_decision
                },
                metadata={
                    "framework": "S3",
                    "stage": "search",
                    "round": round_number,
                    "documents_total": documents_found,
                    "documents_selected": len(selected_documents)
                },
                tags=["s3-framework", "search", f"round-{round_number}"]
            )
            
        except Exception as e:
            logger.error(f"记录S3搜索步骤失败: {e}")
    
    def log_s3_select_step(
        self,
        trace_id: Optional[str],
        round_number: int,
        agent_model: str,
        agent_input: str,
        agent_output: str,
        decision: str,
        confidence: Optional[float] = None
    ):
        """记录S3框架选择步骤"""
        if not self.enabled or not trace_id:
            return
        
        try:
            self.client.generation(
                trace_id=trace_id,
                name=f"S3-Select-Round-{round_number}",
                model=agent_model,
                input=agent_input,
                output=agent_output,
                metadata={
                    "framework": "S3",
                    "stage": "select",
                    "round": round_number,
                    "decision": decision,
                    "confidence": confidence
                },
                tags=["s3-framework", "select", "agent-decision", f"round-{round_number}"]
            )
            
        except Exception as e:
            logger.error(f"记录S3选择步骤失败: {e}")
    
    def log_s3_synthesize_step(
        self,
        trace_id: Optional[str],
        model: str,
        documents_used: List[Dict[str, Any]],
        user_question: str,
        final_answer: str,
        total_rounds: int
    ):
        """记录S3框架合成步骤"""
        if not self.enabled or not trace_id:
            return
        
        try:
            self.client.generation(
                trace_id=trace_id,
                name="S3-Synthesize",
                model=model,
                input={
                    "user_question": user_question,
                    "documents": [doc.get('content', '')[:200] + "..." for doc in documents_used[:3]],
                    "total_search_rounds": total_rounds
                },
                output=final_answer,
                metadata={
                    "framework": "S3",
                    "stage": "synthesize",
                    "documents_count": len(documents_used),
                    "search_rounds": total_rounds
                },
                tags=["s3-framework", "synthesize", "final-answer"]
            )
            
        except Exception as e:
            logger.error(f"记录S3合成步骤失败: {e}")
    
    def log_retrieval_operation(
        self,
        trace_id: Optional[str],
        query: str,
        dataset_ids: List[str],
        results: List[Dict[str, Any]],
        similarity_threshold: float
    ):
        """记录检索操作"""
        if not self.enabled or not trace_id:
            return
        
        try:
            self.client.span(
                trace_id=trace_id,
                name="Knowledge-Retrieval",
                input={
                    "query": query,
                    "dataset_ids": dataset_ids,
                    "similarity_threshold": similarity_threshold
                },
                output={
                    "results_count": len(results),
                    "top_similarities": [r.get('similarity', 0) for r in results[:5]]
                },
                metadata={
                    "operation": "retrieval",
                    "datasets": len(dataset_ids),
                    "results_returned": len(results)
                },
                tags=["retrieval", "knowledge-base"]
            )
            
        except Exception as e:
            logger.error(f"记录检索操作失败: {e}")
    
    def log_user_feedback(
        self,
        trace_id: Optional[str],
        feedback_type: str,
        score: Optional[float] = None,
        comment: Optional[str] = None
    ):
        """记录用户反馈"""
        if not self.enabled or not trace_id:
            return
        
        try:
            self.client.score(
                trace_id=trace_id,
                name=feedback_type,
                value=score or 0,
                comment=comment
            )
            
        except Exception as e:
            logger.error(f"记录用户反馈失败: {e}")
    
    def end_trace(self, trace_id: Optional[str], output: Optional[str] = None):
        """结束追踪"""
        if not self.enabled or not trace_id:
            return
        
        try:
            # Langfuse会自动管理trace的结束
            pass
            
        except Exception as e:
            logger.error(f"结束Langfuse追踪失败: {e}")
    
    def flush(self):
        """强制刷新所有pending的事件"""
        if self.enabled and self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"刷新Langfuse事件失败: {e}")
    
    def shutdown(self):
        """关闭客户端"""
        if self.enabled and self.client:
            try:
                self.client.flush()
                self.client.shutdown()
                logger.info("Langfuse客户端已关闭")
            except Exception as e:
                logger.error(f"关闭Langfuse客户端失败: {e}")


class S3WorkflowTracker:
    """S3工作流追踪器"""
    
    def __init__(self, langfuse_client: LangfuseObservabilityClient):
        self.langfuse = langfuse_client
        self.trace_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.search_rounds = 0
    
    def start_workflow(
        self, 
        user_question: str, 
        chat_id: str, 
        user_id: Optional[str] = None
    ):
        """开始S3工作流追踪"""
        self.session_id = self.langfuse.create_session(chat_id, user_id)
        self.trace_id = self.langfuse.start_trace(
            name="S3-Agentic-RAG-Workflow",
            session_id=self.session_id,
            user_id=user_id,
            metadata={
                "user_question": user_question,
                "chat_id": chat_id,
                "framework": "S3",
                "started_at": datetime.now().isoformat()
            },
            tags=["s3-framework", "agentic-rag", "workflow"]
        )
        
        logger.debug(f"S3工作流追踪已开始: {self.trace_id}")
        return self.trace_id
    
    def log_search_round(
        self,
        query: str,
        documents_found: int,
        selected_documents: List[Dict[str, Any]],
        agent_decision: Optional[str] = None
    ):
        """记录搜索轮次"""
        self.search_rounds += 1
        self.langfuse.log_s3_search_step(
            self.trace_id,
            self.search_rounds,
            query,
            documents_found,
            selected_documents,
            agent_decision
        )
    
    def log_agent_decision(
        self,
        agent_model: str,
        agent_input: str,
        agent_output: str,
        decision: str,
        confidence: Optional[float] = None
    ):
        """记录智能体决策"""
        self.langfuse.log_s3_select_step(
            self.trace_id,
            self.search_rounds,
            agent_model,
            agent_input,
            agent_output,
            decision,
            confidence
        )
    
    def log_final_synthesis(
        self,
        model: str,
        documents_used: List[Dict[str, Any]],
        user_question: str,
        final_answer: str
    ):
        """记录最终合成"""
        self.langfuse.log_s3_synthesize_step(
            self.trace_id,
            model,
            documents_used,
            user_question,
            final_answer,
            self.search_rounds
        )
    
    def end_workflow(self, final_answer: str):
        """结束工作流追踪"""
        self.langfuse.end_trace(self.trace_id, final_answer)
        
        # 重置状态
        self.trace_id = None
        self.session_id = None
        self.search_rounds = 0


# 全局Langfuse客户端实例
langfuse_client = LangfuseObservabilityClient()


def get_langfuse_client() -> LangfuseObservabilityClient:
    """获取Langfuse客户端实例"""
    return langfuse_client


def create_s3_tracker() -> S3WorkflowTracker:
    """创建S3工作流追踪器"""
    return S3WorkflowTracker(langfuse_client)