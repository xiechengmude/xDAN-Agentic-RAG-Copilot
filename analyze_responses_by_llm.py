#!/usr/bin/env python3

"""
使用LLM深度分析三个版本的响应质量
完全基于LLM判断，自定义评估维度
"""

import json
import asyncio
from datetime import datetime
import sys
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

class LLMResponseAnalyzer:
    def __init__(self):
        self.client = EnhancedLiteLLMClient()
        self.analysis_prompt = """你是一个专业的AI响应质量评估专家。请分析以下AI响应，并从以下维度进行评分（每个维度0-10分）：

1. **信息准确性**：响应内容是否准确、可靠
2. **逻辑严密性**：推理过程是否清晰、论证是否充分
3. **实用价值**：对用户问题的实际帮助程度
4. **创新思维**：是否有独特见解或创新方法
5. **交互友好度**：表达是否清晰、易于理解
6. **完整性**：是否全面回答了用户问题
7. **专业深度**：展现的专业知识水平
8. **效率优化**：是否简洁高效，避免冗余

问题：{question}

AI响应：
{response}

请给出：
1. 每个维度的评分（0-10）和简短理由
2. 总体评分（0-100）
3. 核心优势（1-2点）
4. 主要不足（1-2点）
5. 一句话总评

输出格式要求为JSON。"""

    async def analyze_single_response(self, question: str, response: str, version: str) -> dict:
        """分析单个响应"""
        try:
            result = await self.client.chat_completion(
                messages=[{
                    "role": "user", 
                    "content": self.analysis_prompt.format(
                        question=question,
                        response=response
                    )
                }],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(result.choices[0].message.content)
            analysis['version'] = version
            return analysis
            
        except Exception as e:
            print(f"分析失败: {e}")
            return None

    async def analyze_test_results(self):
        """分析测试结果文件中的响应"""
        # 加载测试报告
        with open('parallel_test_report_20250630_001224.json', 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # 收集分析任务
        analysis_tasks = []
        sample_size = 5  # 每个版本分析5个样本
        
        for version_key, version_data in report['versions'].items():
            results = version_data['results'][:sample_size]
            
            for result in results:
                if result.get('success') and result.get('response_text'):
                    task = self.analyze_single_response(
                        question=result['question'],
                        response=result['response_text'],
                        version=version_data['name']
                    )
                    analysis_tasks.append(task)
        
        print(f"开始分析 {len(analysis_tasks)} 个响应样本...")
        
        # 并行执行分析
        analyses = await asyncio.gather(*analysis_tasks)
        analyses = [a for a in analyses if a is not None]
        
        # 汇总分析结果
        self._generate_comprehensive_report(analyses)
        
    def _generate_comprehensive_report(self, analyses):
        """生成综合分析报告"""
        # 按版本分组
        version_analyses = {}
        for analysis in analyses:
            version = analysis['version']
            if version not in version_analyses:
                version_analyses[version] = []
            version_analyses[version].append(analysis)
        
        report = {
            "analysis_time": datetime.now().isoformat(),
            "total_samples": len(analyses),
            "version_summaries": {}
        }
        
        print("\n" + "="*80)
        print("🎯 基于LLM的深度质量分析报告")
        print("="*80)
        
        for version, version_data in version_analyses.items():
            if not version_data:
                continue
                
            # 计算各维度平均分
            dimensions = [
                '信息准确性', '逻辑严密性', '实用价值', '创新思维',
                '交互友好度', '完整性', '专业深度', '效率优化'
            ]
            
            dim_scores = {dim: [] for dim in dimensions}
            total_scores = []
            
            for analysis in version_data:
                for dim in dimensions:
                    if dim in analysis:
                        score = analysis[dim].get('score', 0) if isinstance(analysis[dim], dict) else 0
                        dim_scores[dim].append(score)
                
                if '总体评分' in analysis:
                    total_scores.append(analysis['总体评分'])
            
            # 计算平均值
            avg_dim_scores = {
                dim: sum(scores)/len(scores) if scores else 0 
                for dim, scores in dim_scores.items()
            }
            avg_total = sum(total_scores)/len(total_scores) if total_scores else 0
            
            # 收集优势和不足
            strengths = []
            weaknesses = []
            for analysis in version_data:
                if '核心优势' in analysis:
                    strengths.extend(analysis['核心优势'] if isinstance(analysis['核心优势'], list) else [analysis['核心优势']])
                if '主要不足' in analysis:
                    weaknesses.extend(analysis['主要不足'] if isinstance(analysis['主要不足'], list) else [analysis['主要不足']])
            
            version_summary = {
                "sample_count": len(version_data),
                "average_total_score": avg_total,
                "dimension_scores": avg_dim_scores,
                "top_strengths": strengths[:3],
                "main_weaknesses": weaknesses[:3],
                "sample_analyses": version_data
            }
            
            report["version_summaries"][version] = version_summary
            
            # 打印结果
            print(f"\n📊 {version}:")
            print(f"  样本数: {len(version_data)}")
            print(f"  综合评分: {avg_total:.1f}/100")
            print(f"\n  各维度评分:")
            for dim, score in sorted(avg_dim_scores.items(), key=lambda x: x[1], reverse=True):
                print(f"    - {dim}: {score:.1f}/10")
            print(f"\n  核心优势:")
            for s in strengths[:2]:
                print(f"    ✓ {s}")
            print(f"\n  主要不足:")
            for w in weaknesses[:2]:
                print(f"    ✗ {w}")
        
        # 保存详细报告
        report_file = f"llm_quality_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细分析报告已保存: {report_file}")

async def main():
    analyzer = LLMResponseAnalyzer()
    await analyzer.analyze_test_results()

if __name__ == "__main__":
    asyncio.run(main())