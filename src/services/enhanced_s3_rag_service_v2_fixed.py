"""
增强版S3 RAG服务 - 带详细搜索过程记录
集成了S3框架、Agent功能和Session管理
支持独立的Search和Generator模型配置
"""

import os
import re
import json
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
import logging

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.clients.ragflow_client import RAGFlowClient
from src.clients.llm_client import LLMClient
try:
    from src.clients.xdan_rag_client import XDANRagClient
except ImportError:
    XDANRagClient = None
from config.settings import (
    RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID,
    S3_SEARCH_MODEL_NAME, S3_SEARCH_MODEL_URL, S3_SEARCH_API_KEY,
    S3_GENERATOR_MODEL_NAME, S3_GENERATOR_MODEL_URL, S3_GENERATOR_API_KEY
)

logger = logging.getLogger(__name__)

# S3框架的系统提示
S3_SYSTEM_PROMPT = """You are an expert search agent. Your job is to find the most relevant information to answer the user's question.

For each search iteration:
1. Analyze the retrieved documents
2. Decide if you have enough information to answer the question
3. If not, formulate a new search query

IMPORTANT: Your response must use these XML tags:
- <think>Your reasoning about the search results</think>
- <search_complete>true/false</search_complete>
- If search is not complete: <query>{"question": "your new search query"}</query>
- If search is complete: <important_info>[doc_id1, doc_id2, doc_id3]</important_info> (select up to 3 most relevant document IDs)

Example response for continuing search:
<think>The current documents mention X but don't explain Y which is crucial for answering the question.</think>
<search_complete>false</search_complete>
<query>{"question": "search query for Y"}</query>

Example response for completing search:
<think>Documents 1 and 3 contain all the necessary information about the topic.</think>
<search_complete>true</search_complete>
<important_info>[1, 3]</important_info>
"""

def get_ragflow_client(use_sdk: bool = True):
    """获取RAGFlow客户端（SDK或HTTP）"""
    if use_sdk:
        return RAGFlowSDKWrapper(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
    else:
        return RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)

def get_search_llm_client():
    """获取用于S3搜索决策的LLM客户端"""
    return LLMClient(
        base_url=S3_SEARCH_MODEL_URL, 
        api_key=S3_SEARCH_API_KEY,
        model_name=S3_SEARCH_MODEL_NAME
    )

def get_generator_llm_client():
    """获取用于答案生成的LLM客户端"""
    return LLMClient(
        base_url=S3_GENERATOR_MODEL_URL, 
        api_key=S3_GENERATOR_API_KEY,
        model_name=S3_GENERATOR_MODEL_NAME
    )

class EnhancedS3RAGServiceV2:
    """
    增强版S3 RAG服务 - 带详细搜索过程记录
    """
    
    def __init__(self, ragflow_client, 
                 search_llm_client: LLMClient = None, 
                 generator_llm_client: LLMClient = None):
        self.ragflow_client = ragflow_client
        
        # 如果没有提供，使用默认客户端
        self.search_llm_client = search_llm_client or get_search_llm_client()
        self.generator_llm_client = generator_llm_client or get_generator_llm_client()
        
        # 检测客户端类型
        self.is_sdk_mode = isinstance(ragflow_client, RAGFlowSDKWrapper)
        self.is_xdan_client = XDANRagClient and isinstance(ragflow_client, XDANRagClient)
        
        client_type = "xDAN Client" if self.is_xdan_client else ("SDK模式" if self.is_sdk_mode else "HTTP模式")
        logger.info(f"Enhanced S3 RAG Service V2 初始化 - 客户端类型: {client_type}")
        logger.info(f"Search Model: {S3_SEARCH_MODEL_NAME}")
        logger.info(f"Generator Model: {S3_GENERATOR_MODEL_NAME}")
    
    def format_search_results(self, chunks: List[Dict], doc_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """格式化搜索结果为S3框架所需的格式"""
        if not chunks:
            return "No relevant documents found.", {}
        
        formatted_results = []
        doc_mapping = {}
        
        for i, chunk in enumerate(chunks, doc_id_start):
            doc_info = {
                'id': i,
                'content': chunk.get('content', ''),
                'document_id': chunk.get('document_id', ''),
                'dataset_id': chunk.get('dataset_id', ''),
                'similarity': chunk.get('similarity', 0.0),
                'chunk_id': chunk.get('id', '')
            }
            doc_mapping[i] = doc_info
            
            formatted_results.append(f"Document {i}:")
            formatted_results.append(f"Content: {chunk.get('content', '')[:500]}...")
            formatted_results.append(f"Similarity: {chunk.get('similarity', 0.0)}")
            formatted_results.append("")
        
        return "\n".join(formatted_results), doc_mapping
    
    def extract_search_decision(self, agent_response: str) -> Dict[str, Any]:
        """从智能体响应中提取搜索决策的所有信息"""
        decision = {
            'thinking': '',
            'search_complete': False,
            'new_query': None,
            'important_docs': [],
            'raw_response': agent_response
        }
        
        # 提取思考过程
        think_match = re.search(r'<think>(.*?)</think>', agent_response, re.DOTALL)
        if think_match:
            decision['thinking'] = think_match.group(1).strip()
        
        # 提取搜索完成状态
        complete_match = re.search(r'<search_complete>(.*?)</search_complete>', agent_response)
        if complete_match:
            decision['search_complete'] = complete_match.group(1).strip().lower() == 'true'
        
        # 提取新查询
        query_match = re.search(r'<query>(.*?)</query>', agent_response, re.DOTALL)
        if query_match:
            try:
                query_json = json.loads(query_match.group(1).strip())
                decision['new_query'] = query_json.get('question', query_json.get('query', ''))
            except json.JSONDecodeError:
                decision['new_query'] = query_match.group(1).strip()
        
        # 提取重要文档
        important_match = re.search(r'<important_info>\[(.*?)\]</important_info>', agent_response)
        if important_match:
            try:
                doc_ids = [int(x.strip()) for x in important_match.group(1).split(',') if x.strip()]
                decision['important_docs'] = doc_ids
            except ValueError:
                pass
        
        return decision
    
    def search_step(self, question: str, dataset_ids: List[str], top_k: int = 5, 
                   similarity_threshold: float = 0.1) -> Tuple[List[Dict], bool]:
        """执行单次搜索步骤"""
        try:
            logger.info(f"执行搜索步骤 - 问题: {question}, 数据集: {dataset_ids}, top_k: {top_k}")
            
            # 使用兼容方法调用
            if self.is_xdan_client and hasattr(self.ragflow_client, 'retrieve_chunks_compatible'):
                response = self.ragflow_client.retrieve_chunks_compatible(
                    question=question,
                    dataset_ids=dataset_ids,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
            else:
                response = self.ragflow_client.retrieve_chunks(
                    question=question,
                    dataset_ids=dataset_ids,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
            
            logger.info(f"检索响应代码: {response.get('code')}")
            if response.get('code') == 0:
                chunks = response.get('data', {}).get('chunks', [])
                logger.info(f"检索成功，找到 {len(chunks)} 个chunks")
                return chunks, True
            else:
                logger.error(f"检索失败: {response.get('message')}")
                return [], False
        except Exception as e:
            logger.error(f"搜索步骤失败: {e}")
            return [], False
    
    def s3_search_process_with_history(self, question: str, dataset_ids: List[str], 
                                      max_rounds: int = 3, top_k: int = 5, 
                                      similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        带详细历史记录的S3搜索过程
        """
        search_history = []
        all_documents = {}
        selected_documents = []
        total_documents_retrieved = 0
        
        start_time = time.time()
        
        # 步骤1: 初始搜索
        round_start = time.time()
        initial_chunks, success = self.search_step(question, dataset_ids, top_k, similarity_threshold)
        
        if not success or not initial_chunks:
            logger.warning(f"初始搜索失败或无结果")
            return {
                'question': question,
                'search_rounds': 0,
                'selected_documents': [],
                'search_history': [],
                'total_documents_retrieved': 0,
                'final_context': "未找到相关信息",
                'total_search_time': time.time() - start_time,
                'model_info': {
                    'search_model': S3_SEARCH_MODEL_NAME,
                    'generator_model': S3_GENERATOR_MODEL_NAME,
                    'mode': 'SDK' if self.is_sdk_mode else 'HTTP'
                }
            }
        
        initial_results, doc_mapping = self.format_search_results(initial_chunks, 1)
        all_documents.update(doc_mapping)
        total_documents_retrieved += len(initial_chunks)
        
        # 记录初始搜索
        search_history.append({
            'round': 1,
            'type': 'initial_search',
            'query': question,
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - round_start,
            'results': {
                'count': len(initial_chunks),
                'documents': [
                    {
                        'id': doc['id'],
                        'similarity': doc['similarity'],
                        'content_preview': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                        'content': doc['content'],  # 提供完整内容
                        'document_id': doc.get('document_id', ''),
                        'chunk_id': doc.get('chunk_id', '')
                    }
                    for doc in doc_mapping.values()
                ]
            }
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
                round_start = time.time()
                
                # 使用Search LLM进行决策
                logger.info(f"第{current_round}轮 - Search Model决策")
                messages = [{"role": "user", "content": agent_input}]
                
                llm_start = time.time()
                llm_response = self.search_llm_client.chat_completion(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000
                )
                llm_duration = time.time() - llm_start
                
                # 提取响应内容
                if isinstance(llm_response, dict):
                    agent_response = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
                else:
                    agent_response = llm_response
                
                # 解析决策
                decision = self.extract_search_decision(agent_response)
                
                # 记录智能体决策
                search_history.append({
                    'round': current_round,
                    'type': 'agent_decision',
                    'timestamp': datetime.now().isoformat(),
                    'duration': llm_duration,
                    'agent_decision': {
                        'thinking': decision['thinking'],
                        'search_complete': decision['search_complete'],
                        'new_query': decision['new_query'],
                        'important_docs': decision['important_docs']
                    },
                    'raw_response': agent_response
                })
                
                # 处理重要文档
                if decision['important_docs']:
                    for doc_id in decision['important_docs']:
                        if doc_id in all_documents and len(selected_documents) < 3:
                            selected_documents.append(all_documents[doc_id])
                            logger.info(f"选中文档 {doc_id}")
                
                # 检查是否完成搜索
                if decision['search_complete']:
                    logger.info(f"搜索完成，共{current_round}轮")
                    break
                
                # 执行新搜索
                if decision['new_query']:
                    search_start = time.time()
                    new_chunks, success = self.search_step(
                        decision['new_query'], 
                        dataset_ids, 
                        top_k, 
                        similarity_threshold
                    )
                    search_duration = time.time() - search_start
                    
                    if success and new_chunks:
                        doc_id_start = max(all_documents.keys()) + 1 if all_documents else 1
                        new_results, new_doc_mapping = self.format_search_results(new_chunks, doc_id_start)
                        all_documents.update(new_doc_mapping)
                        total_documents_retrieved += len(new_chunks)
                        
                        # 记录新搜索结果
                        search_history.append({
                            'round': current_round,
                            'type': 'iterative_search',
                            'query': decision['new_query'],
                            'timestamp': datetime.now().isoformat(),
                            'duration': search_duration,
                            'results': {
                                'count': len(new_chunks),
                                'documents': [
                                    {
                                        'id': doc['id'],
                                        'similarity': doc['similarity'],
                                        'content_preview': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                                        'content': doc['content'],  # 提供完整内容
                                        'document_id': doc.get('document_id', ''),
                                        'chunk_id': doc.get('chunk_id', '')
                                    }
                                    for doc in new_doc_mapping.values()
                                ]
                            }
                        })
                        
                        # 更新智能体输入
                        agent_input = f"{agent_input}\n\n<information>\n{new_results}\n</information>"
                    else:
                        logger.warning(f"第{current_round}轮搜索无结果")
                
                current_round += 1
                
            except Exception as e:
                logger.error(f"第{current_round}轮处理失败: {e}")
                search_history.append({
                    'round': current_round,
                    'type': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                })
                break
        
        # 如果没有选中的文档，使用前3个
        if not selected_documents and all_documents:
            selected_documents = list(all_documents.values())[:3]
            logger.info(f"未明确选择文档，使用前{len(selected_documents)}个")
        
        # 构建最终上下文
        final_context = "\n\n".join([
            f"参考资料 {i+1}:\n{doc['content']}"
            for i, doc in enumerate(selected_documents)
        ])
        
        total_time = time.time() - start_time
        
        return {
            'question': question,
            'search_rounds': current_round,
            'total_documents_retrieved': total_documents_retrieved,
            'selected_documents': selected_documents,
            'search_history': search_history,
            'final_context': final_context,
            'total_search_time': total_time,
            'model_info': {
                'search_model': S3_SEARCH_MODEL_NAME,
                'generator_model': S3_GENERATOR_MODEL_NAME,
                'mode': 'SDK' if self.is_sdk_mode else 'HTTP'
            }
        }
    
    def synthesize_answer(self, question: str, selected_docs: List[Dict], 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """使用选中的文档生成最终答案"""
        if not selected_docs:
            return "抱歉，未找到相关信息来回答您的问题。"
        
        # 构建生成提示
        context = "\n\n".join([
            f"参考资料 {i+1}:\n{doc.get('content', '')}"
            for i, doc in enumerate(selected_docs)
        ])
        
        prompt = f"""基于以下参考资料回答用户问题。请确保答案准确、全面，并标注信息来源。

用户问题：{question}

{context}

请提供详细的答案，并在答案末尾标注使用了哪些参考资料。"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.generator_llm_client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if isinstance(response, dict):
                return response.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                return response
                
        except Exception as e:
            logger.error(f"答案生成失败: {e}")
            return f"生成答案时出错: {str(e)}"

# 创建别名以支持流式服务
class StreamingEnhancedS3Service(EnhancedS3RAGServiceV2):
    """支持流式事件的增强S3服务"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_callback = None
    
    def set_event_callback(self, callback):
        """设置事件回调函数"""
        self.event_callback = callback
    
    async def emit_event(self, event_type: str, data: Dict[str, Any], round: Optional[int] = None):
        """发送事件"""
        if self.event_callback:
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "round": round,
                "data": data
            }
            await self.event_callback(event)
    
    async def s3_search_process_streaming(self, question: str, dataset_ids: List[str], 
                                        max_rounds: int = 3, top_k: int = 5, 
                                        similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """带流式事件的S3搜索过程 - 调用父类方法"""
        # 这里简单地调用父类的方法
        return self.s3_search_process_with_history(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=max_rounds,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )