#!/usr/bin/env python3
"""
完整的API测试脚本
测试所有端点的可用性
"""

import requests
import json
import time
from datetime import datetime

# 测试配置
BASE_URL = "http://localhost:8050"
API_KEY = "xdan-demo-key-123456"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api(method, endpoint, data=None, description=""):
    """通用API测试函数"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=HEADERS, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=HEADERS, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        elapsed = round((time.time() - start_time) * 1000, 2)
        
        result = {
            "method": method.upper(),
            "endpoint": endpoint,
            "description": description,
            "status_code": response.status_code,
            "response_time_ms": elapsed,
            "success": 200 <= response.status_code < 300
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
        
        return result
        
    except Exception as e:
        return {
            "method": method.upper(),
            "endpoint": endpoint,
            "description": description,
            "error": str(e),
            "success": False
        }

def main():
    """运行所有API测试"""
    print("🚀 开始API全面测试")
    print("=" * 60)
    
    test_results = []
    
    # 1. 健康检查接口
    print("\n📊 健康检查接口")
    tests = [
        ("GET", "/health", None, "基础健康检查"),
        ("GET", "/health/detailed", None, "详细健康检查")
    ]
    
    for method, endpoint, data, desc in tests:
        result = test_api(method, endpoint, data, desc)
        test_results.append(result)
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {desc}: {result.get('status_code', 'ERROR')} ({result.get('response_time_ms', 0)}ms)")
    
    # 2. 数据集管理接口
    print("\n📁 数据集管理接口")
    tests = [
        ("GET", "/api/v1/datasets", None, "获取数据集列表"),
        ("GET", "/api/v1/datasets?page=1&page_size=5", None, "分页获取数据集"),
        ("POST", "/api/v1/datasets", {
            "name": "API测试数据集_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "description": "用于API测试的数据集"
        }, "创建数据集"),
    ]
    
    for method, endpoint, data, desc in tests:
        result = test_api(method, endpoint, data, desc)
        test_results.append(result)
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {desc}: {result.get('status_code', 'ERROR')} ({result.get('response_time_ms', 0)}ms)")
    
    # 获取一个数据集ID用于后续测试
    dataset_id = None
    datasets_result = test_api("GET", "/api/v1/datasets")
    if datasets_result.get("success") and datasets_result.get("response", {}).get("code") == 0:
        datasets = datasets_result["response"]["data"]
        if datasets:
            dataset_id = datasets[0]["id"]
            print(f"📝 使用数据集ID: {dataset_id}")
    
    # 3. 文档管理接口（如果有数据集ID）
    if dataset_id:
        print("\n📄 文档管理接口")
        tests = [
            ("GET", f"/api/v1/datasets/{dataset_id}/documents", None, "获取文档列表"),
            ("GET", f"/api/v1/datasets/{dataset_id}/documents?page=1&page_size=5", None, "分页获取文档"),
        ]
        
        for method, endpoint, data, desc in tests:
            result = test_api(method, endpoint, data, desc)
            test_results.append(result)
            status = "✅" if result.get("success") else "❌"
            print(f"{status} {desc}: {result.get('status_code', 'ERROR')} ({result.get('response_time_ms', 0)}ms)")
    
    # 4. 对话管理接口
    print("\n💬 对话管理接口")
    tests = [
        ("GET", "/api/v1/chats", None, "获取对话列表"),
        ("GET", "/api/v1/chats?page=1&page_size=5", None, "分页获取对话"),
    ]
    
    # 创建对话测试（如果有数据集ID）
    if dataset_id:
        tests.append(("POST", "/api/v1/chats", {
            "name": "API测试对话_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "description": "用于API测试的对话",
            "dataset_ids": [dataset_id]
        }, "创建对话"))
    
    for method, endpoint, data, desc in tests:
        result = test_api(method, endpoint, data, desc)
        test_results.append(result)
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {desc}: {result.get('status_code', 'ERROR')} ({result.get('response_time_ms', 0)}ms)")
    
    # 5. 统计结果
    print("\n" + "=" * 60)
    print("📈 测试结果统计")
    print("=" * 60)
    
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r.get("success"))
    failed_tests = total_tests - successful_tests
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {successful_tests} (✅)")
    print(f"失败: {failed_tests} (❌)")
    print(f"成功率: {successful_tests/total_tests*100:.1f}%")
    
    # 保存详细结果
    with open("api_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": round(successful_tests/total_tests*100, 1)
            },
            "results": test_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📋 详细结果已保存到: api_test_results.json")
    
    # 显示失败的测试
    failed_results = [r for r in test_results if not r.get("success")]
    if failed_results:
        print("\n❌ 失败的测试:")
        for result in failed_results:
            print(f"  - {result['description']}: {result.get('error', result.get('status_code'))}")

if __name__ == "__main__":
    main()