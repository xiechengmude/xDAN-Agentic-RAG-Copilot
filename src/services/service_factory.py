#!/usr/bin/env python3
"""
服务工厂模式
创建S3服务实例
"""

import logging
from typing import Dict, Any, Optional
from src.core.config_loader import get_config
from src.services.s3_service import S3Service, create_s3_service

logger = logging.getLogger(__name__)

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
            full_config = get_config()
            ragflow_config = full_config.get_ragflow_config()
            
            config = {
                'ragflow_api_url': ragflow_config.get('api_url'),
                'ragflow_api_key': ragflow_config.get('api_key'),
                'default_dataset_id': ragflow_config.get('default_dataset_id')
            }
        
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
    return ServiceFactory.create_default_service()