#!/usr/bin/env python3
"""
S3框架RAG服务演示版本
使用模拟数据展示S3工作流程
"""

import os
import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
import asyncio

from src.clients.llm_client import LLMClient

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 环境变量配置
LLM_API_URL = os.getenv("LLM_API_URL", "http://51.159.189.105:7032/v1")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")

app = FastAPI(title="S3 Agentic-RAG Demo Service", version="1.0.0")

# S3框架的System Prompt
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

Now, start the loop with the following question and initial searched results:"""

# 模拟知识库数据
MOCK_KNOWLEDGE_BASE = {
    "人工智能": [
        {
            "id": 1,
            "document_name": "AI基础知识.md",
            "content": "人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。AI包括机器学习、深度学习、自然语言处理、计算机视觉等多个子领域。",
            "similarity": 0.95
        },
        {
            "id": 2,
            "document_name": "AI发展历史.md",
            "content": "人工智能的发展可以追溯到1950年代，艾伦·图灵提出了著名的图灵测试。1956年，达特茅斯会议标志着人工智能作为一个学科的诞生。经历了多次起伏，现在AI正处于第三次发展高潮。",
            "similarity": 0.88
        }
    ],
    "机器学习": [
        {
            "id": 3,
            "document_name": "机器学习概述.md",
            "content": "机器学习是人工智能的一个子集，它使计算机能够在没有明确编程的情况下学习。主要包括监督学习、无监督学习和强化学习三大类。常见算法有线性回归、决策树、神经网络等。",
            "similarity": 0.92
        },
        {
            "id": 4,
            "document_name": "深度学习基础.md",
            "content": "深度学习是机器学习的一个分支，基于人工神经网络。它通过多层神经网络来学习数据的表示，在图像识别、语音识别、自然语言处理等领域取得了突破性进展。",
            "similarity": 0.90
        }
    ],
    "RAG": [
        {
            "id": 5,
            "document_name": "RAG技术介绍.md",
            "content": "检索增强生成（Retrieval-Augmented Generation，RAG）是一种结合信息检索和文本生成的技术。它首先从知识库中检索相关信息，然后基于检索到的信息生成答案，能够提供更准确、更新的信息。",
            "similarity": 0.94
        },
        {
            "id": 6,
            "document_name": "S3框架.md",
            "content": "S3框架（Search-Select-Synthesize）是一种先进的RAG方法，包含三个阶段：搜索（Search）阶段进行信息检索，选择（Select）阶段筛选重要信息，合成（Synthesize）阶段生成最终答案。这种方法能够提高答案的质量和相关性。",
            "similarity": 0.96
        }
    ]
}

# 请求模型
class DemoS3RAGRequest(BaseModel):
    question: str
    max_search_rounds: Optional[int] = 3
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class DemoS3RAGResponse(BaseModel):
    question: str
    answer: str
    search_rounds: int
    selected_documents: List[Dict[str, Any]]
    search_process: List[Dict[str, Any]]
    final_context: str
    model_info: Dict[str, str]

def get_llm_client() -> LLMClient:
    return LLMClient(base_url=LLM_API_URL, model_name=LLM_MODEL_NAME)

class DemoS3RAGService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def mock_search(self, query: str) -> List[Dict]:
        """模拟搜索功能"""
        results = []
        query_lower = query.lower()
        
        # 简单的关键词匹配
        for keyword, docs in MOCK_KNOWLEDGE_BASE.items():
            if keyword.lower() in query_lower or any(word in query_lower for word in keyword.split()):
                results.extend(docs)
        
        # 如果没有直接匹配，尝试模糊匹配
        if not results:
            for keyword, docs in MOCK_KNOWLEDGE_BASE.items():
                for doc in docs:
                    if any(word in doc['content'].lower() for word in query_lower.split()):
                        results.append(doc)
        
        # 按相似度排序并返回前5个
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:5]
    
    def format_search_results(self, docs: List[Dict], doc_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """格式化搜索结果"""
        if not docs:
            return "No relevant documents found.", {}
        
        formatted_results = []
        doc_mapping = {}
        
        for i, doc in enumerate(docs, doc_id_start):
            doc_mapping[i] = doc
            formatted_results.append(f"[{i}] Document: {doc['document_name']}")
            formatted_results.append(f"Content: {doc['content']}")
            formatted_results.append(f"Similarity: {doc['similarity']:.3f}")
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
    
    def s3_search_process(self, question: str, max_rounds: int = 3) -> Tuple[List[Dict], List[Dict], str]:
        """执行S3框架的搜索和选择过程"""
        search_process = []
        all_doc_mapping = {}
        current_doc_id = 1
        
        # 步骤1: 初始搜索
        logger.info(f"开始S3搜索过程，问题: {question}")
        initial_docs = self.mock_search(question)
        initial_results, initial_mapping = self.format_search_results(initial_docs, current_doc_id)
        
        # 更新文档映射
        all_doc_mapping.update(initial_mapping)
        current_doc_id += len(initial_mapping)
        
        search_process.append({
            'round': 1,
            'query': question,
            'results_count': len(initial_docs),
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
                new_docs = self.mock_search(new_query)
                new_results, new_mapping = self.format_search_results(new_docs, current_doc_id)
                
                # 更新文档映射
                all_doc_mapping.update(new_mapping)
                current_doc_id += len(new_mapping)
                
                search_process.append({
                    'round': current_round + 1,
                    'query': new_query,
                    'results_count': len(new_docs),
                    'type': 'iterative_search'
                })
                
                # 更新智能体输入
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
        logger.warning(f"达到最大搜索轮数({max_rounds})，返回前3个文档")
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

def get_demo_s3_rag_service(llm_client: LLMClient = Depends(get_llm_client)) -> DemoS3RAGService:
    return DemoS3RAGService(llm_client)

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy", 
        "service": "S3 Agentic-RAG Demo Service", 
        "framework": "Search-Select-Synthesize",
        "data_source": "Mock Knowledge Base"
    }

@app.post("/v1/demo-s3-rag/ask", response_model=DemoS3RAGResponse)
async def demo_s3_rag_ask(request: DemoS3RAGRequest, s3_service: DemoS3RAGService = Depends(get_demo_s3_rag_service)):
    """S3框架的演示RAG问答端点"""
    try:
        logger.info(f"开始Demo S3-RAG处理，问题: {request.question}")
        
        # 执行S3搜索和选择过程
        selected_docs, search_process, agent_final_response = s3_service.s3_search_process(
            question=request.question,
            max_rounds=request.max_search_rounds
        )
        
        # 构建最终上下文
        final_context = "\n\n".join([
            f"文档: {doc.get('document_name', '未知')}\n内容: {doc.get('content', '')}"
            for doc in selected_docs
        ])
        
        # 基于选中文档生成答案
        logger.info("开始答案合成...")
        answer = s3_service.synthesize_answer(
            question=request.question,
            selected_docs=selected_docs,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return DemoS3RAGResponse(
            question=request.question,
            answer=answer,
            search_rounds=len(search_process),
            selected_documents=selected_docs,
            search_process=search_process,
            final_context=final_context,
            model_info={
                "framework": "S3 (Search-Select-Synthesize)",
                "retrieval": "Mock Knowledge Base",
                "generation": LLM_MODEL_NAME,
                "agent_model": LLM_MODEL_NAME
            }
        )
        
    except Exception as e:
        logger.error(f"Demo S3-RAG处理出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理Demo S3-RAG请求时出错: {str(e)}")

@app.get("/v1/demo-s3-rag/knowledge-base")
async def get_knowledge_base():
    """获取模拟知识库信息"""
    return {
        "knowledge_base": MOCK_KNOWLEDGE_BASE,
        "total_documents": sum(len(docs) for docs in MOCK_KNOWLEDGE_BASE.values()),
        "categories": list(MOCK_KNOWLEDGE_BASE.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
