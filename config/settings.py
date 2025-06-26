"""
项目配置文件 - 基于YAML配置
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入配置加载器
try:
    from src.core.config_loader import get_config
    config = get_config()
except:
    # 如果无法加载配置，使用环境变量作为后备
    from dotenv import load_dotenv
    load_dotenv()
    config = None

# RAGFlow API 配置
if config:
    ragflow_config = config.get_ragflow_config()
    RAGFLOW_API_URL = ragflow_config.get('api_url', 'http://150.109.16.195:7080')
    RAGFLOW_API_KEY = ragflow_config.get('api_key', 'ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm')
else:
    RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
    RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")

# S3框架模型配置
if config:
    model_config = config.get_model_config()
    s3_config = model_config.get('s3_framework', {})
    llm_providers = config.get('llm_providers', {})
    
    # Search Model - 使用专门的xDAN-R2-Qwen3模型
    agent_provider = s3_config.get('agent_provider', 'xdan_search')
    xdan_config = llm_providers.get('xdan_search', {})
    
    S3_SEARCH_MODEL_NAME = s3_config.get('agent_model', 'xDAN-R2-Qwen3-14b-RagRL-step450-0618')
    S3_SEARCH_MODEL_URL = xdan_config.get('base_url', 'http://209.20.158.45:8001/v1')
    S3_SEARCH_API_KEY = xdan_config.get('api_key', 'sk-empty')
    
    # Generator Model - 使用DeepSeek通过OpenAI兼容接口
    generation_provider = s3_config.get('generation_provider', 'openai')
    openai_config = llm_providers.get('openai', {})
    
    S3_GENERATOR_MODEL_NAME = s3_config.get('generation_model', 'deepseek-chat')
    S3_GENERATOR_MODEL_URL = openai_config.get('base_url', 'http://43.134.187.48:7220/v1')
    S3_GENERATOR_API_KEY = openai_config.get('api_key', '')
else:
    # 从环境变量读取（后备）
    S3_SEARCH_MODEL_NAME = os.getenv("S3_SEARCH_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")
    S3_SEARCH_MODEL_URL = os.getenv("S3_SEARCH_MODEL_URL", "http://209.20.158.45:8001/v1")
    S3_SEARCH_API_KEY = os.getenv("S3_SEARCH_MODEL_API_KEY", "sk-empty")
    
    S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME", "deepseek-chat")
    S3_GENERATOR_MODEL_URL = os.getenv("S3_GENERATOR_API_BASE", "http://43.134.187.48:7220/v1")
    S3_GENERATOR_API_KEY = os.getenv("S3_GENERATOR_API_KEY", "")

# 向后兼容的别名
LLM_API_URL = S3_GENERATOR_MODEL_URL
LLM_MODEL_NAME = S3_GENERATOR_MODEL_NAME

# 默认数据集
if config:
    DEFAULT_DATASET_ID = config.get('ragflow.default_dataset_id', '7e8d9e924cde11f0afc90242ac140006')
else:
    DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# 服务器配置
if config:
    service_config = config.get_service_config()
    HOST = "0.0.0.0"  # 固定值
    PORT = service_config.get('rag_service_port', 8001)
else:
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))