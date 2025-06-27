"""
Langfuse层级关系展示示例
演示S3-RAG-Chat和S3-DeepSearch两种模式在Langfuse中的展示效果
"""

import asyncio
import uuid
from typing import List, Dict, Any
from litellm import acompletion
from src.core.langfuse_trace_config import LangfuseTraceConfig, S3Mode

class S3ServiceWithLangfuse:
    """集成Langfuse层级追踪的S3服务"""
    
    def __init__(self):
        self.config = LangfuseTraceConfig()
        
    async def process_rag_chat(
        self, 
        question: str, 
        session_id: str,
        dataset_ids: List[str]
    ):
        """RAG对话模式 - 适合普通问答"""
        
        # 1. 创建Trace - 在Langfuse中显示为顶级节点
        trace_id = str(uuid.uuid4())
        trace_metadata = self.config.create_trace_metadata(
            mode=S3Mode.RAG_CHAT,
            session_id=session_id,
            question=question,
            dataset_ids=dataset_ids
        )
        
        # 2. 搜索阶段 - 显示为Trace的子节点
        search_results = []
        for i in range(1, 3):  # 2次迭代
            # 创建搜索Generation
            search_metadata = self.config.create_generation_metadata(
                trace_id=trace_id,
                mode=S3Mode.RAG_CHAT,
                phase="search",
                sub_phase="ragflow",
                iteration=i
            )
            
            # 模拟RAGFlow搜索（实际调用时会传递metadata）
            print(f"Langfuse会显示: {search_metadata['generation_name']}")
            search_results.extend(await self._mock_ragflow_search(question, search_metadata))
        
        # 3. 筛选阶段 - 智能体分析
        agent_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.RAG_CHAT,
            phase="select",
            sub_phase="agent_analysis"
        )
        
        # 调用LLM进行分析
        selected_docs = await self._call_agent(
            question=question,
            documents=search_results,
            metadata={**trace_metadata, **agent_metadata}
        )
        
        # 4. 合成阶段 - 生成答案
        generation_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.RAG_CHAT,
            phase="synthesize",
            sub_phase="generation"
        )
        
        answer = await self._generate_answer(
            question=question,
            documents=selected_docs,
            metadata={**trace_metadata, **generation_metadata}
        )
        
        return answer
    
    async def process_deepsearch(
        self, 
        question: str, 
        session_id: str,
        dataset_ids: List[str]
    ):
        """深度搜索模式 - 适合研究性问题"""
        
        # 1. 创建Trace
        trace_id = str(uuid.uuid4())
        trace_metadata = self.config.create_trace_metadata(
            mode=S3Mode.DEEPSEARCH,
            session_id=session_id,
            question=question,
            dataset_ids=dataset_ids,
            search_depth="comprehensive"
        )
        
        all_results = []
        
        # 2. 第一轮：知识库搜索
        kb_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.DEEPSEARCH,
            phase="search",
            sub_phase="ragflow",
            iteration=1
        )
        kb_results = await self._mock_ragflow_search(question, kb_metadata)
        all_results.extend(kb_results)
        
        # 3. 网络搜索（DeepSearch特有）
        web_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.DEEPSEARCH,
            phase="search",
            sub_phase="brightdata"
        )
        web_results = await self._mock_web_search(question, web_metadata)
        all_results.extend(web_results)
        
        # 4. 智能体分析是否需要更多信息
        agent_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.DEEPSEARCH,
            phase="select",
            sub_phase="agent_analysis"
        )
        
        need_more = await self._check_need_more_info(
            question=question,
            results=all_results,
            metadata={**trace_metadata, **agent_metadata}
        )
        
        # 5. 如果需要，进行网页爬取（DeepSearch特有）
        if need_more:
            crawl_metadata = self.config.create_generation_metadata(
                trace_id=trace_id,
                mode=S3Mode.DEEPSEARCH,
                phase="search",
                sub_phase="firecrawl"
            )
            crawl_results = await self._mock_web_crawl(web_results[0], crawl_metadata)
            all_results.extend(crawl_results)
        
        # 6. 去重处理
        dedup_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.DEEPSEARCH,
            phase="select",
            sub_phase="dedup"
        )
        unique_results = await self._deduplicate(all_results, dedup_metadata)
        
        # 7. 生成综合答案
        generation_metadata = self.config.create_generation_metadata(
            trace_id=trace_id,
            mode=S3Mode.DEEPSEARCH,
            phase="synthesize",
            sub_phase="generation"
        )
        
        answer = await self._generate_answer(
            question=question,
            documents=unique_results,
            metadata={**trace_metadata, **generation_metadata}
        )
        
        return answer
    
    async def _call_agent(self, question: str, documents: List[Dict], metadata: Dict[str, Any]):
        """调用智能体进行文档分析"""
        response = await acompletion(
            model="xdan-r2-qwen3",
            messages=[
                {"role": "system", "content": "分析文档是否足够回答问题..."},
                {"role": "user", "content": f"问题: {question}\n文档: {documents[:3]}"}
            ],
            metadata=metadata,
            temperature=0.1
        )
        # 返回筛选后的文档
        return documents[:3]
    
    async def _generate_answer(self, question: str, documents: List[Dict], metadata: Dict[str, Any]):
        """生成最终答案"""
        response = await acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "基于提供的文档回答问题..."},
                {"role": "user", "content": f"文档: {documents}\n问题: {question}"}
            ],
            metadata=metadata,
            temperature=0.7
        )
        return response.choices[0].message.content
    
    # 模拟方法
    async def _mock_ragflow_search(self, question: str, metadata: Dict[str, Any]):
        print(f"RAGFlow搜索: {question}")
        return [{"content": f"关于{question}的知识库内容", "score": 0.9}]
    
    async def _mock_web_search(self, question: str, metadata: Dict[str, Any]):
        print(f"BrightData搜索: {question}")
        return [{"url": "https://example.com", "snippet": f"网络上关于{question}的内容"}]
    
    async def _mock_web_crawl(self, url_data: Dict, metadata: Dict[str, Any]):
        print(f"FireCrawl爬取: {url_data['url']}")
        return [{"content": "爬取的详细内容", "source": url_data['url']}]
    
    async def _check_need_more_info(self, question: str, results: List[Dict], metadata: Dict[str, Any]):
        # 简单判断逻辑
        return len(results) < 5
    
    async def _deduplicate(self, results: List[Dict], metadata: Dict[str, Any]):
        # 简单去重
        return results[:5]


# 使用示例
async def main():
    service = S3ServiceWithLangfuse()
    
    # 示例1: RAG对话模式
    print("=== RAG对话模式 ===")
    answer1 = await service.process_rag_chat(
        question="什么是机器学习？",
        session_id="session-001",
        dataset_ids=["ml-basics"]
    )
    print(f"答案: {answer1}\n")
    
    # 示例2: 深度搜索模式
    print("=== 深度搜索模式 ===")
    answer2 = await service.process_deepsearch(
        question="2024年最新的AI发展趋势是什么？",
        session_id="session-002",
        dataset_ids=["ai-research", "tech-news"]
    )
    print(f"答案: {answer2}\n")
    
    print("""
    在Langfuse UI (http://localhost:3000) 中可以看到:
    
    1. Traces列表:
       - 💬 RAG对话: 什么是机器学习？
       - 🔬 深度搜索: 2024年最新的AI发展趋势是什么？
    
    2. 点击展开后的层级结构清晰可见
    
    3. 使用过滤器:
       - tags:s3-rag-chat - 查看所有RAG对话
       - tags:s3-deepsearch - 查看所有深度搜索
       - tags:phase:search - 查看所有搜索操作
    """)

if __name__ == "__main__":
    # 设置Langfuse环境变量
    import os
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-5a72cd8a-cacc-4716-84d7-eebdee989222"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-778e2663-1371-42f2-9479-e09b8b0767ae"
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
    
    # 启用Langfuse回调
    import litellm
    litellm.success_callback = ["langfuse"]
    
    asyncio.run(main())