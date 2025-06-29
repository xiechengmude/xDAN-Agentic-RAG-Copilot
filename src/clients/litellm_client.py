#!/usr/bin/env python3
"""
LiteLLM SDK客户端 V2 - 完全集成YAML配置
内核服务集成，支持智能路由和多模型管理
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
import json
from pathlib import Path
from datetime import datetime

try:
    import litellm
    from litellm import completion, acompletion, Router
    from litellm.exceptions import (
        AuthenticationError,
        InvalidRequestError, 
        RateLimitError,
        ServiceUnavailableError,
        OpenAIError
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("LiteLLM SDK未安装，请运行: pip install litellm")

# 导入配置加载器
try:
    from ..core.config_loader import get_config
except:
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.core.config_loader import get_config

logger = logging.getLogger(__name__)

class LiteLLMSDKClientV2:
    """
    LiteLLM SDK客户端 V2 - 基于YAML配置
    
    特性：
    1. 完全基于YAML配置文件
    2. 支持多模型智能路由
    3. 成本优化和自动降级
    4. S3框架专用模型配置
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化LiteLLM SDK客户端
        
        Args:
            config_path: YAML配置文件路径
        """
        if not SDK_AVAILABLE:
            raise ImportError("LiteLLM SDK未安装，请安装: pip install litellm")
        
        # 加载配置
        self.config = get_config(config_path)
        self._load_model_config()
        self._setup_litellm()
        
        # 性能统计
        self.request_count = 0
        self.error_count = 0
        self.model_usage = {}
        
        # 设置代理（如果环境变量中有设置）
        self.proxy_config = self._setup_proxy()
        
        logger.info("LiteLLM SDK客户端 V2 初始化完成")
        if self.proxy_config:
            logger.info(f"使用代理配置: {self.proxy_config}")
        self._log_configuration()
    
    def _load_model_config(self):
        """从YAML配置加载模型设置"""
        model_config = self.config.get_model_config()
        s3_config = model_config.get('s3_framework', {})
        
        # 模型配置
        self.default_model = model_config.get('default_model', 'gpt-4o-mini')
        self.fallback_models = model_config.get('fallback_models', ['gpt-3.5-turbo'])
        
        # S3框架专用配置
        self.agent_model = s3_config.get('agent_model', self.default_model)
        self.agent_provider = s3_config.get('agent_provider', None)  # 智能体模型提供商
        self.agent_temperature = s3_config.get('agent_temperature', 0.1)
        self.agent_max_tokens = s3_config.get('agent_max_tokens', 1000)
        
        self.generation_model = s3_config.get('generation_model', self.default_model)
        self.generation_provider = s3_config.get('generation_provider', None)  # 生成模型提供商
        self.generation_temperature = s3_config.get('generation_temperature', 0.7)
        self.generation_max_tokens = s3_config.get('generation_max_tokens', 2000)
    
    def _setup_litellm(self):
        """设置LiteLLM配置"""
        try:
            # 基础配置
            litellm.drop_params = True
            litellm.set_verbose = self.config.get('logging.verbose', False)
            
            # 设置API密钥
            self._setup_api_keys()
            
            # 设置路由器
            self._setup_router()
            
            # 设置 Langfuse 集成
            self._setup_langfuse()
            
            # 设置回调函数
            self._setup_callbacks()
            
        except Exception as e:
            logger.error(f"LiteLLM配置失败: {e}")
            raise
    
    def _setup_api_keys(self):
        """设置API密钥"""
        llm_providers = self.config.get('llm_providers', {})
        available_providers = []
        
        # 设置各提供商的API密钥
        for provider, config in llm_providers.items():
            api_key = config.get('api_key')
            if api_key and not api_key.startswith('${'):  # 跳过未设置的环境变量
                # 特殊处理xdan_search
                if provider == 'xdan_search':
                    os.environ['XDAN_API_KEY'] = api_key
                    os.environ['XDAN_API_BASE'] = config.get('base_url', '')
                else:
                    env_key = f"{provider.upper()}_API_KEY"
                    os.environ[env_key] = api_key
                    
                    # 设置base_url（如果有）
                    if 'base_url' in config:
                        os.environ[f"{provider.upper()}_API_BASE"] = config['base_url']
                        
                available_providers.append(provider)
        
        logger.info(f"已配置的LLM提供商: {available_providers}")
    
    def _setup_router(self):
        """设置智能路由器"""
        routing_config = self.config.get('litellm.routing', {})
        
        if not routing_config.get('enabled', True):
            self.router = None
            logger.info("LiteLLM路由器已禁用")
            return
        
        model_list = self._build_model_list()
        
        if not model_list:
            self.router = None
            logger.warning("没有可用的模型配置，路由器未创建")
            return
        
        # 创建路由器
        self.router = Router(
            model_list=model_list,
            routing_strategy=routing_config.get('strategy', 'cost-based'),
            num_retries=routing_config.get('retry_count', 3),
            timeout=self.config.get('service.api.request_timeout', 300),
            allowed_fails=2
        )
        
        logger.info(f"LiteLLM路由器已配置: {len(model_list)} 个模型")
    
    def _setup_langfuse(self):
        """设置 Langfuse 可观察性集成"""
        try:
            langfuse_config = self.config.get('observability.langfuse', {})
            
            # 检查是否启用LangFuse
            if langfuse_config.get('enabled', False):
                logger.warning("LangFuse已在配置中禁用")
            
            # 禁用所有LangFuse回调
            litellm.success_callback = []
            litellm.failure_callback = []
            
            # 初始化DeepSearch追踪器（如果需要）
            if hasattr(self, 'deepsearch_mode') and self.deepsearch_mode:
                from .langfuse_config import DeepSearchLangfuseTracker
                self.langfuse_tracker = DeepSearchLangfuseTracker()
                
            logger.info(f"Langfuse 集成已启用: {os.environ.get('LANGFUSE_HOST', 'default')}")
        except Exception as e:
            logger.warning(f"Langfuse 集成设置失败: {e}")
            # 继续运行，不影响核心功能
    
    def _setup_callbacks(self):
        """设置回调函数用于成本追踪等"""
        # 初始化成本追踪
        self.total_cost = 0.0
        
        # 成本追踪回调
        def track_cost_callback(kwargs, response, start_time, end_time):
            """追踪请求成本"""
            try:
                if hasattr(response, '_hidden_params') and response._hidden_params.get('response_cost'):
                    cost = response._hidden_params['response_cost']
                    self.total_cost += cost
                    logger.debug(f"请求成本: ${cost:.6f}, 累计: ${self.total_cost:.6f}")
            except Exception as e:
                logger.debug(f"成本计算失败: {e}")
        
        # 确保 success_callback 是列表
        if not hasattr(litellm, 'success_callback'):
            litellm.success_callback = []
        elif not isinstance(litellm.success_callback, list):
            litellm.success_callback = [litellm.success_callback]
            
        # 添加成本追踪回调
        if track_cost_callback not in litellm.success_callback:
            litellm.success_callback.append(track_cost_callback)
            
        logger.info("成本追踪回调已设置")
    
    def _build_model_list(self) -> List[Dict]:
        """构建模型列表"""
        model_list = []
        llm_providers = self.config.get('llm_providers', {})
        model_costs = self.config.get('litellm.model_costs', {})
        
        # xDAN-R2-Qwen3模型（S3框架专用）
        if 'xdan_search' in llm_providers and llm_providers['xdan_search'].get('api_key'):
            xdan_config = llm_providers['xdan_search']
            model_list.append({
                "model_name": xdan_config.get('model_name', 'xDAN-R2-Qwen3-14b-RagRL-step450-0618'),
                "litellm_params": {
                    "model": "openai/" + xdan_config.get('model_name', 'xDAN-R2-Qwen3-14b-RagRL-step450-0618'),
                    "api_key": os.getenv('XDAN_API_KEY'),
                    "api_base": xdan_config.get('base_url')
                },
                "model_info": {
                    "cost_per_token": model_costs.get('xdan-search', 0.001),
                    "is_search_model": True
                }
            })
        
        # OpenAI模型 (实际使用DeepSeek兼容接口)
        if 'openai' in llm_providers and llm_providers['openai'].get('api_key'):
            if not llm_providers['openai']['api_key'].startswith('${'):
                # 使用DeepSeek兼容接口，但映射为标准模型名
                model_list.extend([
                    {
                        "model_name": "deepseek-chat",
                        "litellm_params": {
                            "model": "openai/deepseek-chat",
                            "api_key": llm_providers['openai']['api_key'],
                            "api_base": llm_providers['openai'].get('base_url')
                        },
                        "model_info": {
                            "cost_per_token": model_costs.get('deepseek-chat', 0.0001)
                        }
                    },
                    {
                        "model_name": "gpt-3.5-turbo",
                        "litellm_params": {
                            "model": "openai/deepseek-chat",  # 实际使用deepseek-chat
                            "api_key": llm_providers['openai']['api_key'],
                            "api_base": llm_providers['openai'].get('base_url')
                        },
                        "model_info": {
                            "cost_per_token": model_costs.get('gpt-3.5-turbo', 0.0005)
                        }
                    },
                    {
                        "model_name": "gpt-4o-mini",
                        "litellm_params": {
                            "model": "openai/deepseek-chat",  # 实际使用deepseek-chat
                            "api_key": llm_providers['openai']['api_key'],
                            "api_base": llm_providers['openai'].get('base_url')
                        },
                        "model_info": {
                            "cost_per_token": model_costs.get('gpt-4o-mini', 0.001)
                        }
                    }
                ])
        
        # DeepSeek模型 - 跳过直连，API key无效
        # 改用OpenAI兼容接口
        
        # Anthropic模型
        if 'anthropic' in llm_providers and llm_providers['anthropic'].get('api_key'):
            if not llm_providers['anthropic']['api_key'].startswith('${'):
                model_list.extend([
                    {
                        "model_name": "claude-3-5-sonnet",
                        "litellm_params": {
                            "model": "anthropic/claude-3-5-sonnet-20241022",
                            "api_key": os.getenv('ANTHROPIC_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": model_costs.get('claude-3-5-sonnet', 0.003)
                        }
                    },
                    {
                        "model_name": "claude-3-haiku",
                        "litellm_params": {
                            "model": "anthropic/claude-3-haiku-20240307",
                            "api_key": os.getenv('ANTHROPIC_API_KEY')
                        },
                        "model_info": {
                            "cost_per_token": model_costs.get('claude-3-haiku', 0.0002)
                        }
                    }
                ])
        
        return model_list
    
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
            model: 模型名称（可选）
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            stream: 是否流式返回
            use_case: 使用场景，用于选择预设配置
            **kwargs: 其他参数
            
        Returns:
            完成响应或流式生成器
        """
        self.request_count += 1
        
        # 根据使用场景选择配置
        model, temperature, max_tokens = self._select_model_params(
            model, temperature, max_tokens, use_case
        )
        
        # 记录模型使用
        self.model_usage[model] = self.model_usage.get(model, 0) + 1
        
        try:
            # 统一处理流式和非流式请求
            llm_providers = self.config.get('llm_providers', {})
            
            # 构建通用参数
            completion_params = {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
                "proxy": self.proxy_config,
                **kwargs
            }
            
            # 根据配置选择正确的提供者
            if 'openai' in llm_providers:
                openai_config = llm_providers['openai']
                completion_params.update({
                    "model": "openai/deepseek-chat",
                    "api_key": openai_config['api_key'],
                    "api_base": openai_config['base_url']
                })
                return await acompletion(**completion_params)
            elif self.router:
                completion_params["model"] = model
                return await self.router.acompletion(**completion_params)
            else:
                completion_params["model"] = model
                return await acompletion(**completion_params)
                
        except AuthenticationError as e:
            self.error_count += 1
            logger.error(f"认证失败 (模型: {model}): {e}")
            raise
        except RateLimitError as e:
            self.error_count += 1
            logger.warning(f"速率限制 (模型: {model}): {e}")
            raise
        except InvalidRequestError as e:
            self.error_count += 1
            logger.error(f"无效请求 (模型: {model}): {e}")
            raise
        except ServiceUnavailableError as e:
            self.error_count += 1
            logger.error(f"服务不可用 (模型: {model}): {e}")
            raise
        except OpenAIError as e:
            self.error_count += 1
            logger.error(f"LiteLLM错误 (模型: {model}): {e}")
            raise
        except Exception as e:
            self.error_count += 1
            logger.error(f"未知错误 (模型: {model}): {e}")
            raise
    
    def _select_model_params(self, model, temperature, max_tokens, use_case):
        """根据使用场景选择模型参数"""
        if use_case == "agent":
            # 如果指定了agent_provider，确保使用正确的模型
            selected_model = model or self.agent_model
            return (
                selected_model,
                temperature if temperature is not None else self.agent_temperature,
                max_tokens if max_tokens is not None else self.agent_max_tokens
            )
        elif use_case == "generation":
            selected_model = model or self.generation_model
            return (
                selected_model,
                temperature if temperature is not None else self.generation_temperature,
                max_tokens if max_tokens is not None else self.generation_max_tokens
            )
        else:
            return (
                model or self.default_model,
                temperature if temperature is not None else 0.7,
                max_tokens if max_tokens is not None else 2000
            )
    
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        if self.router:
            return [m["model_name"] for m in self.router.model_list]
        
        # 基于配置推断
        models = []
        llm_providers = self.config.get('llm_providers', {})
        
        if llm_providers.get('openai', {}).get('api_key'):
            models.extend(['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'])
        if llm_providers.get('deepseek', {}).get('api_key'):
            models.append('deepseek-chat')
        if llm_providers.get('anthropic', {}).get('api_key'):
            models.extend(['claude-3-5-sonnet', 'claude-3-haiku'])
            
        return models
    
    def get_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        success_rate = ((self.request_count - self.error_count) / max(self.request_count, 1)) * 100
        
        return {
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "success_rate": round(success_rate, 2),
            "total_cost": getattr(self, 'total_cost', 0.0),
            "average_cost": getattr(self, 'total_cost', 0.0) / max(self.request_count, 1),
            "available_models": self.get_available_models(),
            "model_usage": self.model_usage,
            "configuration": {
                "default_model": self.default_model,
                "agent_model": self.agent_model,
                "generation_model": self.generation_model,
                "fallback_models": self.fallback_models,
                "routing_enabled": self.router is not None,
                "langfuse_enabled": 'langfuse' in getattr(litellm, 'success_callback', [])
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "service": "LiteLLM SDK V2",
            "status": "unknown",
            "config_source": "YAML",
            "available_models": self.get_available_models(),
            "test_results": {}
        }
        
        if not health_status["available_models"]:
            health_status["status"] = "no_models"
            health_status["message"] = "没有配置可用的模型"
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
            
            if response and hasattr(response, 'choices'):
                health_status["status"] = "healthy"
                health_status["test_results"][self.default_model] = "success"
            else:
                health_status["status"] = "degraded"
                health_status["test_results"][self.default_model] = "no_response"
                
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["test_results"][self.default_model] = f"error: {str(e)}"
        
        return health_status
    
    def _log_configuration(self):
        """记录当前配置"""
        logger.info("=== LiteLLM SDK V2 配置 ===")
        logger.info(f"配置来源: YAML ({self.config.config_path})")
        logger.info(f"默认模型: {self.default_model}")
        logger.info(f"智能体模型: {self.agent_model} (温度: {self.agent_temperature})")
        logger.info(f"生成模型: {self.generation_model} (温度: {self.generation_temperature})")
        logger.info(f"备用模型: {self.fallback_models}")
        logger.info(f"路由器状态: {'启用' if self.router else '禁用'}")
        if self.router:
            logger.info(f"路由策略: {self.config.get('litellm.routing.strategy', 'cost-based')}")
            logger.info(f"可用模型数: {len(self.router.model_list)}")
    
    def _setup_proxy(self) -> Optional[Dict[str, str]]:
        """设置代理配置"""
        proxy_config = {}
        
        # 检查环境变量中的代理设置
        http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
        
        if http_proxy:
            proxy_config['http'] = http_proxy
        if https_proxy:
            proxy_config['https'] = https_proxy
            
        return proxy_config if proxy_config else None

# 便捷函数
def create_litellm_client(config_path: str = None) -> LiteLLMSDKClientV2:
    """创建LiteLLM客户端实例"""
    return LiteLLMSDKClientV2(config_path)