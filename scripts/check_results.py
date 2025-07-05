#!/usr/bin/env python3
"""检查S3处理结果"""

import pandas as pd
import os

# 结果文件路径
result_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703_S3结果_20250703_093202.xlsx'

if os.path.exists(result_file):
    # 读取Excel
    df = pd.read_excel(result_file)
    
    print(f"📊 结果文件统计:")
    print(f"总行数: {len(df)}")
    
    # 检查有答案的行数
    result_col = 'xdan结果v2'
    if result_col in df.columns:
        has_answer = df[df[result_col].notna() & (df[result_col] != '')]
        print(f"已有答案的行数: {len(has_answer)}")
        
        # 显示前5个已处理的问题和答案
        print("\n📝 已处理的问题预览:")
        for idx, row in has_answer.head(5).iterrows():
            question = row.get('阶段二问题', '')[:50] + '...'
            answer = str(row.get(result_col, ''))[:100] + '...'
            docs = row.get('文档数量', 0)
            rounds = row.get('搜索轮数', 0)
            
            print(f"\n问题{idx}: {question}")
            print(f"答案: {answer}")
            print(f"文档数: {docs}, 搜索轮数: {rounds}")
    
    # 保存预览到文本文件
    preview_file = result_file.replace('.xlsx', '_preview.txt')
    with open(preview_file, 'w', encoding='utf-8') as f:
        f.write("S3 RAG处理结果预览\n")
        f.write("=" * 60 + "\n\n")
        
        for idx, row in has_answer.iterrows():
            f.write(f"问题{idx}: {row.get('阶段二问题', '')}\n")
            f.write(f"答案: {row.get(result_col, '')}\n")
            f.write(f"文档数: {row.get('文档数量', 0)}, 搜索轮数: {row.get('搜索轮数', 0)}\n")
            f.write(f"搜索过程: {row.get('搜索过程', '')}\n")
            f.write("-" * 60 + "\n\n")
    
    print(f"\n💾 详细预览已保存到: {preview_file}")
else:
    print("❌ 结果文件不存在")