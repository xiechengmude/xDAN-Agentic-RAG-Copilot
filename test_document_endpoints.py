#!/usr/bin/env python3
"""
测试新增的三个文档管理接口
"""

import requests
import json

# 配置
API_BASE_URL = "http://localhost:8050"
API_KEY = "xDAN-RAG-Service-Demo-Key"

def test_document_endpoints():
    """测试新增的文档管理接口"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("🧪 测试新增的文档管理接口")
    print("=" * 50)
    
    # 1. 测试批量删除文档
    print("\n1. 测试批量删除文档")
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/v1/datasets/test_dataset/documents",
            headers=headers,
            json={"ids": ["test_doc1", "test_doc2"]}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            print("✅ 批量删除文档接口可用")
        else:
            print(f"⚠️ 服务器响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 2. 测试获取文档内容
    print("\n2. 测试获取文档内容")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/datasets/test_dataset/documents/test_doc",
            headers={k: v for k, v in headers.items() if k != "Content-Type"}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"内容类型: {response.headers.get('content-type')}")
            content = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"文档内容预览: {content}")
            print("✅ 获取文档内容接口可用")
        else:
            print(f"⚠️ 服务器响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 3. 测试下载文档
    print("\n3. 测试下载文档")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/datasets/test_dataset/documents/test_doc/download",
            headers={k: v for k, v in headers.items() if k != "Content-Type"}
        )
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"内容类型: {response.headers.get('content-type')}")
            print(f"内容长度: {len(response.content)} bytes")
            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                print(f"下载文件名: {content_disposition}")
            print("✅ 下载文档接口可用")
        else:
            print(f"⚠️ 服务器响应: {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 4. 检查OpenAPI文档中的接口
    print("\n4. 检查OpenAPI文档")
    try:
        response = requests.get(f"{API_BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get("paths", {})
            
            # 检查三个新接口
            document_endpoints = []
            for path in paths.keys():
                if "documents" in path:
                    methods = list(paths[path].keys())
                    document_endpoints.append(f"{path}: {methods}")
            
            print("文档相关接口:")
            for endpoint in document_endpoints:
                print(f"  - {endpoint}")
            
            # 检查是否包含我们新增的接口
            required_endpoints = [
                "/api/v1/datasets/{dataset_id}/documents/{document_id}",
                "/api/v1/datasets/{dataset_id}/documents/{document_id}/download",
                "/api/v1/datasets/{dataset_id}/documents"
            ]
            
            missing_endpoints = []
            for required in required_endpoints:
                if required not in paths:
                    missing_endpoints.append(required)
            
            if not missing_endpoints:
                print("✅ 所有新增接口都在OpenAPI文档中")
            else:
                print(f"⚠️ 缺失的接口: {missing_endpoints}")
                
        else:
            print(f"❌ 无法获取OpenAPI文档: {response.status_code}")
    except Exception as e:
        print(f"❌ 检查OpenAPI文档失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 文档接口测试完成")

if __name__ == "__main__":
    test_document_endpoints()