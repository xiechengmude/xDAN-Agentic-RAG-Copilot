#!/usr/bin/env python3
"""
测试远程服务器的删除操作
验证不同的删除方式和错误处理
"""

import requests
import json
import time
from datetime import datetime

# 远程服务器配置
REMOTE_API_URL = "http://150.109.16.195:8050"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

def test_dataset_deletion():
    """测试数据集删除的不同方式"""
    print("\n" + "="*60)
    print("测试数据集删除操作")
    print("="*60)
    
    # 1. 创建测试数据集
    create_data = {
        "name": f"删除测试_{int(time.time())}",
        "description": "用于测试删除操作",
        "embedding_model": "BAAI/bge-m3@SILICONFLOW",
        "chunk_method": "naive"
    }
    
    response = requests.post(
        f"{REMOTE_API_URL}/api/v1/datasets",
        headers=headers,
        json=create_data
    )
    
    if response.status_code != 200:
        print(f"❌ 创建数据集失败: {response.status_code}")
        return
    
    dataset_id = response.json().get("data", {}).get("id")
    print(f"✅ 创建测试数据集: {dataset_id}")
    
    # 2. 测试单个删除（直接调用）
    print("\n测试1: 单个删除 - DELETE /api/v1/datasets/{id}")
    response = requests.delete(
        f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}",
        headers=headers
    )
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")
    
    # 3. 创建另一个数据集用于批量删除测试
    time.sleep(1)
    response = requests.post(
        f"{REMOTE_API_URL}/api/v1/datasets",
        headers=headers,
        json={**create_data, "name": f"批量删除测试_{int(time.time())}"}
    )
    
    if response.status_code == 200:
        dataset_id2 = response.json().get("data", {}).get("id")
        print(f"\n✅ 创建第二个测试数据集: {dataset_id2}")
        
        # 4. 测试批量删除（正确格式）
        print("\n测试2: 批量删除 - DELETE /api/v1/datasets with body")
        response = requests.delete(
            f"{REMOTE_API_URL}/api/v1/datasets",
            headers=headers,
            json={"ids": [dataset_id2]}
        )
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        
        # 5. 测试批量删除（尝试不同的字段名）
        print("\n测试3: 批量删除 - 使用dataset_ids字段")
        response = requests.delete(
            f"{REMOTE_API_URL}/api/v1/datasets",
            headers=headers,
            json={"dataset_ids": [dataset_id2]}
        )
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")

def test_document_deletion():
    """测试文档删除的不同方式"""
    print("\n" + "="*60)
    print("测试文档删除操作")
    print("="*60)
    
    # 使用已知的测试数据集
    dataset_id = "7e8d9e924cde11f0afc90242ac140006"
    
    # 1. 上传测试文档
    test_content = f"删除测试文档 - {datetime.now()}"
    files = {'file': ('delete_test.txt', test_content.encode('utf-8'), 'text/plain')}
    file_headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
    
    response = requests.post(
        f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}/documents",
        headers=file_headers,
        files=files
    )
    
    if response.status_code != 200:
        print(f"❌ 上传文档失败: {response.status_code}")
        return
    
    documents = response.json().get("data", [])
    if not documents:
        print("❌ 未返回文档信息")
        return
        
    doc_id = documents[0].get("id")
    print(f"✅ 上传测试文档: {doc_id}")
    
    # 2. 测试单个文档删除
    print("\n测试1: 单个删除 - DELETE /api/v1/datasets/{dataset_id}/documents/{doc_id}")
    response = requests.delete(
        f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}/documents/{doc_id}",
        headers=headers
    )
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")
    
    # 3. 再上传一个文档用于批量删除测试
    time.sleep(1)
    response = requests.post(
        f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}/documents",
        headers=file_headers,
        files={'file': ('batch_delete_test.txt', test_content.encode('utf-8'), 'text/plain')}
    )
    
    if response.status_code == 200:
        doc_id2 = response.json().get("data", [])[0].get("id")
        print(f"\n✅ 上传第二个测试文档: {doc_id2}")
        
        # 4. 测试批量删除
        print("\n测试2: 批量删除 - DELETE /api/v1/datasets/{dataset_id}/documents with body")
        response = requests.delete(
            f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}/documents",
            headers=headers,
            json={"ids": [doc_id2]}
        )
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")
        
        # 5. 测试批量删除（尝试不同的字段名）
        print("\n测试3: 批量删除 - 使用document_ids字段")
        response = requests.delete(
            f"{REMOTE_API_URL}/api/v1/datasets/{dataset_id}/documents",
            headers=headers,
            json={"document_ids": [doc_id2]}
        )
        print(f"  状态码: {response.status_code}")
        print(f"  响应: {response.text[:200]}")

def test_direct_ragflow_api():
    """直接测试RAGFlow API的删除操作"""
    print("\n" + "="*60)
    print("直接测试RAGFlow API")
    print("="*60)
    
    ragflow_url = "http://150.109.16.195:7080"
    ragflow_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer ragflow-g4ZWE3OTNhNDUxYTExZjA8MTljMDI0Mm"
    }
    
    # 测试RAGFlow的批量删除接口
    print("\n测试RAGFlow批量删除接口:")
    response = requests.delete(
        f"{ragflow_url}/api/v1/datasets",
        headers=ragflow_headers,
        json={"ids": ["test_id"]}
    )
    print(f"  状态码: {response.status_code}")
    print(f"  响应: {response.text[:200]}")

def main():
    print("="*60)
    print("远程服务器删除操作详细测试")
    print(f"服务器: {REMOTE_API_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 运行测试
    test_dataset_deletion()
    test_document_deletion()
    test_direct_ragflow_api()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()