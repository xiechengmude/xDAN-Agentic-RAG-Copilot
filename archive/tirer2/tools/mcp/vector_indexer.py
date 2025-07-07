#!/usr/bin/env python3
"""
ProFlow向量索引器
负责将本地数据索引到Qdrant向量数据库
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import click
from datetime import datetime

# 向量化相关
try:
    import requests
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    import redis
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 缺少依赖 {e}")
    DEPENDENCIES_AVAILABLE = False


class MockEmbeddingService:
    """模拟Embedding服务（用于测试）"""
    
    def __init__(self):
        import random
        self.dimension = 1024  # 更新为bge-m3模型维度
        random.seed(42)  # 固定种子确保可重现
    
    def embed_text(self, text: str) -> List[float]:
        """生成模拟向量"""
        import random
        # 基于文本内容生成相对稳定的向量
        hash_val = hash(text) % 1000000
        random.seed(hash_val)
        return [random.uniform(-1, 1) for _ in range(self.dimension)]


class VectorIndexer:
    """向量索引器"""
    
    def __init__(
        self,
            qdrant_host: str = "qdrant",
            qdrant_port: int = 6333,
            redis_host: str = "redis",
            redis_port: int = 6379,
            embedding_url: str = "http://159.54.182.15:8001",
            embedding_model: str = "bge-m3",
            use_mock_embedding: bool = False
    ):
        self.qdrant_host = qdrant_host
        self.qdrant_port = qdrant_port
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.embedding_url = embedding_url
        self.embedding_model = embedding_model
        self.use_mock_embedding = use_mock_embedding
        
        # 初始化服务连接
        self.qdrant_client = None
        self.redis_client = None
        self.embedding_service = None
        
    def check_dependencies(self) -> tuple[bool, str]:
        """检查依赖"""
        if not DEPENDENCIES_AVAILABLE:
            return False, "缺少必要依赖：pip install qdrant-client redis requests"
        return True, "依赖检查通过"
    
    def check_services(self) -> Dict[str, bool]:
        """检查服务状态"""
        status = {
            'qdrant': False,
            'redis': False,
            'embedding': False
        }
        
        # 检查Qdrant
        try:
            client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
            collections = client.get_collections()
            status['qdrant'] = True
            print(f"✅ Qdrant连接成功 ({self.qdrant_host}:{self.qdrant_port})")
        except Exception as e:
            print(f"❌ Qdrant连接失败: {e}")
        
        # 检查Redis
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            r.ping()
            status['redis'] = True
            print(f"✅ Redis连接成功 ({self.redis_host}:{self.redis_port})")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
        
        # 检查Embedding服务
        if self.use_mock_embedding:
            status['embedding'] = True
            print("✅ 使用模拟Embedding服务")
        elif self.embedding_url:
            try:
                # 检查健康状态
                response = requests.get(f"{self.embedding_url}/health", timeout=5)
                if response.status_code == 200:
                    # 检查可用模型
                    models_response = requests.get(f"{self.embedding_url}/models", timeout=5)
                    if models_response.status_code == 200:
                        models_data = models_response.json()
                        embed_models = [m['id'] for m in models_data['data'] if 'embed' in m.get('capabilities', [])]
                        status['embedding'] = True
                        print(f"✅ Infinity Embedding服务连接成功 ({self.embedding_url})")
                        print(f"   可用模型: {', '.join(embed_models)}")
                    else:
                        print(f"❌ 无法获取模型列表")
                else:
                    print(f"❌ 服务健康检查失败")
            except Exception as e:
                print(f"❌ Embedding服务连接失败: {e}")
        else:
            print("⚠️  未配置Embedding服务，将使用模拟服务")
            status['embedding'] = True
        
        return status
    
    def initialize_services(self):
        """初始化服务连接"""
        # Qdrant
        self.qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)
        
        # Redis
        self.redis_client = redis.Redis(
            host=self.redis_host, 
            port=self.redis_port, 
            decode_responses=True
        )
        
        # Embedding服务
        if self.use_mock_embedding or not self.embedding_url:
            self.embedding_service = MockEmbeddingService()
        else:
            self.embedding_service = InfinityEmbeddingService(self.embedding_url, self.embedding_model)
    
    def create_collection(self, collection_name: str, dimension: int = 1024):
        """创建向量集合"""
        try:
            # 检查集合是否存在
            try:
                self.qdrant_client.get_collection(collection_name)
                print(f"集合 {collection_name} 已存在")
                return True
            except:
                pass
            
            # 创建新集合
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )
            print(f"✅ 创建集合: {collection_name}")
            return True
            
        except Exception as e:
            print(f"❌ 创建集合失败: {e}")
            return False
    
    def load_domain_data(self, domain: str) -> Optional[Dict[str, Any]]:
        """加载领域数据"""
        data_dir = Path("data/proflow") / domain
        metadata_file = data_dir / "metadata.json"
        
        if not metadata_file.exists():
            return None
        
        # 加载元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 查找数据文件
        json_files = [f for f in data_dir.glob("*.json") if f.name != "metadata.json"]
        if not json_files:
            return None
        
        # 加载数据
        with open(json_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'metadata': metadata,
            'data': data
        }
    
    def extract_questions(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取问题列表"""
        questions = []
        
        # 查找问题集合
        questions_key = None
        for key in data.keys():
            if key.endswith('问题集') or '问题集' in key:
                questions_key = key
                break
        
        if not questions_key:
            return questions
        
        raw_questions = data[questions_key]
        
        for q in raw_questions:
            # 构建索引文本（用于向量化）
            index_texts = []
            
            # 主问题
            main_question = q.get('问题', '')
            index_texts.append(main_question)
            
            # 相似问题
            extensions = q.get('问题场景扩展', {})
            similar_questions = extensions.get('同类相近问题', [])
            index_texts.extend(similar_questions)
            
            # 场景特征
            scene_features = extensions.get('场景特征', {})
            for feature_type, features in scene_features.items():
                if isinstance(features, list):
                    index_texts.extend([str(f) for f in features])
                else:
                    index_texts.append(str(features))
            
            # 用户意图
            user_intents = extensions.get('用户意图识别', {})
            for intent_type, intent_data in user_intents.items():
                if isinstance(intent_data, dict):
                    if '描述' in intent_data:
                        index_texts.append(intent_data['描述'])
                    if '关键词' in intent_data:
                        index_texts.extend(intent_data['关键词'])
            
            # 合并文本
            combined_text = ' '.join(index_texts)
            
            questions.append({
                'id': q.get('index', 0),
                'question': main_question,
                'category': q.get('定位', ''),
                'combined_text': combined_text,
                'similar_questions': similar_questions,
                'thinking_chain': q.get('优化后工具思维链', {}),
                'raw_data': q
            })
        
        return questions
    
    def index_domain(self, domain: str, batch_size: int = 10) -> bool:
        """索引指定领域"""
        print(f"\n开始索引领域: {domain}")
        
        # 加载数据
        domain_data = self.load_domain_data(domain)
        if not domain_data:
            print(f"❌ 未找到领域 {domain} 的数据")
            return False
        
        # 提取问题
        questions = self.extract_questions(domain_data['data'])
        if not questions:
            print(f"❌ 未找到可索引的问题")
            return False
        
        print(f"📊 找到 {len(questions)} 个问题")
        
        # 确定集合名称
        collection_name = domain_data['metadata'].get('collection', f'proflow_{domain}')
        
        # 创建集合
        dimension = getattr(self.embedding_service, 'dimension', 1024)
        if not self.create_collection(collection_name, dimension):
            return False
        
        # 批量处理（优化版本，使用批量embedding）
        success_count = 0
        failed_count = 0
        
        for i in range(0, len(questions), batch_size):
            batch = questions[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(questions) + batch_size - 1)//batch_size
            
            print(f"处理批次 {batch_num}/{total_batches} ({len(batch)}个问题)")
            
            try:
                # 批量生成向量
                batch_texts = [q['combined_text'] for q in batch]
                
                if hasattr(self.embedding_service, 'embed_batch'):
                    # 使用批量接口
                    batch_vectors = self.embedding_service.embed_batch(batch_texts)
                else:
                    # 逐个生成
                    batch_vectors = []
                    for text in batch_texts:
                        vector = self.embedding_service.embed_text(text)
                        batch_vectors.append(vector)
                
                # 构建批量点数据
                batch_points = []
                for q, vector in zip(batch, batch_vectors):
                    point = PointStruct(
                        id=q['id'],
                        vector=vector,
                        payload={
                            'question': q['question'],
                            'category': q['category'],
                            'domain': domain,
                            'similar_questions': q['similar_questions'][:5],
                            'thinking_chain_steps': q['thinking_chain'],
                            'indexed_at': datetime.now().isoformat()
                        }
                    )
                    batch_points.append(point)
                
                # 批量上传到Qdrant
                self.qdrant_client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
                
                success_count += len(batch_points)
                print(f"  ✅ 成功索引 {len(batch_points)} 个问题")
                
                # 更新Redis缓存信息
                cache_key = f"proflow:{domain}:indexed_count"
                self.redis_client.set(cache_key, success_count, ex=3600)
                
            except Exception as e:
                print(f"  ❌ 批次处理失败: {e}")
                failed_count += len(batch)
                continue
        
        print(f"\n索引完成:")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {failed_count} 个")
        print(f"  集合: {collection_name}")
        
        # 更新元数据
        self._update_index_metadata(domain, collection_name, success_count)
        
        return success_count > 0
    
    def _update_index_metadata(self, domain: str, collection_name: str, indexed_count: int):
        """更新索引元数据"""
        data_dir = Path("data/proflow") / domain
        metadata_file = data_dir / "metadata.json"
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata.update({
                'indexed': True,
                'indexed_at': datetime.now().isoformat(),
                'indexed_count': indexed_count,
                'vector_collection': collection_name
            })
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"更新元数据失败: {e}")
    
    def test_search(self, domain: str, query: str, top_k: int = 5):
        """测试搜索功能"""
        print(f"\n测试搜索: {query}")
        
        # 加载元数据
        domain_data = self.load_domain_data(domain)
        if not domain_data:
            print(f"❌ 未找到领域数据")
            return
        
        collection_name = domain_data['metadata'].get('vector_collection', f'proflow_{domain}')
        
        try:
            # 生成查询向量
            query_vector = self.embedding_service.embed_text(query)
            
            # 搜索
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=top_k
            )
            
            print(f"找到 {len(search_results)} 个结果:")
            for i, result in enumerate(search_results, 1):
                print(f"{i}. {result.payload['question']}")
                print(f"   相似度: {result.score:.3f}")
                print(f"   分类: {result.payload['category']}")
                print()
                
        except Exception as e:
            print(f"❌ 搜索失败: {e}")


class InfinityEmbeddingService:
    """Infinity Embedding API服务"""
    
    def __init__(self, base_url: str, model: str = "bge-m3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.dimension = None
        self._get_model_info()
    
    def _get_model_info(self):
        """获取模型信息"""
        try:
            # 测试调用获取维度
            test_response = requests.post(
                f"{self.base_url}/embeddings",
                json={
                    "model": self.model,
                    "input": ["test"]
                },
                timeout=10
            )
            test_response.raise_for_status()
            data = test_response.json()
            if data['data'] and data['data'][0]['embedding']:
                self.dimension = len(data['data'][0]['embedding'])
                print(f"📊 模型 {self.model} 向量维度: {self.dimension}")
        except Exception as e:
            print(f"⚠️  获取模型信息失败: {e}，使用默认维度1024")
            self.dimension = 1024
    
    def embed_text(self, text: str) -> List[float]:
        """调用Infinity API生成向量"""
        response = requests.post(
            f"{self.base_url}/embeddings",
            json={
                "model": self.model,
                "input": [text]
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return result['data'][0]['embedding']
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量"""
        response = requests.post(
            f"{self.base_url}/embeddings",
            json={
                "model": self.model,
                "input": texts
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return [item['embedding'] for item in result['data']]


@click.group()
def cli():
    """ProFlow向量索引工具"""
    pass

@cli.command()
@click.option('--qdrant-host', default='localhost', help='Qdrant主机')
@click.option('--qdrant-port', default=6333, help='Qdrant端口')
@click.option('--redis-host', default='localhost', help='Redis主机')
@click.option('--redis-port', default=6379, help='Redis端口')
@click.option('--embedding-url', default='http://159.54.182.15:8001', help='Embedding服务URL')
@click.option('--embedding-model', default='bge-m3', help='Embedding模型')
def check(qdrant_host, qdrant_port, redis_host, redis_port, embedding_url, embedding_model):
    """检查服务状态"""
    indexer = VectorIndexer(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        redis_host=redis_host,
        redis_port=redis_port,
        embedding_url=embedding_url,
        embedding_model=embedding_model,
        use_mock_embedding=False
    )
    
    # 检查依赖
    deps_ok, message = indexer.check_dependencies()
    print(f"依赖检查: {message}")
    
    if not deps_ok:
        return
    
    # 检查服务
    print("\n服务状态检查:")
    status = indexer.check_services()
    
    all_ok = all(status.values())
    print(f"\n整体状态: {'✅ 就绪' if all_ok else '❌ 有问题'}")

@cli.command()
@click.argument('domain')
@click.option('--qdrant-host', default='localhost', help='Qdrant主机')
@click.option('--qdrant-port', default=6333, help='Qdrant端口')
@click.option('--embedding-url', default='http://159.54.182.15:8001', help='Embedding服务URL')
@click.option('--embedding-model', default='bge-m3', help='Embedding模型')
@click.option('--mock-embedding', is_flag=True, help='使用模拟Embedding服务')
@click.option('--batch-size', default=10, help='批处理大小')
def index(domain, qdrant_host, qdrant_port, embedding_url, embedding_model, mock_embedding, batch_size):
    """索引指定领域的数据"""
    indexer = VectorIndexer(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        embedding_url=embedding_url,
        embedding_model=embedding_model,
        use_mock_embedding=mock_embedding
    )
    
    # 检查依赖
    deps_ok, message = indexer.check_dependencies()
    if not deps_ok:
        print(message)
        return
    
    # 检查服务
    status = indexer.check_services()
    required_services = ['qdrant', 'embedding']
    
    for service in required_services:
        if not status[service]:
            print(f"❌ {service} 服务不可用")
            return
    
    # 初始化服务
    indexer.initialize_services()
    
    # 开始索引
    success = indexer.index_domain(domain, batch_size)
    
    if success:
        print(f"\n🎉 领域 {domain} 索引完成！")
    else:
        print(f"\n❌ 领域 {domain} 索引失败")

@cli.command()
@click.argument('domain')
@click.argument('query')
@click.option('--top-k', default=5, help='返回结果数')
@click.option('--qdrant-host', default='localhost', help='Qdrant主机')
@click.option('--qdrant-port', default=6333, help='Qdrant端口')
@click.option('--embedding-url', default='http://159.54.182.15:8001', help='Embedding服务URL')
@click.option('--embedding-model', default='bge-m3', help='Embedding模型')
@click.option('--mock-embedding', is_flag=True, help='使用模拟Embedding服务')
def search(domain, query, top_k, qdrant_host, qdrant_port, embedding_url, embedding_model, mock_embedding):
    """测试搜索功能"""
    indexer = VectorIndexer(
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port,
        embedding_url=embedding_url,
        embedding_model=embedding_model,
        use_mock_embedding=mock_embedding
    )
    
    # 检查依赖
    deps_ok, message = indexer.check_dependencies()
    if not deps_ok:
        print(message)
        return
    
    # 初始化服务
    indexer.initialize_services()
    
    # 测试搜索
    indexer.test_search(domain, query, top_k)

if __name__ == '__main__':
    cli()