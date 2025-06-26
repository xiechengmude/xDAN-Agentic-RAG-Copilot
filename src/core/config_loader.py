#!/usr/bin/env python3
"""
YAML配置加载器
支持环境变量替换和配置验证
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class ConfigLoader:
    """YAML配置加载器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录的config.yaml
        """
        if config_path is None:
            # 查找配置文件
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config.yaml"
            
            # 如果默认配置不存在，尝试其他位置
            if not config_path.exists():
                alt_paths = [
                    current_dir / "config" / "config.yaml",
                    current_dir / "conf" / "config.yaml",
                    Path.home() / ".ragflow" / "config.yaml"
                ]
                for alt_path in alt_paths:
                    if alt_path.exists():
                        config_path = alt_path
                        break
        
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self):
        """加载并解析YAML配置文件"""
        try:
            if not self.config_path.exists():
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._load_defaults()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
            
            # 处理环境变量替换
            self.config = self._substitute_env_vars(raw_config)
            
            logger.info(f"成功加载配置文件: {self.config_path}")
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self._load_defaults()
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """
        递归替换配置中的环境变量
        支持 ${VAR_NAME} 和 ${VAR_NAME:default_value} 格式
        """
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 匹配环境变量模式
            pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
            
            def replacer(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else None
                return os.getenv(var_name, default_value if default_value else match.group(0))
            
            return re.sub(pattern, replacer, config)
        else:
            return config
    
    def _load_defaults(self):
        """加载默认配置"""
        logger.info("使用默认配置")
        self.config = {
            "ragflow": {
                "api_url": os.getenv("RAGFLOW_API_URL", "http://localhost:7080"),
                "api_key": os.getenv("RAGFLOW_API_KEY", ""),
                "default_dataset_id": os.getenv("DEFAULT_DATASET_ID", "")
            },
            "models": {
                "default_model": "gpt-4o-mini",
                "s3_framework": {
                    "agent_model": "gpt-4o-mini",
                    "agent_temperature": 0.1,
                    "agent_max_tokens": 1000,
                    "generation_model": "gpt-4o-mini",
                    "generation_temperature": 0.7,
                    "generation_max_tokens": 2000
                },
                "fallback_models": ["gpt-3.5-turbo", "claude-3-haiku"]
            },
            "s3_framework": {
                "max_search_rounds": 3,
                "default_top_k": 10,
                "similarity_threshold": 0.1
            },
            "litellm": {
                "routing": {
                    "enabled": True,
                    "strategy": "cost-based",
                    "retry_count": 3
                }
            },
            "service": {
                "rag_service_port": 8001
            },
            "logging": {
                "level": "INFO",
                "verbose": False
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点号分隔的路径
        
        Args:
            key_path: 配置键路径，如 "models.default_model"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_ragflow_config(self) -> Dict[str, Any]:
        """获取RAGFlow配置"""
        return self.get("ragflow", {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.get("models", {})
    
    def get_s3_config(self) -> Dict[str, Any]:
        """获取S3框架配置"""
        return self.get("s3_framework", {})
    
    def get_litellm_config(self) -> Dict[str, Any]:
        """获取LiteLLM配置"""
        return self.get("litellm", {})
    
    def get_service_config(self) -> Dict[str, Any]:
        """获取服务配置"""
        return self.get("service", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.get("logging", {})
    
    def update(self, key_path: str, value: Any):
        """
        更新配置值
        
        Args:
            key_path: 配置键路径
            value: 新值
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self, path: str = None):
        """
        保存配置到文件
        
        Args:
            path: 保存路径，默认为原配置文件路径
        """
        save_path = path or self.config_path
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
            logger.info(f"配置已保存到: {save_path}")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def validate(self) -> bool:
        """
        验证配置完整性
        
        Returns:
            配置是否有效
        """
        required_keys = [
            "ragflow.api_url",
            "ragflow.api_key",
            "models.default_model",
            "service.rag_service_port"
        ]
        
        for key in required_keys:
            if not self.get(key):
                logger.error(f"缺少必需的配置项: {key}")
                return False
        
        return True
    
    def __repr__(self) -> str:
        return f"ConfigLoader(config_path={self.config_path})"

# 全局配置实例
_global_config: Optional[ConfigLoader] = None

def get_config(config_path: str = None) -> ConfigLoader:
    """
    获取全局配置实例（单例模式）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置加载器实例
    """
    global _global_config
    
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    
    return _global_config

def reset_config():
    """重置全局配置（用于测试）"""
    global _global_config
    _global_config = None

# 便捷函数
def get_ragflow_config() -> Dict[str, Any]:
    """获取RAGFlow配置"""
    return get_config().get_ragflow_config()

def get_model_config() -> Dict[str, Any]:
    """获取模型配置"""
    return get_config().get_model_config()

def get_s3_config() -> Dict[str, Any]:
    """获取S3框架配置"""
    return get_config().get_s3_config()

def get_litellm_config() -> Dict[str, Any]:
    """获取LiteLLM配置"""
    return get_config().get_litellm_config()

def get_service_config() -> Dict[str, Any]:
    """获取服务配置"""
    return get_config().get_service_config()