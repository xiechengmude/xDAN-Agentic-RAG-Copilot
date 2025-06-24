#!/usr/bin/env python3
"""
xDAN RAG Copilot API Client
支持新版API接口的客户端
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path
from dotenv import load_dotenv

# 确保加载正确的.env文件
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class APIError(Exception):
    """API错误"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Error {code}: {message}")

class XDANRagClient:
    """
    xDAN RAG Copilot API客户端
    实现新版API接口规范
    """
    
    # 错误代码定义
    ERROR_CODES = {
        0: "成功",
        100: "通用错误",
        101: "文件相关错误",
        400: "请求参数错误",
        401: "未授权",
        404: "资源不存在",
        500: "服务器内部错误"
    }
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        初始化客户端
        
        Args:
            api_url: API基础URL（默认: http://localhost:8050）
            api_key: API认证密钥
        """
        self.api_url = api_url or os.getenv("RAGFLOW_API_URL", "http://localhost:8050")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not self.api_key:
            raise ValueError("API Key未设置")
        
        # 确保URL以/api/v1结尾
        if not self.api_url.endswith("/api/v1"):
            self.api_url = f"{self.api_url.rstrip('/')}/api/v1"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"xDAN RAG Client初始化成功: {self.api_url}")
    
    # ==================== 统一响应处理 ====================
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """统一处理API响应"""
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise APIError(500, f"Invalid JSON response: {response.text}")
        
        if data.get('code') != 0:
            error_code = data.get('code', -1)
            error_message = data.get('message', 'Unknown error')
            error_desc = self.ERROR_CODES.get(error_code, f"Unknown error code {error_code}")
            raise APIError(error_code, f"{error_desc}: {error_message}")
        
        return data.get('data', {})
    
    # ==================== 数据集（知识库）管理 ====================
    
    def list_datasets(self, page: int = 1, page_size: int = 30, **kwargs) -> Dict[str, Any]:
        """
        获取数据集列表
        
        Args:
            page: 页码
            page_size: 每页大小
            
        Returns:
            包含数据集列表和分页信息的字典
        """
        params = {"page": page, "page_size": page_size, **kwargs}
        response = requests.get(f"{self.api_url}/datasets", headers=self.headers, params=params)
        data = self._handle_response(response)
        
        # 如果返回的是列表，包装成标准格式
        if isinstance(data, list):
            return {
                "datasets": data,
                "total": len(data)
            }
        return data
    
    def create_dataset(self, name: str, description: str = "", 
                      embedding_model: str = None,
                      chunk_method: str = None, **kwargs) -> Dict[str, Any]:
        """
        创建数据集
        
        Args:
            name: 数据集名称
            description: 描述
            embedding_model: 嵌入模型（格式: 模型名@提供商）
            chunk_method: 分块方法
            
        Returns:
            创建的数据集信息
        """
        # 从环境变量或使用传入的值
        if embedding_model is None:
            embedding_model = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3@SILICONFLOW")
        if chunk_method is None:
            chunk_method = os.getenv("DEFAULT_CHUNK_METHOD", "naive")
            
        payload = {
            "name": name,
            "description": description,
            "embedding_model": embedding_model,
            "chunk_method": chunk_method
        }
        
        # 添加解析配置
        parser_config = kwargs.get('parser_config', {})
        if parser_config:
            payload['parser_config'] = parser_config
        
        response = requests.post(f"{self.api_url}/datasets", headers=self.headers, json=payload)
        return self._handle_response(response)
    
    def update_dataset(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
        """更新数据集信息"""
        response = requests.put(f"{self.api_url}/datasets/{dataset_id}", 
                              headers=self.headers, json=kwargs)
        return self._handle_response(response)
    
    def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """删除单个数据集"""
        response = requests.delete(f"{self.api_url}/datasets/{dataset_id}", headers=self.headers)
        return self._handle_response(response)
    
    # ==================== 文档管理 ====================
    
    def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 30, 
                      **kwargs) -> Dict[str, Any]:
        """获取文档列表"""
        params = {"page": page, "page_size": page_size, **kwargs}
        response = requests.get(f"{self.api_url}/datasets/{dataset_id}/documents", 
                              headers=self.headers, params=params)
        return self._handle_response(response)
    
    def upload_document(self, dataset_id: str, file_path: str) -> Dict[str, Any]:
        """
        上传文档
        
        Args:
            dataset_id: 数据集ID
            file_path: 文件路径
            
        Returns:
            上传的文档信息
        """
        headers = {"Authorization": f"Bearer {self.api_key}"}  # 不设置Content-Type
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}  # 使用'file'而不是'files[]'
            response = requests.post(
                f"{self.api_url}/datasets/{dataset_id}/documents",
                headers=headers,
                files=files
            )
        
        data = self._handle_response(response)
        # 响应是数组格式，取第一个元素
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return data
    
    def get_document(self, dataset_id: str, doc_id: str) -> Dict[str, Any]:
        """获取文档详情"""
        response = requests.get(f"{self.api_url}/datasets/{dataset_id}/documents/{doc_id}", 
                              headers=self.headers)
        return self._handle_response(response)
    
    def delete_document(self, dataset_id: str, doc_id: str) -> Dict[str, Any]:
        """删除单个文档"""
        response = requests.delete(f"{self.api_url}/datasets/{dataset_id}/documents/{doc_id}", 
                                 headers=self.headers)
        return self._handle_response(response)
    
    def batch_delete_documents(self, dataset_id: str, doc_ids: List[str]) -> Dict[str, Any]:
        """批量删除文档"""
        payload = {"ids": doc_ids}
        response = requests.delete(f"{self.api_url}/datasets/{dataset_id}/documents", 
                                 headers=self.headers, json=payload)
        return self._handle_response(response)
    
    def download_document(self, dataset_id: str, doc_id: str) -> bytes:
        """下载文档"""
        response = requests.get(f"{self.api_url}/datasets/{dataset_id}/documents/{doc_id}/download", 
                              headers=self.headers)
        if response.status_code == 200:
            return response.content
        else:
            self._handle_response(response)
    
    # ==================== 对话管理 ====================
    
    def create_chat(self, name: str, dataset_ids: List[str]) -> Dict[str, Any]:
        """
        创建对话
        
        Args:
            name: 对话名称
            dataset_ids: 关联的数据集ID列表
            
        Returns:
            创建的对话信息
        """
        payload = {
            "name": name,
            "dataset_ids": dataset_ids
        }
        response = requests.post(f"{self.api_url}/chats", headers=self.headers, json=payload)
        return self._handle_response(response)
    
    def send_message(self, chat_id: str, content: str, stream: bool = True) -> Union[Dict[str, Any], requests.Response]:
        """
        发送消息
        
        Args:
            chat_id: 对话ID
            content: 消息内容
            stream: 是否使用流式响应
            
        Returns:
            非流式：返回完整响应
            流式：返回Response对象用于流式读取
        """
        payload = {"content": content}
        
        if stream:
            # 流式响应
            response = requests.post(
                f"{self.api_url}/chats/{chat_id}/completions",
                headers=self.headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()
            return response
        else:
            # 非流式响应
            response = requests.post(
                f"{self.api_url}/chats/{chat_id}/completions",
                headers=self.headers,
                json=payload
            )
            return self._handle_response(response)
    
    def get_chat_messages(self, chat_id: str, page: int = 1, page_size: int = 30) -> Dict[str, Any]:
        """获取对话历史"""
        params = {"page": page, "page_size": page_size}
        response = requests.get(f"{self.api_url}/chats/{chat_id}/messages", 
                              headers=self.headers, params=params)
        return self._handle_response(response)
    
    def delete_chat(self, chat_id: str) -> Dict[str, Any]:
        """删除对话"""
        response = requests.delete(f"{self.api_url}/chats/{chat_id}", headers=self.headers)
        return self._handle_response(response)
    
    # ==================== 检索功能 ====================
    
    def retrieve_chunks(self, question: str, dataset_ids: List[str], 
                       page: int = 1, page_size: int = 5, **kwargs) -> Dict[str, Any]:
        """
        知识库检索
        
        Args:
            question: 查询问题
            dataset_ids: 数据集ID列表
            page: 页码
            page_size: 每页大小
            
        Returns:
            检索结果
        """
        payload = {
            "question": question,
            "dataset_ids": dataset_ids,
            "page": page,
            "page_size": page_size
        }
        response = requests.post(f"{self.api_url}/retrieval", headers=self.headers, json=payload)
        return self._handle_response(response)
    
    # ==================== SSE流式处理 ====================
    
    def handle_sse_stream(self, response: requests.Response) -> AsyncGenerator[Dict[str, Any], None]:
        """
        处理SSE流式响应
        
        Args:
            response: 流式响应对象
            
        Yields:
            解析后的事件数据
        """
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data:'):
                    data_str = line[5:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            if data.get('code') == 0:
                                if isinstance(data.get('data'), dict) and 'answer' in data['data']:
                                    yield data['data']
                                elif data.get('data') == True:
                                    # 流结束
                                    break
                            else:
                                # 错误
                                raise APIError(data.get('code', -1), data.get('message', 'Unknown error'))
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析SSE数据: {data_str}")
    
    # ==================== 兼容性方法 ====================
    
    def list_datasets_compatible(self, **kwargs) -> Dict[str, Any]:
        """兼容旧版API的列表方法"""
        try:
            result = self.list_datasets(**kwargs)
            return {
                "code": 0,
                "data": result.get('datasets', [])
            }
        except APIError as e:
            return {"code": e.code, "message": e.message}
    
    def retrieve_chunks_compatible(self, question: str, dataset_ids: List[str] = None, 
                                  top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """兼容旧版API的检索方法"""
        try:
            # 使用page_size代替top_k
            result = self.retrieve_chunks(
                question=question,
                dataset_ids=dataset_ids or [],
                page_size=top_k,
                **kwargs
            )
            
            # 转换格式
            chunks = result.get('chunks', [])
            return {
                "code": 0,
                "data": {
                    "chunks": chunks,
                    "total": len(chunks)
                }
            }
        except APIError as e:
            return {"code": e.code, "message": e.message}