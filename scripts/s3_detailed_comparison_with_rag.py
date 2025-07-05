#!/usr/bin/env python3
"""
S3 JSON问答处理脚本 - 基于召回内容的详细对比评价版本
记录召回的RAG内容，并基于召回内容进行质量评估
"""

import json
import os
import sys
from datetime import datetime
import asyncio
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# xDAN-V2优化的系统提示
XDAN_V2_SYSTEM_PROMPT = """你是一个专业的金融API技术专家，专门解答智信平台API文档相关问题。

回答要求：
1. **精确性第一**：确保所有技术细节准确无误，包括接口名、参数名、枚举值
2. **完整性**：回答要涵盖问题的所有方面，不遗漏关键信息
3. **基于文档**：严格基于文档内容回答，避免过度推测
4. **结构清晰**：使用清晰的结构组织答案
5. **实用性**：提供对开发者有实际帮助的信息

特别注意：
- 准确识别并使用文档中的技术术语
- 理解系统间的调用关系和数据流转
- 掌握各种业务场景的处理逻辑
"""

async def ask_question_with_xdan_v2_and_get_rag(question: str, dataset_ids: List[str]) -> Tuple[str, str]:
    """
    使用xDAN-V2模型进行问答，并返回答案和召回的RAG内容
    返回: (答案, RAG召回内容)
    """
    try:
        # 创建S3服务实例
        s3_service = get_default_service()
        
        # 构建增强问题
        enhanced_question = f"{XDAN_V2_SYSTEM_PROMPT}\n\n问题：{question}\n\n请基于API文档内容，给出准确、完整的技术答案："
        
        # 收集所有的RAG内容
        all_chunks = []
        final_answer = None
        
        # 使用S3服务执行问答
        async for res in s3_service.ask(
            question=enhanced_question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            # 收集检索到的chunks
            if isinstance(res, dict):
                if 'chunks' in res:
                    all_chunks.extend(res['chunks'])
                if 'workflow_completed' in res and res['workflow_completed']:
                    final_answer = res.get('final_answer', '')
                    break
        
        # 格式化RAG内容
        rag_content = format_rag_content(all_chunks)
        
        return final_answer or "生成失败", rag_content
            
    except Exception as e:
        print(f"❌ xDAN-V2服务错误: {e}")
        return "生成失败", f"检索错误: {str(e)}"


def format_rag_content(chunks: List[Dict]) -> str:
    """格式化召回的RAG内容"""
    if not chunks:
        return "未召回到相关内容"
    
    formatted_parts = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get('content', '')
        score = chunk.get('score', 0)
        source = chunk.get('source', '未知')
        
        formatted_parts.append(f"【文档{i}】(相关度: {score:.2f})\n{content}\n")
    
    return "\n".join(formatted_parts)


def evaluate_based_on_rag(generated_answer: str, correct_answer: str, rag_content: str, question: str) -> Tuple[str, float, Dict]:
    """
    基于召回的RAG内容进行评价
    返回：(评价描述, 综合得分, 详细评分字典)
    """
    if not generated_answer or generated_answer == "生成失败":
        return "❌ xDAN-V2生成失败", 0.0, {
            "RAG召回质量": 0,
            "答案准确性": 0,
            "信息利用率": 0,
            "推理合理性": 0,
            "完整性": 0,
            "表达清晰度": 0
        }
    
    # 多维度详细评分
    scores = {
        "RAG召回质量": 0,    # 0-20分
        "答案准确性": 0,     # 0-25分
        "信息利用率": 0,     # 0-15分
        "推理合理性": 0,     # 0-15分
        "完整性": 0,         # 0-15分
        "表达清晰度": 0      # 0-10分
    }
    
    generated_lower = generated_answer.lower()
    correct_lower = correct_answer.lower()
    rag_lower = rag_content.lower() if rag_content else ""
    
    # 1. RAG召回质量评估 (0-20分)
    rag_quality_points = 0
    
    if "未召回到相关内容" not in rag_content and "检索错误" not in rag_content:
        # 检查召回内容是否包含关键信息
        key_elements = extract_key_elements(correct_answer)
        found_in_rag = sum(1 for elem in key_elements if elem.lower() in rag_lower)
        
        if key_elements:
            rag_coverage = found_in_rag / len(key_elements)
            rag_quality_points = int(rag_coverage * 15)
        
        # 检查召回内容的丰富度
        if len(rag_content) > 500:
            rag_quality_points += 3
        if rag_content.count("【文档") > 2:
            rag_quality_points += 2
    
    scores["RAG召回质量"] = min(rag_quality_points, 20)
    
    # 2. 答案准确性评估 (0-25分)
    accuracy_points = 0
    
    # 检查答案是否准确反映了标准答案的关键点
    key_elements = extract_key_elements(correct_answer)
    found_elements = sum(1 for elem in key_elements if elem.lower() in generated_lower)
    
    if key_elements:
        accuracy_ratio = found_elements / len(key_elements)
        accuracy_points = int(accuracy_ratio * 20)
    
    # 检查是否有基于RAG的准确引用
    if "根据文档" in generated_answer or "文档中" in generated_answer:
        accuracy_points += 3
    if any(marker in generated_answer for marker in ["文档1", "文档2", "文档3"]):
        accuracy_points += 2
    
    scores["答案准确性"] = min(accuracy_points, 25)
    
    # 3. 信息利用率评估 (0-15分)
    utilization_points = 0
    
    # 检查答案是否有效利用了召回的信息
    if rag_content and "未召回到相关内容" not in rag_content:
        # 计算答案中包含的RAG信息比例
        rag_words = set(rag_lower.split())
        answer_words = set(generated_lower.split())
        common_words = len(rag_words & answer_words)
        
        if len(answer_words) > 0:
            utilization_ratio = common_words / len(answer_words)
            utilization_points = int(utilization_ratio * 10)
        
        # 检查是否合理组织了信息
        if len(generated_answer) > len(correct_answer):
            utilization_points += 3
        if "此外" in generated_answer or "另外" in generated_answer:
            utilization_points += 2
    
    scores["信息利用率"] = min(utilization_points, 15)
    
    # 4. 推理合理性评估 (0-15分)
    reasoning_points = 0
    
    # 检查推理标记
    reasoning_markers = ['因此', '所以', '由于', '根据', '可以推断', '表明', '说明', '意味着']
    reasoning_count = sum(1 for marker in reasoning_markers if marker in generated_answer)
    reasoning_points = min(reasoning_count * 3, 9)
    
    # 检查是否有逻辑连接
    if any(connector in generated_answer for connector in ['首先', '其次', '最后', '第一', '第二']):
        reasoning_points += 3
    
    # 检查是否承认不确定性
    if any(word in generated_answer for word in ['可能', '推测', '通常', '一般']):
        reasoning_points += 3
    
    scores["推理合理性"] = min(reasoning_points, 15)
    
    # 5. 完整性评估 (0-15分)
    completeness_points = 0
    
    # 检查是否回答了问题的所有部分
    if "？" in question:
        question_parts = question.split("？")[:-1]
        answered_parts = sum(1 for part in question_parts 
                           if any(word in generated_lower for word in extract_question_keywords(part)))
        
        if question_parts:
            completeness_ratio = answered_parts / len(question_parts)
            completeness_points = int(completeness_ratio * 10)
    
    # 检查答案长度
    if len(generated_answer) >= len(correct_answer) * 0.8:
        completeness_points += 5
    
    scores["完整性"] = min(completeness_points, 15)
    
    # 6. 表达清晰度评估 (0-10分)
    clarity_points = 0
    
    # 结构化表达
    if any(marker in generated_answer for marker in ['1.', '2.', '- ', '•', '**']):
        clarity_points += 5
    
    # 段落组织
    if generated_answer.count('\n') > 2:
        clarity_points += 3
    
    # 专业术语使用
    technical_terms = ['接口', 'API', '参数', '字段', '系统', '调用']
    if sum(1 for term in technical_terms if term in generated_answer) >= 3:
        clarity_points += 2
    
    scores["表达清晰度"] = min(clarity_points, 10)
    
    # 计算总分
    total_score = sum(scores.values()) / 100
    
    # 生成详细评价
    evaluation_parts = []
    
    # RAG召回质量评价
    if scores["RAG召回质量"] >= 15:
        evaluation_parts.append("✅ RAG召回优秀")
    elif scores["RAG召回质量"] >= 10:
        evaluation_parts.append("⚠️ RAG召回一般")
    else:
        evaluation_parts.append("❌ RAG召回不足")
    
    # 答案准确性评价
    if scores["答案准确性"] >= 20:
        evaluation_parts.append("✅ 答案准确")
    elif scores["答案准确性"] >= 15:
        evaluation_parts.append("⚠️ 答案基本准确")
    else:
        evaluation_parts.append("❌ 答案不准确")
    
    # 信息利用率评价
    if scores["信息利用率"] >= 12:
        evaluation_parts.append("✅ 信息利用充分")
    elif scores["信息利用率"] >= 8:
        evaluation_parts.append("⚠️ 信息利用一般")
    else:
        evaluation_parts.append("❌ 信息利用不足")
    
    # 最终评级
    if total_score >= 0.85:
        grade = "优秀"
        emoji = "🌟"
    elif total_score >= 0.70:
        grade = "良好"
        emoji = "✅"
    elif total_score >= 0.50:
        grade = "一般"
        emoji = "⚠️"
    else:
        grade = "需改进"
        emoji = "❌"
    
    evaluation = f"{emoji} xDAN-V2 {grade} | 得分{total_score:.1%} | {' | '.join(evaluation_parts)}"
    
    return evaluation, total_score, scores


def extract_key_elements(text: str) -> List[str]:
    """提取文本中的关键元素"""
    import re
    
    elements = []
    
    # 提取接口名
    api_pattern = r'`(\w+)`'
    elements.extend(re.findall(api_pattern, text))
    
    # 提取参数值
    value_pattern = r'(\d{2}[-\s]?\w+)'
    elements.extend(re.findall(value_pattern, text))
    
    # 提取系统名
    system_pattern = r'(ice-\w+-app)'
    elements.extend(re.findall(system_pattern, text))
    
    # 提取关键词
    keywords = ['必填', '可选', '成功', '失败', '处理中', '循环额度', '一次性额度']
    for keyword in keywords:
        if keyword in text:
            elements.append(keyword)
    
    return elements


def extract_question_keywords(question_part: str) -> List[str]:
    """提取问题中的关键词"""
    stop_words = ['的', '是', '有', '在', '和', '与', '或', '但', '如果', '那么']
    words = question_part.split()
    keywords = [w for w in words if len(w) > 1 and w not in stop_words]
    return keywords


async def process_and_compare(json_file_path: str):
    """处理JSON文件并进行详细对比"""
    print(f"📖 读取JSON文件: {json_file_path}")
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"📊 共找到 {len(qa_data)} 个问题")
    
    dataset_ids = [DEFAULT_DATASET_ID]
    results = []
    
    for i, qa_item in enumerate(qa_data, 1):
        print(f"\n{'='*80}")
        print(f"处理第 {i}/{len(qa_data)} 个问题")
        
        question = qa_item.get('question', '')
        correct_answer = qa_item.get('answer_correct', '')
        deepseek_answer = qa_item.get('deepseek-rag-system', '')
        
        if not question:
            continue
        
        print(f"\n📝 问题: {question}")
        print(f"\n✅ 标准答案: {correct_answer}")
        
        # 使用xDAN-V2生成答案并获取RAG内容
        print(f"\n🤖 使用xDAN-V2生成答案...")
        xdan_v2_answer, xdan_v2_rag = await ask_question_with_xdan_v2_and_get_rag(question, dataset_ids)
        
        if xdan_v2_answer and xdan_v2_answer != "生成失败":
            print(f"✅ xDAN-V2生成成功")
            print(f"📚 召回文档数: {xdan_v2_rag.count('【文档')}")
        else:
            print(f"❌ xDAN-V2生成失败")
        
        # 基于RAG内容评价xDAN-V2
        xdan_evaluation, xdan_score, xdan_scores = evaluate_based_on_rag(
            xdan_v2_answer, correct_answer, xdan_v2_rag, question
        )
        
        # 评价DeepSeek（如果存在）
        if deepseek_answer:
            # DeepSeek没有RAG内容，使用传统评价
            deepseek_evaluation, deepseek_score, deepseek_scores = evaluate_based_on_rag(
                deepseek_answer, correct_answer, "", question
            )
        else:
            deepseek_evaluation = "无DeepSeek答案"
            deepseek_score = 0
            deepseek_scores = {}
        
        # 构建详细结果
        result_item = {
            'index': qa_item.get('index', i),
            'question': question,
            'answer_correct': correct_answer,
            'xdan-v2-rag': xdan_v2_rag,  # 新增：召回的RAG内容
            'xdan-v2-answer': xdan_v2_answer,
            'xdan-v2-evaluation': xdan_evaluation,
            'xdan-v2-score': xdan_score,
            'xdan-v2-detailed-scores': xdan_scores,
            'deepseek-answer': deepseek_answer,
            'deepseek-evaluation': deepseek_evaluation,
            'deepseek-score': deepseek_score,
            'deepseek-detailed-scores': deepseek_scores,
            'comparison': generate_comparison(xdan_score, deepseek_score, xdan_scores, deepseek_scores)
        }
        
        results.append(result_item)
        
        # 打印详细对比
        print(f"\n📊 评价结果:")
        print(f"xDAN-V2: {xdan_evaluation}")
        print(f"DeepSeek: {deepseek_evaluation}")
        print(f"\n🔍 详细得分对比:")
        print(f"{'维度':<15} {'xDAN-V2':>10} {'DeepSeek':>10} {'差异':>10}")
        print("-" * 50)
        
        # 显示所有维度的对比
        all_dimensions = set(list(xdan_scores.keys()) + list(deepseek_scores.keys()))
        for dimension in all_dimensions:
            xdan_val = xdan_scores.get(dimension, 0)
            deepseek_val = deepseek_scores.get(dimension, 0)
            diff = xdan_val - deepseek_val
            diff_str = f"+{diff}" if diff > 0 else str(diff)
            print(f"{dimension:<15} {xdan_val:>10} {deepseek_val:>10} {diff_str:>10}")
        
        # 添加延迟
        await asyncio.sleep(2)
    
    return results


def generate_comparison(xdan_score: float, deepseek_score: float, 
                       xdan_scores: Dict, deepseek_scores: Dict) -> str:
    """生成对比结论"""
    diff = xdan_score - deepseek_score
    
    if abs(diff) < 0.05:
        comparison = "两者表现相当"
    elif diff > 0.2:
        comparison = "xDAN-V2显著优于DeepSeek"
    elif diff > 0:
        comparison = "xDAN-V2略优于DeepSeek"
    elif diff < -0.2:
        comparison = "DeepSeek显著优于xDAN-V2"
    else:
        comparison = "DeepSeek略优于xDAN-V2"
    
    # 找出最大差异的维度
    max_diff_dimension = ""
    max_diff_value = 0
    
    all_dimensions = set(list(xdan_scores.keys()) + list(deepseek_scores.keys()))
    for dimension in all_dimensions:
        xdan_val = xdan_scores.get(dimension, 0)
        deepseek_val = deepseek_scores.get(dimension, 0)
        diff_val = abs(xdan_val - deepseek_val)
        if diff_val > max_diff_value:
            max_diff_value = diff_val
            max_diff_dimension = dimension
    
    if max_diff_dimension:
        comparison += f"，主要差异在{max_diff_dimension}"
    
    return comparison


async def main():
    """主函数"""
    # 使用DeepSeek的结果文件作为输入
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_DeepSeek_batch_4_20250703_152420.json'
    
    print("🚀 开始xDAN-V2与DeepSeek详细对比评估（基于RAG内容）")
    print(f"📊 使用模型: {os.getenv('S3_GENERATOR_MODEL_NAME')}")
    print("🔍 启用基于RAG内容的详细评价模式")
    
    # 处理并对比
    results = await process_and_compare(json_file)
    
    # 保存详细结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_RAG详细对比结果_{}.json'.format(timestamp)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成统计报告
    total = len(results)
    xdan_wins = sum(1 for r in results if r['xdan-v2-score'] > r['deepseek-score'])
    deepseek_wins = sum(1 for r in results if r['deepseek-score'] > r['xdan-v2-score'])
    ties = total - xdan_wins - deepseek_wins
    
    avg_xdan_score = sum(r['xdan-v2-score'] for r in results) / max(total, 1)
    avg_deepseek_score = sum(r['deepseek-score'] for r in results) / max(total, 1)
    
    # RAG召回质量统计
    avg_rag_quality = sum(r['xdan-v2-detailed-scores'].get('RAG召回质量', 0) for r in results) / max(total, 1)
    
    print(f"\n{'='*80}")
    print(f"📊 基于RAG内容的详细对比统计:")
    print(f"   - 总问题数: {total}")
    print(f"   - xDAN-V2胜出: {xdan_wins} ({xdan_wins/total:.1%})")
    print(f"   - DeepSeek胜出: {deepseek_wins} ({deepseek_wins/total:.1%})")
    print(f"   - 平局: {ties} ({ties/total:.1%})")
    print(f"   - xDAN-V2平均得分: {avg_xdan_score:.1%}")
    print(f"   - DeepSeek平均得分: {avg_deepseek_score:.1%}")
    print(f"   - xDAN-V2平均RAG召回质量: {avg_rag_quality:.1f}/20")
    print(f"\n📁 详细对比结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())