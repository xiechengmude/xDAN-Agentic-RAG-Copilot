import os
import uvicorn
from dotenv import load_dotenv
from api import app

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 获取服务器配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # 启动服务器
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True  # 开发模式下启用热重载
    )
