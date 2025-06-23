"""
测试已实现的API接口
根据知识库管理系统接口清单进行测试
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


class APITester:
    def __init__(self):
        self.results = []
        self.kb_id = None
        self.doc_id = None
        
    def add_result(self, api_name, status, message=""):
        result = {
            "api": api_name,
            "status": "✓" if status else "✗",
            "message": message
        }
        self.results.append(result)
        print(f"{result['status']} {api_name}: {message}")
    
    def test_get_datasets(self):
        """测试获取知识库列表"""
        print("\n1. 测试获取知识库列表 (GET /api/v1/datasets)")
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/datasets",
                headers=headers,
                params={"page": 1, "page_size": 12}
            )
            
            if response.status_code == 200 and response.json().get('code') == 0:
                data = response.json()['data']
                self.add_result("获取知识库列表", True, f"找到 {len(data)} 个知识库")
                
                # 保存一个知识库ID用于后续测试
                if data:
                    self.kb_id = data[0]['id']
                    print(f"   使用知识库: {data[0]['name']} (ID: {self.kb_id})")
                
                return True
            else:
                self.add_result("获取知识库列表", False, f"状态码: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_result("获取知识库列表", False, str(e))
            return False
    
    def test_create_dataset(self):
        """测试创建知识库"""
        print("\n2. 测试创建知识库 (POST /api/v1/datasets)")
        try:
            data = {
                "name": f"API测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "description": "通过API创建的测试知识库",
                "language": "Chinese",
                "embedding_model": "BAAI/bge-m3",
                "chunk_method": "naive"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.kb_id = result['data']['id']
                    self.add_result("创建知识库", True, f"ID: {self.kb_id}")
                    return True
                else:
                    self.add_result("创建知识库", False, result.get('message', '未知错误'))
            else:
                self.add_result("创建知识库", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("创建知识库", False, str(e))
        
        return False
    
    def test_update_dataset(self):
        """测试更新知识库"""
        if not self.kb_id:
            self.add_result("更新知识库", False, "需要先创建或选择知识库")
            return False
            
        print(f"\n3. 测试更新知识库 (PUT /api/v1/datasets/{self.kb_id})")
        try:
            data = {
                "description": f"更新于 {datetime.now()}"
            }
            
            response = requests.put(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200 and response.json().get('code') == 0:
                self.add_result("更新知识库", True, "描述已更新")
                return True
            else:
                self.add_result("更新知识库", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("更新知识库", False, str(e))
        
        return False
    
    def test_upload_document(self):
        """测试上传文档"""
        if not self.kb_id:
            self.add_result("上传文档", False, "需要先创建或选择知识库")
            return False
            
        print(f"\n4. 测试上传文档 (POST /api/v1/datasets/{self.kb_id}/documents)")
        
        # 创建测试文件
        test_file = Path("test_upload.txt")
        test_content = f"""API测试文档
创建时间: {datetime.now()}

这是通过API上传的测试文档。
用于验证文档上传功能是否正常工作。

测试内容包括：
1. 文档上传
2. 文档解析
3. 文档检索
"""
        test_file.write_text(test_content, encoding='utf-8')
        
        try:
            files = {
                'file': ('test_upload.txt', open(test_file, 'rb'), 'text/plain')
            }
            
            # 上传时不需要Content-Type header
            upload_headers = {
                'Authorization': headers['Authorization']
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents",
                headers=upload_headers,
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    # 响应是数组格式
                    if isinstance(result['data'], list) and len(result['data']) > 0:
                        self.doc_id = result['data'][0]['id']
                        self.add_result("上传文档", True, f"文档ID: {self.doc_id}")
                        return True
                    else:
                        self.add_result("上传文档", False, "响应数据格式错误")
                        return False
                else:
                    self.add_result("上传文档", False, result.get('message', '未知错误'))
            else:
                self.add_result("上传文档", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("上传文档", False, str(e))
        finally:
            if test_file.exists():
                test_file.unlink()
        
        return False
    
    def test_list_documents(self):
        """测试获取文档列表"""
        if not self.kb_id:
            self.add_result("获取文档列表", False, "需要先创建或选择知识库")
            return False
            
        print(f"\n5. 测试获取文档列表 (GET /api/v1/datasets/{self.kb_id}/documents)")
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents",
                headers=headers,
                params={"page": 1, "page_size": 20}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    docs = result.get('data')
                    if isinstance(docs, dict) and 'docs' in docs:
                        doc_count = len(docs['docs'])
                        self.add_result("获取文档列表", True, f"找到 {doc_count} 个文档")
                    else:
                        self.add_result("获取文档列表", True, f"响应格式: {type(docs)}")
                    return True
            
            self.add_result("获取文档列表", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("获取文档列表", False, str(e))
        
        return False
    
    def test_parse_document(self):
        """测试触发文档解析"""
        if not self.kb_id or not self.doc_id:
            self.add_result("触发文档解析", False, "需要先上传文档")
            return False
            
        print(f"\n6. 测试触发文档解析 (POST /api/v1/datasets/{self.kb_id}/documents/{self.doc_id}/run)")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents/{self.doc_id}/run",
                headers=headers
            )
            
            if response.status_code == 200 and response.json().get('code') == 0:
                self.add_result("触发文档解析", True, "解析已触发")
                return True
            else:
                self.add_result("触发文档解析", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("触发文档解析", False, str(e))
        
        return False
    
    def test_retrieval(self):
        """测试知识库检索"""
        if not self.kb_id:
            self.add_result("知识库检索", False, "需要先创建或选择知识库")
            return False
            
        print(f"\n7. 测试知识库检索 (POST /api/v1/retrieval)")
        try:
            data = {
                "question": "测试文档",
                "dataset_ids": [self.kb_id],
                "page": 1,
                "page_size": 10
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/retrieval",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    chunks = result.get('data', {}).get('chunks', [])
                    self.add_result("知识库检索", True, f"返回 {len(chunks)} 个结果")
                    return True
                else:
                    self.add_result("知识库检索", False, result.get('message', '未知错误'))
            else:
                self.add_result("知识库检索", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("知识库检索", False, str(e))
        
        return False
    
    def test_chat(self):
        """测试对话功能"""
        if not self.kb_id:
            self.add_result("对话功能", False, "需要先创建或选择知识库")
            return False
            
        print(f"\n8. 测试对话功能 (POST /api/v1/chats)")
        try:
            # 创建对话
            chat_data = {
                "name": f"测试对话_{datetime.now().strftime('%H%M%S')}",
                "dataset_ids": [self.kb_id]
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/chats",
                headers=headers,
                json=chat_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    chat_id = result['data']['id']
                    self.add_result("创建对话", True, f"对话ID: {chat_id}")
                    
                    # 发送消息
                    msg_data = {
                        "content": "请介绍一下测试文档的内容"
                    }
                    
                    msg_response = requests.post(
                        f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
                        headers=headers,
                        json=msg_data
                    )
                    
                    if msg_response.status_code == 200:
                        msg_result = msg_response.json()
                        if msg_result.get('code') == 0:
                            answer = msg_result.get('data', {}).get('answer', '')
                            self.add_result("发送消息", True, f"收到回复 ({len(answer)} 字符)")
                            return True
                    
                    self.add_result("发送消息", False, f"状态码: {msg_response.status_code}")
                else:
                    self.add_result("创建对话", False, result.get('message', '未知错误'))
            else:
                self.add_result("创建对话", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("对话功能", False, str(e))
        
        return False
    
    def test_delete_dataset(self):
        """测试删除知识库"""
        if not self.kb_id:
            self.add_result("删除知识库", False, "没有可删除的知识库")
            return False
            
        print(f"\n9. 测试删除知识库 (DELETE /api/v1/datasets/{self.kb_id})")
        try:
            response = requests.delete(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}",
                headers=headers
            )
            
            if response.status_code == 200 and response.json().get('code') == 0:
                self.add_result("删除知识库", True, "知识库已删除")
                self.kb_id = None
                return True
            else:
                self.add_result("删除知识库", False, f"状态码: {response.status_code}")
                
        except Exception as e:
            self.add_result("删除知识库", False, str(e))
        
        return False
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        
        passed = sum(1 for r in self.results if r['status'] == "✓")
        total = len(self.results)
        
        print(f"\n总计: {total} 个测试")
        print(f"通过: {passed} 个")
        print(f"失败: {total - passed} 个")
        
        print("\n详细结果:")
        for result in self.results:
            print(f"{result['status']} {result['api']}: {result['message']}")
        
        print("\n" + "="*60)


def main():
    """运行测试"""
    print(f"\n{'='*60}")
    print(f"知识库管理系统 API 接口测试")
    print(f"API地址: {BASE_URL}")
    print(f"测试时间: {datetime.now()}")
    print(f"{'='*60}")
    
    tester = APITester()
    
    # 执行测试
    tester.test_get_datasets()
    
    # 如果没有找到知识库，创建一个
    if not tester.kb_id:
        tester.test_create_dataset()
    
    if tester.kb_id:
        tester.test_update_dataset()
        tester.test_upload_document()
        tester.test_list_documents()
        
        if tester.doc_id:
            tester.test_parse_document()
            # 等待解析
            print("   等待文档解析...")
            time.sleep(3)
        
        tester.test_retrieval()
        tester.test_chat()
        
        # 清理测试数据
        # tester.test_delete_dataset()
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    main()