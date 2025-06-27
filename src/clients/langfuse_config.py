"""
Langfuse配置 for DeepSearch项目
提供细粒度的LLM调用追踪和分析
"""
import os
import litellm
from typing import Dict, Any, Optional, List
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class LangfuseConfig:
    """Langfuse集成配置类"""
    
    def __init__(self):
        # 设置Langfuse凭据
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-78b5ed03-54ba-4a51-8d20-b1221f17046d"
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-7ea885b0-8c1b-4606-bb5d-c004ed367d1f"
        os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
        
        # 启用Langfuse回调
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        
        # 可选：启用调试日志
        # litellm.set_verbose = True
        
        logger.info(f"Langfuse已配置: {os.environ.get('LANGFUSE_HOST')}")
    
    @staticmethod
    def get_deepsearch_metadata(
        search_query: str,
        search_depth: int,
        iteration: int,
        search_type: str = "web_search",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        为DeepSearch生成Langfuse元数据
        
        Args:
            search_query: 搜索查询
            search_depth: 搜索深度
            iteration: 当前迭代次数
            search_type: 搜索类型 (web_search, content_extraction, synthesis)
            user_id: 用户ID
            session_id: 会话ID
        
        Returns:
            Langfuse元数据字典
        """
        metadata = {
            # 生成信息
            "generation_name": f"deepsearch-{search_type}-iter{iteration}",
            
            # 追踪信息
            "trace_name": f"DeepSearch: {search_query[:50]}...",
            "trace_user_id": user_id or "anonymous",
            "session_id": session_id or f"deepsearch-session-{search_query[:20]}",
            
            # 自定义元数据
            "trace_metadata": {
                "search_query": search_query,
                "search_depth": search_depth,
                "iteration": iteration,
                "search_type": search_type,
                "project": "deepsearch",
                "component": search_type,
            },
            
            # 标签
            "tags": [
                "deepsearch",
                search_type,
                f"depth-{search_depth}",
                f"iter-{iteration}"
            ],
            
            # 版本信息
            "version": "1.0.0",
            "trace_version": "deepsearch-v1",
            
            # 调试
            "debug_langfuse": False
        }
        
        return metadata
    
    @staticmethod
    def track_search_phase(phase: str):
        """
        装饰器：追踪DeepSearch的不同阶段
        
        Args:
            phase: 阶段名称 (search, select, synthesize)
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 从参数中提取必要信息
                self = args[0] if args else None
                query = kwargs.get('query', args[1] if len(args) > 1 else 'unknown')
                
                # 生成追踪ID
                trace_id = f"deepsearch-{phase}-{hash(query)}"
                
                # 设置阶段特定的元数据
                kwargs['langfuse_metadata'] = {
                    "trace_id": trace_id,
                    "generation_name": f"{phase}-phase",
                    "trace_metadata": {
                        "phase": phase,
                        "query": query,
                    },
                    "tags": [phase, "deepsearch-phase"]
                }
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator


class DeepSearchLangfuseTracker:
    """DeepSearch专用的Langfuse追踪器"""
    
    def __init__(self, session_id: Optional[str] = None, user_id: Optional[str] = None):
        self.session_id = session_id or f"session-{os.urandom(8).hex()}"
        self.user_id = user_id or "anonymous"
        self.trace_id = None
        self.config = LangfuseConfig()
    
    def start_search_trace(self, query: str, search_config: Dict[str, Any]) -> str:
        """开始一个新的搜索追踪"""
        self.trace_id = f"deepsearch-{hash(query)}-{os.urandom(4).hex()}"
        
        return {
            "trace_id": self.trace_id,
            "trace_name": f"DeepSearch: {query}",
            "session_id": self.session_id,
            "trace_user_id": self.user_id,
            "trace_metadata": {
                "query": query,
                "config": search_config,
                "start_time": os.environ.get('START_TIME', ''),
            },
            "tags": ["deepsearch", "main-search"]
        }
    
    def track_brightdata_search(self, query: str, iteration: int, results_count: int) -> Dict[str, Any]:
        """追踪BrightData搜索调用"""
        return {
            "existing_trace_id": self.trace_id,
            "generation_name": f"brightdata-search-iter{iteration}",
            "parent_observation_id": f"search-phase-{iteration}",
            "trace_metadata": {
                "component": "brightdata",
                "query": query,
                "iteration": iteration,
                "results_count": results_count,
            },
            "tags": ["brightdata", "search", f"iter-{iteration}"]
        }
    
    def track_firecrawl_extraction(self, url: str, iteration: int, content_length: int) -> Dict[str, Any]:
        """追踪FireCrawl内容提取"""
        return {
            "existing_trace_id": self.trace_id,
            "generation_name": f"firecrawl-extract-iter{iteration}",
            "parent_observation_id": f"extract-phase-{iteration}",
            "trace_metadata": {
                "component": "firecrawl",
                "url": url,
                "iteration": iteration,
                "content_length": content_length,
            },
            "tags": ["firecrawl", "extraction", f"iter-{iteration}"]
        }
    
    def track_synthesis(self, sources_count: int, final: bool = False) -> Dict[str, Any]:
        """追踪综合阶段"""
        phase = "final-synthesis" if final else "interim-synthesis"
        return {
            "existing_trace_id": self.trace_id,
            "generation_name": phase,
            "trace_metadata": {
                "component": "synthesis",
                "sources_count": sources_count,
                "is_final": final,
            },
            "tags": ["synthesis", phase]
        }
    
    def track_evaluation(self, eval_type: str, score: float) -> Dict[str, Any]:
        """追踪评估结果"""
        return {
            "existing_trace_id": self.trace_id,
            "generation_name": f"evaluation-{eval_type}",
            "trace_metadata": {
                "component": "evaluation",
                "eval_type": eval_type,
                "score": score,
            },
            "tags": ["evaluation", eval_type]
        }


# 使用示例
"""
# 在DeepSearchEngine中使用
from src.clients.langfuse_config import DeepSearchLangfuseTracker

class DeepSearchEngine:
    def __init__(self):
        self.tracker = DeepSearchLangfuseTracker(
            session_id="user-session-123",
            user_id="user-123"
        )
    
    async def search(self, query: str):
        # 开始追踪
        trace_metadata = self.tracker.start_search_trace(
            query=query,
            search_config={"max_depth": 3, "max_iterations": 5}
        )
        
        # 在LiteLLM调用中使用
        response = await litellm.acompletion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": query}],
            metadata=trace_metadata
        )
        
        # 追踪BrightData搜索
        search_metadata = self.tracker.track_brightdata_search(
            query=query,
            iteration=1,
            results_count=10
        )
        
        # 在搜索调用中使用metadata
        ...
"""