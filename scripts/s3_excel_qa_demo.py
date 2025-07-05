#!/usr/bin/env python3
"""
S3 Excel Q&A Script - 演示版本
只处理前5个问题作为演示
"""

import os
import sys
import pandas as pd
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import time
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/gump_m2/CascadeProjects/ragflow-api-client')

# Load environment variables
load_dotenv()

# 导入S3服务
from src.services.service_factory import get_default_service
from src.clients.ragflow_client import RAGFlowClient

# S3模型配置 - 从环境变量加载
S3_GENERATOR_API_BASE = os.getenv("S3_GENERATOR_API_BASE")
S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME") 
S3_GENERATOR_API_KEY = os.getenv("S3_GENERATOR_API_KEY")

# RAGFlow配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# 只处理前N个问题
MAX_QUESTIONS = 5


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
            max_rounds=3,
            stream=False
        ):
            result = res
            break  # 非流式模式，只取第一个结果
        
        if result and result.get('workflow_completed'):
            answer = result.get('final_answer', '')
            selected_docs = result.get('selected_documents', [])
            rounds = result.get('rounds', [])
            
            return {
                'success': True,
                'answer': answer,
                'documents_count': len(selected_docs),
                'search_rounds': len(rounds),
                'search_process': [f"轮次{i+1}: {r.get('search_query', 'N/A')}" for i, r in enumerate(rounds)]
            }
        else:
            return {
                'success': False,
                'answer': '未能获取有效答案',
                'error': 'S3工作流未完成'
            }
            
    except Exception as e:
        print(f"S3服务错误: {e}")
        return {
            'success': False,
            'answer': f'[错误] {str(e)}',
            'error': str(e)
        }


async def process_excel_qa_demo(excel_path: str):
    """处理Excel中的问答（演示版本）"""
    
    # 读取Excel文件
    print(f"\n📖 读取Excel文件: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # 检查必要的列
    question_col = '阶段二问题'
    result_col = 'xdan结果v2'
    
    if question_col not in df.columns:
        raise Exception(f"找不到问题列 '{question_col}'")
    
    # 获取有效的问题（非空）- 只取前MAX_QUESTIONS个
    valid_mask = df[question_col].notna()
    valid_indices = df[valid_mask].index.tolist()[:MAX_QUESTIONS]
    
    print(f"✅ 找到 {sum(valid_mask)} 个问题，演示处理前 {len(valid_indices)} 个")
    
    # 创建结果DataFrame
    results_data = []
    
    # 批量处理问题
    print(f"\n📝 开始处理问题...")
    
    for idx, q_idx in enumerate(valid_indices):
        question = df.loc[q_idx, question_col]
        
        print(f"\n[{idx+1}/{len(valid_indices)}] 处理问题: {question[:60]}...")
        
        try:
            # 调用S3框架获取答案
            result = await ask_question_with_s3(question, [DEFAULT_DATASET_ID])
            
            if result['success']:
                # 准备结果数据
                result_row = {
                    '序号': q_idx + 1,
                    '阶段二问题': question,
                    'xdan结果v2': result['answer'],
                    '文档数量': result.get('documents_count', 0),
                    '搜索轮数': result.get('search_rounds', 0),
                    '搜索过程': ' -> '.join(result.get('search_process', [])),
                    '处理状态': '成功'
                }
                
                print(f"   ✅ 获取答案成功")
                print(f"   - 答案预览: {result['answer'][:100]}...")
                print(f"   - 找到文档: {result.get('documents_count', 0)}")
                print(f"   - 搜索轮数: {result.get('search_rounds', 0)}")
            else:
                result_row = {
                    '序号': q_idx + 1,
                    '阶段二问题': question,
                    'xdan结果v2': result['answer'],
                    '文档数量': 0,
                    '搜索轮数': 0,
                    '搜索过程': '',
                    '处理状态': '失败'
                }
                print(f"   ❌ 获取答案失败: {result.get('error', '未知错误')}")
            
            results_data.append(result_row)
            
            # 避免请求过快
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            result_row = {
                '序号': q_idx + 1,
                '阶段二问题': question,
                'xdan结果v2': f"[错误] {str(e)}",
                '文档数量': 0,
                '搜索轮数': 0,
                '搜索过程': '',
                '处理状态': '错误'
            }
            results_data.append(result_row)
    
    # 创建结果DataFrame
    results_df = pd.DataFrame(results_data)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/S3结果演示_{timestamp}.xlsx"
    results_df.to_excel(output_path, index=False)
    
    print(f"\n✅ 演示结果已保存到: {output_path}")
    
    # 显示统计
    success_count = len(results_df[results_df['处理状态'] == '成功'])
    print(f"\n📊 处理统计:")
    print(f"   - 处理问题数: {len(results_df)}")
    print(f"   - 成功: {success_count}")
    print(f"   - 失败: {len(results_df) - success_count}")
    
    if success_count > 0:
        avg_docs = results_df[results_df['处理状态'] == '成功']['文档数量'].mean()
        avg_rounds = results_df[results_df['处理状态'] == '成功']['搜索轮数'].mean()
        print(f"\n📈 搜索效果:")
        print(f"   - 平均找到文档数: {avg_docs:.1f}")
        print(f"   - 平均搜索轮数: {avg_rounds:.1f}")
    
    # 显示结果预览
    print("\n📄 结果预览:")
    for _, row in results_df.iterrows():
        print(f"\n问题 {int(row['序号'])}: {row['阶段二问题'][:50]}...")
        print(f"状态: {row['处理状态']}")
        if row['处理状态'] == '成功':
            print(f"答案: {row['xdan结果v2'][:150]}...")
            print(f"文档数: {row['文档数量']}, 搜索轮数: {row['搜索轮数']}")


def main():
    """主函数"""
    excel_path = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703.xlsx'
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"❌ Excel文件不存在: {excel_path}")
        return
    
    # 检查配置
    print(f"🔧 环境配置:")
    print(f"   - RAGFlow API: {RAGFLOW_API_URL}")
    print(f"   - 数据集ID: {DEFAULT_DATASET_ID}")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    print(f"   - S3模型API: {S3_GENERATOR_API_BASE}")
    print(f"   - 演示问题数: {MAX_QUESTIONS}")
    
    if not all([S3_GENERATOR_API_BASE, S3_GENERATOR_MODEL_NAME, S3_GENERATOR_API_KEY]):
        print("\n❌ 缺少S3模型配置，请检查.env文件")
        return
    
    # 检查RAGFlow连接
    print("\n🔍 检查RAGFlow连接...")
    try:
        client = RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        result = client.list_datasets(page=1, page_size=1)
        if result.get('code') == 0:
            print("✅ RAGFlow连接成功")
        else:
            print(f"❌ RAGFlow连接失败: {result.get('message')}")
            return
    except Exception as e:
        print(f"❌ RAGFlow连接错误: {e}")
        return
    
    # 运行异步处理
    asyncio.run(process_excel_qa_demo(excel_path))


if __name__ == "__main__":
    main()