# RAG Tool Service 迁移指南

本指南说明如何将RAG工具检索服务迁移到其他项目。

## 1. 服务概述

RAG Tool Service 是一个基于向量检索的工具智能选择系统，通过语义搜索从180+个工具中精准召回最相关的30个工具，大幅提升LLM的工具选择准确率。

### 核心功能
- 工具向量化索引（BGE-M3模型）
- 语义相似度搜索
- 智能图表工具检测
- 类别过滤支持

## 2. 环境依赖

### 2.1 Python依赖
```bash
pip install qdrant-client>=1.7.0
pip install requests>=2.31.0
pip install numpy>=1.24.0
```

### 2.2 外部服务

#### Qdrant向量数据库
```bash
# Docker方式启动
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

#### Embedding服务
- URL: `http://159.54.182.15:8001` (或自建服务)
- 模型: BGE-M3
- 维度: 1024

### 2.3 环境变量配置
在项目的`.env`文件中添加：
```bash
# RAG Embedding服务
RAG_EMBEDDING_MODEL=bge-m3
RAG_EMBEDDING_URL=http://159.54.182.15:8001

# Qdrant配置（复用MEM0配置或独立配置）
MEM0_VECTOR_STORE_HOST=localhost
MEM0_VECTOR_STORE_PORT=6333
```

## 3. 文件迁移清单

### 3.1 核心服务文件
```bash
# RAG MCP服务主文件
src/core/agent/multi_agent/rag_mcp_service.py

# RAG增强工具层（可选，用于集成）
src/core/agent/multi_agent/v117/rag_enhanced_tool_layer.py

# CLI工具（可选，用于管理）
src/core/tools/mcp/rag_mcp_cli.py
```

### 3.2 数据文件
```bash
# 工具数据（必需）
data/mcp/tools_rag_ready.json
```

### 3.3 最小化迁移
如果只需要RAG检索功能，只需复制：
1. `rag_mcp_service.py`
2. `tools_rag_ready.json`

## 4. 集成步骤

### 4.1 基础使用
```python
from rag_mcp_service import RAGMCPService, RAGMCPConfig

# 创建服务
rag_service = RAGMCPService()

# 搜索工具
results = rag_service.search_tools_by_intent(
    query="获取股票实时行情",
    top_k=30
)

# 处理结果
for tool in results[:10]:
    print(f"{tool.tool_name}: {tool.score:.3f}")
```

### 4.2 自定义配置
```python
# 使用自定义配置
config = RAGMCPConfig(
    embedding_api_url="your_embedding_url",
    embedding_model="your_model",
    qdrant_host="your_qdrant_host",
    qdrant_port=6333,
    collection_name="your_collection_name"
)

rag_service = RAGMCPService(config)
```

### 4.3 与LangChain集成
```python
# 使用RAG增强工具层
from rag_enhanced_tool_layer import create_rag_enhanced_tool_layer

# 创建RAG增强的工具层
rag_tool_layer = await create_rag_enhanced_tool_layer(
    rag_service=rag_service,
    top_k=30
)

# 根据查询获取相关工具
tools = await rag_tool_layer.search_tools_for_query(query)
```

## 5. 数据准备与索引

### 5.1 工具数据格式
`tools_rag_ready.json` 格式示例：
```json
{
  "metadata": {
    "total_tools": 181,
    "format_version": "1.0"
  },
  "tools": [
    {
      "tool_name": "tushareMcp_get_stock_basic_info",
      "description": "获取股票基本信息...",
      "category": "股票数据",
      "related_tools": ["tushareMcp_search_stocks"],
      "full_metadata": {...}
    }
  ]
}
```

### 5.2 创建索引
```bash
# 使用CLI工具
python rag_mcp_cli.py index --data-file data/mcp/tools_rag_ready.json

# 或在代码中
rag_service.index_tools("path/to/tools_rag_ready.json")
```

### 5.3 验证索引
```bash
# 检查服务状态
python rag_mcp_cli.py check

# 查看统计信息
python rag_mcp_cli.py stats

# 测试搜索
python rag_mcp_cli.py search "获取股票信息"
```

## 6. 高级功能

### 6.1 图表工具自动检测
系统会自动检测查询中的图表关键词，优先返回图表相关工具：
```python
# 这些查询会触发图表工具优先
"生成K线图"
"画柱状图"
"技术分析图表"
```

### 6.2 类别过滤
```python
# 只搜索特定类别的工具
results = rag_service.search_tools_by_intent(
    query="财务分析",
    category_filter="股票数据"
)
```

### 6.3 相关工具推荐
每个工具结果包含相关工具列表，可用于扩展搜索。

## 7. 性能优化

### 7.1 批量处理
对于多个查询，建议批量获取embedding以提高效率。

### 7.2 缓存策略
可以在应用层实现查询结果缓存：
```python
import functools

@functools.lru_cache(maxsize=1000)
def cached_search(query: str) -> List[ToolSearchResult]:
    return rag_service.search_tools_by_intent(query)
```

### 7.3 索引优化
- 定期重建索引以包含新工具
- 根据使用统计优化工具描述

## 8. 故障排查

### 8.1 常见问题

1. **Qdrant连接失败**
   - 检查Qdrant服务是否运行
   - 验证端口是否正确（默认6333）

2. **Embedding服务错误**
   - 验证API URL是否可访问
   - 检查模型名称是否正确

3. **搜索结果不准确**
   - 检查工具描述质量
   - 调整score_threshold参数
   - 考虑重新生成embedding

### 8.2 调试模式
```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
```

## 9. 迁移检查清单

- [ ] 安装Python依赖
- [ ] 启动Qdrant服务
- [ ] 配置环境变量
- [ ] 复制必要文件
- [ ] 创建工具索引
- [ ] 运行测试验证
- [ ] 集成到目标系统

## 10. 测试验证

创建简单测试脚本验证迁移成功：

```python
# test_rag_migration.py
from rag_mcp_service import RAGMCPService

def test_rag_service():
    # 创建服务
    service = RAGMCPService()
    
    # 健康检查
    health = service.health_check()
    print(f"健康检查: {health}")
    
    # 测试搜索
    results = service.search_tools_by_intent("获取股票信息", top_k=5)
    print(f"找到 {len(results)} 个工具")
    
    for tool in results:
        print(f"- {tool.tool_name}: {tool.score:.3f}")

if __name__ == "__main__":
    test_rag_service()
```

## 联系支持

如有问题，请参考：
- 原项目文档：`docs/当前架构/RAG工具集成方案.md`
- 测试示例：`tests/v1.1.7/test_rag_simple.py`

---

最后更新：2025-01-06