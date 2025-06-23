"""
简单的API测试脚本
"""
import requests
import json
from datetime import datetime

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

# 测试获取知识库列表
print(f"\n测试时间: {datetime.now()}")
print("="*60)

print("\n1. 测试获取知识库列表...")
url = f"{BASE_URL}/api/v1/datasets"
headers = {
    "Authorization": f"Bearer {API_KEY}"
}

response = requests.get(url, headers=headers)
print(f"状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"响应内容: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
    
    if data.get('code') == 0:
        datasets = data.get('data', [])
        print(f"\n✓ 成功！找到 {len(datasets)} 个知识库")
        
        # 使用现有的知识库进行测试
        if datasets:
            test_kb = datasets[0]
            kb_id = test_kb['id']
            print(f"\n使用知识库进行测试: {test_kb['name']} (ID: {kb_id})")
            
            # 测试获取文档列表
            print("\n2. 测试获取文档列表...")
            doc_url = f"{BASE_URL}/api/v1/datasets/{kb_id}/documents"
            doc_response = requests.get(doc_url, headers=headers)
            print(f"状态码: {doc_response.status_code}")
            
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                if doc_data.get('code') == 0:
                    docs = doc_data.get('data')
                    if isinstance(docs, list):
                        print(f"✓ 成功！找到 {len(docs)} 个文档")
                        for doc in docs[:3]:
                            print(f"  - {doc.get('name', 'Unknown')} (状态: {doc.get('status', 'unknown')})")
                    elif isinstance(docs, dict) and 'docs' in docs:
                        # 可能是分页响应
                        doc_list = docs.get('docs', [])
                        print(f"✓ 成功！找到 {len(doc_list)} 个文档")
                        for doc in doc_list[:3]:
                            print(f"  - {doc.get('name', 'Unknown')} (状态: {doc.get('status', 'unknown')})")
                    else:
                        print(f"✓ 文档数据格式: {type(docs)}")
else:
    print(f"✗ 请求失败: {response.text}")

print("\n" + "="*60)