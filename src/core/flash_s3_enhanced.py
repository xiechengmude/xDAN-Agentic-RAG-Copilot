#!/usr/bin/env python3
"""
FlashSearch + S3-RAG-RL 增强版
集成原版S3 Agent的智能评估能力
"""

import asyncio
import logging
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .flash_search_engine import FlashSearchEngine
from .search_strategy import search_strategy

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """S3评估结果"""
    sufficient: bool
    confidence: float
    gaps: List[str] = None
    next_queries: List[str] = None
    important_docs: List[int] = None


class S3AgentEvaluator:
    """
    S3智能评估器 - 集成原版S3-RAG-RL Agent能力
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        # 原版S3 Agent的系统提示词（核心部分）
        self.system_prompt = """You are an intelligent search assistant specialized in RAG workflows.

## Core Responsibilities:
1. **Evaluate Information Sufficiency**: Assess if current search results contain enough relevant information to answer the user's question comprehensively.
2. **Iterative Search Refinement**: If information is insufficient, formulate targeted search queries to fill knowledge gaps.
3. **Document Selection**: Identify the most relevant documents (up to 3) that directly address the user's query.

## Decision Process:
1. **Initial Assessment**: Review the provided search results against the user's question
2. **Gap Analysis**: Identify missing information or aspects not covered
3. **Search Strategy**: Formulate precise queries to obtain missing information
4. **Relevance Ranking**: Select documents that best answer the question

## Thinking Process (使用<thinking>标签展示推理过程):
1. 理解用户意图和问题类型
2. 评估当前信息的完整性和准确性
3. 识别信息缺口和搜索优先级
4. 制定搜索策略或选择最佳文档

Remember: Quality over quantity - 优选3个高相关文档而非多个边缘相关"""
    
    async def evaluate_with_s3_agent(
        self, 
        question: str, 
        search_results: List[Dict],
        iteration: int = 0
    ) -> EvaluationResult:
        """
        使用S3 Agent方法评估信息充分性
        """
        if not search_results:
            return EvaluationResult(
                sufficient=False,
                confidence=0.0,
                gaps=["未找到任何相关信息"],
                next_queries=[question],
                important_docs=[]
            )
        
        # 构建结果摘要（包含更多细节）
        results_detail = []
        for i, result in enumerate(search_results[:10]):
            results_detail.append({
                "id": i + 1,
                "title": result.get('title', 'Unknown'),
                "url": result.get('url', ''),
                "snippet": result.get('snippet', '')[:200],
                "source": result.get('source', 'unknown')
            })
        
        # 构建S3 Agent风格的评估prompt
        user_prompt = f"""
Current search iteration: {iteration + 1}
User question: {question}

Available search results:
{json.dumps(results_detail, ensure_ascii=False, indent=2)}

Please evaluate:
<thinking>
1. 用户问题分析：
   - 问题类型：{self._analyze_question_type(question)}
   - 关键信息需求：{self._extract_key_requirements(question)}

2. 当前信息评估：
   - 已覆盖的方面
   - 缺失的关键信息
   - 信息质量和可靠性

3. 决策：
   - 是否需要更多搜索
   - 如需搜索，应该查找什么
</thinking>

Based on your analysis, provide:
1. <search_complete>true/false</search_complete>
2. <important_info>[最相关的1-3个文档ID]</important_info>
3. If search is not complete:
   - <query>{{"query": "targeted search query"}}</query> (可以多个)
   - Confidence score (0-1)
   - Key gaps identified
"""

        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm_client.chat_completion(
                messages=messages,
                use_case="s3_evaluation",
                temperature=0.3,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # 解析S3 Agent响应
            return self._parse_s3_response(content, search_results)
            
        except Exception as e:
            logger.error(f"S3评估失败: {e}")
            # 失败时的降级处理
            return self._fallback_evaluation(search_results)
    
    def _analyze_question_type(self, question: str) -> str:
        """分析问题类型"""
        if any(kw in question for kw in ['是什么', '定义', '概念']):
            return "定义型"
        elif any(kw in question for kw in ['如何', '怎么', '步骤']):
            return "操作型"
        elif any(kw in question for kw in ['为什么', '原因', '因为']):
            return "原因型"
        elif any(kw in question for kw in ['对比', '区别', '相同']):
            return "比较型"
        elif any(kw in question for kw in ['分析', '评估', '影响']):
            return "分析型"
        else:
            return "信息查询型"
    
    def _extract_key_requirements(self, question: str) -> str:
        """提取关键信息需求"""
        # 简化实现，实际应该更智能
        keywords = []
        if '财报' in question:
            keywords.extend(['营收', '利润', '增长率'])
        if '技术' in question:
            keywords.extend(['实现方法', '优势', '应用场景'])
        if '市场' in question:
            keywords.extend(['规模', '趋势', '竞争'])
        
        return ', '.join(keywords) if keywords else '相关具体信息'
    
    def _parse_s3_response(self, content: str, search_results: List[Dict]) -> EvaluationResult:
        """解析S3 Agent的响应"""
        try:
            # 提取关键标签内容
            import re
            
            # 搜索是否完成
            complete_match = re.search(r'<search_complete>(.*?)</search_complete>', content, re.IGNORECASE)
            is_complete = complete_match and complete_match.group(1).lower().strip() == 'true'
            
            # 重要文档
            docs_match = re.search(r'<important_info>\[(.*?)\]</important_info>', content)
            important_docs = []
            if docs_match:
                try:
                    docs_str = docs_match.group(1)
                    important_docs = [int(x.strip()) for x in docs_str.split(',') if x.strip()]
                except:
                    pass
            
            # 新查询
            queries = []
            query_matches = re.findall(r'<query>(.*?)</query>', content, re.DOTALL)
            for query_match in query_matches:
                try:
                    query_data = json.loads(query_match)
                    if 'query' in query_data:
                        queries.append(query_data['query'])
                except:
                    pass
            
            # 识别缺口（从thinking部分提取）
            gaps = []
            if '缺失' in content:
                gap_section = content.split('缺失')[1].split('\n')[0]
                gaps.append(gap_section.strip())
            
            # 计算置信度
            confidence = 0.9 if is_complete else 0.4
            if important_docs and len(important_docs) >= 2:
                confidence += 0.1
            
            return EvaluationResult(
                sufficient=is_complete,
                confidence=confidence,
                gaps=gaps if not is_complete else [],
                next_queries=queries,
                important_docs=important_docs
            )
            
        except Exception as e:
            logger.error(f"解析S3响应失败: {e}")
            return self._fallback_evaluation(search_results)
    
    def _fallback_evaluation(self, search_results: List[Dict]) -> EvaluationResult:
        """降级评估策略"""
        has_enough = len(search_results) >= 4
        return EvaluationResult(
            sufficient=has_enough,
            confidence=0.7 if has_enough else 0.3,
            gaps=[] if has_enough else ["需要更多相关信息"],
            next_queries=[],
            important_docs=list(range(1, min(4, len(search_results) + 1)))
        )


class FlashS3Enhanced(FlashSearchEngine):
    """
    增强版混合搜索引擎：FlashSearch并发 + S3智能迭代 + 原版Agent能力
    """
    
    def __init__(self):
        super().__init__()
        self.s3_evaluator = S3AgentEvaluator(self.llm_client)
        self.max_iterations = 3  # 支持更多轮迭代
        self.time_budget = 60    # 总时间预算
    
    async def parallel_search_strategies(
        self, 
        question: str,
        strategies: List[str],
        previous_results: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        并发执行多个搜索策略（增强版）
        """
        tasks = []
        
        # 根据策略类型创建不同的搜索任务
        for strategy in strategies:
            if strategy == "precision":
                # 精准搜索
                task = self.search(question)
            elif strategy == "broad":
                # 扩展搜索
                task = self.search(question, use_alternative_strategy=True)
            elif strategy == "recent":
                # 时间敏感搜索
                recent_question = f"最新 {question} {datetime.now().year}"
                task = self.search(recent_question)
            elif strategy == "deep":
                # 深度搜索（添加专业术语）
                deep_question = self._enhance_with_domain_terms(question)
                task = self.search(deep_question)
            elif strategy.startswith("gap:"):
                # 缺口导向搜索
                gap_query = strategy.replace("gap:", "").strip()
                task = self.search(gap_query)
            else:
                continue
            
            tasks.append(task)
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 智能合并结果
        return self._smart_merge_results(results, previous_results)
    
    def _enhance_with_domain_terms(self, question: str) -> str:
        """添加领域专业术语增强搜索"""
        # 简化实现，实际应该基于领域知识库
        enhancements = {
            '财报': '财务报表 年报 季报 financial report earnings',
            '技术': 'documentation technical guide implementation',
            '市场': 'market analysis industry report trend forecast'
        }
        
        enhanced = question
        for key, terms in enhancements.items():
            if key in question:
                enhanced = f"{question} {terms}"
                break
        
        return enhanced
    
    def _smart_merge_results(
        self, 
        new_results: List[List[Dict]], 
        previous_results: List[Dict] = None
    ) -> List[Dict]:
        """智能合并搜索结果，避免重复，保持多样性"""
        merged = []
        seen_urls = set()
        seen_titles = set()
        
        # 先添加之前的结果
        if previous_results:
            for item in previous_results:
                url = item.get('url', '')
                title = item.get('title', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    seen_titles.add(title.lower())
                    merged.append(item)
        
        # 添加新结果
        for result_set in new_results:
            if isinstance(result_set, Exception):
                logger.warning(f"搜索策略失败: {result_set}")
                continue
            
            for item in result_set:
                url = item.get('url', '')
                title = item.get('title', '').lower()
                
                # 智能去重：URL完全相同或标题高度相似
                if url and url not in seen_urls:
                    is_duplicate = False
                    for seen_title in seen_titles:
                        if self._title_similarity(title, seen_title) > 0.8:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        seen_urls.add(url)
                        seen_titles.add(title)
                        merged.append(item)
        
        return merged
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """计算标题相似度（简化版）"""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    async def flash_s3_enhanced(self, question: str) -> Dict[str, Any]:
        """
        增强版S3搜索主流程
        """
        logger.info(f"[S3-Enhanced] 开始增强搜索: {question}")
        start_time = time.time()
        
        result = {
            "question": question,
            "answer": "",
            "sources": [],
            "stats": {
                "iterations": 0,
                "total_searches": 0,
                "s3_evaluations": 0,
                "search_strategies_used": []
            },
            "timestamp": datetime.now().isoformat()
        }
        
        all_search_results = []
        all_crawled_content = []
        
        try:
            for iteration in range(self.max_iterations):
                # 时间检查
                elapsed = time.time() - start_time
                if elapsed > self.time_budget * 0.85:
                    logger.warning(f"[S3-Enhanced] 接近时间限制，停止迭代")
                    break
                
                logger.info(f"[S3-Enhanced] 第{iteration + 1}轮搜索")
                result["stats"]["iterations"] = iteration + 1
                
                # 1. 确定搜索策略
                if iteration == 0:
                    # 第一轮：基础策略组合
                    strategies = ["precision", "broad", "recent"]
                    result["stats"]["search_strategies_used"].extend(strategies)
                else:
                    # 后续轮：基于S3评估的针对性策略
                    strategies = []
                    if evaluation.next_queries:
                        for query in evaluation.next_queries[:2]:
                            strategies.append(f"gap:{query}")
                    if not strategies:
                        strategies = ["deep"]  # 默认深度搜索
                    result["stats"]["search_strategies_used"].extend(strategies)
                
                # 2. 并发搜索
                search_results = await self.parallel_search_strategies(
                    question, strategies, all_search_results
                )
                result["stats"]["total_searches"] += len(strategies)
                
                # 更新总结果集
                all_search_results = search_results
                
                # 3. S3智能评估
                evaluation = await self.s3_evaluator.evaluate_with_s3_agent(
                    question, all_search_results, iteration
                )
                result["stats"]["s3_evaluations"] += 1
                
                logger.info(
                    f"[S3-Enhanced] 评估结果 - 充分性: {evaluation.sufficient}, "
                    f"置信度: {evaluation.confidence:.2f}, "
                    f"重要文档: {evaluation.important_docs}"
                )
                
                # 4. 判断是否继续
                if evaluation.sufficient or iteration == self.max_iterations - 1:
                    # 选择最相关的URL
                    if evaluation.important_docs:
                        # 使用S3推荐的文档
                        selected_urls = []
                        for doc_id in evaluation.important_docs:
                            if 0 < doc_id <= len(all_search_results):
                                url = all_search_results[doc_id - 1].get('url')
                                if url:
                                    selected_urls.append(url)
                    else:
                        # 降级到原始选择方法
                        selected_urls = await self.select(question, all_search_results)
                    
                    if selected_urls:
                        # 爬取内容
                        crawl_results = await self.crawl(selected_urls, all_search_results)
                        all_crawled_content.extend(crawl_results)
                    
                    break
                
                # 5. 记录缺口信息
                if evaluation.gaps:
                    logger.info(f"[S3-Enhanced] 信息缺口: {evaluation.gaps}")
            
            # 6. 生成最终答案
            if all_crawled_content:
                final_answer = await self.synthesize(question, all_crawled_content)
                result["answer"] = final_answer
                result["sources"] = all_crawled_content
            else:
                result["answer"] = "抱歉，未能获取到足够的信息来回答您的问题。"
            
            # 统计信息
            result["stats"].update({
                "search_results": len(all_search_results),
                "crawled_sources": len(all_crawled_content),
                "successful_crawls": sum(1 for r in all_crawled_content if not r.get("is_fallback")),
                "total_duration": time.time() - start_time,
                "final_confidence": evaluation.confidence
            })
            
            logger.info(
                f"[S3-Enhanced] ✅ 完成搜索: "
                f"{result['stats']['iterations']}轮迭代, "
                f"{result['stats']['total_duration']:.1f}秒, "
                f"置信度: {result['stats']['final_confidence']:.2f}"
            )
            
        except Exception as e:
            logger.error(f"[S3-Enhanced] ❌ 搜索失败: {e}")
            result["answer"] = f"搜索过程中遇到错误: {e}"
        
        return result


# 便捷函数
async def flash_s3_enhanced(question: str) -> Dict[str, Any]:
    """
    增强版S3搜索
    """
    engine = FlashS3Enhanced()
    return await engine.flash_s3_enhanced(question)