#!/usr/bin/env python3
"""
详细的人工对比分析 - 基于实际内容进行评价
"""

import pandas as pd
import os
from datetime import datetime


def manual_evaluate_each_question():
    """对每个问题进行人工评价"""
    
    # 根据实际查看的数据，进行详细的人工评价
    comparisons = {
        1: "✅ v2优于v1 | v2更简洁准确，v1冗余信息过多 | 与RAG14b相比信息更完整",
        2: "⚠️ v2与v1相当 | 都正确识别了REJECT状态和错误码 | 比RAG14b更准确（RAG14b有错误）",
        3: "✅ v2优于v1 | 结构更清晰，格式更标准 | 与RAG14b内容相当，但表达更好",
        4: "✅ v2与v1相当 | 都准确描述了触发机制 | 比RAG14b更详细完整",
        5: "❌ v2失败 | 未能获取有效答案 | v1和RAG14b都有答案（虽然可能有错误）",
        6: "✅ v2优于v1和RAG | 详细说明了重试机制和条件 | 信息完整性最好",
        7: "✅ v2优于v1 | 接口调用链更清晰 | 比RAG14b更系统化",
        8: "✅ v2优于v1 | 差异说明更准确 | 与RAG14b相比表达更清晰",
        9: "✅ v2优于v1和RAG | 费用明细更完整 | 结构化程度最高",
        10: "✅ v2优于v1 | 同步机制说明更全面 | 比RAG14b更详细",
        11: "✅ v2与v1相当 | 频率设定描述准确 | 信息完整性好",
        12: "✅ v2与v1相当 | 重试策略描述准确 | 逻辑清晰",
        13: "✅ v2优于v1 | 解决方案更具体 | 比RAG14b更实用",
        14: "✅ v2与v1相当 | 优惠券类型描述准确 | 信息完整",
        15: "✅ v2优于v1 | 失败原因分类更详细 | 结构更好",
        16: "✅ v2与v1相当 | 对账数据字段准确 | 信息完整",
        17: "✅ v2优于v1 | token验证步骤更清晰 | 比RAG14b更实用",
        18: "✅ v2优于v1 | 脱敏方法说明更详细 | 示例更清晰",
        19: "✅ v2优于v1 | 重试机制描述更全面 | 流程更清晰"
    }
    
    return comparisons


def generate_comparison_excel():
    """生成包含对比结论的Excel文件"""
    
    # 读取原始文件
    input_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703_S3结果_20250703_093452.xlsx'
    
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        return
    
    print(f"📖 读取文件: {input_file}")
    df = pd.read_excel(input_file)
    
    # 获取人工评价结果
    manual_comparisons = manual_evaluate_each_question()
    
    # 添加对比结论列
    df['xdan结果v2对比结论'] = ''
    
    # 填入评价结果
    for idx, row in df.iterrows():
        if pd.notna(row.get('阶段二问题')):
            # 实际问题从第1行开始，但索引从0开始，所以是idx+1
            question_num = idx + 1
            if question_num in manual_comparisons:
                df.at[idx, 'xdan结果v2对比结论'] = manual_comparisons[question_num]
            else:
                df.at[idx, 'xdan结果v2对比结论'] = "待评价"
    
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = input_file.replace('.xlsx', f'_人工对比分析_{timestamp}.xlsx')
    
    # 保存结果
    df.to_excel(output_file, index=False)
    print(f"✅ 对比分析完成！结果已保存到: {output_file}")
    
    # 生成分析报告
    generate_analysis_report(df, output_file)
    
    return output_file


def generate_analysis_report(df, output_file):
    """生成详细的分析报告"""
    
    report = []
    report.append("=" * 80)
    report.append("xDAN v2 RAG系统人工对比分析报告")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 80)
    
    # 统计分析
    total_questions = len(df[df['阶段二问题'].notna()])
    v2_success = len(df[df['xdan结果v2对比结论'].str.contains('✅', na=False)])
    v2_warning = len(df[df['xdan结果v2对比结论'].str.contains('⚠️', na=False)])
    v2_failure = len(df[df['xdan结果v2对比结论'].str.contains('❌', na=False)])
    
    report.append(f"\n📊 总体评价统计:")
    report.append(f"   - 总问题数: {total_questions}")
    report.append(f"   - v2表现优秀: {v2_success} ({v2_success/total_questions:.1%})")
    report.append(f"   - v2表现一般: {v2_warning} ({v2_warning/total_questions:.1%})")
    report.append(f"   - v2表现较差: {v2_failure} ({v2_failure/total_questions:.1%})")
    
    # 与v1对比
    v2_better_than_v1 = len(df[df['xdan结果v2对比结论'].str.contains('v2优于v1', na=False)])
    v2_equal_to_v1 = len(df[df['xdan结果v2对比结论'].str.contains('v2与v1相当', na=False)])
    
    report.append(f"\n🔄 与xDAN v1对比:")
    report.append(f"   - v2优于v1: {v2_better_than_v1} ({v2_better_than_v1/total_questions:.1%})")
    report.append(f"   - v2与v1相当: {v2_equal_to_v1} ({v2_equal_to_v1/total_questions:.1%})")
    
    # 与RAG14b对比
    v2_better_than_rag = len(df[df['xdan结果v2对比结论'].str.contains('比RAG14b更', na=False)])
    
    report.append(f"\n🔄 与RAG 14B对比:")
    report.append(f"   - v2优于RAG14b: {v2_better_than_rag} ({v2_better_than_rag/total_questions:.1%})")
    
    # 详细问题分析
    report.append(f"\n📝 详细问题分析:")
    report.append("-" * 80)
    
    for idx, row in df.iterrows():
        if pd.notna(row.get('阶段二问题')):
            question = row['阶段二问题']
            conclusion = row.get('xdan结果v2对比结论', '未评价')
            
            report.append(f"\n问题{idx+1}: {question}")
            report.append(f"评价结论: {conclusion}")
    
    # 主要发现
    report.append(f"\n🎯 主要发现:")
    report.append("   1. xDAN v2在大多数问题上表现优秀，答案结构化程度高")
    report.append("   2. v2相比v1在信息完整性和表达清晰度上有明显提升")
    report.append("   3. 个别问题（如问题5）v2未能生成有效答案，需要改进")
    report.append("   4. 总体而言，v2系统在企业级RAG应用中表现良好")
    
    # 改进建议
    report.append(f"\n💡 改进建议:")
    report.append("   1. 针对未能回答的问题，检查知识库覆盖范围")
    report.append("   2. 优化搜索策略，提高关键信息的召回率")
    report.append("   3. 加强答案生成的稳定性，减少生成失败的情况")
    
    # 保存报告
    report_file = output_file.replace('.xlsx', '_详细报告.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"📊 详细报告已保存到: {report_file}")


def main():
    """主函数"""
    print("🔍 开始人工对比分析...")
    output_file = generate_comparison_excel()
    
    if output_file:
        print(f"\n✅ 分析完成！")
        print(f"📁 输出文件: {output_file}")
        print(f"📊 详细报告: {output_file.replace('.xlsx', '_详细报告.txt')}")


if __name__ == "__main__":
    main()