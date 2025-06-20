import os
import json
import requests
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RAGFlowClient:
    """RAGFlow API 客户端"""
    
    def __init__(self, api_url: str = None, api_key: str = None):
        """
        初始化 RAGFlow API 客户端
        
        Args:
            api_url: RAGFlow API 的基础 URL
            api_key: RAGFlow API 的认证密钥
        """
        self.api_url = api_url or os.getenv("RAGFLOW_API_URL")
        self.api_key = api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not self.api_url:
            raise ValueError("RAGFlow API URL 未设置")
        if not self.api_key:
            raise ValueError("RAGFlow API Key 未设置")
        
        # 移除 URL 末尾的斜杠
        self.api_url = self.api_url.rstrip("/")
        
        # 设置通用请求头
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Any = None, files: Any = None, 
                     params: Dict = None, stream: bool = False) -> Union[Dict, requests.Response]:
        """
        发送 HTTP 请求到 RAGFlow API
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            data: 请求体数据
            files: 文件数据 (用于上传文档)
            params: URL 查询参数
            stream: 是否以流的形式返回响应
            
        Returns:
            如果 stream=True，返回原始 Response 对象；否则返回解析后的 JSON 数据
        """
        url = f"{self.api_url}{endpoint}"
        
        # 准备请求头
        headers = self.headers.copy()
        
        # 如果有文件，不设置 Content-Type，让 requests 自动处理
        if files:
            headers.pop("Content-Type", None)
        
        # 发送请求
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data if data and not files else None,
            files=files,
            params=params,
            stream=stream
        )
        
        # 检查响应状态
        if not stream and not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get("message", "未知错误")
                error_code = error_data.get("code", 0)
                raise Exception(f"RAGFlow API 错误 (代码 {error_code}): {error_message}")
            except json.JSONDecodeError:
                response.raise_for_status()
        
        # 返回响应
        if stream:
            return response
        
        return response.json()
    
    # =============== OpenAI 兼容 API ===============
    
    def create_chat_completion(self, chat_id: str, model: str, messages: List[Dict], stream: bool = False) -> Any:
        """
        创建聊天完成
        
        Args:
            chat_id: 聊天助手 ID
            model: 模型名称
            messages: 消息列表
            stream: 是否以流的形式返回响应
            
        Returns:
            聊天完成响应
        """
        endpoint = f"/api/v1/chats_openai/{chat_id}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        return self._make_request("POST", endpoint, data, stream=stream)
    
    def create_agent_completion(self, agent_id: str, model: str, messages: List[Dict], stream: bool = False) -> Any:
        """
        创建 Agent 完成
        
        Args:
            agent_id: Agent ID
            model: 模型名称
            messages: 消息列表
            stream: 是否以流的形式返回响应
            
        Returns:
            Agent 完成响应
        """
        endpoint = f"/api/v1/agents_openai/{agent_id}/chat/completions"
        data = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        return self._make_request("POST", endpoint, data, stream=stream)
    
    # =============== 数据集管理 ===============
    
    def create_dataset(self, name: str, **kwargs) -> Dict:
        """
        创建数据集
        
        Args:
            name: 数据集名称
            **kwargs: 其他可选参数
            
        Returns:
            创建结果
        """
        endpoint = "/api/v1/datasets"
        data = {"name": name, **kwargs}
        
        return self._make_request("POST", endpoint, data)
    
    def delete_datasets(self, ids: List[str] = None) -> Dict:
        """
        删除数据集
        
        Args:
            ids: 数据集 ID 列表，如果为 None 则删除所有数据集
            
        Returns:
            删除结果
        """
        endpoint = "/api/v1/datasets"
        data = {"ids": ids}
        
        return self._make_request("DELETE", endpoint, data)
    
    def update_dataset(self, dataset_id: str, **kwargs) -> Dict:
        """
        更新数据集
        
        Args:
            dataset_id: 数据集 ID
            **kwargs: 要更新的字段
            
        Returns:
            更新结果
        """
        endpoint = f"/api/v1/datasets/{dataset_id}"
        
        return self._make_request("PUT", endpoint, kwargs)
    
    def list_datasets(self, page: int = 1, page_size: int = 30, orderby: str = "create_time", 
                     desc: bool = True, name: str = None, id: str = None) -> Dict:
        """
        列出数据集
        
        Args:
            page: 页码
            page_size: 每页大小
            orderby: 排序字段
            desc: 是否降序排序
            name: 按名称过滤
            id: 按 ID 过滤
            
        Returns:
            数据集列表
        """
        endpoint = "/api/v1/datasets"
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc
        }
        
        if name:
            params["name"] = name
        if id:
            params["id"] = id
        
        return self._make_request("GET", endpoint, params=params)
    
    # =============== 文档管理 ===============
    
    def upload_documents(self, dataset_id: str, file_paths: List[str]) -> Dict:
        """
        上传文档到数据集
        
        Args:
            dataset_id: 数据集 ID
            file_paths: 文件路径列表
            
        Returns:
            上传结果
        """
        endpoint = f"/api/v1/datasets/{dataset_id}/documents"
        
        files = []
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            files.append(('file', (file_name, open(file_path, 'rb'))))
        
        return self._make_request("POST", endpoint, files=files)
    
    def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 30, 
                      orderby: str = "create_time", desc: bool = True, 
                      keywords: str = None, id: str = None, name: str = None) -> Dict:
        """
        列出数据集中的文档
        
        Args:
            dataset_id: 数据集 ID
            page: 页码
            page_size: 每页大小
            orderby: 排序字段
            desc: 是否降序排序
            keywords: 关键词过滤
            id: 按 ID 过滤
            name: 按名称过滤
            
        Returns:
            文档列表
        """
        endpoint = f"/api/v1/datasets/{dataset_id}/documents"
        params = {
            "page": page,
            "page_size": page_size,
            "orderby": orderby,
            "desc": desc
        }
        
        if keywords:
            params["keywords"] = keywords
        if id:
            params["id"] = id
        if name:
            params["name"] = name
        
        return self._make_request("GET", endpoint, params=params)
    
    def delete_documents(self, dataset_id: str, document_ids: List[str] = None) -> Dict:
        """
        删除数据集中的文档
        
        Args:
            dataset_id: 数据集 ID
            document_ids: 文档 ID 列表，如果为 None 则删除所有文档
            
        Returns:
            删除结果
        """
        endpoint = f"/api/v1/datasets/{dataset_id}/documents"
        data = {"ids": document_ids}
        
        return self._make_request("DELETE", endpoint, data)
    
    def parse_documents(self, dataset_id: str, document_ids: List[str]) -> Dict:
        """
        解析文档
        
        Args:
            dataset_id: 数据集 ID
            document_ids: 文档 ID 列表
            
        Returns:
            解析结果
        """
        endpoint = f"/api/v1/datasets/{dataset_id}/chunks"
        data = {"document_ids": document_ids}
        
        return self._make_request("POST", endpoint, data)
    
    # =============== 检索 ===============
    
    def retrieve_chunks(self, question: str, dataset_ids: List[str] = None, 
                       document_ids: List[str] = None, page: int = 1, 
                       page_size: int = 30, similarity_threshold: float = 0.2,
                       vector_similarity_weight: float = 0.3, top_k: int = 1024,
                       rerank_id: str = None, keyword: bool = False, 
                       highlight: bool = False):
        """
        检索文本块
        
        Args:
            question: 查询问题
            dataset_ids: 数据集ID列表
            document_ids: 文档ID列表
            page: 页码，默认1
            page_size: 每页大小，默认30
            similarity_threshold: 相似度阈值，默认0.2
            vector_similarity_weight: 向量相似度权重，默认0.3
            top_k: 向量计算的块数量，默认1024
            rerank_id: 重排序模型ID
            keyword: 是否启用关键词匹配，默认False
            highlight: 是否启用高亮，默认False
        """
        # 构建请求体
        data = {
            "question": question,
            "page": page,
            "page_size": page_size,
            "similarity_threshold": similarity_threshold,
            "vector_similarity_weight": vector_similarity_weight,
            "top_k": top_k,
            "keyword": keyword,
            "highlight": highlight
        }
        
        # 只添加非空的ID列表
        if dataset_ids:
            data["dataset_ids"] = dataset_ids
        if document_ids:
            data["document_ids"] = document_ids
        if rerank_id:
            data["rerank_id"] = rerank_id
        
        # 确保至少有一个ID列表
        if not dataset_ids and not document_ids:
            raise ValueError("Either dataset_ids or document_ids must be provided")
        
        response = self._make_request("POST", "/api/v1/retrieval", data)
        return response
