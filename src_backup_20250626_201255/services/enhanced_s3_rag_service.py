#!/usr/bin/env python3
"""
增强版S3 RAG服务
集成Agent和Session支持，保持S3框架的核心价值
"""

import os
import logging
import re
import json
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple, Union
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper, SDK_AVAILABLE
from src.clients.ragflow_client import RAGFlowClient  # 保留作为备选
from src.clients.streaming_ragflow_client import StreamingRAGFlowClient
from src.clients.litellm_sdk_client_v2 import LiteLLMSDKClientV2

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

# 导入配置加载器
try:
    from src.core.config_loader import get_config
    config = get_config()
    
    # 从YAML配置加载
    ragflow_config = config.get_ragflow_config()
    model_config = config.get_model_config()
    s3_config = model_config.get('s3_framework', {})
    openai_config = config.get('llm_providers.openai', {})
    
    RAGFLOW_API_URL = ragflow_config.get('api_url')
    RAGFLOW_API_KEY = ragflow_config.get('api_key')
    S3_SEARCH_MODEL_NAME = s3_config.get('agent_model', 'deepseek-chat')
    S3_SEARCH_MODEL_URL = openai_config.get('base_url', 'http://43.134.187.48:7220/v1')
    S3_SEARCH_API_KEY = openai_config.get('api_key')
    S3_GENERATOR_MODEL_NAME = s3_config.get('generation_model', 'deepseek-chat')
    S3_GENERATOR_MODEL_URL = openai_config.get('base_url', 'http://43.134.187.48:7220/v1')
    S3_GENERATOR_API_KEY = openai_config.get('api_key')
    DEFAULT_DATASET_ID = ragflow_config.get('default_dataset_id')
except:
    # 如果无法加载配置，使用config.settings
    from config.settings import (
        RAGFLOW_API_URL, RAGFLOW_API_KEY, 
        S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
        S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY,
        DEFAULT_DATASET_ID
    )

app = FastAPI(title="Enhanced S3 Agentic-RAG Service", version="2.0.0")

# S3框架的System Prompt（保持不变）
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
[initial search results]
</information>"""

# ==================== 请求/响应模型 ====================

class EnhancedS3RAGRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    agent_id: Optional[str] = None  # 新增：使用指定Agent
    session_id: Optional[str] = None  # 新增：使用现有Session
    use_sdk: Optional[bool] = True  # 新增：是否使用官方SDK
    max_search_rounds: Optional[int] = 3
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.1
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class EnhancedS3RAGResponse(BaseModel):
    question: str
    answer: str
    search_rounds: int
    selected_documents: List[Dict[str, Any]]
    search_process: List[Dict[str, Any]]
    final_context: str
    model_info: Dict[str, str]
    agent_info: Optional[Dict[str, Any]] = None  # 新增：Agent信息
    session_info: Optional[Dict[str, Any]] = None  # 新增：Session信息

class AgentRequest(BaseModel):
    name: str
    description: Optional[str] = None
    dataset_ids: Optional[List[str]] = None

class SessionRequest(BaseModel):
    agent_id: str
    user_id: Optional[str] = None

# ==================== 依赖注入 ====================

def get_ragflow_client():
    """获取RAGFlow客户端（SDK优先，HTTP客户端备选）"""
    if SDK_AVAILABLE:
        return RAGFlowSDKWrapper(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
    else:
        return RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)

def get_search_llm_client():
    """获取用于S3搜索决策的LLM客户端 - 使用LiteLLM"""
    return LiteLLMSDKClientV2()

def get_generator_llm_client():
    """获取用于答案生成的LLM客户端 - 使用LiteLLM"""
    return LiteLLMSDKClientV2()

class EnhancedS3RAGService:
    """
    增强版S3 RAG服务
    保持S3框架核心，集成Agent和Session功能
    支持独立的Search和Generator模型配置
    """
    
    def __init__(self, ragflow_client: Union[RAGFlowSDKWrapper, RAGFlowClient], 
                 search_llm_client: LiteLLMSDKClientV2 = None, 
                 generator_llm_client: LiteLLMSDKClientV2 = None):
        self.ragflow_client = ragflow_client
        
        # 如果没有提供，使用默认客户端
        self.search_llm_client = search_llm_client or get_search_llm_client()
        self.generator_llm_client = generator_llm_client or get_generator_llm_client()
        
        self.is_sdk_mode = isinstance(ragflow_client, RAGFlowSDKWrapper)
        
        logger.info(f"Enhanced S3 RAG Service 初始化 - SDK模式: {self.is_sdk_mode}")
        logger.info(f"Search Model: {S3_SEARCH_MODEL_NAME} (via LiteLLM)")
        logger.info(f"Generator Model: {S3_GENERATOR_MODEL_NAME} (via LiteLLM)")
    
    # ==================== S3框架核心方法（保持不变） ====================
    
    def format_search_results(self, chunks: List[Dict], doc_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """格式化搜索结果为S3框架所需的格式"""
        if not chunks:
            return "No relevant documents found.", {}
        
        formatted_results = []
        doc_mapping = {}
        
        for i, chunk in enumerate(chunks, doc_id_start):
            doc_info = {
                'content': chunk.get('content', ''),
                'document_id': chunk.get('document_id', ''),
                'dataset_id': chunk.get('dataset_id', ''),
                'similarity': chunk.get('similarity', 0.0)
            }
            doc_mapping[i] = doc_info
            
            formatted_results.append(f"Document {i}:")
            formatted_results.append(f"Content: {chunk.get('content', '')[:500]}...")
            formatted_results.append(f"Similarity: {chunk.get('similarity', 0.0)}")
            formatted_results.append("")
        
        return "\n".join(formatted_results), doc_mapping
    
    def extract_search_query(self, agent_response: str) -> Optional[str]:
        """从智能体响应中提取搜索查询"""
        query_match = re.search(r'<query>(.*?)</query>', agent_response, re.DOTALL)
        if query_match:
            try:
                query_json = json.loads(query_match.group(1).strip())
                return query_json.get('question', query_json.get('query', ''))
            except json.JSONDecodeError:
                return query_match.group(1).strip()
        return None
    
    def extract_important_docs(self, agent_response: str) -> List[int]:
        """从智能体响应中提取重要文档ID"""
        important_match = re.search(r'<important_info>\[(.*?)\]</important_info>', agent_response)
        if important_match:
            try:
                doc_ids = [int(x.strip()) for x in important_match.group(1).split(',') if x.strip()]
                return doc_ids
            except ValueError:
                return []
        return []
    
    def is_search_complete(self, agent_response: str) -> bool:
        """检查搜索是否完成"""
        complete_match = re.search(r'<search_complete>(.*?)</search_complete>', agent_response)
        if complete_match:
            return complete_match.group(1).strip().lower() == 'true'
        return False
    
    # ==================== 增强的搜索方法 ====================
    
    def search_step(self, question: str, dataset_ids: List[str], top_k: int = 5, 
                   similarity_threshold: float = 0.1) -> Tuple[List[Dict], bool]:
        """执行单次搜索步骤（支持SDK和HTTP客户端）"""
        try:
            logger.info(f"执行搜索步骤 - 问题: {question}, 数据集: {dataset_ids}, top_k: {top_k}")
            if self.is_sdk_mode:
                # 使用官方SDK
                response = self.ragflow_client.retrieve_chunks(
                    question=question,
                    dataset_ids=dataset_ids,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
                logger.info(f"SDK检索响应代码: {response.get('code')}")
                if response.get('code') == 0:
                    chunks = response.get('data', {}).get('chunks', [])
                    logger.info(f"SDK检索成功，找到 {len(chunks)} 个chunks")
                    return chunks, True
                else:
                    logger.error(f"SDK检索失败: {response.get('message')}")
                    return [], False
            else:
                # 使用HTTP客户端
                response = self.ragflow_client.retrieve_chunks(
                    question=question,
                    dataset_ids=dataset_ids,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
                if response.get('code') == 0:
                    return response.get('data', {}).get('chunks', []), True
                else:
                    logger.error(f"HTTP检索失败: {response.get('message')}")
                    return [], False
        except Exception as e:
            logger.error(f"搜索步骤失败: {e}")
            return [], False
    
    # ==================== Agent和Session集成 ====================
    
    def agent_s3_conversation(self, agent_id: str, question: str, session_id: str = None,
                             dataset_ids: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        基于Agent的S3对话流程
        """
        if not self.is_sdk_mode:
            raise ValueError("Agent功能需要SDK模式")
        
        try:
            # 如果没有提供session_id，创建新的session
            if not session_id:
                session_response = self.ragflow_client.create_session(agent_id)
                if session_response.get('code') != 0:
                    raise ValueError(f"创建Session失败: {session_response.get('message')}")
                session_id = session_response.get('data', {}).get('session_id')
            
            # 执行S3搜索流程
            search_result = self.s3_search_process(
                question=question,
                dataset_ids=dataset_ids or [DEFAULT_DATASET_ID],
                **kwargs
            )
            
            # 使用Agent进行最终答案生成
            final_context = search_result['final_context']
            agent_response = self.ragflow_client.session_ask(
                agent_id=agent_id,
                question=f"基于以下上下文回答问题：\n\n上下文：{final_context}\n\n问题：{question}",
                session_id=session_id,
                stream=False
            )
            
            if agent_response.get('code') == 0:
                answer = agent_response.get('data', {}).get('content', '')
            else:
                # 如果Agent失败，回退到LLM
                answer = self.synthesize_answer(question, search_result['selected_documents'])
            
            return {
                **search_result,
                'answer': answer,
                'agent_info': {'agent_id': agent_id},
                'session_info': {'session_id': session_id}
            }
            
        except Exception as e:
            logger.error(f"Agent S3对话失败: {e}")
            # 回退到标准S3流程
            return self.s3_search_process(question, dataset_ids or [DEFAULT_DATASET_ID], **kwargs)
    
    def s3_search_process(self, question: str, dataset_ids: List[str], max_rounds: int = 3,
                         top_k: int = 5, similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        S3框架的搜索和选择过程（保持原有逻辑）
        """
        search_process = []
        all_documents = {}
        selected_documents = []
        
        # 步骤1: 初始搜索
        initial_chunks, success = self.search_step(question, dataset_ids, top_k, similarity_threshold)
        if not success or not initial_chunks:
            logger.warning(f"初始搜索失败或无结果 - success: {success}, chunks: {len(initial_chunks) if initial_chunks else 0}")
            return {
                'question': question,
                'search_rounds': 0,
                'selected_documents': [],
                'search_process': [],
                'final_context': "未找到相关信息",
                'model_info': {
                    'search_model': S3_SEARCH_MODEL_NAME,
                    'generator_model': S3_GENERATOR_MODEL_NAME,
                    'mode': 'SDK' if self.is_sdk_mode else 'HTTP'
                }
            }
        
        initial_results, doc_mapping = self.format_search_results(initial_chunks, 1)
        all_documents.update(doc_mapping)
        
        search_process.append({
            'round': 1,
            'query': question,
            'results_count': len(initial_chunks),
            'action': 'initial_search'
        })
        
        initial_prompt = f"""<question>
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
                # 使用Search LLM进行决策 - 通过LiteLLM
                messages = [{"role": "user", "content": agent_input}]
                llm_response = asyncio.run(self.search_llm_client.chat_completion(
                    messages=messages,
                    model=S3_SEARCH_MODEL_NAME,  # 指定搜索模型
                    temperature=0.3,
                    max_tokens=1000,
                    use_case="agent"  # 使用agent用例配置
                ))
                
                # 提取实际的响应内容
                if isinstance(llm_response, dict):
                    agent_response = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                else:
                    agent_response = llm_response
                
                search_process.append({
                    'round': current_round,
                    'agent_response': agent_response,
                    'action': 'agent_decision'
                })
                
                # 提取重要文档
                important_doc_ids = self.extract_important_docs(agent_response)
                if important_doc_ids:
                    for doc_id in important_doc_ids:
                        if doc_id in all_documents and len(selected_documents) < 3:
                            selected_documents.append(all_documents[doc_id])
                
                # 检查是否需要继续搜索
                if self.is_search_complete(agent_response):
                    break
                
                # 提取新的搜索查询
                new_query = self.extract_search_query(agent_response)
                if not new_query:
                    break
                
                # 执行新的搜索
                new_chunks, success = self.search_step(new_query, dataset_ids, top_k, similarity_threshold)
                if success and new_chunks:
                    doc_id_start = max(all_documents.keys()) + 1 if all_documents else 1
                    new_results, new_doc_mapping = self.format_search_results(new_chunks, doc_id_start)
                    all_documents.update(new_doc_mapping)
                    
                    search_process.append({
                        'round': current_round,
                        'query': new_query,
                        'results_count': len(new_chunks),
                        'action': 'iterative_search'
                    })
                    
                    # 更新智能体输入
                    agent_input = f"{agent_input}\n\n<information>\n{new_results}\n</information>"
                
                current_round += 1
                
            except Exception as e:
                logger.error(f"第{current_round}轮搜索失败: {e}")
                break
        
        # 如果没有选中的文档，使用前3个
        if not selected_documents and all_documents:
            selected_documents = list(all_documents.values())[:3]
        
        # 构建最终上下文
        final_context = "\n\n".join([
            f"文档 {i+1}: {doc['content']}"
            for i, doc in enumerate(selected_documents)
        ])
        
        return {
            'question': question,
            'search_rounds': current_round,
            'selected_documents': selected_documents,
            'search_process': search_process,
            'final_context': final_context,
            'model_info': {
                'search_model': S3_SEARCH_MODEL_NAME,
                'generator_model': S3_GENERATOR_MODEL_NAME,
                'mode': 'SDK' if self.is_sdk_mode else 'HTTP'
            }
        }
    
    def synthesize_answer(self, question: str, selected_docs: List[Dict], 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """基于选中的文档合成答案"""
        if not selected_docs:
            return "抱歉，没有找到相关信息来回答您的问题。"
        
        context = "\n\n".join([
            f"参考资料 {i+1}:\n{doc['content']}"
            for i, doc in enumerate(selected_docs)
        ])
        
        prompt = f"""请基于以下参考资料回答用户的问题。请确保答案准确、完整，并在适当的地方引用参考资料。

参考资料：
{context}

用户问题：{question}

请提供详细的回答："""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = asyncio.run(self.generator_llm_client.chat_completion(
                messages=messages,
                model=S3_GENERATOR_MODEL_NAME,  # 指定生成模型
                temperature=temperature,
                max_tokens=max_tokens,
                use_case="generation"  # 使用generation用例配置
            ))
            # 提取实际的响应内容
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', '')
            return response
        except Exception as e:
            logger.error(f"合成答案失败: {e}")
            return f"生成答案时出现错误: {str(e)}"

# ==================== 依赖注入函数 ====================

def get_enhanced_s3_rag_service(
    ragflow_client = Depends(get_ragflow_client),
    search_llm_client: LiteLLMSDKClientV2 = Depends(get_search_llm_client),
    generator_llm_client: LiteLLMSDKClientV2 = Depends(get_generator_llm_client)
) -> EnhancedS3RAGService:
    return EnhancedS3RAGService(ragflow_client, search_llm_client, generator_llm_client)

# ==================== API端点 ====================

@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "sdk_available": SDK_AVAILABLE,
        "service": "Enhanced S3 Agentic-RAG Service"
    }

@app.post("/v1/enhanced-s3-rag/ask", response_model=EnhancedS3RAGResponse)
def enhanced_s3_rag_ask(
    request: EnhancedS3RAGRequest,
    s3_service: EnhancedS3RAGService = Depends(get_enhanced_s3_rag_service)
):
    """
    增强版S3框架的智能RAG问答端点
    支持Agent和Session功能
    """
    try:
        dataset_ids = request.dataset_ids or [DEFAULT_DATASET_ID]
        
        # 如果指定了Agent，使用Agent模式
        if request.agent_id and s3_service.is_sdk_mode:
            result = s3_service.agent_s3_conversation(
                agent_id=request.agent_id,
                question=request.question,
                session_id=request.session_id,
                dataset_ids=dataset_ids,
                max_rounds=request.max_search_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
        else:
            # 使用标准S3流程
            search_result = s3_service.s3_search_process(
                question=request.question,
                dataset_ids=dataset_ids,
                max_rounds=request.max_search_rounds,
                top_k=request.top_k,
                similarity_threshold=request.similarity_threshold
            )
            
            answer = s3_service.synthesize_answer(
                question=request.question,
                selected_docs=search_result['selected_documents'],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            result = {**search_result, 'answer': answer}
        
        return EnhancedS3RAGResponse(**result)
        
    except Exception as e:
        logger.error(f"Enhanced S3 RAG处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Agent管理端点 ====================

@app.get("/v1/agents")
def list_agents(s3_service: EnhancedS3RAGService = Depends(get_enhanced_s3_rag_service)):
    """列出所有Agent"""
    if not s3_service.is_sdk_mode:
        raise HTTPException(status_code=501, detail="Agent功能需要SDK模式")
    
    try:
        agents = s3_service.ragflow_client.list_agents()
        return {"code": 0, "data": agents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/agents")
def create_agent(
    request: AgentRequest,
    s3_service: EnhancedS3RAGService = Depends(get_enhanced_s3_rag_service)
):
    """创建新的Agent"""
    if not s3_service.is_sdk_mode:
        raise HTTPException(status_code=501, detail="Agent功能需要SDK模式")
    
    try:
        result = s3_service.ragflow_client.create_agent(
            name=request.name,
            description=request.description
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Session管理端点 ====================

@app.post("/v1/agents/{agent_id}/sessions")
def create_session(
    agent_id: str,
    request: SessionRequest,
    s3_service: EnhancedS3RAGService = Depends(get_enhanced_s3_rag_service)
):
    """为指定Agent创建Session"""
    if not s3_service.is_sdk_mode:
        raise HTTPException(status_code=501, detail="Session功能需要SDK模式")
    
    try:
        result = s3_service.ragflow_client.create_session(agent_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/datasets")
def list_datasets(s3_service: EnhancedS3RAGService = Depends(get_enhanced_s3_rag_service)):
    """列出可用的数据集"""
    try:
        return s3_service.ragflow_client.list_datasets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
