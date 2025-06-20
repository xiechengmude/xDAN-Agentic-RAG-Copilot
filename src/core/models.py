from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: bool = False


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: Optional[Message] = None
    delta: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    logprobs: Optional[Any] = None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Optional[ChatCompletionUsage] = None


class DatasetCreateRequest(BaseModel):
    name: str
    avatar: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    permission: Optional[str] = "me"
    chunk_method: Optional[str] = "naive"
    pagerank: Optional[int] = 0
    parser_config: Optional[Dict[str, Any]] = None


class DatasetResponse(BaseModel):
    code: int
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class DocumentListRequest(BaseModel):
    page: Optional[int] = 1
    page_size: Optional[int] = 30
    orderby: Optional[str] = "create_time"
    desc: Optional[bool] = True
    keywords: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None


class RetrievalRequest(BaseModel):
    question: str
    dataset_ids: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 30
    similarity_threshold: Optional[float] = 0.2
    vector_similarity_weight: Optional[float] = 0.3
    top_k: Optional[int] = 1024
    rerank_id: Optional[str] = None
    keyword: Optional[bool] = False
    highlight: Optional[bool] = False


class ErrorResponse(BaseModel):
    code: int
    message: str
