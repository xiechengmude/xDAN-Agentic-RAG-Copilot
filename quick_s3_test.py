#!/usr/bin/env python3
"""
S3 RAG 服务快速测试版本
专注核心测试用例，快速评估RAG性能
"""
import asyncio
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)

from src.services.s3_service import S3Service
from src.core.config_loader import ConfigLoader
from src.core.langfuse_client import langfuse_client

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickS3Test:
    """S3 RAG 服务快速测试"""
    
    def __init__(self):
        self.test_results = []
        self.setup_services()
    
    def setup_services(self):
        """初始化服务"""
        # 初始化 Langfuse
        langfuse_client.initialize()
        
        # 初始化 S3 服务
        config_loader = ConfigLoader()
        config = {
            'ragflow_api_url': config_loader.get('ragflow.api_url'),
            'ragflow_api_key': config_loader.get('ragflow.api_key'),
            'default_dataset_id': config_loader.get('ragflow.default_dataset_id')
        }
        self.s3_service = S3Service(config)
    
    async def run_quick_test(self):
        """运行快速测试"""
        print("🚀 S3 RAG 服务快速测试")
        print("=" * 60)
        
        # 核心测试用例
        test_cases = [
            {
                "name": "系统核心功能测试",
                "question": "智信平台中的ice-crp系统主要负责什么功能？",
                "expected_keywords": ["ice-crp", "路由系统", "授信路由", "借款路由"],
                "test_type": "core_function"
            },
            {
                "name": "流程完整性测试",
                "question": "智信平台有几种扣款模式？分别是什么？",
                "expected_keywords": ["两种", "机构绑卡扣款模式", "辅助扣款模式"],
                "test_type": "process_completeness"
            },
            {
                "name": "技术架构测试",
                "question": "ice-pfs-app、ice-partner-app、ice-gws-app的作用分别是什么？",
                "expected_keywords": ["ice-pfs-app", "ice-partner-app", "ice-gws-app", "产品流程", "机构配置", "机构交互"],
                "test_type": "architecture"
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n📋 测试 {i}: {case['name']}")
            print("-" * 50)
            
            result = await self.execute_test_case(case, f"quick-{i}")
            self.test_results.append(result)
            
            # 显示结果
            self.display_result(result)
            
            # 短暂等待
            await asyncio.sleep(2)
        
        # 生成报告
        self.generate_quick_report()
    
    async def execute_test_case(self, test_case: Dict, test_id: str) -> Dict:
        """执行测试用例"""
        chat_id = f"s3-quick-{test_id}-{datetime.now().strftime('%H%M%S')}"
        
        # 创建 Langfuse 追踪
        try:
            trace_id = langfuse_client.start_trace(
                name=f"Quick S3 Test - {test_case['name']}",
                metadata={
                    "test_type": test_case.get('test_type', 'unknown'),
                    "test_id": test_id
                },
                tags=["s3-quick-test", test_case.get('test_type', 'general')]
            )
        except Exception as e:
            trace_id = f"trace-error-{test_id}"
            logger.warning(f"Langfuse追踪创建失败: {e}")
        
        # 执行测试
        start_time = time.time()
        try:
            result_data = {}
            async for chunk in self.s3_service.ask(
                question=test_case['question'],
                max_rounds=2,  # 限制轮数以加快速度
                stream=False
            ):
                if isinstance(chunk, dict):
                    result_data.update(chunk)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 分析结果
            analysis = self.analyze_result(test_case, result_data, execution_time)
            
            return {
                "test_id": test_id,
                "test_name": test_case['name'],
                "test_type": test_case.get('test_type', 'unknown'),
                "question": test_case['question'],
                "answer": result_data.get('answer', ''),
                "execution_time": execution_time,
                "metadata": result_data.get('metadata', {}),
                "langfuse_trace": trace_id,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "test_id": test_id,
                "test_name": test_case['name'],
                "test_type": test_case.get('test_type', 'unknown'),
                "question": test_case['question'],
                "error": str(e),
                "execution_time": time.time() - start_time,
                "analysis": {"overall_score": 0, "error": str(e)},
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_result(self, test_case: Dict, result_data: Dict, execution_time: float) -> Dict:
        """分析测试结果"""
        answer = result_data.get('answer', '')
        metadata = result_data.get('metadata', {})
        
        # 关键词覆盖率
        expected_keywords = test_case.get('expected_keywords', [])
        found_keywords = [kw for kw in expected_keywords if kw in answer]
        keyword_coverage = len(found_keywords) / len(expected_keywords) if expected_keywords else 0
        
        # 答案质量
        answer_quality = min(1.0, len(answer) / 200) if answer else 0
        
        # 时间效率
        time_efficiency = 1.0 if execution_time <= 30 else max(0, 1.0 - (execution_time - 30) / 30)
        
        # 文档利用率
        docs_used = metadata.get('documents_used', 0)
        doc_utilization = min(1.0, docs_used / 5) if docs_used > 0 else 0
        
        # 综合评分
        overall_score = (keyword_coverage * 0.4 + answer_quality * 0.3 + 
                        time_efficiency * 0.2 + doc_utilization * 0.1)
        
        return {
            "overall_score": overall_score,
            "keyword_coverage": keyword_coverage,
            "answer_quality": answer_quality,
            "time_efficiency": time_efficiency,
            "doc_utilization": doc_utilization,
            "found_keywords": found_keywords,
            "docs_used": docs_used,
            "search_rounds": metadata.get('search_rounds', 0)
        }
    
    def display_result(self, result: Dict):
        """显示测试结果"""
        score = result['analysis']['overall_score']
        status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
        
        print(f"  {status} 综合评分: {score:.2f}")
        print(f"  ⏱️ 执行时间: {result['execution_time']:.1f}秒")
        
        analysis = result['analysis']
        print(f"  📊 关键词覆盖: {analysis['keyword_coverage']:.1%} ({len(analysis['found_keywords'])}/{len(result['analysis'].get('found_keywords', []))})")
        print(f"  📝 答案质量: {analysis['answer_quality']:.2f}")
        print(f"  📚 使用文档: {analysis['docs_used']} 个")
        print(f"  🔄 搜索轮数: {analysis['search_rounds']}")
        
        if analysis['found_keywords']:
            print(f"  ✅ 匹配关键词: {', '.join(analysis['found_keywords'])}")
        
        # 显示答案片段
        answer = result.get('answer', '')
        if answer:
            preview = answer[:100] + "..." if len(answer) > 100 else answer
            print(f"  💭 答案预览: {preview}")
    
    def generate_quick_report(self):
        """生成快速测试报告"""
        print(f"\n{'='*60}")
        print("📊 S3 RAG 快速测试报告")
        print("="*60)
        
        if not self.test_results:
            print("无测试结果")
            return
        
        # 统计
        successful_tests = [r for r in self.test_results if 'error' not in r]
        avg_score = sum(r['analysis']['overall_score'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_time = sum(r['execution_time'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        print(f"\n📈 整体表现")
        print(f"  总测试数: {len(self.test_results)}")
        print(f"  成功率: {len(successful_tests)}/{len(self.test_results)} ({len(successful_tests)/len(self.test_results):.1%})")
        print(f"  平均评分: {avg_score:.2f}/1.00")
        print(f"  平均响应时间: {avg_time:.1f}秒")
        
        print(f"\n📋 详细结果")
        for result in self.test_results:
            score = result['analysis']['overall_score']
            status = "🟢" if score > 0.8 else "🟡" if score > 0.5 else "🔴"
            print(f"  {status} {result['test_name']}: {score:.2f} ({result['execution_time']:.1f}s)")
        
        # 保存报告
        report_data = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "successful_tests": len(successful_tests),
                "average_score": avg_score,
                "average_time": avg_time
            },
            "detailed_results": self.test_results,
            "generated_at": datetime.now().isoformat()
        }
        
        report_file = f"quick_s3_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存: {report_file}")
        print(f"🔗 Langfuse 追踪: {os.getenv('LANGFUSE_HOST')}")
        print("="*60)

async def main():
    """主函数"""
    test = QuickS3Test()
    await test.run_quick_test()
    
    # 关闭 Langfuse 连接
    langfuse_client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())