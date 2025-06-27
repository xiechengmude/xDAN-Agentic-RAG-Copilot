#!/usr/bin/env python3
"""
Swagger API 接口健康检查脚本（详细版）
检查所有API接口是否可以正常访问，并生成详细的HTML报告
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import time
import argparse

API_BASE_URL = "http://150.109.16.195:8050"
OPENAPI_URL = f"{API_BASE_URL}/openapi.json"
AUTH_TOKEN = "xDAN-RAG-Service-Demo-Key"

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

def prepare_test_data(method: str, path: str, details: Dict) -> Dict:
    """根据接口定义准备测试数据"""
    test_data = {
        "path_params": {},
        "query_params": {},
        "body": None
    }
    
    # 处理路径参数
    if "{chat_id}" in path:
        test_data["path_params"]["chat_id"] = "test-chat-id"
    if "{dataset_id}" in path:
        test_data["path_params"]["dataset_id"] = "test-dataset-id"
    if "{document_id}" in path:
        test_data["path_params"]["document_id"] = "test-doc-id"
    
    # 根据接口准备特定的测试数据
    if path == "/api/v1/chats" and method == "POST":
        test_data["body"] = {
            "name": "Test Chat",
            "dataset_ids": [],
            "description": "API Health Check Test"
        }
    elif path == "/api/v1/datasets" and method == "POST":
        test_data["body"] = {
            "name": "Test Dataset",
            "description": "API Health Check Test"
        }
    elif path == "/api/v1/retrieval" and method == "POST":
        test_data["body"] = {
            "question": "test question",
            "dataset_ids": ["test-dataset-id"]
        }
    elif path == "/api/v1/chats/{chat_id}/completions" and method == "POST":
        test_data["body"] = {
            "content": "Hello, this is a test",
            "stream": False
        }
    elif path == "/api/v1/documents/reference/batch" and method == "POST":
        test_data["body"] = {
            "references": []
        }
    elif path == "/api/v1/documents/reference/{document_id}" and method == "GET":
        test_data["query_params"]["dataset_id"] = "test-dataset-id"
    
    return test_data

def check_endpoint(method: str, path: str, details: Dict, verbose: bool = False) -> Dict:
    """检查单个端点的可访问性"""
    test_data = prepare_test_data(method, path, details)
    
    # 替换路径参数
    test_path = path
    for param, value in test_data["path_params"].items():
        test_path = test_path.replace(f"{{{param}}}", value)
    
    url = f"{API_BASE_URL}{test_path}"
    
    result = {
        "method": method,
        "path": path,
        "url": url,
        "summary": details.get("summary", ""),
        "description": details.get("description", ""),
        "requires_auth": bool(details.get("security")),
        "status": "unknown",
        "status_code": None,
        "response_time": None,
        "error": None,
        "has_path_params": bool(test_data["path_params"]),
        "response_body": None
    }
    
    headers = {"Content-Type": "application/json"}
    if result["requires_auth"]:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    try:
        start_time = time.time()
        
        kwargs = {
            "headers": headers,
            "timeout": 5,
            "params": test_data["query_params"] if test_data["query_params"] else None
        }
        
        if method in ["POST", "PUT", "PATCH"] and test_data["body"] is not None:
            kwargs["json"] = test_data["body"]
        
        response = requests.request(method, url, **kwargs)
        
        response_time = (time.time() - start_time) * 1000
        
        result["status_code"] = response.status_code
        result["response_time"] = f"{response_time:.2f}ms"
        
        if verbose:
            try:
                result["response_body"] = response.json()
            except:
                result["response_body"] = response.text[:500]
        
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

def generate_html_report(results: List[Dict], openapi_spec: Dict) -> str:
    """生成HTML报告"""
    api_info = openapi_spec.get("info", {})
    
    stats = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "error": sum(1 for r in results if r["status"] == "error"),
        "timeout": sum(1 for r in results if r["status"] == "timeout"),
        "unreachable": sum(1 for r in results if r["status"] == "unreachable")
    }
    
    success_rate = (stats["ok"] / len(results) * 100) if results else 0
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>API健康检查报告 - {api_info.get('title', 'Unknown API')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .info {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: flex; gap: 20px; margin-bottom: 30px; }}
        .stat {{ flex: 1; padding: 20px; border-radius: 5px; text-align: center; color: white; }}
        .stat.ok {{ background-color: #4caf50; }}
        .stat.error {{ background-color: #f44336; }}
        .stat.timeout {{ background-color: #ff9800; }}
        .stat.unreachable {{ background-color: #9e9e9e; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f5f5f5; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-ok {{ color: #4caf50; }}
        .status-error {{ color: #f44336; }}
        .status-timeout {{ color: #ff9800; }}
        .status-unreachable {{ color: #9e9e9e; }}
        .method {{ font-weight: bold; padding: 2px 8px; border-radius: 3px; color: white; }}
        .method-GET {{ background-color: #61affe; }}
        .method-POST {{ background-color: #49cc90; }}
        .method-PUT {{ background-color: #fca130; }}
        .method-DELETE {{ background-color: #f93e3e; }}
        .timestamp {{ color: #666; font-size: 14px; }}
        .success-rate {{ font-size: 24px; font-weight: bold; margin: 20px 0; }}
        .note {{ background-color: #fff3cd; padding: 10px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>API健康检查报告</h1>
        <div class="info">
            <h2>{api_info.get('title', 'Unknown API')} - v{api_info.get('version', 'Unknown')}</h2>
            <p>{api_info.get('description', '')}</p>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>基础URL: {API_BASE_URL}</p>
        </div>
        
        <div class="stats">
            <div class="stat ok">
                <h3>正常</h3>
                <div style="font-size: 36px;">{stats['ok']}</div>
            </div>
            <div class="stat error">
                <h3>错误</h3>
                <div style="font-size: 36px;">{stats['error']}</div>
            </div>
            <div class="stat timeout">
                <h3>超时</h3>
                <div style="font-size: 36px;">{stats['timeout']}</div>
            </div>
            <div class="stat unreachable">
                <h3>无法访问</h3>
                <div style="font-size: 36px;">{stats['unreachable']}</div>
            </div>
        </div>
        
        <div class="success-rate">成功率: {success_rate:.1f}%</div>
        
        <h2>详细结果</h2>
        <table>
            <thead>
                <tr>
                    <th>方法</th>
                    <th>路径</th>
                    <th>描述</th>
                    <th>认证</th>
                    <th>状态码</th>
                    <th>响应时间</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for result in results:
        status_class = f"status-{result['status']}"
        method_class = f"method-{result['method']}"
        
        html += f"""                <tr>
                    <td><span class="method {method_class}">{result['method']}</span></td>
                    <td>{result['path']}</td>
                    <td>{result['summary']}</td>
                    <td>{'是' if result['requires_auth'] else '否'}</td>
                    <td>{result['status_code'] or '-'}</td>
                    <td>{result['response_time'] or '-'}</td>
                    <td class="{status_class}">{result['status'].upper()}</td>
                </tr>
"""
    
    html += """            </tbody>
        </table>
        
        <div class="note">
            <strong>注意:</strong> 
            <ul>
                <li>状态码 401 表示需要有效的认证令牌</li>
                <li>状态码 422 表示请求参数验证失败（对于测试数据这是正常的）</li>
                <li>状态码 404 表示资源不存在（对于测试ID这是正常的）</li>
                <li>状态码 500 表示服务器内部错误，需要进一步调查</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
    
    return html

def main():
    parser = argparse.ArgumentParser(description='检查Swagger API接口健康状态')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细的响应信息')
    parser.add_argument('--html', action='store_true', help='生成HTML报告')
    parser.add_argument('--output', '-o', default='api_health_report.html', help='HTML报告输出文件名')
    args = parser.parse_args()
    
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
        result = check_endpoint(method, path, details, args.verbose)
        results.append(result)
        
        if result["status"] == "ok":
            print(" ✅")
        else:
            print(f" {result['status'].upper()}")
        
        if args.verbose and result.get("response_body"):
            print(f"   响应: {json.dumps(result['response_body'], ensure_ascii=False, indent=2)}")
        
        time.sleep(0.1)
    
    if args.html:
        html_content = generate_html_report(results, openapi_spec)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n✅ HTML报告已生成: {args.output}")
    
    # 打印统计
    print("\n" + "="*80)
    stats = {status: sum(1 for r in results if r["status"] == status) 
             for status in ["ok", "error", "timeout", "unreachable"]}
    
    print("统计摘要:")
    print(f"  ✅ 正常: {stats['ok']}")
    print(f"  ❌ 错误: {stats['error']}")
    print(f"  ⏱️  超时: {stats['timeout']}")
    print(f"  🔌 无法连接: {stats['unreachable']}")
    
    success_rate = (stats['ok'] / len(results) * 100) if results else 0
    print(f"\n成功率: {success_rate:.1f}%")
    
    return 0 if stats['error'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())