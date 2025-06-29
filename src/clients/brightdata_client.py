"""
BrightData客户端 - 高性能异步实现
支持Google搜索、学术搜索、新闻搜索等
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Optional, Union
from urllib.parse import quote_plus, urlencode
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime
from ..core.logging_utils import get_logger

logger = logging.getLogger(__name__)
ds_logger = get_logger(__name__)


class BrightDataAsyncClient:
    """高性能异步BrightData客户端"""
    
    def __init__(self, api_key: str, zone: str = "xdan_search_searp", 
                 max_concurrent: int = 5, timeout: int = 30):
        """
        初始化BrightData客户端
        
        Args:
            api_key: BrightData API密钥
            zone: BrightData zone名称
            max_concurrent: 最大并发请求数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.zone = zone
        self.base_url = "https://api.brightdata.com/request"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session = None
        
        logger.info(f"BrightData异步客户端初始化，zone: {zone}, 最大并发: {max_concurrent}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def search(self, query: str, **kwargs) -> Dict[str, any]:
        """
        异步执行搜索
        
        Args:
            query: 搜索查询
            **kwargs: 搜索选项
                - search_type: web/news/academic/images/videos
                - num_results: 结果数量
                - date_range: 时间范围(h/d/w/m/y)
                - language: 语言代码
                - country: 国家代码
                - format: raw/json
        
        Returns:
            搜索结果字典
        """
        async with self.semaphore:
            start_time = time.time()
            
            try:
                # 构建搜索URL
                search_url = self._build_search_url(query, kwargs)
                logger.debug(f"搜索URL: {search_url}")
                
                ds_logger.log_input("BrightData搜索", {
                    "query": query,
                    "search_url": search_url,
                    "options": kwargs
                })
                
                # 准备请求数据
                data = {
                    "zone": self.zone,
                    "url": search_url,
                    "format": kwargs.get("format", "raw")
                }
                
                # 确保session存在
                if not self.session:
                    self.session = aiohttp.ClientSession(timeout=self.timeout)
                
                # 发送异步请求
                async with self.session.post(
                    self.base_url,
                    json=data,
                    headers=self.headers
                ) as response:
                    response.raise_for_status()
                    
                    # 解析响应
                    if kwargs.get("format", "raw") == "raw":
                        html = await response.text()
                        results = self._parse_google_html(html)
                    else:
                        results = await response.json()
                    
                    elapsed = time.time() - start_time
                    logger.info(f"搜索完成: {query[:50]}... 耗时: {elapsed:.2f}s, 结果数: {len(results) if isinstance(results, list) else 1}")
                    
                    ds_logger.log_output("BrightData搜索", {
                        "query": query,
                        "results_count": len(results) if isinstance(results, list) else 1,
                        "elapsed": elapsed
                    })
                    
                    return {
                        'success': True,
                        'query': query,
                        'results': results,
                        'elapsed': elapsed,
                        'search_url': search_url,
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except asyncio.TimeoutError:
                logger.error(f"搜索超时: {query}")
                return {
                    'success': False,
                    'query': query,
                    'error': 'Timeout',
                    'elapsed': time.time() - start_time
                }
            except aiohttp.ClientError as e:
                logger.error(f"网络错误: {query}, 错误: {str(e)}")
                return {
                    'success': False,
                    'query': query,
                    'error': f'Network error: {str(e)}',
                    'elapsed': time.time() - start_time
                }
            except Exception as e:
                logger.error(f"搜索错误: {query}, 错误: {str(e)}")
                ds_logger.log_error("BrightData搜索", e, query=query)
                return {
                    'success': False,
                    'query': query,
                    'error': str(e),
                    'elapsed': time.time() - start_time
                }
    
    async def batch_search(self, queries: List[str], **kwargs) -> List[Dict]:
        """
        批量异步搜索
        
        Args:
            queries: 查询列表
            **kwargs: 搜索选项（应用于所有查询）
        
        Returns:
            搜索结果列表
        """
        tasks = []
        for query in queries:
            task = self.search(query, **kwargs)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'query': queries[i],
                    'error': str(result)
                })
            else:
                processed_results.append(result)
        
        # 统计成功率
        success_count = sum(1 for r in processed_results if r.get('success'))
        logger.info(f"批量搜索完成: {success_count}/{len(queries)} 成功")
        
        return processed_results
    
    async def multi_type_search(self, query: str, search_types: List[str] = None) -> Dict[str, Dict]:
        """
        同时执行多种类型的搜索
        
        Args:
            query: 搜索查询
            search_types: 搜索类型列表，默认为['web', 'news']
        
        Returns:
            按类型组织的结果字典
        """
        if search_types is None:
            search_types = ['web', 'news']
        
        tasks = {}
        for search_type in search_types:
            tasks[search_type] = self.search(query, search_type=search_type)
        
        # 并发执行所有搜索
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 组织结果
        organized_results = {}
        for i, search_type in enumerate(search_types):
            result = results[i]
            if isinstance(result, Exception):
                organized_results[search_type] = {
                    'success': False,
                    'error': str(result),
                    'search_type': search_type
                }
            else:
                organized_results[search_type] = result
        
        return organized_results
    
    async def search_with_retry(self, query: str, max_retries: int = 3, **kwargs) -> Dict:
        """
        带重试的搜索
        
        Args:
            query: 搜索查询
            max_retries: 最大重试次数
            **kwargs: 搜索选项
        
        Returns:
            搜索结果
        """
        for attempt in range(max_retries):
            result = await self.search(query, **kwargs)
            
            if result['success']:
                return result
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 指数退避
                logger.warning(f"搜索失败，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
        
        return result  # 返回最后一次的结果
    
    def _build_search_url(self, query: str, options: dict) -> str:
        """构建Google搜索URL"""
        # URL编码查询
        encoded_query = quote_plus(query)
        
        # 基础URL选择
        search_type = options.get("search_type", "web")
        if search_type == "academic":
            base_url = f"https://scholar.google.com/scholar?q={encoded_query}"
        else:
            base_url = f"https://www.google.com/search?q={encoded_query}"
        
        # 构建参数
        params = []
        
        # 结果数量
        num = options.get("num_results", 10)
        params.append(f"num={num}")
        
        # 语言设置
        lang = options.get("language", "en")
        params.append(f"hl={lang}")
        
        # 国家/地区设置
        country = options.get("country", "US")
        params.append(f"gl={country}")
        
        # 时间范围
        date_range = options.get("date_range")
        if date_range:
            # h(小时), d(天), w(周), m(月), y(年)
            params.append(f"tbs=qdr:{date_range}")
        
        # 搜索类型特定参数
        if search_type == "news":
            params.append("tbm=nws")
        elif search_type == "images":
            params.append("tbm=isch")
        elif search_type == "videos":
            params.append("tbm=vid")
        elif search_type == "books":
            params.append("tbm=bks")
        elif search_type == "shopping":
            params.append("tbm=shop")
        
        # 安全搜索
        safe_search = options.get("safe_search", "off")
        if safe_search != "off":
            params.append(f"safe={safe_search}")
        
        # 组合完整URL
        if params:
            full_url = f"{base_url}&{'&'.join(params)}"
        else:
            full_url = base_url
            
        return full_url
    
    def _parse_google_html(self, html: str) -> List[Dict]:
        """解析Google搜索结果HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # 搜索结果的多种可能选择器
        result_selectors = [
            'div.g',  # 标准搜索结果
            'div.Gx5Zad',  # 移动版结果
            'div.kvH3mc',  # 另一种格式
            'div[data-hveid]',  # 带有data属性的结果
            'div.MjjYud'  # 新版Google结果容器
        ]
        
        # 尝试不同的选择器
        search_items = []
        for selector in result_selectors:
            search_items = soup.select(selector)
            if search_items:
                logger.debug(f"使用选择器 '{selector}' 找到 {len(search_items)} 个结果")
                break
        
        # 如果还是没找到，尝试更宽泛的搜索
        if not search_items:
            # 查找包含链接和标题的div
            search_items = soup.find_all('div', recursive=True)
            search_items = [item for item in search_items 
                           if item.find('a') and item.find('h3')][:20]
            logger.debug(f"使用宽泛搜索找到 {len(search_items)} 个潜在结果")
        
        # 解析每个搜索结果
        position = 1
        for item in search_items:
            try:
                result = self._extract_result_info(item, position)
                if result and result.get('url'):
                    results.append(result)
                    position += 1
            except Exception as e:
                logger.debug(f"解析单个结果失败: {e}")
                continue
        
        # 如果仍然没有结果，尝试解析JSON-LD数据
        if len(results) == 0:
            script_tags = soup.find_all('script', type='application/ld+json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'SearchResultsPage':
                        # 解析结构化数据
                        if 'mainEntity' in data:
                            for item in data['mainEntity']:
                                if item.get('@type') == 'WebPage':
                                    results.append({
                                        'title': item.get('name', ''),
                                        'url': item.get('url', ''),
                                        'snippet': item.get('description', ''),
                                        'position': len(results) + 1
                                    })
                except:
                    continue
        
        # 过滤掉Google内部链接
        filtered_results = []
        for result in results:
            url = result.get('url', '')
            # 跳过Google内部链接
            if url.startswith('/search') or url.startswith('/url'):
                continue
            # 确保是完整的URL
            if url.startswith('http://') or url.startswith('https://'):
                filtered_results.append(result)
        
        logger.info(f"解析完成，找到 {len(results)} 个结果，过滤后 {len(filtered_results)} 个真实搜索结果")
        
        # 如果过滤后没有结果，使用原始结果
        if len(filtered_results) == 0 and len(results) > 0:
            logger.warning("过滤后无结果，返回原始结果")
            return results
        
        return filtered_results
    
    def _extract_result_info(self, item, position: int) -> Optional[Dict]:
        """从单个搜索结果项提取信息"""
        result = {'position': position}
        
        # 提取标题和链接
        link_elem = item.find('a')
        title_elem = item.find('h3')
        
        if link_elem and title_elem:
            result['title'] = title_elem.get_text(strip=True)
            result['url'] = link_elem.get('href', '')
        else:
            # 尝试其他选择器
            link_elem = item.select_one('a[href]')
            if link_elem:
                result['url'] = link_elem.get('href', '')
                title_elem = link_elem.find('h3') or link_elem.find('h2')
                if title_elem:
                    result['title'] = title_elem.get_text(strip=True)
        
        # 提取摘要
        snippet_selectors = [
            'div.VwiC3b',  # 新版Google
            'span.aCOpRe',  # 备选
            'div.s',  # 旧版
            'div.st'  # 更旧版
        ]
        
        for selector in snippet_selectors:
            snippet_elem = item.select_one(selector)
            if snippet_elem:
                result['snippet'] = snippet_elem.get_text(strip=True)
                break
        
        # 提取日期
        date_elem = item.select_one('span.MUxGbd')
        if date_elem:
            result['date'] = date_elem.get_text(strip=True)
        
        # 提取站点信息
        cite_elem = item.select_one('cite')
        if cite_elem:
            result['site'] = cite_elem.get_text(strip=True)
        
        return result if result.get('url') else None
    
    def _generate_mock_results(self, query_hint: str) -> List[Dict]:
        """生成模拟搜索结果（演示用）"""
        # 基于查询生成相关的模拟结果
        base_results = [
            {
                'title': 'Understanding S3 Framework: Search-Select-Synthesize for Advanced RAG',
                'url': 'https://arxiv.org/abs/2024.s3framework',
                'snippet': 'The S3 framework introduces a novel three-phase approach to retrieval-augmented generation, featuring iterative search, intelligent selection, and comprehensive synthesis...',
                'position': 1
            },
            {
                'title': 'S3 vs Traditional RAG: A Comprehensive Comparison',
                'url': 'https://blog.ai-research.com/s3-vs-rag',
                'snippet': 'Comparing S3 framework with traditional RAG systems reveals significant advantages in handling complex queries, multi-hop reasoning, and information sufficiency evaluation...',
                'position': 2
            },
            {
                'title': 'Implementing the S3 Framework: Best Practices and Code Examples',
                'url': 'https://github.com/s3-framework/implementation-guide',
                'snippet': 'Step-by-step guide to implementing the S3 framework, including agent configuration, search strategies, and synthesis techniques with production-ready code examples...',
                'position': 3
            },
            {
                'title': 'Multi-hop Reasoning with S3: Handling Complex Queries',
                'url': 'https://papers.ai/multi-hop-s3-reasoning',
                'snippet': 'S3 framework excels at complex queries requiring multiple reasoning steps. Through iterative search refinement, it can navigate information dependencies effectively...',
                'position': 4
            },
            {
                'title': 'Agent-based Information Retrieval in S3 Framework',
                'url': 'https://research.openai.com/s3-agents',
                'snippet': 'The role of intelligent agents in S3 framework: decision making, search completion evaluation, and dynamic query reformulation for optimal information gathering...',
                'position': 5
            },
            {
                'title': 'Performance Benchmarks: S3 Framework vs RAG Systems',
                'url': 'https://benchmark.ai/s3-performance',
                'snippet': 'Comprehensive benchmarks show S3 outperforms traditional RAG by 35-40% on complex queries, with particularly strong results in multi-document reasoning tasks...',
                'position': 6
            },
            {
                'title': 'S3 Framework Architecture: Deep Dive into Components',
                'url': 'https://docs.s3framework.org/architecture',
                'snippet': 'Detailed exploration of S3 architecture: search module with query generation, select phase with agent evaluation, and synthesize phase for answer generation...',
                'position': 7
            },
            {
                'title': 'Real-world Applications of S3 Framework',
                'url': 'https://casestudies.ai/s3-applications',
                'snippet': 'Case studies demonstrating S3 framework in production: customer support, research assistance, and complex document analysis with significant accuracy improvements...',
                'position': 8
            },
            {
                'title': 'Optimizing S3 Framework for Production Deployment',
                'url': 'https://engineering.ai/s3-optimization',
                'snippet': 'Production optimization strategies for S3: caching strategies, parallel search execution, and cost-effective model selection for agent and synthesis components...',
                'position': 9
            },
            {
                'title': 'Future of RAG: From Simple Retrieval to Intelligent Search',
                'url': 'https://future.ai/rag-evolution-s3',
                'snippet': 'The evolution from traditional RAG to S3 represents a paradigm shift in information retrieval, moving from static retrieval to dynamic, agent-driven search processes...',
                'position': 10
            }
        ]
        
        return base_results


    async def search_for_deepsearch(self, query: str, context: Optional[Dict] = None) -> Dict:
        """
        为DeepSearch优化的搜索方法
        
        Args:
            query: 搜索查询
            context: 搜索上下文（可选）
        
        Returns:
            优化的搜索结果
        """
        context = context or {}
        
        # 基于上下文优化搜索参数
        search_options = {
            'num_results': context.get('num_results', 10),
            'search_type': context.get('search_type', 'web'),
            'date_range': context.get('date_range', 'y'),
            'language': context.get('language', 'en'),
            'country': context.get('country', 'US')
        }
        
        # 执行搜索（带重试）
        result = await self.search_with_retry(query, **search_options)
        
        # 后处理：添加相关性评分
        if result['success'] and result.get('results'):
            for i, item in enumerate(result['results']):
                item['relevance_score'] = 1.0 - (i * 0.1)
                item['needs_crawl'] = item['relevance_score'] > 0.7
        
        return result


# 使用示例
async def example_usage():
    """BrightData异步客户端使用示例"""
    
    # 创建客户端
    async with BrightDataAsyncClient(
        api_key="7f43b8faf2b1e3ccb9c6982c443d9138edc76fb0384bdc551d9ca2da5576ee4a"
    ) as client:
        
        # 1. 简单搜索
        result = await client.search("Agentic RAG implementation")
        if result['success']:
            print(f"找到 {len(result['results'])} 个结果")
            for item in result['results'][:3]:
                print(f"- {item['title']}")
                print(f"  {item['url']}")
        
        # 2. 批量搜索
        queries = [
            "S3 framework search",
            "LLM routing strategies",
            "RAG optimization techniques"
        ]
        batch_results = await client.batch_search(queries, num_results=5)
        print(f"\n批量搜索完成: {len([r for r in batch_results if r['success']])} 成功")
        
        # 3. 多类型搜索
        multi_results = await client.multi_type_search(
            "AI research 2024",
            search_types=['web', 'news', 'academic']
        )
        for search_type, result in multi_results.items():
            if result['success']:
                print(f"\n{search_type.upper()}: {len(result['results'])} 结果")
        
        # 4. 带重试的搜索
        retry_result = await client.search_with_retry(
            "complex query that might fail",
            max_retries=3
        )
        print(f"\n重试搜索: {'成功' if retry_result['success'] else '失败'}")


# DeepSearch集成示例
async def deepsearch_integration():
    """DeepSearch集成示例"""
    
    async with BrightDataAsyncClient(
        api_key="7f43b8faf2b1e3ccb9c6982c443d9138edc76fb0384bdc551d9ca2da5576ee4a"
    ) as client:
        
        # DeepSearch优化搜索
        context = {
            'search_type': 'web',
            'date_range': 'y',
            'num_results': 20
        }
        
        result = await client.search_for_deepsearch(
            "Agentic RAG best practices",
            context
        )
        
        if result['success']:
            print(f"\nDeepSearch搜索结果:")
            high_relevance = [r for r in result['results'] if r.get('needs_crawl')]
            print(f"高相关性结果（需要深度爬取）: {len(high_relevance)}")
            
            for item in high_relevance:
                print(f"- [{item['relevance_score']:.2f}] {item['title']}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())