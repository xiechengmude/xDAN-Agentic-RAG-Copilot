"""
集成追踪的S3服务实现
展示如何用最简单的方式添加全链路追踪
"""

from typing import List, Dict, Any, Optional
import logging
from src.core.simple_trace import init_trace, get_trace, trace_phase
from src.clients.litellm_client import LiteLLMClient
from src.clients.ragflow_client import RagflowClient
from src.core.s3_framework import S3FrameworkAgent

logger = logging.getLogger(__name__)

class TracedS3Service:
    """带追踪功能的S3服务 - 保持简单"""
    
    def __init__(self, litellm_client: LiteLLMClient, ragflow_client: RagflowClient):
        self.litellm = litellm_client
        self.ragflow = ragflow_client
        self.s3_agent = S3FrameworkAgent(litellm_client, ragflow_client)
    
    async def chat_with_trace(
        self,
        question: str,
        session_id: str,
        dataset_ids: List[str],
        user_id: Optional[str] = None,
        stream: bool = False
    ):
        """带追踪的聊天接口"""
        
        # 初始化追踪
        trace_id = init_trace(
            session_id=session_id,
            question=question,
            dataset_ids=dataset_ids,
            user_id=user_id
        )
        
        try:
            # 执行S3流程
            if stream:
                async for chunk in self._process_stream():
                    yield chunk
            else:
                result = await self._process()
                yield result
                
        finally:
            # 完成追踪
            trace = get_trace()
            if trace:
                summary = trace.finalize()
                logger.info(f"Trace completed: {summary}")
    
    @trace_phase("search")
    async def _search_documents(self, question: str, dataset_ids: List[str]) -> List[Dict]:
        """搜索阶段 - 自动追踪"""
        results = []
        iteration = 0
        
        while iteration < 3:  # 最多3次迭代
            iteration += 1
            
            # RAGFlow搜索
            docs = await self.ragflow.search(
                question=question,
                dataset_ids=dataset_ids,
                top_k=10
            )
            
            results.extend(docs)
            
            # 记录迭代信息
            trace = get_trace()
            if trace:
                trace.metadata[f"search_iter_{iteration}"] = len(docs)
            
            # 检查是否需要继续
            if len(results) >= 5:  # 简单的判断逻辑
                break
        
        return results
    
    @trace_phase("select")
    async def _select_documents(self, question: str, documents: List[Dict]) -> List[Dict]:
        """选择阶段 - 自动追踪"""
        
        # 使用Agent判断
        trace = get_trace()
        metadata = trace.to_langfuse_metadata("select", "agent") if trace else {}
        
        response = await self.litellm.acompletion(
            model="xdan-r2-qwen3",
            messages=[
                {"role": "system", "content": "You are a document selector..."},
                {"role": "user", "content": f"Question: {question}\nDocuments: {documents[:5]}"}
            ],
            metadata=metadata,
            temperature=0.1
        )
        
        # 简单解析：选择前3个文档
        selected = documents[:3]
        
        # 记录选择结果
        if trace:
            trace.metadata["selected_count"] = len(selected)
        
        return selected
    
    @trace_phase("synthesize")
    async def _generate_answer(self, question: str, documents: List[Dict], stream: bool = False):
        """合成阶段 - 自动追踪"""
        
        # 构建上下文
        context = "\n\n".join([doc.get("content", "") for doc in documents])
        
        # 使用追踪元数据
        trace = get_trace()
        metadata = trace.to_langfuse_metadata("synthesize", "generation") if trace else {}
        
        # 生成答案
        response = await self.litellm.acompletion(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Answer based on the context..."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            metadata=metadata,
            temperature=0.7,
            stream=stream
        )
        
        if stream:
            async for chunk in response:
                yield chunk
        else:
            yield response.choices[0].message.content
    
    async def _process(self):
        """完整的S3处理流程"""
        trace = get_trace()
        question = trace.metadata["question"]
        dataset_ids = trace.metadata["dataset_ids"]
        
        # 三个阶段
        documents = await self._search_documents(question, dataset_ids)
        selected = await self._select_documents(question, documents)
        
        async for answer in self._generate_answer(question, selected, stream=False):
            return answer
    
    async def _process_stream(self):
        """流式S3处理流程"""
        trace = get_trace()
        question = trace.metadata["question"]
        dataset_ids = trace.metadata["dataset_ids"]
        
        # 搜索和选择
        documents = await self._search_documents(question, dataset_ids)
        selected = await self._select_documents(question, documents)
        
        # 流式生成
        async for chunk in self._generate_answer(question, selected, stream=True):
            yield chunk


# 使用示例
async def example_usage():
    """展示如何使用带追踪的S3服务"""
    
    # 初始化客户端
    import os
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-xxx"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-xxx"
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
    
    # 启用Langfuse
    import litellm
    litellm.success_callback = ["langfuse"]
    
    # 创建服务
    litellm_client = LiteLLMClient()
    ragflow_client = RagflowClient()
    s3_service = TracedS3Service(litellm_client, ragflow_client)
    
    # 执行查询
    async for result in s3_service.chat_with_trace(
        question="What is RAG?",
        session_id="test-session-123",
        dataset_ids=["knowledge-base"],
        stream=False
    ):
        print(f"Answer: {result}")
        
    # 查看追踪
    trace = get_trace()
    if trace:
        print(f"Trace ID: {trace.trace_id}")
        print(f"Total Duration: {trace.metadata['total_duration']:.2f}s")
        print(f"Phases: {trace.metadata['phases']}")