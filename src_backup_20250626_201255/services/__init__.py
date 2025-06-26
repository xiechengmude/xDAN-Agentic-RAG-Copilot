"""
RAGFlow Services Module
Consolidated services with streaming support and factory patterns
"""

# Import available services
from .enhanced_s3_rag_service import EnhancedS3RAGService
from .enhanced_s3_rag_service_v2_fixed import EnhancedS3RAGServiceV2, StreamingEnhancedS3Service

# Import service factory
from .service_factory import (
    RAGServiceFactory,
    create_streaming_service,
    create_sdk_service, 
    create_best_service
)

__all__ = [
    # Core services
    'EnhancedS3RAGService',
    'EnhancedS3RAGServiceV2', 
    'StreamingEnhancedS3Service',
    
    # Factory
    'RAGServiceFactory',
    'create_streaming_service',
    'create_sdk_service',
    'create_best_service'
]