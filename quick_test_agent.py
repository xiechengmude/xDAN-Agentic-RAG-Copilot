#!/usr/bin/env python3
"""
快速测试Agent策略功能
"""

import json
import logging
import sys
import os
import asyncio
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 简化日志
logging.basicConfig(level=logging.INFO, format='%(message)s')
for logger in ['httpx', 'openai', 'LiteLLM', 'urllib3', 'firecrawl']:
    logging.getLogger(logger).setLevel(logging.ERROR)

async def quick_test():
    # Load config
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize
    litellm_client = EnhancedLiteLLMClient()
    deepsearch = DeepSearchFramework(litellm_client, config, prompt_version="v1.2")
    
    question = "特斯拉最新财报的关键数据"
    
    print(f"\n测试Agent策略规划")
    print(f"问题: {question}\n")
    
    # 只测试策略规划
    strategy = await deepsearch.plan_search_strategy(question)
    
    print(f"✅ 策略制定成功！\n")
    print(f"分析: {strategy.get('analysis', '')[:200]}...")
    print(f"\n初始查询: {strategy.get('initial_query', '')}")
    print(f"预计轮数: {strategy.get('estimated_rounds', '')}")
    
    await deepsearch._cleanup_clients()

if __name__ == "__main__":
    asyncio.run(quick_test())