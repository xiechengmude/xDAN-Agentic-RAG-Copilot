#!/usr/bin/env python3
"""
调试S3流程
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper
from src.services.enhanced_s3_rag_service import EnhancedS3RAGService, S3_SYSTEM_PROMPT
from src.clients.llm_client import LLMClient

def test_debug_s3():
    """调试S3流程"""
    # 配置
    api_url = "http://150.109.16.195:7080"
    api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
    dataset_id = "7e8d9e924cde11f0afc90242ac140006"
    
    print("初始化客户端...")
    
    # 初始化
    wrapper = RAGFlowSDKWrapper(api_url=api_url, api_key=api_key)
    llm_client = LLMClient(
        base_url="http://51.159.189.105:7032/v1",
        model_name="xDAN-R2-Qwen3-14b-RagRL-step450-0618"
    )
    service = EnhancedS3RAGService(wrapper, llm_client)
    
    # 测试问题
    question = "什么是智信平台？"
    print(f"\n测试问题: {question}")
    print("=" * 60)
    
    # 步骤1: 测试检索
    print("\n1. 测试检索...")
    chunks, success = service.search_step(
        question=question,
        dataset_ids=[dataset_id],
        top_k=10,
        similarity_threshold=0.3
    )
    
    print(f"检索成功: {success}")
    print(f"找到 {len(chunks)} 个chunks")
    
    if not chunks:
        print("错误：没有找到任何文档")
        return
    
    # 步骤2: 格式化结果
    print("\n2. 格式化搜索结果...")
    formatted_text, doc_mapping = service.format_search_results(chunks[:5])  # 只用前5个
    print("格式化文本预览:")
    print(formatted_text[:500] + "...")
    
    # 步骤3: 测试LLM决策
    print("\n3. 测试LLM决策...")
    initial_prompt = f"""<question>
{question}
</question>
<information>
{formatted_text}
</information>"""
    
    messages = [{"role": "user", "content": S3_SYSTEM_PROMPT + initial_prompt}]
    
    try:
        llm_response = llm_client.chat_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # 提取实际的响应内容
        if isinstance(llm_response, dict):
            agent_response = llm_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            agent_response = llm_response
        
        print("Agent响应:")
        print(agent_response[:500] + "..." if len(agent_response) > 500 else agent_response)
        
        # 测试提取功能
        print("\n4. 测试响应解析...")
        important_docs = service.extract_important_docs(agent_response)
        print(f"重要文档ID: {important_docs}")
        
        is_complete = service.is_search_complete(agent_response)
        print(f"搜索完成: {is_complete}")
        
        new_query = service.extract_search_query(agent_response)
        print(f"新查询: {new_query}")
        
    except Exception as e:
        print(f"LLM调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 步骤4: 完整S3流程
    print("\n5. 运行完整S3流程...")
    try:
        result = service.s3_search_process(
            question=question,
            dataset_ids=[dataset_id],
            max_rounds=3,
            top_k=10,
            similarity_threshold=0.3
        )
        
        print(f"搜索轮数: {result['search_rounds']}")
        print(f"选中文档数: {len(result['selected_documents'])}")
        print(f"最终上下文长度: {len(result['final_context'])}")
        
        if result['selected_documents']:
            print("\n选中的文档:")
            for i, doc in enumerate(result['selected_documents'], 1):
                print(f"\n文档 {i}:")
                print(f"  内容: {doc['content'][:100]}...")
                print(f"  相似度: {doc.get('similarity', 'N/A')}")
    
    except Exception as e:
        print(f"S3流程失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_debug_s3()