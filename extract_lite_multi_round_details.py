#!/usr/bin/env python3
"""提取轻量版多轮搜索的详细传递过程"""

import json
import re

def extract_multi_round_details(response_text):
    """从响应文本中提取多轮搜索的详细信息"""
    # 提取所有next_query内容
    next_query_pattern = r'<next_query>(.*?)</next_query>'
    next_queries = re.findall(next_query_pattern, response_text, re.IGNORECASE | re.DOTALL)
    
    # 提取Search/Select块
    search_select_pattern = r'\*\*Search/Select:\*\*(.*?)(?=\*\*Search/Select:\*\*|$)'
    search_rounds = re.findall(search_select_pattern, response_text, re.IGNORECASE | re.DOTALL)
    
    return {
        'next_queries': next_queries,
        'search_rounds': search_rounds,
        'round_count': len(search_rounds)
    }

def analyze_multi_round_transmission(report_file):
    """分析多轮搜索的传递过程"""
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lite_data = data.get('versions', {}).get('lite', {})
    
    print("=== 轻量版多轮搜索传递过程分析 ===\n")
    
    # 找出具有最多轮次的案例
    max_rounds_example = None
    max_rounds = 0
    
    for result in lite_data.get('results', []):
        response_text = result.get('response_text', '')
        details = extract_multi_round_details(response_text)
        
        if details['round_count'] > max_rounds:
            max_rounds = details['round_count']
            max_rounds_example = {
                'question_id': result.get('question_id'),
                'question': result.get('question'),
                'response_text': response_text,
                'details': details,
                'score': result.get('overall_score', 0)
            }
    
    # 展示多轮搜索传递过程
    if max_rounds_example:
        print(f"最多轮次示例：{max_rounds_example['question_id']} (共{max_rounds}轮)")
        print(f"问题：{max_rounds_example['question'][:150]}...")
        print(f"得分：{max_rounds_example['score']}\n")
        
        print("=== 搜索轮次传递过程 ===\n")
        
        # 展示每一轮的搜索内容
        for i, round_content in enumerate(max_rounds_example['details']['search_rounds'], 1):
            print(f"第{i}轮搜索：")
            print("-" * 50)
            # 只显示每轮的前500个字符
            print(round_content.strip()[:500])
            print("\n")
        
        print("\n=== next_query内容提取 ===\n")
        for i, next_query in enumerate(max_rounds_example['details']['next_queries'], 1):
            print(f"next_query {i}:")
            print("-" * 50)
            print(next_query.strip())
            print("\n")
    
    # 统计多轮搜索的轮次分布
    print("\n=== 多轮搜索轮次分布 ===")
    round_distribution = {}
    
    for result in lite_data.get('results', []):
        response_text = result.get('response_text', '')
        details = extract_multi_round_details(response_text)
        round_count = details['round_count']
        
        if round_count not in round_distribution:
            round_distribution[round_count] = 0
        round_distribution[round_count] += 1
    
    for rounds, count in sorted(round_distribution.items()):
        print(f"{rounds}轮搜索: {count}个案例")
    
    # 分析next_query的内容特征
    print("\n=== next_query内容特征分析 ===")
    all_next_queries = []
    
    for result in lite_data.get('results', []):
        response_text = result.get('response_text', '')
        details = extract_multi_round_details(response_text)
        all_next_queries.extend(details['next_queries'])
    
    print(f"总共发现 {len(all_next_queries)} 个next_query")
    
    # 展示一些典型的next_query示例
    print("\n典型next_query示例:")
    for i, query in enumerate(all_next_queries[:5], 1):
        print(f"\n示例{i}:")
        print(query.strip()[:200] + "..." if len(query) > 200 else query.strip())

if __name__ == "__main__":
    analyze_multi_round_transmission('parallel_test_report_20250630_001224.json')