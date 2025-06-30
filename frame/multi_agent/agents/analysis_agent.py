"""
分析智能体 - 专门负责数据分析和信息提取
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


class AnalysisAgent(BaseAgent):
    """分析智能体"""
    
    def __init__(self, name: str, description: str = "专门负责数据分析和信息提取的智能体"):
        super().__init__(name, description)
        
        # 初始化LLM客户端
        self.llm_client = LiteLLMSDKClientV2()
        
        # 注册消息处理器
        self.register_handler(MessageType.TASK, self._handle_analysis_task)
        self.register_handler(MessageType.REQUEST, self._handle_analysis_request)
        
        # 分析缓存
        self.analysis_cache: Dict[str, Any] = {}
        
        # 分析模板
        self.analysis_templates = {
            "extract_key_points": """
从以下内容中提取关键要点：

内容：
{content}

请提取出最重要的5-10个关键要点，每个要点用简洁的语言描述：
""",
            "summarize": """
请对以下内容进行摘要：

内容：
{content}

要求：
1. 保持客观中立
2. 突出核心信息
3. 控制在200字以内
""",
            "analyze_sentiment": """
请分析以下内容的情感倾向：

内容：
{content}

请从以下维度分析：
1. 整体情感倾向（正面/中性/负面）
2. 情感强度（1-5分）
3. 主要情感关键词
""",
            "extract_entities": """
从以下内容中提取实体信息：

内容：
{content}

请提取：
1. 人名
2. 地名
3. 组织机构
4. 时间
5. 数字/金额
""",
            "compare": """
请比较以下两个内容的异同：

内容A：
{content_a}

内容B：
{content_b}

请从以下角度比较：
1. 相同点
2. 不同点
3. 各自优势
4. 综合评价
"""
        }
    
    async def on_start(self):
        """启动时初始化"""
        self.logger.info(f"AnalysisAgent {self.name} ready for analysis tasks")
        self.state["status"] = "ready"
        self.state["analyses_performed"] = 0
    
    async def on_stop(self):
        """停止时清理"""
        self.logger.info(f"AnalysisAgent {self.name} shutting down")
        self.state["status"] = "stopped"
    
    async def _handle_analysis_task(self, message: Message):
        """处理分析任务"""
        task_content = message.content
        task_type = task_content.get("task_type")
        task_data = task_content.get("task_data", {})
        
        try:
            result = None
            
            if task_type == "extract_key_points":
                result = await self._extract_key_points(task_data.get("content", ""))
                
            elif task_type == "summarize":
                result = await self._summarize(task_data.get("content", ""))
                
            elif task_type == "analyze_sentiment":
                result = await self._analyze_sentiment(task_data.get("content", ""))
                
            elif task_type == "extract_entities":
                result = await self._extract_entities(task_data.get("content", ""))
                
            elif task_type == "compare":
                result = await self._compare_content(
                    task_data.get("content_a", ""),
                    task_data.get("content_b", "")
                )
                
            elif task_type == "analyze_search_results":
                result = await self._analyze_search_results(task_data.get("search_results", []))
                
            else:
                raise ValueError(f"Unknown analysis task type: {task_type}")
            
            # 更新统计
            self.state["analyses_performed"] += 1
            
            # 发送响应
            response = message.create_response(
                content={"analysis_result": result},
                type=MessageType.RESULT
            )
            await self.send(response)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            response = message.create_response(
                content={"error": str(e)},
                type=MessageType.ERROR
            )
            await self.send(response)
    
    async def _handle_analysis_request(self, message: Message):
        """处理分析请求"""
        # 转换为任务消息处理
        await self._handle_analysis_task(message)
    
    async def _extract_key_points(self, content: str) -> Dict[str, Any]:
        """提取关键要点"""
        if not content.strip():
            return {"key_points": [], "error": "Empty content"}
        
        prompt = self.analysis_templates["extract_key_points"].format(content=content)
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            response_text = result.choices[0].message.content if result.choices else ""
            
            # 简单解析关键要点
            key_points = []
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('1.')):
                    key_points.append(line)
            
            return {
                "key_points": key_points,
                "raw_response": response_text
            }
            
        except Exception as e:
            self.logger.error(f"Key points extraction failed: {e}")
            return {"key_points": [], "error": str(e)}
    
    async def _summarize(self, content: str) -> Dict[str, Any]:
        """内容摘要"""
        if not content.strip():
            return {"summary": "", "error": "Empty content"}
        
        prompt = self.analysis_templates["summarize"].format(content=content)
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            summary = result.choices[0].message.content if result.choices else ""
            
            return {
                "summary": summary.strip(),
                "original_length": len(content),
                "summary_length": len(summary)
            }
            
        except Exception as e:
            self.logger.error(f"Summarization failed: {e}")
            return {"summary": "", "error": str(e)}
    
    async def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """情感分析"""
        if not content.strip():
            return {"sentiment": "neutral", "error": "Empty content"}
        
        prompt = self.analysis_templates["analyze_sentiment"].format(content=content)
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            response_text = result.choices[0].message.content if result.choices else ""
            
            # 简单解析情感分析结果
            sentiment = "neutral"
            if "正面" in response_text or "积极" in response_text:
                sentiment = "positive"
            elif "负面" in response_text or "消极" in response_text:
                sentiment = "negative"
            
            return {
                "sentiment": sentiment,
                "analysis": response_text,
                "confidence": 0.8  # 简化的置信度
            }
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {e}")
            return {"sentiment": "neutral", "error": str(e)}
    
    async def _extract_entities(self, content: str) -> Dict[str, Any]:
        """实体提取"""
        if not content.strip():
            return {"entities": {}, "error": "Empty content"}
        
        prompt = self.analysis_templates["extract_entities"].format(content=content)
        
        try:
            result = await self.llm_client.completion(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            response_text = result.choices[0].message.content if result.choices else ""
            
            return {
                "entities": {
                    "raw_extraction": response_text
                },
                "content_length": len(content)
            }
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return {"entities": {}, "error": str(e)}
    
    async def _compare_content(self, content_a: str, content_b: str) -> Dict[str, Any]:
        """内容比较"""
        if not content_a.strip() or not content_b.strip():
            return {"comparison": "", "error": "Empty content"}
        
        prompt = self.analysis_templates["compare"].format(
            content_a=content_a,
            content_b=content_b
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
                "content_a_length": len(content_a),
                "content_b_length": len(content_b)
            }
            
        except Exception as e:
            self.logger.error(f"Content comparison failed: {e}")
            return {"comparison": "", "error": str(e)}
    
    async def _analyze_search_results(self, search_results: List[Dict]) -> Dict[str, Any]:
        """分析搜索结果"""
        if not search_results:
            return {"analysis": "No search results to analyze"}
        
        # 提取搜索结果的关键信息
        titles = [result.get("title", "") for result in search_results]
        snippets = [result.get("snippet", "") for result in search_results]
        
        combined_content = "\n".join([f"标题: {title}\n摘要: {snippet}" 
                                     for title, snippet in zip(titles, snippets)])
        
        # 分析组合内容
        summary = await self._summarize(combined_content)
        key_points = await self._extract_key_points(combined_content)
        
        return {
            "total_results": len(search_results),
            "summary": summary,
            "key_points": key_points,
            "result_sources": [result.get("link", "") for result in search_results]
        }
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """获取分析统计"""
        return {
            "analyses_performed": self.state.get("analyses_performed", 0),
            "cache_size": len(self.analysis_cache),
            "status": self.state.get("status", "unknown"),
            "available_templates": list(self.analysis_templates.keys())
        }