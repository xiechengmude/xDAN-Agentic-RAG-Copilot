#!/usr/bin/env python3
"""
端到端后端测试运行器 - 逐个问题测试并分析
遵循KISS和DRY原则，保存完整trace并用LLM分析
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class E2ETestRunner:
    """端到端测试运行器"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.traces_dir = self.test_dir / "traces"
        self.analysis_dir = self.test_dir / "analysis"
        self.logs_dir = self.test_dir / "logs"
        
        # 确保目录存在
        for dir_path in [self.traces_dir, self.analysis_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def load_questions(self, file_path: str) -> list:
        """加载问题数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def test_single_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个问题"""
        question_id = question_data['id']
        question = question_data['question']
        
        logger.info(f"开始测试问题: {question_id}")
        logger.info(f"问题内容: {question}")
        
        # 创建DeepSearch框架
        litellm_client = EnhancedLiteLLMClient()
        framework = DeepSearchFramework(litellm_client)
        
        # 记录开始时间
        start_time = datetime.now()
        
        try:
            # 执行搜索 - 收集所有结果
            result_parts = []
            async for chunk in framework.execute_deepsearch_workflow(
                question=question,
                max_rounds=3,
                stream=False
            ):
                result_parts.append(chunk)
            
            # 取最后一个结果作为完整结果
            result = result_parts[-1] if result_parts else None
            
            # 记录结束时间
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 构建完整trace
            trace_data = {
                "question_id": question_id,
                "question": question,
                "category": question_data.get('category', ''),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "result": result,
                "success": True,
                "error": None
            }
            
            logger.info(f"问题 {question_id} 测试完成，耗时: {duration:.2f}秒")
            
        except Exception as e:
            logger.error(f"问题 {question_id} 测试失败: {str(e)}")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            trace_data = {
                "question_id": question_id,
                "question": question,
                "category": question_data.get('category', ''),
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "result": None,
                "success": False,
                "error": str(e)
            }
        
        # 保存trace
        trace_file = self.traces_dir / f"{question_id}_trace.json"
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)
        
        return trace_data
    
    async def analyze_trace_with_llm(self, trace_data: Dict[str, Any]) -> Dict[str, Any]:
        """用LLM分析trace结果"""
        question_id = trace_data['question_id']
        
        if not trace_data['success']:
            analysis = {
                "question_id": question_id,
                "analysis_time": datetime.now().isoformat(),
                "success": False,
                "error_analysis": f"测试失败: {trace_data['error']}",
                "scores": None,
                "recommendations": ["修复错误后重新测试"]
            }
        else:
            # 构建分析提示词
            analysis_prompt = f"""
请分析以下DeepSearch测试结果：

问题ID: {question_id}
问题: {trace_data['question']}
类别: {trace_data['category']}
执行时间: {trace_data['duration_seconds']:.2f}秒

结果: {json.dumps(trace_data['result'], ensure_ascii=False, indent=2)}

请从以下维度评分(1-5分)并提供分析：
1. 答案质量 - 回答是否准确、全面、有用
2. 搜索效率 - 搜索轮数是否合理，信息获取是否高效
3. 信息相关性 - 搜索到的信息是否与问题相关
4. 综合表现 - 整体表现评价

请提供JSON格式的分析结果，包含scores(各维度分数)和detailed_analysis(详细分析)。
"""
            
            try:
                # 用LLM分析
                litellm_client = EnhancedLiteLLMClient()
                llm_response = await litellm_client.achat(
                    messages=[{"role": "user", "content": analysis_prompt}],
                    model="deepseek-chat"
                )
                
                # 解析LLM响应
                try:
                    analysis_result = json.loads(llm_response.choices[0].message.content)
                except:
                    analysis_result = {
                        "scores": {"overall": 3},
                        "detailed_analysis": llm_response.choices[0].message.content
                    }
                
                analysis = {
                    "question_id": question_id,
                    "analysis_time": datetime.now().isoformat(),
                    "success": True,
                    "scores": analysis_result.get("scores", {}),
                    "detailed_analysis": analysis_result.get("detailed_analysis", ""),
                    "llm_raw_response": llm_response.choices[0].message.content
                }
                
            except Exception as e:
                logger.error(f"LLM分析失败: {str(e)}")
                analysis = {
                    "question_id": question_id,
                    "analysis_time": datetime.now().isoformat(),
                    "success": False,
                    "error": str(e),
                    "fallback_analysis": "LLM分析失败，需要手动分析"
                }
        
        # 保存分析结果
        analysis_file = self.analysis_dir / f"{question_id}_analysis.json"
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return analysis
    
    async def run_test_batch(self, questions_file: str, start_index: int = 0, count: int = 5):
        """运行批量测试"""
        questions = self.load_questions(questions_file)
        end_index = min(start_index + count, len(questions))
        
        logger.info(f"开始测试问题 {start_index} 到 {end_index-1}，共 {end_index-start_index} 个问题")
        
        results = []
        
        for i in range(start_index, end_index):
            question_data = questions[i]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"测试进度: {i+1-start_index}/{end_index-start_index}")
            
            # 测试问题
            trace_data = await self.test_single_question(question_data)
            
            # 分析结果
            analysis = await self.analyze_trace_with_llm(trace_data)
            
            results.append({
                "question_index": i,
                "trace": trace_data,
                "analysis": analysis
            })
            
            logger.info(f"问题 {question_data['id']} 完成")
        
        # 保存批次总结
        batch_summary = {
            "batch_info": {
                "start_index": start_index,
                "end_index": end_index,
                "total_tested": len(results),
                "timestamp": datetime.now().isoformat()
            },
            "results": results
        }
        
        summary_file = self.logs_dir / f"batch_{start_index}_{end_index-1}_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n批次测试完成，结果保存到: {summary_file}")
        return batch_summary

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python test_runner.py <问题文件路径> [开始索引] [测试数量]")
        print("示例: python test_runner.py ../questions/search/diverse_questions_50_formatted.json 0 3")
        return
    
    questions_file = sys.argv[1]
    start_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    runner = E2ETestRunner()
    await runner.run_test_batch(questions_file, start_index, count)

if __name__ == "__main__":
    asyncio.run(main())