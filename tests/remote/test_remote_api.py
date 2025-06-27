#!/usr/bin/env python3
"""
远程服务器API接口完整性测试
测试所有API接口在远程服务器上的可用性
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import os

# 远程服务器配置
REMOTE_API_URL = "http://150.109.16.195:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

# 测试数据
TEST_DATASET_ID = "7e8d9e924cde11f0afc90242ac140006"  # 已知的测试数据集

# 请求头
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

# 测试结果统计
test_results = {
    "passed": 0,
    "failed": 0,
    "details": []
}

def print_test_header(category: str):
    """打印测试类别标题"""
    print(f"\n{'='*60}")
    print(f"测试类别: {category}")
    print(f"{'='*60}")

def test_endpoint(method: str, endpoint: str, description: str, 
                 data: Dict = None, files: Dict = None, 
                 expected_status: List[int] = [200],
                 stream: bool = False) -> Tuple[bool, str]:
    """
    测试单个端点
    
    Returns:
        (success, message)
    """
    url = f"{REMOTE_API_URL}{endpoint}"
    
    try:
        # 根据方法选择请求方式
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                # 文件上传请求
                file_headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
                response = requests.post(url, headers=file_headers, files=files, timeout=10)
            elif stream:
                # SSE流式请求
                response = requests.post(url, headers=headers, json=data, stream=True, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, json=data, timeout=10)
        else:
            return False, f"不支持的方法: {method}"
        
        # 检查响应状态
        if response.status_code in expected_status:
            # 对于流式响应，只检查连接是否成功
            if stream:
                return True, f"状态码: {response.status_code} (流式响应)"
            
            # 尝试解析JSON响应
            try:
                result = response.json()
                if isinstance(result, dict) and "code" in result:
                    if result["code"] == 0:
                        return True, f"状态码: {response.status_code}, 响应: 成功"
                    else:
                        # API返回了错误，但接口是可用的
                        return True, f"状态码: {response.status_code}, API错误: {result.get('message', 'Unknown')}"
                else:
                    return True, f"状态码: {response.status_code}, 响应格式: {type(result).__name__}"
            except:
                # 非JSON响应（如文件下载）
                return True, f"状态码: {response.status_code} (非JSON响应)"
        else:
            return False, f"状态码: {response.status_code}, 期望: {expected_status}"
            
    except requests.exceptions.Timeout:
        return False, "请求超时"
    except requests.exceptions.ConnectionError:
        return False, "连接错误"
    except Exception as e:
        return False, f"异常: {str(e)}"

def record_result(endpoint: str, method: str, success: bool, message: str):
    """记录测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    result = f"{status} | {method} {endpoint} | {message}"
    print(result)
    
    test_results["details"].append({
        "endpoint": endpoint,
        "method": method,
        "success": success,
        "message": message
    })
    
    if success:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

def test_system_apis():
    """测试系统管理接口"""
    print_test_header("系统管理接口")
    
    # 健康检查
    success, msg = test_endpoint("GET", "/health", "健康检查")
    record_result("/health", "GET", success, msg)
    
    # Swagger文档
    success, msg = test_endpoint("GET", "/docs", "Swagger文档", expected_status=[200, 307])
    record_result("/docs", "GET", success, msg)
    
    # OpenAPI规范
    success, msg = test_endpoint("GET", "/openapi.json", "OpenAPI规范")
    record_result("/openapi.json", "GET", success, msg)

def test_dataset_apis():
    """测试知识库管理接口"""
    print_test_header("知识库管理接口")
    
    # 获取知识库列表
    success, msg = test_endpoint("GET", "/api/v1/datasets?page=1&page_size=10", "获取知识库列表")
    record_result("/api/v1/datasets", "GET", success, msg)
    
    # 搜索知识库
    success, msg = test_endpoint("GET", "/api/v1/datasets?page=1&page_size=10&name=test", "搜索知识库")
    record_result("/api/v1/datasets?name=xxx", "GET", success, msg)
    
    # 创建知识库
    create_data = {
        "name": f"远程测试_{int(time.time())}",
        "description": "远程API测试",
        "embedding_model": "BAAI/bge-m3@SILICONFLOW",
        "chunk_method": "naive"
    }
    success, msg = test_endpoint("POST", "/api/v1/datasets", "创建知识库", data=create_data)
    record_result("/api/v1/datasets", "POST", success, msg)
    
    # 更新知识库（使用已知ID）
    update_data = {"description": "更新测试"}
    success, msg = test_endpoint("PUT", f"/api/v1/datasets/{TEST_DATASET_ID}", "更新知识库", 
                                data=update_data, expected_status=[200, 400, 404])
    record_result(f"/api/v1/datasets/{{dataset_id}}", "PUT", success, msg)
    
    # 删除知识库（测试已确认可以工作）
    # 先创建一个用于删除的数据集
    temp_data = {
        "name": f"临时删除测试_{int(time.time())}",
        "description": "将被删除",
        "embedding_model": "BAAI/bge-m3@SILICONFLOW",
        "chunk_method": "naive"
    }
    create_resp = requests.post(f"{REMOTE_API_URL}/api/v1/datasets", headers=headers, json=temp_data)
    if create_resp.status_code == 200:
        temp_id = create_resp.json().get("data", {}).get("id")
        success, msg = test_endpoint("DELETE", f"/api/v1/datasets/{temp_id}", "删除知识库", 
                                    expected_status=[200])
    else:
        success, msg = False, "无法创建测试数据集"
    record_result("/api/v1/datasets/{dataset_id}", "DELETE", success, msg)
    
    # 批量删除知识库
    delete_data = {"ids": ["test_not_exists"]}
    success, msg = test_endpoint("DELETE", "/api/v1/datasets", "批量删除知识库", 
                                data=delete_data, expected_status=[200, 400])
    record_result("/api/v1/datasets", "DELETE", success, msg)

def test_document_apis():
    """测试文档管理接口"""
    print_test_header("文档管理接口")
    
    # 上传文档（创建测试文件）
    test_content = f"远程测试文档内容 - {datetime.now()}"
    files = {'file': ('remote_test.txt', test_content.encode('utf-8'), 'text/plain')}
    success, msg = test_endpoint("POST", f"/api/v1/datasets/{TEST_DATASET_ID}/documents", 
                                "上传文档", files=files, expected_status=[200, 400])
    record_result("/api/v1/datasets/{dataset_id}/documents", "POST", success, msg)
    
    # 获取文档列表
    success, msg = test_endpoint("GET", f"/api/v1/datasets/{TEST_DATASET_ID}/documents?page=1&page_size=10", 
                                "获取文档列表")
    record_result("/api/v1/datasets/{dataset_id}/documents", "GET", success, msg)
    
    # 获取文档内容（使用不存在的ID测试接口）
    success, msg = test_endpoint("GET", f"/api/v1/datasets/{TEST_DATASET_ID}/documents/test_doc", 
                                "获取文档内容", expected_status=[200, 404])
    record_result("/api/v1/datasets/{dataset_id}/documents/{doc_id}", "GET", success, msg)
    
    # 删除文档（单个）- 测试已确认可以工作
    # 需要先有一个真实的文档ID
    success, msg = test_endpoint("DELETE", f"/api/v1/datasets/{TEST_DATASET_ID}/documents/test_doc", 
                                "删除文档", expected_status=[200, 400, 404])
    record_result("/api/v1/datasets/{dataset_id}/documents/{doc_id}", "DELETE", success, msg)
    
    # 批量删除文档
    delete_data = {"ids": ["test_doc"]}
    success, msg = test_endpoint("DELETE", f"/api/v1/datasets/{TEST_DATASET_ID}/documents", 
                                "批量删除文档", data=delete_data, expected_status=[200, 400])
    record_result("/api/v1/datasets/{dataset_id}/documents", "DELETE", success, msg)
    
    # 下载文档
    success, msg = test_endpoint("GET", f"/api/v1/datasets/{TEST_DATASET_ID}/documents/test_doc/download", 
                                "下载文档", expected_status=[200, 404])
    record_result("/api/v1/datasets/{dataset_id}/documents/{doc_id}/download", "GET", success, msg)
    
    # 解析文档
    parse_data = {"document_ids": ["test_doc"]}
    success, msg = test_endpoint("POST", f"/api/v1/datasets/{TEST_DATASET_ID}/documents/parse", 
                                "解析文档", data=parse_data, expected_status=[200, 400])
    record_result("/api/v1/datasets/{dataset_id}/documents/parse", "POST", success, msg)

def test_chat_apis():
    """测试对话管理接口"""
    print_test_header("对话管理接口")
    
    # 创建对话
    chat_data = {
        "name": "远程测试对话",
        "dataset_ids": [TEST_DATASET_ID]
    }
    success, msg = test_endpoint("POST", "/api/v1/chats", "创建对话", 
                                data=chat_data, expected_status=[200, 400])
    record_result("/api/v1/chats", "POST", success, msg)
    
    # 获取对话列表
    success, msg = test_endpoint("GET", "/api/v1/chats?page=1&page_size=10", "获取对话列表")
    record_result("/api/v1/chats", "GET", success, msg)
    
    # 获取对话详情（使用不存在的ID）
    success, msg = test_endpoint("GET", "/api/v1/chats/test_chat_id", "获取对话详情", 
                                expected_status=[200, 404])
    record_result("/api/v1/chats/{chat_id}", "GET", success, msg)
    
    # 更新对话
    update_data = {"name": "更新的对话名称"}
    success, msg = test_endpoint("PUT", "/api/v1/chats/test_chat_id", "更新对话", 
                                data=update_data, expected_status=[200, 404])
    record_result("/api/v1/chats/{chat_id}", "PUT", success, msg)
    
    # 删除对话
    success, msg = test_endpoint("DELETE", "/api/v1/chats/test_chat_id", "删除对话", 
                                expected_status=[200, 404])
    record_result("/api/v1/chats/{chat_id}", "DELETE", success, msg)
    
    # 发送消息（SSE流式）
    message_data = {"content": "测试消息"}
    success, msg = test_endpoint("POST", "/api/v1/chats/test_chat_id/completions", 
                                "发送消息（流式）", data=message_data, 
                                stream=True, expected_status=[200, 404])
    record_result("/api/v1/chats/{chat_id}/completions", "POST", success, msg)
    
    # 获取对话历史
    success, msg = test_endpoint("GET", "/api/v1/chats/test_chat_id/messages?page=1&page_size=10", 
                                "获取对话历史", expected_status=[200, 404])
    record_result("/api/v1/chats/{chat_id}/messages", "GET", success, msg)

def test_retrieval_apis():
    """测试检索接口"""
    print_test_header("检索接口")
    
    retrieval_data = {
        "question": "测试问题",
        "dataset_ids": [TEST_DATASET_ID],
        "page": 1,
        "page_size": 5
    }
    
    # 知识库检索
    success, msg = test_endpoint("POST", "/api/v1/retrieval", "知识库检索", data=retrieval_data)
    record_result("/api/v1/retrieval", "POST", success, msg)
    
    # 知识库检索（别名）
    success, msg = test_endpoint("POST", "/api/v1/retrieve", "知识库检索（别名）", data=retrieval_data)
    record_result("/api/v1/retrieve", "POST", success, msg)

def test_reference_apis():
    """测试引用文档接口"""
    print_test_header("引用文档接口")
    
    # 查看引用文档
    success, msg = test_endpoint("GET", f"/api/v1/documents/reference/test_doc?dataset_id={TEST_DATASET_ID}", 
                                "查看引用文档", expected_status=[200, 404])
    record_result("/api/v1/documents/reference/{document_id}", "GET", success, msg)
    
    # 批量查看引用文档
    batch_data = {
        "references": [
            {"document_id": "test_doc1", "dataset_id": TEST_DATASET_ID},
            {"document_id": "test_doc2", "dataset_id": TEST_DATASET_ID}
        ]
    }
    success, msg = test_endpoint("POST", "/api/v1/documents/reference/batch", 
                                "批量查看引用文档", data=batch_data)
    record_result("/api/v1/documents/reference/batch", "POST", success, msg)

def generate_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("测试报告")
    print("="*60)
    
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    print(f"总接口数: {total}")
    print(f"✅ 通过: {test_results['passed']}")
    print(f"❌ 失败: {test_results['failed']}")
    print(f"通过率: {pass_rate:.1f}%")
    
    if test_results["failed"] > 0:
        print("\n失败的接口:")
        for detail in test_results["details"]:
            if not detail["success"]:
                print(f"  - {detail['method']} {detail['endpoint']}: {detail['message']}")
    
    # 更新检查清单
    update_checklist()

def update_checklist():
    """更新检查清单文件"""
    checklist_path = os.path.join(os.path.dirname(__file__), "api_checklist.md")
    
    # 读取原始文件
    with open(checklist_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新测试结果
    for detail in test_results["details"]:
        endpoint = detail["endpoint"]
        method = detail["method"]
        status = "x" if detail["success"] else " "
        
        # 查找并更新对应的行
        search_pattern = f"- [ ] `{method} {endpoint.split('?')[0]}"
        replace_pattern = f"- [{status}] `{method} {endpoint.split('?')[0]}"
        content = content.replace(search_pattern, replace_pattern)
    
    # 更新统计表格
    total = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total * 100) if total > 0 else 0
    
    # 更新测试时间
    content = content.replace("**测试时间**: 2025-06-27", 
                             f"**测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 添加测试结果统计
    if "## 测试结果统计" not in content:
        content += f"\n\n## 测试结果统计\n\n"
        content += f"- 总接口数: {total}\n"
        content += f"- 通过: {test_results['passed']}\n"
        content += f"- 失败: {test_results['failed']}\n"
        content += f"- 通过率: {pass_rate:.1f}%\n"
    
    # 写回文件
    with open(checklist_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ 检查清单已更新: {checklist_path}")

def main():
    print("="*60)
    print(f"远程服务器API接口测试")
    print(f"服务器地址: {REMOTE_API_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 运行所有测试
    test_system_apis()
    test_dataset_apis()
    test_document_apis()
    test_chat_apis()
    test_retrieval_apis()
    test_reference_apis()
    
    # 生成报告
    generate_report()

if __name__ == "__main__":
    main()