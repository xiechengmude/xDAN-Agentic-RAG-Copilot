#!/usr/bin/env python3
"""
FlashSearch Search Modes Configuration
搜索模式配置：fast, normal, deep
"""

from typing import Dict, Any
from enum import Enum

class SearchMode(Enum):
    """搜索模式枚举"""
    FAST = "fast"       # 快速模式：~15秒，单轮搜索
    NORMAL = "normal"   # 标准模式：~60秒，多轮迭代
    DEEP = "deep"       # 深度模式：~120秒，全面搜索

# 搜索模式配置
SEARCH_MODE_CONFIGS: Dict[SearchMode, Dict[str, Any]] = {
    SearchMode.FAST: {
        "name": "快速模式",
        "description": "适合快速获取答案，牺牲部分准确性",
        "max_iterations": 1,
        "time_budget": 15,
        "search_strategies": ["precision"],
        "search_results": 6,
        "select_urls": 2,
        "crawl_timeout": 10,
        "brightdata_timeout": 15,
        "parallel_crawl": 2,
        "skip_s3_evaluation": True,
        "enable_cache": True,
        "llm_temperature": 0.5,
        "max_tokens": 800
    },
    SearchMode.NORMAL: {
        "name": "标准模式",
        "description": "平衡速度和质量，适合大多数场景",
        "max_iterations": 3,
        "time_budget": 60,
        "search_strategies": ["precision", "broad", "recent"],
        "search_results": 12,
        "select_urls": 4,
        "crawl_timeout": 30,
        "brightdata_timeout": 60,
        "parallel_crawl": 3,
        "skip_s3_evaluation": False,
        "enable_cache": True,
        "llm_temperature": 0.7,
        "max_tokens": 2000
    },
    SearchMode.DEEP: {
        "name": "深度模式",
        "description": "全面深入搜索，适合研究和分析",
        "max_iterations": 5,
        "time_budget": 120,
        "search_strategies": ["precision", "broad", "recent", "academic", "news"],
        "search_results": 20,
        "select_urls": 6,
        "crawl_timeout": 45,
        "brightdata_timeout": 90,
        "parallel_crawl": 4,
        "skip_s3_evaluation": False,
        "enable_cache": True,
        "llm_temperature": 0.3,
        "max_tokens": 4000
    }
}

def get_search_config(mode: str = "fast") -> Dict[str, Any]:
    """
    获取搜索模式配置
    
    Args:
        mode: 搜索模式 (fast/normal/deep)
        
    Returns:
        搜索配置字典
    """
    try:
        search_mode = SearchMode(mode.lower())
    except ValueError:
        # 默认使用快速模式
        search_mode = SearchMode.FAST
    
    return SEARCH_MODE_CONFIGS[search_mode].copy()

def validate_mode(mode: str) -> bool:
    """验证搜索模式是否有效"""
    try:
        SearchMode(mode.lower())
        return True
    except ValueError:
        return False

def get_available_modes() -> Dict[str, Dict[str, str]]:
    """获取所有可用的搜索模式信息"""
    return {
        mode.value: {
            "name": config["name"],
            "description": config["description"],
            "time_budget": f"{config['time_budget']}s",
            "iterations": config["max_iterations"]
        }
        for mode, config in SEARCH_MODE_CONFIGS.items()
    }