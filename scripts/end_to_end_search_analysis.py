#!/usr/bin/env python3
"""
端到端问题搜索分析脚本
使用FlashSearch引擎进行搜索，并根据evaluation_dimensions进行打分评价
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

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

from src.core.flash_search_engine import FlashSearchEngine
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class QuestionAnalysis:
    """问题分析结果"""
    question_id: str
    question: str
    category: str
    target: str
    search_result: Dict[str, Any] = field(default_factory=dict)
    evaluation_scores: Dict[str, float] = field(default_factory=dict)
    evaluation_comments: Dict[str, str] = field(default_factory=dict)
    overall_score: float = 0.0
    processing_time: float = 0.0
    error: Optional[str] = None


class EndToEndSearchAnalyzer:
    """端到端搜索分析器"""
    
    def __init__(self):
        self.search_engine = FlashSearchEngine()
        self.llm_client = EnhancedLiteLLMClient()
        
    async def analyze_question(self, question_data: Dict[str, Any]) -> QuestionAnalysis:
        """分析单个问题"""
        start_time = datetime.now()
        
        analysis = QuestionAnalysis(
            question_id=question_data['id'],
            question=question_data['question'],
            category=question_data['category'],
            target=question_data['target']
        )
        
        try:
            # 1. 使用FlashSearch进行搜索
            logger.info(f"正在搜索问题: {question_data['id']}")
            search_result = await self.search_engine.flash_search(question_data['question'])
            analysis.search_result = search_result
            
            # 2. 根据评价维度进行评分
            if 'verify' in question_data and 'evaluation_dimensions' in question_data['verify']:
                evaluation_dimensions = question_data['verify']['evaluation_dimensions']
                await self._evaluate_answer(analysis, evaluation_dimensions, search_result)
            
            # 计算处理时间
            analysis.processing_time = (datetime.now() - start_time).total_seconds()
            
        except Exception as e:
            logger.error(f"处理问题 {question_data['id']} 时出错: {str(e)}")
            analysis.error = str(e)
            
        return analysis
    
    async def _evaluate_answer(self, analysis: QuestionAnalysis, dimensions: Dict[str, Any], 
                              search_result: Dict[str, Any]) -> None:
        """根据评价维度对答案进行评分"""
        
        # 构建评价prompt
        evaluation_prompt = self._build_evaluation_prompt(
            question=analysis.question,
            answer=search_result.get('answer', ''),
            dimensions=dimensions,
            search_context=search_result
        )
        
        # 调用LLM进行评价
        evaluation_response = await self.llm_client.agenerate(
            messages=[{"role": "user", "content": evaluation_prompt}],
            model="claude-3-5-sonnet-20241022",
            temperature=0.1
        )
        
        # 解析评价结果
        try:
            evaluation_text = evaluation_response.choices[0].message.content
            evaluation_data = self._parse_evaluation_response(evaluation_text)
            
            analysis.evaluation_scores = evaluation_data.get('scores', {})
            analysis.evaluation_comments = evaluation_data.get('comments', {})
            
            # 计算总分
            if analysis.evaluation_scores:
                analysis.overall_score = sum(analysis.evaluation_scores.values()) / len(analysis.evaluation_scores)
                
        except Exception as e:
            logger.error(f"解析评价结果时出错: {str(e)}")
    
    def _build_evaluation_prompt(self, question: str, answer: str, dimensions: Dict[str, Any],
                                search_context: Dict[str, Any]) -> str:
        """构建评价prompt"""
        
        # 提取搜索上下文信息
        sources_used = len(search_context.get('sources', []))
        search_queries = search_context.get('search_queries', [])
        
        prompt = f"""你是一个专业的答案质量评估专家。请根据以下评价维度对搜索引擎生成的答案进行评分。

问题：{question}

生成的答案：
{answer}

搜索上下文：
- 使用的信息源数量：{sources_used}
- 搜索查询：{', '.join(search_queries)}

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
2. 包含scores对象（每个维度的分数）和comments对象（每个维度的评价理由）
3. 示例格式：
{
    "scores": {
        "维度1": 4,
        "维度2": 3.5
    },
    "comments": {
        "维度1": "答案准确全面，数据来源可靠",
        "维度2": "分析有一定深度，但缺少部分关键信息"
    }
}
"""
        
        return prompt
    
    def _parse_evaluation_response(self, response_text: str) -> Dict[str, Any]:
        """解析评价响应"""
        # 尝试提取JSON部分
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                logger.error("无法解析评价响应为JSON")
                return {}
        return {}
    
    async def analyze_questions_batch(self, questions_file: str, output_file: str, 
                                    limit: Optional[int] = None) -> List[QuestionAnalysis]:
        """批量分析问题"""
        
        # 读取问题文件
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        # 限制处理数量
        if limit:
            questions = questions[:limit]
        
        logger.info(f"开始处理 {len(questions)} 个问题")
        
        # 逐个处理问题（避免并发过高）
        results = []
        for i, question in enumerate(questions):
            logger.info(f"处理进度: {i+1}/{len(questions)}")
            result = await self.analyze_question(question)
            results.append(result)
            
            # 保存中间结果
            self._save_results(results, output_file)
        
        logger.info(f"所有问题处理完成，结果已保存到: {output_file}")
        return results
    
    def _save_results(self, results: List[QuestionAnalysis], output_file: str) -> None:
        """保存分析结果"""
        output_data = []
        
        for result in results:
            output_data.append({
                'question_id': result.question_id,
                'question': result.question,
                'category': result.category,
                'target': result.target,
                'answer': result.search_result.get('answer', ''),
                'sources_count': len(result.search_result.get('sources', [])),
                'evaluation_scores': result.evaluation_scores,
                'evaluation_comments': result.evaluation_comments,
                'overall_score': result.overall_score,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        # 创建输出目录
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存结果
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    def generate_report(self, results: List[QuestionAnalysis], report_file: str) -> None:
        """生成分析报告"""
        report = f"""# 端到端搜索分析报告

生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
分析问题数：{len(results)}

## 整体统计

- 成功处理：{len([r for r in results if not r.error])}
- 处理失败：{len([r for r in results if r.error])}
- 平均处理时间：{sum(r.processing_time for r in results) / len(results):.2f}秒
- 平均总分：{sum(r.overall_score for r in results if r.overall_score > 0) / len([r for r in results if r.overall_score > 0]):.2f}/5

## 分类统计

"""
        
        # 按类别统计
        category_stats = {}
        for result in results:
            if result.category not in category_stats:
                category_stats[result.category] = {
                    'count': 0,
                    'scores': [],
                    'errors': 0
                }
            
            category_stats[result.category]['count'] += 1
            if result.error:
                category_stats[result.category]['errors'] += 1
            elif result.overall_score > 0:
                category_stats[result.category]['scores'].append(result.overall_score)
        
        for category, stats in category_stats.items():
            avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
            report += f"\n### {category}\n"
            report += f"- 问题数：{stats['count']}\n"
            report += f"- 平均分：{avg_score:.2f}/5\n"
            report += f"- 错误数：{stats['errors']}\n"
        
        # 详细结果
        report += "\n## 详细结果\n\n"
        
        for result in results:
            report += f"### {result.question_id}\n"
            report += f"**问题**：{result.question}\n"
            report += f"**类别**：{result.category}\n"
            
            if result.error:
                report += f"**错误**：{result.error}\n"
            else:
                report += f"**总分**：{result.overall_score:.2f}/5\n"
                report += f"**处理时间**：{result.processing_time:.2f}秒\n"
                
                if result.evaluation_scores:
                    report += "\n**各维度得分**：\n"
                    for dim, score in result.evaluation_scores.items():
                        comment = result.evaluation_comments.get(dim, '')
                        report += f"- {dim}：{score}/5 - {comment}\n"
            
            report += "\n---\n\n"
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"分析报告已生成：{report_file}")


async def main():
    """主函数"""
    # 配置文件路径
    questions_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/search/diverse_questions_50.json"
    output_dir = "/Users/gump_m2/CascadeProjects/ragflow-api-client/analysis_results"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"{output_dir}/search_analysis_{timestamp}.json"
    report_file = f"{output_dir}/search_report_{timestamp}.md"
    
    # 创建分析器
    analyzer = EndToEndSearchAnalyzer()
    
    # 执行分析（先测试1个问题）
    results = await analyzer.analyze_questions_batch(
        questions_file=questions_file,
        output_file=output_file,
        limit=1  # 先测试1个问题，可以修改为None处理全部
    )
    
    # 生成报告
    analyzer.generate_report(results, report_file)
    
    print(f"\n分析完成！")
    print(f"结果文件：{output_file}")
    print(f"分析报告：{report_file}")


if __name__ == "__main__":
    asyncio.run(main())