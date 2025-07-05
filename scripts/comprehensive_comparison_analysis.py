#!/usr/bin/env python3
"""
全面对比分析脚本
比较所有问题的xDAN-V2、DeepSeek和标准答案，生成详细CSV报告
"""

import json
import csv
import os
import sys
from datetime import datetime
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# xDAN-V2系统提示
XDAN_V2_SYSTEM_PROMPT = """你是一个专业的金融API技术专家，专门解答智信平台API文档相关问题。

回答要求：
1. 基于文档内容准确回答
2. 保持技术细节的精确性
3. 提供完整全面的信息
4. 使用清晰的结构组织答案
"""

async def get_xdan_v2_answer_with_rag(question: str, dataset_ids: List[str]) -> tuple:
    """获取xDAN-V2答案和RAG召回内容"""
    try:
        s3_service = get_default_service()
        enhanced_question = f"{XDAN_V2_SYSTEM_PROMPT}\n\n问题：{question}\n\n请基于API文档内容回答："
        
        all_chunks = []
        final_answer = None
        
        async for res in s3_service.ask(
            question=enhanced_question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            if isinstance(res, dict):
                if 'chunks' in res:
                    all_chunks.extend(res['chunks'])
                if 'workflow_completed' in res and res['workflow_completed']:
                    final_answer = res.get('final_answer', '')
                    break
        
        rag_content = format_rag_content(all_chunks)
        return final_answer or "生成失败", rag_content
            
    except Exception as e:
        return "生成失败", f"检索错误: {str(e)}"


def format_rag_content(chunks: List[Dict]) -> str:
    """格式化RAG内容"""
    if not chunks:
        return "未召回到相关内容"
    
    formatted_parts = []
    for i, chunk in enumerate(chunks, 1):
        content = chunk.get('content', '')
        score = chunk.get('score', 0)
        formatted_parts.append(f"【文档{i}】(相关度: {score:.2f})\n{content}")
    
    return "\n\n".join(formatted_parts)


def analyze_differences(xdan_answer: str, standard_answer: str) -> Dict[str, str]:
    """分析xDAN-V2与标准答案的差异"""
    differences = {
        "completeness": "",
        "accuracy": "",
        "detail_level": "",
        "missing_info": "",
        "extra_info": "",
        "overall_assessment": ""
    }
    
    # 长度对比
    xdan_len = len(xdan_answer) if xdan_answer else 0
    std_len = len(standard_answer) if standard_answer else 0
    
    if xdan_len > std_len * 1.5:
        differences["detail_level"] = "xDAN-V2提供了更详细的解释"
    elif xdan_len < std_len * 0.7:
        differences["detail_level"] = "xDAN-V2回答过于简略"
    else:
        differences["detail_level"] = "详细程度适中"
    
    # 关键信息提取
    xdan_lower = xdan_answer.lower() if xdan_answer else ""
    std_lower = standard_answer.lower() if standard_answer else ""
    
    # 检查关键技术术语
    key_terms = extract_key_terms(standard_answer)
    missing_terms = []
    for term in key_terms:
        if term.lower() not in xdan_lower:
            missing_terms.append(term)
    
    if missing_terms:
        differences["missing_info"] = f"缺少关键信息: {', '.join(missing_terms)}"
    else:
        differences["missing_info"] = "包含了标准答案的关键信息"
    
    # 检查额外信息
    if "文档" in xdan_answer or "根据" in xdan_answer:
        differences["extra_info"] = "提供了文档引用和依据说明"
    elif xdan_len > std_len * 1.2:
        differences["extra_info"] = "包含了额外的技术细节或背景信息"
    else:
        differences["extra_info"] = "基本与标准答案一致"
    
    # 准确性评估
    if "生成失败" in xdan_answer or "未找到" in xdan_answer:
        differences["accuracy"] = "无法生成有效答案"
    elif any(term in xdan_answer for term in key_terms):
        differences["accuracy"] = "技术要点基本准确"
    else:
        differences["accuracy"] = "可能存在准确性问题"
    
    # 完整性评估
    if "？" in standard_answer:
        questions = standard_answer.count("？")
        if questions > 1:
            differences["completeness"] = "多部分问题，需检查是否全部回答"
        else:
            differences["completeness"] = "单一问题，回答相对完整"
    else:
        differences["completeness"] = "回答了主要问题"
    
    # 整体评估
    if "生成失败" in xdan_answer:
        differences["overall_assessment"] = "❌ 生成失败"
    elif differences["missing_info"].startswith("缺少"):
        differences["overall_assessment"] = "⚠️ 信息不完整"
    elif differences["detail_level"] == "xDAN-V2提供了更详细的解释":
        differences["overall_assessment"] = "✅ 详细且准确"
    else:
        differences["overall_assessment"] = "✅ 基本满足要求"
    
    return differences


def extract_key_terms(text: str) -> List[str]:
    """提取关键术语"""
    import re
    
    terms = []
    
    # 提取接口名
    api_pattern = r'`(\w+)`'
    terms.extend(re.findall(api_pattern, text))
    
    # 提取系统名
    system_pattern = r'(ice-\w+-app)'
    terms.extend(re.findall(system_pattern, text))
    
    # 提取参数值和状态
    value_patterns = [
        r'(\d{2}-\w+)',  # 00-等额本金
        r'(yyyyMMddHHmmss)',  # 时间格式
        r'(status\s*=\s*[A-Z])',  # 状态值
        r'(repayStatus\s*=\s*[A-Z])'  # 还款状态
    ]
    
    for pattern in value_patterns:
        terms.extend(re.findall(pattern, text))
    
    # 关键词
    keywords = ['必填', '可选', '成功', '失败', '处理中', '循环额度', '一次性额度', '撞库', '绑卡', '批扣']
    for keyword in keywords:
        if keyword in text:
            terms.append(keyword)
    
    return list(set(terms))  # 去重


async def process_all_questions():
    """处理所有问题并生成对比报告"""
    
    # 读取原始问题文件
    original_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json'
    with open(original_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # 读取DeepSeek结果文件
    deepseek_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_DeepSeek_batch_4_20250703_152420.json'
    deepseek_data = {}
    
    try:
        with open(deepseek_file, 'r', encoding='utf-8') as f:
            deepseek_list = json.load(f)
            for item in deepseek_list:
                deepseek_data[item.get('index', 0)] = item
    except FileNotFoundError:
        print("⚠️ DeepSeek结果文件未找到，将使用空数据")
    
    print(f"📊 开始处理 {len(questions_data)} 个问题")
    
    results = []
    dataset_ids = [DEFAULT_DATASET_ID]
    
    for i, qa_item in enumerate(questions_data, 1):
        print(f"\n{'='*60}")
        print(f"处理问题 {i}/{len(questions_data)}")
        
        question = qa_item.get('question', '')
        standard_answer = qa_item.get('answer_correct', '')
        
        print(f"问题: {question[:50]}...")
        
        # 获取xDAN-V2答案和RAG内容
        try:
            xdan_answer, xdan_rag = await get_xdan_v2_answer_with_rag(question, dataset_ids)
            print(f"✅ xDAN-V2生成完成")
        except Exception as e:
            xdan_answer = f"生成错误: {str(e)}"
            xdan_rag = "检索失败"
            print(f"❌ xDAN-V2生成失败: {e}")
        
        # 获取DeepSeek答案
        deepseek_item = deepseek_data.get(i, {})
        deepseek_answer = deepseek_item.get('deepseek-rag-system', '无DeepSeek答案')
        
        # 分析差异
        differences = analyze_differences(xdan_answer, standard_answer)
        
        # 构建结果记录
        result = {
            'index': i,
            'question': question,
            'standard_answer': standard_answer,
            'xdan_v2_answer': xdan_answer,
            'xdan_v2_rag': xdan_rag,
            'deepseek_answer': deepseek_answer,
            'difference_completeness': differences['completeness'],
            'difference_accuracy': differences['accuracy'],
            'difference_detail_level': differences['detail_level'],
            'difference_missing_info': differences['missing_info'],
            'difference_extra_info': differences['extra_info'],
            'overall_assessment': differences['overall_assessment']
        }
        
        results.append(result)
        print(f"评估结果: {differences['overall_assessment']}")
        
        # 延迟避免API限制
        await asyncio.sleep(1)
    
    return results


def save_to_csv(results: List[Dict], filename: str):
    """保存结果到CSV文件"""
    
    csv_columns = [
        'index',
        'question',
        'standard_answer',
        'xdan_v2_answer',
        'xdan_v2_rag',
        'deepseek_answer',
        'difference_completeness',
        'difference_accuracy', 
        'difference_detail_level',
        'difference_missing_info',
        'difference_extra_info',
        'overall_assessment'
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✅ CSV文件已保存: {filename}")


def generate_summary_report(results: List[Dict]) -> Dict:
    """生成汇总报告"""
    total = len(results)
    
    # 统计评估结果
    excellent = sum(1 for r in results if '✅ 详细且准确' in r['overall_assessment'])
    good = sum(1 for r in results if '✅ 基本满足要求' in r['overall_assessment'])
    warning = sum(1 for r in results if '⚠️' in r['overall_assessment'])
    failed = sum(1 for r in results if '❌' in r['overall_assessment'])
    
    # RAG召回成功率
    rag_success = sum(1 for r in results if '未召回到相关内容' not in r['xdan_v2_rag'] and '检索失败' not in r['xdan_v2_rag'])
    
    summary = {
        'total_questions': total,
        'excellent_answers': f"{excellent} ({excellent/total:.1%})",
        'good_answers': f"{good} ({good/total:.1%})",
        'warning_answers': f"{warning} ({warning/total:.1%})",
        'failed_answers': f"{failed} ({failed/total:.1%})",
        'rag_success_rate': f"{rag_success} ({rag_success/total:.1%})"
    }
    
    return summary


async def main():
    """主函数"""
    print("🚀 开始全面对比分析")
    print("📊 比较xDAN-V2、DeepSeek和标准答案")
    print("🔍 包含RAG召回内容和详细差异分析")
    
    # 处理所有问题
    results = await process_all_questions()
    
    # 生成CSV文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/全面对比分析结果_{timestamp}.csv'
    save_to_csv(results, csv_filename)
    
    # 生成汇总报告
    summary = generate_summary_report(results)
    
    print(f"\n{'='*60}")
    print("📊 汇总统计:")
    print(f"   - 总问题数: {summary['total_questions']}")
    print(f"   - 优秀答案: {summary['excellent_answers']}")
    print(f"   - 良好答案: {summary['good_answers']}")
    print(f"   - 需改进答案: {summary['warning_answers']}")
    print(f"   - 失败答案: {summary['failed_answers']}")
    print(f"   - RAG召回成功率: {summary['rag_success_rate']}")
    
    # 保存汇总报告
    summary_file = f'/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/汇总报告_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'summary': summary,
            'detailed_results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 详细结果已保存到: {csv_filename}")
    print(f"📁 汇总报告已保存到: {summary_file}")


if __name__ == "__main__":
    asyncio.run(main())