#!/usr/bin/env python3
"""
API接口结构验证测试
验证每个接口的请求/响应格式是否符合预期
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# 清除代理
for var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    if var in os.environ:
        del os.environ[var]

# 加载环境变量
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'
load_dotenv(env_path)

sys.path.append(str(project_root))

from src.clients.xdan_rag_client import XDANRagClient, APIError
from config.settings import RAGFLOW_API_URL, RAGFLOW_API_KEY, DEFAULT_DATASET_ID

class APIStructureValidator:
    """API结构验证器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8050"
        self.client = XDANRagClient(api_url=RAGFLOW_API_URL, api_key=RAGFLOW_API_KEY)
        self.results = []
    
    def validate_response_structure(self, response: Dict[str, Any], expected_fields: Dict[str, type]) -> bool:
        """验证响应结构"""
        for field, expected_type in expected_fields.items():
            if field not in response:
                print(f"    ❌ 缺少字段: {field}")
                return False
            if not isinstance(response[field], expected_type):
                print(f"    ❌ 字段类型错误: {field} 应为 {expected_type.__name__}，实际为 {type(response[field]).__name__}")
                return False
        return True
    
    def test_health_check(self):
        """测试健康检查接口"""
        print("\n1. 健康检查接口 (GET /api/health)")
        
        try:
            response = requests.get(f"{self.base_url}/api/health")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ 状态码错误")
                return False
            
            data = response.json()
            print(f"   响应: {json.dumps(data, indent=2)}")
            
            # 验证响应结构
            expected = {
                "status": str,
                "api_connected": bool,
                "timestamp": str
            }
            
            if self.validate_response_structure(data, expected):
                print("   ✅ 响应结构正确")
                return True
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
    
    def test_openapi_spec(self):
        """测试OpenAPI规范接口"""
        print("\n2. OpenAPI规范 (GET /openapi.json)")
        
        try:
            response = requests.get(f"{self.base_url}/openapi.json")
            print(f"   状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ 状态码错误")
                return False
            
            data = response.json()
            
            # 验证基本结构
            required_fields = ["openapi", "info", "paths"]
            for field in required_fields:
                if field not in data:
                    print(f"   ❌ 缺少必需字段: {field}")
                    return False
            
            print(f"   OpenAPI版本: {data['openapi']}")
            print(f"   API标题: {data['info'].get('title')}")
            print(f"   接口数量: {len(data['paths'])}")
            print("   ✅ OpenAPI规范正确")
            return True
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
    
    def test_search_stream_api(self):
        """测试S3搜索流式接口"""
        print("\n3. S3搜索流式接口 (POST /api/search/stream)")
        
        # 测试正常请求
        payload = {
            "question": "测试问题",
            "dataset_ids": [DEFAULT_DATASET_ID],
            "max_rounds": 1,
            "top_k": 3,
            "similarity_threshold": 0.3
        }
        
        print("   请求体结构:")
        for key, value in payload.items():
            print(f"     - {key}: {type(value).__name__}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search/stream",
                json=payload,
                stream=True
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ 状态码错误")
                return False
            
            # 验证Content-Type
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' not in content_type:
                print(f"   ❌ Content-Type错误: {content_type}")
                return False
            
            print("   ✅ Content-Type: text/event-stream")
            
            # 验证流式响应格式
            event_types = set()
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            event = json.loads(data)
                            event_types.add(event.get('event_type'))
                            
                            # 验证事件结构
                            if 'event_type' not in event or 'timestamp' not in event:
                                print("   ❌ 事件结构错误")
                                return False
                        except json.JSONDecodeError:
                            print("   ❌ JSON解析错误")
                            return False
            
            print(f"   收到事件类型: {event_types}")
            print("   ✅ 流式响应格式正确")
            
            # 测试错误请求
            print("\n   测试错误请求处理:")
            bad_payload = {"invalid": "data"}
            response = requests.post(
                f"{self.base_url}/api/search/stream",
                json=bad_payload
            )
            
            if response.status_code in [400, 422]:
                print(f"   ✅ 错误请求正确返回 {response.status_code}")
                return True
            else:
                print(f"   ❌ 错误请求处理不当: {response.status_code}")
                return False
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
    
    def test_chat_stream_api(self):
        """测试对话流式接口"""
        print("\n4. 对话流式接口 (POST /api/chat/stream)")
        
        # 测试创建新对话
        payload = {
            "question": "测试消息",
            "chat_id": None,
            "dataset_ids": [DEFAULT_DATASET_ID]
        }
        
        print("   请求体结构:")
        for key, value in payload.items():
            print(f"     - {key}: {type(value).__name__ if value is not None else 'None'}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/stream",
                json=payload,
                stream=True
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code != 200:
                print("   ❌ 状态码错误")
                return False
            
            # 验证响应中是否包含chat_id
            chat_id_found = False
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        try:
                            event = json.loads(data)
                            if event.get('event_type') == 'chat_created':
                                chat_id = event.get('data', {}).get('chat_id')
                                if chat_id:
                                    print(f"   ✅ 创建对话成功，chat_id: {chat_id}")
                                    chat_id_found = True
                                    break
                        except:
                            pass
            
            if not chat_id_found:
                print("   ❌ 未找到chat_id")
                return False
            
            print("   ✅ 对话接口响应结构正确")
            return True
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
    
    def test_ragflow_api_structure(self):
        """测试RAGFlow API响应结构"""
        print("\n5. RAGFlow API响应结构")
        
        # 测试数据集列表
        print("\n   5.1 数据集列表接口")
        try:
            result = self.client.list_datasets(page_size=2)
            
            # 验证响应包含必要字段
            if 'datasets' in result or 'data' in result:
                print("   ✅ 数据集列表响应结构正确")
            else:
                print("   ❌ 数据集列表响应结构错误")
                return False
            
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
        
        # 测试检索接口
        print("\n   5.2 检索接口")
        try:
            result = self.client.retrieve_chunks(
                question="test",
                dataset_ids=[DEFAULT_DATASET_ID],
                page_size=2
            )
            
            # 验证响应结构
            if 'chunks' in result:
                chunks = result['chunks']
                if chunks and len(chunks) > 0:
                    # 验证chunk结构
                    chunk = chunks[0]
                    required_fields = ['content', 'similarity']
                    for field in required_fields:
                        if field not in chunk:
                            print(f"   ❌ chunk缺少字段: {field}")
                            return False
                    
                    print("   ✅ 检索响应结构正确")
                    print(f"     - 返回chunks数: {len(chunks)}")
                    print(f"     - 包含相似度: {chunk.get('similarity')}")
                else:
                    print("   ⚠️  没有检索到chunks")
            else:
                print("   ❌ 检索响应缺少chunks字段")
                return False
                
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
        
        return True
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n6. 错误处理测试")
        
        # 测试404错误
        print("\n   6.1 测试404错误")
        response = requests.get(f"{self.base_url}/api/nonexistent")
        print(f"   状态码: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ 404错误处理正确")
        else:
            print("   ❌ 404错误处理异常")
            return False
        
        # 测试无效的JSON
        print("\n   6.2 测试无效请求体")
        response = requests.post(
            f"{self.base_url}/api/search/stream",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [400, 422]:
            print(f"   ✅ 无效JSON正确返回 {response.status_code}")
        else:
            print(f"   ❌ 无效JSON处理不当: {response.status_code}")
            return False
        
        return True
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("API接口结构验证测试")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        tests = [
            ("健康检查", self.test_health_check),
            ("OpenAPI规范", self.test_openapi_spec),
            ("S3搜索接口", self.test_search_stream_api),
            ("对话接口", self.test_chat_stream_api),
            ("RAGFlow API结构", self.test_ragflow_api_structure),
            ("错误处理", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                self.results.append((test_name, success))
            except Exception as e:
                print(f"\n❌ {test_name} 测试异常: {e}")
                self.results.append((test_name, False))
        
        # 打印总结
        print("\n" + "=" * 60)
        print("测试总结")
        print("=" * 60)
        
        for test_name, success in self.results:
            status = "✅ 通过" if success else "❌ 失败"
            print(f"{test_name}: {status}")
        
        total = len(self.results)
        passed = sum(1 for _, success in self.results if success)
        
        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        
        if passed == total:
            print("\n🎉 所有接口结构验证通过！")
            print("✅ 每个接口都畅通且返回结果符合预期结构")
            return True
        else:
            print(f"\n❌ 有 {total - passed} 个测试失败")
            return False

def main():
    # 确保服务器正在运行
    try:
        health_check = requests.get("http://localhost:8050/api/health", timeout=2)
        if health_check.status_code != 200:
            print("❌ 服务器未运行，请先启动服务器")
            return 1
    except:
        print("❌ 无法连接到服务器，请先启动服务器")
        return 1
    
    validator = APIStructureValidator()
    success = validator.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())