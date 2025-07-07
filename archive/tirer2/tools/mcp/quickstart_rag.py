#!/usr/bin/env python3
"""
RAG Tool Service 快速开始脚本
帮助在新项目中快速集成RAG工具检索服务
"""

import os
import sys
import json
import logging
from pathlib import Path

# 假设已经复制了 rag_mcp_service_standalone.py
try:
    from rag_mcp_service_standalone import RAGMCPService, RAGMCPConfig
except ImportError:
    print("错误: 找不到 rag_mcp_service_standalone.py")
    print("请确保已将该文件复制到当前目录")
    sys.exit(1)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """设置环境变量（如果还没有设置）"""
    env_vars = {
        "RAG_EMBEDDING_MODEL": "bge-m3",
        "RAG_EMBEDDING_URL": "http://159.54.182.15:8001",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333"
    }
    
    logger.info("检查环境变量...")
    for key, default_value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            logger.info(f"设置 {key} = {default_value}")
        else:
            logger.info(f"{key} = {os.getenv(key)}")


def create_sample_tools_data():
    """创建示例工具数据文件"""
    sample_data = {
        "metadata": {
            "total_tools": 3,
            "format_version": "1.0",
            "description": "示例工具数据"
        },
        "tools": [
            {
                "tool_name": "example_search_tool",
                "description": "搜索互联网信息的示例工具，支持关键词搜索和语义搜索",
                "category": "搜索工具",
                "related_tools": ["example_fetch_tool"],
                "full_metadata": {
                    "parameters": ["query"],
                    "returns": "search results"
                }
            },
            {
                "tool_name": "example_fetch_tool",
                "description": "获取网页内容的示例工具，支持HTML解析和内容提取",
                "category": "数据获取",
                "related_tools": ["example_search_tool"],
                "full_metadata": {
                    "parameters": ["url"],
                    "returns": "webpage content"
                }
            },
            {
                "tool_name": "example_chart_tool",
                "description": "生成图表的示例工具，支持折线图、柱状图、饼图等多种图表类型",
                "category": "图表可视化",
                "related_tools": [],
                "full_metadata": {
                    "parameters": ["data", "chart_type"],
                    "returns": "chart image"
                }
            }
        ]
    }
    
    # 保存到文件
    sample_file = "sample_tools.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"创建示例工具数据文件: {sample_file}")
    return sample_file


def test_basic_functionality():
    """测试基本功能"""
    logger.info("\n" + "="*60)
    logger.info("测试RAG服务基本功能")
    logger.info("="*60)
    
    # 创建配置
    config = RAGMCPConfig(
        embedding_api_url=os.getenv("RAG_EMBEDDING_URL", "http://159.54.182.15:8001"),
        embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "bge-m3"),
        qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
        qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
        collection_name="quickstart_tools_collection"
    )
    
    # 创建服务
    try:
        service = RAGMCPService(config)
        logger.info("✅ RAG服务创建成功")
    except Exception as e:
        logger.error(f"❌ 创建服务失败: {e}")
        return None
        
    # 健康检查
    health = service.health_check()
    logger.info(f"健康检查结果: {health}")
    
    if not health["qdrant"]:
        logger.error("❌ Qdrant未连接，请确保Qdrant服务正在运行")
        logger.info("提示: docker run -p 6333:6333 qdrant/qdrant")
        return None
        
    if not health["embedding"]:
        logger.error("❌ Embedding服务不可用")
        return None
        
    return service


def index_sample_data(service, data_file):
    """索引示例数据"""
    logger.info("\n" + "="*60)
    logger.info("索引示例工具数据")
    logger.info("="*60)
    
    success = service.index_tools(data_file)
    if success:
        logger.info("✅ 索引创建成功")
        
        # 显示集合信息
        info = service.get_collection_info()
        if info:
            logger.info(f"集合信息:")
            logger.info(f"  名称: {info['name']}")
            logger.info(f"  工具数: {info['points_count']}")
            logger.info(f"  向量维度: {info['vector_size']}")
    else:
        logger.error("❌ 索引创建失败")
        
    return success


def test_search_functionality(service):
    """测试搜索功能"""
    logger.info("\n" + "="*60)
    logger.info("测试搜索功能")
    logger.info("="*60)
    
    test_queries = [
        "搜索信息",
        "获取网页内容",
        "生成图表",
        "数据可视化"
    ]
    
    for query in test_queries:
        logger.info(f"\n查询: '{query}'")
        results = service.search_tools_by_intent(query, top_k=3)
        
        if results:
            logger.info(f"找到 {len(results)} 个相关工具:")
            for i, tool in enumerate(results):
                logger.info(f"  {i+1}. {tool.tool_name}")
                logger.info(f"     分数: {tool.score:.3f}")
                logger.info(f"     类别: {tool.category}")
        else:
            logger.info("未找到相关工具")


def generate_integration_code():
    """生成集成代码示例"""
    logger.info("\n" + "="*60)
    logger.info("集成代码示例")
    logger.info("="*60)
    
    code = '''
# 在你的项目中使用RAG工具服务

from rag_mcp_service_standalone import RAGMCPService, RAGMCPConfig

# 1. 创建服务实例
config = RAGMCPConfig(
    collection_name="your_project_tools"
)
rag_service = RAGMCPService(config)

# 2. 在LLM决策前搜索相关工具
def get_relevant_tools(user_query: str, all_tools: list) -> list:
    """根据用户查询获取相关工具"""
    # 使用RAG搜索
    search_results = rag_service.search_tools_by_intent(
        query=user_query,
        top_k=30
    )
    
    # 匹配实际工具对象
    relevant_tools = []
    for result in search_results:
        tool = next((t for t in all_tools if t.name == result.tool_name), None)
        if tool:
            relevant_tools.append(tool)
    
    return relevant_tools

# 3. 在Agent中使用
class YourAgent:
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.all_tools = load_all_tools()  # 你的工具加载逻辑
        
    async def process_query(self, query: str):
        # 获取相关工具而不是全部工具
        relevant_tools = get_relevant_tools(query, self.all_tools)
        
        # 让LLM从相关工具中选择
        selected_tool = await self.llm_select_tool(query, relevant_tools)
        
        # 执行工具
        result = await selected_tool.execute()
        return result
'''
    
    logger.info("示例代码:")
    print(code)
    
    # 保存到文件
    with open("integration_example.py", 'w', encoding='utf-8') as f:
        f.write(code)
    logger.info("\n代码已保存到: integration_example.py")


def main():
    """主函数"""
    logger.info("RAG Tool Service 快速开始")
    logger.info("="*60)
    
    try:
        # 1. 设置环境
        setup_environment()
        
        # 2. 测试基本功能
        service = test_basic_functionality()
        if not service:
            logger.error("基础测试失败，请检查环境配置")
            return
            
        # 3. 创建示例数据
        sample_file = create_sample_tools_data()
        
        # 4. 询问是否索引示例数据
        response = input("\n是否索引示例数据？(y/n): ")
        if response.lower() == 'y':
            if index_sample_data(service, sample_file):
                # 5. 测试搜索
                test_search_functionality(service)
        
        # 6. 生成集成代码
        generate_integration_code()
        
        logger.info("\n" + "="*60)
        logger.info("快速开始完成！")
        logger.info("下一步:")
        logger.info("1. 准备你的工具数据文件 (参考 sample_tools.json)")
        logger.info("2. 使用 service.index_tools() 创建索引")
        logger.info("3. 在项目中集成 RAG 搜索功能")
        logger.info("4. 参考 RAG_TOOL_MIGRATION_GUIDE.md 了解更多")
        
    except Exception as e:
        logger.error(f"发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()