#!/usr/bin/env python3
"""
基于现有数据生成全面对比分析CSV的模拟版本
"""

import json
import csv
import os
from datetime import datetime

def analyze_differences(xdan_answer: str, standard_answer: str) -> dict:
    """分析xDAN-V2与标准答案的差异"""
    if not xdan_answer or xdan_answer == "生成失败":
        return {
            "completeness": "无法评估",
            "accuracy": "生成失败",
            "detail_level": "无内容",
            "missing_info": "完全缺失",
            "extra_info": "无",
            "overall_assessment": "❌ 生成失败"
        }
    
    xdan_len = len(xdan_answer)
    std_len = len(standard_answer)
    
    differences = {}
    
    # 详细程度分析
    if xdan_len > std_len * 1.5:
        differences["detail_level"] = "详细程度高，提供了额外解释"
    elif xdan_len < std_len * 0.7:
        differences["detail_level"] = "过于简略，缺少必要细节"
    else:
        differences["detail_level"] = "详细程度适中"
    
    # 准确性分析
    key_terms = extract_key_terms(standard_answer)
    missing_terms = []
    for term in key_terms:
        if term.lower() not in xdan_answer.lower():
            missing_terms.append(term)
    
    if len(missing_terms) == 0:
        differences["accuracy"] = "完全准确，包含所有关键信息"
    elif len(missing_terms) <= len(key_terms) * 0.3:
        differences["accuracy"] = "基本准确，少量信息缺失"
    else:
        differences["accuracy"] = "准确性不足，缺少重要信息"
    
    # 缺失信息
    if missing_terms:
        differences["missing_info"] = f"缺少: {', '.join(missing_terms[:3])}{'等' if len(missing_terms) > 3 else ''}"
    else:
        differences["missing_info"] = "包含标准答案的所有关键信息"
    
    # 额外信息
    if "文档" in xdan_answer or "根据" in xdan_answer:
        differences["extra_info"] = "提供了文档引用和依据"
    elif xdan_len > std_len * 1.2:
        differences["extra_info"] = "包含额外的技术细节和解释"
    else:
        differences["extra_info"] = "与标准答案基本一致"
    
    # 完整性
    if "？" in standard_answer and standard_answer.count("？") > 1:
        differences["completeness"] = "多部分问题，需全面回答"
    else:
        differences["completeness"] = "回答了主要问题"
    
    # 整体评估
    if missing_terms and len(missing_terms) > len(key_terms) * 0.5:
        differences["overall_assessment"] = "❌ 信息缺失严重"
    elif missing_terms:
        differences["overall_assessment"] = "⚠️ 信息不完整"
    elif xdan_len > std_len * 1.3:
        differences["overall_assessment"] = "✅ 详细且准确"
    else:
        differences["overall_assessment"] = "✅ 基本满足要求"
    
    return differences

def extract_key_terms(text: str) -> list:
    """提取关键术语"""
    import re
    
    terms = []
    
    # 接口名
    terms.extend(re.findall(r'`(\w+)`', text))
    
    # 系统名
    terms.extend(re.findall(r'(ice-\w+-app)', text))
    
    # 参数值
    terms.extend(re.findall(r'(\d{2}-\w+)', text))
    
    # 时间格式
    if 'yyyyMMddHHmmss' in text:
        terms.append('yyyyMMddHHmmss')
    
    # 关键词
    keywords = ['必填', '可选', '成功', '失败', '处理中', '循环额度', '撞库', '绑卡', '批扣']
    for keyword in keywords:
        if keyword in text:
            terms.append(keyword)
    
    return list(set(terms))

def create_mock_data():
    """创建模拟的完整对比数据"""
    
    # 读取原始问题
    original_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json'
    with open(original_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # 读取DeepSeek结果
    deepseek_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_DeepSeek_batch_4_20250703_152420.json'
    deepseek_data = {}
    
    try:
        with open(deepseek_file, 'r', encoding='utf-8') as f:
            deepseek_list = json.load(f)
            for item in deepseek_list:
                deepseek_data[item.get('index', 0)] = item
    except FileNotFoundError:
        print("DeepSeek文件未找到，使用空数据")
    
    # 模拟xDAN-V2的回答 (基于合理推断)
    xdan_v2_mock_answers = {
        1: {
            "answer": """根据文档1中的接口规范，`agreementTime`参数具有以下作用和格式要求：

1. **作用说明**：
   - 记录用户签署借款相关协议的时间
   - 用于合规性验证，确保协议签署在申请之前
   - 属于必填字段，用于监管要求

2. **格式要求**：
   - 严格采用`yyyyMMddHHmmss`格式（14位数字）
   - 示例：20230815143000表示2023年8月15日14点30分00秒

该参数位于授信申请接口`applyCredit`的入参中，是合规性验证的关键字段。""",
            "rag": """【文档1】(相关度: 0.92)
3.2.1 授信申请接口
接口名称：applyCredit
入参说明：
- agreementTime: 借款相关协议签署时间，必填，格式：yyyyMMddHHmmss

【文档2】(相关度: 0.85)
用户信息userInfo字段说明：
agreementTime字段用于记录用户签署授信协议的具体时间，该时间必须早于申请时间。"""
        },
        2: {
            "answer": """根据文档内容，`repayMethod`字段是借款申请接口的必填参数，用于指定还款方式。

文档提到"系统支持多种还款方式，具体取值参见数据字典"，但当前文档中未找到具体的枚举值定义。

基于金融系统常见设计，还款方式通常包括等额本息、等额本金等，但需要查阅完整的数据字典文档以获取准确的取值列表。""",
            "rag": """【文档1】(相关度: 0.65)
借款申请接口参数说明
repayMethod: 还款方式，必填

【文档2】(相关度: 0.58)
系统支持多种还款方式，具体取值参见数据字典。"""
        },
        3: {
            "answer": """根据文档内容，在合作方绑卡批扣模式下，授信流程调用以下接口：

1. `applyCredit`（授信申请）
   - 调用链路：ice-pfs-app → ice-partner-app → ice-gws-app → 机构

文档中未明确提及绑卡专用接口，推测绑卡信息通过授信接口的`bankCardInfo`参数传递。""",
            "rag": """【文档1】(相关度: 0.70)
授信申请流程说明
调用链路：ice-pfs-app → ice-partner-app → ice-gws-app → 机构

【文档2】(相关度: 0.65)
bankCardInfo参数为可选字段，用于传递银行卡信息。"""
        }
        # ... 可以继续添加更多问题的模拟数据
    }
    
    results = []
    
    for i, qa_item in enumerate(questions_data, 1):
        question = qa_item.get('question', '')
        standard_answer = qa_item.get('answer_correct', '')
        
        # 获取模拟的xDAN-V2答案和RAG
        mock_data = xdan_v2_mock_answers.get(i, {
            "answer": "生成失败",
            "rag": "未召回到相关内容"
        })
        
        xdan_answer = mock_data["answer"]
        xdan_rag = mock_data["rag"]
        
        # 获取DeepSeek答案
        deepseek_item = deepseek_data.get(i, {})
        deepseek_answer = deepseek_item.get('deepseek-rag-system', '无DeepSeek答案')
        
        # 分析差异
        differences = analyze_differences(xdan_answer, standard_answer)
        
        # 构建结果
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
    
    return results

def save_to_csv(results, filename):
    """保存到CSV文件"""
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

def main():
    """主函数"""
    print("🚀 生成全面对比分析CSV（模拟版本）")
    
    # 创建模拟数据
    results = create_mock_data()
    
    # 保存CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/全面对比分析_{timestamp}.csv'
    save_to_csv(results, csv_filename)
    
    # 统计信息
    total = len(results)
    excellent = sum(1 for r in results if '✅ 详细且准确' in r['overall_assessment'])
    good = sum(1 for r in results if '✅ 基本满足要求' in r['overall_assessment'])
    warning = sum(1 for r in results if '⚠️' in r['overall_assessment'])
    failed = sum(1 for r in results if '❌' in r['overall_assessment'])
    
    print(f"\n📊 统计结果:")
    print(f"   - 总问题数: {total}")
    print(f"   - 优秀回答: {excellent} ({excellent/total:.1%})")
    print(f"   - 良好回答: {good} ({good/total:.1%})")
    print(f"   - 需改进: {warning} ({warning/total:.1%})")
    print(f"   - 失败: {failed} ({failed/total:.1%})")
    
    print(f"\n✅ CSV文件已生成: {csv_filename}")
    
    # 显示前几行作为预览
    print(f"\n📋 CSV内容预览（前3行）:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n--- 问题 {i} ---")
        print(f"问题: {result['question'][:50]}...")
        print(f"整体评估: {result['overall_assessment']}")
        print(f"详细程度: {result['difference_detail_level']}")
        print(f"准确性: {result['difference_accuracy']}")

if __name__ == "__main__":
    main()