#!/usr/bin/env python3
"""
分析测试结果
"""

import json
import sys

def analyze_results(filename):
    """分析测试结果文件"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print(f"测试报告分析: {data['test_name']}")
    print(f"测试时间: {data['test_time']}")
    print("=" * 80)
    
    # 配置信息
    print("\n配置信息:")
    print(f"- Search Model: {data['configuration']['search_model']['name']}")
    print(f"- Generator Model: {data['configuration']['generator_model']['name']}")
    print(f"- Dataset ID: {data['configuration']['dataset_id']}")
    
    # 总体统计
    summary = data['summary']
    print(f"\n总体统计:")
    print(f"- 总问题数: {summary['total_questions']}")
    print(f"- 成功率: {summary['success_rate']}%")
    print(f"- 平均总耗时: {summary['average_total_duration']}秒")
    print(f"- 平均搜索耗时: {summary['average_search_duration']}秒")
    print(f"- 平均生成耗时: {summary['average_generation_duration']}秒")
    print(f"- 平均搜索轮数: {summary['average_search_rounds']}")
    print(f"- 平均选中文档数: {summary['average_selected_documents']}")
    
    # 按难度分析
    difficulty_stats = {"简单": [], "中等": [], "复杂": []}
    for result in data['results']:
        if result['status'] == 'success':
            difficulty = result['difficulty']
            difficulty_stats[difficulty].append({
                'search_duration': result['search_model_results']['duration'],
                'generation_duration': result['generator_model_results']['duration'],
                'search_rounds': result['search_model_results']['search_rounds'],
                'selected_docs': result['search_model_results']['selected_documents_count']
            })
    
    print("\n按难度分析:")
    for difficulty, stats in difficulty_stats.items():
        if stats:
            avg_search = sum(s['search_duration'] for s in stats) / len(stats)
            avg_gen = sum(s['generation_duration'] for s in stats) / len(stats)
            avg_rounds = sum(s['search_rounds'] for s in stats) / len(stats)
            avg_docs = sum(s['selected_docs'] for s in stats) / len(stats)
            print(f"\n{difficulty}题目 ({len(stats)}个):")
            print(f"  - 平均搜索耗时: {avg_search:.2f}秒")
            print(f"  - 平均生成耗时: {avg_gen:.2f}秒")
            print(f"  - 平均搜索轮数: {avg_rounds:.2f}")
            print(f"  - 平均选中文档数: {avg_docs:.2f}")
    
    # 找出搜索轮数最多的问题
    print("\n搜索轮数分析:")
    multi_round_questions = []
    for result in data['results']:
        if result['status'] == 'success' and result['search_model_results']['search_rounds'] > 1:
            multi_round_questions.append({
                'id': result['question_id'],
                'question': result['question'],
                'rounds': result['search_model_results']['search_rounds'],
                'duration': result['search_model_results']['duration']
            })
    
    if multi_round_questions:
        print(f"需要多轮搜索的问题 ({len(multi_round_questions)}个):")
        for q in sorted(multi_round_questions, key=lambda x: x['rounds'], reverse=True):
            print(f"  - 问题{q['id']}: {q['rounds']}轮搜索, 耗时{q['duration']:.1f}秒")
            print(f"    {q['question'][:50]}...")
    else:
        print("所有问题都在1轮搜索内完成")
    
    # 答案长度分析
    print("\n答案长度分析:")
    answer_lengths = []
    for result in data['results']:
        if result['status'] == 'success':
            length = result['generator_model_results']['answer_length']
            answer_lengths.append((result['question_id'], length, result['difficulty']))
    
    answer_lengths.sort(key=lambda x: x[1], reverse=True)
    print("最长的5个答案:")
    for qid, length, difficulty in answer_lengths[:5]:
        print(f"  - 问题{qid} ({difficulty}): {length}字符")
    
    # 性能分析
    print("\n性能分析:")
    search_times = [r['search_model_results']['duration'] for r in data['results'] if r['status'] == 'success']
    gen_times = [r['generator_model_results']['duration'] for r in data['results'] if r['status'] == 'success']
    
    print(f"搜索模型性能:")
    print(f"  - 最快: {min(search_times):.2f}秒")
    print(f"  - 最慢: {max(search_times):.2f}秒")
    print(f"  - 中位数: {sorted(search_times)[len(search_times)//2]:.2f}秒")
    
    print(f"\n生成模型性能:")
    print(f"  - 最快: {min(gen_times):.2f}秒")
    print(f"  - 最慢: {max(gen_times):.2f}秒")
    print(f"  - 中位数: {sorted(gen_times)[len(gen_times)//2]:.2f}秒")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "test_results_zhixin_comprehensive_20250620_065044.json"
    
    analyze_results(filename)