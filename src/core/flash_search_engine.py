#!/usr/bin/env python3
"""
FlashSearch 简化搜索引擎
遵循KISS原则，提供快速、可靠的搜索体验
无复杂配置，专注性能
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# 导入基础客户端
from ..clients.brightdata_client import BrightDataAsyncClient
from ..clients.firecrawl_client import FireCrawlAsyncClient
from ..clients.enhanced_litellm_client import EnhancedLiteLLMClient
from .search_strategy import search_strategy

logger = logging.getLogger(__name__)

# 硬编码配置 - 避免复杂的配置文件
SEARCH_RESULTS = 12         # SERP搜索结果数
SELECT_URLS = 4             # 选择爬取的URL数
CRAWL_TIMEOUT = 30          # 爬取超时秒数
PARALLEL_CRAWL = 3          # 并发爬取数
MAX_TOKENS = 2000           # LLM最大tokens
TEMPERATURE = 0.3           # LLM温度参数


class FlashSearchEngine:
    """
    简化的快速搜索引擎
    专注于30-60秒内提供可靠的搜索结果
    """
    
    def __init__(self):
        """初始化搜索引擎"""
        import os
        
        # 初始化客户端，使用环境变量
        bright_api_key = os.getenv('BRIGHTDATA_API_KEY')
        if not bright_api_key:
            raise ValueError("需要设置BRIGHTDATA_API_KEY环境变量")
        
        firecrawl_api_key = os.getenv('FIRECRAWL_API_KEY') 
        if not firecrawl_api_key:
            raise ValueError("需要设置FIRECRAWL_API_KEY环境变量")
        
        # 获取超时配置
        bright_timeout = int(os.getenv('BRIGHTDATA_TIMEOUT', '60'))  # 默认60秒
        bright_zone = os.getenv('BRIGHTDATA_ZONE', 'xdan_search_searp')
        
        self.bright_client = BrightDataAsyncClient(
            api_key=bright_api_key,
            zone=bright_zone,
            timeout=bright_timeout
        )
        self.crawl_client = FireCrawlAsyncClient(api_key=firecrawl_api_key)
        self.llm_client = EnhancedLiteLLMClient()
        
        logger.info("FlashSearchEngine初始化完成")
    
    def _fix_relative_url(self, url: str, base_domain: str = "https://www.google.com") -> str:
        """
        修复相对路径URL为完整URL
        
        Args:
            url: 原始URL（可能是相对路径）
            base_domain: 基础域名
            
        Returns:
            修复后的完整URL
        """
        if not url:
            return url
            
        # 如果已经是完整URL，直接返回
        if url.startswith(('http://', 'https://')):
            return url
            
        # 如果是相对路径，添加base_domain
        if url.startswith('/'):
            return base_domain + url
            
        # 如果是其他格式，尝试添加https://
        if '.' in url and not url.startswith('www.'):
            return f"https://{url}"
            
        return url
    
    def _is_valid_crawl_url(self, url: str) -> bool:
        """
        验证URL是否适合爬取
        
        Args:
            url: 待验证的URL
            
        Returns:
            是否是有效的爬取URL
        """
        if not url:
            return False
            
        # 过滤掉Google搜索页面等无价值URL
        invalid_patterns = [
            '/search?',
            'google.com/search',
            'tbm=nws',
            'udm=2', 
            'fbs=',
            'sa=X',
            'ved=',
            'jsessionid=',  # 添加jsessionid过滤
            '&amp;',        # HTML实体
            'javascript:',  # JavaScript链接
            'mailto:',      # 邮件链接
        ]
        
        for pattern in invalid_patterns:
            if pattern in url:
                logger.debug(f"[URL过滤] 跳过无效URL: {url[:80]}... (匹配模式: {pattern})")
                return False
                
        # 检查URL长度（过长的URL通常是无效的）
        if len(url) > 500:
            logger.debug(f"[URL过滤] 跳过过长URL: {url[:80]}... (长度: {len(url)})")
            return False
                
        return True
    
    def _clean_url(self, url: str) -> str:
        """
        清理URL，移除不必要的参数
        
        Args:
            url: 原始URL
            
        Returns:
            清理后的URL
        """
        if not url:
            return url
        
        # 移除jsessionid等会话参数
        if ';jsessionid=' in url:
            url = url.split(';jsessionid=')[0]
        
        return url
    
    
    def _format_source_citation(self, content_item: Dict[str, Any], index: int) -> str:
        """
        格式化来源引用标注
        
        Args:
            content_item: 内容项
            index: 来源编号
            
        Returns:
            格式化的引用标注
        """
        title = content_item.get("title", f"来源{index}")
        is_fallback = content_item.get("is_fallback", False)
        
        if is_fallback:
            return f"【来源{index}-摘要】{title}"
        else:
            return f"【来源{index}】{title}"
    
    
    async def search(self, question: str, use_alternative_strategy: bool = False, country: str = None, language: str = None) -> List[Dict[str, Any]]:
        """
        快速SERP搜索
        
        Args:
            question: 用户问题
            use_alternative_strategy: 是否使用备选搜索策略（用于重试）
            country: 搜索国家代码（如'CN', 'US'），None时自动检测
            language: 搜索语言（如'zh-CN', 'en'），None时自动检测
            
        Returns:
            搜索结果列表，包含URL、标题、摘要
        """
        logger.info(f"[Search] 开始搜索: {question[:50]}... (备选策略: {use_alternative_strategy}, 国家: {country})")
        start_time = time.time()
        
        try:
            # 使用独立的搜索策略模块进行优化
            if use_alternative_strategy:
                # 重试时使用备选策略
                optimization_result = search_strategy.optimize_search_query_alternative(question)
            else:
                optimization_result = search_strategy.optimize_search_query(question)
            optimized_question = optimization_result['optimized_question']
            
            # 从优化结果中获取SERP参数（包含自动检测的country和language）
            serp_params = optimization_result.get('serp_params', {})
            
            # 使用传入的参数覆盖自动检测的值
            if country:
                search_country = country
            else:
                search_country = serp_params.get('country', 'CN').upper()
            
            if language:
                search_language = language
            else:
                search_language = serp_params.get('language', 'zh-CN')
            
            logger.info(f"[搜索优化] {question} → {optimized_question} (国家: {search_country}, 语言: {search_language})")
            
            # 使用BrightData进行搜索
            search_response = await self.bright_client.search(
                query=optimized_question,
                num_results=SEARCH_RESULTS,
                country=search_country,
                language=search_language
            )
            
            # 检查搜索是否成功
            if not search_response.get('success'):
                logger.error(f"[Search] BrightData搜索失败: {search_response.get('error')}")
                return []
            
            # 获取搜索结果
            search_results = search_response.get('results', [])
            if not search_results:
                logger.warning("[Search] BrightData返回空结果")
                return []
            
            # 格式化搜索结果并应用URL修复和过滤
            formatted_results = []
            skipped_count = 0
            
            for i, result in enumerate(search_results):
                original_url = result.get("url", "")
                
                # 修复URL
                fixed_url = self._fix_relative_url(original_url)
                cleaned_url = self._clean_url(fixed_url)
                
                # 验证URL是否有效
                if not self._is_valid_crawl_url(cleaned_url):
                    skipped_count += 1
                    logger.debug(f"[Search] 跳过无效URL: {original_url}")
                    continue
                
                formatted_result = {
                    "rank": len(formatted_results) + 1,  # 重新编号
                    "title": result.get("title", ""),
                    "url": cleaned_url,  # 使用清理后的URL
                    "snippet": result.get("snippet", ""),
                    "source": "brightdata"
                }
                formatted_results.append(formatted_result)
            
            # 记录过滤统计
            if skipped_count > 0:
                logger.info(f"[Search] 过滤了 {skipped_count} 个无效URL")
            
            duration = time.time() - start_time
            logger.info(f"[Search] ✅ 完成搜索: {len(formatted_results)}个结果 ({duration:.1f}s)")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"[Search] ❌ 搜索失败: {e}")
            return []
    
    async def select(self, question: str, results: List[Dict[str, Any]]) -> List[str]:
        """
        快速选择最相关的URL
        
        Args:
            question: 用户问题
            results: 搜索结果
            
        Returns:
            选中的URL列表
        """
        logger.info(f"[Select] 开始选择URL，候选数: {len(results)}")
        start_time = time.time()
        
        if not results:
            logger.warning("[Select] 无搜索结果可选择")
            return []
        
        # 如果结果数少于目标数，直接返回所有URL
        if len(results) <= SELECT_URLS:
            selected_urls = [r["url"] for r in results if r.get("url")]
            logger.info(f"[Select] 结果数少于目标，选择所有: {len(selected_urls)}个")
            return selected_urls
        
        try:
            # 构建选择prompt
            results_text = ""
            for i, result in enumerate(results[:10], 1):  # 最多考虑前10个
                results_text += f"{i}. 标题: {result.get('title', '')}\n"
                results_text += f"   URL: {result.get('url', '')}\n"
                results_text += f"   摘要: {result.get('snippet', '')}\n\n"
            
            prompt = f"""请从以下搜索结果中选择最相关的{SELECT_URLS}个URL来回答问题。

问题: {question}

搜索结果:
{results_text}

请只返回选中的URL编号，用逗号分隔，例如: 1,3,5,7"""

            # 调用LLM进行选择
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                use_case="search",
                temperature=TEMPERATURE,
                max_tokens=100
            )
            
            selection_text = response.choices[0].message.content.strip()
            logger.info(f"[Select] LLM选择结果: {selection_text}")
            
            # 解析选择结果
            selected_indices = []
            try:
                for num_str in selection_text.split(','):
                    num = int(num_str.strip())
                    if 1 <= num <= len(results):
                        selected_indices.append(num - 1)  # 转换为0-based索引
            except ValueError:
                logger.warning("[Select] LLM返回格式错误，使用前几个结果")
                selected_indices = list(range(min(SELECT_URLS, len(results))))
            
            # 获取选中的URL
            selected_urls = [results[i]["url"] for i in selected_indices if results[i].get("url")]
            
            # 如果选择数不足，补充前几个
            if len(selected_urls) < SELECT_URLS:
                for result in results:
                    if result.get("url") and result["url"] not in selected_urls:
                        selected_urls.append(result["url"])
                        if len(selected_urls) >= SELECT_URLS:
                            break
            
            duration = time.time() - start_time
            logger.info(f"[Select] ✅ 完成选择: {len(selected_urls)}个URL ({duration:.1f}s)")
            
            return selected_urls[:SELECT_URLS]
            
        except Exception as e:
            logger.error(f"[Select] ❌ 选择失败: {e}")
            # 降级：返回前几个URL
            fallback_urls = [r["url"] for r in results[:SELECT_URLS] if r.get("url")]
            logger.info(f"[Select] 降级使用前{len(fallback_urls)}个URL")
            return fallback_urls
    
    async def crawl(self, urls: List[str], search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        并发爬取URL内容，失败时fallback到snippet
        
        Args:
            urls: 要爬取的URL列表
            search_results: 原始搜索结果（用于snippet fallback）
            
        Returns:
            爬取结果列表
        """
        logger.info(f"[Crawl] 开始爬取: {len(urls)}个URL")
        start_time = time.time()
        
        if not urls:
            logger.warning("[Crawl] 无URL可爬取")
            return []
        
        # 创建URL到snippet的映射
        url_to_snippet = {}
        for result in search_results:
            if result.get("url"):
                url_to_snippet[result["url"]] = {
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", "")
                }
        
        # 并发爬取
        crawl_tasks = []
        for url in urls:
            task = self._crawl_single_url(url, url_to_snippet.get(url, {}))
            crawl_tasks.append(task)
        
        # 限制并发数
        semaphore = asyncio.Semaphore(PARALLEL_CRAWL)
        
        async def limited_crawl(task):
            async with semaphore:
                return await task
        
        # 执行爬取
        results = await asyncio.gather(*[limited_crawl(task) for task in crawl_tasks], return_exceptions=True)
        
        # 处理结果
        crawl_results = []
        successful_crawls = 0
        snippet_fallbacks = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"[Crawl] URL {urls[i]} 爬取异常: {result}")
                continue
            
            if result:
                crawl_results.append(result)
                if result.get("is_fallback"):
                    snippet_fallbacks += 1
                else:
                    successful_crawls += 1
        
        duration = time.time() - start_time
        logger.info(f"[Crawl] ✅ 完成爬取: {len(crawl_results)}个结果 "
                   f"({successful_crawls}成功, {snippet_fallbacks}回退) ({duration:.1f}s)")
        
        return crawl_results
    
    async def _crawl_single_url(self, url: str, snippet_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """爬取单个URL"""
        try:
            # 使用FireCrawl爬取
            content = await asyncio.wait_for(
                self.crawl_client.scrape_url(url),
                timeout=CRAWL_TIMEOUT
            )
            
            if content and content.get("content"):
                return {
                    "url": url,
                    "title": content.get("title", snippet_info.get("title", "")),
                    "content": content["content"][:5000],  # 限制内容长度
                    "is_fallback": False,
                    "source": "firecrawl"
                }
        
        except asyncio.TimeoutError:
            logger.warning(f"[Crawl] URL超时: {url}")
        except Exception as e:
            logger.warning(f"[Crawl] URL失败: {url} - {e}")
        
        # Fallback到snippet
        snippet = snippet_info.get("snippet", "")
        if snippet:
            logger.info(f"[Crawl] 使用snippet fallback: {url}")
            return {
                "url": url,
                "title": snippet_info.get("title", ""),
                "content": f"摘要信息: {snippet}",
                "is_fallback": True,
                "source": "snippet"
            }
        
        return None
    
    async def synthesize(self, question: str, content: List[Dict[str, Any]]) -> str:
        """
        生成最终答案
        
        Args:
            question: 用户问题
            content: 爬取的内容列表
            
        Returns:
            结构化答案
        """
        logger.info(f"[Synthesize] 开始生成答案，内容源: {len(content)}个")
        start_time = time.time()
        
        if not content:
            return "抱歉，未能获取到相关信息来回答您的问题。"
        
        try:
            # 构建内容摘要，使用增强的引用标注
            content_summary = ""
            for i, item in enumerate(content, 1):
                citation = self._format_source_citation(item, i)
                text = item.get("content", "")
                
                content_summary += f"{citation}\n"
                content_summary += f"{text[:800]}...\n\n"  # 限制每个来源的长度
            
            # 构建生成prompt
            prompt = f"""请基于以下信息回答问题，要求简洁明了、结构清晰。

问题: {question}

相关信息:
{content_summary}

请提供结构化的回答，包括：
1. 直接回答问题的核心要点
2. 支撑信息和细节
3. 信息来源说明

回答要求：
- 基于提供的信息，不要编造内容
- 如果信息不足，请明确说明
- 保持客观和准确"""

            # 调用LLM生成答案
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                use_case="generation",
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )
            
            final_answer = response.choices[0].message.content
            
            duration = time.time() - start_time
            logger.info(f"[Synthesize] ✅ 完成生成: {len(final_answer)}字符 ({duration:.1f}s)")
            
            return final_answer
            
        except Exception as e:
            logger.error(f"[Synthesize] ❌ 生成失败: {e}")
            return f"抱歉，在生成答案时遇到错误：{e}"
    
    async def flash_search(self, question: str) -> Dict[str, Any]:
        """
        主入口：执行完整的快速搜索流程
        
        Args:
            question: 用户问题
            
        Returns:
            搜索结果字典
        """
        logger.info(f"[FlashSearch] 开始处理问题: {question}")
        overall_start = time.time()
        
        result = {
            "question": question,
            "answer": "",
            "sources": [],
            "stats": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 1. 搜索
            search_results = await self.search(question)
            if not search_results:
                result["answer"] = "抱歉，搜索未找到相关结果。"
                return result
            
            # 2. 选择URL
            selected_urls = await self.select(question, search_results)
            
            # 如果第一次选择失败，尝试重新搜索（使用备选策略）
            if not selected_urls:
                logger.warning("[FlashSearch] 第一次选择失败，尝试使用备选策略重新搜索")
                search_results = await self.search(question, use_alternative_strategy=True)
                if search_results:
                    selected_urls = await self.select(question, search_results)
                
                if not selected_urls:
                    result["answer"] = "抱歉，未能选择到有效的信息源。"
                    return result
            
            # 3. 爬取内容
            crawl_results = await self.crawl(selected_urls, search_results)
            if not crawl_results:
                result["answer"] = "抱歉，未能获取到有效内容。"
                return result
            
            # 4. 生成答案
            final_answer = await self.synthesize(question, crawl_results)
            
            # 5. 整理结果
            result.update({
                "answer": final_answer,
                "sources": crawl_results,
                "stats": {
                    "search_results": len(search_results),
                    "selected_urls": len(selected_urls),
                    "crawled_sources": len(crawl_results),
                    "successful_crawls": sum(1 for r in crawl_results if not r.get("is_fallback")),
                    "snippet_fallbacks": sum(1 for r in crawl_results if r.get("is_fallback")),
                    "total_duration": time.time() - overall_start
                }
            })
            
            logger.info(f"[FlashSearch] ✅ 完成搜索: {result['stats']['total_duration']:.1f}s")
            
        except Exception as e:
            logger.error(f"[FlashSearch] ❌ 搜索失败: {e}")
            result["answer"] = f"抱歉，搜索过程中遇到错误：{e}"
        
        return result


# 便捷函数
async def flash_search(question: str) -> Dict[str, Any]:
    """
    便捷的搜索函数
    
    Args:
        question: 用户问题
        
    Returns:
        搜索结果
    """
    engine = FlashSearchEngine()
    return await engine.flash_search(question)