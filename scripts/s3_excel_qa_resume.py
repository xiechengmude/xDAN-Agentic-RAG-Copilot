#!/usr/bin/env python3
"""
S3 Excel Q&A Script - 支持断点续传版本
可以从上次中断的地方继续处理
"""

import os
import sys
import pandas as pd
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import time
import json
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


def save_progress(output_path: str, df: pd.DataFrame, processed_indices: List[int]):
    """保存进度"""
    # 保存当前的DataFrame
    df.to_excel(output_path, index=False)
    
    # 保存进度信息
    progress_file = output_path.replace('.xlsx', '_progress.json')
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            'processed_indices': processed_indices,
            'timestamp': datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    print(f"💾 进度已保存 (已处理: {len(processed_indices)})")


def load_progress(output_path: str) -> List[int]:
    """加载进度"""
    progress_file = output_path.replace('.xlsx', '_progress.json')
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('processed_indices', [])
    return []


async def process_excel_qa(excel_path: str, output_path: str = None, resume: bool = True, batch_size: int = 5):
    """处理Excel中的问答（支持断点续传）"""
    
    # 设置输出路径
    if output_path is None:
        base_name = os.path.splitext(excel_path)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"{base_name}_S3结果_{timestamp}.xlsx"
    
    # 读取Excel文件
    print(f"\n📖 读取Excel文件: {excel_path}")
    
    # 如果要恢复，先检查是否有已处理的文件
    if resume and os.path.exists(output_path):
        print(f"📂 发现已存在的输出文件，加载进度...")
        df = pd.read_excel(output_path)
        processed_indices = load_progress(output_path)
        print(f"✅ 已加载进度，之前已处理 {len(processed_indices)} 个问题")
    else:
        df = pd.read_excel(excel_path)
        processed_indices = []
    
    # 检查必要的列
    question_col = '阶段二问题'
    result_col = 'xdan结果v2'
    
    if question_col not in df.columns:
        raise Exception(f"找不到问题列 '{question_col}'")
    
    # 如果结果列不存在，创建它
    if result_col not in df.columns:
        df[result_col] = ''
    
    # 添加额外的信息列
    extra_cols = ['文档数量', '搜索轮数', '搜索过程']
    for col in extra_cols:
        if col not in df.columns:
            df[col] = ''
    
    # 获取有效的问题（非空）
    valid_indices = df[df[question_col].notna()].index.tolist()
    
    # 过滤已处理的索引
    remaining_indices = [idx for idx in valid_indices if idx not in processed_indices]
    
    print(f"✅ 总共 {len(valid_indices)} 个问题，还需处理 {len(remaining_indices)} 个")
    
    if len(remaining_indices) == 0:
        print("✅ 所有问题已处理完成！")
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
    
    # 批量处理问题
    print(f"\n📝 开始处理剩余的 {len(remaining_indices)} 个问题...")
    
    for i, q_idx in enumerate(remaining_indices):
        question = df.loc[q_idx, question_col]
        
        print(f"\n[{i+1}/{len(remaining_indices)}] (总进度: {len(processed_indices)+i+1}/{len(valid_indices)}) 处理问题: {question[:50]}...")
        
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
            
            # 记录已处理
            processed_indices.append(q_idx)
            
            # 每处理batch_size个问题保存一次进度
            if (i + 1) % batch_size == 0:
                save_progress(output_path, df, processed_indices)
            
            # 避免请求过快
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            df.loc[q_idx, result_col] = f"[错误] {str(e)}"
            processed_indices.append(q_idx)
    
    # 最终保存
    save_progress(output_path, df, processed_indices)
    print(f"\n✅ 所有问题处理完成！结果已保存到: {output_path}")
    
    # 统计信息
    success_count = df[df[result_col].notna() & ~df[result_col].str.startswith('[错误]', na=False)].shape[0]
    print(f"\n📊 处理统计:")
    print(f"   - 总行数: {len(df)}")
    print(f"   - 有效问题数: {len(valid_indices)}")
    print(f"   - 成功获取答案: {success_count}")
    print(f"   - 失败数: {len(valid_indices) - success_count}")
    
    # 显示搜索效果统计
    numeric_cols = df[['文档数量', '搜索轮数']].apply(pd.to_numeric, errors='coerce')
    avg_docs = numeric_cols['文档数量'].mean()
    avg_rounds = numeric_cols['搜索轮数'].mean()
    
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
    
    # 检查配置
    print(f"🔧 环境配置:")
    print(f"   - RAGFlow API: {RAGFLOW_API_URL}")
    print(f"   - 数据集ID: {DEFAULT_DATASET_ID}")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    print(f"   - S3模型API: {S3_GENERATOR_API_BASE}")
    
    if not all([S3_GENERATOR_API_BASE, S3_GENERATOR_MODEL_NAME, S3_GENERATOR_API_KEY]):
        print("\n❌ 缺少S3模型配置，请检查.env文件")
        return
    
    # 运行异步处理
    asyncio.run(process_excel_qa(excel_path, resume=True, batch_size=5))


if __name__ == "__main__":
    main()