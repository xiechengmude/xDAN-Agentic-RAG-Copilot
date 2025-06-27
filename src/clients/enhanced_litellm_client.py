"""
增强的LiteLLM客户端，集成Langfuse追踪功能
提供统一的LLM调用接口，自动处理追踪上下文
"""

import os
import time
import litellm
from litellm import completion, acompletion
from typing import Dict, Any, Optional, List, Union, AsyncIterator
import logging
from src.core.trace_context import TraceContext

logger = logging.getLogger(__name__)

class EnhancedLiteLLMClient:
    """增强的LiteLLM客户端，集成Langfuse追踪"""
    
    # 模型价格表（每1K tokens的价格，单位：美元）
    MODEL_PRICING = {
        "xdan-r2-qwen3": {"input": 0.001, "output": 0.002},
        "deepseek-chat": {"input": 0.0001, "output": 0.0002},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015}
    }
    
    def __init__(self, 
                 langfuse_public_key: Optional[str] = None,
                 langfuse_secret_key: Optional[str] = None,
                 langfuse_host: Optional[str] = None):
        """
        初始化增强的LiteLLM客户端
        
        Args:
            langfuse_public_key: Langfuse公钥
            langfuse_secret_key: Langfuse私钥
            langfuse_host: Langfuse服务地址
        """
        # 设置Langfuse环境变量
        if langfuse_public_key:
            os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_public_key
        if langfuse_secret_key:
            os.environ["LANGFUSE_SECRET_KEY"] = langfuse_secret_key
        if langfuse_host:
            os.environ["LANGFUSE_HOST"] = langfuse_host
        
        # 启用Langfuse回调
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        
        # 设置日志级别
        litellm.set_verbose = False
        
        logger.info("Enhanced LiteLLM client initialized with Langfuse integration")
    
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
        # 构建追踪元数据
        metadata = self._build_trace_metadata(
            model=model,
            use_case=use_case,
            phase=phase,
            iteration=iteration,
            **kwargs
        )
        
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
            
            # 更新追踪指标
            self._update_trace_metrics(
                response=response,
                phase=phase,
                start_time=start_time,
                model=model
            )
            
            return response
            
        except Exception as e:
            # 记录错误
            TraceContext.update_metadata(f"{phase}_error", str(e))
            TraceContext.update_metadata(f"{phase}_error_type", type(e).__name__)
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
        # 构建追踪元数据
        metadata = self._build_trace_metadata(
            model=model,
            use_case=use_case,
            phase=phase,
            iteration=iteration,
            stream=stream,
            **kwargs
        )
        
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
                # 包装流式响应以收集指标
                return self._wrap_stream_response(
                    response=response,
                    phase=phase,
                    start_time=start_time,
                    model=model
                )
            else:
                # 更新追踪指标
                self._update_trace_metrics(
                    response=response,
                    phase=phase,
                    start_time=start_time,
                    model=model
                )
                return response
                
        except Exception as e:
            # 记录错误
            TraceContext.update_metadata(f"{phase}_error", str(e))
            TraceContext.update_metadata(f"{phase}_error_type", type(e).__name__)
            logger.error(f"Async LLM call failed in {phase} phase: {e}")
            raise
    
    def _build_trace_metadata(
        self,
        model: str,
        use_case: str,
        phase: str,
        iteration: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """构建追踪元数据"""
        
        # 获取基础Langfuse元数据
        metadata = TraceContext.to_langfuse_metadata()
        
        # 生成generation名称
        generation_name = f"{phase}_{use_case}"
        if iteration:
            generation_name = f"{generation_name}_iter_{iteration}"
        
        # 添加generation级别参数
        metadata.update({
            "generation_name": generation_name,
            "version": f"{phase}_v2.0",
            
            # 添加阶段标签
            "tags": metadata.get("tags", []) + [
                f"phase:{phase}",
                f"use_case:{use_case}",
                f"model:{model}"
            ]
        })
        
        # 添加迭代标签
        if iteration:
            metadata["tags"].append(f"iteration:{iteration}")
        
        # 添加流式标签
        if stream:
            metadata["tags"].append("streaming")
        
        # 添加自定义元数据
        metadata["trace_metadata"].update({
            "llm_config": {
                "model": model,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens"),
                "top_p": kwargs.get("top_p", 1.0),
                "stream": stream
            },
            "phase_info": {
                "phase": phase,
                "use_case": use_case,
                "iteration": iteration
            }
        })
        
        return metadata
    
    def _update_trace_metrics(
        self,
        response: Dict[str, Any],
        phase: str,
        start_time: float,
        model: str
    ):
        """更新追踪指标"""
        
        duration = time.time() - start_time
        
        # 提取token使用量
        usage = getattr(response, 'usage', None)
        if usage:
            total_tokens = usage.total_tokens
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            
            # 计算成本
            cost = self._calculate_cost(
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # 更新追踪上下文
            TraceContext.update_metadata(f"{phase}_duration", duration)
            TraceContext.update_metadata(f"{phase}_total_tokens", total_tokens)
            TraceContext.update_metadata(f"{phase}_input_tokens", input_tokens)
            TraceContext.update_metadata(f"{phase}_output_tokens", output_tokens)
            TraceContext.update_metadata(f"{phase}_cost", cost)
            TraceContext.update_metadata(f"{phase}_model", model)
            
            # 累加总指标
            self._accumulate_total_metrics(
                tokens=total_tokens,
                cost=cost
            )
    
    async def _wrap_stream_response(
        self,
        response: AsyncIterator[Dict[str, Any]],
        phase: str,
        start_time: float,
        model: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """包装流式响应以收集指标"""
        
        total_content = ""
        total_tokens = 0
        
        async for chunk in response:
            # 收集内容
            if hasattr(chunk, 'choices') and chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    total_content += delta.content
            
            # 传递chunk
            yield chunk
        
        # 流结束后更新指标
        duration = time.time() - start_time
        
        # 估算token数（简单估算：1 token ≈ 4字符）
        estimated_tokens = len(total_content) // 4
        
        # 更新追踪上下文
        TraceContext.update_metadata(f"{phase}_duration", duration)
        TraceContext.update_metadata(f"{phase}_estimated_tokens", estimated_tokens)
        TraceContext.update_metadata(f"{phase}_content_length", len(total_content))
        TraceContext.update_metadata(f"{phase}_model", model)
        TraceContext.update_metadata(f"{phase}_stream", True)
    
    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算调用成本"""
        
        # 获取模型价格
        pricing = self.MODEL_PRICING.get(model, {"input": 0.001, "output": 0.001})
        
        # 计算成本（价格是每1K tokens）
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def _accumulate_total_metrics(self, tokens: int, cost: float):
        """累加总指标"""
        
        context = TraceContext.get_current()
        metadata = context.get('metadata', {})
        
        # 累加tokens
        current_total_tokens = metadata.get('accumulated_tokens', 0)
        metadata['accumulated_tokens'] = current_total_tokens + tokens
        
        # 累加成本
        current_total_cost = metadata.get('accumulated_cost', 0.0)
        metadata['accumulated_cost'] = current_total_cost + cost
        
        TraceContext.update_metadata('accumulated_tokens', metadata['accumulated_tokens'])
        TraceContext.update_metadata('accumulated_cost', metadata['accumulated_cost'])