#!/usr/bin/env python3
"""
LiteLLM SDK客户端 - 内核服务集成
直接使用LiteLLM SDK而非API调用，提供统一的LLM访问接口
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
import json

try:
    import litellm
    from litellm import completion, acompletion
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("LiteLLM SDK未安装，请运行: pip install litellm")

logger = logging.getLogger(__name__)

class LiteLLMSDKClient:
    """
    LiteLLM SDK客户端 - 内核服务模式
    
    职责：
    1. 提供统一的多模型LLM访问接口
    2. 智能路由和成本优化
    3. 错误处理和自动重试
    4. 流式和非流式响应支持
    """
    
    def __init__(self, config_path: str = None, **kwargs):
        """
        初始化LiteLLM SDK客户端
        
        Args:
            config_path: LiteLLM配置文件路径
            **kwargs: 额外配置参数
        """
        if not SDK_AVAILABLE:
            raise ImportError("LiteLLM SDK未安装，请安装: pip install litellm")
        
        # 配置LiteLLM
        self._setup_litellm_config(config_path, **kwargs)
        
        # 设置默认模型（从环境变量读取）
        self.default_model = kwargs.get('default_model') or os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')
        
        # 备用模型（从环境变量读取）
        fallback_env = os.getenv('FALLBACK_MODELS', 'gpt-3.5-turbo,claude-3-haiku')
        self.fallback_models = kwargs.get('fallback_models') or fallback_env.split(',')
        
        # S3框架专用模型配置
        self.agent_model = os.getenv('AGENT_MODEL', self.default_model)  # 智能体推理模型
        self.generation_model = os.getenv('GENERATION_MODEL', self.default_model)  # 答案生成模型
        
        # 温度配置
        self.agent_temperature = float(os.getenv('AGENT_TEMPERATURE', '0.1'))
        self.generation_temperature = float(os.getenv('GENERATION_TEMPERATURE', '0.7'))
        
        # Token限制
        self.agent_max_tokens = int(os.getenv('AGENT_MAX_TOKENS', '1000'))
        self.generation_max_tokens = int(os.getenv('MAX_TOKENS', '2000'))
        
        # 性能统计
        self.request_count = 0
        self.error_count = 0
        
        logger.info("LiteLLM SDK客户端初始化完成")
        logger.info(f"默认模型: {self.default_model}")
        logger.info(f"智能体模型: {self.agent_model}")
        logger.info(f"生成模型: {self.generation_model}")
        logger.info(f"备用模型: {self.fallback_models}")
    
    def _setup_litellm_config(self, config_path: str = None, **kwargs):
        """设置LiteLLM配置"""
        try:
            # 基础配置
            litellm.drop_params = True  # 自动过滤不支持的参数
            litellm.set_verbose = kwargs.get('verbose', False)
            
            # 从配置文件获取API密钥
            config = get_config()
            llm_providers = config.get('llm_providers', {})
            
            # 配置API密钥
            api_keys = {
                'OPENAI_API_KEY': llm_providers.get('openai', {}).get('api_key') or os.getenv('OPENAI_API_KEY'),
                'ANTHROPIC_API_KEY': llm_providers.get('anthropic', {}).get('api_key') or os.getenv('ANTHROPIC_API_KEY'),
                'DEEPSEEK_API_KEY': llm_providers.get('deepseek', {}).get('api_key') or os.getenv('DEEPSEEK_API_KEY'),
                'GEMINI_API_KEY': llm_providers.get('gemini', {}).get('api_key') or os.getenv('GEMINI_API_KEY'),
            }
            
            # 设置可用的API密钥
            available_providers = []
            for key, value in api_keys.items():
                if value:
                    os.environ[key] = value
                    provider = key.replace('_API_KEY', '').lower()
                    available_providers.append(provider)
            
            logger.info(f"可用的LLM提供商: {available_providers}")
            
            # 如果有配置文件，加载配置
            if config_path and os.path.exists(config_path):
                litellm.utils.load_config(config_path)
                logger.info(f"已加载LiteLLM配置文件: {config_path}")
            
            # 配置路由策略
            enable_routing = kwargs.get('enable_routing')
            if enable_routing is None:
                enable_routing = os.getenv('ENABLE_ROUTING', 'true').lower() == 'true'
            
            if enable_routing:
                self._setup_routing()
            
        except Exception as e:
            logger.error(f"LiteLLM配置失败: {e}")
            raise
    
    def _setup_routing(self):
        """设置智能路由"""
        try:
            # 定义模型组和路由策略
            model_list = []
            
            # OpenAI模型
            if os.getenv('OPENAI_API_KEY'):
                model_list.extend([
                    {
                        "model_name": "gpt-4o",
                        "litellm_params": {
                            "model": "gpt-4o",
                            "api_key": os.getenv('OPENAI_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": 0.000005,
                            "supports_function_calling": True
                        }
                    },
                    {
                        "model_name": "gpt-4o-mini",
                        "litellm_params": {
                            "model": "gpt-4o-mini", 
                            "api_key": os.getenv('OPENAI_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": 0.000001,
                            "supports_function_calling": True
                        }
                    },
                    {
                        "model_name": "gpt-3.5-turbo",
                        "litellm_params": {
                            "model": "gpt-3.5-turbo",
                            "api_key": os.getenv('OPENAI_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": 0.0000005,
                            "supports_function_calling": True
                        }
                    }
                ])
            
            # Anthropic模型
            if os.getenv('ANTHROPIC_API_KEY'):
                model_list.extend([
                    {
                        "model_name": "claude-3-5-sonnet",
                        "litellm_params": {
                            "model": "anthropic/claude-3-5-sonnet-20241022",
                            "api_key": os.getenv('ANTHROPIC_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": 0.000003,
                            "supports_function_calling": True
                        }
                    },
                    {
                        "model_name": "claude-3-haiku",
                        "litellm_params": {
                            "model": "anthropic/claude-3-haiku-20240307",
                            "api_key": os.getenv('ANTHROPIC_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": 0.0000002,
                            "supports_function_calling": True
                        }
                    }
                ])
            
            # DeepSeek模型（成本极低）
            if os.getenv('DEEPSEEK_API_KEY'):
                model_list.append({
                    "model_name": "deepseek-chat",
                    "litellm_params": {
                        "model": "deepseek/deepseek-chat",
                        "api_key": os.getenv('DEEPSEEK_API_KEY'),
                        "base_url": "https://api.deepseek.com/v1"
                    },
                    "model_info": {
                        "cost_per_token": 0.0000001,
                        "supports_function_calling": True
                    }
                })
            
            # 配置路由器
            if model_list:
                from litellm import Router
                # 路由配置从环境变量读取
                routing_strategy = os.getenv('ROUTING_STRATEGY', 'cost-based')
                retry_count = int(os.getenv('RETRY_COUNT', '3'))
                
                self.router = Router(
                    model_list=model_list,
                    routing_strategy=routing_strategy,
                    num_retries=retry_count
                )
                logger.info("LiteLLM路由器配置完成")
            else:
                self.router = None
                logger.warning("没有可用的API密钥，路由器未配置")
            
        except Exception as e:
            logger.warning(f"路由配置失败: {e}")
            self.router = None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        use_case: str = "general",  # "agent" | "generation" | "general"
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """
        聊天完成接口
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式返回
            **kwargs: 其他参数
            
        Returns:
            完成响应或流式生成器
        """
        self.request_count += 1
        
        # 根据使用场景选择模型和参数
        if not model:
            if use_case == "agent":
                model = self.agent_model
                temperature = temperature if temperature is not None else self.agent_temperature
                max_tokens = max_tokens if max_tokens is not None else self.agent_max_tokens
            elif use_case == "generation":
                model = self.generation_model
                temperature = temperature if temperature is not None else self.generation_temperature
                max_tokens = max_tokens if max_tokens is not None else self.generation_max_tokens
            else:
                model = self.default_model
                temperature = temperature if temperature is not None else 0.7
                max_tokens = max_tokens if max_tokens is not None else 2000
        else:
            # 使用默认参数
            temperature = temperature if temperature is not None else 0.7
            max_tokens = max_tokens if max_tokens is not None else 2000
        
        try:
            if stream:
                return await self._stream_completion(messages, model, temperature, max_tokens, **kwargs)
            else:
                return await self._completion(messages, model, temperature, max_tokens, **kwargs)
                
        except Exception as e:
            self.error_count += 1
            logger.error(f"聊天完成失败: {e}")
            
            # 尝试备用模型
            for fallback_model in self.fallback_models:
                try:
                    logger.info(f"尝试备用模型: {fallback_model}")
                    if stream:
                        return await self._stream_completion(messages, fallback_model, temperature, max_tokens, **kwargs)
                    else:
                        return await self._completion(messages, fallback_model, temperature, max_tokens, **kwargs)
                except Exception as fallback_error:
                    logger.warning(f"备用模型 {fallback_model} 也失败: {fallback_error}")
                    continue
            
            # 所有模型都失败
            raise Exception(f"所有模型都不可用，最后错误: {e}")
    
    async def _completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict:
        """非流式完成"""
        try:
            if self.router:
                # 使用路由器
                response = await self.router.acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            else:
                # 直接使用LiteLLM
                response = await acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
            
            return response
            
        except Exception as e:
            logger.error(f"模型 {model} 完成失败: {e}")
            raise
    
    async def _stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> AsyncGenerator[Dict, None]:
        """流式完成"""
        try:
            if self.router:
                # 使用路由器进行流式调用
                response_stream = await self.router.acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )
            else:
                # 直接使用LiteLLM进行流式调用
                response_stream = await acompletion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs
                )
            
            # 异步迭代流式响应
            async for chunk in response_stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"模型 {model} 流式完成失败: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        models = []
        
        if self.router:
            for model_config in self.router.model_list:
                models.append(model_config["model_name"])
        else:
            # 基于API密钥推断可用模型
            if os.getenv('OPENAI_API_KEY'):
                models.extend(['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'])
            if os.getenv('ANTHROPIC_API_KEY'):
                models.extend(['claude-3-5-sonnet', 'claude-3-haiku'])
            if os.getenv('DEEPSEEK_API_KEY'):
                models.append('deepseek-chat')
        
        return models
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """获取模型信息"""
        if self.router:
            for model_config in self.router.model_list:
                if model_config["model_name"] == model:
                    return model_config.get("model_info", {})
        
        # 默认信息
        return {
            "cost_per_token": 0.000001,
            "supports_function_calling": True,
            "provider": "unknown"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        success_rate = ((self.request_count - self.error_count) / max(self.request_count, 1)) * 100
        
        return {
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "available_models": self.get_available_models(),
            "model_config": {
                "default_model": self.default_model,
                "agent_model": self.agent_model,
                "generation_model": self.generation_model,
                "fallback_models": self.fallback_models
            },
            "temperature_config": {
                "agent_temperature": self.agent_temperature,
                "generation_temperature": self.generation_temperature
            },
            "router_enabled": self.router is not None
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "service": "LiteLLM SDK",
            "status": "unknown",
            "available_models": [],
            "test_results": {}
        }
        
        try:
            # 获取可用模型
            available_models = self.get_available_models()
            health_status["available_models"] = available_models
            
            if not available_models:
                health_status["status"] = "no_models"
                health_status["message"] = "没有可用的模型"
                return health_status
            
            # 测试默认模型
            test_messages = [{"role": "user", "content": "Hello, this is a health check."}]
            
            try:
                response = await self.chat_completion(
                    messages=test_messages,
                    model=self.default_model,
                    max_tokens=10,
                    temperature=0
                )
                
                if response and response.choices:
                    health_status["status"] = "healthy"
                    health_status["test_results"][self.default_model] = "success"
                else:
                    health_status["status"] = "degraded"
                    health_status["test_results"][self.default_model] = "no_response"
                    
            except Exception as e:
                health_status["status"] = "degraded"
                health_status["test_results"][self.default_model] = f"error: {e}"
            
            return health_status
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
            return health_status

# 全局客户端实例（单例模式）
_global_client: Optional[LiteLLMSDKClient] = None

def get_litellm_client(**kwargs) -> LiteLLMSDKClient:
    """获取全局LiteLLM客户端实例"""
    global _global_client
    
    if _global_client is None:
        _global_client = LiteLLMSDKClient(**kwargs)
    
    return _global_client

def reset_litellm_client():
    """重置全局客户端（用于测试）"""
    global _global_client
    _global_client = None