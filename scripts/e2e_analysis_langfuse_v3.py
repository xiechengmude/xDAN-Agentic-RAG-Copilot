#!/usr/bin/env python3
"""
使用Langfuse v3的端到端搜索分析脚本
由于LiteLLM不兼容Langfuse v3，我们使用Langfuse的装饰器和观察器
"""

import json
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import logging
from dotenv import load_dotenv

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

# Langfuse v3 imports
from langfuse import langfuse_context
from langfuse.decorators import observe, langfuse_context
from langfuse.client import Langfuse

from src.core.flash_search_engine import FlashSearchEngine
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LangfuseV3Analysis:
    """Langfuse v3追踪的分析结果"""
    question_id: str
    question: str
    category: str
    trace_url: Optional[str] = None
    stages_data: Dict[str, Any] = field(default_factory=dict)
    evaluation_data: Dict[str, Any] = field(default_factory=dict)
    total_duration: float = 0.0
    success: bool = False


class LangfuseV3Analyzer:
    """使用Langfuse v3的分析器"""
    
    def __init__(self):
        # 初始化Langfuse v3客户端
        self.langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        )
        
        # 验证连接
        try:
            # v3使用不同的验证方法
            self.langfuse.auth_check()
            logger.info("✅ Langfuse v3连接成功")
        except Exception as e:
            logger.error(f"❌ Langfuse v3连接失败: {e}")
            raise
        
        # 初始化组件
        self.search_engine = FlashSearchEngine()
        self.llm_client = EnhancedLiteLLMClient()
    
    @observe(name="e2e-search-analysis")
    async def analyze_question(self, question_data: Dict[str, Any]) -> LangfuseV3Analysis:
        """使用Langfuse v3装饰器的分析流程"""
        start_time = datetime.now()
        
        # 通过上下文设置追踪信息
        langfuse_context.update_current_trace(
            name="e2e-search-analysis",
            input={
                "question_id": question_data['id'],
                "question": question_data['question'],
                "category": question_data['category']
            },
            metadata={
                "analysis_type": "flash_search",
                "has_evaluation": "verify" in question_data
            },
            tags=["e2e-analysis", "flash-search", question_data['category']],
            user_id="search-analyzer",
            session_id=f"analysis-{datetime.now().strftime('%Y%m%d')}"
        )
        
        analysis = LangfuseV3Analysis(
            question_id=question_data['id'],
            question=question_data['question'],
            category=question_data['category']
        )
        
        logger.info(f"\n{'='*60}")
        logger.info(f"开始分析: {question_data['id']}")
        logger.info(f"问题: {question_data['question'][:100]}...")
        
        try:
            # 执行各阶段
            await self._serp_search(question_data, analysis)
            await self._url_selection(question_data, analysis)
            await self._content_fetching(question_data, analysis)
            await self._answer_generation(question_data, analysis)
            
            # 评价（如果有）
            if 'verify' in question_data and 'evaluation_dimensions' in question_data['verify']:
                await self._evaluate_answer(question_data, analysis)
            
            analysis.success = True
            
            # 更新追踪输出
            langfuse_context.update_current_trace(
                output={
                    "success": True,
                    "stages_completed": list(analysis.stages_data.keys()),
                    "overall_score": analysis.evaluation_data.get('overall_score', 0) if analysis.evaluation_data else None
                }
            )
            
        except Exception as e:
            logger.error(f"处理出错: {str(e)}")
            analysis.success = False
            
            langfuse_context.update_current_trace(
                output={"success": False, "error": str(e)},
                level="ERROR",
                status_message=str(e)
            )
        
        finally:
            analysis.total_duration = (datetime.now() - start_time).total_seconds()
            
            # 获取trace URL
            try:
                # 在v3中，我们需要通过flush获取trace信息
                self.langfuse.flush()
                # trace URL可能需要从返回的trace对象中获取
                # analysis.trace_url = ...  # 具体实现取决于v3 API
            except:
                pass
            
            logger.info(f"分析完成，总耗时: {analysis.total_duration:.1f}秒")
            logger.info(f"{'='*60}\n")
        
        return analysis
    
    @observe(name="serp-search")
    async def _serp_search(self, question_data: Dict[str, Any], analysis: LangfuseV3Analysis):
        """SERP搜索阶段"""
        start = datetime.now()
        
        langfuse_context.update_current_observation(
            input={"query": question_data['question']}
        )
        
        # 这里保存搜索结果供后续使用
        self._search_results = await self.search_engine.search(question_data['question'])
        
        langfuse_context.update_current_observation(
            output={
                "result_count": len(self._search_results),
                "results_preview": [r.get("title", "") for r in self._search_results[:3]]
            }
        )
        
        analysis.stages_data['serp'] = {
            'result_count': len(self._search_results),
            'duration': (datetime.now() - start).total_seconds()
        }
        
        if not self._search_results:
            raise Exception("SERP搜索未返回结果")
    
    @observe(name="url-selection", capture_input=False, capture_output=False)
    async def _url_selection(self, question_data: Dict[str, Any], analysis: LangfuseV3Analysis):
        """URL选择阶段"""
        start = datetime.now()
        
        # 手动记录输入输出（避免大量数据）
        langfuse_context.update_current_observation(
            input={
                "question": question_data['question'],
                "candidate_count": len(self._search_results)
            }
        )
        
        # 执行选择
        self._selected_urls = await self.search_engine.select(
            question_data['question'], 
            self._search_results
        )
        
        langfuse_context.update_current_observation(
            output={
                "selected_count": len(self._selected_urls),
                "selected_urls": self._selected_urls
            }
        )
        
        analysis.stages_data['select'] = {
            'selected_count': len(self._selected_urls),
            'duration': (datetime.now() - start).total_seconds()
        }
        
        if not self._selected_urls:
            raise Exception("未能选择到有效的URL")
    
    @observe(name="content-fetching")
    async def _content_fetching(self, question_data: Dict[str, Any], analysis: LangfuseV3Analysis):
        """内容抓取阶段"""
        start = datetime.now()
        
        langfuse_context.update_current_observation(
            input={"urls_to_fetch": self._selected_urls}
        )
        
        self._crawl_results = await self.search_engine.crawl(
            self._selected_urls, 
            self._search_results
        )
        
        successful = sum(1 for r in self._crawl_results if not r.get("is_fallback"))
        fallbacks = sum(1 for r in self._crawl_results if r.get("is_fallback"))
        
        langfuse_context.update_current_observation(
            output={
                "fetched_count": len(self._crawl_results),
                "successful_crawls": successful,
                "fallback_snippets": fallbacks
            }
        )
        
        analysis.stages_data['fetch'] = {
            'fetched_count': len(self._crawl_results),
            'successful_crawls': successful,
            'duration': (datetime.now() - start).total_seconds()
        }
        
        if not self._crawl_results:
            raise Exception("未能获取到有效内容")
    
    @observe(name="answer-generation")
    async def _answer_generation(self, question_data: Dict[str, Any], analysis: LangfuseV3Analysis):
        """答案生成阶段"""
        start = datetime.now()
        
        langfuse_context.update_current_observation(
            input={
                "question": question_data['question'],
                "sources_count": len(self._crawl_results)
            }
        )
        
        self._final_answer = await self.search_engine.synthesize(
            question_data['question'], 
            self._crawl_results
        )
        
        langfuse_context.update_current_observation(
            output={
                "answer_length": len(self._final_answer),
                "answer_preview": self._final_answer[:200] + "..." if len(self._final_answer) > 200 else self._final_answer
            }
        )
        
        analysis.stages_data['generate'] = {
            'answer_length': len(self._final_answer),
            'duration': (datetime.now() - start).total_seconds()
        }
    
    @observe(name="answer-evaluation")
    async def _evaluate_answer(self, question_data: Dict[str, Any], analysis: LangfuseV3Analysis):
        """答案评价阶段"""
        dimensions = question_data['verify']['evaluation_dimensions']
        
        langfuse_context.update_current_observation(
            input={"dimensions_count": len(dimensions)}
        )
        
        # 构建并执行评价
        evaluation_prompt = self._build_evaluation_prompt(
            question_data['question'],
            self._final_answer,
            dimensions,
            self._crawl_results
        )
        
        evaluation_response = await self.llm_client.agenerate(
            messages=[{"role": "user", "content": evaluation_prompt}],
            model="claude-3-5-sonnet-20241022",
            temperature=0.1
        )
        
        # 解析结果
        evaluation_text = evaluation_response.choices[0].message.content
        evaluation_data = self._parse_evaluation_response(evaluation_text)
        
        # 计算总分
        if evaluation_data.get('scores'):
            evaluation_data['overall_score'] = sum(evaluation_data['scores'].values()) / len(evaluation_data['scores'])
        
        analysis.evaluation_data = evaluation_data
        
        langfuse_context.update_current_observation(
            output={
                "overall_score": evaluation_data.get('overall_score', 0),
                "dimension_scores": evaluation_data.get('scores', {})
            }
        )
        
        # 记录评分
        for dim_name, score in evaluation_data.get('scores', {}).items():
            langfuse_context.score_current_trace(
                name=f"eval-{dim_name}",
                value=score / 5.0,
                comment=evaluation_data.get('comments', {}).get(dim_name, '')
            )
        
        # 总体评分
        if evaluation_data.get('overall_score'):
            langfuse_context.score_current_trace(
                name="overall-quality",
                value=evaluation_data['overall_score'] / 5.0,
                comment="综合各维度的平均得分"
            )
    
    def _build_evaluation_prompt(self, question: str, answer: str, dimensions: Dict[str, Any],
                                sources: List[Dict[str, Any]]) -> str:
        """构建评价prompt"""
        prompt = f"""你是一个专业的答案质量评估专家。请根据以下评价维度对搜索引擎生成的答案进行评分。

问题：{question}

生成的答案：
{answer}

搜索上下文：
- 使用的信息源数量：{len(sources)}

评价维度：
"""
        
        for dim_name, dim_info in dimensions.items():
            prompt += f"\n\n{dim_name}：\n"
            prompt += f"描述：{dim_info['description']}\n"
            prompt += "评分标准：\n"
            for score, criteria in dim_info['scoring_criteria'].items():
                prompt += f"  {score}：{criteria}\n"
        
        prompt += """

请为每个维度打分（1-5分），并提供简短的评价理由。

输出格式要求：
1. 必须严格按照JSON格式输出
2. 示例：
{
    "scores": {"维度1": 4, "维度2": 3.5},
    "comments": {"维度1": "理由", "维度2": "理由"}
}
"""
        return prompt
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """解析评价响应"""
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return {}
        return {}


async def main():
    """主函数"""
    # 检查环境变量
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        logger.error("请设置LANGFUSE_PUBLIC_KEY和LANGFUSE_SECRET_KEY环境变量")
        logger.info("在.env文件中添加：")
        logger.info("LANGFUSE_PUBLIC_KEY=pk-lf-xxx")
        logger.info("LANGFUSE_SECRET_KEY=sk-lf-xxx")
        return
    
    # 读取问题
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/diverse_questions_50.json"
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # 创建分析器
    analyzer = LangfuseV3Analyzer()
    
    # 分析第一个问题
    question = questions[0]
    result = await analyzer.analyze_question(question)
    
    logger.info(f"\n分析完成！")
    logger.info(f"- 问题ID: {result.question_id}")
    logger.info(f"- 成功: {result.success}")
    logger.info(f"- 总耗时: {result.total_duration:.1f}秒")
    
    if result.evaluation_data:
        logger.info(f"- 总体评分: {result.evaluation_data.get('overall_score', 0):.2f}/5")
    
    # 确保所有事件都被发送
    analyzer.langfuse.flush()
    
    logger.info("\n请访问Langfuse Dashboard查看完整追踪信息")


if __name__ == "__main__":
    asyncio.run(main())