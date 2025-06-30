#!/usr/bin/env python3
"""
搜索配置加载器
负责加载和管理search_config.yaml中的配置
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class SearchConfigLoader:
    """搜索配置加载器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置加载器"""
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载搜索配置文件"""
        # 配置文件搜索路径
        search_paths = [
            Path.cwd() / "search_config.yaml",
            Path.cwd() / "config" / "search_config.yaml",
            Path.cwd() / "conf" / "search_config.yaml",
            Path.home() / ".ragflow" / "search_config.yaml",
        ]
        
        # 查找配置文件
        config_path = None
        for path in search_paths:
            if path.exists():
                config_path = path
                logger.info(f"找到搜索配置文件: {config_path}")
                break
        
        if not config_path:
            logger.warning("未找到search_config.yaml，使用默认配置")
            return self._get_default_config()
        
        try:
            # 加载YAML配置
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 展开环境变量
            config = self._expand_env_vars(config)
            
            # 合并默认配置
            default_config = self._get_default_config()
            config = self._merge_configs(default_config, config)
            
            logger.info("搜索配置加载成功")
            return config
            
        except Exception as e:
            logger.error(f"加载搜索配置失败: {e}")
            return self._get_default_config()
    
    def _expand_env_vars(self, config: Any) -> Any:
        """递归展开配置中的环境变量"""
        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            # 匹配 ${VAR:default} 模式
            pattern = r'\$\{([^}:]+):([^}]*)\}'
            
            def replace_match(match):
                var_name = match.group(1)
                default_value = match.group(2)
                return os.getenv(var_name, default_value)
            
            return re.sub(pattern, replace_match, config)
        else:
            return config
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """递归合并配置"""
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "search": {
                "max_rounds": 5,
                "min_rounds": 1,
                "results_per_round": 10,
                "max_total_results": 50,
                "max_crawl_urls_per_round": 3,
                "max_total_crawl_urls": 10,
                "search_timeout": 30,
                "crawl_timeout": 20,
                "total_timeout": 300
            },
            "concurrent_search": {
                "default_strategy": "single",
                "max_concurrent_searches": 5,
                "max_concurrent_crawls": 3,
                "strategies": {
                    "single": {"enabled": False},
                    "smart": {
                        "enabled": True,
                        "max_parallel": 2,
                        "subquery_method": "expand"
                    },
                    "flash": {
                        "enabled": True,
                        "max_parallel": 3,
                        "subquery_method": "decompose"
                    }
                }
            },
            "content_quality": {
                "min_content_length": 500,
                "max_content_length": 20000,
                "relevance_threshold": 0.7,
                "quality_score_threshold": 0.6,
                "dedup_enabled": True,
                "dedup_similarity_threshold": 0.9
            },
            "search_modes": {
                "flash": {
                    "name": "Flash模式",
                    "max_rounds": 2,
                    "concurrent_strategy": "flash"
                },
                "standard": {
                    "name": "标准模式",
                    "max_rounds": 5,
                    "concurrent_strategy": "smart"
                },
                "deep": {
                    "name": "深度模式",
                    "max_rounds": 10,
                    "concurrent_strategy": "single"
                }
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，如 "search.max_rounds" 或 "concurrent_search.strategies.flash"
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_search_mode_config(self, mode: str) -> Dict[str, Any]:
        """获取特定搜索模式的配置"""
        mode_config = self.get(f"search_modes.{mode}", {})
        
        # 如果模式不存在，返回标准模式配置
        if not mode_config:
            logger.warning(f"搜索模式 '{mode}' 不存在，使用标准模式")
            mode_config = self.get("search_modes.standard", {})
        
        # 应用并发策略配置
        strategy = mode_config.get("concurrent_strategy", "single")
        strategy_config = self.get(f"concurrent_search.strategies.{strategy}", {})
        mode_config["concurrent_config"] = strategy_config
        
        return mode_config
    
    def get_concurrent_strategy_config(self, strategy: str) -> Dict[str, Any]:
        """获取并发策略配置"""
        return self.get(f"concurrent_search.strategies.{strategy}", {})
    
    def reload(self):
        """重新加载配置"""
        logger.info("重新加载搜索配置...")
        self._config = self._load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()


# 全局配置实例
search_config = SearchConfigLoader()