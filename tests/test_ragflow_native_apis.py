"""
测试RAGFlow原生API接口
"""
import requests
import json
import os
import time
from datetime import datetime
from pathlib import Path

# RAGFlow API配置
RAGFLOW_API_URL = os.getenv('RAGFLOW_API_URL', 'http://150.109.16.195:7080')
API_KEY = os.getenv('RAGFLOW_API_KEY', 'ragflow-g4ZWE3OTNhNDUxYTExZjA8MTljMDI0Mm')

# 请求头
headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# 测试数据
TEST_KB_NAME = f"测试知识库_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def test_list_datasets():
    """测试获取知识库列表"""
    print("\n1. 测试获取知识库列表...")
    
    url = f"{RAGFLOW_API_URL}/api/v1/datasets"
    params = {
        'page': 1,
        'page_size': 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"   ✓ 成功获取知识库列表")
                datasets = data.get('data', [])
                print(f"   知识库数量: {len(datasets)}")
                
                # 打印前3个知识库
                for i, kb in enumerate(datasets[:3]):
                    print(f"   - {kb['name']} (ID: {kb['id']})")
                
                return datasets
            else:
                print(f"   ✗ 失败: {data.get('message', 'Unknown error')}")
                return []
        else:
            print(f"   ✗ 失败: {response.text}")
            return []
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
        return []


def test_create_dataset():
    """测试创建知识库"""
    print("\n2. 测试创建知识库...")
    
    url = f"{RAGFLOW_API_URL}/api/v1/datasets"
    data = {
        "name": TEST_KB_NAME,
        "description": "API测试创建的知识库",
        "language": "Chinese",
        "embedding_model": "BAAI/bge-m3",
        "chunk_method": "naive",
        "parser_config": {
            "chunk_token_num": 512,
            "delimiter": "\n"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                kb_id = result['data']['id']
                print(f"   ✓ 成功创建知识库")
                print(f"   知识库ID: {kb_id}")
                print(f"   知识库名称: {result['data']['name']}")
                return kb_id
            else:
                print(f"   ✗ 创建失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ 请求失败: {response.text}")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    return None


def test_upload_document(kb_id):
    """测试上传文档"""
    print(f"\n3. 测试上传文档到知识库 {kb_id}...")
    
    # 创建测试文件
    test_file = Path("test_doc.txt")
    test_content = f"""测试文档
创建时间: {datetime.now()}

这是一个用于测试RAGFlow知识库的文档。

主要内容：
1. RAGFlow是一个基于深度学习的检索增强生成系统
2. 支持多种文档格式的上传和解析
3. 提供了完整的API接口用于集成

测试段落：
RAGFlow使用了先进的向量检索技术，能够快速从大量文档中找到相关内容。
系统支持中英文双语，并且可以处理PDF、Word、TXT等多种格式的文档。
"""
    test_file.write_text(test_content, encoding='utf-8')
    
    try:
        url = f"{RAGFLOW_API_URL}/api/v1/datasets/{kb_id}/documents"
        
        # 准备文件上传
        files = {
            'file': ('test_doc.txt', open(test_file, 'rb'), 'text/plain')
        }
        
        # 移除Content-Type header让requests自动设置
        upload_headers = {
            'Authorization': headers['Authorization']
        }
        
        response = requests.post(url, headers=upload_headers, files=files)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                doc_id = result['data']['id']
                print(f"   ✓ 成功上传文档")
                print(f"   文档ID: {doc_id}")
                print(f"   文档名称: {result['data']['name']}")
                return doc_id
            else:
                print(f"   ✗ 上传失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ 请求失败: {response.text}")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    finally:
        # 清理测试文件
        if test_file.exists():
            test_file.unlink()
    
    return None


def test_list_documents(kb_id):
    """测试获取文档列表"""
    print(f"\n4. 测试获取知识库 {kb_id} 的文档列表...")
    
    url = f"{RAGFLOW_API_URL}/api/v1/datasets/{kb_id}/documents"
    params = {
        'page': 1,
        'page_size': 20
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                docs = result.get('data', [])
                print(f"   ✓ 成功获取文档列表")
                print(f"   文档数量: {len(docs)}")
                
                for doc in docs[:3]:
                    print(f"   - {doc['name']} (状态: {doc.get('status', 'unknown')})")
                
                return docs
            else:
                print(f"   ✗ 获取失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ 请求失败: {response.text}")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    return []


def test_parse_document(kb_id, doc_id):
    """测试解析文档"""
    print(f"\n5. 测试解析文档 {doc_id}...")
    
    url = f"{RAGFLOW_API_URL}/api/v1/datasets/{kb_id}/documents/{doc_id}/run"
    
    try:
        response = requests.post(url, headers=headers)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print(f"   ✓ 成功触发文档解析")
                return True
            else:
                print(f"   ✗ 解析失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ 请求失败: {response.text}")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    return False


def test_chat_with_kb(kb_id):
    """测试基于知识库的对话"""
    print(f"\n6. 测试基于知识库 {kb_id} 的对话...")
    
    # 创建对话
    url = f"{RAGFLOW_API_URL}/api/v1/chats"
    data = {
        "name": f"测试对话_{datetime.now().strftime('%H%M%S')}",
        "dataset_ids": [kb_id]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"   创建对话状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                chat_id = result['data']['id']
                print(f"   ✓ 成功创建对话")
                print(f"   对话ID: {chat_id}")
                
                # 发送消息
                msg_url = f"{RAGFLOW_API_URL}/api/v1/chats/{chat_id}/messages"
                msg_data = {
                    "content": "请介绍一下RAGFlow系统"
                }
                
                msg_response = requests.post(msg_url, headers=headers, json=msg_data)
                print(f"   发送消息状态码: {msg_response.status_code}")
                
                if msg_response.status_code == 200:
                    msg_result = msg_response.json()
                    if msg_result.get('code') == 0:
                        print(f"   ✓ 成功发送消息")
                        answer = msg_result.get('data', {}).get('answer', 'No answer')
                        print(f"   回复: {answer[:100]}..." if len(answer) > 100 else f"   回复: {answer}")
                        return True
        
        print(f"   ✗ 对话失败")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    return False


def test_delete_dataset(kb_id):
    """测试删除知识库"""
    print(f"\n7. 测试删除知识库 {kb_id}...")
    
    url = f"{RAGFLOW_API_URL}/api/v1/datasets/{kb_id}"
    
    try:
        response = requests.delete(url, headers=headers)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:
                print(f"   ✓ 成功删除知识库")
                return True
            else:
                print(f"   ✗ 删除失败: {result.get('message', 'Unknown error')}")
        else:
            print(f"   ✗ 请求失败: {response.text}")
    
    except Exception as e:
        print(f"   ✗ 错误: {str(e)}")
    
    return False


def main():
    """运行所有测试"""
    print(f"\n{'='*60}")
    print(f"RAGFlow API 测试")
    print(f"API地址: {RAGFLOW_API_URL}")
    print(f"测试时间: {datetime.now()}")
    print(f"{'='*60}")
    
    # 1. 获取知识库列表
    datasets = test_list_datasets()
    
    # 2. 创建知识库
    kb_id = test_create_dataset()
    
    if kb_id:
        # 3. 上传文档
        doc_id = test_upload_document(kb_id)
        
        # 4. 获取文档列表
        docs = test_list_documents(kb_id)
        
        if doc_id:
            # 5. 解析文档
            test_parse_document(kb_id, doc_id)
            
            # 等待解析完成
            print("\n   等待文档解析完成...")
            time.sleep(5)
        
        # 6. 基于知识库对话
        test_chat_with_kb(kb_id)
        
        # 7. 删除知识库
        test_delete_dataset(kb_id)
    
    print(f"\n{'='*60}")
    print(f"测试完成")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()