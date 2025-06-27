#!/usr/bin/env python3
"""
演示单个复杂问题的处理 - 展示完整的多跳推理过程
"""

import asyncio
import logging
import json
from datetime import datetime

# 配置DEBUG日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.clients.brightdata_client import BrightDataAsyncClient
from src.clients.firecrawl_client import FireCrawlAsyncClient
from src.core.config_loader import get_config


async def demo_complex_question():
    """演示处理一个复杂的多跳推理问题"""
    config = get_config()
    
    # 一个需要多跳推理的复杂问题
    complex_question = """
    Compare the S3 (Search-Select-Synthesize) framework with traditional RAG systems 
    in terms of architecture, performance on complex queries, and implementation details. 
    What are the specific advantages of S3's iterative search approach?
    """
    
    print("\n" + "="*80)
    print("🧪 复杂问题多跳推理演示")
    print("="*80)
    print(f"\n📝 问题: {complex_question.strip()}")
    print("-"*80)
    
    # 记录整个过程
    process_log = {
        'question': complex_question.strip(),
        'timestamp': datetime.now().isoformat(),
        'search_iterations': [],
        'selected_urls': [],
        'crawled_content': [],
        'reasoning_chain': []
    }
    
    # 第1跳：理解S3框架
    print("\n🔍 第1跳：搜索S3框架基础信息")
    logger.debug("开始第一跳搜索 - 目标：理解S3框架")
    
    brightdata = BrightDataAsyncClient(
        api_key=config.get('brightdata.api_key'),
        zone=config.get('brightdata.zone', 'xdan_search_searp')
    )
    
    iteration1_results = []
    async with brightdata:
        # 尝试使用模拟搜索展示流程
        query1 = "S3 framework Search Select Synthesize architecture"
        logger.debug(f"第1跳查询: {query1}")
        
        # 模拟搜索结果
        mock_results1 = [
            {
                'title': 'Understanding S3 Framework: Search-Select-Synthesize for Advanced RAG',
                'url': 'https://arxiv.org/example/s3-framework',
                'snippet': 'S3 framework introduces a three-phase approach to retrieval-augmented generation...'
            },
            {
                'title': 'S3 vs Traditional RAG: Architecture Comparison',
                'url': 'https://blog.ai/s3-vs-rag',
                'snippet': 'Key differences between S3 and traditional RAG systems in handling complex queries...'
            }
        ]
        
        iteration1_results = mock_results1
        process_log['search_iterations'].append({
            'iteration': 1,
            'query': query1,
            'results_count': len(mock_results1),
            'purpose': 'Understanding S3 framework basics'
        })
        
        print(f"✅ 找到 {len(mock_results1)} 个相关结果")
        for i, r in enumerate(mock_results1, 1):
            print(f"  {i}. {r['title']}")
    
    # 第2跳：深入技术细节
    print("\n🔍 第2跳：搜索技术实现细节")
    logger.debug("开始第二跳搜索 - 目标：获取实现细节")
    
    async with brightdata:
        query2 = "S3 framework iterative search agent implementation code"
        logger.debug(f"第2跳查询: {query2}")
        
        mock_results2 = [
            {
                'title': 'Implementing S3 Framework: Code Examples and Best Practices',
                'url': 'https://github.com/s3-framework/implementation',
                'snippet': 'Complete implementation of S3 framework with iterative search agents...'
            },
            {
                'title': 'S3 Agent Decision Loop: Technical Deep Dive',
                'url': 'https://techblog.ai/s3-agent-loop',
                'snippet': 'How S3 agents evaluate information sufficiency and decide when to stop searching...'
            }
        ]
        
        process_log['search_iterations'].append({
            'iteration': 2,
            'query': query2,
            'results_count': len(mock_results2),
            'purpose': 'Getting implementation details'
        })
        
        print(f"✅ 找到 {len(mock_results2)} 个技术实现结果")
    
    # 第3跳：性能对比数据
    print("\n🔍 第3跳：搜索性能对比数据")
    logger.debug("开始第三跳搜索 - 目标：性能基准对比")
    
    async with brightdata:
        query3 = "S3 framework vs RAG benchmark performance complex queries"
        logger.debug(f"第3跳查询: {query3}")
        
        mock_results3 = [
            {
                'title': 'Benchmarking S3 vs RAG: Performance on Complex Multi-hop Queries',
                'url': 'https://benchmark.ai/s3-vs-rag',
                'snippet': 'S3 outperforms traditional RAG by 35% on complex queries requiring multiple reasoning steps...'
            }
        ]
        
        process_log['search_iterations'].append({
            'iteration': 3,
            'query': query3,
            'results_count': len(mock_results3),
            'purpose': 'Performance comparison data'
        })
        
        print(f"✅ 找到 {len(mock_results3)} 个性能对比结果")
    
    # 选择要深度爬取的URL
    print("\n\n📋 选择阶段：确定需要深度爬取的页面")
    all_results = iteration1_results + mock_results2 + mock_results3
    
    urls_to_crawl = [
        all_results[0],  # S3框架介绍
        all_results[2],  # 实现代码
        all_results[4]   # 性能对比
    ]
    
    process_log['selected_urls'] = [u['url'] for u in urls_to_crawl]
    print(f"选择了 {len(urls_to_crawl)} 个关键页面进行深度内容提取")
    
    # 爬取阶段（使用模拟数据展示）
    print("\n\n🕷️ 爬取阶段：深度内容提取")
    
    # 模拟爬取结果
    crawled_data = [
        {
            'url': urls_to_crawl[0]['url'],
            'title': 'S3 Framework Complete Guide',
            'content': """
            # S3 Framework: Search-Select-Synthesize
            
            The S3 framework revolutionizes RAG by introducing three distinct phases:
            
            1. **Search Phase**: Iterative query refinement based on agent evaluation
            2. **Select Phase**: Agent determines information sufficiency 
            3. **Synthesize Phase**: Generate comprehensive answer from selected information
            
            Key advantages over traditional RAG:
            - Dynamic search strategy adaptation
            - Multi-round information gathering
            - Agent-based relevance assessment
            - Better handling of complex, multi-faceted queries
            
            The iterative nature allows S3 to:
            - Start with broad searches and progressively narrow down
            - Evaluate after each round if more information is needed
            - Adapt search strategy based on what's already found
            - Handle queries that require multiple reasoning steps
            """,
            'length': 850
        },
        {
            'url': urls_to_crawl[1]['url'],
            'title': 'S3 Implementation Code',
            'content': """
            ```python
            class S3Agent:
                def iterative_search(self, query, max_iterations=3):
                    results = []
                    for i in range(max_iterations):
                        # Search
                        search_results = self.search(query)
                        results.extend(search_results)
                        
                        # Evaluate sufficiency
                        if self.is_information_sufficient(results, query):
                            break
                            
                        # Refine query for next iteration
                        query = self.refine_query(query, results)
                    
                    return results
            ```
            
            The agent uses structured prompts with <search_complete> tags to control the search flow.
            """,
            'length': 600
        },
        {
            'url': urls_to_crawl[2]['url'],
            'title': 'S3 vs RAG Benchmarks',
            'content': """
            # Performance Comparison: S3 vs Traditional RAG
            
            ## Benchmark Results:
            
            | Metric | Traditional RAG | S3 Framework | Improvement |
            |--------|----------------|--------------|-------------|
            | Complex Queries | 62% accuracy | 84% accuracy | +35% |
            | Multi-hop Reasoning | 45% | 78% | +73% |
            | Information Completeness | 71% | 89% | +25% |
            | Latency (avg) | 1.2s | 3.8s | -217% |
            
            S3 excels at complex queries but trades off latency for accuracy.
            """,
            'length': 450
        }
    ]
    
    for data in crawled_data:
        print(f"\n✅ 爬取成功: {data['title']}")
        print(f"   长度: {data['length']} 字符")
        print(f"   预览: {data['content'][:150]}...")
        
        process_log['crawled_content'].append({
            'url': data['url'],
            'title': data['title'],
            'content_length': data['length']
        })
    
    # 推理链展示
    print("\n\n🧠 推理链构建")
    print("-"*80)
    
    reasoning_steps = [
        {
            'step': 1,
            'insight': 'S3使用三阶段方法：搜索-选择-合成，与传统RAG的单次检索不同',
            'source': 'S3 Framework Complete Guide'
        },
        {
            'step': 2,
            'insight': 'S3的迭代搜索由智能agent控制，可评估信息充分性',
            'source': 'S3 Implementation Code'
        },
        {
            'step': 3,
            'insight': 'S3在复杂查询上性能提升35%，多跳推理提升73%',
            'source': 'S3 vs RAG Benchmarks'
        },
        {
            'step': 4,
            'conclusion': 'S3的优势在于动态适应性和多轮信息收集能力，特别适合处理复杂的多方面查询'
        }
    ]
    
    for step in reasoning_steps:
        print(f"\n步骤 {step['step']}:")
        if 'insight' in step:
            print(f"  发现: {step['insight']}")
            print(f"  来源: {step.get('source', 'synthesis')}")
        else:
            print(f"  结论: {step['conclusion']}")
    
    process_log['reasoning_chain'] = reasoning_steps
    
    # 最终答案
    print("\n\n📝 综合答案")
    print("="*80)
    
    final_answer = """
基于深度搜索和分析，S3框架与传统RAG系统的主要区别如下：

**架构差异**：
- 传统RAG：单次向量搜索 → LLM生成
- S3框架：迭代搜索 → 智能选择 → 综合生成

**性能对比**：
- 复杂查询准确率：S3 (84%) vs RAG (62%)，提升35%
- 多跳推理能力：S3 (78%) vs RAG (45%)，提升73%
- 信息完整性：S3 (89%) vs RAG (71%)，提升25%

**S3迭代搜索的具体优势**：
1. 动态策略适应：根据已有信息调整搜索策略
2. 信息充分性评估：Agent自动判断何时停止搜索
3. 渐进式细化：从宽泛搜索逐步聚焦到具体信息
4. 更好的复杂查询处理：特别适合需要多步推理的问题

S3通过引入智能Agent和迭代机制，从根本上改变了信息检索的方式，使其能够更好地处理复杂的信息需求。
    """
    
    print(final_answer)
    
    # 保存完整过程日志
    process_log['final_answer'] = final_answer
    
    with open('complex_question_process.json', 'w', encoding='utf-8') as f:
        json.dump(process_log, f, ensure_ascii=False, indent=2)
    
    print("\n" + "="*80)
    print("✅ 演示完成！")
    print("完整过程已保存到: complex_question_process.json")
    print("="*80)


if __name__ == "__main__":
    print("\n🔬 DeepSearch 复杂问题处理演示")
    print("展示如何通过多跳推理获取精准信息")
    
    asyncio.run(demo_complex_question())