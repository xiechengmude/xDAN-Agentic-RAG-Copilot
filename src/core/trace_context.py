"""
全链路追踪上下文管理器
用于在整个S3框架中传递和管理追踪信息
"""

from contextvars import ContextVar
from typing import Optional, Dict, Any, List
import uuid
import time
from datetime import datetime

# 全局追踪上下文变量
trace_context: ContextVar[Dict[str, Any]] = ContextVar('trace_context', default={})

class TraceContext:
    """统一的追踪上下文管理器"""
    
    @staticmethod
    def init_trace(
        session_id: str,
        user_id: Optional[str] = None,
        question: Optional[str] = None,
        dataset_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        初始化追踪上下文
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            question: 用户问题
            dataset_ids: 数据集ID列表
            metadata: 额外的元数据
            
        Returns:
            trace_id: 生成的追踪ID
        """
        trace_id = str(uuid.uuid4())
        
        context = {
            # 基础追踪信息
            'trace_id': trace_id,
            'session_id': session_id,
            'user_id': user_id,
            'trace_name': f"s3_workflow_{session_id}",
            'tags': ['s3-framework', 'rag'],
            
            # 请求信息
            'question': question,
            'dataset_ids': dataset_ids or [],
            
            # 元数据
            'metadata': {
                'framework': 's3',
                'version': '2.0',
                'start_time': time.time(),
                'timestamp': datetime.utcnow().isoformat(),
                **(metadata or {})
            },
            
            # 阶段追踪
            'phases': {
                'search': {'status': 'pending'},
                'select': {'status': 'pending'},
                'synthesize': {'status': 'pending'}
            },
            
            # 观察点ID管理
            'current_observation_id': None,
            'observation_stack': []
        }
        
        trace_context.set(context)
        return trace_id
    
    @staticmethod
    def get_current() -> Dict[str, Any]:
        """获取当前追踪上下文"""
        return trace_context.get()
    
    @staticmethod
    def get_trace_id() -> Optional[str]:
        """获取当前追踪ID"""
        context = trace_context.get()
        return context.get('trace_id')
    
    @staticmethod
    def update_metadata(key: str, value: Any):
        """更新追踪元数据"""
        context = trace_context.get()
        if 'metadata' not in context:
            context['metadata'] = {}
        context['metadata'][key] = value
        trace_context.set(context)
    
    @staticmethod
    def add_tag(tag: str):
        """添加标签"""
        context = trace_context.get()
        if 'tags' not in context:
            context['tags'] = []
        if tag not in context['tags']:
            context['tags'].append(tag)
        trace_context.set(context)
    
    @staticmethod
    def start_phase(phase: str):
        """开始一个阶段"""
        context = trace_context.get()
        if 'phases' not in context:
            context['phases'] = {}
        
        context['phases'][phase] = {
            'status': 'in_progress',
            'start_time': time.time()
        }
        
        # 创建阶段observation
        observation_id = f"{phase}_{uuid.uuid4().hex[:8]}"
        context['current_observation_id'] = observation_id
        context['observation_stack'].append(observation_id)
        
        trace_context.set(context)
        return observation_id
    
    @staticmethod
    def end_phase(phase: str, status: str = 'completed', error: Optional[str] = None):
        """结束一个阶段"""
        context = trace_context.get()
        
        if phase in context.get('phases', {}):
            phase_data = context['phases'][phase]
            phase_data['status'] = status
            phase_data['end_time'] = time.time()
            phase_data['duration'] = phase_data['end_time'] - phase_data['start_time']
            
            if error:
                phase_data['error'] = error
            
            # 更新总体元数据
            TraceContext.update_metadata(f'{phase}_duration', phase_data['duration'])
            TraceContext.update_metadata(f'{phase}_status', status)
        
        # 弹出observation栈
        if context.get('observation_stack'):
            context['observation_stack'].pop()
            if context['observation_stack']:
                context['current_observation_id'] = context['observation_stack'][-1]
            else:
                context['current_observation_id'] = None
        
        trace_context.set(context)
    
    @staticmethod
    def add_search_iteration(iteration: int, query: str, results_count: int, duration: float):
        """添加搜索迭代信息"""
        context = trace_context.get()
        
        if 'search_iterations' not in context['metadata']:
            context['metadata']['search_iterations'] = []
        
        context['metadata']['search_iterations'].append({
            'iteration': iteration,
            'query': query,
            'results_count': results_count,
            'duration': duration
        })
        
        # 更新总迭代次数
        context['metadata']['total_iterations'] = iteration
        
        trace_context.set(context)
    
    @staticmethod
    def set_agent_decision(decision: str, selected_count: int, reasoning: Optional[str] = None):
        """设置Agent决策信息"""
        context = trace_context.get()
        
        context['metadata']['agent_decision'] = {
            'action': decision,
            'selected_count': selected_count,
            'reasoning': reasoning,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        trace_context.set(context)
    
    @staticmethod
    def set_final_metrics(
        total_tokens: int,
        total_cost: float,
        answer_length: int,
        status: str = 'success'
    ):
        """设置最终指标"""
        context = trace_context.get()
        
        total_duration = time.time() - context['metadata']['start_time']
        
        context['metadata'].update({
            'total_duration': total_duration,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'answer_length': answer_length,
            'final_status': status,
            'end_time': time.time(),
            'end_timestamp': datetime.utcnow().isoformat()
        })
        
        trace_context.set(context)
    
    @staticmethod
    def to_langfuse_metadata() -> Dict[str, Any]:
        """
        转换为Langfuse兼容的元数据格式
        
        Returns:
            适用于LiteLLM metadata参数的字典
        """
        context = trace_context.get()
        
        if not context:
            return {}
        
        return {
            # Trace级别参数
            "trace_id": context.get('trace_id'),
            "trace_name": context.get('trace_name'),
            "session_id": context.get('session_id'),
            "trace_user_id": context.get('user_id'),
            "tags": context.get('tags', []),
            
            # Generation级别参数
            "parent_observation_id": context.get('current_observation_id'),
            
            # 自定义元数据
            "trace_metadata": context.get('metadata', {}),
            
            # 调试模式
            "debug_langfuse": True
        }
    
    @staticmethod
    def clear():
        """清除追踪上下文"""
        trace_context.set({})


class TracePhase:
    """追踪阶段的上下文管理器"""
    
    def __init__(self, phase: str):
        self.phase = phase
        self.observation_id = None
    
    def __enter__(self):
        self.observation_id = TraceContext.start_phase(self.phase)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            TraceContext.end_phase(self.phase, status='failed', error=str(exc_val))
        else:
            TraceContext.end_phase(self.phase, status='completed')
        
        # 不吞掉异常
        return False