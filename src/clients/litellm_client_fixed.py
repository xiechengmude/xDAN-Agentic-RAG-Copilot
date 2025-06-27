"""
临时修复版本的 LiteLLM 客户端
专门解决流式响应的 async for 问题
"""

from typing import AsyncGenerator, Dict, List, Union
from litellm import acompletion

class LiteLLMSDKClientV2Fixed:
    def __init__(self, config: dict):
        self.config = config
        self.llm_providers = config.get('llm_providers', {})
        self.proxy_config = None
        self.router = None
        
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator:
        """
        创建一个异步生成器用于流式响应
        注意：这个方法本身不是 async 的，但返回一个 AsyncGenerator
        """
        # 选择正确的配置
        llm_providers = self.llm_providers
        if 'openai' in llm_providers:
            openai_config = llm_providers['openai']
            # 不使用 await，直接返回 acompletion 的结果
            return acompletion(
                model="openai/deepseek-chat",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                api_key=openai_config['api_key'],
                api_base=openai_config['base_url'],
                **kwargs
            )
        else:
            # 默认配置
            return acompletion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        use_case: str = "general",
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """
        聊天完成接口 - 修复版
        """
        # 使用默认值
        if model is None:
            model = "deepseek-chat"
        if temperature is None:
            temperature = 0.7
        if max_tokens is None:
            max_tokens = 2000
            
        if stream:
            # 对于流式响应，直接返回 AsyncGenerator
            return self.chat_completion_stream(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        else:
            # 对于非流式响应，使用 await
            llm_providers = self.llm_providers
            if 'openai' in llm_providers:
                openai_config = llm_providers['openai']
                return await acompletion(
                    model="openai/deepseek-chat",
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                    api_key=openai_config['api_key'],
                    api_base=openai_config['base_url'],
                    **kwargs
                )
            else:
                return await acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                    **kwargs
                )