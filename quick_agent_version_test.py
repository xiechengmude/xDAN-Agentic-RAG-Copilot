#!/usr/bin/env python3
"""
快速统一Agent版本对比测试
使用真实问题进行快速A/B测试
"""

import json
import logging
import sys
import os
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
for logger in ['httpx', 'openai', 'LiteLLM', 'urllib3']:
    logging.getLogger(logger).setLevel(logging.WARNING)

class QuickVersionTester:
    def __init__(self):
        self.client = EnhancedLiteLLMClient()
        
    async def run_quick_comparison(self):
        """运行快速版本对比"""
        
        print("⚡ 快速统一Agent版本A/B测试")
        print("目标: 使用真实问题快速对比完整版vs轻量版")
        print("="*80)
        
        # 加载真实测试问题
        test_questions = self._load_sample_questions()
        
        print(f"📝 测试问题: {len(test_questions)}个")
        
        results = {}
        
        # 测试两个版本
        for version_name, prompt_file in [
            ("完整版", "unified_agent_system.txt"),
            ("轻量版", "unified_agent_lite.txt")
        ]:
            print(f"\n{'='*50}")
            print(f"🔄 测试{version_name}")
            print(f"{'='*50}")
            
            version_results = await self._test_version(test_questions, prompt_file, version_name)
            results[version_name] = version_results
        
        # 生成对比报告
        self._generate_quick_report(results)
    
    def _load_sample_questions(self) -> List[Dict]:
        """加载样本问题"""
        try:
            with open('questions/search/test_sample_50.json', 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            
            # 选择3个代表性问题进行快速测试
            selected = []
            indices = [0, 25, 45]  # 分散选择
            
            for idx in indices:
                if idx < len(all_questions):
                    q = all_questions[idx]
                    selected.append({
                        "id": q.get("id", f"test_{idx}"),
                        "category": q.get("category", "未知"),
                        "question": q.get("question", ""),
                        "complexity": self._assess_complexity(q.get("question", ""))
                    })
            
            return selected
            
        except FileNotFoundError:
            # 备用问题
            return [
                {
                    "id": "roe_analysis",
                    "category": "数据分析",
                    "question": "请对新能源汽车行业的ROE进行深度分析，包括历史趋势、影响因素和未来预测。",
                    "complexity": "high"
                },
                {
                    "id": "tech_system",
                    "category": "技术分析", 
                    "question": "设计一个在线学习系统，实现数据可视化、报表生成功能。",
                    "complexity": "medium"
                },
                {
                    "id": "business_model",
                    "category": "业务分析",
                    "question": "分析字节跳动的商业模式和竞争优势。",
                    "complexity": "low"
                }
            ]
    
    def _assess_complexity(self, question: str) -> str:
        """评估问题复杂度"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['深度分析', 'roe', '预测', '系统性']):
            return "high"
        elif any(word in question_lower for word in ['分析', '设计', '比较', '评估']):
            return "medium"
        else:
            return "low"
    
    async def _test_version(self, questions: List[Dict], prompt_file: str, version_name: str) -> List[Dict]:
        """测试特定版本"""
        
        # 加载prompt
        prompt_path = f"prompts/deepsearch/versions/v1.2.1/{prompt_file}"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            print(f"⚠️ Prompt文件未找到: {prompt_path}")
            return []
        
        results = []
        
        for i, question_data in enumerate(questions, 1):
            question = question_data['question']
            
            print(f"\n[{i}/{len(questions)}] {question_data['category']}: {question[:40]}...")
            
            # 创建简化的测试场景
            test_scenario = f"""
问题: {question}

候选搜索结果:
1. 官方权威报告 - 包含专业数据和分析
2. 行业研究机构报告 - 深度市场分析
3. 学术论文 - 理论基础和方法论
4. 新闻媒体报道 - 最新动态和观点

请评估这些信息源并做出搜索决策。
"""
            
            start_time = time.time()
            
            try:
                response = await self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_scenario}
                    ],
                    temperature=0.1,
                    max_tokens=600  # 限制长度提升速度
                )
                
                response_text = response.choices[0].message.content
                response_time = time.time() - start_time
                
                # 快速质量评估
                quality_score = self._quick_quality_check(response_text)
                
                result = {
                    "question_id": question_data['id'],
                    "question": question,
                    "complexity": question_data['complexity'],
                    "response_time": response_time,
                    "response_length": len(response_text),
                    "quality_score": quality_score,
                    "has_thinking": '<thinking>' in response_text,
                    "has_decision": any(tag in response_text for tag in ['<search_complete>', '<important_urls>']),
                    "success": True
                }
                
                results.append(result)
                
                print(f"  ✅ 响应时间: {response_time:.1f}s")
                print(f"  📏 响应长度: {len(response_text)}字符")
                print(f"  🎯 质量评分: {quality_score*100:.1f}%")
                
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                results.append({
                    "question_id": question_data['id'],
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def _quick_quality_check(self, response: str) -> float:
        """快速质量检查"""
        score = 0.0
        
        # 格式完整性 (50%)
        if '<thinking>' in response and '</thinking>' in response:
            score += 0.25
        if '<search_complete>' in response:
            score += 0.15
        if '<important_urls>' in response or '<next_query>' in response:
            score += 0.1
        
        # 内容质量 (50%)
        if '分析' in response or 'analysis' in response.lower():
            score += 0.2
        if '选择' in response or 'select' in response.lower():
            score += 0.15
        if len(response) > 200:  # 足够详细
            score += 0.15
        
        return min(score, 1.0)
    
    def _generate_quick_report(self, results: Dict):
        """生成快速报告"""
        
        print(f"\n{'='*80}")
        print("📊 快速版本对比报告")
        print(f"{'='*80}")
        
        full_results = [r for r in results.get("完整版", []) if r.get('success')]
        lite_results = [r for r in results.get("轻量版", []) if r.get('success')]
        
        if not full_results or not lite_results:
            print("❌ 测试数据不足")
            return
        
        # 性能对比
        full_avg_time = sum(r['response_time'] for r in full_results) / len(full_results)
        lite_avg_time = sum(r['response_time'] for r in lite_results) / len(lite_results)
        
        print(f"⚡ 响应速度对比:")
        print(f"  完整版平均: {full_avg_time:.1f}秒")
        print(f"  轻量版平均: {lite_avg_time:.1f}秒")
        
        speed_improvement = (full_avg_time - lite_avg_time) / full_avg_time * 100
        print(f"  轻量版提升: {speed_improvement:+.1f}%")
        
        # 质量对比
        full_avg_quality = sum(r['quality_score'] for r in full_results) / len(full_results)
        lite_avg_quality = sum(r['quality_score'] for r in lite_results) / len(lite_results)
        
        print(f"\n🎯 质量对比:")
        print(f"  完整版平均: {full_avg_quality*100:.1f}%")
        print(f"  轻量版平均: {lite_avg_quality*100:.1f}%")
        
        quality_change = (lite_avg_quality - full_avg_quality) * 100
        print(f"  质量变化: {quality_change:+.1f}%")
        
        # 响应长度对比
        full_avg_length = sum(r['response_length'] for r in full_results) / len(full_results)
        lite_avg_length = sum(r['response_length'] for r in lite_results) / len(lite_results)
        
        print(f"\n📏 响应详细度对比:")
        print(f"  完整版平均: {full_avg_length:.0f}字符")
        print(f"  轻量版平均: {lite_avg_length:.0f}字符")
        
        length_change = (lite_avg_length - full_avg_length) / full_avg_length * 100
        print(f"  长度变化: {length_change:+.1f}%")
        
        # 格式一致性对比
        full_thinking_rate = sum(1 for r in full_results if r.get('has_thinking')) / len(full_results)
        lite_thinking_rate = sum(1 for r in lite_results if r.get('has_thinking')) / len(lite_results)
        
        full_decision_rate = sum(1 for r in full_results if r.get('has_decision')) / len(full_results)
        lite_decision_rate = sum(1 for r in lite_results if r.get('has_decision')) / len(lite_results)
        
        print(f"\n🔧 格式一致性对比:")
        print(f"  思考过程完整率:")
        print(f"    完整版: {full_thinking_rate*100:.1f}%")
        print(f"    轻量版: {lite_thinking_rate*100:.1f}%")
        print(f"  决策格式完整率:")
        print(f"    完整版: {full_decision_rate*100:.1f}%")
        print(f"    轻量版: {lite_decision_rate*100:.1f}%")
        
        # 按复杂度分析
        print(f"\n📈 按问题复杂度分析:")
        
        for complexity in ['high', 'medium', 'low']:
            full_complex = [r for r in full_results if r.get('complexity') == complexity]
            lite_complex = [r for r in lite_results if r.get('complexity') == complexity]
            
            if full_complex and lite_complex:
                full_time = sum(r['response_time'] for r in full_complex) / len(full_complex)
                lite_time = sum(r['response_time'] for r in lite_complex) / len(lite_complex)
                
                full_qual = sum(r['quality_score'] for r in full_complex) / len(full_complex)
                lite_qual = sum(r['quality_score'] for r in lite_complex) / len(lite_complex)
                
                time_imp = (full_time - lite_time) / full_time * 100 if full_time > 0 else 0
                qual_change = (lite_qual - full_qual) * 100
                
                print(f"  {complexity.upper()}复杂度:")
                print(f"    速度提升: {time_imp:+.1f}%")
                print(f"    质量变化: {qual_change:+.1f}%")
        
        # 综合建议
        print(f"\n💡 测试结论:")
        
        if speed_improvement > 15 and abs(quality_change) < 20:
            print("✅ 推荐轻量版")
            print("  理由: 显著性能提升，质量损失可控")
        elif quality_change < -25:
            print("⚠️ 推荐完整版")
            print("  理由: 轻量版质量损失较大")
        elif speed_improvement > 10:
            print("🎯 推荐场景化使用")
            print("  简单任务用轻量版，复杂任务用完整版")
        else:
            print("🤔 建议扩大测试样本")
            print("  当前差异不够明显，需要更多数据")
        
        # 保存报告
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "speed_improvement_pct": speed_improvement,
                "quality_change_pct": quality_change,
                "full_version_avg_time": full_avg_time,
                "lite_version_avg_time": lite_avg_time,
                "full_version_avg_quality": full_avg_quality,
                "lite_version_avg_quality": lite_avg_quality
            },
            "detailed_results": results
        }
        
        report_file = f"quick_version_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细报告已保存: {report_file}")

async def main():
    tester = QuickVersionTester()
    await tester.run_quick_comparison()

if __name__ == "__main__":
    asyncio.run(main())