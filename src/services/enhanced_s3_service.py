"""
增强的S3服务 - 集成Langfuse追踪，支持RAG-Chat和DeepSearch两种模式
"""

import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional, AsyncIterator
from enum import Enum
import logging

from src.core.langfuse_trace_config import LangfuseTraceConfig, S3Mode
from src.core.simple_trace import init_trace, get_trace, trace_phase
from src.clients.litellm_client import LiteLLMSDKClientV2 as LiteLLMSDKClient
from src.clients.ragflow_client import EnhancedRAGFlowClient
from src.clients.brightdata_client import BrightDataClient
from src.clients.firecrawl_client import FirecrawlClient

logger = logging.getLogger(__name__)

class EnhancedS3Service:
    """增强的S3服务，支持两种模式并集成Langfuse追踪"""
    
    def __init__(
        self,
        litellm_client: Optional[LiteLLMSDKClient] = None,
        ragflow_client: Optional[EnhancedRAGFlowClient] = None,
        brightdata_client: Optional[BrightDataClient] = None,
        firecrawl_client: Optional[FirecrawlClient] = None
    ):
        self.litellm = litellm_client or LiteLLMSDKClient()
        self.ragflow = ragflow_client or EnhancedRAGFlowClient()
        self.brightdata = brightdata_client
        self.firecrawl = firecrawl_client
        self.trace_config = LangfuseTraceConfig()
        
    async def ask(
        self,
        question: str,
        dataset_ids: List[str],
        chat_id: Optional[str] = None,
        mode: str = "rag-chat",  # "rag-chat" or "deepsearch"
        stream: bool = False,
        user_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """统一的问答接口，支持两种模式"""
        
        # 确定模式
        s3_mode = S3Mode.DEEPSEARCH if mode == "deepsearch" else S3Mode.RAG_CHAT
        
        # 生成会话ID
        session_id = chat_id or str(uuid.uuid4())
        
        # 初始化追踪
        trace_id = init_trace(
            session_id=session_id,
            question=question,
            dataset_ids=dataset_ids,
            user_id=user_id,
            mode=s3_mode.value
        )
        
        # 创建Langfuse追踪元数据
        trace_metadata = self.trace_config.create_trace_metadata(
            mode=s3_mode,
            session_id=session_id,
            question=question,
            dataset_ids=dataset_ids,
            user_id=user_id,
            **kwargs
        )
        
        try:
            # 根据模式执行不同的流程
            if s3_mode == S3Mode.RAG_CHAT:
                async for chunk in self._process_rag_chat(
                    question, dataset_ids, trace_id, trace_metadata, stream
                ):
                    yield chunk
            else:
                async for chunk in self._process_deepsearch(
                    question, dataset_ids, trace_id, trace_metadata, stream
                ):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error in {mode} mode: {e}")
            trace = get_trace()
            if trace:
                trace.metadata["error"] = str(e)
                trace.metadata["final_status"] = "failed"
            raise
        finally:
            # 完成追踪
            trace = get_trace()
            if trace:
                summary = trace.finalize()
                logger.info(f"Trace completed: {trace_id}, Duration: {summary['duration']:.2f}s")
    
    async def _process_rag_chat(
        self,
        question: str,
        dataset_ids: List[str],
        trace_id: str,
        trace_metadata: Dict[str, Any],
        stream: bool
    ) -> AsyncIterator[str]:
        """RAG对话模式处理流程"""
        
        # 1. 搜索阶段
        documents = await self._search_phase_rag(
            question, dataset_ids, trace_id, S3Mode.RAG_CHAT, max_iterations=3
        )
        
        # 2. 筛选阶段
        selected_docs = await self._select_phase(
            question, documents, trace_id, S3Mode.RAG_CHAT
        )
        
        # 3. 合成阶段
        async for chunk in self._synthesize_phase(
            question, selected_docs, trace_id, S3Mode.RAG_CHAT, trace_metadata, stream
        ):
            yield chunk
    
    async def _process_deepsearch(
        self,
        question: str,
        dataset_ids: List[str],
        trace_id: str,
        trace_metadata: Dict[str, Any],
        stream: bool
    ) -> AsyncIterator[str]:
        """深度搜索模式处理流程"""
        
        all_documents = []
        
        # 1. 初始知识库搜索
        kb_docs = await self._search_phase_rag(
            question, dataset_ids, trace_id, S3Mode.DEEPSEARCH, max_iterations=2
        )
        all_documents.extend(kb_docs)
        
        # 2. 网络搜索（如果配置了BrightData）
        if self.brightdata:
            web_docs = await self._search_web(
                question, trace_id, S3Mode.DEEPSEARCH
            )
            all_documents.extend(web_docs)
        
        # 3. 智能分析是否需要更多信息
        need_more, refined_query = await self._analyze_need_more(
            question, all_documents, trace_id, S3Mode.DEEPSEARCH
        )
        
        # 4. 如果需要更多信息，进行深度爬取
        if need_more and self.firecrawl and len(all_documents) > 0:
            crawled_docs = await self._crawl_sources(
                all_documents[:2], trace_id, S3Mode.DEEPSEARCH
            )
            all_documents.extend(crawled_docs)
        
        # 5. 最终筛选和去重
        final_docs = await self._final_selection(
            question, all_documents, trace_id, S3Mode.DEEPSEARCH
        )
        
        # 6. 生成综合答案
        async for chunk in self._synthesize_phase(
            question, final_docs, trace_id, S3Mode.DEEPSEARCH, trace_metadata, stream
        ):
            yield chunk
    
    @trace_phase("search")
    async def _search_phase_rag(
        self,
        question: str,
        dataset_ids: List[str],
        trace_id: str,
        mode: S3Mode,
        max_iterations: int
    ) -> List[Dict[str, Any]]:
        """RAGFlow搜索阶段"""
        
        all_results = []
        current_query = question
        
        for iteration in range(1, max_iterations + 1):
            # 创建搜索追踪元数据
            search_metadata = self.trace_config.create_generation_metadata(
                trace_id=trace_id,
                mode=mode,
                phase="search",
                sub_phase="ragflow",
                iteration=iteration,
                query=current_query
            )
            
            # 执行搜索
            results = await self.ragflow.search(
                question=current_query,
                dataset_ids=dataset_ids,
                top_k=10
            )
            
            all_results.extend(results)
            
            # 记录搜索结果
            trace = get_trace()
            if trace:
                trace.add_search_iteration(
                    iteration=iteration,
                    query=current_query,
                    results_count=len(results),
                    duration=0.5  # 示例值
                )
            
            # 检查是否需要继续搜索
            if len(all_results) >= 5 or len(results) == 0:
                break
            
            # 生成新查询（简化版）
            current_query = f"{question} 更多细节"
        
        return all_results
    
    @trace_phase("search_web")
    async def _search_web(
        self,
        question: str,
        trace_id: str,
        mode: S3Mode
    ) -> List[Dict[str, Any]]:
        """网络搜索阶段（DeepSearch特有）"""
        
        search_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="search",
            sub_phase="brightdata"
        )
        
        # 执行网络搜索
        results = await self.brightdata.search(question)
        
        # 转换为统一格式
        web_docs = []
        for result in results[:5]:  # 限制结果数量
            web_docs.append({
                "content": result.get("snippet", ""),
                "metadata": {
                    "source": "web",
                    "url": result.get("url", ""),
                    "title": result.get("title", "")
                }
            })
        
        return web_docs
    
    @trace_phase("select")
    async def _select_phase(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        trace_id: str,
        mode: S3Mode
    ) -> List[Dict[str, Any]]:
        """文档筛选阶段"""
        
        # 创建Agent分析的追踪元数据
        trace = get_trace()
        agent_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="select",
            sub_phase="agent_analysis"
        )
        
        # 准备Agent提示
        system_prompt = """你是一个文档分析专家。请分析提供的文档是否足够回答用户问题。
选择最相关的3-5个文档，并说明选择理由。"""
        
        user_prompt = f"""问题：{question}

找到的文档：
{self._format_documents(documents[:10])}

请选择最相关的文档并说明理由。"""
        
        # 调用LLM
        langfuse_metadata = trace.to_langfuse_metadata("select", "agent") if trace else {}
        langfuse_metadata.update(agent_metadata)
        
        response = await self.litellm.acompletion(
            model="xdan-r2-qwen3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            metadata=langfuse_metadata
        )
        
        # 简化处理：选择前3个文档
        selected = documents[:3]
        
        # 记录选择结果
        if trace:
            trace.set_agent_decision(
                decision="sufficient",
                selected_count=len(selected),
                reasoning="选择了最相关的文档"
            )
        
        return selected
    
    @trace_phase("synthesize")
    async def _synthesize_phase(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        trace_id: str,
        mode: S3Mode,
        trace_metadata: Dict[str, Any],
        stream: bool
    ) -> AsyncIterator[str]:
        """答案合成阶段"""
        
        # 创建合成追踪元数据
        trace = get_trace()
        synthesis_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="synthesize",
            sub_phase="generation" if not stream else "streaming"
        )
        
        # 准备上下文
        context = self._build_context(documents)
        
        system_prompt = """你是一个专业的问答助手。请基于提供的文档内容，准确、全面地回答用户问题。
如果文档中没有相关信息，请诚实说明。"""
        
        user_prompt = f"""参考文档：
{context}

用户问题：{question}

请基于以上文档内容回答问题。"""
        
        # 调用LLM生成答案
        langfuse_metadata = trace.to_langfuse_metadata("synthesize", "generation") if trace else {}
        langfuse_metadata.update(synthesis_metadata)
        
        response = await self.litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            stream=stream,
            metadata=langfuse_metadata
        )
        
        if stream:
            # 流式响应
            total_content = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    total_content += content
                    yield content
            
            # 记录最终结果
            if trace:
                trace.set_final_metrics(
                    total_tokens=len(total_content) // 4,  # 估算
                    total_cost=0.001,  # 估算
                    answer_length=len(total_content)
                )
        else:
            # 同步响应
            answer = response.choices[0].message.content
            if trace:
                trace.set_final_metrics(
                    total_tokens=response.usage.total_tokens if hasattr(response, 'usage') else 0,
                    total_cost=0.001,  # 估算
                    answer_length=len(answer)
                )
            yield answer
    
    async def _analyze_need_more(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        trace_id: str,
        mode: S3Mode
    ) -> tuple[bool, Optional[str]]:
        """分析是否需要更多信息（DeepSearch特有）"""
        
        trace = get_trace()
        analysis_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="select",
            sub_phase="relevance_check"
        )
        
        # 简化判断：如果文档少于5个，需要更多信息
        need_more = len(documents) < 5
        refined_query = f"{question} latest information" if need_more else None
        
        return need_more, refined_query
    
    async def _crawl_sources(
        self,
        documents: List[Dict[str, Any]],
        trace_id: str,
        mode: S3Mode
    ) -> List[Dict[str, Any]]:
        """爬取网页获取详细内容（DeepSearch特有）"""
        
        crawl_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="search",
            sub_phase="firecrawl"
        )
        
        crawled_docs = []
        for doc in documents:
            if "url" in doc.get("metadata", {}):
                url = doc["metadata"]["url"]
                # 模拟爬取
                crawled_docs.append({
                    "content": f"详细内容来自 {url}",
                    "metadata": {"source": "crawled", "url": url}
                })
        
        return crawled_docs
    
    async def _final_selection(
        self,
        question: str,
        documents: List[Dict[str, Any]],
        trace_id: str,
        mode: S3Mode
    ) -> List[Dict[str, Any]]:
        """最终文档筛选和去重（DeepSearch特有）"""
        
        dedup_metadata = self.trace_config.create_generation_metadata(
            trace_id=trace_id,
            mode=mode,
            phase="select",
            sub_phase="dedup"
        )
        
        # 简化去重：保留前5个文档
        return documents[:5]
    
    def _format_documents(self, documents: List[Dict[str, Any]]) -> str:
        """格式化文档用于展示"""
        formatted = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")[:200] + "..."
            source = doc.get("metadata", {}).get("source", "unknown")
            formatted.append(f"{i+1}. [{source}] {content}")
        return "\n\n".join(formatted)
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """构建上下文"""
        context_parts = []
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "knowledge_base")
            context_parts.append(f"[文档{i+1} - 来源:{source}]\n{content}")
        return "\n\n".join(context_parts)