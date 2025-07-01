#!/usr/bin/env python3
"""
Patch for FlashSearchEngine to support search modes
修补FlashSearchEngine以支持搜索模式的动态配置
"""

import os
from typing import Dict, Any

def apply_search_mode_config(engine_instance: Any, config: Dict[str, Any]):
    """
    应用搜索模式配置到FlashSearchEngine实例
    
    Args:
        engine_instance: FlashSearchEngine实例
        config: 搜索模式配置
    """
    # 更新环境变量以影响搜索行为
    os.environ['SEARCH_RESULTS'] = str(config.get('search_results', 12))
    os.environ['SELECT_URLS'] = str(config.get('select_urls', 4))
    os.environ['CRAWL_TIMEOUT'] = str(config.get('crawl_timeout', 30))
    os.environ['BRIGHTDATA_TIMEOUT'] = str(config.get('brightdata_timeout', 60))
    os.environ['PARALLEL_CRAWL'] = str(config.get('parallel_crawl', 3))
    
    # 如果引擎有相关属性，直接更新
    if hasattr(engine_instance, 'search_results'):
        engine_instance.search_results = config.get('search_results', 12)
    
    if hasattr(engine_instance, 'select_urls'):
        engine_instance.select_urls = config.get('select_urls', 4)
        
    if hasattr(engine_instance, 'crawl_timeout'):
        engine_instance.crawl_timeout = config.get('crawl_timeout', 30)
        
    if hasattr(engine_instance, 'brightdata_timeout'):
        engine_instance.brightdata_timeout = config.get('brightdata_timeout', 60)
    
    # 更新BrightData客户端配置
    if hasattr(engine_instance, 'brightdata_client'):
        engine_instance.brightdata_client.timeout = config.get('brightdata_timeout', 60)
    
    # 更新LLM温度参数
    if hasattr(engine_instance, 'llm_client'):
        engine_instance.llm_client.temperature = config.get('llm_temperature', 0.7)