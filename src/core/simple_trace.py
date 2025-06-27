"""
简化的追踪实现 - 遵循KISS和DRY原则
只保留核心功能，避免过度设计
"""

import time
import uuid
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class SimpleTrace:
    """简单的追踪管理器 - 专注于核心功能"""
    
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.session_id = None
        self.metadata = {
            "start_time": time.time(),
            "phases": {}
        }
    
    def init(self, session_id: str, question: str, **kwargs):
        """初始化追踪"""
        self.session_id = session_id
        self.metadata.update({
            "question": question,
            "trace_name": f"s3_workflow_{session_id}",
            **kwargs
        })
        return self.trace_id
    
    def to_langfuse_metadata(self, phase: str, use_case: str, iteration: Optional[int] = None) -> Dict[str, Any]:
        """生成Langfuse元数据 - 优化故事展示效果"""
        
        # 为不同阶段生成故事性的名称
        phase_emojis = {
            "search": "🔍",
            "select": "🤔", 
            "synthesize": "✍️"
        }
        
        use_case_names = {
            "agent": "AI智能体分析",
            "generation": "答案生成",
            "ragflow": "知识库搜索"
        }
        
        # 构建故事性的generation名称
        emoji = phase_emojis.get(phase, "📌")
        action = use_case_names.get(use_case, use_case)
        
        if iteration:
            generation_name = f"{emoji} {action} - 第{iteration}次"
        else:
            generation_name = f"{emoji} {action}"
        
        # 构建标签 - 便于过滤和分组
        tags = [
            "s3-framework",
            f"phase:{phase}",
            f"use_case:{use_case}"
        ]
        
        if iteration:
            tags.append(f"iteration:{iteration}")
        
        # 添加故事性的元数据
        story_metadata = {
            **self.metadata,
            "current_phase": {
                "name": phase,
                "emoji": emoji,
                "action": action,
                "iteration": iteration
            }
        }
        
        return {
            "trace_id": self.trace_id,
            "trace_name": self.metadata.get("trace_name"),
            "session_id": self.session_id,
            "generation_name": generation_name,
            "tags": tags,
            "trace_metadata": story_metadata,
            "version": "s3-v2.0"  # 版本信息
        }
    
    def record_phase(self, phase: str):
        """记录阶段指标的装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self._update_phase(phase, time.time() - start_time, "success")
                    return result
                except Exception as e:
                    self._update_phase(phase, time.time() - start_time, "failed", str(e))
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self._update_phase(phase, time.time() - start_time, "success")
                    return result
                except Exception as e:
                    self._update_phase(phase, time.time() - start_time, "failed", str(e))
                    raise
            
            # 根据函数类型返回相应的包装器
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        return decorator
    
    def _update_phase(self, phase: str, duration: float, status: str, error: Optional[str] = None):
        """更新阶段信息"""
        self.metadata["phases"][phase] = {
            "duration": duration,
            "status": status,
            "error": error
        }
    
    def finalize(self):
        """完成追踪并返回总结"""
        self.metadata["total_duration"] = time.time() - self.metadata["start_time"]
        return {
            "trace_id": self.trace_id,
            "duration": self.metadata["total_duration"],
            "phases": self.metadata["phases"]
        }


# 全局追踪实例 - 简化使用
_current_trace: Optional[SimpleTrace] = None

def init_trace(session_id: str, question: str, **kwargs) -> str:
    """初始化全局追踪"""
    global _current_trace
    _current_trace = SimpleTrace()
    return _current_trace.init(session_id, question, **kwargs)

def get_trace() -> Optional[SimpleTrace]:
    """获取当前追踪实例"""
    return _current_trace

def trace_phase(phase: str):
    """阶段追踪装饰器"""
    if _current_trace:
        return _current_trace.record_phase(phase)
    # 如果没有追踪，返回原函数
    return lambda func: func


# 使用示例：
import asyncio

class SimpleLiteLLMClient:
    """简化的LiteLLM客户端集成"""
    
    async def call_llm(self, model: str, messages: list, phase: str, use_case: str, **kwargs):
        """统一的LLM调用接口"""
        # 获取追踪元数据
        trace = get_trace()
        metadata = trace.to_langfuse_metadata(phase, use_case) if trace else {}
        
        # 调用LiteLLM
        from litellm import acompletion
        response = await acompletion(
            model=model,
            messages=messages,
            metadata=metadata,
            **kwargs
        )
        
        # 记录关键指标
        if trace and hasattr(response, 'usage'):
            trace.metadata[f"{phase}_tokens"] = response.usage.total_tokens
        
        return response