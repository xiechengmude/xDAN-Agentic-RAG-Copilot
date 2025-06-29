#!/usr/bin/env python3
"""
快速检查v1.2的搜索策略是否生效
"""

import asyncio
import yaml
import logging
from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 专门捕获搜索查询
class SearchQueryCapture:
    def __init__(self):
        self.queries = []
        self.thinking = []
    
    def capture(self, record):
        msg = record.getMessage()
        if "搜索查询:" in msg or "search query:" in msg.lower():
            self.queries.append(msg)
        if "<thinking>" in msg:
            self.thinking.append(msg)

capture = SearchQueryCapture()
handler = logging.StreamHandler()
handler.addFilter(lambda r: capture.capture(r) or True)
logging.getLogger().addHandler(handler)

async def check_search_strategy():
    """检查搜索策略实际使用情况"""
    
    # 测试一个明确需要优化的查询
    test_query = "Meta Platforms Facebook 2024 Q3 quarterly earnings report investor relations official PDF"
    
    print(f"🔍 测试查询: {test_query}")
    print("="*60)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    litellm_client = EnhancedLiteLLMClient()
    
    try:
        # 创建v1.2版本的DeepSearch
        deepsearch = DeepSearchFramework(
            litellm_client, 
            config,
            prompt_version="v1.2",
            enable_time_aware=True
        )
        
        print("📋 开始搜索流程...")
        
        # 只运行第一轮搜索
        async for result in deepsearch.execute_deepsearch_workflow(
            question=test_query,
            max_rounds=1,
            stream=False
        ):
            if 'search_query' in result:
                actual_query = result['search_query']
                print(f"\n✅ 实际发送的搜索查询:")
                print(f"   {actual_query}")
                
                # 分析使用的技巧
                print(f"\n🔧 检测到的搜索优化技巧:")
                
                techniques = []
                if '"' in actual_query:
                    techniques.append("✓ 精确短语搜索 (引号)")
                if 'site:' in actual_query:
                    techniques.append("✓ 站点限定搜索 (site:)")
                if 'filetype:' in actual_query:
                    techniques.append("✓ 文件类型搜索 (filetype:)")
                if any(year in actual_query for year in ['2024', 'Q3', 'quarterly']):
                    techniques.append("✓ 时间感知 (2024/Q3)")
                if any(term in actual_query.lower() for term in ['investor', 'official', 'earnings']):
                    techniques.append("✓ 领域专业术语")
                
                if techniques:
                    for tech in techniques:
                        print(f"   {tech}")
                else:
                    print("   ❌ 未检测到明显的搜索优化技巧")
                
                # 对比原始查询
                print(f"\n📊 查询优化对比:")
                print(f"   原始: {test_query}")
                print(f"   优化: {actual_query}")
                
                # 计算优化程度
                if actual_query == test_query:
                    print("   ⚠️ 查询未被优化（与原始相同）")
                else:
                    print("   ✅ 查询已被优化")
            
            break
        
        # 检查捕获的日志
        if capture.queries:
            print(f"\n📝 捕获的搜索相关日志:")
            for q in capture.queries[:3]:
                print(f"   {q[:100]}...")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    finally:
        if 'deepsearch' in locals():
            await deepsearch._cleanup_clients()

if __name__ == "__main__":
    asyncio.run(check_search_strategy())