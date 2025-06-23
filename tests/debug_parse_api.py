"""
调试文档解析API
"""
import requests
import json

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# 使用刚才创建的知识库和文档
kb_id = "96f213004fea11f096400242ac140006"
doc_id = "9715372c4fea11f0a07f0242ac140006"

print(f"测试文档解析API")
print(f"知识库ID: {kb_id}")
print(f"文档ID: {doc_id}")

# 测试不同的解析API路径
parse_endpoints = [
    f"/api/v1/datasets/{kb_id}/documents/{doc_id}/run",
    f"/api/v1/datasets/{kb_id}/documents/{doc_id}/parse",
    f"/api/v1/datasets/{kb_id}/documents/{doc_id}/start",
    f"/api/v1/documents/{doc_id}/run",
    f"/api/v1/documents/{doc_id}/parse",
    f"/api/v1/datasets/{kb_id}/documents/run",  # 批量解析
    f"/api/v1/datasets/{kb_id}/run",  # 知识库级别解析
]

print(f"\n测试解析端点:")
print("="*60)

for endpoint in parse_endpoints:
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers=headers
        )
        
        print(f"\n端点: {endpoint}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}")
                if result.get('code') == 0:
                    print(f"✅ 成功!")
                else:
                    print(f"❌ API错误: {result.get('message', 'Unknown')}")
            except:
                print(f"响应文本: {response.text[:200]}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

# 测试文档状态查看
print(f"\n\n测试文档状态查看:")
print("="*60)

status_endpoints = [
    f"/api/v1/datasets/{kb_id}/documents/{doc_id}",
    f"/api/v1/datasets/{kb_id}/documents/{doc_id}/status",
    f"/api/v1/documents/{doc_id}",
    f"/api/v1/documents/{doc_id}/status",
]

for endpoint in status_endpoints:
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers
        )
        
        print(f"\n端点: {endpoint}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:300]}")
            except:
                print(f"响应文本: {response.text[:200]}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

print(f"\n完成调试")