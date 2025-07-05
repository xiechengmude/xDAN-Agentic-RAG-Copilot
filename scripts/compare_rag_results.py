#!/usr/bin/env python3
"""
比较不同RAG系统的结果并生成评价结论
对比 xdan结果v2 与 xdan结果、普通rag 14b结果
"""

import pandas as pd
import os
from datetime import datetime
import re


def extract_key_points(text):
    """提取答案中的关键要点"""
    if pd.isna(text) or text == '':
        return []
    
    # 提取核心接口名、状态码、参数等关键信息
    key_points = []
    
    # 提取接口名（如 applyCredit, queryCreditResult 等）
    interfaces = re.findall(r'`(\w+)`', str(text))
    key_points.extend(interfaces)
    
    # 提取编号列表项（如 1. 2. 3.）
    numbered_items = re.findall(r'\d+\.\s*\*?\*?([^：:]+)[:：]?', str(text))
    key_points.extend([item.strip('*').strip() for item in numbered_items])
    
    # 提取状态码或错误码（如 ICE3101, ZX0001 等）
    codes = re.findall(r'\b[A-Z]+\d+\b', str(text))
    key_points.extend(codes)
    
    return key_points


def calculate_similarity(text1, text2):
    """计算两个答案的相似度（基于关键点匹配）"""
    if pd.isna(text1) or pd.isna(text2) or text1 == '' or text2 == '':
        return 0.0
    
    points1 = set(extract_key_points(text1))
    points2 = set(extract_key_points(text2))
    
    if not points1 and not points2:
        # 如果都没有提取到关键点，比较文本长度
        return min(len(str(text1)), len(str(text2))) / max(len(str(text1)), len(str(text2)))
    
    if not points1 or not points2:
        return 0.0
    
    # Jaccard相似度
    intersection = points1.intersection(points2)
    union = points1.union(points2)
    
    return len(intersection) / len(union) if union else 0.0


def evaluate_answer_quality(answer):
    """评估单个答案的质量"""
    if pd.isna(answer) or answer == '' or answer == '未能获取有效答案':
        return 0
    
    # 质量评分标准
    score = 0
    
    # 1. 答案长度（200-800字符为优）
    length = len(str(answer))
    if 200 <= length <= 800:
        score += 2
    elif length > 800:
        score += 1
    elif length > 100:
        score += 0.5
    
    # 2. 结构化程度（包含编号列表）
    if re.search(r'\d+\..*\d+\.', str(answer)):
        score += 2
    
    # 3. 包含具体接口或参数
    if re.search(r'`\w+`', str(answer)):
        score += 1
    
    # 4. 包含来源引用
    if '文档' in str(answer) or '来源' in str(answer):
        score += 1
    
    # 5. 包含示例或具体数值
    if re.search(r'例如|如：|示例', str(answer)):
        score += 1
    
    return score


def compare_results(row):
    """对比不同版本的结果并生成评价结论"""
    question = row.get('阶段二问题', '')
    xdan_v1 = row.get('xdan结果', '')
    xdan_v2 = row.get('xdan结果v2', '')
    rag_14b = row.get('普通rag 14b结果', '')
    comparison = row.get('xdan结果与RAG14结果对比', '')
    
    # 如果没有v2结果，返回空
    if pd.isna(xdan_v2) or xdan_v2 == '':
        return "无v2结果"
    
    # 评估各版本质量
    v1_quality = evaluate_answer_quality(xdan_v1)
    v2_quality = evaluate_answer_quality(xdan_v2)
    rag_quality = evaluate_answer_quality(rag_14b)
    
    # 计算相似度
    v2_v1_similarity = calculate_similarity(xdan_v2, xdan_v1)
    v2_rag_similarity = calculate_similarity(xdan_v2, rag_14b)
    
    # 提取关键点
    v2_points = extract_key_points(xdan_v2)
    v1_points = extract_key_points(xdan_v1)
    rag_points = extract_key_points(rag_14b)
    
    # 生成评价结论
    conclusions = []
    
    # 1. 质量对比
    if v2_quality > max(v1_quality, rag_quality):
        conclusions.append("✅ v2版本质量最优")
    elif v2_quality == max(v1_quality, rag_quality) and v2_quality > 0:
        conclusions.append("✅ v2版本质量与最优版本相当")
    else:
        conclusions.append("⚠️ v2版本质量有待提升")
    
    # 2. 完整性对比
    if len(v2_points) >= max(len(v1_points), len(rag_points)):
        conclusions.append("信息完整性好")
    elif len(v2_points) >= 0.8 * max(len(v1_points), len(rag_points)):
        conclusions.append("信息较完整")
    else:
        conclusions.append("信息不够完整")
    
    # 3. 与v1版本对比
    if v2_v1_similarity > 0.7:
        conclusions.append(f"与v1高度一致({v2_v1_similarity:.0%})")
    elif v2_v1_similarity > 0.4:
        conclusions.append(f"与v1部分一致({v2_v1_similarity:.0%})")
    else:
        conclusions.append(f"与v1差异较大({v2_v1_similarity:.0%})")
    
    # 4. 特殊情况
    if '未能获取有效答案' in str(xdan_v2):
        conclusions = ["❌ 未能生成有效答案"]
    elif len(str(xdan_v2)) < 50:
        conclusions.append("答案过于简短")
    
    # 5. 根据原有对比结果补充
    if pd.notna(comparison):
        if 'xdan更好' in str(comparison) and v2_quality >= v1_quality:
            conclusions.append("保持了v1的优势")
        elif 'RAG更好' in str(comparison) and v2_quality > rag_quality:
            conclusions.append("改进了RAG版本的不足")
    
    return " | ".join(conclusions)


def generate_comparison_report(df):
    """生成对比分析报告"""
    report = []
    report.append("=" * 80)
    report.append("xDAN v2 RAG系统对比分析报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # 统计有效答案
    total_questions = len(df[df['阶段二问题'].notna()])
    v2_valid = len(df[df['xdan结果v2'].notna() & (df['xdan结果v2'] != '') & (df['xdan结果v2'] != '未能获取有效答案')])
    v1_valid = len(df[df['xdan结果'].notna() & (df['xdan结果'] != '')])
    rag_valid = len(df[df['普通rag 14b结果'].notna() & (df['普通rag 14b结果'] != '')])
    
    report.append(f"\n📊 答案覆盖率统计:")
    report.append(f"   - 总问题数: {total_questions}")
    report.append(f"   - xDAN v2有效答案: {v2_valid} ({v2_valid/total_questions:.1%})")
    report.append(f"   - xDAN v1有效答案: {v1_valid} ({v1_valid/total_questions:.1%})")
    report.append(f"   - RAG 14B有效答案: {rag_valid} ({rag_valid/total_questions:.1%})")
    
    # 质量评分统计
    v2_scores = []
    v1_scores = []
    rag_scores = []
    
    for _, row in df.iterrows():
        if pd.notna(row.get('xdan结果v2')):
            v2_scores.append(evaluate_answer_quality(row['xdan结果v2']))
        if pd.notna(row.get('xdan结果')):
            v1_scores.append(evaluate_answer_quality(row['xdan结果']))
        if pd.notna(row.get('普通rag 14b结果')):
            rag_scores.append(evaluate_answer_quality(row['普通rag 14b结果']))
    
    if v2_scores:
        report.append(f"\n📈 答案质量评分（满分7分）:")
        report.append(f"   - xDAN v2平均分: {sum(v2_scores)/len(v2_scores):.2f}")
        report.append(f"   - xDAN v1平均分: {sum(v1_scores)/len(v1_scores):.2f}")
        report.append(f"   - RAG 14B平均分: {sum(rag_scores)/len(rag_scores):.2f}")
    
    # 详细对比
    report.append(f"\n📝 问题级别对比分析:")
    report.append("-" * 80)
    
    for idx, row in df.iterrows():
        if pd.notna(row.get('阶段二问题')) and pd.notna(row.get('xdan结果v2对比结论')):
            report.append(f"\n问题{idx}: {row['阶段二问题']}")
            report.append(f"对比结论: {row['xdan结果v2对比结论']}")
    
    return "\n".join(report)


def main():
    """主函数"""
    # 输入文件路径
    input_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703_S3结果_20250703_093452.xlsx'
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return
    
    print(f"📖 读取文件: {input_file}")
    df = pd.read_excel(input_file)
    
    # 检查必要的列
    required_cols = ['阶段二问题', 'xdan结果', 'xdan结果v2', '普通rag 14b结果', 'xdan结果与RAG14结果对比']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"⚠️ 缺少必要的列: {missing_cols}")
        # 创建缺失的列
        for col in missing_cols:
            df[col] = ''
    
    # 生成对比结论
    print("\n🔄 正在生成对比分析...")
    df['xdan结果v2对比结论'] = df.apply(compare_results, axis=1)
    
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = input_file.replace('.xlsx', f'_对比分析_{timestamp}.xlsx')
    
    # 保存结果
    df.to_excel(output_file, index=False)
    print(f"\n✅ 对比分析完成！结果已保存到: {output_file}")
    
    # 生成分析报告
    report = generate_comparison_report(df)
    report_file = output_file.replace('.xlsx', '_报告.txt')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📊 分析报告已保存到: {report_file}")
    
    # 显示简要统计
    print("\n📈 对比结论统计:")
    conclusion_stats = df['xdan结果v2对比结论'].value_counts()
    for conclusion, count in conclusion_stats.items():
        if pd.notna(conclusion):
            print(f"   - {conclusion}: {count}个")


if __name__ == "__main__":
    main()