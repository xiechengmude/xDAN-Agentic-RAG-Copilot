#!/usr/bin/env python3
"""
RAG-MCP CLI 工具
提供数据管理、查询、测试等功能
"""

import sys
import json
import asyncio
import click
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    # 修正导入路径
    sys.path.append(str(project_root.parent.parent.parent))
    from src.core.agent.multi_agent.rag_mcp_service import RAGMCPService, RAGMCPConfig
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams
    import requests
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 缺少依赖 {e}")
    print("请安装: pip install qdrant-client redis requests")
    DEPENDENCIES_AVAILABLE = False


class RAGMCPManager:
    """RAG-MCP管理器"""
    
    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embedding_url: str = "http://159.54.182.15:8001",
        embedding_model: str = "bge-m3",
        collection_name: str = "mcp_tools_bge_m3_1024",
        embedding_dim: int = 1024
    ):
        self.config = RAGMCPConfig(
            collection_name=collection_name,
            embedding_api_url=embedding_url,
            embedding_model=embedding_model,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            embedding_dim=embedding_dim,
            redis_cache_enabled=False  # CLI不使用缓存
        )
        self.service = None
        self.qdrant_client = None
    
    def check_services(self) -> Dict[str, bool]:
        """检查服务状态"""
        status = {
            'qdrant': False,
            'embedding': False
        }
        
        # 检查Qdrant
        try:
            client = QdrantClient(host=self.config.qdrant_host, port=self.config.qdrant_port)
            collections = client.get_collections()
            status['qdrant'] = True
            click.echo(f"✅ Qdrant连接成功 ({self.config.qdrant_host}:{self.config.qdrant_port})")
        except Exception as e:
            click.echo(f"❌ Qdrant连接失败: {e}")
        
        # 检查Embedding服务
        try:
            response = requests.post(
                f"{self.config.embedding_api_url}/embeddings",
                json={
                    "input": "test",
                    "model": self.config.embedding_model
                },
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    embedding_dim = len(data["data"][0]["embedding"])
                    status['embedding'] = True
                    click.echo(f"✅ Embedding服务连接成功 ({self.config.embedding_api_url})")
                    click.echo(f"   模型: {self.config.embedding_model}, 维度: {embedding_dim}")
                else:
                    click.echo(f"❌ Embedding服务响应格式异常")
            else:
                click.echo(f"❌ Embedding服务响应异常: {response.status_code}")
        except Exception as e:
            click.echo(f"❌ Embedding服务连接失败: {e}")
        
        return status
    
    def initialize(self):
        """初始化服务"""
        self.service = RAGMCPService(self.config)
        self.qdrant_client = QdrantClient(
            host=self.config.qdrant_host,
            port=self.config.qdrant_port
        )
    
    async def search_tools(self, query: str, top_k: int = 10, category: Optional[str] = None):
        """搜索工具"""
        if not self.service:
            self.initialize()
        
        results = self.service.search_tools_by_intent(query, top_k=top_k, category_filter=category)
        
        click.echo(f"\n🔍 搜索查询: {query}")
        if category:
            click.echo(f"   类别过滤: {category}")
        click.echo(f"   返回数量: {top_k}")
        
        # 检测是否包含图表关键词
        if hasattr(self.service, '_contains_chart_keywords'):
            has_chart = self.service._contains_chart_keywords(query)
            if has_chart:
                click.echo("   ✅ 检测到图表关键词，已启用默认图表工具")
        
        click.echo(f"\n找到 {len(results)} 个工具:\n")
        
        for i, tool in enumerate(results, 1):
            # 标记默认图表工具
            is_default = tool.tool_name in getattr(self.service, 'DEFAULT_CHART_TOOLS', [])
            marker = "📊" if is_default else "  "
            
            click.echo(f"{marker} {i}. {tool.tool_name} (score: {tool.score:.3f})")
            click.echo(f"      类别: {tool.category}")
            click.echo(f"      描述: {tool.description[:100]}...")
            if tool.related_tools:
                click.echo(f"      相关工具: {', '.join(tool.related_tools[:3])}")
            click.echo()
    
    async def list_categories(self):
        """列出所有工具类别"""
        if not self.qdrant_client:
            self.initialize()
        
        try:
            # 获取所有工具
            all_tools = self.qdrant_client.scroll(
                collection_name=self.config.collection_name,
                limit=1000
            )[0]
            
            categories = {}
            for point in all_tools:
                cat = point.payload.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            click.echo("\n📊 工具类别统计:")
            click.echo("="*50)
            
            total = sum(categories.values())
            for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total) * 100
                click.echo(f"  {cat:<20} {count:>4} 个工具 ({percentage:>5.1f}%)")
            
            click.echo(f"\n总计: {total} 个工具")
            
        except Exception as e:
            click.echo(f"❌ 获取类别失败: {e}")
    
    async def get_tool_info(self, tool_name: str):
        """获取工具详细信息"""
        if not self.service:
            self.initialize()
        
        tools = self.service._get_tools_by_names([tool_name])
        
        if tools:
            tool = tools[0]
            click.echo(f"\n📦 工具详情:")
            click.echo("="*50)
            click.echo(f"名称: {tool.tool_name}")
            click.echo(f"类别: {tool.category}")
            click.echo(f"描述: {tool.description}")
            
            if tool.related_tools:
                click.echo(f"\n相关工具:")
                for rt in tool.related_tools:
                    click.echo(f"  - {rt}")
            
            # 显示完整元数据
            if tool.full_metadata:
                click.echo(f"\n元数据:")
                for key, value in tool.full_metadata.items():
                    if key not in ['tool_name', 'description', 'category', 'related_tools']:
                        click.echo(f"  {key}: {value}")
        else:
            click.echo(f"❌ 未找到工具: {tool_name}")
    
    async def index_tools(self, data_file: str, force: bool = False):
        """索引工具数据"""
        if not self.service:
            self.initialize()
        
        # 检查集合是否存在
        try:
            info = self.qdrant_client.get_collection(self.config.collection_name)
            if info and not force:
                click.echo(f"⚠️  集合 {self.config.collection_name} 已存在")
                click.echo(f"   包含 {info.points_count} 个工具")
                click.echo("   使用 --force 参数强制重新索引")
                return
        except:
            pass
        
        if force:
            click.echo(f"🗑️  删除现有集合...")
            try:
                self.qdrant_client.delete_collection(self.config.collection_name)
                click.echo("✅ 集合删除成功")
            except:
                pass
        
        click.echo(f"\n📚 开始索引工具数据...")
        click.echo(f"   数据文件: {data_file}")
        click.echo(f"   集合名称: {self.config.collection_name}")
        click.echo(f"   向量维度: {self.config.embedding_dim}")
        
        success = self.service.index_tools(data_file)
        
        if success:
            # 获取集合信息
            info = self.service.get_collection_info()
            if info:
                click.echo(f"\n✅ 索引完成!")
                click.echo(f"   工具数量: {info.get('points_count', 0)}")
                click.echo(f"   集合状态: {info.get('status', 'unknown')}")
        else:
            click.echo("❌ 索引失败")
    
    async def test_search(self):
        """测试搜索功能"""
        if not self.service:
            self.initialize()
        
        test_queries = [
            ("获取股票基本信息", 5),
            ("技术分析图表生成 K线图", 10),
            ("资金流向监控", 5),
            ("chart visualization", 5)
        ]
        
        click.echo("\n🧪 运行搜索测试...")
        click.echo("="*60)
        
        for query, top_k in test_queries:
            click.echo(f"\n测试查询: {query}")
            results = self.service.search_tools_by_intent(query, top_k=top_k)
            
            if results:
                click.echo(f"✅ 找到 {len(results)} 个结果")
                # 统计类别
                categories = {}
                for tool in results:
                    cat = tool.category
                    categories[cat] = categories.get(cat, 0) + 1
                
                click.echo("   类别分布: " + " ".join([f"{cat}({count})" for cat, count in categories.items()]))
                
                # 显示前3个结果
                for i, tool in enumerate(results[:3], 1):
                    click.echo(f"   {i}. {tool.tool_name} (score: {tool.score:.3f})")
            else:
                click.echo("❌ 未找到结果")
    
    async def show_stats(self):
        """显示统计信息"""
        if not self.qdrant_client:
            self.initialize()
        
        try:
            # 获取集合信息
            info = self.qdrant_client.get_collection(self.config.collection_name)
            
            click.echo(f"\n📊 RAG-MCP 统计信息")
            click.echo("="*50)
            click.echo(f"集合名称: {self.config.collection_name}")
            click.echo(f"工具总数: {info.points_count}")
            click.echo(f"向量维度: {info.config.params.vectors.size}")
            click.echo(f"距离度量: {info.config.params.vectors.distance}")
            
            # 默认图表工具信息
            if hasattr(RAGMCPService, 'DEFAULT_CHART_TOOLS'):
                click.echo(f"\n默认图表工具 ({len(RAGMCPService.DEFAULT_CHART_TOOLS)}个):")
                for tool in RAGMCPService.DEFAULT_CHART_TOOLS:
                    click.echo(f"  - {tool}")
            
            # 获取所有工具进行详细统计
            all_tools = self.qdrant_client.scroll(
                collection_name=self.config.collection_name,
                limit=1000
            )[0]
            
            # 统计类别
            categories = {}
            chart_tools = []
            
            for point in all_tools:
                cat = point.payload.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
                
                # 统计chart工具
                tool_name = point.payload.get('tool_name', '')
                if 'chart' in tool_name.lower():
                    chart_tools.append(tool_name)
            
            click.echo(f"\n图表工具统计:")
            click.echo(f"  总数: {len(chart_tools)} 个")
            click.echo(f"  占比: {(len(chart_tools) / info.points_count * 100):.1f}%")
            
        except Exception as e:
            click.echo(f"❌ 获取统计信息失败: {e}")


@click.group()
@click.option('--qdrant-host', default='localhost', help='Qdrant服务地址')
@click.option('--qdrant-port', default=6333, type=int, help='Qdrant服务端口')
@click.option('--embedding-url', default='http://159.54.182.15:8001', help='Embedding服务URL')
@click.option('--embedding-model', default='bge-m3', help='Embedding模型')
@click.option('--collection', default='mcp_tools_bge_m3_1024', help='集合名称')
@click.pass_context
def cli(ctx, qdrant_host, qdrant_port, embedding_url, embedding_model, collection):
    """RAG-MCP CLI 工具"""
    if not DEPENDENCIES_AVAILABLE:
        click.echo("❌ 缺少必要依赖，请安装后再试")
        ctx.exit(1)
    
    ctx.obj = RAGMCPManager(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        embedding_url=embedding_url,
        embedding_model=embedding_model,
        collection_name=collection
    )


@cli.command()
@click.pass_obj
def check(manager):
    """检查服务状态"""
    click.echo("🔍 检查服务状态...")
    status = manager.check_services()
    
    all_ok = all(status.values())
    if all_ok:
        click.echo("\n✅ 所有服务正常")
    else:
        click.echo("\n❌ 部分服务异常，请检查")


@cli.command()
@click.argument('query')
@click.option('-k', '--top-k', default=10, type=int, help='返回结果数')
@click.option('-c', '--category', help='类别过滤')
@click.pass_obj
def search(manager, query, top_k, category):
    """搜索工具"""
    asyncio.run(manager.search_tools(query, top_k, category))


@cli.command()
@click.pass_obj
def categories(manager):
    """列出所有类别"""
    asyncio.run(manager.list_categories())


@cli.command()
@click.argument('tool_name')
@click.pass_obj
def info(manager, tool_name):
    """获取工具详情"""
    asyncio.run(manager.get_tool_info(tool_name))


@cli.command()
@click.option('--data-file', default='data/mcp/tools_rag_ready.json', help='工具数据文件')
@click.option('--force', is_flag=True, help='强制重新索引')
@click.pass_obj
def index(manager, data_file, force):
    """索引工具数据"""
    data_path = Path(data_file)
    if not data_path.is_absolute():
        data_path = Path(__file__).parent.parent.parent / data_file
    
    if not data_path.exists():
        click.echo(f"❌ 数据文件不存在: {data_path}")
        return
    
    asyncio.run(manager.index_tools(str(data_path), force))


@cli.command()
@click.pass_obj
def test(manager):
    """运行测试"""
    asyncio.run(manager.test_search())


@cli.command()
@click.pass_obj
def stats(manager):
    """显示统计信息"""
    asyncio.run(manager.show_stats())


@cli.command()
@click.pass_obj
def reset(manager):
    """重置数据（删除集合）"""
    if not click.confirm("⚠️  确定要删除集合吗？这将清除所有索引数据"):
        return
    
    try:
        manager.initialize()
        manager.qdrant_client.delete_collection(manager.config.collection_name)
        click.echo(f"✅ 集合 {manager.config.collection_name} 已删除")
    except Exception as e:
        click.echo(f"❌ 删除失败: {e}")


if __name__ == "__main__":
    cli()