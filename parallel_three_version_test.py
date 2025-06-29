#!/usr/bin/env python3

"""
并行测试三个版本的DeepSearch Agent
- 每个版本独立运行，独立日志
- 支持断点续跑
- 优化性能，减少等待时间
"""

import asyncio
import json
import logging
from datetime import datetime
import sys
import os
from typing import Dict, List, Optional
import time
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

class ParallelVersionTester:
    def __init__(self):
        self.client = EnhancedLiteLLMClient()
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 版本配置
        self.versions = {
            "original": {
                "name": "原版",
                "file": "s3-rag-rl/versions/original/agent_system.txt",
                "start_from": 36  # 从第36题开始
            },
            "lite": {
                "name": "轻量版",
                "file": "deepsearch/versions/v1.2.1/unified_agent_lite.txt",
                "start_from": 1  # 从头开始
            },
            "full": {
                "name": "完备版",
                "file": "deepsearch/versions/v1.2.1/unified_agent_system.txt",
                "start_from": 1  # 从头开始
            }
        }
        
        # 为每个版本设置独立的日志
        self.loggers = {}
        self._setup_loggers()
        
        # 测试结果
        self.test_results = {
            "original": [],
            "lite": [],
            "full": []
        }
        
        # 加载或恢复之前的结果
        self._load_previous_results()
        
    def _setup_loggers(self):
        """为每个版本设置独立的日志记录器"""
        log_dir = Path("logs/parallel_test")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        for version_key in self.versions:
            logger_name = f"test_{version_key}"
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
            
            # 清除现有处理器
            logger.handlers.clear()
            
            # 文件处理器 - 每个版本独立文件
            file_handler = logging.FileHandler(
                log_dir / f"{version_key}_{self.timestamp}.log",
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            
            # 格式化
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            self.loggers[version_key] = logger
            
    def _load_previous_results(self):
        """加载之前的测试结果用于断点续跑"""
        for version_key in self.versions:
            resume_file = f"parallel_test_{version_key}_checkpoint.json"
            if os.path.exists(resume_file):
                try:
                    with open(resume_file, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                        self.test_results[version_key] = saved_data.get('results', [])
                        completed_count = len([r for r in self.test_results[version_key] if r.get('success')])
                        self.loggers[version_key].info(f"加载已完成的{completed_count}个测试结果")
                except Exception as e:
                    self.loggers[version_key].error(f"加载检查点失败: {e}")
                    
    def _save_checkpoint(self, version_key: str):
        """保存检查点用于断点续跑"""
        checkpoint_file = f"parallel_test_{version_key}_checkpoint.json"
        try:
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'version': version_key,
                    'timestamp': self.timestamp,
                    'results': self.test_results[version_key]
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.loggers[version_key].error(f"保存检查点失败: {e}")
            
    async def test_version(self, version_key: str, questions: List[Dict]):
        """测试单个版本"""
        config = self.versions[version_key]
        version_name = config['name']
        logger = self.loggers[version_key]
        start_from = config['start_from']
        
        print(f"\n🚀 开始{version_name}测试 (从第{start_from}题开始)")
        logger.info(f"开始{version_name}测试，共{len(questions)}个问题")
        
        # 加载prompt
        prompt_path = f"prompts/{config['file']}"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            logger.info(f"成功加载prompt: {prompt_path}")
        except FileNotFoundError:
            logger.error(f"Prompt文件未找到: {prompt_path}")
            print(f"❌ {version_name}: Prompt文件未找到")
            return
            
        # 获取已完成的问题ID
        completed_ids = {r['question_id'] for r in self.test_results[version_key] if r.get('success')}
        
        # 测试每个问题
        for i, question_data in enumerate(questions[start_from-1:], start_from):
            question_id = question_data['id']
            
            # 跳过已完成的
            if question_id in completed_ids:
                logger.info(f"跳过已完成的问题 {i}: {question_id}")
                continue
                
            question = question_data['question']
            logger.info(f"开始测试问题 {i}/50: {question[:50]}...")
            
            try:
                # 执行测试
                result = await self._execute_single_test(
                    system_prompt, question_data, version_key, logger
                )
                
                self.test_results[version_key].append(result)
                
                # 打印进度
                print(f"  {version_name} [{i}/50] ✅ {result['execution_time']:.1f}s - {result['overall_score']*100:.0f}%")
                
                # 每完成一题就保存检查点
                self._save_checkpoint(version_key)
                
            except Exception as e:
                logger.error(f"问题 {i} 测试失败: {e}", exc_info=True)
                error_result = {
                    "question_id": question_id,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                }
                self.test_results[version_key].append(error_result)
                print(f"  {version_name} [{i}/50] ❌ 错误: {str(e)[:50]}...")
                
            # 短暂休息避免过载
            await asyncio.sleep(1)
            
        print(f"\n✅ {version_name}测试完成！")
        logger.info(f"{version_name}测试完成，共{len(self.test_results[version_key])}个结果")
        
    async def _execute_single_test(self, system_prompt: str, question_data: Dict, 
                                   version_key: str, logger: logging.Logger) -> Dict:
        """执行单个测试"""
        start_time = time.time()
        
        # 创建测试场景
        test_scenario = f"""请分析以下问题：

{question_data['question']}

请按照系统提示的格式要求进行回答。"""
        
        # 调用LLM
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_scenario}
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    timeout=90
                )
                break
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
        response_text = response.choices[0].message.content
        execution_time = time.time() - start_time
        
        # 简单评分
        score = self._simple_score(response_text, version_key)
        
        return {
            "question_id": question_data['id'],
            "question": question_data['question'],
            "category": question_data.get('category', 'unknown'),
            "complexity": question_data.get('complexity', 'medium'),
            "version": version_key,
            "response_text": response_text,
            "response_length": len(response_text),
            "execution_time": execution_time,
            "overall_score": score,
            "success": True,
            "timestamp": datetime.now().isoformat()
        }
        
    def _simple_score(self, response: str, version_key: str) -> float:
        """简单评分函数"""
        score = 0.0
        
        # 检查关键元素
        if '<thinking>' in response and '</thinking>' in response:
            score += 0.3
        if '<search_complete>' in response:
            score += 0.2
        if len(response) > 200:
            score += 0.2
        if any(term in response for term in ['分析', '评估', '选择']):
            score += 0.3
            
        return min(score, 1.0)
        
    async def run_parallel_tests(self):
        """并行运行所有版本的测试"""
        # 加载测试问题
        with open('questions/search/diverse_questions_50.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
            
        print(f"\n🎯 并行测试开始 - {datetime.now().strftime('%H:%M:%S')}")
        print(f"📋 测试问题数: 50")
        print(f"🔧 版本: 原版(从36题)、轻量版、完备版")
        print(f"📁 日志目录: logs/parallel_test/")
        
        # 创建并行任务
        tasks = []
        for version_key in self.versions:
            task = asyncio.create_task(self.test_version(version_key, questions))
            tasks.append(task)
            
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 生成最终报告
        self._generate_final_report()
        
    def _generate_final_report(self):
        """生成最终测试报告"""
        report = {
            "test_timestamp": self.timestamp,
            "versions": {}
        }
        
        print(f"\n{'='*60}")
        print("📊 并行测试完成报告")
        print(f"{'='*60}")
        
        for version_key, version_config in self.versions.items():
            results = self.test_results[version_key]
            success_results = [r for r in results if r.get('success')]
            
            if success_results:
                avg_time = sum(r['execution_time'] for r in success_results) / len(success_results)
                avg_score = sum(r['overall_score'] for r in success_results) / len(success_results)
            else:
                avg_time = 0
                avg_score = 0
                
            version_report = {
                "name": version_config['name'],
                "total_questions": len(results),
                "success_count": len(success_results),
                "average_time": avg_time,
                "average_score": avg_score,
                "results": results
            }
            
            report["versions"][version_key] = version_report
            
            print(f"\n{version_config['name']}:")
            print(f"  ✅ 成功: {len(success_results)}/{len(results)}")
            print(f"  ⏱️  平均时间: {avg_time:.1f}秒")
            print(f"  🎯 平均质量: {avg_score*100:.1f}%")
            
        # 保存报告
        report_file = f"parallel_test_report_{self.timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
        print(f"\n💾 完整报告已保存: {report_file}")
        
async def main():
    tester = ParallelVersionTester()
    await tester.run_parallel_tests()
    
if __name__ == "__main__":
    asyncio.run(main())