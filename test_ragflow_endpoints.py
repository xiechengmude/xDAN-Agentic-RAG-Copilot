#!/usr/bin/env python3
"""
RAGFlow API 端点完整测试脚本
测试所有与RAGFlow相关的接口
"""

import requests
import json
import time
import sys
from datetime import datetime

# API配置
API_BASE_URL = "http://localhost:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

# 测试数据
test_dataset_name = f"测试数据集_{int(time.time())}"
test_dataset_id = None
test_document_id = None

def print_test_header(test_name):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")

def print_result(success, message, details=None):
    """打印测试结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"{status}: {message}")
    if details:
        print(f"详情: {json.dumps(details, ensure_ascii=False, indent=2)}")

def test_list_datasets():
    """测试1: 获取数据集列表"""
    print_test_header("1. 获取数据集列表")
    
    try:
        # 测试基本列表
        response = requests.get(
            f"{API_BASE_URL}/api/v1/datasets?page=1&page_size=10",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                datasets = result.get("data", [])
                print_result(True, f"获取到 {len(datasets)} 个数据集")
                
                # 显示前3个数据集
                for i, ds in enumerate(datasets[:3]):
                    print(f"  [{i+1}] {ds.get('name')} (ID: {ds.get('id')})")
                
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_list_datasets_with_search():
    """测试2: 搜索数据集"""
    print_test_header("2. 搜索数据集（name参数）")
    
    try:
        # 测试搜索功能
        search_term = "测试"
        response = requests.get(
            f"{API_BASE_URL}/api/v1/datasets?page=1&page_size=10&name={search_term}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                datasets = result.get("data", [])
                print_result(True, f"搜索 '{search_term}' 返回 {len(datasets)} 个结果")
                
                # 验证搜索结果
                for ds in datasets[:3]:
                    if search_term in ds.get('name', ''):
                        print(f"  ✓ {ds.get('name')} 包含搜索词")
                
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_create_dataset():
    """测试3: 创建数据集"""
    global test_dataset_id
    print_test_header("3. 创建数据集")
    
    try:
        create_data = {
            "name": test_dataset_name,
            "description": "API测试创建的数据集",
            "chunk_method": "naive",
            "embedding_model": "BAAI/bge-m3@SILICONFLOW",
            "parser_config": {
                "chunk_token_num": 256,
                "delimiter": "\\n"
            }
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/datasets",
            headers=headers,
            json=create_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                dataset = result.get("data", {})
                test_dataset_id = dataset.get("id")
                print_result(True, f"数据集创建成功", {
                    "id": test_dataset_id,
                    "name": dataset.get("name")
                })
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_update_dataset():
    """测试4: 更新数据集"""
    print_test_header("4. 更新数据集")
    
    if not test_dataset_id:
        print_result(False, "没有可用的测试数据集ID")
        return False
    
    try:
        update_data = {
            "description": "更新后的描述 - " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        response = requests.put(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_result(True, "数据集更新成功")
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_upload_document():
    """测试5: 上传文档"""
    global test_document_id
    print_test_header("5. 上传文档到数据集")
    
    if not test_dataset_id:
        print_result(False, "没有可用的测试数据集ID")
        return False
    
    try:
        # 创建测试文件内容
        test_content = f"""这是一个测试文档
创建时间: {datetime.now()}
用于测试RAGFlow API的文档上传功能

测试内容包括:
1. 文档上传
2. 文档解析
3. 文档检索

这是第二段内容，用于测试分块功能。
RAGFlow是一个强大的知识库管理系统。
"""
        
        # 使用multipart上传
        files = {
            'file': ('test_document.txt', test_content.encode('utf-8'), 'text/plain')
        }
        
        # 临时修改headers，去除Content-Type让requests自动设置
        upload_headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}/documents",
            headers=upload_headers,
            files=files
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                documents = result.get("data", [])
                if documents:
                    test_document_id = documents[0].get("id")
                    print_result(True, "文档上传成功", {
                        "document_id": test_document_id,
                        "name": documents[0].get("name")
                    })
                    return True
                else:
                    print_result(False, "上传成功但未返回文档信息")
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_list_documents():
    """测试6: 获取文档列表"""
    print_test_header("6. 获取数据集中的文档列表")
    
    if not test_dataset_id:
        print_result(False, "没有可用的测试数据集ID")
        return False
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}/documents?page=1&page_size=10",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                # RAGFlow返回的data可能是一个包含docs的对象
                data = result.get("data", {})
                if isinstance(data, dict):
                    documents = data.get("docs", [])
                else:
                    documents = data if isinstance(data, list) else []
                    
                print_result(True, f"获取到 {len(documents)} 个文档")
                
                for doc in documents:
                    if isinstance(doc, dict):
                        print(f"  - {doc.get('name')} (ID: {doc.get('id')}, 状态: {doc.get('run')})")
                
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_parse_document():
    """测试7: 解析文档"""
    print_test_header("7. 解析文档")
    
    if not test_dataset_id or not test_document_id:
        print_result(False, "没有可用的测试数据")
        return False
    
    try:
        parse_data = {
            "document_ids": [test_document_id]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}/documents/parse",
            headers=headers,
            json=parse_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_result(True, "文档解析任务已启动")
                
                # 等待解析完成
                print("等待解析完成...")
                time.sleep(3)
                
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_retrieve_chunks():
    """测试8: 检索文档块"""
    print_test_header("8. 检索文档块")
    
    if not test_dataset_id:
        print_result(False, "没有可用的测试数据集ID")
        return False
    
    try:
        retrieve_data = {
            "question": "RAGFlow是什么",
            "dataset_ids": [test_dataset_id]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/retrieve",
            headers=headers,
            json=retrieve_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                chunks = result.get("data", {}).get("chunks", [])
                print_result(True, f"检索到 {len(chunks)} 个相关文档块")
                
                for i, chunk in enumerate(chunks[:3]):
                    print(f"\n  块 {i+1}:")
                    print(f"    内容: {chunk.get('content', '')[:100]}...")
                    print(f"    相似度: {chunk.get('similarity', 0):.3f}")
                
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_delete_documents():
    """测试9: 删除文档"""
    print_test_header("9. 删除文档")
    
    if not test_dataset_id or not test_document_id:
        print_result(False, "没有可用的测试数据")
        return False
    
    try:
        delete_data = {
            "ids": [test_document_id]
        }
        
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}/documents",
            headers=headers,
            json=delete_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_result(True, "文档删除成功")
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def test_delete_dataset():
    """测试10: 删除数据集"""
    print_test_header("10. 删除数据集")
    
    if not test_dataset_id:
        print_result(False, "没有可用的测试数据集ID")
        return False
    
    try:
        # 测试单个删除（使用批量接口）
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/datasets/{test_dataset_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_result(True, "数据集删除成功")
                return True
            else:
                print_result(False, f"API返回错误: {result.get('message')}")
        else:
            print_result(False, f"HTTP错误: {response.status_code}", response.text)
    except Exception as e:
        print_result(False, f"异常: {e}")
    
    return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("RAGFlow API 端点测试")
    print(f"API地址: {API_BASE_URL}")
    print(f"认证令牌: {AUTH_TOKEN[:20]}...")
    print("="*60)
    
    tests = [
        test_list_datasets,
        test_list_datasets_with_search,
        test_create_dataset,
        test_update_dataset,
        test_upload_document,
        test_list_documents,
        test_parse_document,
        test_retrieve_chunks,
        test_delete_documents,
        test_delete_dataset
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"测试执行错误: {e}")
            failed += 1
        
        time.sleep(1)  # 避免请求过快
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  {failed} 个测试失败")

if __name__ == "__main__":
    run_all_tests()