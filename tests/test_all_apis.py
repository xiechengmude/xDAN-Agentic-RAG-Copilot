#!/usr/bin/env python3
"""
API接口自动化测试脚本
自动从Swagger文档爬取所有接口并进行测试
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class APITester:
    """API接口测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8025"):
        self.base_url = base_url
        self.api_key = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.test_results = []
        self.openapi_spec = None
        
    def fetch_openapi_spec(self) -> Dict[str, Any]:
        """获取OpenAPI规范文档"""
        try:
            response = requests.get(f"{self.base_url}/openapi.json")
            response.raise_for_status()
            self.openapi_spec = response.json()
            return self.openapi_spec
        except Exception as e:
            print(f"❌ 无法获取OpenAPI文档: {e}")
            sys.exit(1)
            
    def generate_test_data(self, endpoint: str, method: str, operation: Dict) -> Dict[str, Any]:
        """根据接口定义生成测试数据"""
        test_data = {
            "path_params": {},
            "query_params": {},
            "body": None,
            "files": None
        }
        
        # 处理参数
        parameters = operation.get("parameters", [])
        for param in parameters:
            param_name = param.get("name")
            param_in = param.get("in")
            param_required = param.get("required", False)
            param_schema = param.get("schema", {})
            
            # 生成测试值
            test_value = self._generate_test_value(param_schema, param_name)
            
            if param_in == "path":
                test_data["path_params"][param_name] = test_value
            elif param_in == "query":
                if param_required or param_name in ["keyword", "query", "kb_id"]:
                    test_data["query_params"][param_name] = test_value
                    
        # 处理请求体
        request_body = operation.get("requestBody", {})
        if request_body:
            content = request_body.get("content", {})
            
            # 处理JSON请求体
            if "application/json" in content:
                schema = content["application/json"].get("schema", {})
                test_data["body"] = self._generate_body_data(schema, endpoint)
            
            # 处理文件上传
            elif "multipart/form-data" in content:
                test_data["files"] = self._generate_file_data(content["multipart/form-data"])
                
        return test_data
    
    def _generate_test_value(self, schema: Dict, param_name: str) -> Any:
        """根据schema生成测试值"""
        param_type = schema.get("type", "string")
        
        # 特殊参数处理
        special_values = {
            "kb_id": "kb_1234567890",
            "doc_id": "doc_test_123",
            "conversation_id": "conv_test_123",
            "message_id": "msg_test_123",
            "keyword": "测试关键词",
            "query": "如何使用RAG系统？",
            "question": "什么是知识库？",
            "page": 1,
            "page_size": 10,
            "limit": 10,
            "top_k": 5
        }
        
        if param_name in special_values:
            return special_values[param_name]
        
        # 根据类型生成默认值
        if param_type == "string":
            return f"test_{param_name}"
        elif param_type == "integer":
            return 1
        elif param_type == "number":
            return 1.0
        elif param_type == "boolean":
            return True
        elif param_type == "array":
            return []
        else:
            return None
    
    def _generate_body_data(self, schema: Dict, endpoint: str) -> Dict:
        """生成请求体数据"""
        # 根据不同的端点生成特定的测试数据
        endpoint_test_data = {
            "/api/v1/knowledge-bases": {
                "name": f"测试知识库_{int(time.time())}",
                "description": "自动化测试创建的知识库",
                "embedding_model": "text-embedding-ada-002",
                "chunk_size": 500
            },
            "/api/v1/documents": {
                "kb_id": "kb_1234567890",
                "file_path": "/test/document.pdf",
                "parser_method": "default"
            },
            "/api/v1/search": {
                "query": "如何使用RAG系统进行知识检索？",
                "kb_ids": ["kb_1234567890"],
                "top_k": 5,
                "similarity_threshold": 0.7
            },
            "/api/v1/chat": {
                "question": "什么是RAG系统？",
                "kb_ids": ["kb_1234567890"],
                "conversation_id": "conv_test_123",
                "stream": False
            },
            "/api/v1/conversations": {
                "name": "测试对话",
                "kb_id": "kb_1234567890"
            }
        }
        
        # 查找匹配的端点
        for pattern, data in endpoint_test_data.items():
            if pattern in endpoint:
                return data
                
        # 如果没有特定数据，生成通用数据
        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            result = {}
            required = schema.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                if prop_name in required:
                    result[prop_name] = self._generate_test_value(prop_schema, prop_name)
                    
            return result
        
        return {}
    
    def _generate_file_data(self, schema: Dict) -> Dict:
        """生成文件上传数据"""
        # 创建一个测试文件
        test_content = "这是一个测试文件内容。\n用于API接口测试。"
        return {
            "file": ("test_document.txt", test_content, "text/plain")
        }
    
    def test_endpoint(self, path: str, method: str, operation: Dict) -> Dict[str, Any]:
        """测试单个端点"""
        result = {
            "endpoint": f"{method.upper()} {path}",
            "description": operation.get("summary", ""),
            "status": "pending",
            "response_code": None,
            "response_time": None,
            "error": None,
            "response_data": None
        }
        
        try:
            # 生成测试数据
            test_data = self.generate_test_data(path, method, operation)
            
            # 替换路径参数
            test_path = path
            for param_name, param_value in test_data["path_params"].items():
                test_path = test_path.replace(f"{{{param_name}}}", str(param_value))
            
            # 构建完整URL
            url = urljoin(self.base_url, test_path)
            
            # 准备请求
            kwargs = {
                "headers": self.headers.copy(),
                "timeout": 10
            }
            
            if test_data["query_params"]:
                kwargs["params"] = test_data["query_params"]
                
            if test_data["body"] is not None:
                kwargs["json"] = test_data["body"]
                
            if test_data["files"]:
                kwargs["files"] = test_data["files"]
                # 文件上传时移除Content-Type
                kwargs["headers"].pop("Content-Type", None)
            
            # 发送请求
            start_time = time.time()
            response = requests.request(method, url, **kwargs)
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 记录结果
            result["response_code"] = response.status_code
            result["response_time"] = f"{response_time:.2f}ms"
            
            # 尝试解析JSON响应
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text[:200]  # 只保存前200字符
            
            # 判断测试结果
            if response.status_code < 400:
                result["status"] = "success"
            else:
                result["status"] = "failed"
                result["error"] = f"HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            result["status"] = "failed"
            result["error"] = "请求超时"
        except requests.exceptions.ConnectionError:
            result["status"] = "failed"
            result["error"] = "连接失败"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            
        return result
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """运行所有接口测试"""
        print("🚀 开始API接口测试...")
        print(f"目标服务器: {self.base_url}")
        print("=" * 60)
        
        # 获取OpenAPI文档
        print("📋 获取API文档...")
        self.fetch_openapi_spec()
        
        paths = self.openapi_spec.get("paths", {})
        total_endpoints = sum(len(methods) for methods in paths.values() if isinstance(methods, dict))
        print(f"✅ 发现 {total_endpoints} 个接口端点\n")
        
        # 测试每个端点
        tested = 0
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if method not in ["get", "post", "put", "delete", "patch"]:
                    continue
                    
                tested += 1
                print(f"[{tested}/{total_endpoints}] 测试 {method.upper()} {path}...", end=" ")
                
                result = self.test_endpoint(path, method, operation)
                self.test_results.append(result)
                
                # 打印简单结果
                if result["status"] == "success":
                    print(f"✅ 成功 ({result['response_time']})")
                else:
                    print(f"❌ 失败 ({result['error']})")
                    
                # 避免请求过快
                time.sleep(0.5)
        
        return self.test_results
    
    def generate_report(self, output_file: str = None):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        # 统计结果
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r["status"] == "success")
        failed = sum(1 for r in self.test_results if r["status"] == "failed")
        
        print(f"总接口数: {total}")
        print(f"✅ 成功: {success}")
        print(f"❌ 失败: {failed}")
        print(f"成功率: {(success/total*100):.1f}%")
        print()
        
        # 详细结果
        if failed > 0:
            print("失败的接口:")
            for result in self.test_results:
                if result["status"] == "failed":
                    print(f"  - {result['endpoint']}: {result['error']}")
            print()
        
        # 响应时间统计
        response_times = [
            float(r["response_time"].rstrip("ms")) 
            for r in self.test_results 
            if r["response_time"] and r["status"] == "success"
        ]
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print("响应时间统计:")
            print(f"  平均: {avg_time:.2f}ms")
            print(f"  最快: {min_time:.2f}ms")
            print(f"  最慢: {max_time:.2f}ms")
        
        # 保存详细报告
        if output_file or True:  # 默认保存
            output_file = output_file or f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_data = {
                "test_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "summary": {
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "success_rate": f"{(success/total*100):.1f}%"
                },
                "results": self.test_results
            }
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
                
            print(f"\n📄 详细报告已保存到: {output_file}")
            
        return report_data


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API接口自动化测试工具")
    parser.add_argument(
        "--base-url", 
        default="http://localhost:8025",
        help="API服务器地址 (默认: http://localhost:8025)"
    )
    parser.add_argument(
        "--output", 
        help="测试报告输出文件名"
    )
    
    args = parser.parse_args()
    
    # 创建测试器并运行测试
    tester = APITester(base_url=args.base_url)
    
    try:
        tester.run_all_tests()
        tester.generate_report(args.output)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        if tester.test_results:
            tester.generate_report(args.output)
    except Exception as e:
        print(f"\n\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()