#!/usr/bin/env python3
"""对比各版本的多轮搜索实现情况"""

import json
import re

def analyze_response_structure(response_text):
    """分析响应文本的结构"""
    features = {
        'has_search_complete': bool(re.search(r'<search_complete>', response_text, re.IGNORECASE)),
        'has_next_query': bool(re.search(r'<next_query>', response_text, re.IGNORECASE)),
        'has_search_query': bool(re.search(r'<search_query>', response_text, re.IGNORECASE)),
        'has_search_select': bool(re.search(r'\*\*Search/Select:\*\*', response_text)),
        'has_thinking': bool(re.search(r'<thinking>', response_text, re.IGNORECASE)),
        'has_important_urls': bool(re.search(r'<important_urls>', response_text, re.IGNORECASE)),
        'response_length': len(response_text)
    }
    
    # 统计各种标签的数量
    features['search_complete_count'] = len(re.findall(r'<search_complete>', response_text, re.IGNORECASE))
    features['next_query_count'] = len(re.findall(r'<next_query>', response_text, re.IGNORECASE))
    features['search_query_count'] = len(re.findall(r'<search_query>', response_text, re.IGNORECASE))
    features['search_select_count'] = len(re.findall(r'\*\*Search/Select:\*\*', response_text))
    
    return features

def compare_versions(report_file):
    """对比各版本的实现差异"""
    with open(report_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== 各版本多轮搜索实现对比 ===\n")
    
    versions = ['original', 'lite', 'full']
    version_stats = {}
    
    for version in versions:
        version_data = data.get('versions', {}).get(version, {})
        stats = {
            'total': version_data.get('total_questions', 0),
            'success': version_data.get('success_count', 0),
            'avg_time': version_data.get('average_time', 0),
            'avg_score': version_data.get('average_score', 0),
            'multi_round_count': 0,
            'features': {
                'has_search_complete': 0,
                'has_next_query': 0,
                'has_search_query': 0,
                'has_search_select': 0,
                'has_thinking': 0,
                'has_important_urls': 0
            },
            'avg_response_length': 0,
            'avg_search_select_count': 0
        }
        
        total_length = 0
        total_search_select = 0
        
        for result in version_data.get('results', []):
            response_text = result.get('response_text', '')
            features = analyze_response_structure(response_text)
            
            # 统计特征
            for feature, value in features.items():
                if feature.startswith('has_') and value:
                    stats['features'][feature] += 1
            
            if features['has_next_query']:
                stats['multi_round_count'] += 1
            
            total_length += features['response_length']
            total_search_select += features['search_select_count']
        
        if stats['total'] > 0:
            stats['avg_response_length'] = total_length / stats['total']
            stats['avg_search_select_count'] = total_search_select / stats['total']
        
        version_stats[version] = stats
    
    # 展示对比结果
    for version, stats in version_stats.items():
        print(f"\n=== {version}版本 ===")
        print(f"总问题数: {stats['total']}")
        print(f"成功数: {stats['success']}")
        print(f"平均时间: {stats['avg_time']:.2f}秒")
        print(f"平均得分: {stats['avg_score']:.2f}")
        print(f"多轮搜索数: {stats['multi_round_count']} ({stats['multi_round_count']/max(stats['total'], 1)*100:.1f}%)")
        print(f"平均响应长度: {stats['avg_response_length']:.0f}字符")
        print(f"平均Search/Select轮次: {stats['avg_search_select_count']:.1f}")
        
        print("\n特征分布:")
        for feature, count in stats['features'].items():
            percentage = count / max(stats['total'], 1) * 100
            print(f"  {feature}: {count} ({percentage:.1f}%)")
    
    # 分析原版和轻量版的具体差异
    print("\n\n=== 原版 vs 轻量版响应示例对比 ===")
    
    # 找一个相同的问题在两个版本中的响应
    original_results = {r['question_id']: r for r in version_stats.get('original', {}).get('results', [])}
    lite_results = {r['question_id']: r for r in data.get('versions', {}).get('lite', {}).get('results', [])}
    
    # 展示第一个原版响应
    if data.get('versions', {}).get('original', {}).get('results'):
        first_original = data.get('versions', {}).get('original', {}).get('results', [])[0]
        print("\n原版响应示例:")
        print(f"问题: {first_original.get('question', '')[:100]}...")
        print(f"响应长度: {len(first_original.get('response_text', ''))}字符")
        print("响应内容:")
        print(first_original.get('response_text', '')[:500])
        
    # 展示第一个轻量版响应
    if data.get('versions', {}).get('lite', {}).get('results'):
        first_lite = data.get('versions', {}).get('lite', {}).get('results', [])[0]
        print("\n\n轻量版响应示例:")
        print(f"问题: {first_lite.get('question', '')[:100]}...")
        print(f"响应长度: {len(first_lite.get('response_text', ''))}字符")
        print("响应内容:")
        print(first_lite.get('response_text', '')[:500])

if __name__ == "__main__":
    compare_versions('parallel_test_report_20250630_001224.json')