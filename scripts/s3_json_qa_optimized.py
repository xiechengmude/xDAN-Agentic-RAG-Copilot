#!/usr/bin/env python3
"""
S3 JSON问答处理脚本 - 优化版本
通过改进prompt来提高答案精确度
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

# 优化的系统提示
SYSTEM_PROMPT = """你是一个技术文档专家。回答时请遵循以下原则：
1. 优先使用具体的接口名称（如checkUser、applyCredit等），而非描述性语言
2. 保持答案简洁精确，直接给出技术细节
3. 如果文档中没有相关信息，明确说明"文档中未找到相关信息"
4. 避免添加文档中未提及的额外步骤或信息
5. 使用原始的技术术语和参数名，不要翻译或解释"""

async def ask_question_with_s3_optimized(question: str, dataset_ids: List[str]) -> str:
    """使用优化后的S3框架回答问题"""
    try:
        # 创建S3服务实例
        s3_service = get_default_service()
        
        # 在问题前添加提示
        enhanced_question = f"{SYSTEM_PROMPT}\n\n问题：{question}\n\n请基于文档内容，给出精确的技术答案："
        
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
        print(f"❌ S3服务错误: {e}")
        return None


def compare_answers_advanced(generated_answer, correct_answer):
    """高级答案对比，检查关键技术要素"""
    if not generated_answer:
        return "❌ S3生成失败 | 未能获取有效答案", 0.0
    
    # 提取关键技术要素进行对比
    generated_lower = generated_answer.lower()
    correct_lower = correct_answer.lower()
    
    # 检查关键接口名称
    key_interfaces = ['checkuser', 'applycredit', 'applycertification', 'verifycode', 
                      'noticecreditresult', 'querycreditresult', 'applyloan', 'loantrial']
    
    # 检查关键参数名
    key_params = ['agreementtime', 'repaymethod', 'yyyymmddhhmmss', 'bankcardinfo']
    
    # 检查关键取值
    key_values = ['00', '01', '02', '03', '等额本金', '等额本息', '先息后本', '等本等息']
    
    # 计算技术要素匹配度
    matches = 0
    total_checks = 0
    
    # 检查接口名称
    for interface in key_interfaces:
        if interface in correct_lower:
            total_checks += 1
            if interface in generated_lower:
                matches += 1
    
    # 检查参数名
    for param in key_params:
        if param in correct_lower:
            total_checks += 1
            if param in generated_lower:
                matches += 1
    
    # 检查取值
    for value in key_values:
        if value in correct_lower:
            total_checks += 1
            if value in generated_lower:
                matches += 1
    
    # 计算技术精确度
    if total_checks > 0:
        accuracy = matches / total_checks
    else:
        # 如果没有技术要素，使用简单的文本相似度
        common_words = set(generated_lower.split()) & set(correct_lower.split())
        accuracy = len(common_words) / max(len(set(correct_lower.split())), 1)
    
    # 根据精确度给出评价
    if accuracy >= 0.8:
        return f"✅ S3优秀 | 技术要素匹配度{accuracy:.1%}", accuracy
    elif accuracy >= 0.6:
        return f"✅ S3良好 | 技术要素匹配度{accuracy:.1%}", accuracy
    elif accuracy >= 0.3:
        return f"⚠️ S3一般 | 技术要素匹配度{accuracy:.1%}", accuracy
    else:
        return f"❌ S3较差 | 技术要素匹配度{accuracy:.1%}", accuracy


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
            
            # 使用优化的S3生成答案
            generated_answer = await ask_question_with_s3_optimized(question, dataset_ids)
            
            if generated_answer:
                print(f"✅ 生成成功")
            else:
                print(f"❌ 生成失败")
                generated_answer = "生成失败"
            
            # 高级对比
            comparison, accuracy = compare_answers_advanced(generated_answer, correct_answer)
            
            # 构建包含index的结果
            result_item = {
                'index': i,  # 添加index列
                'question': question,
                'answer_correct': correct_answer,
                'xdan-rag-system': generated_answer,
                '对比评价': comparison,
                '技术精确度': accuracy
            }
            
            # 保留原有的其他字段
            for key, value in qa_item.items():
                if key not in result_item:
                    result_item[key] = value
            
            results.append(result_item)
            
            print(f"对比评价: {comparison}")
            
            # 添加延迟
            await asyncio.sleep(1)
        
        # 保存中间结果
        if end_idx < len(qa_data):
            print(f"\n💾 保存中间结果...")
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = json_file_path.replace('.json', f'_S3结果_batch_{start_idx//batch_size + 1}_{timestamp}.json')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results


async def main():
    """主函数"""
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json'
    
    print("🚀 开始S3 JSON问答处理（优化版）")
    print(f"📊 使用模型: {os.getenv('S3_GENERATOR_MODEL_NAME')}")
    print("✨ 启用优化提示策略")
    
    # 处理问题
    results = await process_json_batch(json_file, batch_size=3)
    
    # 保存最终结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = json_file.replace('.json', f'_S3结果_优化版_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成统计报告
    total = len(results)
    excellent = sum(1 for r in results if '优秀' in r.get('对比评价', ''))
    good = sum(1 for r in results if '良好' in r.get('对比评价', ''))
    average = sum(1 for r in results if '一般' in r.get('对比评价', ''))
    poor = sum(1 for r in results if '较差' in r.get('对比评价', '') or '失败' in r.get('对比评价', ''))
    
    avg_accuracy = sum(r.get('技术精确度', 0) for r in results) / max(total, 1)
    
    print(f"\n{'='*60}")
    print(f"📊 处理完成统计:")
    print(f"   - 总问题数: {total}")
    print(f"   - 优秀: {excellent} ({excellent/total:.1%})")
    print(f"   - 良好: {good} ({good/total:.1%})")
    print(f"   - 一般: {average} ({average/total:.1%})")
    print(f"   - 较差/失败: {poor} ({poor/total:.1%})")
    print(f"   - 平均技术精确度: {avg_accuracy:.1%}")
    print(f"\n📁 结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())