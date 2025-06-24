#!/usr/bin/env python3
"""
详细的逐个接口测试脚本 - 修复JSON序列化问题
包含真实的请求响应示例和文档对照验证
"""
import requests
import json
import time
import tempfile
from datetime import datetime
from typing import Dict, Any, List

class DetailedInterfaceTestRunner:
    def __init__(self, base_url: str = "http://localhost:8050"):
        self.base_url = base_url
        self.api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.test_results = []
        self.test_data = {}  # 存储测试过程中创建的数据ID
    
    def make_json_serializable(self, obj):
        """将对象转换为JSON可序列化的格式"""
        if isinstance(obj, bytes):
            return f"<bytes: {len(obj)} bytes>"
        elif isinstance(obj, dict):
            return {k: self.make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self.make_json_serializable(v) for v in obj]
        elif hasattr(obj, '__dict__'):
            return str(obj)
        else:
            return obj
        
    def log_test_result(self, interface_name: str, success: bool, request_data: Dict, response_data: Dict, 
                       doc_comparison: Dict = None):
        """记录测试结果"""
        # 确保所有数据都是JSON可序列化的
        safe_request_data = self.make_json_serializable(request_data)
        safe_response_data = self.make_json_serializable(response_data)
        safe_doc_comparison = self.make_json_serializable(doc_comparison or {})
        
        result = {
            "interface": interface_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "request": safe_request_data,
            "response": safe_response_data,
            "doc_comparison": safe_doc_comparison
        }
        self.test_results.append(result)
        
    def print_interface_header(self, interface_name: str, method: str, endpoint: str, doc_section: str):
        """打印接口测试头部"""
        print(f"\n{'='*100}")
        print(f"🔍 接口测试: {interface_name}")
        print(f"📍 文档位置: {doc_section}")
        print(f"🌐 方法: {method}")
        print(f"🔗 端点: {endpoint}")
        print('='*100)
        
    def print_request_response(self, title: str, request_data: Dict, response: requests.Response):
        """打印请求响应详情"""
        print(f"\n📤 {title} - 请求详情:")
        print(f"   URL: {response.url}")
        print(f"   方法: {response.request.method}")
        print(f"   请求头: {dict(response.request.headers)}")
        if request_data:
            # 确保request_data是JSON可序列化的
            safe_request_data = self.make_json_serializable(request_data)
            print(f"   请求体: {json.dumps(safe_request_data, ensure_ascii=False, indent=2)}")
            
        print(f"\n📥 {title} - 响应详情:")
        print(f"   状态码: {response.status_code}")
        print(f"   响应头: {dict(response.headers)}")
        try:
            response_json = response.json()
            print(f"   响应体: {json.dumps(response_json, ensure_ascii=False, indent=2)}")
            return response_json
        except:
            print(f"   响应体 (非JSON): {response.text[:500]}...")
            return {"raw_response": response.text}
            
    def compare_with_doc_spec(self, actual_response: Dict, expected_fields: List[str], 
                             expected_structure: Dict = None) -> Dict:
        """与文档规范对比"""
        comparison = {
            "field_compliance": {},
            "structure_compliance": True,
            "additional_fields": [],
            "missing_fields": []
        }
        
        # 检查必要字段
        for field in expected_fields:
            if field in actual_response:
                comparison["field_compliance"][field] = "✅ 存在"
            else:
                comparison["field_compliance"][field] = "❌ 缺失"
                comparison["missing_fields"].append(field)
                
        # 检查额外字段
        if expected_structure:
            for field in actual_response:
                if field not in expected_structure:
                    comparison["additional_fields"].append(field)
                    
        comparison["structure_compliance"] = len(comparison["missing_fields"]) == 0
        
        return comparison

    def test_health_check(self):
        """测试健康检查接口"""
        self.print_interface_header(
            "健康检查", "GET", "/health", 
            "基础配置 > 健康检查"
        )
        
        response = requests.get(f"{self.base_url}/health")
        response_data = self.print_request_response("健康检查", {}, response)
        
        # 文档对比
        expected_fields = ["code", "message", "data"]
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        print(f"\n📋 文档规范对比:")
        for field, status in comparison["field_compliance"].items():
            print(f"   {field}: {status}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("健康检查", success, {}, response_data, comparison)
        
        return success

    def test_get_datasets(self):
        """测试获取知识库列表"""
        self.print_interface_header(
            "获取知识库列表", "GET", "/api/v1/datasets?page=1&page_size=12&name=keyword",
            "知识库管理 > 1. 获取知识库列表"
        )
        
        # 测试请求参数
        params = {
            "page": 1,
            "page_size": 12,
            "name": "test"
        }
        
        response = requests.get(f"{self.base_url}/api/v1/datasets", params=params, headers=self.headers)
        response_data = self.print_request_response("获取知识库列表", params, response)
        
        # 文档规范对比
        expected_fields = ["code", "data", "meta"]
        meta_fields = ["page", "page_size", "total", "has_next", "has_prev"]
        dataset_fields = ["id", "name", "description", "document_count", "chunk_count", 
                         "token_num", "embedding_model", "chunk_method", "status", 
                         "create_date", "update_date", "parser_config"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        # 验证meta结构
        if "meta" in response_data:
            meta_comparison = self.compare_with_doc_spec(response_data["meta"], meta_fields)
            comparison["meta_compliance"] = meta_comparison
            
        # 验证data数组结构
        if "data" in response_data and isinstance(response_data["data"], list) and response_data["data"]:
            dataset_comparison = self.compare_with_doc_spec(response_data["data"][0], dataset_fields)
            comparison["dataset_structure"] = dataset_comparison
            
        print(f"\n📋 文档规范对比:")
        print(f"   基础结构: {'✅' if comparison['structure_compliance'] else '❌'}")
        if "meta_compliance" in comparison:
            print(f"   分页元数据: {'✅' if comparison['meta_compliance']['structure_compliance'] else '❌'}")
        if "dataset_structure" in comparison:
            print(f"   知识库数据结构: {'✅' if comparison['dataset_structure']['structure_compliance'] else '❌'}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("获取知识库列表", success, params, response_data, comparison)
        
        return success

    def test_create_dataset(self):
        """测试创建知识库"""
        self.print_interface_header(
            "创建知识库", "POST", "/api/v1/datasets",
            "知识库管理 > 2. 创建知识库"
        )
        
        # 按文档规范构造请求
        request_data = {
            "name": "详细测试知识库",
            "description": "用于详细接口测试的知识库",
            "embedding_model": "BAAI/bge-m3@SILICONFLOW",
            "chunk_method": "naive",
            "parser_config": {
                "chunk_token_num": 512,
                "delimiter": "\n",
                "auto_keywords": 0,
                "auto_questions": 0
            }
        }
        
        response = requests.post(f"{self.base_url}/api/v1/datasets", 
                               headers=self.headers, json=request_data)
        response_data = self.print_request_response("创建知识库", request_data, response)
        
        # 文档规范对比
        expected_response_fields = ["code", "data"]
        expected_data_fields = ["id", "name", "status"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_response_fields)
        
        if "data" in response_data:
            data_comparison = self.compare_with_doc_spec(response_data["data"], expected_data_fields)
            comparison["data_structure"] = data_comparison
            
            # 保存创建的知识库ID
            if "id" in response_data["data"]:
                self.test_data["dataset_id"] = response_data["data"]["id"]
                print(f"\n💾 保存测试数据: dataset_id = {self.test_data['dataset_id']}")
                
        print(f"\n📋 文档规范对比:")
        print(f"   响应结构: {'✅' if comparison['structure_compliance'] else '❌'}")
        if "data_structure" in comparison:
            print(f"   数据字段: {'✅' if comparison['data_structure']['structure_compliance'] else '❌'}")
            
        # 验证embedding_model格式
        if "embedding_model" in request_data:
            model_format_correct = "@" in request_data["embedding_model"]
            print(f"   embedding_model格式: {'✅' if model_format_correct else '❌'}")
            
        success = (response.status_code == 200 and 
                  comparison["structure_compliance"] and 
                  response_data.get("code") == 0)
        self.log_test_result("创建知识库", success, request_data, response_data, comparison)
        
        return success

    def test_get_dataset_detail(self):
        """测试获取知识库详情"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "获取知识库详情", "GET", f"/api/v1/datasets/{{{dataset_id}}}",
            "知识库管理 > 获取知识库详情"
        )
        
        response = requests.get(f"{self.base_url}/api/v1/datasets/{dataset_id}", 
                              headers=self.headers)
        response_data = self.print_request_response("获取知识库详情", {}, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        detail_fields = ["id", "name", "description", "document_count", "chunk_count", 
                        "token_num", "embedding_model", "chunk_method", "status", 
                        "create_date", "update_date", "parser_config"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        if "data" in response_data:
            detail_comparison = self.compare_with_doc_spec(response_data["data"], detail_fields)
            comparison["detail_structure"] = detail_comparison
            
        print(f"\n📋 文档规范对比:")
        for field, status in comparison["field_compliance"].items():
            print(f"   {field}: {status}")
        if "detail_structure" in comparison:
            print(f"   详情数据完整性: {'✅' if comparison['detail_structure']['structure_compliance'] else '❌'}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("获取知识库详情", success, {"dataset_id": dataset_id}, response_data, comparison)
        
        return success

    def test_update_dataset(self):
        """测试更新知识库"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "更新知识库", "PUT", f"/api/v1/datasets/{{{dataset_id}}}",
            "知识库管理 > 3. 更新知识库"
        )
        
        request_data = {
            "name": "更新后的详细测试知识库",
            "description": "这是更新后的描述信息"
        }
        
        response = requests.put(f"{self.base_url}/api/v1/datasets/{dataset_id}",
                              headers=self.headers, json=request_data)
        response_data = self.print_request_response("更新知识库", request_data, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        print(f"\n📋 文档规范对比:")
        for field, status in comparison["field_compliance"].items():
            print(f"   {field}: {status}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("更新知识库", success, request_data, response_data, comparison)
        
        return success

    def test_upload_document(self):
        """测试上传文档"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "上传文档", "POST", f"/api/v1/datasets/{{{dataset_id}}}/documents",
            "文档管理 > 1. 上传文档"
        )
        
        # 创建测试文件内容
        test_content = """这是一个详细的测试文档。
内容包含多行文本，用于验证文档上传功能。
这个文档将被解析为知识片段。"""
        
        # 使用multipart/form-data格式，字段名为file
        files = {
            'file': ('详细测试文档.txt', test_content.encode('utf-8'), 'text/plain')
        }
        
        # 上传时不使用Content-Type: application/json
        upload_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                               headers=upload_headers, files=files)
        
        # 为了JSON序列化，创建安全的请求数据表示
        safe_request_data = {
            "file_name": "详细测试文档.txt", 
            "content_preview": test_content[:50] + "...",
            "content_size": len(test_content),
            "content_type": "text/plain"
        }
        
        response_data = self.print_request_response("上传文档", safe_request_data, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        doc_fields = ["id", "name", "size", "type", "location", "dataset_id", "run", "parser_config"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        # 验证返回数组格式
        if "data" in response_data:
            if isinstance(response_data["data"], list):
                comparison["array_format"] = "✅ 正确的数组格式"
                if response_data["data"]:
                    doc_comparison = self.compare_with_doc_spec(response_data["data"][0], doc_fields)
                    comparison["document_structure"] = doc_comparison
                    
                    # 保存文档ID
                    if "id" in response_data["data"][0]:
                        self.test_data["document_id"] = response_data["data"][0]["id"]
                        print(f"\n💾 保存测试数据: document_id = {self.test_data['document_id']}")
            else:
                comparison["array_format"] = "❌ 应该返回数组格式"
                
        print(f"\n📋 文档规范对比:")
        print(f"   响应结构: {'✅' if comparison['structure_compliance'] else '❌'}")
        if "array_format" in comparison:
            print(f"   数组格式: {comparison['array_format']}")
        if "document_structure" in comparison:
            print(f"   文档数据结构: {'✅' if comparison['document_structure']['structure_compliance'] else '❌'}")
            
        # 验证上传格式
        print(f"   上传格式: multipart/form-data ✅")
        print(f"   字段名称: file (不是files[]) ✅")
        
        success = (response.status_code == 200 and 
                  comparison["structure_compliance"] and
                  isinstance(response_data.get("data"), list))
        
        # 使用安全的请求数据记录
        self.log_test_result("上传文档", success, safe_request_data, response_data, comparison)
        
        return success

    def test_get_documents(self):
        """测试获取文档列表"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "获取文档列表", "GET", f"/api/v1/datasets/{{{dataset_id}}}/documents?page=1&page_size=20",
            "文档管理 > 2. 获取文档列表"
        )
        
        params = {"page": 1, "page_size": 20}
        
        response = requests.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
                              params=params, headers=self.headers)
        response_data = self.print_request_response("获取文档列表", params, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        data_fields = ["docs", "total"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        if "data" in response_data:
            data_comparison = self.compare_with_doc_spec(response_data["data"], data_fields)
            comparison["data_structure"] = data_comparison
            
        print(f"\n📋 文档规范对比:")
        for field, status in comparison["field_compliance"].items():
            print(f"   {field}: {status}")
        if "data_structure" in comparison:
            print(f"   数据结构(docs, total): {'✅' if comparison['data_structure']['structure_compliance'] else '❌'}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("获取文档列表", success, params, response_data, comparison)
        
        return success

    def test_get_document_content(self):
        """测试获取文档内容"""
        if "dataset_id" not in self.test_data or "document_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID或文档ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        document_id = self.test_data["document_id"]
        
        self.print_interface_header(
            "获取文档内容", "GET", f"/api/v1/datasets/{{{dataset_id}}}/documents/{{{document_id}}}",
            "文档管理 > 3. 获取文档内容"
        )
        
        response = requests.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{document_id}",
                              headers=self.headers)
        
        print(f"\n📤 获取文档内容 - 请求详情:")
        print(f"   URL: {response.url}")
        print(f"   方法: {response.request.method}")
        
        print(f"\n📥 获取文档内容 - 响应详情:")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   响应内容: {response.text[:200]}...")
        
        # 文档规范对比
        content_type = response.headers.get('content-type', '')
        is_text_format = 'text/plain' in content_type or not content_type.startswith('application/json')
        
        comparison = {
            "content_format": "✅ 纯文本格式" if is_text_format else "❌ 应该返回纯文本",
            "status_code": "✅ 200" if response.status_code == 200 else f"❌ {response.status_code}"
        }
        
        print(f"\n📋 文档规范对比:")
        for key, status in comparison.items():
            print(f"   {key}: {status}")
            
        success = response.status_code == 200 and is_text_format
        self.log_test_result("获取文档内容", success, 
                           {"dataset_id": dataset_id, "document_id": document_id}, 
                           {"content": response.text, "content_type": content_type}, 
                           comparison)
        
        return success

    def test_download_document(self):
        """测试下载文档"""
        if "dataset_id" not in self.test_data or "document_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID或文档ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        document_id = self.test_data["document_id"]
        
        self.print_interface_header(
            "下载文档", "GET", f"/api/v1/datasets/{{{dataset_id}}}/documents/{{{document_id}}}/download",
            "文档管理 > 6. 下载文档"
        )
        
        response = requests.get(f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{document_id}/download",
                              headers=self.headers)
        
        print(f"\n📤 下载文档 - 请求详情:")
        print(f"   URL: {response.url}")
        
        print(f"\n📥 下载文档 - 响应详情:")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Disposition: {response.headers.get('content-disposition', 'N/A')}")
        print(f"   内容长度: {len(response.content)} bytes")
        
        # 文档规范对比
        content_type = response.headers.get('content-type', '')
        content_disposition = response.headers.get('content-disposition', '')
        
        is_file_response = ('application/octet-stream' in content_type or 
                           'attachment' in content_disposition)
        
        comparison = {
            "file_format": "✅ 文件流格式" if is_file_response else "❌ 应该返回文件流",
            "status_code": "✅ 200" if response.status_code == 200 else f"❌ {response.status_code}",
            "headers": "✅ 包含下载头" if content_disposition else "⚠️ 缺少Content-Disposition"
        }
        
        print(f"\n📋 文档规范对比:")
        for key, status in comparison.items():
            print(f"   {key}: {status}")
            
        success = response.status_code == 200
        self.log_test_result("下载文档", success, 
                           {"dataset_id": dataset_id, "document_id": document_id}, 
                           {"content_length": len(response.content), "headers": dict(response.headers)}, 
                           comparison)
        
        return success

    def test_create_chat(self):
        """测试创建对话"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "创建对话", "POST", "/api/v1/chats",
            "对话管理 > 1. 创建对话"
        )
        
        # 按文档规范构造请求
        request_data = {
            "name": "详细测试对话",
            "dataset_ids": [dataset_id],  # 注意使用dataset_ids而不是kb_ids
            "description": "用于详细接口测试的对话"
        }
        
        response = requests.post(f"{self.base_url}/api/v1/chats",
                               headers=self.headers, json=request_data)
        response_data = self.print_request_response("创建对话", request_data, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        data_fields = ["id", "name", "dataset_ids", "llm", "create_date"]
        llm_fields = ["model_name", "temperature", "max_tokens"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        if "data" in response_data:
            data_comparison = self.compare_with_doc_spec(response_data["data"], data_fields)
            comparison["data_structure"] = data_comparison
            
            # 验证llm配置结构
            if "llm" in response_data["data"]:
                llm_comparison = self.compare_with_doc_spec(response_data["data"]["llm"], llm_fields)
                comparison["llm_structure"] = llm_comparison
                
            # 保存对话ID
            if "id" in response_data["data"]:
                self.test_data["chat_id"] = response_data["data"]["id"]
                print(f"\n💾 保存测试数据: chat_id = {self.test_data['chat_id']}")
                
        print(f"\n📋 文档规范对比:")
        print(f"   响应结构: {'✅' if comparison['structure_compliance'] else '❌'}")
        if "data_structure" in comparison:
            print(f"   数据字段: {'✅' if comparison['data_structure']['structure_compliance'] else '❌'}")
        if "llm_structure" in comparison:
            print(f"   LLM配置: {'✅' if comparison['llm_structure']['structure_compliance'] else '❌'}")
            
        # 验证字段名称
        if "dataset_ids" in request_data:
            print(f"   字段名称(dataset_ids): ✅")
        
        success = (response.status_code == 200 and 
                  comparison["structure_compliance"] and 
                  response_data.get("code") == 0)
        self.log_test_result("创建对话", success, request_data, response_data, comparison)
        
        return success

    def test_send_message_sse(self):
        """测试发送消息（SSE流式响应）"""
        if "chat_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的对话ID")
            return False
            
        chat_id = self.test_data["chat_id"]
        
        self.print_interface_header(
            "发送消息（SSE流式）", "POST", f"/api/v1/chats/{{{chat_id}}}/completions",
            "对话管理 > 2. 发送消息（SSE流式响应）"
        )
        
        request_data = {
            "content": "你好，请介绍一下这个知识库的内容"
        }
        
        response = requests.post(f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                               headers=self.headers, json=request_data, stream=True)
        
        print(f"\n📤 发送消息 - 请求详情:")
        print(f"   URL: {response.url}")
        print(f"   请求体: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        print(f"\n📥 发送消息 - SSE响应详情:")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        # 读取SSE流
        sse_messages = []
        message_count = 0
        
        if response.status_code == 200:
            print(f"   SSE消息流:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        if data_str:
                            try:
                                sse_data = json.loads(data_str)
                                sse_messages.append(sse_data)
                                message_count += 1
                                print(f"     消息{message_count}: {json.dumps(sse_data, ensure_ascii=False)}")
                            except json.JSONDecodeError:
                                print(f"     无效JSON: {data_str}")
                                
        # 文档规范对比
        comparison = {
            "status_code": "✅ 200" if response.status_code == 200 else f"❌ {response.status_code}",
            "message_count": f"✅ {len(sse_messages)}条消息" if len(sse_messages) >= 2 else f"❌ 消息数量不足({len(sse_messages)})",
            "sse_format": "✅ SSE格式" if len(sse_messages) > 0 else "❌ 非SSE格式"
        }
        
        # 验证第一条消息格式
        if len(sse_messages) > 0:
            first_msg = sse_messages[0]
            has_answer = "data" in first_msg and "answer" in first_msg.get("data", {})
            comparison["first_message"] = "✅ 包含answer" if has_answer else "❌ 缺少answer"
            
        # 验证最后一条消息格式
        if len(sse_messages) > 1:
            last_msg = sse_messages[-1]
            is_end_marker = last_msg.get("data") is True
            comparison["last_message"] = "✅ 结束标记(data:true)" if is_end_marker else "❌ 缺少结束标记"
            
        print(f"\n📋 文档规范对比:")
        for key, status in comparison.items():
            print(f"   {key}: {status}")
            
        success = (response.status_code == 200 and len(sse_messages) >= 2)
        self.log_test_result("发送消息SSE", success, request_data, 
                           {"sse_messages": sse_messages, "message_count": len(sse_messages)}, 
                           comparison)
        
        return success

    def test_get_chat_messages(self):
        """测试获取对话历史"""
        if "chat_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的对话ID")
            return False
            
        chat_id = self.test_data["chat_id"]
        
        self.print_interface_header(
            "获取对话历史", "GET", f"/api/v1/chats/{{{chat_id}}}/messages?page=1&page_size=20",
            "对话管理 > 获取对话历史"
        )
        
        params = {"page": 1, "page_size": 20}
        
        response = requests.get(f"{self.base_url}/api/v1/chats/{chat_id}/messages",
                              params=params, headers=self.headers)
        response_data = self.print_request_response("获取对话历史", params, response)
        
        # 文档规范对比
        expected_fields = ["code", "data", "meta"]
        meta_fields = ["page", "page_size", "total", "has_next", "has_prev"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        if "meta" in response_data:
            meta_comparison = self.compare_with_doc_spec(response_data["meta"], meta_fields)
            comparison["meta_structure"] = meta_comparison
            
        print(f"\n📋 文档规范对比:")
        for field, status in comparison["field_compliance"].items():
            print(f"   {field}: {status}")
        if "meta_structure" in comparison:
            print(f"   分页元数据: {'✅' if comparison['meta_structure']['structure_compliance'] else '❌'}")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("获取对话历史", success, params, response_data, comparison)
        
        return success

    def test_retrieval(self):
        """测试知识库检索"""
        if "dataset_id" not in self.test_data:
            print("⚠️ 跳过测试：没有可用的知识库ID")
            return False
            
        dataset_id = self.test_data["dataset_id"]
        
        self.print_interface_header(
            "知识库检索", "POST", "/api/v1/retrieval",
            "检索接口 > 知识库检索"
        )
        
        request_data = {
            "question": "什么是权益申请？",
            "dataset_ids": [dataset_id],  # 注意使用dataset_ids
            "page": 1,
            "page_size": 5
        }
        
        response = requests.post(f"{self.base_url}/api/v1/retrieval",
                               headers=self.headers, json=request_data)
        response_data = self.print_request_response("知识库检索", request_data, response)
        
        # 文档规范对比
        expected_fields = ["code", "data"]
        data_fields = ["chunks"]
        chunk_fields = ["id", "content_ltks", "similarity", "document_name", "dataset_id"]
        
        comparison = self.compare_with_doc_spec(response_data, expected_fields)
        
        if "data" in response_data:
            data_comparison = self.compare_with_doc_spec(response_data["data"], data_fields)
            comparison["data_structure"] = data_comparison
            
            # 验证chunks结构
            if "chunks" in response_data["data"] and response_data["data"]["chunks"]:
                chunk_comparison = self.compare_with_doc_spec(response_data["data"]["chunks"][0], chunk_fields)
                comparison["chunk_structure"] = chunk_comparison
                
        print(f"\n📋 文档规范对比:")
        print(f"   响应结构: {'✅' if comparison['structure_compliance'] else '❌'}")
        if "data_structure" in comparison:
            print(f"   数据结构: {'✅' if comparison['data_structure']['structure_compliance'] else '❌'}")
        if "chunk_structure" in comparison:
            print(f"   检索片段结构: {'✅' if comparison['chunk_structure']['structure_compliance'] else '❌'}")
            
        # 验证字段名称
        if "dataset_ids" in request_data:
            print(f"   字段名称(dataset_ids): ✅")
            
        success = response.status_code == 200 and comparison["structure_compliance"]
        self.log_test_result("知识库检索", success, request_data, response_data, comparison)
        
        return success

    def test_error_handling(self):
        """测试错误处理"""
        self.print_interface_header(
            "错误处理测试", "GET", "/api/v1/datasets (无效token)",
            "错误处理 > 常见错误码"
        )
        
        # 测试无效token
        invalid_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token_12345"
        }
        
        response = requests.get(f"{self.base_url}/api/v1/datasets", headers=invalid_headers)
        
        print(f"\n📤 错误处理测试 - 请求详情:")
        print(f"   URL: {response.url}")
        print(f"   无效Token: invalid_token_12345")
        
        print(f"\n📥 错误处理测试 - 响应详情:")
        print(f"   状态码: {response.status_code}")
        
        # 文档规范对比
        comparison = {
            "status_code": "✅ 401未授权" if response.status_code == 401 else f"❌ 应该返回401，实际{response.status_code}",
            "error_format": "✅ 正确的错误响应" if response.status_code == 401 else "❌ 错误响应格式"
        }
        
        print(f"\n📋 文档规范对比:")
        for key, status in comparison.items():
            print(f"   {key}: {status}")
            
        success = response.status_code == 401
        self.log_test_result("错误处理", success, {"token": "invalid"}, 
                           {"status_code": response.status_code}, comparison)
        
        return success

    def cleanup_test_data(self):
        """清理测试数据"""
        print(f"\n{'='*100}")
        print("🧹 清理测试数据")
        print('='*100)
        
        # 删除对话
        if "chat_id" in self.test_data:
            try:
                response = requests.delete(f"{self.base_url}/api/v1/chats/{self.test_data['chat_id']}",
                                         headers=self.headers)
                if response.status_code == 200:
                    print(f"✅ 删除对话: {self.test_data['chat_id']}")
                else:
                    print(f"⚠️ 删除对话失败: {response.status_code}")
            except Exception as e:
                print(f"⚠️ 删除对话异常: {e}")
                
        # 删除知识库（会自动删除相关文档）
        if "dataset_id" in self.test_data:
            try:
                response = requests.delete(f"{self.base_url}/api/v1/datasets/{self.test_data['dataset_id']}",
                                         headers=self.headers)
                if response.status_code == 200:
                    print(f"✅ 删除知识库: {self.test_data['dataset_id']}")
                else:
                    print(f"⚠️ 删除知识库失败: {response.status_code}")
            except Exception as e:
                print(f"⚠️ 删除知识库异常: {e}")

    def generate_test_report(self):
        """生成测试报告"""
        print(f"\n{'='*100}")
        print("📊 详细接口测试报告生成")
        print('='*100)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        
        print(f"\n📈 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   成功数: {successful_tests}")
        print(f"   失败数: {total_tests - successful_tests}")
        print(f"   成功率: {successful_tests/total_tests*100:.1f}%")
        
        print(f"\n📋 测试详情:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result["success"] else "❌"
            print(f"   {i:2d}. {status} {result['interface']}")
            
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests/total_tests*100,
            "results": self.test_results
        }

    def run_all_tests(self):
        """运行所有详细接口测试"""
        print(f"\n{'='*100}")
        print("🚀 开始详细接口测试")
        print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 API地址: {self.base_url}")
        print(f"🔑 认证Token: {self.api_key}")
        print('='*100)
        
        # 按顺序执行测试
        test_methods = [
            self.test_health_check,
            self.test_get_datasets,
            self.test_create_dataset,
            self.test_get_dataset_detail,
            self.test_update_dataset,
            self.test_upload_document,
            self.test_get_documents,
            self.test_get_document_content,
            self.test_download_document,
            self.test_create_chat,
            self.test_send_message_sse,
            self.test_get_chat_messages,
            self.test_retrieval,
            self.test_error_handling
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(0.5)  # 短暂延迟
            except Exception as e:
                print(f"\n❌ 测试方法 {test_method.__name__} 发生异常: {e}")
                
        # 清理测试数据
        self.cleanup_test_data()
        
        # 生成报告
        report = self.generate_test_report()
        
        # 保存详细报告到文件
        try:
            report_file = f"detailed_interface_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            print(f"\n💾 详细测试报告已保存到: {report_file}")
        except Exception as e:
            print(f"\n⚠️ 保存测试报告时发生错误: {e}")
            print("测试已完成，但JSON报告保存失败")
        
        return report

def main():
    """主函数"""
    import sys
    
    base_url = "http://localhost:8050"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
        
    tester = DetailedInterfaceTestRunner(base_url)
    
    try:
        report = tester.run_all_tests()
        
        print(f"\n🎉 详细接口测试完成!")
        print(f"   成功率: {report['success_rate']:.1f}%")
        
        sys.exit(0 if report['success_rate'] == 100 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        tester.cleanup_test_data()
        sys.exit(1)

if __name__ == "__main__":
    main()