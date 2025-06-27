#!/usr/bin/env python3
"""
DeepSearch with Langfuse Integration Example
展示如何使用Langfuse追踪DeepSearch的各个阶段
"""

import asyncio
import os
from typing import Dict, Any

# 设置Langfuse凭据
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-78b5ed03-54ba-4a51-8d20-b1221f17046d"
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-7ea885b0-8c1b-4606-bb5d-c004ed367d1f"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"

import litellm
from litellm import acompletion

# 导入DeepSearch相关组件
from src.clients.langfuse_config import DeepSearchLangfuseTracker
from src.clients.brightdata_client import BrightDataClient
from src.clients.firecrawl_client import FireCrawlClient


class DeepSearchWithLangfuse:
    """集成Langfuse追踪的DeepSearch示例"""
    
    def __init__(self):
        # 初始化追踪器
        self.tracker = DeepSearchLangfuseTracker(
            session_id="deepsearch-demo-session",
            user_id="demo-user"
        )
        
        # 初始化客户端
        self.brightdata = BrightDataClient()
        self.firecrawl = FireCrawlClient()
        
        # 启用Langfuse
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
    
    async def search(self, query: str) -> Dict[str, Any]:
        """执行带追踪的深度搜索"""
        print(f"\n🔍 开始DeepSearch: {query}")
        print("=" * 60)
        
        # 1. 开始搜索追踪
        trace_metadata = self.tracker.start_search_trace(
            query=query,
            search_config={
                "max_depth": 3,
                "max_iterations": 5,
                "search_type": "deepsearch"
            }
        )
        
        # 2. 初始查询分析（使用Langfuse追踪）
        print("\n📊 Phase 1: 查询分析")
        analysis_response = await acompletion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个搜索查询分析专家。分析用户查询并提取关键搜索词。"
                },
                {
                    "role": "user",
                    "content": f"分析这个查询并提取3-5个关键搜索词：{query}"
                }
            ],
            metadata={
                **trace_metadata,
                "generation_name": "query-analysis",
                "trace_metadata": {
                    **trace_metadata.get("trace_metadata", {}),
                    "phase": "analysis",
                    "component": "query_analyzer"
                }
            }
        )
        
        keywords = analysis_response.choices[0].message.content
        print(f"提取的关键词: {keywords}")
        
        # 3. 网络搜索（模拟）
        print("\n🌐 Phase 2: 网络搜索")
        search_metadata = self.tracker.track_brightdata_search(
            query=query,
            iteration=1,
            results_count=10
        )
        
        # 模拟搜索结果
        search_results = [
            {"title": "Result 1", "url": "https://example.com/1", "snippet": "Sample result 1"},
            {"title": "Result 2", "url": "https://example.com/2", "snippet": "Sample result 2"}
        ]
        
        # 使用LLM选择相关结果
        selection_response = await acompletion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "选择最相关的搜索结果进行深入分析。"
                },
                {
                    "role": "user",
                    "content": f"查询: {query}\n\n搜索结果: {search_results}\n\n选择最相关的1-2个结果。"
                }
            ],
            metadata={
                **search_metadata,
                "generation_name": "result-selection",
            }
        )
        
        # 4. 内容提取（模拟）
        print("\n📄 Phase 3: 内容提取")
        for i, result in enumerate(search_results[:2]):
            extract_metadata = self.tracker.track_firecrawl_extraction(
                url=result["url"],
                iteration=i+1,
                content_length=1000
            )
            
            # 模拟内容提取
            print(f"提取内容从: {result['url']}")
        
        # 5. 综合分析
        print("\n🧠 Phase 4: 综合分析")
        synthesis_metadata = self.tracker.track_synthesis(
            sources_count=len(search_results),
            final=True
        )
        
        final_response = await acompletion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "基于搜索结果提供综合答案。"
                },
                {
                    "role": "user",
                    "content": f"查询: {query}\n\n基于以下信息提供综合答案：{search_results}"
                }
            ],
            metadata={
                **synthesis_metadata,
                "generation_name": "final-synthesis",
                "update_trace_keys": ["output"]  # 更新trace的输出
            }
        )
        
        answer = final_response.choices[0].message.content
        
        # 6. 评估结果
        print("\n✅ Phase 5: 结果评估")
        eval_metadata = self.tracker.track_evaluation(
            eval_type="relevance",
            score=0.85
        )
        
        # 模拟评估
        eval_response = await acompletion(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "评估答案的相关性和完整性，给出0-1的分数。"
                },
                {
                    "role": "user",
                    "content": f"查询: {query}\n\n答案: {answer}\n\n评分："
                }
            ],
            metadata=eval_metadata
        )
        
        print("\n" + "=" * 60)
        print(f"✅ DeepSearch完成！")
        print(f"📊 追踪ID: {self.tracker.trace_id}")
        print(f"🔗 查看详情: {os.environ['LANGFUSE_HOST']}")
        
        return {
            "query": query,
            "answer": answer,
            "trace_id": self.tracker.trace_id,
            "sources": search_results
        }


async def main():
    """运行示例"""
    print("🚀 DeepSearch with Langfuse Integration Demo")
    print("=" * 60)
    
    # 检查Langfuse配置
    if not os.getenv("LANGFUSE_PUBLIC_KEY"):
        print("⚠️  请先配置Langfuse密钥")
        return
    
    # 创建搜索引擎
    engine = DeepSearchWithLangfuse()
    
    # 测试查询
    test_queries = [
        "2024年诺贝尔物理学奖获得者是谁？他们的主要贡献是什么？",
        "解释一下机器学习中的注意力机制是如何工作的",
        "比较React和Vue框架的优缺点"
    ]
    
    for query in test_queries[:1]:  # 只运行第一个查询作为演示
        result = await engine.search(query)
        
        print(f"\n📝 最终答案:")
        print(result["answer"])
        
        print(f"\n📊 Langfuse追踪信息:")
        print(f"- Trace ID: {result['trace_id']}")
        print(f"- 查看详情: {os.environ['LANGFUSE_HOST']}/trace/{result['trace_id']}")
    
    print("\n✅ 演示完成！请在Langfuse UI中查看详细的追踪信息。")


if __name__ == "__main__":
    asyncio.run(main())