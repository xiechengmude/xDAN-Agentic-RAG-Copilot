#!/usr/bin/env python3
"""分析轻量版的多轮搜索测试结果"""

import json
import re
from collections import defaultdict

def extract_search_rounds(response_text):
    """从响应文本中提取搜索轮次信息"""
    rounds = []
    
    # 查找search_complete标签
    search_complete_pattern = r'<search_complete>(.*?)</search_complete>'
    search_complete_matches = re.findall(search_complete_pattern, response_text, re.IGNORECASE)
    
    # 查找next_query
    next_query_pattern = r'<next_query>(.*?)</next_query>'
    next_query_matches = re.findall(next_query_pattern, response_text, re.IGNORECASE | re.DOTALL)
    
    # 查找search_query
    search_query_pattern = r'<search_query>(.*?)</search_query>'
    search_query_matches = re.findall(search_query_pattern, response_text, re.IGNORECASE | re.DOTALL)
    
    return {
        'search_complete': search_complete_matches,
        'next_query': next_query_matches,
        'search_query': search_query_matches,
        'has_multi_round': len(next_query_matches) > 0
    }

def analyze_lite_version(report_file):
    """分析轻量版的测试结果"""
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取轻量版的测试结果
    lite_data = data.get('versions', {}).get('lite', {})
    
    print("=== 轻量版(lite)测试结果分析 ===\n")
    print(f"总问题数: {lite_data.get('total_questions', 0)}")
    print(f"成功数: {lite_data.get('success_count', 0)}")
    print(f"平均时间: {lite_data.get('average_time', 0):.2f}秒")
    print(f"平均得分: {lite_data.get('average_score', 0):.2f}\n")
    
    # 分析多轮搜索情况
    multi_round_examples = []
    single_round_examples = []
    
    for result in lite_data.get('results', []):
        question_id = result.get('question_id')
        response_text = result.get('response_text', '')
        
        search_info = extract_search_rounds(response_text)
        
        if search_info['has_multi_round']:
            multi_round_examples.append({
                'question_id': question_id,
                'question': result.get('question'),
                'search_info': search_info,
                'response_text': response_text,
                'score': result.get('overall_score', 0)
            })
        else:
            single_round_examples.append({
                'question_id': question_id,
                'search_complete': search_info['search_complete'],
                'search_query_count': len(search_info['search_query'])
            })
    
    print(f"=== 多轮搜索统计 ===")
    print(f"多轮搜索案例数: {len(multi_round_examples)}")
    print(f"单轮搜索案例数: {len(single_round_examples)}\n")
    
    # 展示多轮搜索示例
    if multi_round_examples:
        print("=== 多轮搜索示例 ===\n")
        for i, example in enumerate(multi_round_examples[:3], 1):  # 展示前3个
            print(f"示例 {i}:")
            print(f"问题ID: {example['question_id']}")
            print(f"问题: {example['question'][:100]}...")
            print(f"得分: {example['score']}")
            print(f"包含next_query数: {len(example['search_info']['next_query'])}")
            print(f"\n响应文本片段:")
            print(example['response_text'][:500])
            print("\n" + "="*50 + "\n")
    
    # 对比其他版本
    print("\n=== 各版本多轮搜索对比 ===")
    versions_comparison = {}
    
    for version in ['original', 'lite', 'full']:
        version_data = data.get('versions', {}).get(version, {})
        multi_round_count = 0
        
        for result in version_data.get('results', []):
            response_text = result.get('response_text', '')
            if '<next_query>' in response_text:
                multi_round_count += 1
        
        versions_comparison[version] = {
            'total': version_data.get('total_questions', 0),
            'multi_round': multi_round_count,
            'percentage': (multi_round_count / version_data.get('total_questions', 1)) * 100
        }
    
    for version, stats in versions_comparison.items():
        print(f"\n{version}版本:")
        print(f"  总问题数: {stats['total']}")
        print(f"  多轮搜索数: {stats['multi_round']}")
        print(f"  多轮搜索比例: {stats['percentage']:.1f}%")
    
    # 分析search_complete标签使用情况
    print("\n=== search_complete标签使用分析 ===")
    for version in ['original', 'lite', 'full']:
        version_data = data.get('versions', {}).get(version, {})
        true_count = 0
        false_count = 0
        no_tag_count = 0
        
        for result in version_data.get('results', []):
            response_text = result.get('response_text', '')
            if '<search_complete>True</search_complete>' in response_text:
                true_count += 1
            elif '<search_complete>False</search_complete>' in response_text:
                false_count += 1
            else:
                no_tag_count += 1
        
        print(f"\n{version}版本:")
        print(f"  search_complete=True: {true_count}")
        print(f"  search_complete=False: {false_count}")
        print(f"  无标签: {no_tag_count}")

if __name__ == "__main__":
    analyze_lite_version('parallel_test_report_20250630_001224.json')