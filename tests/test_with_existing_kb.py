"""
使用现有知识库测试完整的问答流程
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

# 使用现有的已解析知识库
EXISTING_KB_ID = "7e8d9e924cde11f0afc90242ac140006"  # 360test00000

def test_with_existing_kb():
    """使用现有知识库测试完整流程"""
    print(f"\n{'='*80}")
    print(f"使用现有知识库测试完整问答流程")
    print(f"知识库ID: {EXISTING_KB_ID}")
    print(f"测试时间: {datetime.now()}")
    print(f"{'='*80}")
    
    results = []
    
    # 1. 检查知识库状态
    print(f"\n1. 检查知识库状态...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/datasets",
            headers=headers,
            params={"page": 1, "page_size": 50}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                datasets = result.get('data', [])
                target_kb = None
                for kb in datasets:
                    if kb['id'] == EXISTING_KB_ID:
                        target_kb = kb
                        break
                
                if target_kb:
                    print(f"✅ 找到知识库: {target_kb['name']}")
                    print(f"   文档数量: {target_kb.get('document_count', 0)}")
                    print(f"   向量数量: {target_kb.get('chunk_count', 0)}")
                    print(f"   状态: {target_kb.get('status', 'unknown')}")
                    results.append(("检查知识库", True, f"文档数: {target_kb.get('document_count', 0)}"))
                else:
                    print(f"❌ 未找到知识库 {EXISTING_KB_ID}")
                    results.append(("检查知识库", False, "知识库不存在"))
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
    
    # 2. 测试检索
    print(f"\n2. 测试知识库检索...")
    test_questions = [
        "什么是人工智能？",
        "请介绍一下机器学习",
        "深度学习的概念",
        "神经网络是什么？",
        "AI的应用场景有哪些？"
    ]
    
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
                    print(f"   问题 {i}: {question}")
                    print(f"   ✅ 返回 {len(chunks)} 个相关片段")
                    
                    # 显示最佳匹配
                    if chunks:
                        best_chunk = chunks[0]
                        score = best_chunk.get('similarity', 0)
                        content = best_chunk.get('content_ltks', '')[:100]
                        print(f"   最佳匹配 (相似度 {score:.3f}): {content}...")
                    
                    results.append((f"检索问题{i}", True, f"{len(chunks)}个结果"))
                else:
                    print(f"   ❌ API错误: {result.get('message', 'Unknown')}")
                    results.append((f"检索问题{i}", False, result.get('message', 'Unknown')))
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                results.append((f"检索问题{i}", False, f"HTTP {response.status_code}"))
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append((f"检索问题{i}", False, str(e)))
    
    # 3. 创建对话
    print(f"\n3. 创建对话会话...")
    chat_id = None
    try:
        data = {
            "name": f"测试对话_{datetime.now().strftime('%H%M%S')}",
            "dataset_ids": [EXISTING_KB_ID]
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
                print(f"✅ 创建对话成功")
                print(f"   对话ID: {chat_id}")
                print(f"   模型: {model_name}")
                results.append(("创建对话", True, f"ID: {chat_id}"))
            else:
                print(f"❌ API错误: {result.get('message', 'Unknown')}")
                results.append(("创建对话", False, result.get('message', 'Unknown')))
                return
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            results.append(("创建对话", False, f"HTTP {response.status_code}"))
            return
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        results.append(("创建对话", False, str(e)))
        return
    
    # 4. 测试智能问答
    print(f"\n4. 测试智能问答...")
    qa_questions = [
        "你好，请介绍一下你的功能",
        "什么是人工智能？请详细解释",
        "机器学习和深度学习有什么区别？",
        "AI在现实生活中有哪些应用？"
    ]
    
    for i, question in enumerate(qa_questions, 1):
        try:
            data = {
                "content": question
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/chats/{chat_id}/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                response_text = response.text
                
                if response_text.startswith('data:'):
                    try:
                        json_part = response_text[5:]
                        result = json.loads(json_part)
                        
                        if result.get('code') == 0:
                            answer = result.get('data', {}).get('answer', '')
                            reference = result.get('data', {}).get('reference', {})
                            
                            print(f"   问题 {i}: {question}")
                            print(f"   ✅ 回答长度: {len(answer)} 字符")
                            
                            # 显示回答预览
                            answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                            print(f"   回答预览: {answer_preview}")
                            
                            # 显示引用信息
                            if reference and 'chunks' in reference:
                                chunk_count = len(reference['chunks'])
                                print(f"   引用片段: {chunk_count} 个")
                            
                            results.append((f"问答{i}", True, f"{len(answer)}字符回答"))
                        else:
                            print(f"   ❌ API错误: {result.get('message', 'Unknown')}")
                            results.append((f"问答{i}", False, result.get('message', 'Unknown')))
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON解析错误: {str(e)}")
                        results.append((f"问答{i}", False, f"JSON解析错误"))
                else:
                    print(f"   ❌ 意外的响应格式: {response_text[:100]}")
                    results.append((f"问答{i}", False, "响应格式错误"))
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                results.append((f"问答{i}", False, f"HTTP {response.status_code}"))
                
            # 间隔，避免请求过快
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            results.append((f"问答{i}", False, str(e)))
    
    # 5. 测试摘要
    print(f"\n{'='*80}")
    print(f"测试摘要")
    print(f"{'='*80}")
    
    total = len(results)
    success = sum(1 for r in results if r[1])
    print(f"总测试项: {total}")
    print(f"成功: {success}")
    print(f"失败: {total - success}")
    print(f"成功率: {(success/total*100):.1f}%")
    
    print(f"\n详细结果:")
    for test_name, status, message in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {test_name}: {message}")
    
    if chat_id:
        print(f"\n创建的资源:")
        print(f"- 对话ID: {chat_id}")


if __name__ == "__main__":
    test_with_existing_kb()