"""
服务模块
提供S3框架服务和工厂模式
"""

# Import available services
from .s3_service import S3Service, create_s3_service

# Import service factory
from .service_factory import (
    ServiceFactory,
    get_s3_service,
    get_default_service
)

__all__ = [
    # Core services
    'S3Service',
    'create_s3_service',
    
    # Factory
    'ServiceFactory',
    'get_s3_service',
    'get_default_service'
]