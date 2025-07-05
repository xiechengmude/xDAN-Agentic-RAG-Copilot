#!/usr/bin/env python3
"""
S3 JSON问答处理 - 最终版本
使用最简洁有效的优化策略
"""

import json
import os
import sys
from datetime import datetime
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv

sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')
load_dotenv()

from src.services.service_factory import get_default_service

DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

class S3JsonProcessor:
    def __init__(self):
        self.s3_service = get_default_service()
        self.dataset_ids = [DEFAULT_DATASET_ID]
        self.processed_count = 0
        self.failed_count = 0
    
    async def process_question(self, question: str) -> str:
        """处理单个问题"""
        try:
            # 对特定类型的问题添加轻微提示
            if "接口" in question and "哪些" in question:
                # 对于询问接口列表的问题，稍微引导
                enhanced_q = question + " 请列出接口名称。"
            else:
                enhanced_q = question
            
            result = None
            async for res in self.s3_service.ask(
                question=enhanced_q,
                dataset_ids=self.dataset_ids,
                max_rounds=3,
                stream=False
            ):
                result = res
                break
            
            if result and result.get('workflow_completed'):
                return result.get('final_answer', '')
            return None
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            return None
    
    def evaluate_answer(self, generated: str, correct: str) -> tuple:
        """评估答案质量"""
        if not generated:
            return "❌ 生成失败", 0.0
        
        # 关键技术要素检查
        tech_keywords = {
            'interfaces': ['checkUser', 'applyCredit', 'applyCertification', 'verifyCode', 
                          'noticeCreditResult', 'queryCreditResult', 'applyLoan', 'loanTrial',
                          'applyRepayment', 'queryRepayResult', 'noticeRepayment'],
            'params': ['agreementTime', 'repayMethod', 'bankCardInfo', 'creditType',
                      'repayStatus', 'loanStatus', 'applyResult'],
            'values': ['yyyyMMddHHmmss', '00', '01', '02', '03', 'ice-pfs-app', 
                      'ice-partner-app', 'ice-gws-app', 'ice-core-app'],
            'keywords': ['等额本金', '等额本息', '先息后本', '等本等息', '循环额度', '处理中']
        }
        
        # 统计匹配情况
        gen_lower = generated.lower()
        correct_lower = correct.lower()
        
        matches = 0
        total_relevant = 0
        
        for category, keywords in tech_keywords.items():
            for keyword in keywords:
                if keyword.lower() in correct_lower:
                    total_relevant += 1
                    if keyword.lower() in gen_lower:
                        matches += 1
        
        # 如果正确答案中没有技术关键词，使用通用相似度
        if total_relevant == 0:
            common_words = set(gen_lower.split()) & set(correct_lower.split())
            score = len(common_words) / max(len(set(correct_lower.split())), 1)
        else:
            score = matches / total_relevant
        
        # 评级
        if score >= 0.8:
            return f"✅ 优秀 (匹配度{score:.0%})", score
        elif score >= 0.6:
            return f"✅ 良好 (匹配度{score:.0%})", score
        elif score >= 0.4:
            return f"⚠️ 一般 (匹配度{score:.0%})", score
        else:
            return f"❌ 较差 (匹配度{score:.0%})", score
    
    async def process_batch(self, qa_data: list, start_idx: int, batch_size: int):
        """批量处理"""
        end_idx = min(start_idx + batch_size, len(qa_data))
        
        for i in range(start_idx, end_idx):
            qa_item = qa_data[i]
            print(f"\n{'='*60}")
            print(f"处理 {i+1}/{len(qa_data)}: {qa_item['question'][:60]}...")
            
            # 生成答案
            answer = await self.process_question(qa_item['question'])
            
            if answer:
                self.processed_count += 1
                print("✅ 生成成功")
            else:
                self.failed_count += 1
                print("❌ 生成失败")
                answer = "生成失败"
            
            # 评估
            evaluation, score = self.evaluate_answer(answer, qa_item['answer_correct'])
            
            # 更新结果
            qa_item['xdan-rag-system'] = answer
            qa_item['对比评价'] = evaluation
            qa_item['匹配度'] = score
            
            print(f"📊 评价: {evaluation}")
            
            await asyncio.sleep(1)
        
        return qa_data[start_idx:end_idx]

async def main():
    """主函数"""
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_fixed.json'
    
    print("🚀 S3 JSON问答处理系统")
    print(f"📊 模型: {os.getenv('S3_GENERATOR_MODEL_NAME')}")
    print(f"📁 数据集: {DEFAULT_DATASET_ID}")
    
    # 读取数据
    with open(json_file, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    print(f"📝 共 {len(qa_data)} 个问题\n")
    
    # 创建处理器
    processor = S3JsonProcessor()
    
    # 批量处理
    batch_size = 5
    all_results = []
    
    for start_idx in range(0, len(qa_data), batch_size):
        print(f"\n🔄 批次 {start_idx//batch_size + 1}/{(len(qa_data)-1)//batch_size + 1}")
        
        batch_results = await processor.process_batch(qa_data, start_idx, batch_size)
        all_results.extend(batch_results)
        
        # 保存中间结果
        if start_idx + batch_size < len(qa_data):
            temp_file = f'/tmp/s3_json_batch_{start_idx//batch_size + 1}.json'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"💾 中间结果: {temp_file}")
    
    # 保存最终结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = json_file.replace('_fixed.json', f'_S3结果_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_data, f, ensure_ascii=False, indent=2)
    
    # 统计报告
    total = len(qa_data)
    avg_score = sum(item.get('匹配度', 0) for item in qa_data) / total
    
    print(f"\n{'='*60}")
    print(f"📊 最终统计:")
    print(f"   成功: {processor.processed_count}/{total} ({processor.processed_count/total:.1%})")
    print(f"   失败: {processor.failed_count}/{total}")
    print(f"   平均匹配度: {avg_score:.1%}")
    print(f"\n📁 结果文件: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())