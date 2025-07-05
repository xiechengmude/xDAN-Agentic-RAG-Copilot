#!/usr/bin/env python3
"""
S3 JSON问答处理脚本 - 分批处理版本
"""

import json
import os
import sys
from datetime import datetime
import time
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

async def ask_question_with_s3(question: str, dataset_ids: List[str]) -> Dict[str, Any]:
    """使用S3框架回答问题"""
    try:
        # 创建S3服务实例
        s3_service = get_default_service()
        
        # 使用S3服务执行问答
        result = None
        async for res in s3_service.ask(
            question=question,
            dataset_ids=dataset_ids,
            stream=False
        ):
            result = res
            break  # 只取第一个结果
        
        return result
        
    except Exception as e:
        print(f"❌ S3服务调用失败: {str(e)}")
        return None

def compare_answers(generated_answer, correct_answer):
    """对比生成答案与正确答案"""
    if not generated_answer:
        return "❌ S3生成失败 | 未能获取有效答案"
    
    # 简化的对比逻辑
    generated_clean = generated_answer.strip().lower()
    correct_clean = correct_answer.strip().lower()
    
    # 计算相似度（简单的关键词匹配）
    generated_keywords = set(generated_clean.split())
    correct_keywords = set(correct_clean.split())
    
    if len(correct_keywords) == 0:
        similarity = 0
    else:
        common_keywords = generated_keywords.intersection(correct_keywords)
        similarity = len(common_keywords) / len(correct_keywords)
    
    if similarity >= 0.8:
        return f"✅ S3优秀 | 答案准确完整，相似度{similarity:.1%}"
    elif similarity >= 0.6:
        return f"✅ S3良好 | 答案基本正确，相似度{similarity:.1%}"
    elif similarity >= 0.3:
        return f"⚠️ S3一般 | 答案部分正确，相似度{similarity:.1%}"
    else:
        return f"❌ S3较差 | 答案偏差较大，相似度{similarity:.1%}"

async def process_batch(qa_data, start_idx=0, batch_size=3):
    """分批处理问题"""
    dataset_ids = [DEFAULT_DATASET_ID]
    processed_count = 0
    failed_count = 0
    
    end_idx = min(start_idx + batch_size, len(qa_data))
    
    print(f"🔄 处理第 {start_idx+1}-{end_idx} 个问题（共 {len(qa_data)} 个）")
    
    for i in range(start_idx, end_idx):
        qa_item = qa_data[i]
        
        print(f"\n{'='*60}")
        print(f"处理第 {i+1}/{len(qa_data)} 个问题")
        
        question = qa_item.get('question', '')
        correct_answer = qa_item.get('answer_correct', '')
        
        if not question:
            print("❌ 跳过空问题")
            continue
        
        print(f"问题: {question[:100]}...")
        
        # 使用S3生成答案
        try:
            result = await ask_question_with_s3(question, dataset_ids)
            
            if result and 'answer' in result:
                generated_answer = result['answer']
                print(f"✅ 生成答案: {generated_answer[:100]}...")
                processed_count += 1
            else:
                print("❌ 未获取到答案")
                generated_answer = None
                failed_count += 1
            
        except Exception as e:
            print(f"❌ 处理异常: {str(e)}")
            generated_answer = None
            failed_count += 1
        
        # 对比答案
        comparison = compare_answers(generated_answer, correct_answer)
        
        # 更新结果
        qa_item['xdan-rag-system'] = generated_answer or "生成失败"
        qa_item['对比评价'] = comparison
        
        print(f"🔍 对比评价: {comparison}")
        
        # 添加延迟避免请求过快
        await asyncio.sleep(2)
    
    return processed_count, failed_count

async def main():
    """主函数"""
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_fixed.json'
    
    if not os.path.exists(json_file):
        print(f"❌ 文件不存在: {json_file}")
        return
    
    print("🚀 开始S3 JSON问答处理（分批模式）...")
    
    # 读取JSON文件
    with open(json_file, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"📊 共找到 {len(qa_data)} 个问题")
    
    # 分批处理，每次处理3个问题
    batch_size = 3
    total_processed = 0
    total_failed = 0
    
    for start_idx in range(0, len(qa_data), batch_size):
        print(f"\n{'🔄 批次处理':=^60}")
        
        processed, failed = await process_batch(qa_data, start_idx, batch_size)
        total_processed += processed
        total_failed += failed
        
        print(f"\n📊 本批次统计: 成功 {processed}, 失败 {failed}")
        print(f"📊 总体统计: 成功 {total_processed}, 失败 {total_failed}")
        
        # 保存中间结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_output = json_file.replace('_fixed.json', f'_S3结果_batch_{start_idx}_{timestamp}.json')
        
        with open(temp_output, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 中间结果已保存: {temp_output}")
        
        # 如果不是最后一批，等待一下
        if start_idx + batch_size < len(qa_data):
            print("⏱️ 等待10秒后处理下一批...")
            await asyncio.sleep(10)
    
    # 生成最终输出文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = json_file.replace('_fixed.json', f'_S3结果_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 处理完成!")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 最终统计: 成功 {total_processed}, 失败 {total_failed}")

if __name__ == "__main__":
    asyncio.run(main())