"""
调试SSE响应格式
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

# 使用刚创建的对话
chat_id = "e734ebbc4fea11f0bc100242ac140006"

print(f"调试SSE响应格式")
print(f"对话ID: {chat_id}")

data = {
    "content": "你好"
}

response = requests.post(
    f"{BASE_URL}/api/v1/chats/{chat_id}/completions",
    headers=headers,
    json=data
)

print(f"\n状态码: {response.status_code}")
print(f"响应头: {dict(response.headers)}")
print(f"\n原始响应:")
print("-" * 80)
print(repr(response.text))
print("-" * 80)

print(f"\n格式化响应:")
print("-" * 80)
print(response.text)
print("-" * 80)

# 尝试解析SSE格式
print(f"\n解析SSE数据:")
lines = response.text.split('\n')
for i, line in enumerate(lines):
    print(f"行 {i+1}: {repr(line)}")
    
    if line.startswith('data:'):
        json_part = line[5:].strip()
        try:
            parsed = json.loads(json_part)
            print(f"  解析成功: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"  解析失败: {e}")
            print(f"  JSON部分: {repr(json_part)}")

# 尝试不同的解析方式
print(f"\n尝试整体解析:")
try:
    # 方式1: 假设是单行JSON
    result = json.loads(response.text)
    print(f"整体JSON解析成功: {json.dumps(result, indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"整体JSON解析失败: {e}")

# 方式2: 处理多行SSE
print(f"\n处理多行SSE:")
data_lines = []
for line in response.text.split('\n'):
    if line.startswith('data:'):
        data_lines.append(line[5:].strip())

print(f"找到 {len(data_lines)} 个data行:")
for i, data_line in enumerate(data_lines):
    print(f"Data {i+1}: {data_line}")
    try:
        parsed = json.loads(data_line)
        print(f"  解析成功！")
        if 'data' in parsed and 'answer' in parsed.get('data', {}):
            answer = parsed['data']['answer']
            print(f"  回答: {answer[:100]}...")
    except Exception as e:
        print(f"  解析失败: {e}")