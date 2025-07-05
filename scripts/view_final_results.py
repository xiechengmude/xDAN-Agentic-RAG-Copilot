#!/usr/bin/env python3
"""查看最终的S3处理结果"""

import pandas as pd
import os
from datetime import datetime

# 查找最新的结果文件
result_dir = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/'
result_files = [f for f in os.listdir(result_dir) if 'S3结果' in f and f.endswith('.xlsx')]

if result_files:
    # 按修改时间排序，获取最新的文件
    result_files.sort(key=lambda x: os.path.getmtime(os.path.join(result_dir, x)), reverse=True)
    latest_file = os.path.join(result_dir, result_files[0])
    
    print(f"📊 分析最新结果文件: {os.path.basename(latest_file)}")
    print(f"文件修改时间: {datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 读取Excel
    df = pd.read_excel(latest_file)
    
    # 基本统计
    total_rows = len(df)
    question_col = '阶段二问题'
    result_col = 'xdan结果v2'
    
    # 统计有效问题和答案
    valid_questions = df[df[question_col].notna()]
    has_answer = df[df[result_col].notna() & (df[result_col] != '')]
    has_error = df[df[result_col].str.startswith('[错误]', na=False)]
    
    print(f"\n📈 处理统计:")
    print(f"   - 总行数: {total_rows}")
    print(f"   - 有效问题数: {len(valid_questions)}")
    print(f"   - 已获得答案: {len(has_answer) - len(has_error)}")
    print(f"   - 处理失败: {len(has_error)}")
    print(f"   - 待处理: {len(valid_questions) - len(has_answer)}")
    
    # 搜索效果统计
    if '文档数量' in df.columns and '搜索轮数' in df.columns:
        valid_stats = has_answer[~has_answer[result_col].str.startswith('[错误]', na=False)]
        if len(valid_stats) > 0:
            avg_docs = valid_stats['文档数量'].mean()
            avg_rounds = valid_stats['搜索轮数'].mean()
            print(f"\n📊 搜索效果:")
            print(f"   - 平均找到文档数: {avg_docs:.1f}")
            print(f"   - 平均搜索轮数: {avg_rounds:.1f}")
    
    # 显示所有已处理的问题
    print(f"\n📝 已处理的问题详情:")
    print("-" * 80)
    
    for idx, row in has_answer.iterrows():
        question = row[question_col]
        answer = row[result_col]
        docs = row.get('文档数量', 'N/A')
        rounds = row.get('搜索轮数', 'N/A')
        status = "❌ 错误" if str(answer).startswith('[错误]') else "✅ 成功"
        
        print(f"\n[{idx+1}] {question}")
        print(f"状态: {status}")
        if status == "✅ 成功":
            print(f"文档数: {docs}, 搜索轮数: {rounds}")
            print(f"答案预览: {str(answer)[:200]}...")
        else:
            print(f"错误信息: {answer}")
    
    # 显示待处理的问题
    pending = valid_questions[~valid_questions.index.isin(has_answer.index)]
    if len(pending) > 0:
        print(f"\n⏳ 待处理的问题:")
        print("-" * 80)
        for idx, row in pending.iterrows():
            print(f"[{idx+1}] {row[question_col]}")
    
    # 生成完整报告
    report_file = latest_file.replace('.xlsx', '_完整报告.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"S3 RAG 批处理完整报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据文件: {os.path.basename(latest_file)}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"处理统计:\n")
        f.write(f"- 总行数: {total_rows}\n")
        f.write(f"- 有效问题数: {len(valid_questions)}\n")
        f.write(f"- 已获得答案: {len(has_answer) - len(has_error)}\n")
        f.write(f"- 处理失败: {len(has_error)}\n")
        f.write(f"- 待处理: {len(valid_questions) - len(has_answer)}\n\n")
        
        f.write("已处理问题详情:\n")
        f.write("=" * 80 + "\n\n")
        
        for idx, row in has_answer.iterrows():
            f.write(f"问题{idx+1}: {row[question_col]}\n")
            f.write(f"答案: {row[result_col]}\n")
            if not str(row[result_col]).startswith('[错误]'):
                f.write(f"文档数: {row.get('文档数量', 'N/A')}, 搜索轮数: {row.get('搜索轮数', 'N/A')}\n")
                f.write(f"搜索过程: {row.get('搜索过程', 'N/A')}\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"\n💾 完整报告已保存到: {report_file}")
    
else:
    print("❌ 未找到任何结果文件")