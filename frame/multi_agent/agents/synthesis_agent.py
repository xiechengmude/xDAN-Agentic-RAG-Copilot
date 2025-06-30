"""
综合智能体 - 专门负责信息综合和最终答案生成
"""

import asyncio
from typing import Dict, Any, List, Optional
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ..core.base_agent import BaseAgent
from ..core.message import Message, MessageType
from src.clients.litellm_client import LiteLLMSDKClientV2


class SynthesisAgent(BaseAgent):
    """综合智能体"""
    
    def __init__(self, name: str, description: str = "专门负责信息综合和最终答案生成的智能体"):
        super().__init__(name, description)
        
        # 初始化LLM客户端
        self.llm_client = LiteLLMSDKClientV2()
        
        # 注册消息处理器
        self.register_handler(MessageType.TASK, self._handle_synthesis_task)
        self.register_handler(MessageType.REQUEST, self._handle_synthesis_request)
        
        # 综合模板
        self.synthesis_templates = {
            "final_answer": """
基于以下收集的信息，请生成对问题的最终回答：

原始问题：
{question}

收集的信息：
{collected_info}

搜索结果摘要：
{search_summary}

分析结果：
{analysis_results}

要求：
1. 直接回答用户问题
2. 基于提供的信息，确保准确性
3. 结构清晰，逻辑性强
4. 如果信息不足，请说明
5. 提供信息来源（如有）

请生成完整的最终答案：
""",
            "multi_round_synthesis": """
这是一个多轮搜索的信息综合任务。

问题：{question}

已收集信息：
{previous_rounds}

当前轮新信息：
{current_round}

请分析：
1. 当前信息是否已足够回答问题
2. 还需要搜索哪些方面的信息
3. 如果信息充足，请生成最终答案
4. 如果信息不足，请提出下一轮搜索建议

分析结果：
""",
            "compare_sources": """
请比较和综合来自不同来源的信息：

问题：{question}

来源信息：
{sources_info}

请：
1. 识别信息的一致性和矛盾点
2. 评估各来源的可靠性
3. 综合得出最准确的答案
4. 指出需要进一步验证的信息

综合分析：
""",
            "structured_answer": """
请将以下信息整理成结构化的答案：

问题：{question}

原始信息：
{raw_info}

请按以下结构组织答案：
1. 核心回答
2. 详细说明
3. 关键数据/事实
4. 相关背景
5. 信息来源

结构化答案：
"""
        }
    
    async def on_start(self):
        """启动时初始化"""
        self.logger.info(f"SynthesisAgent {self.name} ready for synthesis tasks")
        self.state["status"] = "ready"
        self.state["syntheses_performed"] = 0
    
    async def on_stop(self):
        """停止时清理"""
        self.logger.info(f"SynthesisAgent {self.name} shutting down")
        self.state["status"] = "stopped"
    
    async def _handle_synthesis_task(self, message: Message):
        """处理综合任务"""
        task_content = message.content
        task_type = task_content.get("task_type")
        task_data = task_content.get("task_data", {})
        
        try:
            result = None
            
            if task_type == "final_answer":
                result = await self._generate_final_answer(
                    task_data.get("question", ""),
                    task_data.get("collected_info", {}),
                    task_data.get("search_results", []),
                    task_data.get("analysis_results", {})
                )
                
            elif task_type == "multi_round_synthesis":
                result = await self._multi_round_synthesis(
                    task_data.get("question", ""),
                    task_data.get("previous_rounds", []),
                    task_data.get("current_round", {})
                )
                
            elif task_type == "compare_sources":
                result = await self._compare_sources(
                    task_data.get("question", ""),
                    task_data.get("sources_info", [])
                )
                
            elif task_type == "structured_answer":
                result = await self._generate_structured_answer(
                    task_data.get("question", ""),
                    task_data.get("raw_info", "")
                )
                
            else:
                raise ValueError(f"Unknown synthesis task type: {task_type}")
            
            # 更新统计
            self.state["syntheses_performed"] += 1
            
            # 发送响应
            response = message.create_response(
                content={"synthesis_result": result},
                type=MessageType.RESULT
            )
            await self.send(response)
            
        except Exception as e:
            self.logger.error(f"Synthesis failed: {e}")
            response = message.create_response(
                content={"error": str(e)},
                type=MessageType.ERROR
            )
            await self.send(response)
    
    async def _handle_synthesis_request(self, message: Message):
        """处理综合请求"""
        # 转换为任务消息处理
        await self._handle_synthesis_task(message)
    
    async def _generate_final_answer(
        self, 
        question: str, 
        collected_info: Dict[str, Any],
        search_results: List[Dict],
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成最终答案"""
        
        if not question.strip():
            return {"final_answer": "", "error": "Empty question"}
        
        # 格式化信息
        info_text = self._format_collected_info(collected_info)
        search_text = self._format_search_results(search_results)
        analysis_text = self._format_analysis_results(analysis_results)
        
        prompt = self.synthesis_templates["final_answer"].format(
            question=question,
            collected_info=info_text,
            search_summary=search_text,
            analysis_results=analysis_text
        )
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的信息综合专家，善于基于多源信息生成准确、全面的答案。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            final_answer = result.choices[0].message.content if result.choices else ""
            
            return {
                "final_answer": final_answer,
                "sources_used": len(search_results),
                "info_sources": list(collected_info.keys()) if isinstance(collected_info, dict) else [],
                "answer_length": len(final_answer)
            }
            
        except Exception as e:
            self.logger.error(f"Final answer generation failed: {e}")
            return {"final_answer": "", "error": str(e)}
    
    async def _multi_round_synthesis(
        self,
        question: str,
        previous_rounds: List[Dict],
        current_round: Dict
    ) -> Dict[str, Any]:
        """多轮综合分析"""
        
        previous_text = "\n".join([
            f"第{i+1}轮: {round_data.get('summary', '')}" 
            for i, round_data in enumerate(previous_rounds)
        ])
        
        current_text = current_round.get("summary", "")
        
        prompt = self.synthesis_templates["multi_round_synthesis"].format(
            question=question,
            previous_rounds=previous_text,
            current_round=current_text
        )
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            synthesis = result.choices[0].message.content if result.choices else ""
            
            # 简单判断是否需要继续搜索
            need_more_search = "需要" in synthesis or "不足" in synthesis or "建议" in synthesis
            
            return {
                "synthesis": synthesis,
                "need_more_search": need_more_search,
                "total_rounds": len(previous_rounds) + 1,
                "confidence": 0.8 if not need_more_search else 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Multi-round synthesis failed: {e}")
            return {"synthesis": "", "error": str(e)}
    
    async def _compare_sources(self, question: str, sources_info: List[Dict]) -> Dict[str, Any]:
        """比较来源信息"""
        
        sources_text = "\n".join([
            f"来源{i+1}: {source.get('title', 'Unknown')}\n内容: {source.get('content', '')[:200]}..."
            for i, source in enumerate(sources_info)
        ])
        
        prompt = self.synthesis_templates["compare_sources"].format(
            question=question,
            sources_info=sources_text
        )
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            comparison = result.choices[0].message.content if result.choices else ""
            
            return {
                "comparison": comparison,
                "sources_count": len(sources_info),
                "reliability_assessment": "需要人工验证"  # 简化版本
            }
            
        except Exception as e:
            self.logger.error(f"Source comparison failed: {e}")
            return {"comparison": "", "error": str(e)}
    
    async def _generate_structured_answer(self, question: str, raw_info: str) -> Dict[str, Any]:
        """生成结构化答案"""
        
        prompt = self.synthesis_templates["structured_answer"].format(
            question=question,
            raw_info=raw_info
        )
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            structured_answer = result.choices[0].message.content if result.choices else ""
            
            return {
                "structured_answer": structured_answer,
                "raw_info_length": len(raw_info),
                "structure_applied": True
            }
            
        except Exception as e:
            self.logger.error(f"Structured answer generation failed: {e}")
            return {"structured_answer": "", "error": str(e)}
    
    def _format_collected_info(self, collected_info: Dict[str, Any]) -> str:
        """格式化收集的信息"""
        if not collected_info:
            return "暂无收集信息"
        
        formatted = []
        for key, value in collected_info.items():
            if isinstance(value, str):
                formatted.append(f"{key}: {value}")
            else:
                formatted.append(f"{key}: {str(value)}")
        
        return "\n".join(formatted)
    
    def _format_search_results(self, search_results: List[Dict]) -> str:
        """格式化搜索结果"""
        if not search_results:
            return "暂无搜索结果"
        
        formatted = []
        for i, result in enumerate(search_results[:5]):  # 限制前5个
            title = result.get("title", "无标题")
            snippet = result.get("snippet", "")
            formatted.append(f"{i+1}. {title}\n   {snippet[:100]}...")
        
        return "\n".join(formatted)
    
    def _format_analysis_results(self, analysis_results: Dict[str, Any]) -> str:
        """格式化分析结果"""
        if not analysis_results:
            return "暂无分析结果"
        
        formatted = []
        for key, value in analysis_results.items():
            if isinstance(value, dict):
                formatted.append(f"{key}: {value.get('summary', str(value))}")
            else:
                formatted.append(f"{key}: {str(value)}")
        
        return "\n".join(formatted)
    
    def get_synthesis_stats(self) -> Dict[str, Any]:
        """获取综合统计"""
        return {
            "syntheses_performed": self.state.get("syntheses_performed", 0),
            "status": self.state.get("status", "unknown"),
            "available_templates": list(self.synthesis_templates.keys())
        }