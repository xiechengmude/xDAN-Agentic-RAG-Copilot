"""
项目常量定义
这些常量应该在必要时从环境变量中读取
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 确保加载正确的.env文件
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(env_path)

# 默认的嵌入模型配置
DEFAULT_EMBEDDING_MODEL = os.getenv("DEFAULT_EMBEDDING_MODEL", "BAAI/bge-m3@SILICONFLOW")
DEFAULT_CHUNK_METHOD = os.getenv("DEFAULT_CHUNK_METHOD", "naive")

# 默认的解析配置
DEFAULT_PARSER_CONFIG = {
    "chunk_token_num": int(os.getenv("CHUNK_TOKEN_NUM", "512")),
    "delimiter": os.getenv("CHUNK_DELIMITER", "\n"),
    "auto_keywords": int(os.getenv("AUTO_KEYWORDS", "0")),
    "auto_questions": int(os.getenv("AUTO_QUESTIONS", "0"))
}

# 检索相关配置
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))
DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.3"))
DEFAULT_MAX_ROUNDS = int(os.getenv("DEFAULT_MAX_ROUNDS", "3"))

# 页面大小配置
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "30"))