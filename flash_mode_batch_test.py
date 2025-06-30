#!/usr/bin/env python3
"""
Flash模式批量测试 - 测试50个问题并生成详细分析报告
对比Flash并发搜索模式与原版单次搜索的效果
"""

import asyncio
import time
import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# 加载.env文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.deepsearch_framework import DeepSearchFramework
from src.clients.litellm_client import LiteLLMSDKClientV2

# 设置日志级别，减少输出
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class FlashModeAnalyzer:
    """Flash模式效果分析器"""
    
    def __init__(self):
        self.results = {
            'flash': [],
            'single': [],
            'metadata': {
                'test_start_time': datetime.now().isoformat(),
                'total_questions': 0,
                'flash_mode_version': 'v1.0',
                'test_description': 'Flash并发搜索模式vs单次搜索模式对比测试'
            },
            'analysis': {}
        }
    
    def analyze_single_question(self, question: str, flash_result: Dict, single_result: Dict) -> Dict:
        """分析单个问题的结果对比"""
        analysis = {
            'question': question,
            'flash_success': flash_result.get('success', False),
            'single_success': single_result.get('success', False),
            'performance_comparison': {},
            'quality_comparison': {},
            'recommendation': ''
        }
        
        # 性能对比
        if flash_result.get('success') and single_result.get('success'):
            flash_duration = flash_result.get('duration', 0)
            single_duration = single_result.get('duration', 0)
            
            analysis['performance_comparison'] = {
                'flash_duration': flash_duration,
                'single_duration': single_duration,
                'speedup_ratio': single_duration / flash_duration if flash_duration > 0 else 0,
                'duration_diff': flash_duration - single_duration
            }
            
            # 质量对比
            flash_length = flash_result.get('answer_length', 0)
            single_length = single_result.get('answer_length', 0)
            
            analysis['quality_comparison'] = {
                'flash_answer_length': flash_length,
                'single_answer_length': single_length,
                'length_improvement': (flash_length - single_length) / max(single_length, 1),
                'flash_rounds': flash_result.get('rounds', 0),
                'single_rounds': single_result.get('rounds', 0)
            }
            
            # 推荐策略
            if flash_length > single_length * 1.2 and flash_duration < single_duration * 1.5:
                analysis['recommendation'] = 'Flash模式优于单次搜索'
            elif flash_length < single_length * 0.8:
                analysis['recommendation'] = '单次搜索质量更好'
            elif flash_duration > single_duration * 2:
                analysis['recommendation'] = '单次搜索效率更高'
            else:
                analysis['recommendation'] = '两种模式效果相近'
        
        return analysis
    
    def generate_comprehensive_report(self) -> Dict:
        """生成综合分析报告"""
        flash_results = [r for r in self.results['flash'] if r.get('success')]
        single_results = [r for r in self.results['single'] if r.get('success')]
        
        if not flash_results or not single_results:
            return {'error': '缺少有效的测试结果'}
        
        # 统计分析
        flash_avg_duration = sum(r['duration'] for r in flash_results) / len(flash_results)
        single_avg_duration = sum(r['duration'] for r in single_results) / len(single_results)
        
        flash_avg_length = sum(r['answer_length'] for r in flash_results) / len(flash_results)
        single_avg_length = sum(r['answer_length'] for r in single_results) / len(single_results)
        
        flash_success_rate = len(flash_results) / len(self.results['flash']) * 100
        single_success_rate = len(single_results) / len(self.results['single']) * 100
        
        report = {
            'overall_statistics': {
                'flash_mode': {
                    'success_rate': flash_success_rate,
                    'avg_duration': flash_avg_duration,
                    'avg_answer_length': flash_avg_length,
                    'total_tests': len(self.results['flash'])
                },
                'single_mode': {
                    'success_rate': single_success_rate,
                    'avg_duration': single_avg_duration,
                    'avg_answer_length': single_avg_length,
                    'total_tests': len(self.results['single'])
                }
            },
            'comparative_analysis': {
                'duration_improvement': (single_avg_duration - flash_avg_duration) / single_avg_duration * 100,
                'length_improvement': (flash_avg_length - single_avg_length) / single_avg_length * 100,
                'success_rate_diff': flash_success_rate - single_success_rate
            },
            'recommendations': self._generate_recommendations(flash_results, single_results),
            'detailed_breakdown': self._analyze_performance_distribution(flash_results, single_results)
        }
        
        return report
    
    def _generate_recommendations(self, flash_results: List, single_results: List) -> List[str]:
        """生成使用建议"""
        recommendations = []
        
        # 计算优势场景
        flash_better_count = 0
        single_better_count = 0
        
        for i in range(min(len(flash_results), len(single_results))):
            flash_r = flash_results[i]
            single_r = single_results[i]
            
            if flash_r['answer_length'] > single_r['answer_length'] * 1.1:
                flash_better_count += 1
            elif single_r['answer_length'] > flash_r['answer_length'] * 1.1:
                single_better_count += 1
        
        if flash_better_count > single_better_count:
            recommendations.append("Flash模式在大多数情况下能提供更详细的答案")
        
        # 分析平均性能
        flash_avg_duration = sum(r['duration'] for r in flash_results) / len(flash_results)
        single_avg_duration = sum(r['duration'] for r in single_results) / len(single_results)
        
        if flash_avg_duration < single_avg_duration * 0.8:
            recommendations.append("Flash模式显著提升搜索效率")
        elif flash_avg_duration > single_avg_duration * 1.5:
            recommendations.append("Flash模式虽然质量好但耗时较长，适合深度研究场景")
        
        if not recommendations:
            recommendations.append("Flash模式与单次搜索各有优势，建议根据具体需求选择")
        
        return recommendations
    
    def _analyze_performance_distribution(self, flash_results: List, single_results: List) -> Dict:
        """分析性能分布"""
        return {
            'duration_ranges': {
                'flash_fast': len([r for r in flash_results if r['duration'] < 30]),
                'flash_medium': len([r for r in flash_results if 30 <= r['duration'] < 60]),
                'flash_slow': len([r for r in flash_results if r['duration'] >= 60]),
                'single_fast': len([r for r in single_results if r['duration'] < 30]),
                'single_medium': len([r for r in single_results if 30 <= r['duration'] < 60]),
                'single_slow': len([r for r in single_results if r['duration'] >= 60])
            },
            'quality_ranges': {
                'flash_detailed': len([r for r in flash_results if r['answer_length'] > 1000]),
                'flash_medium': len([r for r in flash_results if 500 <= r['answer_length'] <= 1000]),
                'flash_brief': len([r for r in flash_results if r['answer_length'] < 500]),
                'single_detailed': len([r for r in single_results if r['answer_length'] > 1000]),
                'single_medium': len([r for r in single_results if 500 <= r['answer_length'] <= 1000]),
                'single_brief': len([r for r in single_results if r['answer_length'] < 500])
            }
        }

async def run_batch_test():
    """运行批量测试"""
    print("🚀 Flash模式批量测试开始")
    print("=" * 60)
    
    # 检查环境
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY 未设置")
        return None
    
    # 加载问题集
    questions_file = "questions/search/diverse_questions_50.json"
    if not os.path.exists(questions_file):
        print(f"❌ 问题文件不存在: {questions_file}")
        return None
    
    try:
        with open(questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
        
        # 解析问题格式
        if isinstance(questions_data, list):
            questions = [q.get('question', q) if isinstance(q, dict) else q for q in questions_data]
        else:
            questions = [q['question'] for q in questions_data.get('questions', [])]
        
        print(f"✅ 加载了 {len(questions)} 个测试问题")
        
        # 限制测试数量（避免时间过长）
        test_questions = questions[:15]  # 先测试15个问题
        print(f"🎯 本次测试前 {len(test_questions)} 个问题")
        
        # 初始化分析器
        analyzer = FlashModeAnalyzer()
        analyzer.results['metadata']['total_questions'] = len(test_questions)
        
        # 初始化客户端
        print("🔧 初始化DeepSearch框架...")
        litellm_client = LiteLLMSDKClientV2()
        framework = DeepSearchFramework(litellm_client=litellm_client, config={})
        
        # 批量测试
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 问题 {i}/{len(test_questions)}: {question[:60]}...")
            
            # 测试Flash模式
            print(f"🔥 Flash模式...")
            flash_result = await test_single_question(framework, question, "flash")
            analyzer.results['flash'].append(flash_result)
            
            if flash_result['success']:
                print(f"  ✅ Flash: {flash_result['duration']:.1f}秒, {flash_result['answer_length']}字符")
            else:
                print(f"  ❌ Flash: 失败")
            
            # 测试单次模式
            print(f"🔍 单次模式...")
            single_result = await test_single_question(framework, question, "single")
            analyzer.results['single'].append(single_result)
            
            if single_result['success']:
                print(f"  ✅ 单次: {single_result['duration']:.1f}秒, {single_result['answer_length']}字符")
            else:
                print(f"  ❌ 单次: 失败")
            
            # 简单对比
            if flash_result['success'] and single_result['success']:
                if flash_result['answer_length'] > single_result['answer_length'] * 1.1:
                    print(f"  📈 Flash模式答案更详细 (+{(flash_result['answer_length']/single_result['answer_length']-1)*100:.1f}%)")
                elif flash_result['duration'] < single_result['duration'] * 0.9:
                    print(f"  ⚡ Flash模式更快 (-{(1-flash_result['duration']/single_result['duration'])*100:.1f}%)")
            
            # 休息避免API限流
            if i < len(test_questions):
                await asyncio.sleep(3)
        
        # 生成最终报告
        print(f"\n📊 生成分析报告...")
        analyzer.results['metadata']['test_end_time'] = datetime.now().isoformat()
        final_report = analyzer.generate_comprehensive_report()
        analyzer.results['analysis'] = final_report
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = f"flash_mode_batch_test_results_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(analyzer.results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 详细结果已保存到: {result_file}")
        
        # 显示汇总
        display_summary(final_report)
        
        return analyzer.results
        
    except Exception as e:
        print(f"❌ 批量测试失败: {e}")
        logger.exception("批量测试异常")
        return None

async def test_single_question(framework: DeepSearchFramework, question: str, mode: str) -> Dict:
    """测试单个问题"""
    start_time = time.time()
    
    try:
        result = None
        async for result in framework.execute_deepsearch_workflow(
            question=question,
            max_rounds=1,  # 只测试1轮，专注对比搜索阶段的并发效果
            search_mode=mode
        ):
            result = result
            break
        
        duration = time.time() - start_time
        
        if result and result.get('final_answer'):
            return {
                'success': True,
                'duration': duration,
                'answer_length': len(result.get('final_answer', '')),
                'rounds': len(result.get('rounds', [])),
                'final_answer': result.get('final_answer', ''),
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'mode': mode
            }
        else:
            return {
                'success': False,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'question': question,
                'mode': mode,
                'error': 'No result returned'
            }
            
    except Exception as e:
        duration = time.time() - start_time
        return {
            'success': False,
            'duration': duration,
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'mode': mode,
            'error': str(e)
        }

def display_summary(report: Dict):
    """显示测试汇总结果"""
    print(f"\n" + "=" * 60)
    print(f"📈 Flash模式批量测试汇总")
    print(f"=" * 60)
    
    if 'error' in report:
        print(f"❌ 报告生成失败: {report['error']}")
        return
    
    overall = report['overall_statistics']
    comparative = report['comparative_analysis']
    
    print(f"📊 整体统计:")
    print(f"  Flash模式: {overall['flash_mode']['success_rate']:.1f}% 成功率")
    print(f"    平均耗时: {overall['flash_mode']['avg_duration']:.1f}秒")
    print(f"    平均答案长度: {overall['flash_mode']['avg_answer_length']:.0f}字符")
    
    print(f"  单次模式: {overall['single_mode']['success_rate']:.1f}% 成功率")
    print(f"    平均耗时: {overall['single_mode']['avg_duration']:.1f}秒")
    print(f"    平均答案长度: {overall['single_mode']['avg_answer_length']:.0f}字符")
    
    print(f"\n📈 对比分析:")
    print(f"  耗时变化: {comparative['duration_improvement']:+.1f}%")
    print(f"  答案长度变化: {comparative['length_improvement']:+.1f}%")
    print(f"  成功率差异: {comparative['success_rate_diff']:+.1f}%")
    
    print(f"\n💡 使用建议:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # 简单结论
    if comparative['length_improvement'] > 10 and comparative['duration_improvement'] > -20:
        print(f"\n🎉 结论: Flash并发搜索模式表现优秀，推荐使用！")
    elif comparative['length_improvement'] > 0:
        print(f"\n✅ 结论: Flash模式略有优势，可以考虑使用。")
    else:
        print(f"\n⚠️ 结论: Flash模式需要进一步优化。")

async def main():
    """主函数"""
    print("🧪 Flash并发搜索模式批量评估测试")
    
    # 运行批量测试
    results = await run_batch_test()
    
    if results:
        print(f"\n🎯 测试完成！请查看JSON文件了解详细数据。")
        print(f"📝 可以基于这些结果来决定是否启用Flash模式。")
    else:
        print(f"\n❌ 测试失败")

if __name__ == "__main__":
    asyncio.run(main())