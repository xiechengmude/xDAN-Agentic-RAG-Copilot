#!/usr/bin/env python3
"""
S3 JSON问答处理脚本 - 处理JSON格式的问答数据
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
from src.clients.ragflow_client import RAGFlowClient

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

class S3JsonQAProcessor:
    def __init__(self):
        """初始化S3处理器"""
        # 初始化S3服务
        self.s3_service = get_default_service()
        self.dataset_ids = [DEFAULT_DATASET_ID]
        
        self.processed_count = 0
        self.failed_count = 0
        self.results = []
        
    async def process_question(self, question_text):
        """使用S3框架处理单个问题"""
        try:
            print(f"\n🔍 开始处理问题...")
            print(f"问题: {question_text[:100]}...")
            
            # 使用S3服务执行问答
            result = None
            async for res in self.s3_service.ask(
                question=question_text,
                dataset_ids=self.dataset_ids,
                max_rounds=3,
                stream=False
            ):
                result = res
                break  # 只取第一个结果
            
            if not result:
                print("❌ S3服务未返回结果")
                return None
            
            # 检查工作流是否完成
            if result.get('workflow_completed'):
                # 提取最终答案
                answer = result.get('final_answer', '')
                if answer:
                    print(f"✅ 生成答案: {answer[:100]}...")
                    return answer
                else:
                    print("❌ 答案为空")
                    return None
            else:
                print("❌ S3工作流未完成")
                return None
            
        except Exception as e:
            print(f"❌ 处理问题时出错: {str(e)}")
            return None
    
    def compare_answers(self, generated_answer, correct_answer):
        """对比生成答案与正确答案"""
        if not generated_answer:
            return "❌ S3生成失败 | 未能获取有效答案"
        
        # 简化的对比逻辑，可以后续优化
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
    
    async def process_json_file(self, json_file_path):
        """处理JSON文件中的所有问题"""
        print(f"📖 读取JSON文件: {json_file_path}")
        
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            qa_data = json.load(f)
        
        print(f"📊 共找到 {len(qa_data)} 个问题")
        
        # 处理每个问题
        for i, qa_item in enumerate(qa_data, 1):
            print(f"\n{'='*60}")
            print(f"处理第 {i}/{len(qa_data)} 个问题")
            
            question = qa_item.get('question', '')
            correct_answer = qa_item.get('answer_correct', '')
            
            if not question:
                print("❌ 跳过空问题")
                continue
            
            # 使用S3生成答案
            generated_answer = await self.process_question(question)
            
            # 对比答案
            comparison = self.compare_answers(generated_answer, correct_answer)
            
            # 更新结果
            qa_item['xdan-rag-system'] = generated_answer or "生成失败"
            qa_item['对比评价'] = comparison
            
            if generated_answer:
                self.processed_count += 1
                print(f"✅ 问题 {i} 处理成功")
            else:
                self.failed_count += 1
                print(f"❌ 问题 {i} 处理失败")
            
            print(f"🔍 对比评价: {comparison}")
            
            # 添加延迟避免请求过快
            await asyncio.sleep(1)
        
        return qa_data
    
    def save_results(self, qa_data, original_file_path):
        """保存处理结果"""
        # 生成输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = original_file_path.replace('.json', f'_S3结果_{timestamp}.json')
        
        # 保存JSON文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 结果已保存到: {output_file}")
        
        # 生成统计报告
        self.generate_report(qa_data, output_file)
        
        return output_file
    
    def generate_report(self, qa_data, output_file):
        """生成统计报告"""
        total_questions = len(qa_data)
        
        # 统计评价分布
        excellent = len([qa for qa in qa_data if 'S3优秀' in qa.get('对比评价', '')])
        good = len([qa for qa in qa_data if 'S3良好' in qa.get('对比评价', '')])
        average = len([qa for qa in qa_data if 'S3一般' in qa.get('对比评价', '')])
        poor = len([qa for qa in qa_data if 'S3较差' in qa.get('对比评价', '') or 'S3生成失败' in qa.get('对比评价', '')])
        
        report = []
        report.append("=" * 80)
        report.append("S3 RAG系统JSON问答处理报告")
        report.append(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        report.append(f"\n📊 处理统计:")
        report.append(f"   - 总问题数: {total_questions}")
        report.append(f"   - 成功处理: {self.processed_count} ({self.processed_count/total_questions:.1%})")
        report.append(f"   - 处理失败: {self.failed_count} ({self.failed_count/total_questions:.1%})")
        
        report.append(f"\n🎯 答案质量分布:")
        report.append(f"   - 优秀: {excellent} ({excellent/total_questions:.1%})")
        report.append(f"   - 良好: {good} ({good/total_questions:.1%})")
        report.append(f"   - 一般: {average} ({average/total_questions:.1%})")
        report.append(f"   - 较差/失败: {poor} ({poor/total_questions:.1%})")
        
        # 详细问题列表
        report.append(f"\n📝 详细结果:")
        report.append("-" * 80)
        for i, qa in enumerate(qa_data, 1):
            question = qa.get('question', '')[:50] + "..."
            evaluation = qa.get('对比评价', '未评价')
            report.append(f"问题{i}: {evaluation} | {question}")
        
        # 保存报告
        report_file = output_file.replace('.json', '_处理报告.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"📊 处理报告已保存到: {report_file}")

async def main():
    """主函数"""
    json_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_fixed.json'
    
    if not os.path.exists(json_file):
        print(f"❌ 文件不存在: {json_file}")
        return
    
    print("🚀 开始S3 JSON问答处理...")
    
    # 创建处理器
    processor = S3JsonQAProcessor()
    
    # 处理JSON文件
    qa_data = await processor.process_json_file(json_file)
    
    # 保存结果
    output_file = processor.save_results(qa_data, json_file)
    
    print(f"\n🎉 处理完成!")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 处理统计: 成功 {processor.processed_count}, 失败 {processor.failed_count}")

if __name__ == "__main__":
    asyncio.run(main())