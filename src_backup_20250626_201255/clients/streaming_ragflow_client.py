#!/usr/bin/env python3
"""
Enhanced RAGFlow Client with OpenAI-compatible streaming support
Designed for better LiteLLM integration and proper streaming handling
"""

import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional, Iterator, Union
from datetime import datetime
import uuid
import time

logger = logging.getLogger(__name__)

class StreamingRAGFlowClient:
    """
    Enhanced RAGFlow client with proper streaming support and OpenAI compatibility
    """
    
    def __init__(self, api_url: str, api_key: str, timeout: int = 60):
        """
        Initialize the streaming RAGFlow client
        
        Args:
            api_url: RAGFlow API base URL
            api_key: RAGFlow API key
            timeout: Request timeout in seconds
        """
        self.base_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Create session with persistent connection
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'StreamingRAGFlowClient/1.0'
        })
        
        logger.info(f"StreamingRAGFlowClient initialized: {self.base_url}")
    
    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle standard HTTP response"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            try:
                error_data = response.json()
                raise Exception(f"API Error {response.status_code}: {error_data.get('message', str(e))}")
            except json.JSONDecodeError:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise Exception(f"Invalid JSON response: {response.text}")
    
    def _parse_sse_line(self, line: str) -> Optional[Dict]:
        """Parse Server-Sent Events line"""
        line = line.strip()
        if not line:
            return None
        
        if line.startswith('data:'):
            data_part = line[5:].strip()  # Remove 'data:' prefix
            
            # Handle special SSE markers
            if data_part == '[DONE]':
                return {'type': 'done'}
            
            # Handle empty data
            if not data_part:
                return None
            
            try:
                return json.loads(data_part)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse SSE data: {data_part}, error: {e}")
                return None
        
        return None
    
    def _stream_request(self, endpoint: str, payload: Dict[str, Any]) -> Iterator[Dict]:
        """
        Handle streaming request with proper SSE parsing
        
        Args:
            endpoint: API endpoint
            payload: Request payload
            
        Yields:
            Parsed streaming chunks
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(
                url,
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    chunk = self._parse_sse_line(line)
                    if chunk:
                        if chunk.get('type') == 'done':
                            break
                        yield chunk
                        
        except requests.exceptions.RequestException as e:
            logger.error(f"Streaming request failed: {e}")
            raise Exception(f"Streaming request failed: {e}")
    
    # ==================== Dataset Management ====================
    
    def list_datasets(self, page: int = 1, page_size: int = 30) -> Dict:
        """List datasets"""
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets",
            params={'page': page, 'page_size': page_size},
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def get_dataset(self, dataset_id: str) -> Dict:
        """Get dataset details using parameter filtering"""
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets",
            params={'id': dataset_id},
            timeout=self.timeout
        )
        result = self._handle_response(response)
        
        # Extract single dataset from list response
        if result.get('code') == 0:
            datasets = result.get('data', [])
            if datasets:
                return {'code': 0, 'data': datasets[0]}
            else:
                return {'code': 404, 'message': 'Dataset not found'}
        return result
    
    def create_dataset(self, name: str, description: str = None) -> Dict:
        """Create a new dataset"""
        payload = {'name': name}
        if description:
            payload['description'] = description
            
        response = self.session.post(
            f"{self.base_url}/api/v1/datasets",
            json=payload,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    # ==================== Document Management ====================
    
    def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 30) -> Dict:
        """List documents in a dataset"""
        response = self.session.get(
            f"{self.base_url}/api/v1/datasets/{dataset_id}/documents",
            params={'page': page, 'page_size': page_size},
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    # ==================== Chat Management ====================
    
    def create_chat(self, chat_data: Dict) -> Dict:
        """Create a new chat"""
        response = self.session.post(
            f"{self.base_url}/api/v1/chats",
            json=chat_data,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def list_chats(self, page: int = 1, page_size: int = 30) -> Dict:
        """List chats"""
        response = self.session.get(
            f"{self.base_url}/api/v1/chats",
            params={'page': page, 'page_size': page_size},
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    def get_chat(self, chat_id: str) -> Dict:
        """Get chat details"""
        response = self.session.get(
            f"{self.base_url}/api/v1/chats/{chat_id}",
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    # ==================== OpenAI-Compatible Chat Completions ====================
    
    def send_message_openai_compatible(
        self, 
        chat_id: str, 
        messages: List[Dict], 
        model: str = "ragflow",
        stream: bool = False
    ) -> Union[Dict, Iterator[Dict]]:
        """
        Send message using OpenAI-compatible endpoint
        
        Args:
            chat_id: Chat ID
            messages: List of messages in OpenAI format
            model: Model name
            stream: Whether to stream the response
            
        Returns:
            Response dict or iterator of chunks if streaming
        """
        endpoint = f"/api/v1/chats_openai/{chat_id}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if stream:
            return self._stream_openai_completion(endpoint, payload)
        else:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=self.timeout
            )
            return self._handle_response(response)
    
    def _stream_openai_completion(self, endpoint: str, payload: Dict) -> Iterator[Dict]:
        """
        Stream OpenAI-compatible completion
        
        Args:
            endpoint: API endpoint
            payload: Request payload
            
        Yields:
            OpenAI-compatible streaming chunks
        """
        try:
            for chunk in self._stream_request(endpoint, payload):
                # Convert RAGFlow streaming format to OpenAI format
                if chunk.get('data'):
                    data = chunk['data']
                    
                    # Handle final completion
                    if isinstance(data, bool) and data:
                        yield {
                            'id': f'chatcmpl-{uuid.uuid4()}',
                            'object': 'chat.completion.chunk',
                            'created': int(time.time()),
                            'model': payload.get('model', 'ragflow'),
                            'choices': [{
                                'index': 0,
                                'delta': {},
                                'finish_reason': 'stop'
                            }]
                        }
                        break
                    
                    # Handle content chunks
                    elif isinstance(data, dict) and data.get('answer'):
                        yield {
                            'id': f'chatcmpl-{uuid.uuid4()}',
                            'object': 'chat.completion.chunk',
                            'created': int(time.time()),
                            'model': payload.get('model', 'ragflow'),
                            'choices': [{
                                'index': 0,
                                'delta': {
                                    'content': data['answer']
                                },
                                'finish_reason': None
                            }]
                        }
                        
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield {
                'error': {
                    'message': str(e),
                    'type': 'streaming_error'
                }
            }
    
    # ==================== Legacy Chat Interface ====================
    
    def send_message(self, chat_id: str, message: str, stream: bool = False) -> Union[Dict, Iterator[Dict]]:
        """
        Send message using legacy endpoint (with fallback to OpenAI endpoint)
        
        Args:
            chat_id: Chat ID
            message: Message content
            stream: Whether to stream the response
            
        Returns:
            Response dict or iterator if streaming
        """
        # Try legacy endpoint first
        legacy_payload = {
            "question": message,
            "stream": stream
        }
        
        if stream:
            try:
                # Try RAGFlow native streaming
                return self._stream_ragflow_completion(chat_id, legacy_payload)
            except Exception as e:
                logger.warning(f"Legacy streaming failed, falling back to OpenAI: {e}")
                # Fallback to OpenAI endpoint
                messages = [{"role": "user", "content": message}]
                return self.send_message_openai_compatible(chat_id, messages, stream=True)
        else:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/chats/{chat_id}/completions",
                    json=legacy_payload,
                    timeout=self.timeout
                )
                return self._handle_response(response)
            except Exception as e:
                logger.warning(f"Legacy endpoint failed, falling back to OpenAI: {e}")
                # Fallback to OpenAI endpoint
                messages = [{"role": "user", "content": message}]
                return self.send_message_openai_compatible(chat_id, messages, stream=False)
    
    def _stream_ragflow_completion(self, chat_id: str, payload: Dict) -> Iterator[Dict]:
        """
        Stream using RAGFlow native format
        
        Args:
            chat_id: Chat ID
            payload: Request payload
            
        Yields:
            RAGFlow native streaming chunks
        """
        endpoint = f"/api/v1/chats/{chat_id}/completions"
        
        try:
            for chunk in self._stream_request(endpoint, payload):
                # Process RAGFlow native streaming format
                if chunk.get('code') == 0:
                    data = chunk.get('data', {})
                    
                    # Handle final response
                    if isinstance(data, bool) and data:
                        break
                    
                    # Handle content response
                    elif isinstance(data, dict):
                        yield {
                            'chunk_type': 'content',
                            'content': data.get('answer', ''),
                            'references': data.get('references', []),
                            'session_id': data.get('session_id'),
                            'timestamp': datetime.now().isoformat()
                        }
                        
        except Exception as e:
            logger.error(f"RAGFlow streaming failed: {e}")
            yield {
                'chunk_type': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # ==================== Retrieval ====================
    
    def retrieve(self, question: str, dataset_ids: List[str], top_k: int = 5) -> Dict:
        """Retrieve relevant chunks"""
        payload = {
            "question": question,
            "dataset_ids": dataset_ids,
            "top_k": top_k
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/retrieval",
            json=payload,
            timeout=self.timeout
        )
        return self._handle_response(response)
    
    # ==================== Health Check ====================
    
    def health_check(self) -> Dict:
        """Perform health check"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/health",
                timeout=10
            )
            return self._handle_response(response)
        except Exception as e:
            return {
                "code": 500,
                "message": f"Health check failed: {e}",
                "status": "unhealthy"
            }