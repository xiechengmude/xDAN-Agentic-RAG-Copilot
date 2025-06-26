#!/usr/bin/env python3
"""
Service Factory for RAGFlow Services
Creates appropriate service instances with different client types
"""

import os
import logging
from typing import Union, Optional

from src.clients.ragflow_sdk_wrapper import RAGFlowSDKWrapper, SDK_AVAILABLE
from src.clients.ragflow_client import RAGFlowClient
from src.clients.streaming_ragflow_client import StreamingRAGFlowClient
from src.clients.llm_client import LLMClient

from .enhanced_s3_rag_service import EnhancedS3RAGService
from .enhanced_s3_rag_service_v2_fixed import EnhancedS3RAGServiceV2

logger = logging.getLogger(__name__)

class RAGServiceFactory:
    """Factory for creating RAG services with appropriate clients"""
    
    @staticmethod
    def create_streaming_s3_service(
        ragflow_api_url: str = None,
        ragflow_api_key: str = None,
        search_model_config: dict = None,
        generator_model_config: dict = None
    ) -> EnhancedS3RAGServiceV2:
        """
        Create Enhanced S3 RAG Service V2 with streaming client
        
        Args:
            ragflow_api_url: RAGFlow API URL
            ragflow_api_key: RAGFlow API key
            search_model_config: Search model configuration
            generator_model_config: Generator model configuration
            
        Returns:
            EnhancedS3RAGServiceV2 instance with streaming client
        """
        # Use environment variables as defaults
        api_url = ragflow_api_url or os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        api_key = ragflow_api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not api_key:
            raise ValueError("RAGFlow API key is required")
        
        # Create streaming RAGFlow client
        streaming_client = StreamingRAGFlowClient(api_url, api_key)
        
        # Create LLM clients
        search_llm = None
        generator_llm = None
        
        if search_model_config:
            search_llm = LLMClient(
                base_url=search_model_config.get('url'),
                api_key=search_model_config.get('api_key'),
                model_name=search_model_config.get('model_name')
            )
        
        if generator_model_config:
            generator_llm = LLMClient(
                base_url=generator_model_config.get('url'),
                api_key=generator_model_config.get('api_key'),
                model_name=generator_model_config.get('model_name')
            )
        
        # Create and return service
        service = EnhancedS3RAGServiceV2(
            ragflow_client=streaming_client,
            search_llm_client=search_llm,
            generator_llm_client=generator_llm
        )
        
        logger.info("Created EnhancedS3RAGServiceV2 with StreamingRAGFlowClient")
        return service
    
    @staticmethod
    def create_sdk_s3_service(
        ragflow_api_url: str = None,
        ragflow_api_key: str = None,
        search_model_config: dict = None,
        generator_model_config: dict = None
    ) -> Union[EnhancedS3RAGService, EnhancedS3RAGServiceV2]:
        """
        Create Enhanced S3 RAG Service with SDK wrapper (if available)
        
        Args:
            ragflow_api_url: RAGFlow API URL
            ragflow_api_key: RAGFlow API key
            search_model_config: Search model configuration
            generator_model_config: Generator model configuration
            
        Returns:
            EnhancedS3RAGService or EnhancedS3RAGServiceV2 instance with SDK client
        """
        if not SDK_AVAILABLE:
            raise ImportError("RAGFlow SDK not available. Use create_streaming_s3_service instead.")
        
        # Use environment variables as defaults
        api_url = ragflow_api_url or os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        api_key = ragflow_api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not api_key:
            raise ValueError("RAGFlow API key is required")
        
        # Create SDK wrapper client
        sdk_client = RAGFlowSDKWrapper(api_url, api_key)
        
        # Create LLM clients
        search_llm = None
        generator_llm = None
        
        if search_model_config:
            search_llm = LLMClient(
                base_url=search_model_config.get('url'),
                api_key=search_model_config.get('api_key'),
                model_name=search_model_config.get('model_name')
            )
        
        if generator_model_config:
            generator_llm = LLMClient(
                base_url=generator_model_config.get('url'),
                api_key=generator_model_config.get('api_key'),
                model_name=generator_model_config.get('model_name')
            )
        
        # Create and return V2 service (supports both SDK and streaming)
        service = EnhancedS3RAGServiceV2(
            ragflow_client=sdk_client,
            search_llm_client=search_llm,
            generator_llm_client=generator_llm
        )
        
        logger.info("Created EnhancedS3RAGServiceV2 with RAGFlowSDKWrapper")
        return service
    
    @staticmethod
    def create_http_s3_service(
        ragflow_api_url: str = None,
        ragflow_api_key: str = None,
        search_model_config: dict = None,
        generator_model_config: dict = None
    ) -> EnhancedS3RAGService:
        """
        Create Enhanced S3 RAG Service with HTTP client (legacy)
        
        Args:
            ragflow_api_url: RAGFlow API URL
            ragflow_api_key: RAGFlow API key
            search_model_config: Search model configuration
            generator_model_config: Generator model configuration
            
        Returns:
            EnhancedS3RAGService instance with HTTP client
        """
        # Use environment variables as defaults
        api_url = ragflow_api_url or os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
        api_key = ragflow_api_key or os.getenv("RAGFLOW_API_KEY")
        
        if not api_key:
            raise ValueError("RAGFlow API key is required")
        
        # Create HTTP client
        http_client = RAGFlowClient(api_url, api_key)
        
        # Create LLM clients
        search_llm = None
        generator_llm = None
        
        if search_model_config:
            search_llm = LLMClient(
                base_url=search_model_config.get('url'),
                api_key=search_model_config.get('api_key'),
                model_name=search_model_config.get('model_name')
            )
        
        if generator_model_config:
            generator_llm = LLMClient(
                base_url=generator_model_config.get('url'),
                api_key=generator_model_config.get('api_key'),
                model_name=generator_model_config.get('model_name')
            )
        
        # Create and return service
        service = EnhancedS3RAGService(
            ragflow_client=http_client,
            search_llm_client=search_llm,
            generator_llm_client=generator_llm
        )
        
        logger.info("Created EnhancedS3RAGService with RAGFlowClient")
        return service
    
    @staticmethod
    def create_best_available_service(
        ragflow_api_url: str = None,
        ragflow_api_key: str = None,
        search_model_config: dict = None,
        generator_model_config: dict = None,
        prefer_streaming: bool = True
    ) -> Union[EnhancedS3RAGService, EnhancedS3RAGServiceV2]:
        """
        Create the best available S3 RAG service based on what's installed
        
        Args:
            ragflow_api_url: RAGFlow API URL
            ragflow_api_key: RAGFlow API key
            search_model_config: Search model configuration
            generator_model_config: Generator model configuration
            prefer_streaming: Whether to prefer streaming client over SDK
            
        Returns:
            Best available RAG service instance
        """
        try:
            if prefer_streaming:
                # Try streaming client first
                return RAGServiceFactory.create_streaming_s3_service(
                    ragflow_api_url, ragflow_api_key, 
                    search_model_config, generator_model_config
                )
            elif SDK_AVAILABLE:
                # Try SDK client
                return RAGServiceFactory.create_sdk_s3_service(
                    ragflow_api_url, ragflow_api_key, 
                    search_model_config, generator_model_config
                )
            else:
                # Fallback to streaming
                return RAGServiceFactory.create_streaming_s3_service(
                    ragflow_api_url, ragflow_api_key, 
                    search_model_config, generator_model_config
                )
        except Exception as e:
            logger.warning(f"Failed to create preferred service: {e}")
            # Ultimate fallback to HTTP client
            return RAGServiceFactory.create_http_s3_service(
                ragflow_api_url, ragflow_api_key, 
                search_model_config, generator_model_config
            )

# Convenience functions
def create_streaming_service(**kwargs) -> EnhancedS3RAGServiceV2:
    """Create streaming S3 service - recommended for new deployments"""
    return RAGServiceFactory.create_streaming_s3_service(**kwargs)

def create_sdk_service(**kwargs) -> Union[EnhancedS3RAGService, EnhancedS3RAGServiceV2]:
    """Create SDK-based S3 service - for official SDK users"""
    return RAGServiceFactory.create_sdk_s3_service(**kwargs)

def create_best_service(**kwargs) -> Union[EnhancedS3RAGService, EnhancedS3RAGServiceV2]:
    """Create best available S3 service - automatic selection"""
    return RAGServiceFactory.create_best_available_service(**kwargs)