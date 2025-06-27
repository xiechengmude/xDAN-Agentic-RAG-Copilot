#!/usr/bin/env python3
"""
Swagger API 接口健康检查脚本
检查所有API接口是否可以正常访问
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import time

API_BASE_URL = "http://150.109.16.195:8050"
OPENAPI_URL = f"{API_BASE_URL}/openapi.json"

def fetch_openapi_spec() -> Dict:
    """获取OpenAPI规范"""
    try:
        response = requests.get(OPENAPI_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 无法获取OpenAPI规范: {e}")
        sys.exit(1)

def extract_endpoints(openapi_spec: Dict) -> List[Tuple[str, str, Dict]]:
    """从OpenAPI规范中提取所有端点"""
    endpoints = []
    paths = openapi_spec.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                endpoints.append((method.upper(), path, details))
    
    return endpoints

def check_endpoint(method: str, path: str, details: Dict) -> Dict:
    """检查单个端点的可访问性"""
    # 处理路径参数
    test_path = path
    if "{chat_id}" in path:
        test_path = path.replace("{chat_id}", "test-chat-id")
    if "{dataset_id}" in path:
        test_path = path.replace("{dataset_id}", "test-dataset-id")
    if "{document_id}" in path:
        test_path = path.replace("{document_id}", "test-document-id")
    
    url = f"{API_BASE_URL}{test_path}"
    result = {
        "method": method,
        "path": path,
        "url": url,
        "summary": details.get("summary", ""),
        "requires_auth": bool(details.get("security")),
        "status": "unknown",
        "status_code": None,
        "response_time": None,
        "error": None,
        "has_path_params": "{" in path
    }
    
    headers = {"Content-Type": "application/json"}
    if result["requires_auth"]:
        headers["Authorization"] = "Bearer xDAN-RAG-Service-Demo-Key"
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json={}, timeout=5)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json={}, timeout=5)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=5)
        else:
            response = requests.request(method, url, headers=headers, timeout=5)
        
        response_time = (time.time() - start_time) * 1000
        
        result["status_code"] = response.status_code
        result["response_time"] = f"{response_time:.2f}ms"
        
        if response.status_code < 500:
            result["status"] = "ok"
        else:
            result["status"] = "error"
            result["error"] = f"服务器错误 {response.status_code}"
            
    except requests.exceptions.Timeout:
        result["status"] = "timeout"
        result["error"] = "请求超时"
    except requests.exceptions.ConnectionError:
        result["status"] = "unreachable"
        result["error"] = "无法连接到服务器"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result

def print_results(results: List[Dict]):
    """打印检查结果"""
    print("\n" + "="*80)
    print(f"API 健康检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"\n基础URL: {API_BASE_URL}")
    print(f"总接口数: {len(results)}\n")
    
    stats = {
        "ok": 0,
        "error": 0,
        "timeout": 0,
        "unreachable": 0,
        "unknown": 0
    }
    
    for result in results:
        stats[result["status"]] += 1
        
        status_icon = {
            "ok": "✅",
            "error": "❌",
            "timeout": "⏱️",
            "unreachable": "🔌",
            "unknown": "❓"
        }[result["status"]]
        
        print(f"{status_icon} {result['method']:6} {result['path']}")
        print(f"   摘要: {result['summary']}")
        print(f"   需要认证: {'是' if result['requires_auth'] else '否'}")
        
        if result["has_path_params"]:
            print(f"   注意: 此接口包含路径参数")
        if result["status_code"]:
            print(f"   状态码: {result['status_code']}")
        if result["response_time"]:
            print(f"   响应时间: {result['response_time']}")
        if result["error"]:
            print(f"   错误: {result['error']}")
        print()
    
    print("="*80)
    print("统计摘要:")
    print(f"  ✅ 正常: {stats['ok']}")
    print(f"  ❌ 错误: {stats['error']}")
    print(f"  ⏱️  超时: {stats['timeout']}")
    print(f"  🔌 无法连接: {stats['unreachable']}")
    print(f"  ❓ 未知: {stats['unknown']}")
    print("="*80)
    
    success_rate = (stats['ok'] / len(results) * 100) if results else 0
    print(f"\n成功率: {success_rate:.1f}%")
    
    if stats['ok'] == len(results):
        print("\n🎉 所有接口都可以正常访问！")
    elif stats['unreachable'] > 0:
        print("\n⚠️  服务器似乎无法访问，请检查网络连接和服务器状态。")
    else:
        print(f"\n⚠️  有 {len(results) - stats['ok']} 个接口存在问题，请检查上面的详细信息。")

def main():
    """主函数"""
    print("开始检查API接口...\n")
    
    openapi_spec = fetch_openapi_spec()
    print(f"✅ 成功获取OpenAPI规范")
    print(f"   API标题: {openapi_spec.get('info', {}).get('title', 'Unknown')}")
    print(f"   API版本: {openapi_spec.get('info', {}).get('version', 'Unknown')}")
    
    endpoints = extract_endpoints(openapi_spec)
    print(f"\n发现 {len(endpoints)} 个API端点\n")
    
    print("开始检查每个端点...")
    results = []
    
    for i, (method, path, details) in enumerate(endpoints, 1):
        print(f"[{i}/{len(endpoints)}] 检查 {method} {path}...", end="", flush=True)
        result = check_endpoint(method, path, details)
        results.append(result)
        
        if result["status"] == "ok":
            print(" ✅")
        else:
            print(f" {result['status'].upper()}")
        
        time.sleep(0.1)
    
    print_results(results)
    
    return 0 if all(r["status"] == "ok" for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())