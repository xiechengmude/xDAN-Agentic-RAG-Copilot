#!/usr/bin/env python3
"""
快速验证v1.2多轮搜索功能
"""

import json
import logging
import sys
import os
from datetime import datetime
import asyncio
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 简化日志输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)
# 禁用一些噪音日志
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('LiteLLM').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

async def quick_test():
    """快速测试多轮搜索"""
    
    # Load configuration
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Initialize
    litellm_client = EnhancedLiteLLMClient()
    deepsearch = DeepSearchFramework(litellm_client, config, prompt_version="v1.2")
    
    # 使用一个需要多轮搜索的复杂问题
    question = "比较苹果公司2024年Q4和2025年Q1的财报，分析营收、利润和各产品线的增长趋势"
    
    print(f"\n{'='*80}")
    print(f"问题: {question}")
    print(f"{'='*80}\n")
    
    round_info = []
    start_time = datetime.now()
    
    try:
        async for result in deepsearch.execute_deepsearch_workflow(
            question=question,
            max_rounds=3,
            stream=False
        ):
            if result.get("rounds"):
                for round_data in result["rounds"]:
                    round_num = round_data.get("round", 0)
                    query = round_data.get("search_query", "")
                    decision = round_data.get("decision", {})
                    
                    info = {
                        "round": round_num,
                        "query": query,
                        "search_complete": decision.get("search_complete", False),
                        "next_query": decision.get("next_query"),
                        "urls_selected": len(round_data.get("selected_urls", []))
                    }
                    
                    if round_num > len(round_info):
                        round_info.append(info)
                        print(f"第{round_num}轮搜索:")
                        print(f"  查询: {query}")
                        print(f"  选择URL数: {info['urls_selected']}")
                        print(f"  搜索完成: {info['search_complete']}")
                        if info['next_query']:
                            print(f"  下一轮查询: {info['next_query']}")
                        print()
    
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*80}")
        print(f"测试结果:")
        print(f"  总耗时: {duration:.1f}秒")
        print(f"  搜索轮数: {len(round_info)}")
        
        if len(round_info) > 1:
            print(f"\n✅ 成功！v1.2版本支持多轮搜索")
            print(f"\n各轮查询对比:")
            for i, info in enumerate(round_info):
                print(f"  第{i+1}轮: {info['query'][:50]}...")
        else:
            print(f"\n❌ 只进行了1轮搜索")
        
        print(f"{'='*80}")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await deepsearch._cleanup_clients()

if __name__ == "__main__":
    asyncio.run(quick_test())