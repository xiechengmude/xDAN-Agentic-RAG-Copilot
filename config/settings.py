"""
项目配置文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 确保加载正确的.env文件
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# RAGFlow API 配置
RAGFLOW_API_URL = os.getenv("RAGFLOW_API_URL")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY")

# S3框架模型配置
# Search Model - 用于S3框架中的搜索决策
S3_SEARCH_MODEL_NAME = os.getenv("S3_SEARCH_MODEL_NAME")
S3_SEARCH_MODEL_URL = os.getenv("S3_SEARCH_MODEL_URL")
S3_SEARCH_API_KEY = os.getenv("S3_SEARCH_MODEL_API_KEY")

# Generator Model - 用于最终答案生成
S3_GENERATOR_MODEL_NAME = os.getenv("S3_GENERATOR_MODEL_NAME")
S3_GENERATOR_MODEL_URL = os.getenv("S3_GENERATOR_API_BASE")  # 使用API_BASE作为主要配置
S3_GENERATOR_API_KEY = os.getenv("S3_GENERATOR_API_KEY")

# 向后兼容的别名
LLM_API_URL = S3_GENERATOR_MODEL_URL
LLM_MODEL_NAME = S3_GENERATOR_MODEL_NAME

# 默认数据集
DEFAULT_DATASET_ID = os.getenv("DEFAULT_DATASET_ID")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 验证必要的环境变量
_required_vars = {
    "RAGFLOW_API_URL": RAGFLOW_API_URL,
    "RAGFLOW_API_KEY": RAGFLOW_API_KEY,
    "S3_SEARCH_MODEL_NAME": S3_SEARCH_MODEL_NAME,
    "S3_SEARCH_MODEL_URL": S3_SEARCH_MODEL_URL,
    "S3_GENERATOR_MODEL_NAME": S3_GENERATOR_MODEL_NAME,
    "S3_GENERATOR_API_BASE": S3_GENERATOR_MODEL_URL,
}

_missing_vars = [var for var, value in _required_vars.items() if not value]
if _missing_vars:
    print(f"警告: 以下环境变量未设置: {', '.join(_missing_vars)}")
    print(f"请检查 .env 文件: {env_path}")