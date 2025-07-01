#!/usr/bin/env python3
"""
增强版评分系统：包含搜索控制决策
支持：维度评价 + 搜索决策 + 任务规划
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
from dotenv import load_dotenv
from dataclasses import dataclass

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

# 加载环境变量
load_dotenv()

# Langfuse v3 imports
from langfuse import Langfuse, observe

# FlashSearch相关导入
from src.core.flash_search_engine import FlashSearchEngine
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient
from src.core.time_aware_prompt import TimeAwarePrompt

logger = logging.getLogger(__name__)

@dataclass
class SearchDecision:
    """搜索决策结果"""
    need_next_round: bool
    confidence_score: float
    missing_aspects: List[str]
    search_tasks: List[Dict[str, Any]]
    reasoning: str

@dataclass
class EnhancedEvaluationResult:
    """增强版评估结果"""
    dimension_scores: Dict[str, float]
    dimension_details: Dict[str, str]
    overall_quality: float
    search_decision: SearchDecision
    summary: str

class EnhancedScoringSystem:
    """增强版评分系统：评分 + 搜索控制"""
    
    def __init__(self):
        self.llm_client = EnhancedLiteLLMClient()
        self.scoring_model = os.getenv("SCORING_MODEL", "deepseek-chat")
        self.time_aware = TimeAwarePrompt()
        
    def build_enhanced_evaluation_prompt(self, question: str, answer: str, 
                                       dimensions: Dict[str, Any], 
                                       search_round: int = 1) -> str:
        """构建增强版评估prompt，包含搜索决策"""
        
        # 获取时间感知信息
        time_info = self.time_aware.get_current_time_info()
        
        prompt = f"""请作为一个智能搜索质量评估专家，对以下搜索结果进行全面评估并做出搜索决策。

【时间上下文】
当前时间：{time_info['beijing_time']} ({time_info['weekday_cn']})
当前日期：{time_info['current_date']}
本周范围：{time_info['week_start']} 至 {time_info['week_end']}
本月范围：{time_info['month_start']} 至 {time_info['month_end']}
市场状态：{time_info['market_status']}

【原始问题】
{question}

【当前搜索轮次】第 {search_round} 轮

【生成的答案】
{answer}

【任务一：维度评分】
请根据以下维度进行评分（1-5分，1分最低，5分最高）：

"""
        
        for dim_name, dim_info in dimensions.items():
            prompt += f"\n{dim_name}："
            prompt += f"\n定义：{dim_info['description']}"
            prompt += f"\n评分标准："
            for score, criteria in dim_info['scoring_criteria'].items():
                prompt += f"\n  {score}：{criteria}"
            prompt += "\n"
        
        prompt += f"""
【任务二：搜索决策分析】
基于当前答案质量和时间上下文，判断是否需要进行下一轮搜索：

1. 分析当前答案的完整性和准确性
2. 识别缺失的关键信息或薄弱环节
3. 评估继续搜索的必要性和价值
4. 如果需要下一轮搜索，规划具体的搜索任务（考虑时间相关性）

【时间感知搜索策略】
- 对于市场相关问题，考虑当前市场状态和时间敏感性
- 搜索查询应包含最新的时间信息（如当前年份、季度、月份）
- 如果是实时性要求高的问题，优先搜索最新数据
- 考虑工作日vs周末、交易时间vs休市时间的数据可用性

【Google搜索关键词优化策略】
- 将完整问题拆解为3-8个核心关键词
- 优先使用行业术语和专业词汇
- 包含时间信息（如2025、最新、Q1等）
- 添加文档类型关键词（如报告、研究、数据等）
- 避免停用词和无意义连接词
- 结合中英文关键词提高覆盖率

【决策标准】
- 如果平均分≥4.0且所有维度≥3.0：通常不需要下一轮
- 如果平均分<3.0或有维度<2.0：强烈建议下一轮搜索
- 如果平均分3.0-4.0：根据具体缺失情况决定
- 特别注意：如果缺失时间敏感信息，即使分数较高也建议补充搜索

【输出格式】
请严格按照以下JSON格式输出：
{{
    "dimension_evaluation": {{
        "scores": {{
            "维度名称": 分数（1-5的数字）
        }},
        "details": {{
            "维度名称": "评分理由（20-50字）"
        }}
    }},
    "search_decision": {{
        "need_next_round": true/false,
        "confidence_score": 当前答案的整体置信度（0-1之间的小数）,
        "missing_aspects": ["缺失的关键信息1", "缺失的关键信息2"],
        "search_tasks": [
            {{
                "task_type": "补充搜索类型（如：数据补充、案例研究、专业观点等）",
                "search_query": "具体的搜索查询（必须包含时间信息，如2025年、最新、当前等）",
                "google_keywords": "针对Google优化的关键词组合（用空格分隔，如：订阅服务 市场规模 2025 报告）",
                "priority": "high/medium/low",
                "expected_content": "期望获得的内容类型",
                "time_sensitivity": "high/medium/low（时间敏感度）",
                "target_timeframe": "目标时间范围（如2025年Q1、2024年度、最新一个月等）"
            }}
        ],
        "reasoning": "是否进行下一轮搜索的详细理由（50-100字）"
    }},
    "summary": "整体评价和建议（50-100字）"
}}

注意：
1. 所有分数必须是1-5之间的数字
2. need_next_round必须是布尔值
3. confidence_score必须是0-1之间的小数
4. 如果不需要下一轮搜索，search_tasks可以为空数组
5. 输出必须是有效的JSON格式
"""
        
        return prompt

    async def enhanced_evaluate_answer(self, question: str, answer: str, 
                                     dimensions: Dict[str, Any],
                                     search_round: int = 1) -> EnhancedEvaluationResult:
        """执行增强版评估：维度评分 + 搜索决策"""
        
        # 构建增强版评估prompt
        prompt = self.build_enhanced_evaluation_prompt(question, answer, dimensions, search_round)
        
        try:
            # 调用LLM进行评估
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的搜索质量评估专家和搜索策略规划师。你需要既评估当前结果质量，又决定是否需要进一步搜索优化。"
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                model=self.scoring_model,
                temperature=0.1,
                max_tokens=2000,
                use_case="enhanced_evaluation"
            )
            
            # 解析LLM响应
            evaluation_text = response.choices[0].message.content
            result = self.parse_enhanced_evaluation(evaluation_text, dimensions)
            
            logger.info(f"增强评估完成 - 总体质量: {result.overall_quality:.2f}, 需要下一轮: {result.search_decision.need_next_round}")
            
            return result
            
        except Exception as e:
            logger.error(f"增强评估失败: {e}")
            # 返回保守的默认结果
            return self._create_fallback_result(dimensions)

    def parse_enhanced_evaluation(self, response_text: str, 
                                dimensions: Dict[str, Any]) -> EnhancedEvaluationResult:
        """解析增强版评估响应"""
        import re
        
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                
                # 解析维度评分
                dimension_scores = {}
                dimension_details = {}
                
                if 'dimension_evaluation' in data:
                    eval_data = data['dimension_evaluation']
                    
                    # 提取分数
                    if 'scores' in eval_data:
                        for dim_name in dimensions.keys():
                            if dim_name in eval_data['scores']:
                                score = float(eval_data['scores'][dim_name])
                                dimension_scores[dim_name] = max(1.0, min(5.0, score))
                            else:
                                dimension_scores[dim_name] = 3.0
                    
                    # 提取详情
                    if 'details' in eval_data:
                        dimension_details = eval_data['details']
                
                # 解析搜索决策
                search_decision = SearchDecision(
                    need_next_round=False,
                    confidence_score=0.5,
                    missing_aspects=[],
                    search_tasks=[],
                    reasoning="解析失败，使用默认值"
                )
                
                if 'search_decision' in data:
                    decision_data = data['search_decision']
                    search_decision = SearchDecision(
                        need_next_round=bool(decision_data.get('need_next_round', False)),
                        confidence_score=float(decision_data.get('confidence_score', 0.5)),
                        missing_aspects=decision_data.get('missing_aspects', []),
                        search_tasks=decision_data.get('search_tasks', []),
                        reasoning=decision_data.get('reasoning', '无详细理由')
                    )
                
                # 计算总体质量
                overall_quality = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 3.0
                
                # 获取总结
                summary = data.get('summary', '评估完成')
                
                return EnhancedEvaluationResult(
                    dimension_scores=dimension_scores,
                    dimension_details=dimension_details,
                    overall_quality=overall_quality,
                    search_decision=search_decision,
                    summary=summary
                )
                
        except Exception as e:
            logger.error(f"解析增强评估响应失败: {e}")
        
        # 如果解析失败，返回保守结果
        return self._create_fallback_result(dimensions)

    def _create_fallback_result(self, dimensions: Dict[str, Any]) -> EnhancedEvaluationResult:
        """创建兜底评估结果"""
        dimension_scores = {dim_name: 3.0 for dim_name in dimensions.keys()}
        dimension_details = {dim_name: "评估失败，使用默认分数" for dim_name in dimensions.keys()}
        
        search_decision = SearchDecision(
            need_next_round=True,
            confidence_score=0.3,
            missing_aspects=["评估系统异常"],
            search_tasks=[{
                "task_type": "重新搜索",
                "search_query": "重新执行原查询",
                "priority": "high",
                "expected_content": "更完整的信息"
            }],
            reasoning="评估系统异常，建议重新搜索以确保质量"
        )
        
        return EnhancedEvaluationResult(
            dimension_scores=dimension_scores,
            dimension_details=dimension_details,
            overall_quality=3.0,
            search_decision=search_decision,
            summary="评估系统异常，建议重新处理"
        )

class MultiRoundSearchEngine:
    """多轮搜索引擎：基于评分结果进行智能搜索"""
    
    def __init__(self):
        self.base_engine = FlashSearchEngine()
        self.scoring_system = EnhancedScoringSystem()
        self.max_rounds = int(os.getenv("MAX_SEARCH_ROUNDS", "3"))
        self.time_aware = TimeAwarePrompt()
        
    @observe(name="multi-round-search")
    async def intelligent_search(self, question: str, 
                                evaluation_dimensions: Dict[str, Any]) -> Dict[str, Any]:
        """智能多轮搜索主流程"""
        
        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST", "http://localhost:3000")
        )
        
        # 初始化结果
        search_history = []
        current_answer = ""
        round_number = 1
        
        while round_number <= self.max_rounds:
            logger.info(f"开始第 {round_number} 轮搜索")
            
            # 执行搜索
            if round_number == 1:
                # 第一轮：标准搜索
                search_result = await self.base_engine.flash_search(question)
            else:
                # 后续轮次：基于上轮评估结果的目标搜索
                search_tasks = search_history[-1]['evaluation_result'].search_decision.search_tasks
                search_result = await self._targeted_search(question, search_tasks)
            
            current_answer = search_result.get('answer', '')
            
            # 执行增强评估
            evaluation_result = await self.scoring_system.enhanced_evaluate_answer(
                question, current_answer, evaluation_dimensions, round_number
            )
            
            # 记录本轮结果
            round_data = {
                'round': round_number,
                'search_result': search_result,
                'evaluation_result': evaluation_result,
                'timestamp': datetime.now().isoformat()
            }
            search_history.append(round_data)
            
            # 更新Langfuse追踪
            langfuse_client.update_current_span(
                metadata={
                    'round': round_number,
                    'overall_quality': evaluation_result.overall_quality,
                    'need_next_round': evaluation_result.search_decision.need_next_round,
                    'confidence_score': evaluation_result.search_decision.confidence_score
                }
            )
            
            # 创建评分记录
            for dim_name, score in evaluation_result.dimension_scores.items():
                langfuse_client.score_current_trace(
                    name=f"round-{round_number}-{dim_name}",
                    value=score / 5.0,
                    comment=evaluation_result.dimension_details.get(dim_name, f"第{round_number}轮评分")
                )
            
            # 决策是否继续
            if not evaluation_result.search_decision.need_next_round:
                logger.info(f"评估系统决定停止搜索，当前质量满足要求")
                break
                
            if round_number >= self.max_rounds:
                logger.info(f"达到最大搜索轮次 {self.max_rounds}")
                break
                
            logger.info(f"评估系统建议继续搜索: {evaluation_result.search_decision.reasoning}")
            round_number += 1
        
        # 整理最终结果
        final_result = {
            'question': question,
            'final_answer': current_answer,
            'total_rounds': round_number,
            'search_history': search_history,
            'final_evaluation': search_history[-1]['evaluation_result'],
            'improvement_summary': self._analyze_improvement(search_history)
        }
        
        return final_result

    async def _targeted_search(self, original_question: str, 
                             search_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于评估结果的目标性搜索（集成时间感知和Google关键词优化）"""
        
        if not search_tasks:
            # 如果没有具体任务，执行原问题的重新搜索
            return await self.base_engine.flash_search(original_question)
        
        # 选择最高优先级的搜索任务
        high_priority_tasks = [task for task in search_tasks if task.get('priority') == 'high']
        target_task = high_priority_tasks[0] if high_priority_tasks else search_tasks[0]
        
        # 获取时间感知信息
        time_info = self.time_aware.get_current_time_info()
        
        # 优先使用Google关键词，如果没有则生成优化的关键词
        google_keywords = target_task.get('google_keywords', '')
        if google_keywords:
            # 使用预生成的Google关键词
            optimized_query = self._enhance_google_keywords_with_time(
                google_keywords, 
                target_task, 
                time_info
            )
        else:
            # 如果没有Google关键词，从search_query生成
            base_query = target_task.get('search_query', '')
            optimized_query = self._generate_google_keywords(base_query, target_task, time_info)
        
        logger.info(f"执行Google关键词优化搜索:")
        logger.info(f"  任务类型: {target_task.get('task_type')}")
        logger.info(f"  原始查询: {target_task.get('search_query', '')}")
        logger.info(f"  Google关键词: {optimized_query}")
        logger.info(f"  时间上下文: {time_info['current_date']} ({time_info['market_status']})")
        
        # 执行搜索
        return await self.base_engine.flash_search(optimized_query)
    
    def _enhance_query_with_time(self, base_query: str, task: Dict[str, Any], 
                               time_info: Dict[str, str]) -> str:
        """使用时间感知信息增强搜索查询"""
        
        # 基础查询
        enhanced_query = base_query
        
        # 获取任务的时间相关信息
        time_sensitivity = task.get('time_sensitivity', 'medium')
        target_timeframe = task.get('target_timeframe', '')
        
        # 根据时间敏感度添加时间信息
        if time_sensitivity == 'high':
            # 高时间敏感度：添加具体日期和最新标识
            if '最新' not in enhanced_query and '2025' not in enhanced_query:
                enhanced_query += f" {time_info['current_date']} 最新"
        elif time_sensitivity == 'medium':
            # 中等时间敏感度：添加当前年份
            if '2025' not in enhanced_query:
                enhanced_query += " 2025年"
        
        # 如果指定了目标时间范围，优先使用
        if target_timeframe:
            enhanced_query += f" {target_timeframe}"
        
        # 根据市场状态调整查询（针对金融/市场相关问题）
        if any(keyword in base_query.lower() for keyword in ['市场', '金融', '投资', '股票', '经济']):
            if time_info['market_status'] == '交易时间':
                enhanced_query += " 实时数据"
            elif time_info['market_status'] == '盘后时间':
                enhanced_query += " 最新收盘"
        
        # 移除重复的时间信息
        enhanced_query = self._deduplicate_time_terms(enhanced_query)
        
        return enhanced_query
    
    def _deduplicate_time_terms(self, query: str) -> str:
        """去重时间相关术语"""
        
        # 常见时间术语
        time_terms = ['2025年', '2025', '最新', '当前', '实时', '最近']
        
        # 去重逻辑
        seen_terms = set()
        words = query.split()
        deduplicated_words = []
        
        for word in words:
            # 检查是否是重复的时间术语
            is_duplicate = False
            for term in time_terms:
                if term in word and term in seen_terms:
                    is_duplicate = True
                    break
                elif term in word:
                    seen_terms.add(term)
            
            if not is_duplicate:
                deduplicated_words.append(word)
        
        return ' '.join(deduplicated_words)
    
    def _enhance_google_keywords_with_time(self, google_keywords: str, task: Dict[str, Any], 
                                         time_info: Dict[str, str]) -> str:
        """对已有Google关键词进行时间感知增强"""
        
        keywords = google_keywords.split()
        enhanced_keywords = []
        
        # 获取任务的时间相关信息
        time_sensitivity = task.get('time_sensitivity', 'medium')
        target_timeframe = task.get('target_timeframe', '')
        
        # 添加原有关键词
        enhanced_keywords.extend(keywords)
        
        # 根据时间敏感度添加时间关键词
        if time_sensitivity == 'high':
            if '2025' not in google_keywords:
                enhanced_keywords.append('2025')
            if '最新' not in google_keywords and 'latest' not in google_keywords.lower():
                enhanced_keywords.append('最新')
        elif time_sensitivity == 'medium':
            if '2025' not in google_keywords:
                enhanced_keywords.append('2025')
        
        # 如果指定了目标时间范围，优先使用
        if target_timeframe:
            # 提取时间范围中的关键词
            timeframe_keywords = self._extract_timeframe_keywords(target_timeframe)
            enhanced_keywords.extend(timeframe_keywords)
        
        # 针对特定类型添加搜索算子
        task_type = task.get('task_type', '')
        if task_type == '数据补充':
            enhanced_keywords.extend(['报告', 'report', 'market'])
        elif task_type == '案例研究':
            enhanced_keywords.extend(['案例', 'case', 'study'])
        elif task_type == '专业观点':
            enhanced_keywords.extend(['分析', 'analysis', 'expert'])
        
        # 去重并返回
        unique_keywords = list(dict.fromkeys(enhanced_keywords))  # 保持顺序去重
        return ' '.join(unique_keywords)
    
    def _generate_google_keywords(self, search_query: str, task: Dict[str, Any], 
                                time_info: Dict[str, str]) -> str:
        """从完整搜索查询生成Google优化的关键词"""
        
        # 从搜索查询中提取关键词
        keywords = self._extract_key_terms(search_query)
        
        # 使用时间感知增强
        enhanced_keywords = self._enhance_google_keywords_with_time(
            ' '.join(keywords), task, time_info
        )
        
        return enhanced_keywords
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """从查询中提取关键术语"""
        
        # 停用词列表
        stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '个', '上', '也', '很',
            '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '为', '来',
            '请', '为一家', '分析', '提供', '详细', '报告', '如何', '什么', '哪些', '怎么', '以及'
        }
        
        # 重要术语匹配模式
        important_terms = {
            '订阅': ['订阅', 'subscription'],
            '生活用品': ['生活用品', 'daily goods', 'consumer goods'],
            '配送': ['配送', 'delivery'],
            '市场规模': ['市场规模', 'market size'],
            '增长率': ['增长率', 'growth rate'],
            '金融科技': ['金融科技', 'fintech'],
            '竞争': ['竞争', 'competition'],
            '消费者': ['消费者', 'consumer'],
            '战略': ['战略', 'strategy'],
            '趋势': ['趋势', 'trend'],
            '投资': ['投资', 'investment'],
            '回报': ['回报', 'ROI', 'return']
        }
        
        keywords = []
        query_lower = query.lower()
        
        # 匹配重要术语
        for term_key, term_variants in important_terms.items():
            for variant in term_variants:
                if variant.lower() in query_lower:
                    keywords.append(term_key)
                    break
        
        # 提取数字和年份
        import re
        years = re.findall(r'\b(20\d{2})\b', query)
        keywords.extend(years)
        
        # 提取品牌名和专有名词（大写开头的词）
        proper_nouns = re.findall(r'\b[A-Z][a-zA-Z]+\b', query)
        keywords.extend(proper_nouns[:3])  # 最多3个专有名词
        
        return keywords[:8]  # 限制关键词数量
    
    def _extract_timeframe_keywords(self, timeframe: str) -> List[str]:
        """从时间范围中提取关键词"""
        
        keywords = []
        timeframe_lower = timeframe.lower()
        
        # 年份提取
        import re
        years = re.findall(r'\b(20\d{2})\b', timeframe)
        keywords.extend(years)
        
        # 季度提取
        if 'q1' in timeframe_lower or '第一季度' in timeframe_lower:
            keywords.append('Q1')
        elif 'q2' in timeframe_lower or '第二季度' in timeframe_lower:
            keywords.append('Q2')
        elif 'q3' in timeframe_lower or '第三季度' in timeframe_lower:
            keywords.append('Q3')
        elif 'q4' in timeframe_lower or '第四季度' in timeframe_lower:
            keywords.append('Q4')
        
        # 时间修饰词
        if '最新' in timeframe or 'latest' in timeframe_lower:
            keywords.append('最新')
        if '当前' in timeframe or 'current' in timeframe_lower:
            keywords.append('当前')
        
        return keywords

    def _analyze_improvement(self, search_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析多轮搜索的改进效果"""
        
        if len(search_history) < 2:
            return {"message": "单轮搜索，无改进分析"}
        
        first_round = search_history[0]['evaluation_result']
        final_round = search_history[-1]['evaluation_result']
        
        quality_improvement = final_round.overall_quality - first_round.overall_quality
        
        dimension_improvements = {}
        for dim_name in first_round.dimension_scores.keys():
            improvement = (final_round.dimension_scores.get(dim_name, 0) - 
                         first_round.dimension_scores.get(dim_name, 0))
            dimension_improvements[dim_name] = improvement
        
        return {
            'quality_improvement': quality_improvement,
            'dimension_improvements': dimension_improvements,
            'rounds_needed': len(search_history),
            'final_confidence': final_round.search_decision.confidence_score,
            'improvement_summary': f"总体质量提升 {quality_improvement:.2f} 分，经过 {len(search_history)} 轮搜索"
        }

async def demo_intelligent_search():
    """演示智能多轮搜索"""
    
    # 加载测试问题
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/diverse_questions_50_formatted.json"
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # 选择一个问题进行测试
    test_question = questions[0]
    
    # 初始化多轮搜索引擎
    search_engine = MultiRoundSearchEngine()
    
    # 执行智能搜索
    result = await search_engine.intelligent_search(
        question=test_question['question'],
        evaluation_dimensions=test_question['verify']['evaluation_dimensions']
    )
    
    # 保存结果
    output_file = f"intelligent_search_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"智能搜索完成，结果保存到: {output_file}")
    print(f"总轮次: {result['total_rounds']}")
    print(f"最终质量: {result['final_evaluation'].overall_quality:.2f}")
    print(f"质量改进: {result['improvement_summary']['improvement_summary']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demo_intelligent_search())