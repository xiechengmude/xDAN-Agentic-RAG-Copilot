"""
项目配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# RAGFlow API 配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL", "http://150.109.16.195:7080")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "ragflow-g4ZWE3OTNhNDUxYTExZjA4MTljMDI0Mm")

# S3框架模型配置
# Search Model - 用于S3框架中的搜索决策
S3_SEARCH_MODEL_NAME = os.getenv("S3_SEARCH_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")
S3_SEARCH_MODEL_URL = os.getenv("S3_SEARCH_MODEL_URL", "http://51.159.189.105:7032/v1")
S3_SEARCH_API_KEY = os.getenv("S3_SEARCH_MODEL_API_KEY", "")  # 注意环境变量名

# Generator Model - 用于最终答案生成
S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME", "xDAN-R2-Qwen3-14b-RagRL-step450-0618")
S3_GENERATOR_MODEL_URL = os.getenv("S3_GENERATOR_API_BASE", os.getenv("S3_GENERATOR_MODEL_URL", "http://51.159.189.105:7032/v1"))
S3_GENERATOR_API_KEY = os.getenv("S3_GENERATOR_API_KEY", "")

# 向后兼容的别名
LLM_API_URL = S3_GENERATOR_MODEL_URL
LLM_MODEL_NAME = S3_GENERATOR_MODEL_NAME

# 默认数据集
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID", "7e8d9e924cde11f0afc90242ac140006")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))