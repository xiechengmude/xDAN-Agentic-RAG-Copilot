#!/usr/bin/env python3
"""
RAGFlow客户端实现
提供S3框架需要的核心检索功能
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))

class RAGFlowClient:
    """
    RAGFlow客户端
    
    职责：
    - 知识库检索（retrieve_chunks）
    - 数据集列表（list_datasets）
    - 基础的数据集和文档管理
    """
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            api_url: RAGFlow API地址
            api_key: API密钥
            timeout: 请求超时时间（秒）
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # 设置session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
        
        # 增强连接稳定性和重试机制
        retry_strategy = requests.adapters.Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504, 408, 429]
        )
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=retry_strategy
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 代理配置（如果需要）
        self._setup_proxy()
        
        logger.info(f"RAGFlow客户端初始化: {api_url}")
    
    def _setup_proxy(self):
        """设置代理（如果环境变量中有配置）"""
        import os
        if os.getenv('HTTP_PROXY'):
            self.session.proxies = {
                'http': os.getenv('HTTP_PROXY'),
                'https': os.getenv('HTTPS_PROXY', os.getenv('HTTP_PROXY'))
            }
            logger.info("使用代理配置")
    
    def retrieve_chunks(self, 
                       question: str, 
                       dataset_ids: List[str],
                       page: int = 1,
                       page_size: int = 10,
                       similarity_threshold: float = 0.1) -> Dict[str, Any]:
        """
        检索相关文档片段 - S3框架的核心需求
        
        Args:
            question: 检索查询
            dataset_ids: 数据集ID列表
            page: 页码
            page_size: 返回结果数量
            similarity_threshold: 相似度阈值
            
        Returns:
            检索结果，格式：
            {
                "code": 0,
                "data": {
                    "chunks": [
                        {
                            "content": "文档内容",
                            "document_name": "文档名",
                            "dataset_id": "数据集ID",
                            "similarity": 0.95
                        }
                    ]
                }
            }
        """
        url = f"{self.api_url}/api/v1/retrieval"
        
        payload = {
            "question": question,
            "dataset_ids": dataset_ids,
            "page": page,
            "page_size": page_size,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": 0.7
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"检索失败: {e}")
            return {
                "code": -1,
                "message": str(e),
                "data": {"chunks": []}
            }
    
    def list_datasets(self, page: int = 1, page_size: int = 12, name: str = None) -> Dict[str, Any]:
        """
        获取数据集列表
        
        Args:
            page: 页码
            page_size: 每页数量
            name: 名称筛选（可选）
            
        Returns:
            数据集列表响应
        """
        url = f"{self.api_url}/api/v1/datasets"
        
        # RAGFlow API不支持name参数作为搜索过滤器
        # 需要获取所有数据后在客户端过滤
        params = {
            "page": 1,  # 先获取第一页
            "page_size": 100  # 获取更多数据以便过滤
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            
            # 如果成功获取数据且指定了name参数，进行客户端过滤
            if result.get("code") == 0 and name and result.get("data"):
                filtered_data = [
                    dataset for dataset in result["data"]
                    if name.lower() in dataset.get("name", "").lower()
                ]
                # 实现分页
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                result["data"] = filtered_data[start_idx:end_idx]
                
            # 如果没有name参数但指定了分页，重新请求正确的分页
            elif result.get("code") == 0 and not name and (page != 1 or page_size != 100):
                params = {
                    "page": page,
                    "page_size": page_size
                }
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"获取数据集列表失败: {e}")
            return {"code": -1, "message": str(e)}
    
    def create_dataset(self, name: str, description: str = None, embedding_model: str = "BAAI/bge-m3@SILICONFLOW", 
                      chunk_method: str = "naive", parser_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建知识库"""
        url = f"{self.api_url}/api/v1/datasets"
        
        data = {
            "name": name,
            "description": description,
            "embedding_model": embedding_model,
            "chunk_method": chunk_method,
            "parser_config": parser_config or {
                "chunk_token_num": 512,
                "delimiter": "\n"
            }
        }
        
        try:
            response = self.session.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"创建知识库失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def update_dataset(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
        """更新知识库"""
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}"
        
        try:
            response = self.session.put(url, json=kwargs, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"更新知识库失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def delete_datasets(self, dataset_ids: List[str]) -> Dict[str, Any]:
        """删除知识库 - 使用批量删除接口"""
        url = f"{self.api_url}/api/v1/datasets"
        
        try:
            # RAGFlow使用批量删除接口，即使是单个删除
            data = {"ids": dataset_ids}
            response = self.session.delete(url, json=data, timeout=self.timeout)
            
            # 先尝试解析响应，即使状态码不是2xx
            try:
                result = response.json()
                # 如果响应包含RAGFlow的错误码，直接返回
                if "code" in result:
                    if result.get("code") == 0:
                        return {
                            "code": 0,
                            "message": "Dataset(s) deleted successfully",
                            "data": None
                        }
                    else:
                        return result
            except ValueError:
                # 如果响应不是JSON格式，继续处理
                pass
                
            # 如果没有获取到有效的错误码，才检查HTTP状态
            response.raise_for_status()
            
            # 如果到这里，说明响应成功但没有错误码
            return {
                "code": 0,
                "message": "Dataset(s) deleted successfully",
                "data": None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"删除知识库失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def upload_documents(self, dataset_id: str, file_paths: List[str]) -> Dict[str, Any]:
        """上传文档到知识库"""
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}/documents"
        
        try:
            # 目前只支持单文件上传
            if len(file_paths) == 1:
                file_path = file_paths[0]
                with open(file_path, 'rb') as f:
                    files = {'file': f}
                    # 临时移除Content-Type以支持multipart
                    headers = {'Authorization': self.session.headers['Authorization']}
                    response = requests.post(url, files=files, headers=headers, timeout=self.timeout)
                    response.raise_for_status()
                    return response.json()
            else:
                return {"code": 400, "message": "暂时只支持单文件上传", "data": None}
        except requests.exceptions.RequestException as e:
            logger.error(f"上传文档失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取文档列表"""
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}/documents"
        
        params = {
            "page": page,
            "page_size": page_size
        }
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"获取文档列表失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def delete_documents(self, dataset_id: str, document_ids: List[str]) -> Dict[str, Any]:
        """删除文档 - 使用批量删除接口"""
        # RAGFlow使用批量删除接口，即使是单个文档
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}/documents"
        
        try:
            data = {"ids": document_ids}
            response = self.session.delete(url, json=data, timeout=self.timeout)
            
            # 先尝试解析响应，即使状态码不是2xx
            try:
                result = response.json()
                # 如果响应包含RAGFlow的错误码，直接返回
                if "code" in result:
                    if result.get("code") == 0:
                        return {
                            "code": 0,
                            "message": "Document(s) deleted successfully",
                            "data": None
                        }
                    else:
                        return result
            except ValueError:
                # 如果响应不是JSON格式，继续处理
                pass
                
            # 如果没有获取到有效的错误码，才检查HTTP状态
            response.raise_for_status()
            
            # 如果到这里，说明响应成功但没有错误码
            return {
                "code": 0,
                "message": "Document(s) deleted successfully",
                "data": None
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"删除文档失败: {e}")
            return {"code": 500, "message": str(e), "data": None}
    
    def get_document_content(self, dataset_id: str, document_id: str) -> str:
        """获取文档内容"""
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}/documents/{document_id}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text  # 返回原始文本内容
        except requests.exceptions.RequestException as e:
            logger.error(f"获取文档内容失败: {e}")
            raise e
    
    def download_document(self, dataset_id: str, document_id: str) -> bytes:
        """下载文档"""
        url = f"{self.api_url}/api/v1/datasets/{dataset_id}/documents/{document_id}/download"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content  # 返回二进制内容
        except requests.exceptions.RequestException as e:
            logger.error(f"下载文档失败: {e}")
            raise e

    def __repr__(self):
        return f"RAGFlowClient(api_url='{self.api_url}')"