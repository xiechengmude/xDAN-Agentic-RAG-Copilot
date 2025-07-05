#!/usr/bin/env python3
"""
S3 Excel Q&A Script - 直接调用版本
直接使用S3服务，不依赖API服务器
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


def check_ragflow_connection():
    """检查RAGFlow连接"""
    try:
        client = RAGFlowClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        # 尝试列出数据集
        result = client.list_datasets(page=1, page_size=1)
        if result.get('code') == 0:
            print("✅ RAGFlow连接成功")
            return True
        else:
            print(f"❌ RAGFlow连接失败: {result.get('message')}")
            return False
    except Exception as e:
        print(f"❌ RAGFlow连接错误: {e}")
        return False


async def process_excel_qa(excel_path: str, output_path: str = None):
    """处理Excel中的问答"""
    
    # 读取Excel文件
    print(f"\n📖 读取Excel文件: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # 检查必要的列
    question_col = '阶段二问题'
    result_col = 'xdan结果v2'
    
    if question_col not in df.columns:
        raise Exception(f"找不到问题列 '{question_col}'")
    
    # 如果结果列不存在，创建它
    if result_col not in df.columns:
        df[result_col] = ''
    
    # 添加额外的信息列
    if '文档数量' not in df.columns:
        df['文档数量'] = 0
    if '搜索轮数' not in df.columns:
        df['搜索轮数'] = 0
    if '搜索过程' not in df.columns:
        df['搜索过程'] = ''
    
    # 获取有效的问题（非空）
    valid_indices = df[df[question_col].notna()].index.tolist()
    questions = df.loc[valid_indices, question_col].tolist()
    print(f"✅ 找到 {len(questions)} 个问题需要处理")
    
    # 检查配置
    print(f"\n🔧 环境配置:")
    print(f"   - RAGFlow API: {RAGFLOW_API_URL}")
    print(f"   - 数据集ID: {DEFAULT_DATASET_ID}")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    print(f"   - S3模型API: {S3_GENERATOR_API_BASE}")
    
    if not all([S3_GENERATOR_API_BASE, S3_GENERATOR_MODEL_NAME, S3_GENERATOR_API_KEY]):
        print("\n❌ 缺少S3模型配置，请检查.env文件")
        return
    
    # 检查RAGFlow连接
    print("\n🔍 检查RAGFlow连接...")
    if not check_ragflow_connection():
        print("❌ 无法连接到RAGFlow，请检查配置")
        return
    
    # 批量处理问题
    print(f"\n📝 开始处理问题...")
    
    for idx, q_idx in enumerate(valid_indices):
        question = df.loc[q_idx, question_col]
        
        print(f"\n[{idx+1}/{len(questions)}] 处理问题: {question[:50]}...")
        
        try:
            # 调用S3框架获取答案
            result = await ask_question_with_s3(question, [DEFAULT_DATASET_ID])
            
            if result['success']:
                df.loc[q_idx, result_col] = result['answer']
                df.loc[q_idx, '文档数量'] = result.get('documents_count', 0)
                df.loc[q_idx, '搜索轮数'] = result.get('search_rounds', 0)
                df.loc[q_idx, '搜索过程'] = ' -> '.join(result.get('search_process', []))
                
                print(f"   ✅ 获取答案成功")
                print(f"   - 答案长度: {len(result['answer'])}")
                print(f"   - 找到文档: {result.get('documents_count', 0)}")
                print(f"   - 搜索轮数: {result.get('search_rounds', 0)}")
            else:
                df.loc[q_idx, result_col] = result['answer']
                print(f"   ❌ 获取答案失败: {result.get('error', '未知错误')}")
            
            # 避免请求过快
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            df.loc[q_idx, result_col] = f"[错误] {str(e)}"
    
    # 保存结果
    if output_path is None:
        # 在原文件名基础上添加时间戳
        base_name = os.path.splitext(excel_path)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"{base_name}_S3结果_{timestamp}.xlsx"
    
    df.to_excel(output_path, index=False)
    print(f"\n✅ 结果已保存到: {output_path}")
    
    # 统计信息
    success_count = df[df[result_col].notna() & ~df[result_col].str.startswith('[错误]', na=False)].shape[0]
    print(f"\n📊 处理统计:")
    print(f"   - 总行数: {len(df)}")
    print(f"   - 有效问题数: {len(questions)}")
    print(f"   - 成功获取答案: {success_count}")
    print(f"   - 失败数: {len(questions) - success_count}")
    
    # 显示搜索效果统计
    avg_docs = df.loc[valid_indices, '文档数量'].mean()
    avg_rounds = df.loc[valid_indices, '搜索轮数'].mean()
    print(f"\n📈 搜索效果:")
    print(f"   - 平均找到文档数: {avg_docs:.1f}")
    print(f"   - 平均搜索轮数: {avg_rounds:.1f}")


def main():
    """主函数"""
    excel_path = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703.xlsx'
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"❌ Excel文件不存在: {excel_path}")
        return
    
    # 运行异步处理
    asyncio.run(process_excel_qa(excel_path))


if __name__ == "__main__":
    main()