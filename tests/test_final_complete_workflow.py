"""
完整的全链路API测试 - 最终版本
包含所有修正后的接口调用
"""
import requests
import json
import time
from datetime import datetime

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 使用现有的已解析知识库进行完整测试
EXISTING_KB_ID = "7e8d9e924cde11f0afc90242ac140006"  # 360test00000


def parse_sse_response(response_text):
    """解析SSE响应"""
    results = []
    lines = response_text.split('\n')
    
    for line in lines:
        if line.startswith('data:'):
            try:
                json_part = line[5:].strip()
                parsed = json.loads(json_part)
                results.append(parsed)
            except json.JSONDecodeError:
                continue
    
    return results


def run_complete_test():
    """运行完整的API测试"""
    print(f"\n{'='*80}")
    print(f"RAGFlow 完整全链路API测试 - 最终版本")
    print(f"测试时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}")
    print(f"{'='*80}")
    
    results = []
    
    # ==================== 步骤1: 知识库管理测试 ====================
    print(f"\n🔷 步骤1: 知识库管理测试")
    print("-" * 60)
    
    # 1.1 获取知识库列表
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/datasets",
            headers=headers,
            params={"page": 1, "page_size": 20}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                datasets = result.get('data', [])
                print(f"✅ 获取知识库列表: 找到 {len(datasets)} 个知识库")
                results.append(("获取知识库列表", True, f"{len(datasets)}个"))
                
                # 找到目标知识库
                target_kb = None
                for kb in datasets:
                    if kb['id'] == EXISTING_KB_ID:
                        target_kb = kb
                        break
                
                if target_kb:
                    print(f"   目标知识库: {target_kb['name']}")
                    print(f"   文档数量: {target_kb.get('document_count', 0)}")
                    print(f"   向量数量: {target_kb.get('chunk_count', 0)}")
                else:
                    print(f"❌ 未找到目标知识库 {EXISTING_KB_ID}")
                    return
            else:
                print(f"❌ API错误: {result.get('message', 'Unknown')}")
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return
    
    # 1.2 创建新知识库（测试创建功能）
    try:
        kb_name = f"API测试_{datetime.now().strftime('%m%d_%H%M%S')}"
        data = {
            "name": kb_name,
            "description": "API全链路测试知识库",
            "embedding_model": "BAAI/bge-m3@SILICONFLOW",
            "chunk_method": "naive"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/datasets",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                new_kb_id = result['data']['id']
                print(f"✅ 创建知识库: ID {new_kb_id}")
                results.append(("创建知识库", True, f"ID: {new_kb_id}"))
                
                # 删除测试知识库（清理）
                delete_response = requests.delete(
                    f"{BASE_URL}/api/v1/datasets/{new_kb_id}",
                    headers=headers
                )
                if delete_response.status_code == 200:
                    print(f"✅ 清理测试知识库: 已删除")
                
            else:
                print(f"❌ 创建知识库失败: {result.get('message', 'Unknown')}")
                results.append(("创建知识库", False, result.get('message', 'Unknown')))
        else:
            print(f"❌ 创建知识库HTTP错误: {response.status_code}")
            results.append(("创建知识库", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ 创建知识库异常: {str(e)}")
        results.append(("创建知识库", False, str(e)))
    
    # ==================== 步骤2: 文件管理测试 ====================
    print(f"\n🔷 步骤2: 文件管理测试")
    print("-" * 60)
    
    # 2.1 获取文档列表
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/datasets/{EXISTING_KB_ID}/documents",
            headers=headers,
            params={"page": 1, "page_size": 20}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                docs_data = result.get('data')
                if isinstance(docs_data, dict) and 'docs' in docs_data:
                    docs = docs_data['docs']
                    total = docs_data.get('total', len(docs))
                elif isinstance(docs_data, list):
                    docs = docs_data
                    total = len(docs)
                else:
                    docs = []
                    total = 0
                
                print(f"✅ 获取文档列表: 找到 {len(docs)} 个文档 (总计 {total})")
                results.append(("获取文档列表", True, f"{len(docs)}个"))
                
                # 显示文档信息
                for doc in docs[:3]:
                    status = doc.get('run', 'UNKNOWN')
                    size = doc.get('size', 0)
                    print(f"   - {doc.get('name', 'Unknown')}: {status}, {size}字节")
            else:
                print(f"❌ API错误: {result.get('message', 'Unknown')}")
                results.append(("获取文档列表", False, result.get('message', 'Unknown')))
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            results.append(("获取文档列表", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        results.append(("获取文档列表", False, str(e)))
    
    # ==================== 步骤3: 知识库检索测试 ====================
    print(f"\n🔷 步骤3: 知识库检索测试")
    print("-" * 60)
    
    test_questions = [
        "什么是权益申请？",
        "借款申请的流程是什么？",
        "如何进行费用核算？",
        "贷款业务有哪些要求？"
    ]
    
    retrieval_success = 0
    for i, question in enumerate(test_questions, 1):
        try:
            data = {
                "question": question,
                "dataset_ids": [EXISTING_KB_ID],
                "page": 1,
                "page_size": 3
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/retrieval",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    chunks = result.get('data', {}).get('chunks', [])
                    print(f"✅ 检索问题 {i}: {question}")
                    print(f"   返回 {len(chunks)} 个相关片段")
                    
                    if chunks:
                        best_chunk = chunks[0]
                        score = best_chunk.get('similarity', 0)
                        content = best_chunk.get('content_ltks', '')[:100]
                        print(f"   最佳匹配 (相似度 {score:.3f}): {content}...")
                        retrieval_success += 1
                    
                    results.append((f"检索问题{i}", True, f"{len(chunks)}个结果"))
                else:
                    print(f"❌ API错误: {result.get('message', 'Unknown')}")
                    results.append((f"检索问题{i}", False, result.get('message', 'Unknown')))
            else:
                print(f"❌ HTTP错误: {response.status_code}")
                results.append((f"检索问题{i}", False, f"HTTP {response.status_code}"))
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            results.append((f"检索问题{i}", False, str(e)))
    
    print(f"✅ 检索测试汇总: {retrieval_success}/{len(test_questions)} 个问题有结果")
    
    # ==================== 步骤4: 对话管理测试 ====================
    print(f"\n🔷 步骤4: 对话管理测试")
    print("-" * 60)
    
    chat_id = None
    session_id = None
    
    # 4.1 创建对话
    try:
        data = {
            "name": f"全链路测试对话_{datetime.now().strftime('%H%M%S')}",
            "dataset_ids": [EXISTING_KB_ID],
            "description": "用于API全链路测试的对话会话"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chats",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                chat_id = result['data']['id']
                model_name = result['data'].get('llm', {}).get('model_name', 'Unknown')
                print(f"✅ 创建对话: ID {chat_id}")
                print(f"   模型: {model_name}")
                results.append(("创建对话", True, f"ID: {chat_id}"))
            else:
                print(f"❌ API错误: {result.get('message', 'Unknown')}")
                results.append(("创建对话", False, result.get('message', 'Unknown')))
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            results.append(("创建对话", False, f"HTTP {response.status_code}"))
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        results.append(("创建对话", False, str(e)))
    
    # ==================== 步骤5: 智能问答测试 ====================
    print(f"\n🔷 步骤5: 智能问答测试")
    print("-" * 60)
    
    if chat_id:
        qa_questions = [
            "你好，请介绍一下你的功能",
            "什么是权益申请业务？",
            "借款申请的流程和要求是什么？",
            "请解释一下费用核算的概念"
        ]
        
        qa_success = 0
        for i, question in enumerate(qa_questions, 1):
            try:
                data = {"content": question}
                
                response = requests.post(
                    f"{BASE_URL}/api/v1/chats/{chat_id}/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    # 解析SSE响应
                    sse_results = parse_sse_response(response.text)
                    
                    if sse_results:
                        # 寻找包含答案的响应
                        answer_found = False
                        for sse_result in sse_results:
                            if (sse_result.get('code') == 0 and 
                                isinstance(sse_result.get('data'), dict) and 
                                'answer' in sse_result.get('data', {})):
                                
                                answer = sse_result['data']['answer']
                                reference = sse_result['data'].get('reference', {})
                                if not session_id:
                                    session_id = sse_result['data'].get('session_id')
                                
                                print(f"✅ 问答 {i}: {question}")
                                print(f"   回答长度: {len(answer)} 字符")
                                
                                # 显示回答预览
                                answer_preview = answer[:150] + "..." if len(answer) > 150 else answer
                                print(f"   回答: {answer_preview}")
                                
                                # 显示引用信息
                                if reference and 'chunks' in reference:
                                    chunk_count = len(reference['chunks'])
                                    print(f"   引用片段: {chunk_count} 个")
                                
                                results.append((f"问答{i}", True, f"{len(answer)}字符"))
                                answer_found = True
                                qa_success += 1
                                break
                        
                        if not answer_found:
                            print(f"❌ 问答 {i}: 未找到答案数据")
                            results.append((f"问答{i}", False, "未找到答案"))
                    else:
                        print(f"❌ 问答 {i}: SSE解析失败")
                        results.append((f"问答{i}", False, "SSE解析失败"))
                else:
                    print(f"❌ 问答 {i}: HTTP错误 {response.status_code}")
                    results.append((f"问答{i}", False, f"HTTP {response.status_code}"))
                
                # 间隔，避免请求过快
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 问答 {i}: 异常 {str(e)}")
                results.append((f"问答{i}", False, str(e)))
        
        print(f"✅ 问答测试汇总: {qa_success}/{len(qa_questions)} 个问题成功")
    else:
        print(f"❌ 跳过问答测试: 没有有效的对话ID")
    
    # ==================== 测试总结 ====================
    print(f"\n{'='*80}")
    print(f"🎯 全链路测试总结")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r[1])
    
    print(f"\n📊 测试概览:")
    print(f"   总测试项: {total_tests}")
    print(f"   成功: {successful_tests}")
    print(f"   失败: {total_tests - successful_tests}")
    print(f"   成功率: {(successful_tests/total_tests*100):.1f}%")
    
    print(f"\n🔧 创建的资源:")
    if chat_id:
        print(f"   对话ID: {chat_id}")
    if session_id:
        print(f"   会话ID: {session_id}")
    
    print(f"\n📋 详细结果:")
    
    categories = {
        "知识库管理": ["获取知识库列表", "创建知识库"],
        "文件管理": ["获取文档列表"],
        "知识检索": [f"检索问题{i}" for i in range(1, 5)],
        "对话管理": ["创建对话"],
        "智能问答": [f"问答{i}" for i in range(1, 5)]
    }
    
    for category, test_names in categories.items():
        print(f"\n   {category}:")
        for test_name, status, message in results:
            if test_name in test_names:
                status_icon = "✅" if status else "❌"
                print(f"     {status_icon} {test_name}: {message}")
    
    # 显示总体评价
    if successful_tests >= total_tests * 0.9:
        print(f"\n🎉 优秀！API全链路测试几乎完全通过")
    elif successful_tests >= total_tests * 0.7:
        print(f"\n👍 良好！API全链路测试大部分通过")
    elif successful_tests >= total_tests * 0.5:
        print(f"\n⚠️  一般，API全链路测试部分通过，需要检查失败项")
    else:
        print(f"\n❌ 需要改进，API全链路测试失败项较多")
    
    print(f"\n测试完成时间: {datetime.now()}")
    print(f"{'='*80}")


if __name__ == "__main__":
    run_complete_test()