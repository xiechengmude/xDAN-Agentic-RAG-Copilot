"""
增强的LiteLLM客户端
提供统一的LLM调用接口
"""

import os
import time
import litellm
from litellm import completion, acompletion
from typing import Dict, Any, Optional, List, Union, AsyncIterator
import logging
# TraceContext 已移除

logger = logging.getLogger(__name__)

class EnhancedLiteLLMClient:
    """增强的LiteLLM客户端"""
    
    # 模型价格表（每1K tokens的价格，单位：美元）
    MODEL_PRICING = {
        "xdan-r2-qwen3": {"input": 0.001, "output": 0.002},
        "deepseek-chat": {"input": 0.0001, "output": 0.0002},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015}
    }
    
    def __init__(self):
        """
        初始化增强的LiteLLM客户端
        """
        # 设置DeepSeek的API配置
        os.environ["DEEPSEEK_API_KEY"] = "sk-6a32ae2b5dc440558aa628eec3dfda07"
        os.environ["DEEPSEEK_API_BASE"] = "https://api.deepseek.com/v1"
        
        # 设置OpenAI兼容接口配置（用于deepseek-chat）
        os.environ["OPENAI_API_KEY"] = "sk-6a32ae2b5dc440558aa628eec3dfda07"
        os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com/v1"
        
        # 禁用所有回调
        litellm.success_callback = []
        litellm.failure_callback = []
        
        # 设置日志级别
        litellm.set_verbose = False
        
        logger.info("Enhanced LiteLLM client initialized")
    
    def call_with_trace(
        self,
        model: str,
        messages: List[Dict[str, str]],
        use_case: str,
        phase: str,
        iteration: Optional[int] = None,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        带追踪的同步LLM调用
        
        Args:
            model: 模型名称
            messages: 消息列表
            use_case: 使用场景（agent/generation）
            phase: 当前阶段（search/select/synthesize）
            iteration: 迭代次数
            **kwargs: 其他LiteLLM参数
            
        Returns:
            LLM响应
        """
        # 构建基本元数据
        metadata = {
            "use_case": use_case,
            "phase": phase,
            "iteration": iteration
        }
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 执行LLM调用
            response = completion(
                model=model,
                messages=messages,
                metadata=metadata,
                **kwargs
            )
            
            # 记录耗时
            duration = time.time() - start_time
            logger.debug(f"{phase} phase completed in {duration:.2f}s")
            
            return response
            
        except Exception as e:
            # 记录错误
            logger.error(f"LLM call failed in {phase} phase: {e}")
            raise
    
    async def acall_with_trace(
        self,
        model: str,
        messages: List[Dict[str, str]],
        use_case: str,
        phase: str,
        iteration: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        带追踪的异步LLM调用
        
        Args:
            model: 模型名称
            messages: 消息列表
            use_case: 使用场景（agent/generation）
            phase: 当前阶段（search/select/synthesize）
            iteration: 迭代次数
            stream: 是否流式响应
            **kwargs: 其他LiteLLM参数
            
        Returns:
            LLM响应或流式响应生成器
        """
        # 构建基本元数据
        metadata = {
            "use_case": use_case,
            "phase": phase,
            "iteration": iteration,
            "stream": stream
        }
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 执行异步LLM调用
            response = await acompletion(
                model=model,
                messages=messages,
                metadata=metadata,
                stream=stream,
                **kwargs
            )
            
            if stream:
                # 直接返回流式响应
                return response
            else:
                # 记录耗时
                duration = time.time() - start_time
                logger.debug(f"{phase} phase completed in {duration:.2f}s")
                return response
                
        except Exception as e:
            # 记录错误
            logger.error(f"Async LLM call failed in {phase} phase: {e}")
            raise
    
    
    
    
    
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        use_case: str = "generation",
        phase: str = "default",
        iteration: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], AsyncIterator[Dict[str, Any]]]:
        """
        兼容性方法：提供chat_completion接口
        
        Args:
            messages: 消息列表
            use_case: 使用场景（agent/generation）
            phase: 当前阶段
            iteration: 迭代次数
            stream: 是否流式响应
            **kwargs: 其他参数，包括model
            
        Returns:
            LLM响应
        """
        # 从kwargs中提取model，如果没有则使用默认值
        model = kwargs.pop('model', 'deepseek-chat')
        
        # 修正DeepSeek模型格式 - 使用OpenAI兼容格式
        if model == 'deepseek-chat':
            # 使用openai格式，因为DeepSeek API兼容OpenAI
            model = 'openai/deepseek-chat'
            kwargs['api_key'] = "sk-6a32ae2b5dc440558aa628eec3dfda07"
            kwargs['api_base'] = "https://api.deepseek.com/v1"
        
        return await self.acall_with_trace(
            model=model,
            messages=messages,
            use_case=use_case,
            phase=phase,
            iteration=iteration,
            stream=stream,
            **kwargs
        )