#!/usr/bin/env python3
"""
三版本Agent全面对比测试
使用完整50个真实问题进行debug级别的详细测试
"""

import json
import logging
import sys
import os
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Any
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.clients.enhanced_litellm_client import EnhancedLiteLLMClient

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'three_version_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

# 抑制外部库日志
for logger in ['httpx', 'openai', 'LiteLLM', 'urllib3']:
    logging.getLogger(logger).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class ComprehensiveThreeVersionTester:
    def __init__(self):
        self.client = EnhancedLiteLLMClient()
        self.test_results = {
            "original": [],
            "lite": [], 
            "full": []
        }
        self.test_config = {
            "original": {
                "name": "原版(S3-RAG-RL)",
                "file": "s3-rag-rl/versions/original/agent_system.txt",
                "description": "基础RAG检索助手"
            },
            "lite": {
                "name": "轻量版(Unified Lite)",
                "file": "deepsearch/versions/v1.2.1/unified_agent_lite.txt", 
                "description": "统一搜索代理"
            },
            "full": {
                "name": "完备版(Unified Full)",
                "file": "deepsearch/versions/v1.2.1/unified_agent_system.txt",
                "description": "专业搜索智能体"
            }
        }
        
    async def run_comprehensive_test(self):
        """运行全面的三版本对比测试"""
        
        print("🔬 三版本Agent全面对比测试")
        print("目标: 使用50个真实问题全面对比三个版本的表现")
        print("="*100)
        
        # 加载完整50个测试问题
        test_questions = await self._load_all_test_questions()
        
        print(f"📝 测试问题总数: {len(test_questions)}个")
        print(f"🎯 测试版本: {len(self.test_config)}个")
        print(f"📊 预计测试用例: {len(test_questions) * len(self.test_config)}个")
        
        # 逐版本测试
        for version_key, config in self.test_config.items():
            print(f"\n{'='*80}")
            print(f"🔄 测试版本: {config['name']}")
            print(f"📁 Prompt文件: {config['file']}")
            print(f"📝 版本描述: {config['description']}")
            print(f"{'='*80}")
            
            await self._test_single_version(version_key, config, test_questions)
            
            # 版本间休息，避免API限制
            print(f"\n⏱️ 版本测试完成，休息10秒...")
            await asyncio.sleep(10)
        
        # 生成综合分析报告
        self._generate_comprehensive_report()
    
    async def _load_all_test_questions(self) -> List[Dict]:
        """加载全部50个测试问题"""
        try:
            with open('questions/search/test_sample_50.json', 'r', encoding='utf-8') as f:
                all_questions = json.load(f)
            
            logger.info(f"成功加载 {len(all_questions)} 个测试问题")
            
            # 为每个问题添加元数据
            processed_questions = []
            for i, question_data in enumerate(all_questions):
                processed_question = {
                    "id": question_data.get("id", f"test_{i}"),
                    "index": i,
                    "category": question_data.get("category", "未知"),
                    "question": question_data.get("question", ""),
                    "target": question_data.get("target", ""),
                    "complexity": self._assess_question_complexity(question_data),
                    "estimated_tokens": len(question_data.get("question", "")) * 4,  # 粗略估算
                    "original_data": question_data
                }
                processed_questions.append(processed_question)
            
            # 按复杂度分组统计
            complexity_stats = {}
            for q in processed_questions:
                complexity = q['complexity']
                complexity_stats[complexity] = complexity_stats.get(complexity, 0) + 1
            
            logger.info(f"问题复杂度分布: {complexity_stats}")
            
            return processed_questions
            
        except FileNotFoundError:
            logger.error("测试问题文件未找到，使用备用问题集")
            return self._get_fallback_questions()
    
    def _assess_question_complexity(self, question_data: Dict) -> str:
        """详细评估问题复杂度"""
        question = question_data.get("question", "")
        category = question_data.get("category", "")
        target = question_data.get("target", "")
        
        # 复杂度评估指标
        high_indicators = [
            "深度分析", "预测", "对比分析", "综合评估", "ROE", "战略分析",
            "系统性", "多维度", "跨领域", "建模", "算法", "架构设计"
        ]
        
        medium_indicators = [
            "分析", "比较", "趋势", "影响", "市场", "技术", "发展",
            "评估", "研究", "报告", "数据", "统计"
        ]
        
        low_indicators = [
            "查找", "列出", "简单", "基本", "什么是", "介绍",
            "定义", "概述", "说明"
        ]
        
        text_to_check = f"{question} {category} {target}".lower()
        
        # 计算复杂度得分
        high_score = sum(1 for indicator in high_indicators if indicator in text_to_check)
        medium_score = sum(1 for indicator in medium_indicators if indicator in text_to_check)
        low_score = sum(1 for indicator in low_indicators if indicator in text_to_check)
        
        # 长度因子
        length_factor = len(question) / 100  # 标准化
        
        # 综合评分
        if high_score >= 2 or (high_score >= 1 and length_factor > 1.5):
            return "high"
        elif medium_score >= 2 or (medium_score >= 1 and high_score >= 1):
            return "medium"
        elif low_score >= 1:
            return "low"
        else:
            return "medium"  # 默认中等
    
    def _get_fallback_questions(self) -> List[Dict]:
        """备用问题集"""
        return [
            {
                "id": "fallback_1",
                "index": 0,
                "category": "数据分析",
                "question": "请对新能源汽车行业的ROE进行深度分析",
                "complexity": "high",
                "target": "测试复杂分析能力",
                "estimated_tokens": 200
            }
        ]
    
    async def _test_single_version(self, version_key: str, config: Dict, questions: List[Dict]):
        """测试单个版本"""
        
        version_name = config['name']
        
        # 加载prompt
        prompt_path = f"prompts/{config['file']}"
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            logger.info(f"成功加载prompt: {prompt_path} ({len(system_prompt)}字符)")
        except FileNotFoundError:
            logger.error(f"Prompt文件未找到: {prompt_path}")
            return
        
        version_results = []
        failed_count = 0
        
        for i, question_data in enumerate(questions, 1):
            question_id = question_data['id']
            question = question_data['question']
            complexity = question_data['complexity']
            
            print(f"\n[{i}/{len(questions)}] {version_name} - {complexity.upper()}")
            print(f"📝 {question_data['category']}: {question[:60]}...")
            
            logger.debug(f"开始测试问题 {question_id}: {question}")
            
            # 创建测试场景
            test_scenario = self._create_realistic_test_scenario(question_data)
            
            # 执行测试
            start_time = time.time()
            
            try:
                result = await self._execute_single_test(
                    system_prompt, test_scenario, question_data, version_key, version_name
                )
                
                result['execution_time'] = time.time() - start_time
                result['success'] = True
                
                version_results.append(result)
                
                # 输出测试结果
                self._print_test_result(result, i, len(questions))
                
                logger.info(f"问题 {question_id} 测试成功: {result['execution_time']:.1f}s")
                
            except Exception as e:
                failed_count += 1
                error_result = {
                    "question_id": question_id,
                    "question": question,
                    "version": version_key,
                    "complexity": complexity,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "execution_time": time.time() - start_time,
                    "success": False,
                    "timestamp": datetime.now().isoformat()
                }
                
                version_results.append(error_result)
                
                print(f"  ❌ 测试失败: {str(e)[:100]}...")
                logger.error(f"问题 {question_id} 测试失败: {e}", exc_info=True)
            
            # 问题间休息，避免API限制
            if i % 10 == 0:  # 每10个问题休息
                print(f"  ⏱️ 已完成{i}个问题，休息5秒...")
                await asyncio.sleep(5)
        
        # 保存版本结果
        self.test_results[version_key] = version_results
        
        # 版本测试总结
        success_count = len([r for r in version_results if r.get('success')])
        print(f"\n📊 {version_name} 测试完成:")
        print(f"  ✅ 成功: {success_count}/{len(questions)}")
        print(f"  ❌ 失败: {failed_count}/{len(questions)}")
        print(f"  📈 成功率: {success_count/len(questions)*100:.1f}%")
    
    def _create_realistic_test_scenario(self, question_data: Dict) -> str:
        """创建真实的测试场景"""
        question = question_data['question']
        category = question_data['category']
        complexity = question_data['complexity']
        
        # 根据问题类别生成相应的搜索结果
        if '财务' in category or 'ROE' in question or '数据分析' in category:
            search_results = """
1. 上市公司财务数据平台 - 详细的财务报表和比率分析
   URL: https://finance.sina.com.cn/stock/finance/
   摘要: 提供完整的ROE历史数据，包含同行对比和趋势分析

2. 中信证券研究报告 - 新能源汽车行业深度分析
   URL: https://research.citics.com/reports/industry/automotive
   摘要: 专业分析师对行业ROE驱动因素的详细解读和预测模型

3. Wind金融终端数据 - 行业财务指标数据库
   URL: https://www.wind.com.cn/industry-metrics
   摘要: 历史财务数据完整，支持多维度分析和自定义计算

4. 国泰君安研究所报告 - ROE影响因素分析
   URL: https://www.gtja.com/research/industry-analysis
   摘要: 从杜邦分析角度深入解析ROE构成和变动原因
"""
        
        elif '技术' in category or '系统' in question or '架构' in question:
            search_results = """
1. 技术架构设计最佳实践 - 企业级系统设计指南
   URL: https://martinfowler.com/architecture/
   摘要: Martin Fowler等专家的权威架构设计理念和实践案例

2. Spring Boot官方文档 - 微服务架构实现指南
   URL: https://spring.io/guides/microservices/
   摘要: 官方提供的微服务架构模式、配置和最佳实践

3. AWS架构中心 - 云原生系统设计模式
   URL: https://aws.amazon.com/architecture/
   摘要: 企业级云架构参考模型，包含数据处理和监控系统设计

4. GitHub开源项目 - 在线学习系统实现案例
   URL: https://github.com/topics/online-learning-platform
   摘要: 实际项目代码和架构实现，可参考具体技术选型和设计
"""
        
        elif '医疗' in category or '健康' in category:
            search_results = """
1. 中华医学会官方指南 - 阿尔茨海默病诊疗规范
   URL: https://www.cma.org.cn/guidelines/alzheimer
   摘要: 权威医学机构发布的标准诊疗指南和循证医学证据

2. 新英格兰医学杂志 - 阿尔茨海默病最新研究
   URL: https://www.nejm.org/alzheimer-research
   摘要: 顶级医学期刊的最新研究成果和治疗方案进展

3. 国家卫健委官方文件 - 老年痴呆防治策略
   URL: https://www.nhc.gov.cn/elderly-care/policies
   摘要: 国家政策层面的防治策略和公共卫生措施

4. Cochrane系统评价 - 阿尔茨海默病干预措施
   URL: https://www.cochranelibrary.com/alzheimer-interventions
   摘要: 基于循证医学的系统评价和meta分析结果
"""
        
        else:
            search_results = """
1. 官方权威机构报告 - 政府部门或国际组织发布
   URL: https://official-source.gov/reports
   摘要: 权威性最高的官方数据和政策解读

2. 知名咨询公司研究 - 专业市场分析报告
   URL: https://consulting-firm.com/industry-reports
   摘要: 专业分析师的深度市场调研和商业洞察

3. 学术期刊论文 - 同行评议的研究成果
   URL: https://academic-journal.com/peer-reviewed
   摘要: 经过同行评议的学术研究，理论基础扎实

4. 行业领先媒体 - 专业记者的深度报道
   URL: https://industry-media.com/in-depth
   摘要: 实地调研的一手资料和行业内部观点
"""
        
        return f"""
问题: {question}

类别: {category}
复杂度: {complexity}

候选搜索结果:
{search_results}

请根据问题需求，分析这些搜索结果的价值，选择最合适的信息源，并制定后续搜索策略。
"""
    
    async def _execute_single_test(self, system_prompt: str, test_scenario: str, 
                                 question_data: Dict, version_key: str, version_name: str) -> Dict:
        """执行单个测试用例"""
        
        start_time = time.time()
        
        # 调用LLM (增加超时和重试机制)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await self.client.chat_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": test_scenario}
                    ],
                    temperature=0.1,
                    max_tokens=1000,  # 限制长度保证测试效率
                    timeout=60  # 增加超时到60秒
                )
                break
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        response_text = response.choices[0].message.content
        llm_time = time.time() - start_time
        
        # 详细分析响应
        analysis_start = time.time()
        analysis = self._analyze_response_comprehensive(response_text, version_key)
        analysis_time = time.time() - analysis_start
        
        # 构建结果
        result = {
            "question_id": question_data['id'],
            "question": question_data['question'],
            "category": question_data['category'],
            "complexity": question_data['complexity'],
            "version": version_key,
            "version_name": version_name,
            
            # 响应信息
            "response_text": response_text,
            "response_length": len(response_text),
            "response_lines": len(response_text.split('\n')),
            
            # 时间分析
            "llm_response_time": llm_time,
            "analysis_time": analysis_time,
            "total_time": llm_time + analysis_time,
            
            # 质量分析
            "quality_analysis": analysis,
            "overall_quality_score": analysis['overall_score'],
            
            # 格式分析
            "format_compliance": analysis['format_compliance'],
            "has_thinking": analysis['has_thinking'],
            "has_decision_tags": analysis['has_decision_tags'],
            
            # 内容分析
            "content_depth": analysis['content_depth'],
            "decision_quality": analysis['decision_quality'],
            "professional_level": analysis['professional_level'],
            
            # 元数据
            "timestamp": datetime.now().isoformat(),
            "test_metadata": {
                "prompt_length": len(system_prompt),
                "scenario_length": len(test_scenario),
                "estimated_tokens": question_data.get('estimated_tokens', 0)
            }
        }
        
        return result
    
    def _analyze_response_comprehensive(self, response: str, version_key: str) -> Dict:
        """全面分析响应质量"""
        
        analysis = {
            "format_compliance": 0.0,
            "content_depth": 0.0,
            "decision_quality": 0.0,
            "professional_level": 0.0,
            "has_thinking": False,
            "has_decision_tags": False,
            "overall_score": 0.0
        }
        
        # 1. 格式合规性分析 (25%)
        format_score = 0.0
        format_indicators = []
        
        if '<thinking>' in response and '</thinking>' in response:
            format_score += 0.4
            analysis['has_thinking'] = True
            format_indicators.append("思考过程完整")
        
        if '<search_complete>' in response:
            format_score += 0.3
            format_indicators.append("搜索状态明确")
        
        if '<important_urls>' in response or '<important_info>' in response:
            format_score += 0.2
            analysis['has_decision_tags'] = True
            format_indicators.append("URL选择明确")
        
        if '<next_query>' in response or '<query>' in response:
            format_score += 0.1
            format_indicators.append("查询生成")
        
        analysis['format_compliance'] = min(format_score, 1.0)
        
        # 2. 内容深度分析 (25%)
        depth_score = 0.0
        depth_indicators = []
        
        thinking_content = ""
        if '<thinking>' in response and '</thinking>' in response:
            thinking_content = response.split('<thinking>')[1].split('</thinking>')[0]
        
        # 分析深度指标
        analysis_terms = ['分析', '评估', '比较', '考虑', 'analysis', 'evaluate', 'consider']
        if any(term in response.lower() for term in analysis_terms):
            depth_score += 0.3
            depth_indicators.append("包含分析思考")
        
        if len(thinking_content) > 100:
            depth_score += 0.2
            depth_indicators.append("思考过程详细")
        
        if any(term in response for term in ['策略', '方法', 'approach', 'strategy']):
            depth_score += 0.2
            depth_indicators.append("包含策略思考")
        
        if len(response) > 300:
            depth_score += 0.2
            depth_indicators.append("内容充实")
        
        reasoning_indicators = ['因为', '由于', '基于', 'because', 'since', 'based on']
        if any(term in response for term in reasoning_indicators):
            depth_score += 0.1
            depth_indicators.append("包含推理过程")
        
        analysis['content_depth'] = min(depth_score, 1.0)
        
        # 3. 决策质量分析 (25%)
        decision_score = 0.0
        decision_indicators = []
        
        # URL选择质量
        if 'URL' in response and ('选择' in response or 'select' in response.lower()):
            decision_score += 0.3
            decision_indicators.append("URL选择有依据")
        
        # 搜索完成判断
        if '<search_complete>' in response:
            complete_value = response.split('<search_complete>')[1].split('<')[0].lower()
            if 'true' in complete_value or 'false' in complete_value:
                decision_score += 0.2
                decision_indicators.append("搜索状态明确")
        
        # 缺口识别
        gap_terms = ['缺口', '不足', '需要', 'gap', 'missing', 'need']
        if any(term in response for term in gap_terms):
            decision_score += 0.2
            decision_indicators.append("识别信息缺口")
        
        # 优先级判断
        priority_terms = ['重要', '优先', '关键', 'important', 'priority', 'key']
        if any(term in response for term in priority_terms):
            decision_score += 0.2
            decision_indicators.append("体现优先级判断")
        
        # 逻辑连贯性
        if len(response.split('\n')) >= 5:  # 结构化程度
            decision_score += 0.1
            decision_indicators.append("逻辑结构清晰")
        
        analysis['decision_quality'] = min(decision_score, 1.0)
        
        # 4. 专业性水平分析 (25%)
        professional_score = 0.0
        professional_indicators = []
        
        # 专业术语使用
        if version_key in ['lite', 'full']:
            s3_terms = ['S3', '搜索', '选择', '综合', 'search', 'select', 'synthesize']
            if any(term in response for term in s3_terms):
                professional_score += 0.2
                professional_indicators.append("体现S3理念")
        
        # 技术术语
        tech_terms = ['权威', '相关性', '时效性', 'authority', 'relevance', 'timeliness']
        if any(term in response for term in tech_terms):
            professional_score += 0.2
            professional_indicators.append("使用专业术语")
        
        # 系统性思考
        system_terms = ['系统', '全面', '综合', 'systematic', 'comprehensive']
        if any(term in response for term in system_terms):
            professional_score += 0.2
            professional_indicators.append("体现系统性思考")
        
        # 质量标准意识
        quality_terms = ['质量', '标准', '准确', 'quality', 'standard', 'accurate']
        if any(term in response for term in quality_terms):
            professional_score += 0.2
            professional_indicators.append("质量意识")
        
        # 版本特定专业性
        if version_key == 'full':
            advanced_terms = ['策略', '框架', '评估标准', 'strategy', 'framework', 'criteria']
            if any(term in response for term in advanced_terms):
                professional_score += 0.2
                professional_indicators.append("高级专业概念")
        
        analysis['professional_level'] = min(professional_score, 1.0)
        
        # 计算综合得分
        analysis['overall_score'] = (
            analysis['format_compliance'] * 0.25 +
            analysis['content_depth'] * 0.25 +
            analysis['decision_quality'] * 0.25 +
            analysis['professional_level'] * 0.25
        )
        
        # 记录详细指标
        analysis['detailed_indicators'] = {
            "format": format_indicators,
            "depth": depth_indicators, 
            "decision": decision_indicators,
            "professional": professional_indicators
        }
        
        return analysis
    
    def _print_test_result(self, result: Dict, current: int, total: int):
        """打印测试结果"""
        print(f"  ✅ 响应时间: {result['llm_response_time']:.1f}s")
        print(f"  📏 响应长度: {result['response_length']}字符")
        print(f"  🎯 综合质量: {result['overall_quality_score']*100:.1f}%")
        print(f"  🔧 格式合规: {result['format_compliance']*100:.1f}%")
        print(f"  📊 内容深度: {result['content_depth']*100:.1f}%")
        print(f"  🎪 决策质量: {result['decision_quality']*100:.1f}%")
        print(f"  🏆 专业水平: {result['professional_level']*100:.1f}%")
    
    def _generate_comprehensive_report(self):
        """生成全面的对比分析报告"""
        
        print(f"\n{'='*100}")
        print("📊 三版本全面对比分析报告")
        print(f"{'='*100}")
        
        # 基础统计
        total_tests = sum(len(results) for results in self.test_results.values())
        successful_tests = sum(len([r for r in results if r.get('success')]) 
                             for results in self.test_results.values())
        
        print(f"📈 测试总览:")
        print(f"  总测试用例: {total_tests}")
        print(f"  成功用例: {successful_tests}")
        print(f"  总体成功率: {successful_tests/total_tests*100:.1f}%")
        
        # 按版本统计
        version_stats = {}
        for version_key, results in self.test_results.items():
            successful = [r for r in results if r.get('success')]
            if successful:
                version_stats[version_key] = {
                    "total": len(results),
                    "successful": len(successful),
                    "success_rate": len(successful) / len(results) * 100,
                    "avg_response_time": sum(r['llm_response_time'] for r in successful) / len(successful),
                    "avg_quality": sum(r['overall_quality_score'] for r in successful) / len(successful),
                    "avg_format": sum(r['format_compliance'] for r in successful) / len(successful),
                    "avg_depth": sum(r['content_depth'] for r in successful) / len(successful),
                    "avg_decision": sum(r['decision_quality'] for r in successful) / len(successful),
                    "avg_professional": sum(r['professional_level'] for r in successful) / len(successful),
                    "avg_length": sum(r['response_length'] for r in successful) / len(successful)
                }
        
        # 版本对比表
        print(f"\n📊 版本性能对比:")
        print(f"{'版本':<15} {'成功率':<8} {'平均时间':<10} {'综合质量':<10} {'格式':<8} {'深度':<8} {'决策':<8} {'专业':<8}")
        print("-" * 80)
        
        for version_key, stats in version_stats.items():
            version_name = self.test_config[version_key]['name'][:12]
            print(f"{version_name:<15} "
                  f"{stats['success_rate']:.1f}%{'':<3} "
                  f"{stats['avg_response_time']:.1f}s{'':<6} "
                  f"{stats['avg_quality']*100:.1f}%{'':<6} "
                  f"{stats['avg_format']*100:.1f}%{'':<4} "
                  f"{stats['avg_depth']*100:.1f}%{'':<4} "
                  f"{stats['avg_decision']*100:.1f}%{'':<4} "
                  f"{stats['avg_professional']*100:.1f}%{'':<4}")
        
        # 按复杂度分析
        print(f"\n📈 按问题复杂度分析:")
        
        complexity_analysis = {}
        for version_key, results in self.test_results.items():
            version_name = self.test_config[version_key]['name']
            complexity_analysis[version_name] = {}
            
            for complexity in ['low', 'medium', 'high']:
                complex_results = [r for r in results if r.get('success') and r.get('complexity') == complexity]
                if complex_results:
                    complexity_analysis[version_name][complexity] = {
                        "count": len(complex_results),
                        "avg_time": sum(r['llm_response_time'] for r in complex_results) / len(complex_results),
                        "avg_quality": sum(r['overall_quality_score'] for r in complex_results) / len(complex_results)
                    }
        
        for complexity in ['low', 'medium', 'high']:
            print(f"\n  {complexity.upper()}复杂度问题:")
            for version_name, data in complexity_analysis.items():
                if complexity in data:
                    stats = data[complexity]
                    print(f"    {version_name}: {stats['count']}题, "
                          f"时间{stats['avg_time']:.1f}s, "
                          f"质量{stats['avg_quality']*100:.1f}%")
        
        # 最佳表现分析
        print(f"\n🏆 最佳表现分析:")
        
        if version_stats:
            best_speed = min(version_stats.items(), key=lambda x: x[1]['avg_response_time'])
            best_quality = max(version_stats.items(), key=lambda x: x[1]['avg_quality'])
            best_format = max(version_stats.items(), key=lambda x: x[1]['avg_format'])
            
            print(f"  🚀 响应速度最快: {self.test_config[best_speed[0]]['name']} ({best_speed[1]['avg_response_time']:.1f}s)")
            print(f"  🎯 综合质量最高: {self.test_config[best_quality[0]]['name']} ({best_quality[1]['avg_quality']*100:.1f}%)")
            print(f"  🔧 格式规范最好: {self.test_config[best_format[0]]['name']} ({best_format[1]['avg_format']*100:.1f}%)")
        
        # 生成建议
        print(f"\n💡 使用建议:")
        
        if 'lite' in version_stats and 'full' in version_stats:
            lite_stats = version_stats['lite']
            full_stats = version_stats['full']
            
            speed_diff = (full_stats['avg_response_time'] - lite_stats['avg_response_time']) / full_stats['avg_response_time'] * 100
            quality_diff = (lite_stats['avg_quality'] - full_stats['avg_quality']) * 100
            
            if speed_diff > 15 and abs(quality_diff) < 10:
                print("  ✅ 推荐轻量版作为主力版本")
                print("     理由: 显著速度优势，质量损失可控")
            elif quality_diff < -15:
                print("  ⚠️ 推荐完备版用于复杂任务")
                print("     理由: 质量优势明显，值得额外时间成本")
            else:
                print("  🎯 推荐场景化使用策略")
                print("     简单任务用轻量版，复杂任务用完备版")
        
        # 保存详细报告
        comprehensive_report = {
            "test_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "overall_success_rate": successful_tests/total_tests*100 if total_tests > 0 else 0
            },
            "version_statistics": version_stats,
            "complexity_analysis": complexity_analysis,
            "detailed_results": self.test_results,
            "test_configuration": self.test_config
        }
        
        report_file = f"comprehensive_three_version_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 详细测试报告已保存: {report_file}")
        print(f"📋 测试日志文件: three_version_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

async def main():
    tester = ComprehensiveThreeVersionTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())