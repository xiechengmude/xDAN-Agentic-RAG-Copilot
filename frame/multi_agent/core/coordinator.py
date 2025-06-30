"""
智能体协调器 - 高级工作流编排和智能体协调
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from .agent_manager import AgentManager
from .message import Message, MessageType, TaskMessage
from ..agents.search_agent import SearchAgent
from ..agents.analysis_agent import AnalysisAgent
from ..agents.synthesis_agent import SynthesisAgent


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MultiAgentCoordinator(AgentManager):
    """多智能体协调器"""
    
    def __init__(self, name: str = "MultiAgentCoordinator"):
        super().__init__(name)
        
        # 工作流管理
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # 响应等待管理
        self.pending_responses: Dict[str, asyncio.Event] = {}
        self.response_results: Dict[str, Any] = {}
        
        # 注册智能体类型
        self.register_agent_type("search", SearchAgent)
        self.register_agent_type("analysis", AnalysisAgent)
        self.register_agent_type("synthesis", SynthesisAgent)
        
    async def setup_default_agents(self):
        """设置默认智能体"""
        # 创建默认智能体
        await self.create_agent("search", "search_agent")
        await self.create_agent("analysis", "analysis_agent")
        await self.create_agent("synthesis", "synthesis_agent")
        
        self.logger.info("Default agents setup completed")
    
    async def execute_search_workflow(self, question: str, **kwargs) -> Dict[str, Any]:
        """执行搜索工作流"""
        workflow_id = f"search_{datetime.now().timestamp()}"
        
        try:
            # 记录工作流开始
            self.active_workflows[workflow_id] = {
                "status": WorkflowStatus.RUNNING,
                "question": question,
                "start_time": datetime.now(),
                "steps": []
            }
            
            # 步骤1: 搜索信息
            search_result = await self._execute_search_step(question, **kwargs)
            self.active_workflows[workflow_id]["steps"].append({
                "step": "search",
                "result": search_result,
                "timestamp": datetime.now()
            })
            
            # 步骤2: 分析搜索结果
            analysis_result = await self._execute_analysis_step(
                search_result, question
            )
            self.active_workflows[workflow_id]["steps"].append({
                "step": "analysis", 
                "result": analysis_result,
                "timestamp": datetime.now()
            })
            
            # 步骤3: 综合生成最终答案
            synthesis_result = await self._execute_synthesis_step(
                question, search_result, analysis_result
            )
            self.active_workflows[workflow_id]["steps"].append({
                "step": "synthesis",
                "result": synthesis_result,
                "timestamp": datetime.now()
            })
            
            # 工作流完成
            self.active_workflows[workflow_id]["status"] = WorkflowStatus.COMPLETED
            self.active_workflows[workflow_id]["end_time"] = datetime.now()
            
            # 构建最终结果
            final_result = {
                "workflow_id": workflow_id,
                "question": question,
                "final_answer": synthesis_result.get("synthesis_result", {}).get("final_answer", ""),
                "search_results": search_result.get("results", []),
                "analysis": analysis_result,
                "synthesis": synthesis_result,
                "workflow_status": WorkflowStatus.COMPLETED.value,
                "duration": (
                    self.active_workflows[workflow_id]["end_time"] - 
                    self.active_workflows[workflow_id]["start_time"]
                ).total_seconds()
            }
            
            return final_result
            
        except Exception as e:
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            
            # 标记工作流失败
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = WorkflowStatus.FAILED
                self.active_workflows[workflow_id]["error"] = str(e)
            
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_status": WorkflowStatus.FAILED.value
            }
    
    async def _execute_search_step(self, question: str, **kwargs) -> Dict[str, Any]:
        """执行搜索步骤"""
        num_results = kwargs.get("num_results", 10)
        include_crawl = kwargs.get("include_crawl", True)
        
        # 创建搜索任务
        task_message = TaskMessage(
            task_type="search",
            task_data={
                "query": question,
                "num_results": num_results,
                "include_crawl": include_crawl
            },
            sender=self.name,
            receiver="search_agent"
        )
        
        # 发送任务并等待响应
        result = await self._send_task_and_wait(task_message, timeout=60)
        
        if result and "error" not in result:
            self.logger.info(f"Search completed: found {len(result.get('results', []))} results")
        else:
            self.logger.error(f"Search failed: {result.get('error', 'Unknown error')}")
        
        return result or {}
    
    async def _execute_analysis_step(self, search_result: Dict[str, Any], question: str) -> Dict[str, Any]:
        """执行分析步骤"""
        search_results = search_result.get("results", [])
        
        if not search_results:
            return {"error": "No search results to analyze"}
        
        # 创建分析任务
        task_message = TaskMessage(
            task_type="analyze_search_results",
            task_data={
                "search_results": search_results,
                "question": question
            },
            sender=self.name,
            receiver="analysis_agent"
        )
        
        # 发送任务并等待响应
        result = await self._send_task_and_wait(task_message, timeout=30)
        
        if result and "error" not in result:
            self.logger.info("Analysis completed successfully")
        else:
            self.logger.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        
        return result or {}
    
    async def _execute_synthesis_step(
        self, 
        question: str, 
        search_result: Dict[str, Any], 
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行综合步骤"""
        
        # 创建综合任务
        task_message = TaskMessage(
            task_type="final_answer",
            task_data={
                "question": question,
                "collected_info": {
                    "search_summary": f"Found {len(search_result.get('results', []))} search results",
                    "analysis_summary": analysis_result.get("analysis_result", {}).get("summary", {}).get("summary", "")
                },
                "search_results": search_result.get("results", []),
                "analysis_results": analysis_result.get("analysis_result", {})
            },
            sender=self.name,
            receiver="synthesis_agent"
        )
        
        # 发送任务并等待响应
        result = await self._send_task_and_wait(task_message, timeout=45)
        
        if result and "error" not in result:
            self.logger.info("Synthesis completed successfully")
        else:
            self.logger.error(f"Synthesis failed: {result.get('error', 'Unknown error')}")
        
        return result or {}
    
    async def _send_task_and_wait(self, task_message: TaskMessage, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """发送任务并等待响应"""
        correlation_id = task_message.correlation_id or task_message.id
        
        # 设置响应等待
        response_event = asyncio.Event()
        self.pending_responses[correlation_id] = response_event
        
        try:
            # 发送任务
            await self.send_message(task_message)
            
            # 等待响应
            await asyncio.wait_for(response_event.wait(), timeout=timeout)
            
            # 获取结果
            result = self.response_results.get(correlation_id)
            
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_message.content.get('task_type')} timed out after {timeout}s")
            return {"error": f"Task timed out after {timeout} seconds"}
            
        finally:
            # 清理
            self.pending_responses.pop(correlation_id, None)
            self.response_results.pop(correlation_id, None)
    
    async def _monitor_agent_output(self, agent):
        """重写智能体输出监控，处理响应"""
        while self.is_running and agent.is_running:
            try:
                # 从智能体的输出队列获取消息
                message = await asyncio.wait_for(agent.outbox.get(), timeout=1.0)
                
                # 检查是否是我们等待的响应
                if message.correlation_id in self.pending_responses:
                    self.response_results[message.correlation_id] = message.content
                    self.pending_responses[message.correlation_id].set()
                else:
                    # 正常路由消息
                    await self.send_message(message)
                
                self.stats["messages_processed"] += 1
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error monitoring agent {agent.name}: {e}")
    
    async def execute_multi_round_search(
        self, 
        question: str, 
        max_rounds: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """执行多轮搜索工作流"""
        workflow_id = f"multi_search_{datetime.now().timestamp()}"
        
        try:
            # 初始化工作流
            self.active_workflows[workflow_id] = {
                "status": WorkflowStatus.RUNNING,
                "question": question,
                "start_time": datetime.now(),
                "rounds": [],
                "max_rounds": max_rounds
            }
            
            all_search_results = []
            all_analysis_results = []
            
            for round_num in range(1, max_rounds + 1):
                self.logger.info(f"Starting round {round_num}/{max_rounds}")
                
                # 第一轮使用原始问题，后续轮次可能需要调整查询
                if round_num == 1:
                    search_query = question
                else:
                    # 基于前一轮结果调整搜索查询
                    search_query = await self._generate_next_search_query(
                        question, all_search_results, all_analysis_results
                    )
                
                # 执行搜索
                search_result = await self._execute_search_step(
                    search_query, 
                    num_results=kwargs.get("num_results", 8)
                )
                
                # 分析结果
                analysis_result = await self._execute_analysis_step(search_result, question)
                
                # 记录轮次结果
                round_data = {
                    "round": round_num,
                    "query": search_query,
                    "search_result": search_result,
                    "analysis_result": analysis_result,
                    "timestamp": datetime.now()
                }
                
                self.active_workflows[workflow_id]["rounds"].append(round_data)
                all_search_results.extend(search_result.get("results", []))
                all_analysis_results.append(analysis_result)
                
                # 检查是否需要继续搜索
                if round_num < max_rounds:
                    need_more = await self._assess_if_more_search_needed(
                        question, all_search_results, all_analysis_results
                    )
                    
                    if not need_more:
                        self.logger.info(f"Sufficient information found after {round_num} rounds")
                        break
            
            # 最终综合
            synthesis_result = await self._execute_final_synthesis(
                question, all_search_results, all_analysis_results
            )
            
            # 完成工作流
            self.active_workflows[workflow_id]["status"] = WorkflowStatus.COMPLETED
            self.active_workflows[workflow_id]["end_time"] = datetime.now()
            self.active_workflows[workflow_id]["synthesis"] = synthesis_result
            
            return {
                "workflow_id": workflow_id,
                "question": question,
                "total_rounds": len(self.active_workflows[workflow_id]["rounds"]),
                "final_answer": synthesis_result.get("synthesis_result", {}).get("final_answer", ""),
                "all_search_results": all_search_results,
                "round_details": self.active_workflows[workflow_id]["rounds"],
                "synthesis": synthesis_result,
                "workflow_status": WorkflowStatus.COMPLETED.value
            }
            
        except Exception as e:
            self.logger.error(f"Multi-round workflow {workflow_id} failed: {e}")
            
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id]["status"] = WorkflowStatus.FAILED
                self.active_workflows[workflow_id]["error"] = str(e)
            
            return {
                "workflow_id": workflow_id,
                "error": str(e),
                "workflow_status": WorkflowStatus.FAILED.value
            }
    
    async def _generate_next_search_query(
        self, 
        original_question: str, 
        previous_results: List[Dict], 
        previous_analyses: List[Dict]
    ) -> str:
        """生成下一轮搜索查询"""
        # 简化版本：在原问题基础上添加更具体的关键词
        # 实际实现中可以使用LLM来生成更智能的查询
        
        if len(previous_results) > 0:
            # 基于前一轮结果调整查询
            return f"{original_question} 详细分析 深入研究"
        
        return original_question
    
    async def _assess_if_more_search_needed(
        self, 
        question: str, 
        all_results: List[Dict], 
        all_analyses: List[Dict]
    ) -> bool:
        """评估是否需要更多搜索"""
        # 简化判断：如果结果数量足够，则停止
        if len(all_results) >= 15:  # 阈值可配置
            return False
        
        # 可以加入更复杂的判断逻辑
        return True
    
    async def _execute_final_synthesis(
        self, 
        question: str, 
        all_search_results: List[Dict], 
        all_analysis_results: List[Dict]
    ) -> Dict[str, Any]:
        """执行最终综合"""
        
        # 汇总所有分析结果
        combined_analysis = {
            "total_sources": len(all_search_results),
            "analysis_rounds": len(all_analysis_results),
            "key_insights": []
        }
        
        for analysis in all_analysis_results:
            if "analysis_result" in analysis:
                combined_analysis["key_insights"].append(
                    analysis["analysis_result"].get("summary", {})
                )
        
        # 创建最终综合任务
        task_message = TaskMessage(
            task_type="final_answer",
            task_data={
                "question": question,
                "collected_info": {
                    "multi_round_summary": f"Collected {len(all_search_results)} sources across {len(all_analysis_results)} rounds"
                },
                "search_results": all_search_results,
                "analysis_results": combined_analysis
            },
            sender=self.name,
            receiver="synthesis_agent"
        )
        
        return await self._send_task_and_wait(task_message, timeout=60)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        return self.active_workflows.get(workflow_id)
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """列出活动工作流"""
        return [
            {
                "workflow_id": wf_id,
                "status": wf_data["status"].value if isinstance(wf_data["status"], WorkflowStatus) else wf_data["status"],
                "question": wf_data.get("question", ""),
                "start_time": wf_data.get("start_time", "").isoformat() if isinstance(wf_data.get("start_time"), datetime) else str(wf_data.get("start_time", ""))
            }
            for wf_id, wf_data in self.active_workflows.items()
        ]