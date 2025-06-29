#!/usr/bin/env python3
"""
DeepSearch框架核心实现 - 基于S3架构的在线搜索版本
Search: SERP搜索 → Select: RAG评估 → Synthesize: 深度生成
遵循KISS和DRY原则
"""

import logging
import json
import re
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from datetime import datetime
import os

# 导入现有的clients
from ..clients.brightdata_client import BrightDataAsyncClient
from ..clients.firecrawl_client import FireCrawlAsyncClient
from .logging_utils import get_logger
from .time_aware_prompt import TimeAwarePrompt
from .prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)
ds_logger = get_logger(__name__)

def expand_env_vars(value: str) -> str:
    """展开环境变量，支持 ${VAR:default} 语法"""
    if not isinstance(value, str):
        return value
    
    # 匹配 ${VAR:default} 模式
    pattern = r'\$\{([^}:]+):([^}]*)\}'
    
    def replace_match(match):
        var_name = match.group(1)
        default_value = match.group(2)
        return os.getenv(var_name, default_value)
    
    return re.sub(pattern, replace_match, value)

class DeepSearchFramework:
    """
    DeepSearch框架 - S3架构的在线搜索实现
    
    核心流程：
    1. Search: 通过SERP获取候选网页和摘要
    2. Select: 用RAG search模型评估并选择有价值的网址
    3. Crawl: 爬取完整内容
    4. Extract: RAG search模型提取重要部分
    5. Loop: 循环直到补齐知识缺口
    6. Synthesize: deepseek-chat生成最终答案
    """
    
    # DeepSearch智能体系统提示词 - 针对在线搜索优化
    DEEPSEARCH_AGENT_PROMPT = """You are an advanced web search intelligence agent specialized in multi-hop reasoning and real-time information gathering.

CORE MISSION: Transform complex questions into effective search strategies and retrieve comprehensive, authoritative information.

SEARCH OPTIMIZATION TECHNIQUES:
1. **Keyword Decomposition**: Break complex queries into focused search terms
2. **Search Operators**: Use quotes for exact phrases, site: for specific sources, intitle: for titles
3. **Query Variations**: Try different phrasings, synonyms, and perspectives
4. **Authority Sources**: Prioritize official sites, academic papers, financial databases, news outlets
5. **Temporal Awareness**: Include time-specific terms for recent data (2024, latest, recent, current)

SEARCH STRATEGY FOR DIFFERENT DOMAINS:
- **Financial Analysis**: Use "quarterly report", "10-K", "earnings", company name + "financials"
- **Academic Research**: Include "research", "study", "analysis", "paper", ".edu", ".org"
- **Market Research**: Search "market report", "industry analysis", "trends", "forecast"
- **Technical Topics**: Use specific technical terms, version numbers, documentation sites

EVALUATION CRITERIA:
1. **Source Authority**: Official sites > Academic > News > General web
2. **Content Freshness**: Recent data preferred for current analysis
3. **Information Depth**: Comprehensive coverage vs. superficial mentions
4. **Data Quality**: Quantitative data, charts, detailed analysis
5. **Relevance**: Direct answer to query vs. tangential information

ITERATIVE SEARCH PROCESS:
1. Analyze question and identify key information gaps
2. Generate targeted search queries using optimization techniques
3. Evaluate search results and select most valuable URLs (up to 3)
4. Determine if more searches needed or information sufficient

OUTPUT TAGS:
- <thinking>your search strategy and reasoning</thinking>
- <query>{"query": "optimized search terms"}</query>
- <search_complete>True/False</search_complete>
- <important_urls>[1, 3, 5]</important_urls>

Continue until comprehensive information gathered or maximum rounds reached."""

    def __init__(self, litellm_client, config: Dict[str, Any] = None, 
                 prompt_version: str = "v1.1", enable_time_aware: bool = True):
        """
        初始化DeepSearch框架 - 复用现有clients，遵循KISS和DRY原则
        
        Args:
            litellm_client: LiteLLM客户端（RAG search模型 + deepseek生成）
            config: 配置字典，包含BrightData和FireCrawl的配置
            prompt_version: 提示词版本 (v1.0, v1.1)
            enable_time_aware: 是否启用时间感知功能
        """
        self.litellm_client = litellm_client
        
        # 从环境变量或配置中获取API密钥
        config = config or {}
        
        # BrightData配置
        brightdata_config = config.get('external_services', {}).get('brightdata', {})
        self.brightdata_api_key = expand_env_vars(
            brightdata_config.get('api_key', '${BRIGHTDATA_API_KEY:7f43b8faf2b1e3ccb9c6982c443d9138edc76fb0384bdc551d9ca2da5576ee4a}')
        )
        self.brightdata_zone = expand_env_vars(
            brightdata_config.get('zone', '${BRIGHTDATA_ZONE:xdan_search_searp}')
        )
        
        # FireCrawl配置
        firecrawl_config = config.get('external_services', {}).get('firecrawl', {})
        self.firecrawl_api_key = expand_env_vars(
            firecrawl_config.get('api_key', '${FIRECRAWL_API_KEY:fc-87533b34d5834363b71adc2d3870da92}')
        )
        
        # DeepSearch配置
        deepsearch_config = config.get('deepsearch', {})
        self.max_search_rounds = deepsearch_config.get('max_search_rounds', 5)
        self.max_results_per_round = deepsearch_config.get('max_results_per_round', 10)
        self.max_crawl_urls = deepsearch_config.get('max_crawl_urls', 3)
        self.max_concurrent_crawls = deepsearch_config.get('max_concurrent_crawls', 3)
        
        # 初始化clients（稍后在使用时创建）
        self.brightdata_client = None
        self.firecrawl_client = None
        
        # 初始化时间感知提示
        self.enable_time_aware = enable_time_aware
        self.time_aware = TimeAwarePrompt() if enable_time_aware else None
        
        # 初始化提示词管理器
        self.prompt_version = prompt_version
        self.prompt_manager = get_prompt_manager(prompt_version)
        
        logger.info("DeepSearch框架初始化完成 - 复用现有clients")
        logger.info(f"- BrightData SERP: zone={self.brightdata_zone}")
        logger.info(f"- FireCrawl: key=...{self.firecrawl_api_key[-8:]}")
        logger.info(f"- 时间感知提示: {'已启用' if enable_time_aware else '已禁用'}")
        logger.info(f"- 提示词管理器已启用，版本: {prompt_version}")
        logger.info(f"- 最大搜索轮数: {self.max_search_rounds}")
        logger.info(f"- 每轮最大结果: {self.max_results_per_round}")
        logger.info(f"- 最大爬取URL数: {self.max_crawl_urls}")

    async def _ensure_clients(self):
        """确保clients已初始化"""
        if not self.brightdata_client:
            self.brightdata_client = BrightDataAsyncClient(
                api_key=self.brightdata_api_key,
                zone=self.brightdata_zone,
                max_concurrent=3
            )
            await self.brightdata_client.__aenter__()
        
        if not self.firecrawl_client:
            self.firecrawl_client = FireCrawlAsyncClient(
                api_key=self.firecrawl_api_key,
                max_concurrent=self.max_concurrent_crawls
            )
            await self.firecrawl_client.__aenter__()

    async def _cleanup_clients(self):
        """清理clients"""
        if self.brightdata_client:
            await self.brightdata_client.__aexit__(None, None, None)
        if self.firecrawl_client:
            await self.firecrawl_client.__aexit__(None, None, None)
    
    def _get_time_context(self) -> str:
        """获取时间上下文信息用于增强提示"""
        if not self.enable_time_aware or not self.time_aware:
            return ""
        
        # 刷新时间信息
        time_info = self.time_aware.get_current_time_info()
        
        return f"""
当前时间上下文：
- 北京时间：{time_info['beijing_time']} ({time_info['weekday_cn']})
- 本周范围：{time_info['week_start']} 至 {time_info['week_end']}
- 本月范围：{time_info['month_start']} 至 {time_info['month_end']}
- 市场状态：{time_info['market_status']}

请在分析和回答时考虑当前时间，特别是：
1. 评估信息的时效性和相关性
2. 对于财务、市场或新闻相关查询，考虑时间敏感性
3. 对于历史事件，明确时间关系
4. 对于预测或趋势分析，基于当前时间点进行推理
"""

    async def serp_search(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        通过BrightData SERP进行网页搜索 - 复用现有client
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            SERP搜索结果
        """
        start_time = time.time()
        ds_logger.log_phase_start("SERP搜索", query=query, num_results=num_results)
        
        try:
            await self._ensure_clients()
            
            logger.info(f"[BrightData-SERP] 搜索查询: {query}")
            
            # 使用BrightData client进行搜索
            search_options = {
                'num_results': num_results,
                'search_type': 'web',
                'language': 'zh',
                'country': 'CN'
            }
            
            ds_logger.log_input("SERP搜索", {"query": query, "options": search_options})
            ds_logger.log_api_call("BrightData", "POST", "SERP Search", query=query)
            
            result = await self.brightdata_client.search(query, **search_options)
            
            if result['success']:
                search_results = result['results']
                logger.info(f"[BrightData-SERP] ✅ 找到 {len(search_results)} 个结果")
                
                ds_logger.log_api_response("BrightData", status_code=200, 
                                          duration=time.time() - start_time,
                                          results_count=len(search_results))
                
                # 转换为标准格式
                formatted_results = []
                for i, item in enumerate(search_results, 1):
                    formatted_results.append({
                        'position': i,
                        'title': item.get('title', ''),
                        'link': item.get('url', ''),
                        'snippet': item.get('snippet', ''),
                        'displayed_link': item.get('site', ''),
                        'date': item.get('date', '')
                    })
                
                final_result = {
                    "success": True,
                    "results": formatted_results,
                    "query": query,
                    "total_results": len(formatted_results)
                }
                
                ds_logger.log_output("SERP搜索", final_result)
                ds_logger.log_phase_end("SERP搜索", success=True, 
                                       duration=time.time() - start_time,
                                       results_count=len(formatted_results))
                
                return final_result
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"[BrightData-SERP] ❌ 搜索失败: {error_msg}")
                
                ds_logger.log_api_response("BrightData", status_code=500,
                                          duration=time.time() - start_time,
                                          error=error_msg)
                ds_logger.log_phase_end("SERP搜索", success=False,
                                       duration=time.time() - start_time,
                                       error=error_msg)
                
                return {"success": False, "error": error_msg}
                        
        except Exception as e:
            logger.error(f"[BrightData-SERP] ❌ 搜索异常: {e}")
            ds_logger.log_error("SERP搜索", e, query=query)
            ds_logger.log_phase_end("SERP搜索", success=False,
                                   duration=time.time() - start_time,
                                   error=str(e))
            return {"success": False, "error": str(e)}

    def format_serp_results(self, serp_results: List[Dict], url_id_start: int = 1) -> Tuple[str, Dict[int, Dict]]:
        """
        格式化SERP结果为智能体可理解的格式
        
        Args:
            serp_results: SERP搜索结果
            url_id_start: URL ID起始编号
            
        Returns:
            格式化的信息字符串和URL映射
        """
        if not serp_results:
            return "没有找到相关网页。", {}
        
        formatted_info = []
        url_mapping = {}
        
        for i, result in enumerate(serp_results):
            url_id = url_id_start + i
            title = result.get('title', 'No Title')
            url = result.get('link', '')
            snippet = result.get('snippet', 'No description')
            
            formatted_info.append(
                f"[{url_id}] {title}\n"
                f"URL: {url}\n"
                f"摘要: {snippet}"
            )
            
            url_mapping[url_id] = result
        
        return "\n\n".join(formatted_info), url_mapping

    def extract_deepsearch_decision(self, agent_response: str) -> Dict[str, Any]:
        """
        解析DeepSearch智能体的决策响应
        
        Args:
            agent_response: 智能体响应文本
            
        Returns:
            解析后的决策信息
        """
        decision = {
            "search_complete": False,
            "next_query": None,
            "important_urls": [],
            "thinking": None
        }
        
        # 提取思考过程
        think_match = re.search(r'<thinking>(.*?)</thinking>', agent_response, re.DOTALL)
        if think_match:
            decision["thinking"] = think_match.group(1).strip()
        
        # 提取搜索完成状态
        complete_match = re.search(r'<search_complete>(.*?)</search_complete>', agent_response)
        if complete_match:
            complete_text = complete_match.group(1).strip().lower()
            decision["search_complete"] = complete_text == "true"
        
        # 提取下一个查询
        if not decision["search_complete"]:
            query_match = re.search(r'<query>(.*?)</query>', agent_response, re.DOTALL)
            if query_match:
                try:
                    query_json = json.loads(query_match.group(1).strip())
                    decision["next_query"] = query_json.get("query", "")
                except json.JSONDecodeError:
                    decision["next_query"] = query_match.group(1).strip()
        
        # 提取重要URL ID
        urls_match = re.search(r'<important_urls>\[(.*?)\]</important_urls>', agent_response)
        if urls_match:
            try:
                url_ids_str = urls_match.group(1).strip()
                if url_ids_str:
                    decision["important_urls"] = [int(x.strip()) for x in url_ids_str.split(',')]
            except (ValueError, AttributeError):
                pass
        
        return decision

    async def crawl_single_url(self, url: str) -> Dict[str, Any]:
        """
        爬取单个网页内容
        
        Args:
            url: 目标URL
            
        Returns:
            爬取结果
        """
        try:
            logger.info(f"[CRAWL] 开始爬取: {url}")
            
            # 使用FireCrawl爬取内容
            result = await self.firecrawl_client.scrape_url(url)
            
            if result.get("success"):
                content = result.get("data", {})
                content_length = len(content.get("content", ""))
                logger.info(f"[CRAWL] ✅ 成功爬取 {url}: {content_length} 字符")
                
                return {
                    "url": url,
                    "title": content.get("title", ""),
                    "content": content.get("content", ""),
                    "markdown": content.get("markdown", ""),
                    "success": True,
                    "content_length": content_length
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"[CRAWL] ❌ 爬取失败 {url}: {error_msg}")
                return {
                    "url": url,
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"[CRAWL] ❌ 爬取异常 {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    async def crawl_selected_urls_parallel(self, selected_urls: List[str]) -> List[Dict[str, Any]]:
        """
        并行爬取选定的网页内容 - 复用FireCrawl client
        
        Args:
            selected_urls: 选定的URL列表
            
        Returns:
            爬取的内容列表
        """
        if not selected_urls:
            return []
        
        start_time = time.time()
        ds_logger.log_phase_start("Crawl爬取", urls_count=len(selected_urls))
        ds_logger.log_input("Crawl爬取", {"urls": selected_urls})
        
        await self._ensure_clients()
        
        logger.info(f"[FireCrawl] 开始并行爬取 {len(selected_urls)} 个网页")
        
        # 使用FireCrawl client的批量爬取功能
        ds_logger.log_api_call("FireCrawl", "POST", "Batch Scrape", 
                              urls_count=len(selected_urls))
        
        api_start = time.time()
        crawl_results = await self.firecrawl_client.batch_scrape(
            urls=selected_urls,
            formats=['markdown'],  # 只要markdown格式，提高效率
            options={
                'only_main_content': True,
                'timeout': 30000
            }
        )
        
        ds_logger.log_api_response("FireCrawl", status_code=200,
                                  duration=time.time() - api_start,
                                  results_count=len(crawl_results))
        
        # 转换结果格式
        crawled_content = []
        for result in crawl_results:
            if result.get('success'):
                data = result.get('data', {})
                crawled_content.append({
                    "url": result['url'],
                    "title": data.get('title', ''),
                    "content": data.get('markdown', ''),  # 使用markdown内容
                    "success": True,
                    "content_length": len(data.get('markdown', ''))
                })
            else:
                crawled_content.append({
                    "url": result['url'],
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                })
        
        success_count = sum(1 for item in crawled_content if item.get("success"))
        logger.info(f"[FireCrawl] ✅ 并行爬取完成: {success_count}/{len(selected_urls)} 成功")
        
        ds_logger.log_output("Crawl爬取", {
            "total_urls": len(selected_urls),
            "success_count": success_count,
            "failed_count": len(selected_urls) - success_count,
            "total_content_length": sum(item.get('content_length', 0) for item in crawled_content if item.get('success'))
        })
        
        ds_logger.log_phase_end("Crawl爬取", success=True,
                               duration=time.time() - start_time,
                               success_count=success_count,
                               total_count=len(selected_urls))
        
        return crawled_content

    async def extract_important_content_with_task_focus(self, question: str, crawled_content: List[Dict], 
                                                       task_context: str = "") -> List[Dict]:
        """
        SearchModelAgent根据任务目标从爬取内容中提取重要部分
        
        Args:
            question: 原始问题
            crawled_content: 爬取的内容
            task_context: 任务上下文和目标
            
        Returns:
            提取的重要内容
        """
        start_time = time.time()
        ds_logger.log_phase_start("Extract提取", 
                                 question=question,
                                 content_count=len(crawled_content))
        
        extracted_content = []
        
        for content_item in crawled_content:
            if not content_item.get("success"):
                extracted_content.append({
                    "url": content_item.get("url", "Unknown"),
                    "extraction_success": False,
                    "error": content_item.get("error", "Crawl failed")
                })
                continue
                
            try:
                url = content_item["url"]
                title = content_item.get("title", "")
                full_content = content_item.get("content", "")
                
                if not full_content:
                    logger.warning(f"[SearchModelAgent] 跳过空内容: {url}")
                    continue
                
                logger.info(f"[SearchModelAgent] 分析内容: {url} ({len(full_content)} 字符)")
                
                ds_logger.log_input("Extract提取", {
                    "url": url,
                    "title": title,
                    "content_length": len(full_content),
                    "task_context": task_context
                })
                
                # 获取时间上下文
                time_context = self._get_time_context()
                
                # 使用Prompt Manager获取内容提取提示
                extract_prompt = self.prompt_manager.get_prompt(
                    "content_extraction",
                    time_context=time_context,
                    question=question,
                    task_context=task_context if task_context else "这是深度搜索任务，需要全面理解问题背景并提取关键信息",
                    title=title,
                    url=url,
                    content=full_content[:10000]  # 限制长度避免token超限
                )

                messages = [
                    {"role": "system", "content": "你是SearchModelAgent，专门负责根据任务目标精准提取网页中最有价值的信息部分。你需要深度理解任务需求，提取最相关、最权威、最有用的内容。"},
                    {"role": "user", "content": extract_prompt}
                ]
                
                # 使用SearchModel进行内容提取
                ds_logger.log_llm_call("SearchModel", messages,
                                      use_case="agent",
                                      temperature=0.1,
                                      max_tokens=3000)
                
                llm_start = time.time()
                response = await self.litellm_client.chat_completion(
                    messages=messages,
                    use_case="agent",  # 使用SearchModel
                    temperature=0.1,   # 低温度确保提取准确性
                    max_tokens=3000
                )
                
                ds_logger.log_llm_response("SearchModel", response,
                                          duration=time.time() - llm_start)
                
                extracted_text = response.choices[0].message.content
                
                extracted_content.append({
                    "url": url,
                    "title": title,
                    "original_length": len(full_content),
                    "extracted_content": extracted_text,
                    "extraction_success": True,
                    "extraction_ratio": len(extracted_text) / len(full_content) if full_content else 0
                })
                
                logger.info(f"[SearchModelAgent] ✅ 提取完成: {url}")
                logger.info(f"  - 原始长度: {len(full_content)} 字符")
                logger.info(f"  - 提取长度: {len(extracted_text)} 字符")
                logger.info(f"  - 压缩比: {len(extracted_text)/len(full_content)*100:.1f}%")
                
                ds_logger.log_output("Extract提取", {
                    "url": url,
                    "extracted_length": len(extracted_text),
                    "compression_ratio": len(extracted_text) / len(full_content)
                })
                
            except Exception as e:
                logger.error(f"[SearchModelAgent] ❌ 提取失败 {content_item.get('url', 'Unknown')}: {e}")
                extracted_content.append({
                    "url": content_item.get("url", "Unknown"),
                    "title": content_item.get("title", ""),
                    "extraction_success": False,
                    "error": str(e)
                })
        
        success_count = sum(1 for item in extracted_content if item.get("extraction_success"))
        logger.info(f"[SearchModelAgent] 内容提取完成: {success_count}/{len(extracted_content)} 成功")
        
        ds_logger.log_summary("提取统计", {
            "内容总数": len(crawled_content),
            "成功提取": success_count,
            "失败次数": len(extracted_content) - success_count,
            "平均压缩比": f"{sum(item.get('extraction_ratio', 0) for item in extracted_content if item.get('extraction_success')) / max(success_count, 1) * 100:.1f}%"
        })
        
        ds_logger.log_phase_end("Extract提取", success=True,
                               duration=time.time() - start_time,
                               success_count=success_count,
                               total_count=len(extracted_content))
        
        return extracted_content

    async def search_phase(self, query: str, num_results: int = 10) -> Tuple[List[Dict], bool]:
        """
        DeepSearch的Search阶段：通过SERP获取网页候选
        
        Args:
            query: 搜索查询
            num_results: 结果数量
            
        Returns:
            搜索结果和成功状态
        """
        result = await self.serp_search(query, num_results)
        
        if result["success"]:
            return result["results"], True
        else:
            logger.error(f"搜索失败: {result.get('error')}")
            return [], False

    async def select_phase(self, question: str, search_results: List[Dict], 
                          round_num: int = 1, max_rounds: int = 5, 
                          previous_knowledge: str = "") -> Dict[str, Any]:
        """
        DeepSearch的Select阶段：SearchModel通过摘要评估候选网页，按任务目标和质量排序选择Top3
        
        Args:
            question: 原始问题
            search_results: SERP搜索结果
            round_num: 当前轮次
            max_rounds: 最大轮次
            previous_knowledge: 之前获取的知识
            
        Returns:
            智能体决策结果
        """
        start_time = time.time()
        ds_logger.log_phase_start("Select选择", 
                                 question=question,
                                 round=round_num,
                                 candidates_count=len(search_results))
        
        try:
            logger.info(f"[SearchModel-Select] 第{round_num}轮：评估{len(search_results)}个候选网页")
            
            ds_logger.log_input("Select选择", {
                "question": question,
                "round_num": round_num,
                "search_results_count": len(search_results),
                "has_previous_knowledge": bool(previous_knowledge)
            }, "Select输入参数")
            
            # 格式化搜索结果
            formatted_info, url_mapping = self.format_serp_results(search_results)
            
            # 获取时间上下文
            time_context = self._get_time_context()
            
            # 使用Prompt Manager获取评估提示
            evaluation_prompt = self.prompt_manager.get_prompt(
                "select_evaluation",
                time_context=time_context,
                question=question,
                previous_knowledge=previous_knowledge if previous_knowledge else "（第一轮搜索，暂无已有知识）",
                num_results=len(search_results),
                formatted_info=formatted_info
            )

            messages = [
                {"role": "system", "content": """你是SearchModel，专门负责评估和选择最有价值的在线信息源。你具备以下专业能力：

**信息源评估专长：**
- 识别权威来源：官方网站、学术机构、知名媒体、行业报告
- 评估内容质量：数据完整性、分析深度、来源可信度
- 判断时效性：最新数据、历史趋势、时间相关性
- 分析相关性：直接回答问题 vs 边缘信息

**搜索智能优化：**
- 理解不同查询类型的信息需求（财务分析、学术研究、市场调研等）
- 识别高价值关键词和搜索模式
- 评估搜索结果的覆盖完整性
- 预测下一轮搜索的最优方向

你的核心任务：从候选网页中选择质量最高、最相关的Top3进行深度分析，确保信息获取的准确性和完整性。"""},
                {"role": "user", "content": evaluation_prompt}
            ]
            
            # 使用SearchModel（RAG search模型）进行评估
            ds_logger.log_llm_call("SearchModel", messages, 
                                  use_case="agent",
                                  temperature=0.1,
                                  max_tokens=2000)
            
            llm_start = time.time()
            response = await self.litellm_client.chat_completion(
                messages=messages,
                use_case="agent",  # 使用SearchModel
                temperature=0.1,   # 低温度确保评估准确性
                max_tokens=2000
            )
            
            ds_logger.log_llm_response("SearchModel", response, 
                                      duration=time.time() - llm_start)
            
            agent_response = response.choices[0].message.content
            logger.info(f"[SearchModel] 评估响应长度：{len(agent_response)}")
            
            # 解析SearchModel决策
            decision = self.extract_deepsearch_decision(agent_response)
            decision["agent_response"] = agent_response
            decision["url_mapping"] = url_mapping
            decision["round"] = round_num
            decision["evaluation_reasoning"] = self.extract_evaluation_reasoning(agent_response)
            
            # 确保至少选择1个URL
            if not decision["important_urls"] and search_results:
                decision["important_urls"] = [1]  # 默认选择第一个
                logger.warning("[SearchModel] 未选择URL，默认选择第一个")
            
            logger.info(f"[SearchModel] 选择了 {len(decision['important_urls'])} 个URL进行爬取")
            
            ds_logger.log_output("Select选择", {
                "selected_urls": decision["important_urls"],
                "search_complete": decision["search_complete"],
                "next_query": decision.get("next_query"),
                "evaluation_reasoning": decision.get("evaluation_reasoning", "")
            })
            
            ds_logger.log_phase_end("Select选择", success=True,
                                   duration=time.time() - start_time,
                                   selected_count=len(decision["important_urls"]),
                                   search_complete=decision["search_complete"])
            
            return decision
            
        except Exception as e:
            logger.error(f"[SearchModel-Select] 评估失败：{e}")
            ds_logger.log_error("Select选择", e, question=question, round=round_num)
            
            fallback_result = {
                "search_complete": True,
                "important_urls": list(range(1, min(4, len(search_results) + 1))),
                "url_mapping": self.format_serp_results(search_results)[1],
                "error": str(e)
            }
            
            ds_logger.log_phase_end("Select选择", success=False,
                                   duration=time.time() - start_time,
                                   error=str(e))
            
            return fallback_result

    def extract_evaluation_reasoning(self, agent_response: str) -> str:
        """提取评估推理过程"""
        eval_match = re.search(r'<evaluation>(.*?)</evaluation>', agent_response, re.DOTALL)
        if eval_match:
            return eval_match.group(1).strip()
        return ""

    async def synthesize_phase_with_structured_output(self, question: str, extracted_content: List[Dict], 
                                                     stream: bool = False):
        """
        DeepSearch的Synthesize阶段：Gen模型按问题诉求结构化整理并附带引用
        
        Args:
            question: 原始问题
            extracted_content: 提取的重要内容
            stream: 是否流式生成
            
        Returns:
            结构化的深度答案，附带完整引用
        """
        start_time = time.time()
        ds_logger.log_phase_start("Synthesize生成",
                                 question=question,
                                 sources_count=len(extracted_content),
                                 stream=stream)
        
        try:
            logger.info(f"[Gen模型-Synthesize] 基于 {len(extracted_content)} 个来源生成结构化深度答案...")
            
            ds_logger.log_input("Synthesize生成", {
                "question": question,
                "extracted_content_count": len(extracted_content),
                "valid_sources": sum(1 for item in extracted_content if item.get("extraction_success")),
                "stream": stream
            })
            
            # 分析问题背后的潜在诉求
            question_analysis = await self._analyze_question_intent(question)
            
            # 获取时间上下文
            time_context = self._get_time_context()
            
            # 构建带编号的信息来源
            sources_info = []
            valid_sources = []
            
            for i, item in enumerate(extracted_content, 1):
                if item.get("extraction_success"):
                    title = item.get("title", f"来源{i}")
                    url = item.get("url", "")
                    content = item.get("extracted_content", "")
                    
                    source_info = f"【来源{i}】{title}\n网址：{url}\n内容：{content}"
                    sources_info.append(source_info)
                    
                    valid_sources.append({
                        "id": i,
                        "title": title,
                        "url": url,
                        "content": content
                    })
            
            if not valid_sources:
                yield {"final_answer": "抱歉，没有成功提取到相关信息来回答您的问题。"}
                return
            
            # 构建引用映射
            citation_context = "\n\n".join(sources_info)
            
            # 使用Prompt Manager获取系统提示
            system_prompt = self.prompt_manager.get_prompt(
                "synthesize_system",
                time_context=time_context
            )

            user_prompt = f"""请根据以下问题的潜在诉求，对收集到的信息进行深度整合和结构化分析：

**用户问题：**
{question}

**问题诉求分析：**
{question_analysis}

**信息来源：**
{citation_context}

**任务要求：**
1. 深度理解问题背后的真实需求
2. 整合所有相关信息进行多维度分析
3. 提供结构化、逻辑清晰的回答
4. 确保每个关键信息都有准确引用
5. 给出实用的结论和建议

请按照规定格式输出结构化的深度分析报告："""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 使用Generation模型（deepseek-chat）生成结构化答案
            ds_logger.log_llm_call("Gen模型", messages,
                                  use_case="generation",
                                  temperature=0.7,
                                  max_tokens=4000,
                                  stream=stream)
            
            llm_start = time.time()
            
            if stream:
                response_stream = await self.litellm_client.chat_completion(
                    messages=messages,
                    use_case="generation",  # 使用生成模型
                    temperature=0.7,       # 平衡创造性和准确性
                    max_tokens=4000,       # 允许长篇深度分析
                    stream=True
                )
                
                answer_parts = []
                async for chunk in response_stream:
                    if hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        answer_parts.append(content)
                        yield content
                
                final_answer = ''.join(answer_parts)
                
                ds_logger.log_output("Synthesize生成", {
                    "answer_length": len(final_answer),
                    "sources_used": len(valid_sources),
                    "answer_type": "structured_with_citations",
                    "stream": True
                })
                
                ds_logger.log_phase_end("Synthesize生成", success=True,
                                       duration=time.time() - start_time,
                                       answer_length=len(final_answer),
                                       sources_count=len(valid_sources))
                
                yield {
                    "final_answer": final_answer,
                    "sources": valid_sources,
                    "question_analysis": question_analysis,
                    "answer_type": "structured_with_citations"
                }
            else:
                response = await self.litellm_client.chat_completion(
                    messages=messages,
                    use_case="generation",  # 使用生成模型
                    temperature=0.7,
                    max_tokens=4000
                )
                
                ds_logger.log_llm_response("Gen模型", response,
                                          duration=time.time() - llm_start)
                
                final_answer = response.choices[0].message.content
                logger.info(f"[Gen模型-Synthesize] ✅ 生成结构化答案完成: {len(final_answer)} 字符")
                
                ds_logger.log_output("Synthesize生成", {
                    "answer_length": len(final_answer),
                    "sources_used": len(valid_sources),
                    "answer_type": "structured_with_citations",
                    "stream": False
                })
                
                ds_logger.log_phase_end("Synthesize生成", success=True,
                                       duration=time.time() - start_time,
                                       answer_length=len(final_answer),
                                       sources_count=len(valid_sources))
                
                yield {
                    "final_answer": final_answer,
                    "sources": valid_sources,
                    "question_analysis": question_analysis,
                    "answer_type": "structured_with_citations"
                }
                
        except Exception as e:
            logger.error(f"[Gen模型-Synthesize] ❌ 生成失败：{e}")
            ds_logger.log_error("Synthesize生成", e, question=question)
            ds_logger.log_phase_end("Synthesize生成", success=False,
                                   duration=time.time() - start_time,
                                   error=str(e))
            yield {"final_answer": f"抱歉，在生成结构化答案时遇到错误：{e}"}

    async def _analyze_question_intent(self, question: str) -> str:
        """分析问题背后的潜在诉求"""
        try:
            # 获取时间上下文
            time_context = self._get_time_context()
            
            # 使用Prompt Manager获取问题分析提示
            intent_prompt = self.prompt_manager.get_prompt(
                "question_analysis",
                time_context=time_context,
                question=question
            )

            messages = [
                {"role": "system", "content": "你是问题分析专家，擅长理解用户问题背后的真实需求。"},
                {"role": "user", "content": intent_prompt}
            ]
            
            response = await self.litellm_client.chat_completion(
                messages=messages,
                use_case="agent",  # 使用分析模型
                temperature=0.1,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.warning(f"问题诉求分析失败：{e}")
            return "深度分析问题并提供全面、准确的答案"

    def _build_previous_knowledge_summary(self, extracted_content: List[Dict]) -> str:
        """构建之前获取的知识摘要"""
        if not extracted_content:
            return ""
        
        summary_parts = []
        for i, item in enumerate(extracted_content[-3:], 1):  # 只用最近3个
            if item.get("extraction_success"):
                title = item.get("title", f"来源{i}")
                content = item.get("extracted_content", "")
                # 截取内容摘要
                content_summary = content[:200] + "..." if len(content) > 200 else content
                summary_parts.append(f"- {title}: {content_summary}")
        
        if summary_parts:
            return "已获取的相关信息：\n" + "\n".join(summary_parts)
        return ""

    async def execute_deepsearch_workflow(self, question: str, max_rounds: int = 5, 
                                        num_results: int = 10, stream: bool = False):
        """
        执行完整的DeepSearch工作流
        
        Args:
            question: 用户问题
            max_rounds: 最大搜索轮数
            num_results: 每轮搜索结果数
            stream: 是否流式返回
            
        Returns:
            完整的DeepSearch执行结果
        """
        workflow_result = {
            "question": question,
            "rounds": [],
            "final_answer": "",
            "extracted_content": [],
            "workflow_completed": False,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            logger.info(f"开始DeepSearch工作流：{question[:50]}...")
            all_extracted_content = []
            
            for round_num in range(1, max_rounds + 1):
                logger.info(f"=== DeepSearch工作流第{round_num}轮 ===")
                
                # 1. Search阶段：SERP搜索
                if round_num == 1:
                    search_query = question
                else:
                    last_decision = workflow_result["rounds"][-1]["decision"]
                    search_query = last_decision.get("next_query", question)
                
                search_results, search_success = await self.search_phase(search_query, num_results)
                
                if not search_success:
                    logger.error("搜索失败，尝试继续...")
                    continue
                
                # 2. Select阶段：智能体评估
                previous_knowledge = self._build_previous_knowledge_summary(all_extracted_content)
                decision = await self.select_phase(question, search_results, round_num, max_rounds, previous_knowledge)
                
                # 3. Crawl阶段：爬取选定网页
                important_url_ids = decision.get("important_urls", [])
                url_mapping = decision.get("url_mapping", {})
                
                selected_urls = []
                for url_id in important_url_ids:
                    if url_id in url_mapping:
                        selected_urls.append(url_mapping[url_id].get("link", ""))
                
                extracted_content = []
                if selected_urls:
                    # 使用并行爬取
                    crawled_content = await self.crawl_selected_urls_parallel(selected_urls)
                    
                    # 4. Extract阶段：提取重要内容
                    task_context = f"已完成{round_num}轮搜索，正在深度分析相关内容"
                    extracted_content = await self.extract_important_content_with_task_focus(
                        question, crawled_content, task_context
                    )
                    all_extracted_content.extend(extracted_content)
                
                # 记录本轮结果
                round_result = {
                    "round": round_num,
                    "search_query": search_query,
                    "search_results_count": len(search_results),
                    "selected_urls": selected_urls,
                    "extracted_content_count": len(extracted_content) if selected_urls else 0,
                    "decision": decision,
                    "timestamp": datetime.now().isoformat()
                }
                workflow_result["rounds"].append(round_result)
                
                # 检查是否搜索完成
                if decision.get("search_complete", False):
                    logger.info(f"智能体判断信息充足，停止搜索（第{round_num}轮）")
                    break
                else:
                    logger.info(f"智能体判断需要更多信息，继续搜索...")
                    if not decision.get("next_query"):
                        logger.warning("智能体未提供下一个搜索查询，使用原问题")
                        decision["next_query"] = question
            
            # 5. Synthesize阶段：生成最终答案
            workflow_result["extracted_content"] = all_extracted_content
            
            if all_extracted_content:
                if stream:
                    final_result = {}
                    async for chunk in self.synthesize_phase_with_structured_output(question, all_extracted_content, stream=True):
                        if isinstance(chunk, dict) and "final_answer" in chunk:
                            final_result = chunk
                            workflow_result.update(final_result)
                        else:
                            yield chunk
                else:
                    async for result in self.synthesize_phase_with_structured_output(question, all_extracted_content, stream=False):
                        if isinstance(result, dict) and "final_answer" in result:
                            workflow_result.update(result)
                            break
            else:
                workflow_result["final_answer"] = "抱歉，没有成功获取到相关信息来回答您的问题。"
            
            workflow_result["workflow_completed"] = True
            workflow_result["end_time"] = datetime.now().isoformat()
            logger.info("DeepSearch工作流执行完成")
            
            if stream:
                yield {"workflow_result": workflow_result}
            else:
                yield workflow_result
            
        except Exception as e:
            logger.error(f"DeepSearch工作流执行失败：{e}")
            workflow_result["error"] = str(e)
            workflow_result["final_answer"] = f"抱歉，在处理您的问题时遇到错误：{e}"
            if stream:
                yield {"workflow_result": workflow_result}
            else:
                yield workflow_result
        finally:
            # 清理clients
            await self._cleanup_clients()