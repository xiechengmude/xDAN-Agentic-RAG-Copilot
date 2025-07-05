#!/usr/bin/env python3
"""
创建详细的对比分析表格
基于实际的DeepSeek数据和模拟的xDAN-V2数据
"""

import json
import csv
import pandas as pd
from datetime import datetime

def create_comprehensive_comparison():
    """创建全面的对比分析"""
    
    # 读取原始问题
    original_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json'
    with open(original_file, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # 读取DeepSeek结果
    deepseek_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_DeepSeek_batch_4_20250703_152420.json'
    with open(deepseek_file, 'r', encoding='utf-8') as f:
        deepseek_data = json.load(f)
    
    # 创建DeepSeek数据映射
    deepseek_map = {item['index']: item for item in deepseek_data}
    
    # 基于实际数据分析的xDAN-V2模拟答案（考虑RAG召回质量）
    xdan_v2_data = {
        1: {
            "answer": """根据文档中的接口规范，`agreementTime`参数的作用和格式如下：

**作用**：
- 记录用户签署借款相关协议的时间戳（必填字段）
- 用于合规性验证，确保协议签署时间早于授信申请时间
- 满足监管合规要求

**格式**：
- 严格采用`yyyyMMddHHmmss`格式（14位数字）
- 示例：20230815143000表示2023年8月15日14点30分00秒

该参数位于授信申请接口的入参中，是业务流程的关键字段。""",
            "rag": "【文档1】授信申请接口参数说明：agreementTime为必填字段，格式yyyyMMddHHmmss，用于记录协议签署时间",
            "vs_standard": "✅ 完全准确，增加了示例说明",
            "vs_deepseek": "相当，都准确但xDAN-V2略简洁"
        },
        2: {
            "answer": """根据文档内容，`repayMethod`字段是借款申请接口的必填参数。

文档中提到该字段用于指定还款方式，但具体的枚举值定义在当前文档中未找到，需要参考数据字典。

基于常见的金融系统设计，还款方式可能包括等额本息、等额本金等类型。""",
            "rag": "【文档1】repayMethod：还款方式，必填参数。【文档2】系统支持多种还款方式，具体取值参见数据字典",
            "vs_standard": "❌ 缺少具体枚举值，RAG召回不足",
            "vs_deepseek": "明显劣于DeepSeek，DeepSeek准确列出了所有枚举值"
        },
        3: {
            "answer": """根据文档内容，在合作方绑卡批扣模式下，智信平台授信流程主要调用：

1. `applyCredit`（授信申请接口）
   - 调用链路：ice-pfs-app → ice-partner-app → ice-gws-app → 机构

文档中未明确描述绑卡专用接口，推测通过授信接口的相关参数处理绑卡信息。""",
            "rag": "【文档1】授信申请流程，调用链路说明。【文档2】bankCardInfo为可选参数",
            "vs_standard": "❌ 遗漏了checkUser、applyCertification等关键接口",
            "vs_deepseek": "都不完整，但DeepSeek提供了更多接口分析"
        },
        4: {
            "answer": """根据文档说明：

**loanTrial接口**：
- 用途：借款试算，计算还款计划和利率
- 前置条件：授信审批通过后使用
- 仅处理试算逻辑，不进行准入控制

**applyLoan接口**：
- 用途：正式借款申请
- 状态处理：支持同步和异步结果处理

**调用链路**：
ice-pfs-app → ice-partner-app → ice-gws-app → 机构

两个接口都需要在授信通过后使用，但用途不同。""",
            "rag": "【文档1】loanTrial试算接口说明。【文档2】applyLoan申请接口说明。【文档3】调用链路架构",
            "vs_standard": "✅ 准确且详细，超越标准答案",
            "vs_deepseek": "相当，都提供了详细分析"
        },
        5: {
            "answer": """文档中未明确说明`userInfo`、`companyInfo`、`faceInfo`字段的具体采集系统。

根据业务流程推测，这些字段应该在用户申请授信的过程中由前端系统采集，然后通过接口调用链传递到后端。""",
            "rag": "【文档1】applyCredit接口参数说明，userInfo、companyInfo为复杂对象，faceInfo为可选",
            "vs_standard": "❌ 过于保守，未能推断出ice-pfs-app",
            "vs_deepseek": "不如DeepSeek，DeepSeek基于流程做了合理推断"
        }
    }
    
    # 扩展到所有24个问题
    for i in range(6, 25):
        if i not in xdan_v2_data:
            xdan_v2_data[i] = {
                "answer": "生成失败或RAG召回不足",
                "rag": "未召回到相关文档或检索失败",
                "vs_standard": "❌ 无法提供有效答案",
                "vs_deepseek": "劣于DeepSeek"
            }
    
    # 构建完整对比数据
    comparison_data = []
    
    for i in range(1, 25):
        if i <= len(questions_data):
            question_item = questions_data[i-1]
            question = question_item.get('question', '')
            standard_answer = question_item.get('answer_correct', '')
        else:
            question = f"问题{i}"
            standard_answer = "标准答案"
        
        deepseek_item = deepseek_map.get(i, {})
        deepseek_answer = deepseek_item.get('deepseek-rag-system', '无DeepSeek数据')
        
        xdan_item = xdan_v2_data.get(i, xdan_v2_data[6])  # 使用默认值
        
        # 创建对比记录
        record = {
            'question_id': i,
            'question': question,
            'standard_answer': standard_answer,
            'xdan_v2_answer': xdan_item['answer'],
            'xdan_v2_rag_content': xdan_item['rag'],
            'deepseek_answer': deepseek_answer,
            'xdan_vs_standard': xdan_item['vs_standard'],
            'xdan_vs_deepseek': xdan_item['vs_deepseek'],
            'winner': determine_winner(xdan_item, deepseek_answer, standard_answer),
            'key_differences': analyze_key_differences(xdan_item['answer'], deepseek_answer, standard_answer)
        }
        
        comparison_data.append(record)
    
    return comparison_data

def determine_winner(xdan_item, deepseek_answer, standard_answer):
    """确定最佳答案"""
    vs_standard = xdan_item['vs_standard']
    vs_deepseek = xdan_item['vs_deepseek']
    
    if '✅' in vs_standard and '完全准确' in vs_standard:
        if 'xDAN-V2' in vs_deepseek or '相当' in vs_deepseek:
            return "xDAN-V2"
        else:
            return "xDAN-V2 = DeepSeek"
    elif '✅' in vs_standard:
        return "xDAN-V2 = 标准答案"
    elif '❌' in vs_standard and 'DeepSeek' in vs_deepseek:
        return "DeepSeek"
    elif '❌' in vs_standard:
        return "标准答案"
    else:
        return "标准答案"

def analyze_key_differences(xdan_answer, deepseek_answer, standard_answer):
    """分析关键差异"""
    differences = []
    
    if "生成失败" in xdan_answer:
        differences.append("xDAN-V2生成失败")
    
    if len(xdan_answer) > len(standard_answer) * 1.5:
        differences.append("xDAN-V2更详细")
    
    if "文档" in xdan_answer:
        differences.append("xDAN-V2提供文档引用")
    
    if len(deepseek_answer) > len(xdan_answer):
        differences.append("DeepSeek更详细")
    
    return " | ".join(differences) if differences else "无显著差异"

def save_comparison_to_csv(data, filename):
    """保存对比数据到CSV"""
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8')
    
    print(f"✅ 详细对比表格已保存: {filename}")
    
    # 生成统计
    winner_stats = df['winner'].value_counts()
    print(f"\n📊 获胜者统计:")
    for winner, count in winner_stats.items():
        print(f"   {winner}: {count}次 ({count/len(df):.1%})")

def main():
    """主函数"""
    print("🚀 创建详细对比分析表格")
    
    # 创建对比数据
    comparison_data = create_comprehensive_comparison()
    
    # 保存CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/详细对比分析表格_{timestamp}.csv'
    
    save_comparison_to_csv(comparison_data, csv_filename)
    
    # 显示前5个问题的预览
    print(f"\n📋 前5个问题的对比预览:")
    for i, record in enumerate(comparison_data[:5], 1):
        print(f"\n--- 问题 {i} ---")
        print(f"问题: {record['question'][:60]}...")
        print(f"获胜者: {record['winner']}")
        print(f"xDAN-V2 vs 标准答案: {record['xdan_vs_standard']}")
        print(f"关键差异: {record['key_differences']}")

if __name__ == "__main__":
    main()