#!/usr/bin/env python3
"""
S3 JSON问答测试脚本 - 测试前3个问题
"""

import json
import os
import sys
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

async def test_s3_json():
    """测试S3 JSON问答"""
    
    # 读取JSON文件
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_fixed.json'
    with open(json_file, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    # 只处理前3个问题
    test_data = qa_data[:3]
    
    # 创建S3服务
    s3_service = get_default_service()
    dataset_ids = [DEFAULT_DATASET_ID]
    
    results = []
    
    for i, qa_item in enumerate(test_data, 1):
        print(f"\n{'='*60}")
        print(f"处理第 {i}/3 个问题")
        
        question = qa_item['question']
        correct_answer = qa_item['answer_correct']
        
        print(f"问题: {question}")
        print(f"正确答案: {correct_answer}")
        
        # 调用S3服务
        result = None
        async for res in s3_service.ask(
            question=question,
            dataset_ids=dataset_ids,
            max_rounds=3,
            stream=False
        ):
            result = res
            break
        
        if result and result.get('workflow_completed'):
            generated_answer = result.get('final_answer', '')
            print(f"\nS3生成答案: {generated_answer}")
            
            # 简单对比
            if correct_answer.lower() in generated_answer.lower():
                evaluation = "✅ 答案基本正确"
            else:
                evaluation = "❌ 答案有差异"
            
            print(f"\n对比评价: {evaluation}")
        else:
            print("❌ S3生成失败")
            generated_answer = "生成失败"
            evaluation = "❌ 生成失败"
        
        results.append({
            "question": question,
            "answer_correct": correct_answer,
            "xdan-rag-system": generated_answer,
            "对比评价": evaluation
        })
        
        # 添加延迟
        await asyncio.sleep(2)
    
    # 保存结果
    output_file = f'/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试完成，结果保存到: {output_file}")

if __name__ == "__main__":
    print("🚀 开始S3 JSON问答测试 (使用xDAN模型)")
    print(f"📊 配置: {os.getenv('S3_GENERATOR_MODEL_NAME')}")
    asyncio.run(test_s3_json())