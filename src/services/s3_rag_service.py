#!/usr/bin/env python3
"""
基于S3框架的Agentic-RAG服务
整合Search-Select-Synthesize工作流
"""

import os
import logging
import re
import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio

from src.clients.ragflow_client import RAGFlowClient
from src.clients.llm_client import LLMClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")
LLM_API_URL = os.getenv("LLM_API_URL", "http://51.159.189.105:7032/v1")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

app = FastAPI(title="S3 Agentic-RAG Service", version="1.0.0")

# S3框架的System Prompt（基于训练代码）
S3_SYSTEM_PROMPT = """You are a search copilot for the generation model. Based on a user's query and initial searched results, you will first determine if the searched results are enough to produce an answer.

If the searched results are enough, you will use <search_complete>True</search_complete> to indicate that you have gathered enough information for the generation model to produce an answer.

If the searched results are not enough, you will go through a loop of <query> -> <information> -> <important_info> -> <search_complete> -> <query> (if not complete) ..., to help the generation model to generate a better answer with more relevant information searched.

You should show the search query between <query> and </query> in JSON format.
Based on the search query, we will return the top searched results between <information> and </information>. You need to put the doc ids of the important documents (up to 3 documents, within the current information window) between <important_info> and </important_info> (e.g., <important_info>[1, 4]</important_info>).

A search query MUST be followed by a <search_complete> tag if the search is not complete.
After reviewing the information, you must decide whether to continue searching with a new query or indicate that the search is complete. If you need more information, use <search_complete>False</search_complete> to indicate you want to continue searching with a better query. Otherwise, use <search_complete>True</search_complete> to terminate the search.

During the process, you can add reasoning process within <think></think> tag whenever you want. Note: Only the important information would be used for the generation model to produce an answer.

For a question and initial searched results:
<question>
[user's question]
</question>
<information>
[initial searched results]
</information>

If the initial searched results are enough to produce an answer, you should output:
<search_complete>
True
</search_complete>

If the initial searched results are not enough to produce an answer, you should output:
<query>
{
    "query": "[search query]"
} 
</query>
<information>
[top searched results based on the above search query]
</information>
<important_info>
[doc ids]
</important_info>
<search_complete>
False
</search_complete>
<query>
{
    "query": "[search query]"
}
</query>
...... (can be several turns until <search_complete> is True)

<search_complete>
True
</search_complete>

Now, start the loop with the following question and initial searched results:"""

# 请求模型
class S3RAGRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    max_search_rounds: Optional[int] = 3
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.1
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class S3RAGResponse(BaseModel):
    question: str
    answer: str
    search_rounds: int
    selected_documents: List[Dict[str, Any]]
    search_process: List[Dict[str, Any]]
    final_context: str
    model_info: Dict[str, str]

# 依赖注入
def get_ragflow_client() -> RAGFlowClient:
    return RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)

def get_llm_client() -> LLMClient:
    return LLMClient(base_url=LLM_API_URL, model_name=LLM_MODEL_NAME)

class S3RAGService:
    def __init__(self, ragflow_client: RAGFlowClient, llm_client: LLMClient):
        self.ragflow_client = ragflow_client
        self.llm_client = llm_client
    
    def format_search_results(self, chunks: List[Dict], doc_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """格式化搜索结果为S3框架所需的格式"""
        if not chunks:
            return "No relevant documents found.", {}
        
        formatted_results = []
        doc_mapping = {}
        
        for i, chunk in enumerate(chunks, doc_id_start):
            doc_info = {
                'chunk_id': chunk.get('id', ''),
                'document_id': chunk.get('document_id', ''),
                'document_name': chunk.get('document_name', ''),
                'content': chunk.get('content_with_weight', ''),
                'similarity': chunk.get('similarity', 0)
            }
            doc_mapping[i] = doc_info
            
            formatted_results.append(f"[{i}] Document: {doc_info['document_name']}")
            formatted_results.append(f"Content: {doc_info['content'][:500]}...")
            formatted_results.append(f"Similarity: {doc_info['similarity']:.3f}")
            formatted_results.append("")
        
        return "\n".join(formatted_results), doc_mapping
    
    def extract_search_query(self, agent_response: str) -> Optional[str]:
        """从智能体响应中提取搜索查询"""
        query_pattern = r'<query>\s*\{\s*"query":\s*"([^"]+)"\s*\}\s*</query>'
        match = re.search(query_pattern, agent_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None
    
    def extract_important_docs(self, agent_response: str) -> List[int]:
        """从智能体响应中提取重要文档ID"""
        important_pattern = r'<important_info>\s*\[([^\]]+)\]\s*</important_info>'
        match = re.search(important_pattern, agent_response)
        if match:
            try:
                doc_ids_str = match.group(1)
                doc_ids = [int(x.strip()) for x in doc_ids_str.split(',')]
                return doc_ids
            except:
                return []
        return []
    
    def is_search_complete(self, agent_response: str) -> bool:
        """检查搜索是否完成"""
        complete_pattern = r'<search_complete>\s*(True|true)\s*</search_complete>'
        return bool(re.search(complete_pattern, agent_response))
    
    def search_step(self, question: str, dataset_ids: List[str], top_k: int = 5, 
                   similarity_threshold: float = 0.1) -> Tuple[str, List[Dict], Dict[int, Dict]]:
        """执行单次搜索步骤"""
        try:
            response = self.ragflow_client.retrieve_chunks(
                question=question,
                dataset_ids=dataset_ids,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                highlight=True
            )
            
            chunks = response.get('data', {}).get('chunks', [])
            formatted_results, doc_mapping = self.format_search_results(chunks)
            
            return formatted_results, chunks, doc_mapping
            
        except Exception as e:
            logger.error(f"搜索步骤出错: {e}")
            return "Search failed due to an error.", [], {}
    
    def s3_search_process(self, question: str, dataset_ids: List[str], max_rounds: int = 3,
                         top_k: int = 5, similarity_threshold: float = 0.1) -> Tuple[List[Dict], List[Dict], str]:
        """执行S3框架的搜索和选择过程"""
        search_process = []
        all_doc_mapping = {}
        current_doc_id = 1
        
        # 步骤1: 初始搜索
        logger.info(f"开始S3搜索过程，问题: {question}")
        initial_results, initial_chunks, initial_mapping = self.search_step(
            question, dataset_ids, top_k, similarity_threshold
        )
        
        # 更新文档映射
        for doc_id, doc_info in initial_mapping.items():
            all_doc_mapping[current_doc_id] = doc_info
            current_doc_id += 1
        
        search_process.append({
            'round': 1,
            'query': question,
            'results_count': len(initial_chunks),
            'type': 'initial_search'
        })
        
        # 构建初始提示
        initial_prompt = f"""
<question>
{question}
</question>
<information>
{initial_results}
</information>"""
        
        # 步骤2: 智能体决策和迭代搜索
        current_round = 1
        agent_input = S3_SYSTEM_PROMPT + initial_prompt
        
        while current_round <= max_rounds:
            try:
                # 调用智能体进行决策
                messages = [{"role": "user", "content": agent_input}]
                agent_response = self.llm_client.chat_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )
                
                agent_content = agent_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.info(f"第{current_round}轮智能体响应: {agent_content[:200]}...")
                
                # 检查是否搜索完成
                if self.is_search_complete(agent_content):
                    logger.info("智能体判断搜索完成")
                    # 提取重要文档
                    important_doc_ids = self.extract_important_docs(agent_content)
                    selected_docs = [all_doc_mapping.get(doc_id) for doc_id in important_doc_ids if doc_id in all_doc_mapping]
                    selected_docs = [doc for doc in selected_docs if doc is not None]
                    
                    search_process.append({
                        'round': current_round,
                        'decision': 'search_complete',
                        'selected_docs': important_doc_ids,
                        'agent_response': agent_content
                    })
                    
                    return selected_docs, search_process, agent_content
                
                # 提取新的搜索查询
                new_query = self.extract_search_query(agent_content)
                if not new_query:
                    logger.warning("无法提取搜索查询，结束搜索")
                    break
                
                logger.info(f"提取到新搜索查询: {new_query}")
                
                # 执行新搜索
                new_results, new_chunks, new_mapping = self.search_step(
                    new_query, dataset_ids, top_k, similarity_threshold
                )
                
                # 更新文档映射
                for doc_info in new_mapping.values():
                    all_doc_mapping[current_doc_id] = doc_info
                    current_doc_id += 1
                
                search_process.append({
                    'round': current_round + 1,
                    'query': new_query,
                    'results_count': len(new_chunks),
                    'type': 'iterative_search'
                })
                
                # 更新智能体输入，添加新的搜索结果
                agent_input += f"""
<query>
{{
    "query": "{new_query}"
}}
</query>
<information>
{new_results}
</information>"""
                
                current_round += 1
                
            except Exception as e:
                logger.error(f"第{current_round}轮搜索出错: {e}")
                break
        
        # 如果达到最大轮数仍未完成，返回所有文档
        logger.warning(f"达到最大搜索轮数({max_rounds})，返回所有文档")
        all_docs = list(all_doc_mapping.values())
        return all_docs[:3], search_process, "搜索达到最大轮数限制"
    
    def synthesize_answer(self, question: str, selected_docs: List[Dict], 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """基于选中的文档合成答案"""
        if not selected_docs:
            return "抱歉，没有找到相关信息来回答您的问题。"
        
        # 构建上下文
        context_parts = []
        for i, doc in enumerate(selected_docs, 1):
            context_parts.append(f"文档{i}: {doc.get('document_name', '未知')}")
            context_parts.append(f"内容: {doc.get('content', '')}")
            context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # 生成答案
        prompt = f"""基于以下上下文信息，准确回答用户的问题。请确保答案基于提供的信息，如果信息不足请说明。

上下文信息：
{context}

用户问题：{question}

请基于上述上下文信息回答问题："""

        try:
            messages = [
                {"role": "system", "content": "你是一个专业的知识问答助手，能够基于提供的上下文信息准确回答用户问题。"},
                {"role": "user", "content": prompt}
            ]
            
            response = self.llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.get('choices', [{}])[0].get('message', {}).get('content', '抱歉，无法生成答案。')
            
        except Exception as e:
            logger.error(f"合成答案时出错: {e}")
            return f"生成答案时出现错误: {str(e)}"

def get_s3_rag_service(
    ragflow_client: RAGFlowClient = Depends(get_ragflow_client),
    llm_client: LLMClient = Depends(get_llm_client)
) -> S3RAGService:
    return S3RAGService(ragflow_client, llm_client)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "S3 Agentic-RAG Service", "framework": "Search-Select-Synthesize"}

@app.post("/v1/s3-rag/ask", response_model=S3RAGResponse)
async def s3_rag_ask(request: S3RAGRequest, s3_service: S3RAGService = Depends(get_s3_rag_service)):
    """S3框架的智能RAG问答端点"""
    try:
        # 使用默认数据集ID如果未指定
        dataset_ids = request.dataset_ids or [DEFAULT_DATASET_ID]
        
        logger.info(f"开始S3-RAG处理，问题: {request.question}")
        
        # 步骤1&2: Search & Select - 执行S3搜索和选择过程
        selected_docs, search_process, agent_final_response = s3_service.s3_search_process(
            question=request.question,
            dataset_ids=dataset_ids,
            max_rounds=request.max_search_rounds,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        # 构建最终上下文
        final_context = "\n\n".join([
            f"文档: {doc.get('document_name', '未知')}\n内容: {doc.get('content', '')}"
            for doc in selected_docs
        ])
        
        # 步骤3: Synthesize - 基于选中文档生成答案
        logger.info("开始答案合成...")
        answer = s3_service.synthesize_answer(
            question=request.question,
            selected_docs=selected_docs,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return S3RAGResponse(
            question=request.question,
            answer=answer,
            search_rounds=len(search_process),
            selected_documents=selected_docs,
            search_process=search_process,
            final_context=final_context,
            model_info={
                "framework": "S3 (Search-Select-Synthesize)",
                "retrieval": "RAGFlow",
                "generation": LLM_MODEL_NAME,
                "agent_model": LLM_MODEL_NAME
            }
        )
        
    except Exception as e:
        logger.error(f"S3-RAG处理出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理S3-RAG请求时出错: {str(e)}")

@app.get("/v1/s3-rag/datasets")
async def list_datasets(ragflow_client: RAGFlowClient = Depends(get_ragflow_client)):
    """列出可用的数据集"""
    try:
        response = ragflow_client.list_datasets()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
