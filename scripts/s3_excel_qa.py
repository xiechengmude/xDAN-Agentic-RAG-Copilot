#!/usr/bin/env python3
"""
S3 Excel Q&A Script
读取Excel中的问题，调用S3 API获取答案，并更新到Excel中
"""

import os
import sys
import pandas as pd
import requests
import json
from typing import List, Dict, Any
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API配置
API_BASE_URL = "http://localhost:8050"
API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")

# S3模型配置 - 从环境变量加载
S3_GENERATOR_API_BASE = os.getenv("S3_GENERATOR_API_BASE")
S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME") 
S3_GENERATOR_API_KEY = os.getenv("S3_GENERATOR_API_KEY")

# 默认数据集ID
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# 请求头
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def check_api_health():
    """检查API服务健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API服务健康检查通过")
            print(f"   - 服务版本: {data['data']['version']}")
            print(f"   - S3框架: {'✓' if data['data']['components']['s3_framework'] else '✗'}")
            print(f"   - RAGFlow: {'✓' if data['data']['components']['ragflow'] else '✗'}")
            print(f"   - LiteLLM: {'✓' if data['data']['components']['litellm'] else '✗'}")
            return True
        else:
            print(f"❌ API服务健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到API服务: {e}")
        return False


def create_chat_session(name: str, dataset_ids: List[str]) -> str:
    """创建一个新的对话会话"""
    payload = {
        "name": name,
        "dataset_ids": dataset_ids,
        "description": f"Excel问答批处理 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "llm_config": {
            "model_name": S3_GENERATOR_MODEL_NAME,
            "temperature": 0.7,
            "max_tokens": 2000
        }
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/chats", 
                           headers=HEADERS, 
                           json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return data['data']['id']
    else:
        raise Exception(f"创建对话失败: {response.status_code} - {response.text}")


def ask_question(chat_id: str, question: str, stream: bool = False) -> str:
    """向S3系统提问并获取答案"""
    payload = {
        "content": question,
        "stream": stream
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v1/chats/{chat_id}/completions",
                           headers=HEADERS,
                           json=payload,
                           timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        answer = data['data']['answer']
        
        # 打印S3搜索信息
        reference = data['data'].get('reference', {})
        if reference:
            print(f"   - 找到文档数: {reference.get('total', 0)}")
            print(f"   - 搜索轮数: {reference.get('search_rounds', 0)}")
            search_process = reference.get('search_process', [])
            if search_process:
                print(f"   - 搜索过程: {' -> '.join(search_process[:3])}")
        
        return answer
    else:
        raise Exception(f"获取答案失败: {response.status_code} - {response.text}")


def process_excel_qa(excel_path: str, output_path: str = None):
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
    
    # 获取有效的问题（非空）
    questions = df[df[question_col].notna()][question_col].tolist()
    print(f"✅ 找到 {len(questions)} 个问题需要处理")
    
    # 检查API健康状态
    print("\n🔍 检查API服务状态...")
    if not check_api_health():
        print("❌ API服务不可用，请先启动服务")
        return
    
    # 创建对话会话
    print(f"\n🚀 创建对话会话...")
    print(f"   - 使用数据集: {DEFAULT_DATASET_ID}")
    print(f"   - 使用模型: {S3_GENERATOR_MODEL_NAME}")
    chat_id = create_chat_session("Excel批量问答", [DEFAULT_DATASET_ID])
    print(f"✅ 对话会话创建成功: {chat_id}")
    
    # 批量处理问题
    print(f"\n📝 开始处理问题...")
    results = []
    
    for idx, (_, row) in enumerate(df.iterrows()):
        question = row.get(question_col)
        
        # 跳过空问题
        if pd.isna(question) or str(question).strip() == '':
            results.append('')
            continue
        
        print(f"\n[{idx+1}/{len(df)}] 处理问题: {question[:50]}...")
        
        try:
            # 调用S3 API获取答案
            answer = ask_question(chat_id, question)
            results.append(answer)
            print(f"   ✅ 获取答案成功 (长度: {len(answer)})")
            
            # 避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 获取答案失败: {e}")
            results.append(f"[错误] {str(e)}")
    
    # 更新结果到DataFrame
    df[result_col] = results
    
    # 保存结果
    if output_path is None:
        # 在原文件名基础上添加时间戳
        base_name = os.path.splitext(excel_path)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"{base_name}_S3结果_{timestamp}.xlsx"
    
    df.to_excel(output_path, index=False)
    print(f"\n✅ 结果已保存到: {output_path}")
    
    # 统计信息
    valid_results = [r for r in results if r and not r.startswith('[错误]')]
    print(f"\n📊 处理统计:")
    print(f"   - 总问题数: {len(df)}")
    print(f"   - 有效问题数: {len(questions)}")
    print(f"   - 成功获取答案: {len(valid_results)}")
    print(f"   - 失败数: {len(questions) - len(valid_results)}")


def main():
    """主函数"""
    excel_path = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test/副本奇富科技-RAG效果测试-人工核对-v2-0703.xlsx'
    
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        print(f"❌ Excel文件不存在: {excel_path}")
        return
    
    # 检查环境变量
    print("🔧 环境配置:")
    print(f"   - API地址: {API_BASE_URL}")
    print(f"   - 数据集ID: {DEFAULT_DATASET_ID}")
    print(f"   - S3模型: {S3_GENERATOR_MODEL_NAME}")
    print(f"   - S3模型API: {S3_GENERATOR_API_BASE}")
    
    if not all([S3_GENERATOR_API_BASE, S3_GENERATOR_MODEL_NAME, S3_GENERATOR_API_KEY]):
        print("\n❌ 缺少S3模型配置，请检查.env文件")
        return
    
    # 处理Excel问答
    process_excel_qa(excel_path)


if __name__ == "__main__":
    main()