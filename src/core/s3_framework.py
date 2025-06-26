#!/usr/bin/env python3
"""
S3框架核心实现（Search-Select-Synthesize）
基于架构文档的Agentic-RAG-Service设计
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from datetime import datetime

logger = logging.getLogger(__name__)

class S3FrameworkAgent:
    """
    S3框架智能体 - 实现Search-Select-Synthesize工作流
    基于架构文档中定义的智能体System Prompt
    """
    
    # S3智能体系统提示词 - 基于官方论文版本（保持原始重要性）
    AGENT_SYSTEM_PROMPT = """You are a search copilot for a generation model. Based on a user's query and initial searched results, you will first determine if the searched results are enough to produce an answer.

If the searched results are enough, you will use <search_complete>True</search_complete> to indicate that you have gathered enough information for the generation model to produce an answer.

If the searched results are not enough, you will go through a loop of <query> → <information> → <important_info> → <search_complete> → <query> (if not complete) ..., to help the generation model to generate a better answer with more relevant information searched.

You should show the search query between <query> and </query> in JSON format.

Based on the search query, we will return the top searched results between <information> and </information>. You need to put the doc ids of the important documents (up to 3 documents, within the current information window) between <important_info> and </important_info> (e.g., <important_info>[1, 4]</important_info>).

A search query must be followed by a <search_complete> tag if the search is not complete.

After reviewing the information, you must decide whether to continue searching with a new query or indicate that the search is complete. If you need more information, use <search_complete>False</search_complete>. Otherwise, use <search_complete>True</search_complete> to terminate the search.

Note: Only the content between <important_info> will be used by the generation model to produce an answer."""

    def __init__(self, ragflow_client, litellm_sdk_client):
        """
        初始化S3框架智能体
        
        Args:
            ragflow_client: RAGFlow检索客户端（专门负责知识库检索）
            litellm_sdk_client: LiteLLM SDK客户端（内核服务，负责智能体推理和答案生成）
        """
        self.ragflow_client = ragflow_client
        self.litellm_client = litellm_sdk_client
        
        logger.info("S3框架智能体初始化完成")
        logger.info("RAGFlow: 负责检索和知识库管理")
        logger.info("LiteLLM SDK: 内核服务，负责智能体推理和答案生成")

    def format_search_results(self, chunks: List[Dict], doc_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """
        格式化搜索结果为智能体可理解的格式
        
        Args:
            chunks: RAGFlow返回的检索结果
            doc_id_start: 文档ID起始编号
            
        Returns:
            格式化的信息字符串和文档映射
        """
        if not chunks:
            return "没有找到相关信息。", {}
        
        formatted_info = []
        doc_mapping = {}
        
        for i, chunk in enumerate(chunks):
            doc_id = doc_id_start + i
            content = chunk.get('content', '')
            similarity = chunk.get('similarity', 0)
            source = chunk.get('document_name', 'Unknown')
            
            formatted_info.append(
                f"[{doc_id}] {content}\n"
                f"来源: {source} (相似度: {similarity:.3f})"
            )
            
            doc_mapping[doc_id] = chunk
        
        return "\n\n".join(formatted_info), doc_mapping

    def extract_agent_decision(self, agent_response: str) -> Dict[str, Any]:
        """
        解析智能体的决策响应
        
        Args:
            agent_response: 智能体的响应文本
            
        Returns:
            解析后的决策信息
        """
        decision = {
            "search_complete": False,
            "next_query": None,
            "important_docs": [],
            "thinking": None
        }
        
        # 提取思考过程
        think_match = re.search(r'<think>(.*?)</think>', agent_response, re.DOTALL)
        if think_match:
            decision["thinking"] = think_match.group(1).strip()
        
        # 提取搜索完成状态
        complete_match = re.search(r'<search_complete>(.*?)</search_complete>', agent_response)
        if complete_match:
            complete_text = complete_match.group(1).strip().lower()
            decision["search_complete"] = complete_text == "true"
        
        # 提取下一个查询
        if not decision["search_complete"]:
            query_match = re.search(r'<query>(.*?)</query>', agent_response, re.DOTALL)
            if query_match:
                try:
                    query_json = json.loads(query_match.group(1).strip())
                    decision["next_query"] = query_json.get("query", query_json.get("question", ""))
                except json.JSONDecodeError:
                    decision["next_query"] = query_match.group(1).strip()
        
        # 提取重要文档ID
        docs_match = re.search(r'<important_info>\[(.*?)\]</important_info>', agent_response)
        if docs_match:
            try:
                doc_ids_str = docs_match.group(1).strip()
                if doc_ids_str:
                    decision["important_docs"] = [int(x.strip()) for x in doc_ids_str.split(',')]
            except (ValueError, AttributeError):
                pass
        
        return decision

    async def search_phase(self, question: str, dataset_ids: List[str], 
                          top_k: int = 10, similarity_threshold: float = 0.1) -> Tuple[List[Dict], bool]:
        """
        S3框架的Search阶段：从RAGFlow执行检索
        
        Args:
            question: 用户问题
            dataset_ids: 数据集ID列表
            top_k: 检索数量
            similarity_threshold: 相似度阈值
            
        Returns:
            检索结果和成功状态
        """
        try:
            logger.info(f"S3-Search阶段：检索问题 - {question[:50]}...")
            
            # 使用RAGFlow进行检索
            result = self.ragflow_client.retrieve_chunks(
                question=question,
                dataset_ids=dataset_ids,
                page_size=top_k
            )
            
            if result.get("code") == 0:
                chunks = result.get("data", {}).get("chunks", [])
                logger.info(f"S3-Search成功：找到 {len(chunks)} 个相关文档")
                return chunks, True
            else:
                logger.error(f"S3-Search失败：{result.get('message')}")
                return [], False
                
        except Exception as e:
            logger.error(f"S3-Search异常：{e}")
            return [], False

    async def select_phase(self, question: str, search_results: List[Dict], 
                          round_num: int = 1, max_rounds: int = 3) -> Dict[str, Any]:
        """
        S3框架的Select阶段：智能体判断信息充分性并选择重要文档
        
        Args:
            question: 原始问题
            search_results: 当前搜索结果
            round_num: 当前轮次
            max_rounds: 最大轮次
            
        Returns:
            智能体决策结果
        """
        try:
            logger.info(f"S3-Select阶段（第{round_num}轮）：分析信息充分性...")
            
            # 格式化搜索结果
            formatted_info, doc_mapping = self.format_search_results(search_results)
            
            # 构建智能体输入
            if round_num == 1:
                user_prompt = f"""<question>
{question}
</question>

<information>
{formatted_info}
</information>

Please analyze whether the above information is sufficient to answer the question. If sufficient, mark the important documents. If not, suggest a new search query."""
            else:
                user_prompt = f"""继续分析问题：{question}（第{round_num}/{max_rounds}轮，剩余{max_rounds-round_num}轮）

当前搜索结果：
<information>
{formatted_info}
</information>

请判断当前信息是否足够回答问题。如果是最后一轮或信息已充足，请标记搜索完成。"""
            
            # 构建智能体输入
            messages = [
                {"role": "system", "content": self.AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
            
            # 使用LiteLLM SDK进行智能体推理
            response = await self.litellm_client.chat_completion(
                messages=messages,
                use_case="agent"  # 使用智能体模型和参数
            )
            
            agent_response = response.choices[0].message.content
            logger.info(f"智能体响应长度：{len(agent_response)}")
            
            # 解析智能体决策
            decision = self.extract_agent_decision(agent_response)
            decision["agent_response"] = agent_response
            decision["doc_mapping"] = doc_mapping
            decision["round"] = round_num
            
            return decision
            
        except Exception as e:
            logger.error(f"S3-Select阶段失败：{e}")
            return {
                "search_complete": True,  # 出错时终止搜索
                "important_docs": list(range(1, min(4, len(search_results) + 1))),  # 选择前3个
                "doc_mapping": self.format_search_results(search_results)[1],
                "error": str(e)
            }

    async def synthesize_phase(self, question: str, selected_docs: List[Dict], 
                              stream: bool = False):
        """
        S3框架的Synthesize阶段：基于选定文档生成最终答案
        
        Args:
            question: 原始问题
            selected_docs: 选定的重要文档
            stream: 是否流式生成
            
        Returns:
            生成的答案
        """
        try:
            logger.info(f"S3-Synthesize阶段：基于 {len(selected_docs)} 个文档生成答案...")
            
            # 构建上下文
            context_parts = []
            for i, doc in enumerate(selected_docs, 1):
                content = doc.get('content', '')
                source = doc.get('document_name', 'Unknown')
                context_parts.append(f"[文档{i}] {content}\n来源：{source}")
            
            context = "\n\n".join(context_parts)
            
            # 构建生成提示
            system_prompt = """你是一个专业的问答助手。请基于提供的上下文信息准确回答用户的问题。

要求：
1. 答案要准确、相关、有帮助
2. 如果上下文中没有足够信息，请诚实说明
3. 保持答案的逻辑性和连贯性
4. 可以引用文档编号来标注信息来源"""

            user_prompt = f"""请基于以下上下文信息回答问题：

上下文信息：
{context}

问题：{question}

请提供准确、有用的回答："""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 使用LiteLLM SDK生成答案
            if stream:
                response_stream = await self.litellm_client.chat_completion(
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=2000,
                    stream=True
                )
                
                # 处理流式响应
                answer_parts = []
                async for chunk in response_stream:
                    if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        answer_parts.append(content)
                        yield content  # 流式返回
                
                # 不能在async generator中使用return，用yield返回最终结果
                yield {"final_answer": ''.join(answer_parts)}
            else:
                response = await self.litellm_client.chat_completion(
                    messages=messages,
                    model="gpt-4o-mini",
                    temperature=0.7,
                    max_tokens=2000
                )
                
                answer = response.choices[0].message.content
                logger.info(f"S3-Synthesize完成：生成答案长度 {len(answer)}")
                yield {"final_answer": answer}
                
        except Exception as e:
            logger.error(f"S3-Synthesize阶段失败：{e}")
            yield {"final_answer": f"抱歉，在生成答案时遇到错误：{e}"}

    async def execute_s3_workflow(self, question: str, dataset_ids: List[str], 
                                 max_rounds: int = 3, top_k: int = 10, 
                                 stream: bool = False):
        """
        执行完整的S3工作流：Search-Select-Synthesize
        
        Args:
            question: 用户问题
            dataset_ids: 数据集ID列表
            max_rounds: 最大搜索轮数
            top_k: 每轮检索数量
            stream: 是否流式返回
            
        Returns:
            完整的S3执行结果
        """
        workflow_result = {
            "question": question,
            "rounds": [],
            "final_answer": "",
            "selected_documents": [],
            "workflow_completed": False,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"开始S3工作流：{question[:50]}...")
            all_search_results = []
            
            for round_num in range(1, max_rounds + 1):
                logger.info(f"=== S3工作流第{round_num}轮 ===")
                
                # 1. Search阶段
                if round_num == 1:
                    search_query = question
                else:
                    # 使用上一轮智能体建议的查询
                    last_decision = workflow_result["rounds"][-1]["decision"]
                    search_query = last_decision.get("next_query", question)
                
                search_results, search_success = await self.search_phase(
                    search_query, dataset_ids, top_k
                )
                
                if not search_success:
                    break
                
                all_search_results.extend(search_results)
                
                # 2. Select阶段
                decision = await self.select_phase(question, all_search_results, round_num, max_rounds)
                
                # 记录本轮结果
                round_result = {
                    "round": round_num,
                    "search_query": search_query,
                    "search_results_count": len(search_results),
                    "decision": decision,
                    "timestamp": datetime.now().isoformat()
                }
                workflow_result["rounds"].append(round_result)
                
                # 检查是否搜索完成
                if decision.get("search_complete", False):
                    logger.info(f"智能体判断信息充足，停止搜索（第{round_num}轮）")
                    
                    # 提取选定的重要文档
                    important_doc_ids = decision.get("important_docs", [])
                    doc_mapping = decision.get("doc_mapping", {})
                    
                    selected_docs = []
                    for doc_id in important_doc_ids:
                        if doc_id in doc_mapping:
                            selected_docs.append(doc_mapping[doc_id])
                    
                    # 如果没有选定文档，使用前3个
                    if not selected_docs and all_search_results:
                        selected_docs = all_search_results[:3]
                    
                    workflow_result["selected_documents"] = selected_docs
                    
                    # 3. Synthesize阶段
                    if stream:
                        # 流式生成答案
                        final_answer = ""
                        async for chunk in self.synthesize_phase(question, selected_docs, stream=True):
                            if isinstance(chunk, dict) and "final_answer" in chunk:
                                final_answer = chunk["final_answer"]
                                workflow_result["final_answer"] = final_answer
                            else:
                                yield chunk
                    else:
                        async for result in self.synthesize_phase(question, selected_docs, stream=False):
                            if isinstance(result, dict) and "final_answer" in result:
                                final_answer = result["final_answer"]
                                workflow_result["final_answer"] = final_answer
                                break
                    
                    workflow_result["workflow_completed"] = True
                    break
                else:
                    logger.info(f"智能体判断需要更多信息，继续搜索...")
                    if not decision.get("next_query"):
                        logger.warning("智能体未提供下一个搜索查询，使用原问题")
                        decision["next_query"] = question
            
            if not workflow_result["workflow_completed"]:
                logger.warning("达到最大搜索轮数，强制结束")
                # 使用所有搜索结果生成答案
                if all_search_results:
                    workflow_result["selected_documents"] = all_search_results[:3]
                    async for result in self.synthesize_phase(
                        question, workflow_result["selected_documents"], stream=False
                    ):
                        if isinstance(result, dict) and "final_answer" in result:
                            workflow_result["final_answer"] = result["final_answer"]
                            break
                    workflow_result["workflow_completed"] = True
                else:
                    workflow_result["final_answer"] = "抱歉，没有找到相关信息来回答您的问题。"
            
            workflow_result["end_time"] = datetime.now().isoformat()
            logger.info("S3工作流执行完成")
            
            if stream:
                yield {"workflow_result": workflow_result}
            else:
                yield workflow_result
            
        except Exception as e:
            logger.error(f"S3工作流执行失败：{e}")
            workflow_result["error"] = str(e)
            workflow_result["final_answer"] = f"抱歉，在处理您的问题时遇到错误：{e}"
            if stream:
                yield {"workflow_result": workflow_result}
            else:
                yield workflow_result