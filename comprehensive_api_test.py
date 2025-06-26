#!/usr/bin/env python3
"""
全面的API接口测试 - 验证所有接口是否按照文档规范工作
使用真实的RAGFlow数据进行测试
"""

import requests
import json
import time

# 配置
API_BASE_URL = "http://localhost:8050"
API_KEY = "xDAN-RAG-Service-Demo-Key"

# RAGFlow真实数据 (从配置文件中获取)
REAL_DATASET_ID = "7e8d9e924cde11f0afc90242ac140006"  # 配置文件中的默认数据集
REAL_RAGFLOW_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

def test_all_endpoints():
    """测试所有API接口"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("🧪 全面API接口测试")
    print("=" * 80)
    
    results = {
        "passed": [],
        "failed": [],
        "total": 0
    }
    
    # 1. 基础接口测试
    print("\n📍 1. 基础接口测试")
    print("-" * 40)
    
    # 健康检查
    test_result = test_endpoint("GET", "/health", None, None, "健康检查", check_unified_format=True)
    record_result(results, test_result)
    
    # 根路径
    test_result = test_endpoint("GET", "/", None, None, "根路径", check_unified_format=True)
    record_result(results, test_result)
    
    # 2. 认证测试
    print("\n📍 2. 认证机制测试")
    print("-" * 40)
    
    # 无认证访问
    test_result = test_auth_failure("/api/v1/datasets", "无认证访问应返回403/401")
    record_result(results, test_result)
    
    # 错误API Key
    test_result = test_auth_failure("/api/v1/datasets", "错误API Key应返回401", {"Authorization": "Bearer wrong-key"})
    record_result(results, test_result)
    
    # 3. 知识库管理接口
    print("\n📍 3. 知识库管理接口")
    print("-" * 40)
    
    # 获取知识库列表
    test_result = test_endpoint("GET", "/api/v1/datasets?page=1&page_size=12", headers, None, "获取知识库列表")
    record_result(results, test_result)
    
    # 创建知识库
    dataset_data = {
        "name": "API测试知识库",
        "description": "自动化测试创建的知识库",
        "embedding_model": "BAAI/bge-m3@SILICONFLOW",
        "chunk_method": "naive",
        "parser_config": {
            "chunk_token_num": 512,
            "delimiter": "\\n"
        }
    }
    test_result = test_endpoint("POST", "/api/v1/datasets", headers, dataset_data, "创建知识库")
    record_result(results, test_result)
    
    # 更新知识库（使用真实的dataset_id）
    update_data = {"name": "API测试更新", "description": "通过API测试更新的描述"}
    test_result = test_endpoint("PUT", f"/api/v1/datasets/{REAL_DATASET_ID}", headers, update_data, "更新知识库（真实数据）")
    record_result(results, test_result)
    
    # 注意：不删除真实的知识库，以免影响其他测试
    print("跳过删除真实知识库的测试，以保护数据")
    
    # 4. 文档管理接口
    print("\n📍 4. 文档管理接口")
    print("-" * 40)
    
    # 获取文档列表（使用真实数据集）
    test_result = test_endpoint("GET", f"/api/v1/datasets/{REAL_DATASET_ID}/documents?page=1&page_size=20", headers, None, "获取文档列表（真实数据）")
    record_result(results, test_result)
    
    # 先获取真实的文档ID用于测试
    real_doc_id = None
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/datasets/{REAL_DATASET_ID}/documents?page=1&page_size=1", headers=headers)
        if response.status_code == 200:
            result = response.json()
            docs = result.get("data", {}).get("docs", [])
            if docs:
                real_doc_id = docs[0].get("id")
                print(f"找到真实文档ID: {real_doc_id}")
    except:
        print("无法获取真实文档ID，使用模拟ID测试")
    
    # 使用真实文档ID或模拟ID
    doc_id_for_test = real_doc_id if real_doc_id else "test_doc"
    
    # 获取文档内容
    test_result = test_document_content(f"/api/v1/datasets/{REAL_DATASET_ID}/documents/{doc_id_for_test}", headers, "获取文档内容（真实数据）")
    record_result(results, test_result)
    
    # 下载文档
    test_result = test_document_download(f"/api/v1/datasets/{REAL_DATASET_ID}/documents/{doc_id_for_test}/download", headers, "下载文档（真实数据）")
    record_result(results, test_result)
    
    # 注意：不删除真实文档，以免影响数据
    print("跳过删除真实文档的测试，以保护数据")
    
    # 5. 对话管理接口
    print("\n📍 5. 对话管理接口")
    print("-" * 40)
    
    # 获取对话列表
    test_result = test_endpoint("GET", "/api/v1/chats?page=1&page_size=20", headers, None, "获取对话列表")
    record_result(results, test_result)
    
    # 创建对话（使用真实数据集）
    chat_data = {
        "name": "API测试对话",
        "dataset_ids": [REAL_DATASET_ID],
        "description": "使用真实数据集的自动化测试对话"
    }
    test_result = test_endpoint("POST", "/api/v1/chats", headers, chat_data, "创建对话")
    chat_id = None
    if test_result["success"] and test_result.get("data"):
        chat_id = test_result["data"].get("id")
    record_result(results, test_result)
    
    # 如果成功创建了对话，测试相关接口
    if chat_id:
        # 发送消息
        message_data = {"content": "你好，这是一个测试消息"}
        test_result = test_endpoint("POST", f"/api/v1/chats/{chat_id}/completions", headers, message_data, "发送消息")
        record_result(results, test_result)
        
        # 获取对话历史
        test_result = test_endpoint("GET", f"/api/v1/chats/{chat_id}/messages?page=1&page_size=20", headers, None, "获取对话历史")
        record_result(results, test_result)
        
        # 删除对话
        test_result = test_endpoint("DELETE", f"/api/v1/chats/{chat_id}", headers, None, "删除对话")
        record_result(results, test_result)
    
    # 6. 检索接口
    print("\n📍 6. 检索接口")
    print("-" * 40)
    
    # 知识库检索（使用真实数据集）
    retrieval_data = {
        "question": "什么是权益申请？",
        "dataset_ids": [REAL_DATASET_ID],
        "page": 1,
        "page_size": 5
    }
    test_result = test_endpoint("POST", "/api/v1/retrieval", headers, retrieval_data, "知识库检索")
    record_result(results, test_result)
    
    # 7. OpenAPI文档检查
    print("\n📍 7. OpenAPI文档检查")
    print("-" * 40)
    
    test_result = check_openapi_documentation()
    record_result(results, test_result)
    
    # 输出测试结果总结
    print("\n" + "=" * 80)
    print("📊 测试结果总结")
    print(f"✅ 通过: {len(results['passed'])}")
    print(f"❌ 失败: {len(results['failed'])}")
    print(f"📈 总计: {results['total']}")
    print(f"🎯 成功率: {len(results['passed'])/results['total']*100:.1f}%")
    
    if results['failed']:
        print("\n❌ 失败的接口:")
        for failed in results['failed']:
            print(f"  - {failed}")
    
    print("\n✅ 通过的接口:")
    for passed in results['passed']:
        print(f"  - {passed}")

def test_endpoint(method, path, headers, data, description, check_unified_format=False):
    """测试单个接口"""
    url = f"{API_BASE_URL}{path}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers if headers else {})
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, json=data)
        
        print(f"{method} {path} - {description}")
        print(f"  状态码: {response.status_code}")
        
        # 检查统一响应格式
        if check_unified_format and response.status_code == 200:
            try:
                result = response.json()
                if "code" in result and "message" in result and "data" in result:
                    print(f"  ✅ 统一响应格式正确")
                    return {"success": True, "description": description, "data": result.get("data")}
                else:
                    print(f"  ❌ 响应格式不符合统一标准")
                    return {"success": False, "description": description, "error": "响应格式错误"}
            except:
                print(f"  ❌ 响应不是有效JSON")
                return {"success": False, "description": description, "error": "无效JSON响应"}
        
        # 一般接口检查
        if response.status_code in [200, 201]:
            print(f"  ✅ 接口可用")
            try:
                result = response.json()
                return {"success": True, "description": description, "data": result.get("data")}
            except:
                return {"success": True, "description": description, "data": None}
        else:
            print(f"  ⚠️ 状态码: {response.status_code}")
            return {"success": False, "description": description, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return {"success": False, "description": description, "error": str(e)}

def test_auth_failure(path, description, custom_headers=None):
    """测试认证失败的情况"""
    url = f"{API_BASE_URL}{path}"
    
    try:
        response = requests.get(url, headers=custom_headers or {})
        print(f"GET {path} - {description}")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code in [401, 403]:
            print(f"  ✅ 正确拒绝未授权访问")
            return {"success": True, "description": description}
        else:
            print(f"  ⚠️ 未按预期拒绝访问")
            return {"success": False, "description": description, "error": f"应返回401/403，实际返回{response.status_code}"}
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return {"success": False, "description": description, "error": str(e)}

def test_document_content(path, headers, description):
    """测试文档内容接口"""
    url = f"{API_BASE_URL}{path}"
    
    try:
        # 移除Content-Type header用于GET请求
        get_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        response = requests.get(url, headers=get_headers)
        
        print(f"GET {path} - {description}")
        print(f"  状态码: {response.status_code}")
        print(f"  内容类型: {response.headers.get('content-type', 'unknown')}")
        
        if response.status_code == 200:
            print(f"  ✅ 接口可用，返回文档内容")
            return {"success": True, "description": description}
        else:
            print(f"  ⚠️ 状态码: {response.status_code}")
            return {"success": False, "description": description, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return {"success": False, "description": description, "error": str(e)}

def test_document_download(path, headers, description):
    """测试文档下载接口"""
    url = f"{API_BASE_URL}{path}"
    
    try:
        # 移除Content-Type header用于GET请求
        get_headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        response = requests.get(url, headers=get_headers)
        
        print(f"GET {path} - {description}")
        print(f"  状态码: {response.status_code}")
        print(f"  内容类型: {response.headers.get('content-type', 'unknown')}")
        
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            print(f"  下载文件头: {content_disposition}")
        
        if response.status_code == 200:
            print(f"  ✅ 接口可用，支持文件下载")
            return {"success": True, "description": description}
        else:
            print(f"  ⚠️ 状态码: {response.status_code}")
            return {"success": False, "description": description, "error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return {"success": False, "description": description, "error": str(e)}

def check_openapi_documentation():
    """检查OpenAPI文档是否包含所有接口"""
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json")
        
        print("GET /openapi.json - OpenAPI文档检查")
        print(f"  状态码: {response.status_code}")
        
        if response.status_code != 200:
            return {"success": False, "description": "OpenAPI文档检查", "error": f"HTTP {response.status_code}"}
        
        openapi_spec = response.json()
        paths = openapi_spec.get("paths", {})
        
        # 期望的接口列表
        expected_endpoints = [
            "/health",
            "/",
            "/api/v1/datasets",
            "/api/v1/datasets/{dataset_id}",
            "/api/v1/datasets/{dataset_id}/documents",
            "/api/v1/datasets/{dataset_id}/documents/{document_id}",
            "/api/v1/datasets/{dataset_id}/documents/{document_id}/download",
            "/api/v1/chats",
            "/api/v1/chats/{chat_id}",
            "/api/v1/chats/{chat_id}/completions",
            "/api/v1/chats/{chat_id}/messages",
            "/api/v1/retrieval"
        ]
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in paths:
                missing_endpoints.append(endpoint)
        
        print(f"  接口总数: {len(paths)}")
        print(f"  期望接口数: {len(expected_endpoints)}")
        
        if missing_endpoints:
            print(f"  ❌ 缺失接口: {missing_endpoints}")
            return {"success": False, "description": "OpenAPI文档检查", "error": f"缺失接口: {missing_endpoints}"}
        else:
            print(f"  ✅ 所有期望接口都已定义")
            return {"success": True, "description": "OpenAPI文档检查"}
            
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        return {"success": False, "description": "OpenAPI文档检查", "error": str(e)}

def record_result(results, test_result):
    """记录测试结果"""
    results["total"] += 1
    if test_result["success"]:
        results["passed"].append(test_result["description"])
    else:
        results["failed"].append(test_result["description"])

if __name__ == "__main__":
    test_all_endpoints()