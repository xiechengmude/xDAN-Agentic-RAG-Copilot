#!/usr/bin/env python3
"""
分析parallel测试报告，提取三个版本的响应内容进行对比
"""
import json
import sys
from typing import Dict, List

def extract_version_responses(report_path: str):
    """提取各版本的响应示例"""
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    versions = data.get('versions', {})
    
    # 收集每个版本的响应
    version_responses = {}
    
    for version_key, version_data in versions.items():
        version_name = version_data.get('name', version_key)
        results = version_data.get('results', [])
        
        # 提取前3个不同类型的响应作为示例
        examples = []
        categories_seen = set()
        
        for result in results:
            category = result.get('category', '')
            if category not in categories_seen and len(examples) < 3:
                examples.append({
                    'question_id': result.get('question_id'),
                    'question': result.get('question'),
                    'category': category,
                    'response_text': result.get('response_text'),
                    'response_length': result.get('response_length'),
                    'execution_time': result.get('execution_time'),
                    'overall_score': result.get('overall_score')
                })
                categories_seen.add(category)
        
        version_responses[version_name] = {
            'average_score': version_data.get('average_score'),
            'average_time': version_data.get('average_time'),
            'examples': examples
        }
    
    return version_responses

def analyze_response_differences(version_responses: Dict):
    """分析响应差异"""
    print("=" * 80)
    print("三个版本响应内容深度对比分析")
    print("=" * 80)
    
    # 打印总体统计
    print("\n1. 总体表现对比:")
    print("-" * 50)
    for version, data in version_responses.items():
        print(f"\n{version}:")
        print(f"  - 平均得分: {data['average_score']:.2%}")
        print(f"  - 平均响应时间: {data['average_time']:.2f}秒")
    
    # 分析具体响应示例
    print("\n\n2. 具体响应示例对比:")
    print("-" * 50)
    
    # 找到共同的问题进行对比
    all_questions = {}
    for version, data in version_responses.items():
        for example in data['examples']:
            qid = example['question_id']
            if qid not in all_questions:
                all_questions[qid] = {}
            all_questions[qid][version] = example
    
    # 对每个共同问题进行对比
    for qid, versions_data in all_questions.items():
        if len(versions_data) > 1:  # 只对比多个版本都有的问题
            print(f"\n\n问题ID: {qid}")
            first_version = list(versions_data.values())[0]
            print(f"类别: {first_version['category']}")
            print(f"问题: {first_version['question'][:100]}...")
            print("\n各版本响应对比:")
            
            for version, example in versions_data.items():
                print(f"\n  [{version}] (得分: {example['overall_score']}, 长度: {example['response_length']})")
                print(f"  响应内容:")
                response = example['response_text']
                # 格式化输出响应内容
                if response:
                    lines = response.strip().split('\n')
                    for line in lines[:10]:  # 只显示前10行
                        print(f"    {line}")
                    if len(lines) > 10:
                        print(f"    ... (还有{len(lines)-10}行)")

def main():
    report_path = "/Users/gump_m2/CascadeProjects/ragflow-api-client/parallel_test_report_20250630_001224.json"
    
    try:
        version_responses = extract_version_responses(report_path)
        analyze_response_differences(version_responses)
        
        # 保存分析结果
        output_path = "parallel_report_analysis.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(version_responses, f, ensure_ascii=False, indent=2)
        
        print(f"\n\n分析结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()