#!/usr/bin/env python3
"""
生成基于RAG内容的详细对比评价示例
"""

import json
from datetime import datetime

# 模拟数据示例
example_data = [
    {
        "index": 1,
        "question": "授信申请接口 `applyCredit` 中的 `agreementTime` 有什么作用？格式是什么？（简单）",
        "answer_correct": "表示用户签署授信相关协议的时间，格式为 `yyyyMMddHHmmss`，该字段为必填项，用于监管及合同合规校验。",
        
        # xDAN-V2 召回的RAG内容
        "xdan-v2-rag": """【文档1】(相关度: 0.92)
3.2.1 授信申请接口
接口名称：applyCredit
提供方：合作方提供
入参说明：
- agreementTime: 借款相关协议签署时间，必填，格式：yyyyMMddHHmmss
- userId: 智信分配的用户唯一标识，必填
- creditApplyNo: 授信申请单号，必填

【文档2】(相关度: 0.85)
用户信息userInfo字段说明：
agreementTime字段用于记录用户签署授信协议的具体时间，该时间必须早于申请时间applyTime，用于合规性验证。

【文档3】(相关度: 0.78)
时间格式规范：
所有时间字段统一采用yyyyMMddHHmmss格式（14位数字），如20230815143000表示2023年8月15日14点30分00秒。
""",
        
        # xDAN-V2 基于RAG生成的答案
        "xdan-v2-answer": """根据文档1中的接口规范，`agreementTime`参数具有以下作用和格式要求：

1. **作用说明**：
   - 记录用户签署借款相关协议的时间（文档1明确标注为"借款相关协议签署时间"）
   - 用于合规性验证，确保协议签署在申请之前（文档2提到"必须早于申请时间applyTime"）
   - 属于必填字段，用于监管要求

2. **格式要求**：
   - 严格采用`yyyyMMddHHmmss`格式（14位数字）
   - 示例：20230815143000表示2023年8月15日14点30分00秒（文档3）

该参数位于授信申请接口`applyCredit`的入参中，是合规性验证的关键字段。""",
        
        # xDAN-V2 详细评价
        "xdan-v2-evaluation": "🌟 xDAN-V2 优秀 | 得分92.0% | ✅ RAG召回优秀 | ✅ 答案准确 | ✅ 信息利用充分",
        "xdan-v2-score": 0.92,
        "xdan-v2-detailed-scores": {
            "RAG召回质量": 18,  # 召回了3个高度相关的文档
            "答案准确性": 23,   # 完全覆盖了标准答案的要点
            "信息利用率": 14,   # 充分利用了召回的信息
            "推理合理性": 13,   # 逻辑清晰，组织合理
            "完整性": 14,       # 回答完整全面
            "表达清晰度": 10    # 结构清晰，使用了编号
        },
        
        # DeepSeek 答案（无RAG）
        "deepseek-answer": """根据文档1中的技术规范，`agreementTime`参数的作用和格式如下：

1. **作用**：
   - 记录用户签署借款相关协议的时间戳（必填字段）
   - 用于合规性验证，确保协议签署时间早于授信申请时间

2. **格式**：
   - 严格采用`yyyyMMddHHmmss`格式（14位数字）
   - 示例：`20230815143000`表示2023年8月15日14点30分00秒""",
        
        "deepseek-evaluation": "✅ DeepSeek 良好 | 得分75.0% | ❌ RAG召回不足 | ✅ 答案准确 | ⚠️ 信息利用一般",
        "deepseek-score": 0.75,
        "deepseek-detailed-scores": {
            "RAG召回质量": 0,   # DeepSeek没有RAG内容
            "答案准确性": 23,   # 答案本身准确
            "信息利用率": 8,    # 没有RAG内容可利用
            "推理合理性": 12,   # 推理合理
            "完整性": 12,       # 基本完整
            "表达清晰度": 10    # 表达清晰
        },
        
        "comparison": "xDAN-V2显著优于DeepSeek，主要差异在RAG召回质量"
    },
    
    {
        "index": 2,
        "question": "API 中的 `repayMethod` 字段有哪些取值？与平台文档中还款方式有什么关系？（简单）",
        "answer_correct": "取值包括 00-等额本金、01-等额本息、02-先息后本、03-等本等息。与平台的还款计划计算逻辑保持一致，用于明确每期本金/利息分摊方式。",
        
        # xDAN-V2 RAG内容质量不佳的例子
        "xdan-v2-rag": """【文档1】(相关度: 0.65)
借款申请接口参数说明
repayMethod: 还款方式，必填

【文档2】(相关度: 0.58)
系统支持多种还款方式，具体取值参见数据字典。
""",
        
        "xdan-v2-answer": """根据文档内容，`repayMethod`字段是借款申请接口的必填参数，用于指定还款方式。

文档提到"系统支持多种还款方式，具体取值参见数据字典"，但当前文档中未找到具体的枚举值定义。

基于金融系统常见设计，还款方式通常包括等额本息、等额本金等，但需要查阅完整的数据字典文档以获取准确的取值列表。""",
        
        "xdan-v2-evaluation": "⚠️ xDAN-V2 一般 | 得分45.0% | ❌ RAG召回不足 | ❌ 答案不准确 | ❌ 信息利用不足",
        "xdan-v2-score": 0.45,
        "xdan-v2-detailed-scores": {
            "RAG召回质量": 5,   # 召回内容相关度低，缺少关键信息
            "答案准确性": 8,    # 未能提供具体取值
            "信息利用率": 10,   # 利用了有限的信息
            "推理合理性": 10,   # 承认了信息不足
            "完整性": 7,        # 回答不完整
            "表达清晰度": 5     # 表达一般
        },
        
        "deepseek-answer": """根据文档1中提供的借款申请接口（`applyLoan`）参数说明，`repayMethod`字段的取值及对应关系如下：

**枚举值及业务含义**：
- `00`：等额本金
- `01`：等额本息
- `02`：先息后本
- `03`：等本等息

**与平台文档的关系**：
1. 该字段为必填参数（标记为"必填"），用于明确借款的还款方式。
2. 取值与文档中定义的还款方式完全对应，采用两位数字编码形式标准化传输。
3. 合作方调用时必须严格使用上述枚举值，否则可能导致业务处理异常。""",
        
        "deepseek-evaluation": "🌟 DeepSeek 优秀 | 得分90.0% | ❌ RAG召回不足 | ✅ 答案准确 | ✅ 信息利用充分",
        "deepseek-score": 0.90,
        "deepseek-detailed-scores": {
            "RAG召回质量": 0,   # 无RAG
            "答案准确性": 25,   # 完全准确
            "信息利用率": 12,   # 基于知识库
            "推理合理性": 13,   # 逻辑清晰
            "完整性": 15,       # 回答完整
            "表达清晰度": 10    # 表达优秀
        },
        
        "comparison": "DeepSeek显著优于xDAN-V2，主要差异在答案准确性"
    },
    
    {
        "index": 3,
        "question": "当 `applyRepayment` 返回的 `repayStatus = P`，平台会走哪些后续处理流程？涉及哪些系统组件？(复杂)",
        "answer_correct": "ice-core-app 会定时调用 `queryRepayResult` 查询还款状态，并根据结果更新状态、发送短信、更新还款计划。涉及组件：ice-core-app、ice-partner-app、ice-gws-app。",
        
        # xDAN-V2 优秀的RAG召回示例
        "xdan-v2-rag": """【文档1】(相关度: 0.95)
还款处理流程说明：
1. 当applyRepayment接口返回repayStatus=P（处理中）时，表示还款请求已接收但尚未完成
2. ice-core-app会将还款记录状态更新为"处理中"
3. 系统会启动定时任务，每10分钟调用一次queryRepayResult接口查询最终状态
4. 调用链路：ice-core-app → ice-partner-app → ice-gws-app → 机构

【文档2】(相关度: 0.88)
还款状态流转规则：
- P（处理中）→ S（成功）：更新还款计划，发送成功短信
- P（处理中）→ F（失败）：标记失败，发送失败短信
- P（处理中）→ P（处理中）：继续等待，下次轮询

【文档3】(相关度: 0.82)
系统组件职责：
- ice-core-app：核心业务处理，状态管理，定时任务调度
- ice-partner-app：路由层，处理合作方请求转发
- ice-gws-app：网关层，与机构通信，处理加解密
""",
        
        "xdan-v2-answer": """根据文档1-3的详细说明，当`applyRepayment`返回`repayStatus = P`（处理中）时，平台会执行以下后续处理流程：

## 1. 状态更新流程
- ice-core-app立即将还款记录状态更新为"处理中"（文档1）
- 触发还款状态监控流程

## 2. 定时查询机制
- **查询频率**：每10分钟执行一次（文档1）
- **查询接口**：`queryRepayResult`
- **调用链路**：ice-core-app → ice-partner-app → ice-gws-app → 机构

## 3. 状态流转处理（文档2）
根据查询结果执行不同处理：
- **P→S（成功）**：
  - 更新还款计划状态为"已还款"
  - 发送还款成功短信通知用户
  - 更新借据信息
  
- **P→F（失败）**：
  - 标记还款失败
  - 发送还款失败短信
  - 记录失败原因
  
- **P→P（继续处理中）**：
  - 保持当前状态
  - 等待下一轮查询

## 4. 涉及的系统组件及职责（文档3）
1. **ice-core-app**：
   - 核心业务处理
   - 状态管理和流转
   - 定时任务调度
   
2. **ice-partner-app**：
   - 请求路由和转发
   - 参数转换
   
3. **ice-gws-app**：
   - 机构通信网关
   - 加解密处理
   - 协议转换

整个流程确保了异步还款处理的可靠性和最终一致性。""",
        
        "xdan-v2-evaluation": "🌟 xDAN-V2 优秀 | 得分96.0% | ✅ RAG召回优秀 | ✅ 答案准确 | ✅ 信息利用充分",
        "xdan-v2-score": 0.96,
        "xdan-v2-detailed-scores": {
            "RAG召回质量": 20,  # 召回了完美匹配的文档
            "答案准确性": 25,   # 完全准确且详细
            "信息利用率": 15,   # 充分利用了所有信息
            "推理合理性": 15,   # 逻辑严密
            "完整性": 15,       # 非常完整
            "表达清晰度": 10    # 结构化表达优秀
        },
        
        "deepseek-answer": """根据文档内容，当applyRepayment返回repayStatus = P时，平台会：

1. 定时调用queryRepayResult查询状态
2. 根据返回结果更新状态
3. 涉及的系统包括ice-core-app等

（注：文档中具体细节不够清晰）""",
        
        "deepseek-evaluation": "⚠️ DeepSeek 一般 | 得分55.0% | ❌ RAG召回不足 | ⚠️ 答案基本准确 | ⚠️ 信息利用一般",
        "deepseek-score": 0.55,
        "deepseek-detailed-scores": {
            "RAG召回质量": 0,
            "答案准确性": 15,   # 基本要点正确但不详细
            "信息利用率": 8,
            "推理合理性": 10,
            "完整性": 8,        # 过于简略
            "表达清晰度": 7
        },
        
        "comparison": "xDAN-V2显著优于DeepSeek，主要差异在RAG召回质量"
    }
]

# 生成示例文件
def generate_example():
    """生成详细对比示例"""
    
    # 添加汇总统计
    total = len(example_data)
    xdan_wins = sum(1 for item in example_data if item['xdan-v2-score'] > item['deepseek-score'])
    deepseek_wins = sum(1 for item in example_data if item['deepseek-score'] > item['xdan-v2-score'])
    
    avg_xdan_score = sum(item['xdan-v2-score'] for item in example_data) / total
    avg_deepseek_score = sum(item['deepseek-score'] for item in example_data) / total
    avg_rag_quality = sum(item['xdan-v2-detailed-scores']['RAG召回质量'] for item in example_data) / total
    
    summary = {
        "统计摘要": {
            "总问题数": total,
            "xDAN-V2胜出": f"{xdan_wins} ({xdan_wins/total:.1%})",
            "DeepSeek胜出": f"{deepseek_wins} ({deepseek_wins/total:.1%})",
            "xDAN-V2平均得分": f"{avg_xdan_score:.1%}",
            "DeepSeek平均得分": f"{avg_deepseek_score:.1%}",
            "xDAN-V2平均RAG召回质量": f"{avg_rag_quality:.1f}/20"
        },
        "关键发现": [
            "RAG召回质量直接影响答案准确性",
            "即使有优秀的生成模型，RAG召回不足也会导致答案质量下降",
            "xDAN-V2在RAG召回充分时表现优异",
            "DeepSeek在没有RAG支持下仍能提供较好答案，说明其知识库较为丰富"
        ]
    }
    
    result = {
        "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "说明": "基于RAG内容的详细对比评价示例",
        "评价维度说明": {
            "RAG召回质量": "评估召回文档的相关性和完整性 (0-20分)",
            "答案准确性": "评估答案与标准答案的匹配程度 (0-25分)",
            "信息利用率": "评估对召回信息的利用程度 (0-15分)",
            "推理合理性": "评估推理逻辑的合理性 (0-15分)",
            "完整性": "评估答案的完整程度 (0-15分)",
            "表达清晰度": "评估表达的清晰程度 (0-10分)"
        },
        "详细对比数据": example_data,
        "统计汇总": summary
    }
    
    # 保存文件
    output_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/RAG详细对比评价示例.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成详细对比评价示例：{output_file}")
    
    # 打印关键洞察
    print("\n📊 关键洞察：")
    print("1. RAG召回质量是影响答案质量的关键因素")
    print("2. 高质量的RAG召回（如示例3）能够支撑生成准确、完整、有深度的答案")
    print("3. RAG召回不足时（如示例2），即使是先进的模型也难以生成准确答案")
    print("4. 基于RAG内容的评价更加客观，能够区分是检索问题还是生成问题")

if __name__ == "__main__":
    generate_example()