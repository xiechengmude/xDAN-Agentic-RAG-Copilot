"""
API数据模型定义 - 使用Pydantic进行请求/响应验证
遵循KISS原则，保持模型简洁明了
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class SearchMode(str, Enum):
    """搜索模式枚举"""
    FLASH = "flash"      # 闪电搜索（1-2轮）
    STANDARD = "standard" # 标准搜索（3-5轮）
    DEEP = "deep"        # 深度搜索（5+轮）

class SearchRequest(BaseModel):
    """搜索请求模型"""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "question": "分析字节跳动的商业模式和竞争优势",
            "mode": "standard",
            "max_rounds": 5,
            "stream": False
        }
    })
    
    question: str = Field(..., min_length=1, max_length=1000, description="搜索问题")
    mode: SearchMode = Field(default=SearchMode.STANDARD, description="搜索模式")
    max_rounds: int = Field(default=5, ge=1, le=10, description="最大搜索轮数")
    stream: bool = Field(default=False, description="是否流式返回结果")
    language: str = Field(default="zh", description="响应语言")

class SearchRound(BaseModel):
    """单轮搜索结果"""
    round: int = Field(..., description="轮次")
    query: str = Field(..., description="搜索查询")
    results_count: int = Field(..., description="搜索结果数")
    selected_urls: List[str] = Field(default_factory=list, description="选中的URL")
    thinking: Optional[str] = Field(None, description="思考过程")
    duration: float = Field(..., description="耗时（秒）")

class SearchSource(BaseModel):
    """信息来源"""
    url: str = Field(..., description="来源URL")
    title: str = Field(..., description="标题")
    snippet: Optional[str] = Field(None, description="摘要")
    relevance_score: float = Field(..., ge=0, le=1, description="相关性分数")

class SearchResponse(BaseModel):
    """搜索响应模型"""
    request_id: str = Field(..., description="请求ID")
    question: str = Field(..., description="原始问题")
    answer: str = Field(..., description="最终答案")
    rounds: List[SearchRound] = Field(..., description="搜索轮次详情")
    sources: List[SearchSource] = Field(..., description="信息来源")
    total_duration: float = Field(..., description="总耗时（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "request_id": "req_123456",
            "question": "分析字节跳动的商业模式",
            "answer": "字节跳动的商业模式主要包括...",
            "rounds": [
                {
                    "round": 1,
                    "query": "字节跳动 商业模式 2024",
                    "results_count": 10,
                    "selected_urls": ["https://example.com"],
                    "thinking": "需要了解最新的商业模式信息",
                    "duration": 15.2
                }
            ],
            "sources": [
                {
                    "url": "https://example.com",
                    "title": "字节跳动2024年报",
                    "snippet": "...",
                    "relevance_score": 0.95
                }
            ],
            "total_duration": 45.6,
            "timestamp": "2024-06-30T01:00:00"
        }
    })

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    detail: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    uptime: float = Field(..., description="运行时间（秒）")
    services: Dict[str, bool] = Field(..., description="依赖服务状态")

class StreamChunk(BaseModel):
    """流式响应块"""
    type: str = Field(..., description="数据类型: content/status/error")
    data: str = Field(..., description="数据内容")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")