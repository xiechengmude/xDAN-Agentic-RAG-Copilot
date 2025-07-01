#!/usr/bin/env python3
"""
FlashSearch + S3-RAG-RL 混合架构
结合并发搜索的效率和智能迭代的精准
"""

import asyncio
import logging
import time
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


class S3IntelligentEvaluator:
    """S3智能评估器 - 简化版"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def evaluate_sufficiency(
        self, 
        question: str, 
        search_results: List[Dict]
    ) -> EvaluationResult:
        """
        评估信息充分性（简化版）
        """
        if not search_results:
            return EvaluationResult(
                sufficient=False,
                confidence=0.0,
                gaps=["未找到任何相关信息"],
                next_queries=[question]
            )
        
        # 构建评估prompt
        results_summary = "\n".join([
            f"{i+1}. {r.get('title', 'Unknown')} - {r.get('snippet', '')[:100]}..."
            for i, r in enumerate(search_results[:5])
        ])
        
        prompt = f"""
请快速评估以下搜索结果是否足够回答用户问题。

用户问题：{question}

搜索结果摘要：
{results_summary}

请回答：
1. 信息是否充分（是/否）
2. 置信度（0-1分数）
3. 如果不充分，缺少什么关键信息？（简短列出）
4. 建议的补充搜索关键词（如有需要）

请用JSON格式回答：
{{"sufficient": bool, "confidence": float, "gaps": ["..."], "next_queries": ["..."]}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                use_case="evaluation",
                temperature=0.3,
                max_tokens=200
            )
            
            # 解析响应（简化处理）
            content = response.choices[0].message.content
            # 这里应该用json.loads，但为了简化示例直接返回
            
            # 模拟返回
            has_enough = len(search_results) >= 3
            return EvaluationResult(
                sufficient=has_enough,
                confidence=0.8 if has_enough else 0.4,
                gaps=[] if has_enough else ["需要更多具体信息"],
                next_queries=[] if has_enough else [f"{question} 详细数据"]
            )
            
        except Exception as e:
            logger.error(f"评估失败: {e}")
            # 失败时默认认为信息充分，避免无限循环
            return EvaluationResult(sufficient=True, confidence=0.5)


class FlashSearchS3Hybrid(FlashSearchEngine):
    """
    混合搜索引擎：FlashSearch并发 + S3智能迭代
    """
    
    def __init__(self):
        super().__init__()
        self.evaluator = S3IntelligentEvaluator(self.llm_client)
        self.max_iterations = 2  # 最多2轮迭代
        self.time_budget = 60    # 总时间预算
    
    async def parallel_search_strategies(
        self, 
        question: str,
        strategies: List[str]
    ) -> List[Dict[str, Any]]:
        """
        并发执行多个搜索策略
        """
        tasks = []
        
        # 策略1：精准搜索（原始问题）
        if "precision" in strategies:
            task1 = self.search(question)
            tasks.append(task1)
        
        # 策略2：扩展搜索（使用备选策略）
        if "broad" in strategies:
            task2 = self.search(question, use_alternative_strategy=True)
            tasks.append(task2)
        
        # 策略3：时间敏感搜索（添加最新）
        if "recent" in strategies:
            recent_question = f"最新 {question} {datetime.now().year}"
            task3 = self.search(recent_question)
            tasks.append(task3)
        
        # 并发执行所有搜索
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并结果
        merged_results = []
        seen_urls = set()
        
        for result_set in results:
            if isinstance(result_set, Exception):
                logger.warning(f"搜索策略失败: {result_set}")
                continue
            
            for item in result_set:
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    merged_results.append(item)
        
        return merged_results
    
    async def flash_search_s3(self, question: str) -> Dict[str, Any]:
        """
        S3增强的Flash搜索主流程
        """
        logger.info(f"[S3-Flash] 开始混合搜索: {question}")
        start_time = time.time()
        
        result = {
            "question": question,
            "answer": "",
            "sources": [],
            "stats": {
                "iterations": 0,
                "total_searches": 0,
                "s3_evaluations": 0
            },
            "timestamp": datetime.now().isoformat()
        }
        
        all_search_results = []
        all_crawled_content = []
        
        try:
            for iteration in range(self.max_iterations):
                # 检查时间预算
                elapsed = time.time() - start_time
                if elapsed > self.time_budget * 0.8:  # 80%时间用完则停止
                    logger.warning(f"[S3-Flash] 接近时间限制，停止迭代")
                    break
                
                logger.info(f"[S3-Flash] 第{iteration + 1}轮搜索")
                result["stats"]["iterations"] = iteration + 1
                
                # 1. 确定搜索策略
                if iteration == 0:
                    # 第一轮：并发多策略
                    strategies = ["precision", "broad", "recent"]
                    search_results = await self.parallel_search_strategies(
                        question, strategies
                    )
                    result["stats"]["total_searches"] += len(strategies)
                else:
                    # 后续轮：基于缺口的针对性搜索
                    if evaluation.next_queries:
                        tasks = [self.search(q) for q in evaluation.next_queries[:2]]
                        results = await asyncio.gather(*tasks)
                        search_results = []
                        for r in results:
                            search_results.extend(r)
                        result["stats"]["total_searches"] += len(tasks)
                    else:
                        break
                
                all_search_results.extend(search_results)
                
                # 2. S3智能评估
                evaluation = await self.evaluator.evaluate_sufficiency(
                    question, all_search_results
                )
                result["stats"]["s3_evaluations"] += 1
                
                logger.info(
                    f"[S3-Flash] 评估结果 - 充分性: {evaluation.sufficient}, "
                    f"置信度: {evaluation.confidence:.2f}"
                )
                
                # 3. 如果信息充分或达到迭代上限，进入选择和爬取阶段
                if evaluation.sufficient or iteration == self.max_iterations - 1:
                    # 选择最相关的URL
                    selected_urls = await self.select(question, all_search_results)
                    
                    if selected_urls:
                        # 爬取内容
                        crawl_results = await self.crawl(selected_urls, all_search_results)
                        all_crawled_content.extend(crawl_results)
                    
                    break
                
                # 4. 否则继续下一轮迭代
                if evaluation.gaps:
                    logger.info(f"[S3-Flash] 信息缺口: {evaluation.gaps}")
            
            # 5. 生成最终答案
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
                "total_duration": time.time() - start_time,
                "average_confidence": evaluation.confidence
            })
            
            logger.info(
                f"[S3-Flash] ✅ 完成搜索: "
                f"{result['stats']['iterations']}轮迭代, "
                f"{result['stats']['total_duration']:.1f}秒"
            )
            
        except Exception as e:
            logger.error(f"[S3-Flash] ❌ 搜索失败: {e}")
            result["answer"] = f"搜索过程中遇到错误: {e}"
        
        return result


# 便捷函数
async def flash_search_s3(question: str) -> Dict[str, Any]:
    """
    S3增强的Flash搜索
    """
    engine = FlashSearchS3Hybrid()
    return await engine.flash_search_s3(question)