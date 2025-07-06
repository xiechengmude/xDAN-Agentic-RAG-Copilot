#!/usr/bin/env python3
"""
服务工厂模式
创建S3服务实例
"""

import os
import logging
from typing import Dict, Any, Optional
from src.core.config_loader import get_config
from src.services.s3_service import S3Service, create_s3_service

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), logging.INFO))

class ServiceFactory:
    """服务工厂类"""
    
    @staticmethod
    def create_s3_service(config: Optional[Dict[str, Any]] = None) -> S3Service:
        """
        创建S3服务实例
        
        Args:
            config: 配置字典，如果为None则从配置文件加载
            
        Returns:
            S3Service实例
        """
        if config is None:
            # 从配置文件加载
            logger.info(f"[S3_TRACE] Loading config from file")
            full_config = get_config()
            ragflow_config = full_config.get_ragflow_config()
            logger.info(f"[S3_TRACE] RAGFlow config loaded: {list(ragflow_config.keys())}")
            
            config = {
                'ragflow_api_url': ragflow_config.get('api_url'),
                'ragflow_api_key': ragflow_config.get('api_key'),
                'default_dataset_id': ragflow_config.get('default_dataset_id')
            }
            logger.info(f"[S3_TRACE] Config prepared: api_url={config.get('ragflow_api_url')}")
            logger.info(f"[S3_TRACE] Config prepared: api_key exists={bool(config.get('ragflow_api_key'))}")
            logger.info(f"[S3_TRACE] Config prepared: default_dataset_id={config.get('default_dataset_id')}")
        
        logger.info("创建S3服务实例")
        return create_s3_service(config)
    
    @staticmethod
    def create_default_service() -> S3Service:
        """
        使用默认配置创建S3服务
        
        Returns:
            S3Service实例
        """
        return ServiceFactory.create_s3_service()

# 便捷函数
def get_s3_service(config: Optional[Dict[str, Any]] = None) -> S3Service:
    """获取S3服务实例"""
    return ServiceFactory.create_s3_service(config)

def get_default_service() -> S3Service:
    """获取默认配置的S3服务"""
    logger.info(f"[S3_TRACE] get_default_service called")
    
    # 记录环境变量
    import os
    logger.info(f"[S3_TRACE] LITELLM_API_BASE: {os.getenv('LITELLM_API_BASE', 'not set')}")
    logger.info(f"[S3_TRACE] LITELLM_API_KEY exists: {bool(os.getenv('LITELLM_API_KEY'))}")
    logger.info(f"[S3_TRACE] RAGFLOW_API_URL: {os.getenv('RAGFLOW_API_URL', 'not set')}")
    logger.info(f"[S3_TRACE] RAGFLOW_API_KEY exists: {bool(os.getenv('RAGFLOW_API_KEY'))}")
    
    try:
        service = ServiceFactory.create_default_service()
        logger.info(f"[S3_TRACE] S3Service instance created: {service}")
        return service
    except Exception as e:
        logger.error(f"[S3_TRACE] Failed to create S3 service: {e}", exc_info=True)
        raise