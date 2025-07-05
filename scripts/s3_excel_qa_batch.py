#!/usr/bin/env python3
"""
S3 Excel Q&A Script - 分批处理版本
每次处理指定数量的问题，支持断点续传
"""

import os
import sys
import pandas as pd
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import time
import json
import argparse
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


def get_progress_info(excel_path: str):
    """获取进度信息"""
    # 查找已存在的结果文件
    base_dir = os.path.dirname(excel_path)
    base_name = os.path.basename(excel_path).replace('.xlsx', '')
    
    result_files = []
    for f in os.listdir(base_dir):
        if f.startswith(base_name) and 'S3结果' in f and f.endswith('.xlsx'):
            result_files.append(os.path.join(base_dir, f))
    
    if result_files:
        # 按修改时间排序，获取最新的文件
        result_files.sort(key=os.path.getmtime, reverse=True)
        latest_file = result_files[0]
        progress_file = latest_file.replace('.xlsx', '_progress.json')
        
        if os.path.exists(progress_file):
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                return latest_file, progress_data.get('processed_indices', [])
    
    return None, []


async def process_batch(excel_path: str, batch_size: int = 3):
    """分批处理Excel中的问答"""
    
    # 检查进度
    result_file, processed_indices = get_progress_info(excel_path)
    
    if result_file:
        print(f"📂 发现已存在的进度文件")
        print(f"   - 结果文件: {os.path.basename(result_file)}")
        print(f"   - 已处理: {len(processed_indices)} 个问题")
        df = pd.read_excel(result_file)
    else:
        print(f"📖 读取原始Excel文件: {excel_path}")
        df = pd.read_excel(excel_path)
        # 创建新的结果文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_file = excel_path.replace('.xlsx', f'_S3结果_{timestamp}.xlsx')
        processed_indices = []
    
    # 检查必要的列
    question_col = '阶段二问题'
    result_col = 'xdan结果v2'
    
    if question_col not in df.columns:
        raise Exception(f"找不到问题列 '{question_col}'")
    
    # 确保结果列存在
    for col in [result_col, '文档数量', '搜索轮数', '搜索过程']:
        if col not in df.columns:
            df[col] = ''
    
    # 获取未处理的问题
    valid_indices = df[df[question_col].notna()].index.tolist()
    remaining_indices = [idx for idx in valid_indices if idx not in processed_indices]
    
    if len(remaining_indices) == 0:
        print("✅ 所有问题已处理完成！")
        return
    
    # 本次要处理的问题
    batch_indices = remaining_indices[:batch_size]
    
    print(f"\n📊 处理统计:")
    print(f"   - 总问题数: {len(valid_indices)}")
    print(f"   - 已处理: {len(processed_indices)}")
    print(f"   - 待处理: {len(remaining_indices)}")
    print(f"   - 本批次: {len(batch_indices)}")
    
    # 处理本批次问题
    print(f"\n🚀 开始处理本批次 {len(batch_indices)} 个问题...")
    
    for i, q_idx in enumerate(batch_indices):
        question = df.loc[q_idx, question_col]
        overall_progress = len(processed_indices) + i + 1
        
        print(f"\n[{i+1}/{len(batch_indices)}] (总进度: {overall_progress}/{len(valid_indices)}) 处理问题: {question[:50]}...")
        
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
            
            # 避免请求过快
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 处理失败: {e}")
            df.loc[q_idx, result_col] = f"[错误] {str(e)}"
            processed_indices.append(q_idx)
    
    # 保存结果和进度
    df.to_excel(result_file, index=False)
    
    progress_file = result_file.replace('.xlsx', '_progress.json')
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({
            'processed_indices': processed_indices,
            'timestamp': datetime.now().isoformat(),
            'total_questions': len(valid_indices),
            'batch_size': batch_size
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 结果已保存到: {result_file}")
    print(f"   进度文件: {progress_file}")
    
    # 显示完成情况
    remaining_count = len(valid_indices) - len(processed_indices)
    if remaining_count > 0:
        print(f"\n📋 还剩 {remaining_count} 个问题待处理")
        print(f"   预计还需运行 {(remaining_count + batch_size - 1) // batch_size} 次")
    else:
        print(f"\n🎉 所有 {len(valid_indices)} 个问题已处理完成！")
        
        # 生成最终统计
        success_count = df[df[result_col].notna() & ~df[result_col].str.startswith('[错误]', na=False)].shape[0]
        error_count = df[df[result_col].str.startswith('[错误]', na=False)].shape[0]
        
        print(f"\n📊 最终统计:")
        print(f"   - 成功: {success_count}")
        print(f"   - 失败: {error_count}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='S3 Excel批处理工具')
    parser.add_argument('--batch-size', type=int, default=3, help='每批处理的问题数量（默认3个）')
    parser.add_argument('--file', type=str, help='Excel文件路径')
    args = parser.parse_args()
    
    # Excel文件路径
    excel_path = args.file or '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703.xlsx'
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"❌ Excel文件不存在: {excel_path}")
        return
    
    # 检查配置
    print(f"🔧 配置信息:")
    print(f"   - Excel文件: {os.path.basename(excel_path)}")
    print(f"   - 批处理大小: {args.batch_size}")
    print(f"   - RAGFlow API: {RAGFLOW_API_URL}")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    
    if not all([S3_GENERATOR_API_BASE, S3_GENERATOR_MODEL_NAME, S3_GENERATOR_API_KEY]):
        print("\n❌ 缺少S3模型配置，请检查.env文件")
        return
    
    # 运行批处理
    asyncio.run(process_batch(excel_path, batch_size=args.batch_size))


if __name__ == "__main__":
    main()