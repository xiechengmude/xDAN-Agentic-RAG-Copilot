#!/usr/bin/env python3
"""
诊断删除接口500错误的专用脚本
"""

import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
API_BASE_URL = "http://localhost:8050"
RAGFLOW_BASE_URL = "http://150.109.16.195:7080"
API_KEY = "xDAN-RAG-Service-Demo-Key"
RAGFLOW_API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

def test_direct_ragflow_delete():
    """直接测试RAGFlow的删除接口"""
    print("\n=== 测试直接调用RAGFlow删除接口 ===")
    
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. 测试删除数据集（批量接口）
    print("\n1. 测试RAGFlow删除数据集（批量接口）")
    try:
        # RAGFlow使用批量删除接口
        url = f"{RAGFLOW_BASE_URL}/api/v1/datasets"
        data = {"ids": ["test_dataset_id"]}
        
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求数据: {json.dumps(data)}")
        logger.debug(f"请求头: {headers}")
        
        response = requests.delete(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
        if response.status_code != 200:
            # 尝试解析错误信息
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
                
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)
    
    # 2. 测试删除文档（批量接口）
    print("\n2. 测试RAGFlow删除文档（批量接口）")
    try:
        dataset_id = "7e8d9e924cde11f0afc90242ac140006"  # 使用配置中的默认数据集
        url = f"{RAGFLOW_BASE_URL}/api/v1/datasets/{dataset_id}/documents"
        data = {"ids": ["test_doc_id"]}
        
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求数据: {json.dumps(data)}")
        
        response = requests.delete(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
                
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)

def test_proxy_delete():
    """测试通过代理服务器的删除接口"""
    print("\n\n=== 测试通过代理服务器的删除接口 ===")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. 测试删除数据集
    print("\n1. 测试代理删除数据集")
    try:
        url = f"{API_BASE_URL}/api/v1/datasets/test_dataset_id"
        
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求头: {headers}")
        
        response = requests.delete(url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
        if response.status_code == 500:
            # 分析500错误
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
                
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)
    
    # 2. 测试批量删除文档
    print("\n2. 测试代理批量删除文档")
    try:
        dataset_id = "7e8d9e924cde11f0afc90242ac140006"
        url = f"{API_BASE_URL}/api/v1/datasets/{dataset_id}/documents"
        data = {"ids": ["test_doc_id"]}
        
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求数据: {json.dumps(data)}")
        
        response = requests.delete(url, headers=headers, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
                
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)
    
    # 3. 测试删除单个文档
    print("\n3. 测试代理删除单个文档")
    try:
        dataset_id = "7e8d9e924cde11f0afc90242ac140006"
        doc_id = "test_doc_id"
        url = f"{API_BASE_URL}/api/v1/datasets/{dataset_id}/documents/{doc_id}"
        
        logger.debug(f"请求URL: {url}")
        
        response = requests.delete(url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:500]}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"原始响应: {response.text}")
                
    except Exception as e:
        logger.error(f"请求失败: {e}", exc_info=True)

def test_ragflow_connectivity():
    """测试RAGFlow服务连通性"""
    print("\n=== 测试RAGFlow服务连通性 ===")
    
    headers = {
        "Authorization": f"Bearer {RAGFLOW_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # 测试获取数据集列表
        url = f"{RAGFLOW_BASE_URL}/api/v1/datasets"
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"RAGFlow服务状态: {'正常' if response.status_code == 200 else '异常'}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                datasets = result.get("data", [])
                print(f"成功获取到 {len(datasets)} 个数据集")
            else:
                print(f"API返回错误: {result.get('message')}")
        else:
            print(f"响应: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print("错误: 连接RAGFlow服务超时")
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到RAGFlow服务")
    except Exception as e:
        print(f"错误: {e}")

def analyze_delete_api_differences():
    """分析删除接口的差异"""
    print("\n=== 分析删除接口差异 ===")
    
    print("\n根据代码分析:")
    print("1. RAGFlow删除数据集:")
    print("   - URL: DELETE /api/v1/datasets")
    print("   - Body: {\"ids\": [dataset_id1, dataset_id2, ...]}")
    print("   - 使用批量删除接口")
    
    print("\n2. RAGFlow删除文档:")
    print("   - URL: DELETE /api/v1/datasets/{dataset_id}/documents")
    print("   - Body: {\"ids\": [doc_id1, doc_id2, ...]}")
    print("   - 也是批量删除接口")
    
    print("\n3. 代理服务器处理:")
    print("   - 单个删除: DELETE /api/v1/datasets/{dataset_id}")
    print("   - 内部转换为批量删除调用")
    print("   - 单个文档删除: DELETE /api/v1/datasets/{dataset_id}/documents/{doc_id}")
    print("   - 内部也转换为批量删除调用")

if __name__ == "__main__":
    print("=== RAGFlow删除接口诊断脚本 ===")
    print(f"代理服务器: {API_BASE_URL}")
    print(f"RAGFlow服务: {RAGFLOW_BASE_URL}")
    
    # 1. 先测试连通性
    test_ragflow_connectivity()
    
    # 2. 测试直接调用RAGFlow
    test_direct_ragflow_delete()
    
    # 3. 测试通过代理调用
    test_proxy_delete()
    
    # 4. 分析差异
    analyze_delete_api_differences()
    
    print("\n诊断完成!")