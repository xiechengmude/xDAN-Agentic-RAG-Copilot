#!/usr/bin/env python3
"""
S3 JSON问答处理脚本 - DeepSeek v2版本
通过DeepSeek模型提高答案质量和准确度
"""

import json
import os
import sys
from datetime import datetime
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# DeepSeek优化的系统提示
DEEPSEEK_SYSTEM_PROMPT = """你是一个资深的金融API技术专家，专门解答智信平台API文档相关问题。

回答要求：
1. **技术精确性**：使用准确的接口名、参数名、枚举值，避免任何技术细节错误
2. **业务理解**：深入理解金融业务流程，包括授信、借款、还款的完整链路
3. **系统架构**：清楚各系统组件(ice-pfs-app、ice-partner-app、ice-gws-app、ice-core-app等)的职责和调用关系
4. **完整性**：回答要覆盖问题的所有方面，不遗漏关键信息
5. **逻辑性**：基于文档进行合理推理，关联相关信息
6. **诚实性**：如确实没有相关信息，明确说明，但要尝试从上下文推理

特别注意：
- 区分不同接口的具体用途(如applyCredit vs applyCertification vs applyLoan)
- 理解状态流转逻辑(如授信状态S/F/R，还款状态P/S/F等)
- 掌握系统间调用链路(前端→ice-pfs-app→ice-partner-app→ice-gws-app→机构)
- 关注业务场景差异(合作方批扣 vs 机构批扣，同步 vs 异步通知等)
"""

async def ask_question_with_deepseek(question: str, dataset_ids: List[str]) -> str:
    """使用DeepSeek模型进行问答"""
    try:
        # 创建S3服务实例
        s3_service = get_default_service()
        
        # 构建增强问题
        enhanced_question = f"{DEEPSEEK_SYSTEM_PROMPT}\n\n问题：{question}\n\n请基于API文档内容，给出专业、准确、完整的技术答案："
        
        # 使用S3服务执行问答
        result = None
        async for res in s3_service.ask(
            question=enhanced_question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            result = res
            break
        
        if result and result.get('workflow_completed'):
            return result.get('final_answer', '')
        else:
            return None
            
    except Exception as e:
        print(f"❌ DeepSeek服务错误: {e}")
        return None


def comprehensive_evaluation(generated_answer, correct_answer):
    """DeepSeek版本的综合评价函数"""
    if not generated_answer or generated_answer == "生成失败":
        return "❌ DeepSeek生成失败 | 未能获取有效答案", 0.0
    
    generated_lower = generated_answer.lower()
    correct_lower = correct_answer.lower()
    
    # 关键技术要素
    technical_keywords = [
        # 接口名称
        'applycredit', 'applycertification', 'checkuser', 'verifycode', 
        'noticecreditresult', 'querycreditresult', 'loantrial', 'applyloan',
        'applyrepayment', 'queryrepayresult', 'noticerepayment',
        
        # 系统组件
        'ice-pfs-app', 'ice-partner-app', 'ice-gws-app', 'ice-core-app', 'ice-crp-app',
        
        # 关键参数
        'agreementtime', 'repaymethod', 'bankcardinfo', 'credittype', 'rejectperiod',
        'repaysstatus', 'loantrial', 'certificationcode',
        
        # 状态值和格式
        'yyyymmddhhmmss', '00', '01', '02', '03', 
        '等额本金', '等额本息', '先息后本', '等本等息'
    ]
    
    # 业务流程关键词
    business_keywords = [
        'dubbo', 'http', '撞库', '绑卡', '授信', '借款', '还款', '批扣',
        '处理中', '成功', '失败', '循环额度', '一次性额度'
    ]
    
    all_keywords = technical_keywords + business_keywords
    
    # 计算关键词匹配度
    matches = 0
    total_checks = 0
    
    for keyword in all_keywords:
        if keyword in correct_lower:
            total_checks += 1
            if keyword in generated_lower:
                matches += 1
    
    # 基础匹配度
    if total_checks > 0:
        keyword_accuracy = matches / total_checks
    else:
        # 使用词汇重叠度
        generated_words = set(generated_lower.split())
        correct_words = set(correct_lower.split())
        common_words = generated_words & correct_words
        keyword_accuracy = len(common_words) / max(len(correct_words), 1)
    
    # 多维度评分
    dimensions = {
        "技术准确性": 0.35,  # 技术细节是否正确
        "业务理解": 0.25,    # 业务流程理解是否正确
        "完整性": 0.20,      # 是否覆盖所有要点
        "逻辑性": 0.10,      # 推理是否合理
        "表达清晰": 0.10     # 表达是否清晰
    }
    
    # 额外评分因子
    bonus_factors = 0.0
    penalty_factors = 0.0
    
    # 奖励因子
    if len(generated_answer) > len(correct_answer) * 0.8:  # 回答足够详细
        bonus_factors += 0.1
    if "文档" in generated_answer or "根据" in generated_answer:  # 有依据说明
        bonus_factors += 0.05
    if any(sys in generated_answer for sys in ['ice-', '系统', '组件']):  # 提及系统架构
        bonus_factors += 0.05
    
    # 惩罚因子
    if "未找到" in generated_answer and len(generated_answer) < 50:  # 过于简单的否定回答
        penalty_factors += 0.2
    if "文档中未" in generated_answer and keyword_accuracy < 0.3:  # 可能存在检索问题
        penalty_factors += 0.1
    
    # 最终评分
    final_score = keyword_accuracy + bonus_factors - penalty_factors
    final_score = max(0.0, min(1.0, final_score))  # 限制在0-1之间
    
    # 评级
    if final_score >= 0.85:
        return f"✅ DeepSeek优秀 | 综合得分{final_score:.1%}", final_score
    elif final_score >= 0.70:
        return f"✅ DeepSeek良好 | 综合得分{final_score:.1%}", final_score
    elif final_score >= 0.50:
        return f"⚠️ DeepSeek一般 | 综合得分{final_score:.1%}", final_score
    else:
        return f"❌ DeepSeek需改进 | 综合得分{final_score:.1%}", final_score


async def process_json_batch(json_file_path, batch_size=3):
    """批量处理JSON文件中的问题"""
    print(f"📖 读取JSON文件: {json_file_path}")
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"📊 共找到 {len(qa_data)} 个问题")
    
    dataset_ids = [DEFAULT_DATASET_ID]
    results = []
    
    # 分批处理
    for start_idx in range(0, len(qa_data), batch_size):
        end_idx = min(start_idx + batch_size, len(qa_data))
        batch = qa_data[start_idx:end_idx]
        
        print(f"\n{'='*60}")
        print(f"处理批次 {start_idx//batch_size + 1}: 问题 {start_idx+1}-{end_idx}")
        
        for i, qa_item in enumerate(batch, start_idx + 1):
            print(f"\n处理第 {i}/{len(qa_data)} 个问题")
            
            question = qa_item.get('question', '')
            correct_answer = qa_item.get('answer_correct', '')
            
            if not question:
                continue
            
            print(f"问题: {question[:80]}...")
            
            # 使用DeepSeek生成答案
            generated_answer = await ask_question_with_deepseek(question, dataset_ids)
            
            if generated_answer:
                print(f"✅ DeepSeek生成成功")
            else:
                print(f"❌ DeepSeek生成失败")
                generated_answer = "生成失败"
            
            # 综合评价
            comparison, accuracy = comprehensive_evaluation(generated_answer, correct_answer)
            
            # 构建结果
            result_item = {
                'index': i,
                'question': question,
                'answer_correct': correct_answer,
                'deepseek-rag-system': generated_answer,  # 使用新的字段名
                'deepseek-对比评价': comparison,           # 使用新的字段名
                'deepseek-综合得分': accuracy
            }
            
            # 保留原有的其他字段
            for key, value in qa_item.items():
                if key not in result_item:
                    result_item[key] = value
            
            results.append(result_item)
            
            print(f"DeepSeek评价: {comparison}")
            
            # 添加延迟避免API限制
            await asyncio.sleep(2)
        
        # 保存中间结果
        if end_idx < len(qa_data):
            print(f"\n💾 保存DeepSeek中间结果...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = json_file_path.replace('.json', f'_DeepSeek_batch_{start_idx//batch_size + 1}_{timestamp}.json')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results


async def main():
    """主函数"""
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json'
    
    print("🚀 开始DeepSeek S3 JSON问答处理（v2版本）")
    print(f"📊 使用模型: {os.getenv('S3_GENERATOR_MODEL_NAME')}")
    print("🔥 启用DeepSeek优化策略")
    
    # 处理问题
    results = await process_json_batch(json_file, batch_size=3)
    
    # 保存最终结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = json_file.replace('.json', f'_DeepSeek_S3结果_v2_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成统计报告
    total = len(results)
    excellent = sum(1 for r in results if '优秀' in r.get('deepseek-对比评价', ''))
    good = sum(1 for r in results if '良好' in r.get('deepseek-对比评价', ''))
    average = sum(1 for r in results if '一般' in r.get('deepseek-对比评价', ''))
    poor = sum(1 for r in results if '需改进' in r.get('deepseek-对比评价', '') or '失败' in r.get('deepseek-对比评价', ''))
    
    avg_score = sum(r.get('deepseek-综合得分', 0) for r in results) / max(total, 1)
    
    print(f"\n{'='*60}")
    print(f"📊 DeepSeek处理完成统计:")
    print(f"   - 总问题数: {total}")
    print(f"   - 优秀: {excellent} ({excellent/total:.1%})")
    print(f"   - 良好: {good} ({good/total:.1%})")
    print(f"   - 一般: {average} ({average/total:.1%})")
    print(f"   - 需改进/失败: {poor} ({poor/total:.1%})")
    print(f"   - 平均综合得分: {avg_score:.1%}")
    print(f"\n📁 DeepSeek结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())