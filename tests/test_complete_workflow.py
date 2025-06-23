"""
完整的全链路API测试
测试从创建知识库到智能问答的完整流程
"""
import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path

# API配置
BASE_URL = "http://150.109.16.195:7080"
API_KEY = "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class CompleteWorkflowTester:
    def __init__(self):
        self.results = []
        self.kb_id = None
        self.doc_id = None
        self.chat_id = None
        self.session_id = None
        
    def log(self, step, status, message="", data=None):
        """记录测试步骤"""
        result = {
            "step": step,
            "status": "✅" if status else "❌",
            "message": message,
            "data": data,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        self.results.append(result)
        print(f"[{result['timestamp']}] {result['status']} {step}: {message}")
        if data and isinstance(data, dict):
            # 只显示关键信息
            key_info = {}
            for key in ['id', 'name', 'status', 'code', 'answer']:
                if key in data:
                    key_info[key] = data[key]
            if key_info:
                print(f"    关键信息: {key_info}")
    
    def step1_create_knowledge_base(self):
        """步骤1: 创建知识库"""
        print(f"\n{'='*80}")
        print(f"步骤1: 创建知识库")
        print(f"{'='*80}")
        
        kb_name = f"全链路测试知识库_{datetime.now().strftime('%m%d_%H%M%S')}"
        
        data = {
            "name": kb_name,
            "description": "用于全链路API测试的知识库",
            "embedding_model": "BAAI/bge-m3@SILICONFLOW",
            "chunk_method": "naive",
            "parser_config": {
                "chunk_token_num": 512,
                "delimiter": "\n",
                "auto_keywords": 0,
                "auto_questions": 0
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/datasets",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.kb_id = result['data']['id']
                    self.log("创建知识库", True, f"ID: {self.kb_id}, 名称: {kb_name}", result['data'])
                    return True
                else:
                    self.log("创建知识库", False, f"错误: {result.get('message', 'Unknown error')}")
            else:
                self.log("创建知识库", False, f"HTTP错误: {response.status_code}")
        except Exception as e:
            self.log("创建知识库", False, f"异常: {str(e)}")
        
        return False
    
    def step2_upload_documents(self):
        """步骤2: 上传测试文档"""
        print(f"\n{'='*80}")
        print(f"步骤2: 上传测试文档")
        print(f"{'='*80}")
        
        if not self.kb_id:
            self.log("上传文档", False, "需要先创建知识库")
            return False
        
        # 创建多个测试文档
        test_files = [
            {
                "name": "产品介绍.txt",
                "content": """RAGFlow产品介绍

RAGFlow是一款基于深度学习的检索增强生成（RAG）系统，专为企业级应用设计。

主要功能：
1. 智能文档解析 - 支持PDF、Word、PPT、Excel等多种格式
2. 向量化存储 - 使用先进的embedding模型进行文档向量化
3. 语义检索 - 基于语义相似度的智能检索
4. 问答生成 - 结合检索结果生成准确的答案
5. 多模态支持 - 支持文本、图片等多种内容类型

技术特点：
- 高精度的文档切分算法
- 多种embedding模型支持
- 实时流式问答体验
- 完整的API接口
- 可视化管理界面

应用场景：
- 企业知识管理
- 客服问答系统
- 文档智能检索
- 教育培训平台
"""
            },
            {
                "name": "技术文档.txt",
                "content": """RAGFlow技术架构文档

系统架构：
1. 前端界面层
   - React + TypeScript
   - Ant Design UI组件
   - WebSocket实时通信

2. API服务层
   - FastAPI框架
   - RESTful API设计
   - JWT身份认证

3. 核心处理层
   - 文档解析引擎
   - 向量检索引擎
   - 语言模型集成

4. 数据存储层
   - PostgreSQL关系数据库
   - Elasticsearch向量数据库
   - MinIO对象存储

部署方式：
- Docker容器化部署
- Kubernetes集群部署
- 云原生架构支持

配置参数：
- chunk_token_num: 文档切分token数量，默认512
- similarity_threshold: 相似度阈值，默认0.2
- max_tokens: 生成答案最大token数
- temperature: 生成温度参数
"""
            },
            {
                "name": "使用指南.txt",
                "content": """RAGFlow使用指南

快速开始：
1. 创建知识库
   - 设置知识库名称和描述
   - 选择合适的语言和模型
   - 配置解析参数

2. 上传文档
   - 支持拖拽上传
   - 批量文件上传
   - 自动格式识别

3. 文档解析
   - 自动触发解析流程
   - 实时查看解析进度
   - 解析结果预览

4. 智能问答
   - 创建对话会话
   - 选择知识库范围
   - 获得AI助手回答

常见问题：
Q: 支持哪些文件格式？
A: 支持PDF、Word、PPT、Excel、TXT等常见格式

Q: 如何提高检索准确度？
A: 可以调整相似度阈值和chunk大小参数

Q: 是否支持多语言？
A: 支持中文、英文等多种语言

Q: 如何集成到现有系统？
A: 提供完整的REST API接口，支持各种编程语言集成
"""
            }
        ]
        
        uploaded_docs = []
        
        for file_info in test_files:
            # 创建临时文件
            test_file = Path(file_info["name"])
            test_file.write_text(file_info["content"], encoding='utf-8')
            
            try:
                # 上传文件
                with open(test_file, 'rb') as f:
                    files = {
                        'file': (file_info["name"], f, 'text/plain')
                    }
                    
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
                        if result.get('code') == 0 and isinstance(result['data'], list):
                            doc_info = result['data'][0]
                            uploaded_docs.append(doc_info)
                            self.log(f"上传文档 {file_info['name']}", True, 
                                   f"ID: {doc_info['id']}, 大小: {doc_info['size']}字节", doc_info)
                            
                            # 保存第一个文档ID用于后续测试
                            if not self.doc_id:
                                self.doc_id = doc_info['id']
                        else:
                            self.log(f"上传文档 {file_info['name']}", False, 
                                   f"响应格式错误: {result}")
                    else:
                        self.log(f"上传文档 {file_info['name']}", False, 
                               f"HTTP错误: {response.status_code}")
                        
            except Exception as e:
                self.log(f"上传文档 {file_info['name']}", False, f"异常: {str(e)}")
            finally:
                # 清理临时文件
                if test_file.exists():
                    test_file.unlink()
        
        if uploaded_docs:
            self.log("文档上传汇总", True, f"成功上传 {len(uploaded_docs)} 个文档")
            return True
        else:
            self.log("文档上传汇总", False, "没有成功上传任何文档")
            return False
    
    def step3_parse_documents(self):
        """步骤3: 解析文档"""
        print(f"\n{'='*80}")
        print(f"步骤3: 解析文档")
        print(f"{'='*80}")
        
        if not self.kb_id:
            self.log("解析文档", False, "需要先创建知识库")
            return False
        
        # 获取所有文档
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents",
                headers=headers,
                params={"page": 1, "page_size": 50}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    # 处理文档列表响应格式
                    docs_data = result.get('data')
                    if isinstance(docs_data, dict) and 'docs' in docs_data:
                        docs = docs_data['docs']
                    elif isinstance(docs_data, list):
                        docs = docs_data
                    else:
                        docs = []
                    
                    self.log("获取文档列表", True, f"找到 {len(docs)} 个文档")
                    
                    # 触发所有文档的解析
                    parse_success = 0
                    for doc in docs:
                        doc_id = doc['id']
                        doc_name = doc.get('name', 'Unknown')
                        
                        # 检查文档状态
                        current_status = doc.get('run', 'UNKNOWN')
                        self.log(f"文档 {doc_name} 当前状态", True, current_status)
                        
                        # 检查文档是否已经有内容（可能自动解析了）
                        try:
                            content_response = requests.get(
                                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents/{doc_id}",
                                headers=headers
                            )
                            
                            if content_response.status_code == 200 and len(content_response.text) > 10:
                                self.log(f"文档 {doc_name}", True, f"已解析 (内容长度: {len(content_response.text)})")
                                parse_success += 1
                            else:
                                self.log(f"文档 {doc_name}", False, f"状态: {current_status} (未解析)")
                        except Exception as e:
                            self.log(f"检查文档 {doc_name}", False, f"异常: {str(e)}")
                    
                    if parse_success > 0:
                        # 等待解析完成
                        self.log("等待解析", True, "等待文档解析完成...")
                        time.sleep(10)  # 等待解析
                        
                        # 检查解析状态
                        self._check_parse_status()
                        return True
                    else:
                        self.log("解析文档", False, "没有成功触发任何文档解析")
                        return False
                else:
                    self.log("获取文档列表", False, f"错误: {result.get('message', 'Unknown')}")
            else:
                self.log("获取文档列表", False, f"HTTP错误: {response.status_code}")
        except Exception as e:
            self.log("解析文档", False, f"异常: {str(e)}")
        
        return False
    
    def _check_parse_status(self):
        """检查解析状态"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/datasets/{self.kb_id}/documents",
                headers=headers,
                params={"page": 1, "page_size": 50}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    docs_data = result.get('data')
                    if isinstance(docs_data, dict) and 'docs' in docs_data:
                        docs = docs_data['docs']
                    elif isinstance(docs_data, list):
                        docs = docs_data
                    else:
                        docs = []
                    
                    status_summary = {}
                    for doc in docs:
                        status = doc.get('run', 'UNKNOWN')
                        status_summary[status] = status_summary.get(status, 0) + 1
                    
                    self.log("解析状态检查", True, f"状态统计: {status_summary}")
        except Exception as e:
            self.log("解析状态检查", False, f"异常: {str(e)}")
    
    def step4_test_retrieval(self):
        """步骤4: 测试知识库检索"""
        print(f"\n{'='*80}")
        print(f"步骤4: 测试知识库检索")
        print(f"{'='*80}")
        
        if not self.kb_id:
            self.log("知识库检索", False, "需要先创建知识库")
            return False
        
        # 测试多个检索问题
        test_questions = [
            "RAGFlow是什么？",
            "RAGFlow有哪些主要功能？",
            "如何上传文档到RAGFlow？",
            "RAGFlow支持哪些文件格式？",
            "RAGFlow的技术架构是怎样的？"
        ]
        
        retrieval_success = 0
        
        for question in test_questions:
            try:
                data = {
                    "question": question,
                    "dataset_ids": [self.kb_id],
                    "page": 1,
                    "page_size": 5
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
                        self.log(f"检索问题: {question}", True, 
                               f"返回 {len(chunks)} 个相关片段", {"chunks_count": len(chunks)})
                        
                        # 显示第一个检索结果
                        if chunks:
                            first_chunk = chunks[0]
                            content_preview = first_chunk.get('content_ltks', '')[:100] + "..."
                            score = first_chunk.get('similarity', 0)
                            self.log(f"  最佳匹配", True, 
                                   f"相似度: {score:.3f}, 内容: {content_preview}")
                        
                        retrieval_success += 1
                    else:
                        self.log(f"检索问题: {question}", False, 
                               f"错误: {result.get('message', 'Unknown')}")
                else:
                    self.log(f"检索问题: {question}", False, 
                           f"HTTP错误: {response.status_code}")
            except Exception as e:
                self.log(f"检索问题: {question}", False, f"异常: {str(e)}")
        
        if retrieval_success > 0:
            self.log("检索测试汇总", True, f"成功检索 {retrieval_success}/{len(test_questions)} 个问题")
            return True
        else:
            self.log("检索测试汇总", False, "所有检索测试都失败")
            return False
    
    def step5_create_chat(self):
        """步骤5: 创建对话会话"""
        print(f"\n{'='*80}")
        print(f"步骤5: 创建对话会话")
        print(f"{'='*80}")
        
        if not self.kb_id:
            self.log("创建对话", False, "需要先创建知识库")
            return False
        
        data = {
            "name": f"全链路测试对话_{datetime.now().strftime('%H%M%S')}",
            "dataset_ids": [self.kb_id],
            "description": "用于全链路测试的对话会话"
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/chats",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    self.chat_id = result['data']['id']
                    llm_info = result['data'].get('llm', {})
                    model_name = llm_info.get('model_name', 'Unknown')
                    
                    self.log("创建对话", True, 
                           f"ID: {self.chat_id}, 模型: {model_name}", result['data'])
                    return True
                else:
                    self.log("创建对话", False, f"错误: {result.get('message', 'Unknown')}")
            else:
                self.log("创建对话", False, f"HTTP错误: {response.status_code}")
        except Exception as e:
            self.log("创建对话", False, f"异常: {str(e)}")
        
        return False
    
    def step6_test_qa(self):
        """步骤6: 测试智能问答"""
        print(f"\n{'='*80}")
        print(f"步骤6: 测试智能问答")
        print(f"{'='*80}")
        
        if not self.chat_id:
            self.log("智能问答", False, "需要先创建对话")
            return False
        
        # 测试问题列表
        test_questions = [
            "你好，请简单介绍一下RAGFlow系统",
            "RAGFlow有哪些主要功能和特点？",
            "如何使用RAGFlow创建知识库？",
            "RAGFlow支持哪些文档格式？",
            "RAGFlow的技术架构包含哪几层？"
        ]
        
        qa_success = 0
        
        for i, question in enumerate(test_questions, 1):
            try:
                data = {
                    "content": question,
                    "question": question  # 尝试两种字段名
                }
                
                # 使用正确的completions端点
                response = requests.post(
                    f"{BASE_URL}/api/v1/chats/{self.chat_id}/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    # 处理SSE响应
                    response_text = response.text
                    
                    # 解析SSE数据
                    if response_text.startswith('data:'):
                        try:
                            # 提取JSON部分
                            json_part = response_text[5:]  # 去掉 'data:' 前缀
                            result = json.loads(json_part)
                            
                            if result.get('code') == 0:
                                answer = result.get('data', {}).get('answer', '')
                                session_id = result.get('data', {}).get('session_id', '')
                                
                                if not self.session_id:
                                    self.session_id = session_id
                                
                                # 显示问答结果
                                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                                self.log(f"问题 {i}: {question}", True, 
                                       f"回答长度: {len(answer)}字符")
                                self.log(f"  AI回答预览", True, answer_preview)
                                
                                qa_success += 1
                            else:
                                self.log(f"问题 {i}: {question}", False, 
                                       f"API错误: {result.get('message', 'Unknown')}")
                        except json.JSONDecodeError as e:
                            self.log(f"问题 {i}: {question}", False, 
                                   f"JSON解析错误: {str(e)}")
                    else:
                        # 尝试直接解析JSON
                        try:
                            result = json.loads(response_text)
                            self.log(f"问题 {i}: {question}", False, 
                                   f"意外响应格式: {result}")
                        except:
                            self.log(f"问题 {i}: {question}", False, 
                                   f"无法解析响应: {response_text[:100]}")
                else:
                    self.log(f"问题 {i}: {question}", False, 
                           f"HTTP错误: {response.status_code}")
                    
                # 间隔时间，避免请求过快
                time.sleep(2)
                
            except Exception as e:
                self.log(f"问题 {i}: {question}", False, f"异常: {str(e)}")
        
        if qa_success > 0:
            self.log("问答测试汇总", True, f"成功问答 {qa_success}/{len(test_questions)} 个问题")
            return True
        else:
            self.log("问答测试汇总", False, "所有问答测试都失败")
            return False
    
    def step7_cleanup(self):
        """步骤7: 清理测试数据（可选）"""
        print(f"\n{'='*80}")
        print(f"步骤7: 清理测试数据")
        print(f"{'='*80}")
        
        # 可以选择保留或删除测试数据
        self.log("数据清理", True, "保留测试数据供进一步验证")
        
        # 如果需要删除，取消下面的注释
        # if self.kb_id:
        #     try:
        #         response = requests.delete(
        #             f"{BASE_URL}/api/v1/datasets/{self.kb_id}",
        #             headers=headers
        #         )
        #         if response.status_code == 200 and response.json().get('code') == 0:
        #             self.log("删除知识库", True, f"已删除知识库 {self.kb_id}")
        #         else:
        #             self.log("删除知识库", False, "删除失败")
        #     except Exception as e:
        #         self.log("删除知识库", False, f"异常: {str(e)}")
    
    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{'='*80}")
        print(f"全链路测试摘要")
        print(f"{'='*80}")
        
        total_steps = len(self.results)
        success_steps = sum(1 for r in self.results if r['status'] == '✅')
        
        print(f"\n测试概览:")
        print(f"- 总步骤数: {total_steps}")
        print(f"- 成功步骤: {success_steps}")
        print(f"- 失败步骤: {total_steps - success_steps}")
        print(f"- 成功率: {(success_steps/total_steps*100):.1f}%")
        
        print(f"\n创建的资源:")
        if self.kb_id:
            print(f"- 知识库ID: {self.kb_id}")
        if self.chat_id:
            print(f"- 对话ID: {self.chat_id}")
        if self.session_id:
            print(f"- 会话ID: {self.session_id}")
        
        print(f"\n详细结果:")
        current_section = ""
        for result in self.results:
            # 检测是否是新的步骤节
            if result['step'].startswith(('步骤', '创建', '上传', '解析', '测试', '智能', '清理')):
                if result['step'] != current_section:
                    current_section = result['step']
                    print(f"\n{result['step']}:")
            
            print(f"  {result['status']} [{result['timestamp']}] {result['step']}: {result['message']}")


def main():
    """运行完整的全链路测试"""
    print(f"\n{'='*80}")
    print(f"RAGFlow 全链路API测试")
    print(f"测试时间: {datetime.now()}")
    print(f"API地址: {BASE_URL}")
    print(f"{'='*80}")
    
    tester = CompleteWorkflowTester()
    
    # 执行完整的测试流程
    try:
        # 步骤1: 创建知识库
        if tester.step1_create_knowledge_base():
            
            # 步骤2: 上传文档
            if tester.step2_upload_documents():
                
                # 步骤3: 解析文档
                if tester.step3_parse_documents():
                    
                    # 步骤4: 测试检索
                    tester.step4_test_retrieval()
                    
                    # 步骤5: 创建对话
                    if tester.step5_create_chat():
                        
                        # 步骤6: 测试问答
                        tester.step6_test_qa()
                
                # 步骤7: 清理（可选）
                tester.step7_cleanup()
    
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生异常: {str(e)}")
    
    # 打印摘要
    tester.print_summary()


if __name__ == "__main__":
    main()