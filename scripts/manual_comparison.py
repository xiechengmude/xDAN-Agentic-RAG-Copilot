#!/usr/bin/env python3
"""
手动对比分析RAG结果 - 逐条人工评价
"""

import pandas as pd
import os
from datetime import datetime


def compare_individual_results():
    """逐条对比分析RAG结果"""
    
    # 读取Excel文件
    input_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703_S3结果_20250703_093452.xlsx'
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return
    
    print(f"📖 读取文件: {input_file}")
    df = pd.read_excel(input_file)
    
    # 显示文件基本信息
    print(f"文件包含 {len(df)} 行数据")
    print(f"列名: {list(df.columns)}")
    
    # 找到有问题的行
    question_rows = df[df['阶段二问题'].notna()]
    print(f"找到 {len(question_rows)} 个有效问题")
    
    # 显示前几行数据供检查
    for idx, row in question_rows.head().iterrows():
        print(f"\n问题{idx}: {row.get('阶段二问题', '')}")
        print(f"xdan结果v2: {str(row.get('xdan结果v2', ''))[:100]}...")
        print(f"xdan结果: {str(row.get('xdan结果', ''))[:100]}...")
        print(f"普通rag 14b结果: {str(row.get('普通rag 14b结果', ''))[:100]}...")
        print(f"现有对比: {row.get('xdan结果与RAG14结果对比', '')}")


if __name__ == "__main__":
    compare_individual_results()