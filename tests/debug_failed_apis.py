"""
调试失败的API接口
"""
import requests
import json
from datetime import datetime
from pathlib import Path

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}


def debug_upload_document():
    """调试文档上传接口"""
    print("\n1. 调试文档上传接口")
    print("="*60)
    
    # 使用现有的知识库
    kb_id = "7e9fe1de4ce211f09cf90242ac140006"  # test知识库
    
    # 创建测试文件
    test_file = Path("debug_upload.txt")
    test_content = f"""调试文档
时间: {datetime.now()}
内容: 测试文档上传API
"""
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        # 方式1: 使用files参数
        print("\n尝试方式1: 使用 'file' 字段")
        with open(test_file, 'rb') as f:
            files = {
                'file': ('debug_upload.txt', f, 'text/plain')
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets/{kb_id}/documents",
                headers=headers,
                files=files
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            print(f"响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n解析后的JSON:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"JSON解析错误: {e}")
        
        # 方式2: 使用files[]参数（根据接口文档）
        print("\n\n尝试方式2: 使用 'files[]' 字段")
        with open(test_file, 'rb') as f:
            files = {
                'files[]': ('debug_upload.txt', f, 'text/plain')
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets/{kb_id}/documents",
                headers=headers,
                files=files
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n解析后的JSON:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                except Exception as e:
                    print(f"JSON解析错误: {e}")
        
        # 方式3: 使用多个文件
        print("\n\n尝试方式3: 使用多个文件")
        with open(test_file, 'rb') as f:
            files = [
                ('file', ('debug_upload1.txt', f, 'text/plain')),
            ]
            
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets/{kb_id}/documents",
                headers=headers,
                files=files
            )
            
            print(f"状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if test_file.exists():
            test_file.unlink()


def debug_send_message():
    """调试发送消息接口"""
    print("\n\n2. 调试发送消息接口")
    print("="*60)
    
    # 先创建一个对话
    kb_id = "7e9fe1de4ce211f09cf90242ac140006"
    
    # 创建对话
    print("\n创建新对话...")
    chat_data = {
        "name": f"调试对话_{datetime.now().strftime('%H%M%S')}",
        "dataset_ids": [kb_id]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chats",
        headers={**headers, "Content-Type": "application/json"},
        json=chat_data
    )
    
    print(f"创建对话状态码: {response.status_code}")
    print(f"创建对话响应: {response.text[:200]}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            chat_id = result['data']['id']
            print(f"成功创建对话，ID: {chat_id}")
            
            # 测试不同的消息发送方式
            print("\n\n发送消息测试...")
            
            # 方式1: 基本消息
            print("\n方式1: 发送基本消息")
            msg_data = {
                "content": "你好，请介绍一下自己"
            }
            
            msg_response = requests.post(
                f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
                headers={**headers, "Content-Type": "application/json"},
                json=msg_data
            )
            
            print(f"状态码: {msg_response.status_code}")
            print(f"响应头: {dict(msg_response.headers)}")
            print(f"响应内容前500字符: {msg_response.text[:500]}")
            
            if msg_response.status_code == 200:
                try:
                    msg_result = msg_response.json()
                    print(f"\n完整响应结构:")
                    print(json.dumps(msg_result, indent=2, ensure_ascii=False)[:1000])
                    
                    # 尝试不同的字段名
                    print(f"\n尝试提取响应内容:")
                    print(f"- data字段: {msg_result.get('data', 'Not found')}")
                    print(f"- answer字段: {msg_result.get('answer', 'Not found')}")
                    print(f"- message字段: {msg_result.get('message', 'Not found')}")
                    print(f"- content字段: {msg_result.get('content', 'Not found')}")
                    
                    if 'data' in msg_result:
                        data = msg_result['data']
                        if isinstance(data, dict):
                            print(f"\ndata内部字段:")
                            for key in data.keys():
                                print(f"  - {key}: {str(data[key])[:100]}")
                        elif isinstance(data, list):
                            print(f"\ndata是列表，长度: {len(data)}")
                            if data:
                                print(f"第一个元素: {data[0]}")
                                
                except Exception as e:
                    print(f"JSON解析错误: {e}")
            
            # 方式2: 带stream参数
            print("\n\n方式2: 带stream参数的消息")
            msg_data = {
                "content": "请简单介绍一下测试文档",
                "stream": False
            }
            
            msg_response = requests.post(
                f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
                headers={**headers, "Content-Type": "application/json"},
                json=msg_data
            )
            
            print(f"状态码: {msg_response.status_code}")
            if msg_response.status_code == 200:
                try:
                    result = msg_response.json()
                    print(f"响应格式: {list(result.keys())}")
                except:
                    print(f"响应内容: {msg_response.text[:300]}")


def check_api_docs():
    """检查API文档端点"""
    print("\n\n3. 检查API文档")
    print("="*60)
    
    # 尝试访问API文档
    doc_urls = [
        "/docs",
        "/api/docs",
        "/swagger",
        "/api/v1/docs",
        "/redoc"
    ]
    
    for doc_url in doc_urls:
        try:
            response = requests.get(f"{BASE_URL}{doc_url}")
            if response.status_code == 200:
                print(f"✓ 找到文档: {BASE_URL}{doc_url}")
            else:
                print(f"✗ {doc_url}: {response.status_code}")
        except:
            print(f"✗ {doc_url}: 连接失败")


def main():
    print(f"\nRAGFlow API 调试")
    print(f"时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}")
    
    debug_upload_document()
    debug_send_message()
    check_api_docs()


if __name__ == "__main__":
    main()