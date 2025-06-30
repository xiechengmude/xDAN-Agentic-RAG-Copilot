#!/usr/bin/env python3
"""
FlashSearch 搜索策略模块
负责问题分析、关键词增强、搜索算子优化
遵循KISS+DRY原则，易于维护和扩展
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SearchStrategy:
    """FlashSearch搜索策略管理器"""
    
    def __init__(self):
        """初始化搜索策略"""
        # 时间关键词
        self.time_keywords = ['最新', '最近', '今年', '2024', '2025', '当前', '现在']
        
        # 领域识别配置
        self.domain_config = {
            'finance': {
                'indicators': ['财报', '财务', '收入', '利润', '营收', '业绩', 'roe', '市值', '股价', '季报', '年报'],
                'keywords': ['财报', '年报', '季报', 'financial report', 'earnings'],
                'boost_words': ['年报', '季报', '财务数据']
            },
            'academic': {
                'indicators': ['研究', '分析', '报告', '调研', '数据', '统计', '论文', '学术'],
                'keywords': ['research', 'analysis', 'report', 'study'],
                'boost_words': ['报告', '数据', '研究']
            },
            'technology': {
                'indicators': ['技术', '开发', 'api', '文档', '教程', '编程', '代码', '软件'],
                'keywords': ['documentation', 'tutorial', 'guide', 'manual'],
                'boost_words': ['官方文档', '开发者文档']
            },
            'policy': {
                'indicators': ['政策', '法规', '条例', '监管', '规定', '政府', '部委'],
                'keywords': ['policy', 'regulation', 'government'],
                'boost_words': ['官方', '政府', '政策文件']
            },
            'market': {
                'indicators': ['市场', '行业', '趋势', '预测', '竞争', '份额'],
                'keywords': ['market', 'industry', 'trend', 'forecast'],
                'boost_words': ['行业报告', '市场分析']
            },
            'news': {
                'indicators': ['新闻', '事件', '突发', '最新消息', '报道', '采访', '评论', '最新进展', '动态', '快讯'],
                'keywords': ['news', 'breaking', 'latest', 'report', 'update'],
                'boost_words': ['最新报道', '深度分析', '独家新闻'],
                'authority_sites': {
                    'cn': ['sina.com.cn', 'qq.com', '163.com', 'people.com.cn', 'xinhuanet.com', 'caixin.com', 'thepaper.cn'],
                    'us': ['nytimes.com', 'wsj.com', 'reuters.com', 'bloomberg.com', 'cnn.com', 'apnews.com'],
                    'uk': ['bbc.com', 'ft.com', 'theguardian.com', 'economist.com'],
                    'finance': ['finance.sina.com.cn', 'finance.qq.com', 'eastmoney.com', 'wallstreeteen.com', 'cnbc.com']
                }
            }
        }
        
        # 搜索算子配置
        self.search_operators = {
            'site_restrictions': {
                'government': ['政策', '法规', '条例', '监管', '官方'],
                'academic': ['研究', '论文', '学术', '期刊'],
                'documentation': ['文档', 'api', '教程', '手册'],
                'finance': ['财报', '金融', '投资']
            },
            'file_types': {
                'pdf': ['报告', '文档', '手册', '财报'],
                'doc': ['政策', '法规', '条例']
            },
            'time_filters': {
                'recent': ['最新', '最近', '当前'],
                'yearly': ['2024', '2025', '今年']
            }
        }
        
        logger.info("搜索策略模块初始化完成")
    
    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        分析问题特征
        
        Args:
            question: 用户问题
            
        Returns:
            问题分析结果
        """
        question_lower = question.lower()
        
        analysis = {
            'original_question': question,
            'detected_domain': None,
            'has_time_context': False,
            'question_type': 'general',
            'complexity': 'simple',
            'suggested_operators': []
        }
        
        # 检测时间上下文
        analysis['has_time_context'] = any(kw in question for kw in self.time_keywords)
        
        # 检测领域
        for domain, config in self.domain_config.items():
            if any(indicator in question_lower for indicator in config['indicators']):
                analysis['detected_domain'] = domain
                break
        
        # 检测问题类型
        if '?' in question or '如何' in question or '怎么' in question:
            analysis['question_type'] = 'how_to'
        elif '什么' in question or 'what' in question_lower:
            analysis['question_type'] = 'definition'
        elif '分析' in question or '对比' in question:
            analysis['question_type'] = 'analysis'
        elif '最新' in question or '趋势' in question:
            analysis['question_type'] = 'trend'
        
        # 评估复杂度
        if len(question) > 20 or '分析' in question or '对比' in question:
            analysis['complexity'] = 'complex'
        
        logger.debug(f"[问题分析] {question} → 领域: {analysis['detected_domain']}, 类型: {analysis['question_type']}")
        
        return analysis
    
    def enhance_with_time_context(self, question: str, analysis: Dict[str, Any]) -> str:
        """
        添加时间上下文
        
        Args:
            question: 原始问题
            analysis: 问题分析结果
            
        Returns:
            时间增强后的问题
        """
        if analysis['has_time_context']:
            return question
        
        current_year = datetime.now().year
        enhanced_question = f"{question} {current_year}"
        
        logger.debug(f"[时间增强] {question} → {enhanced_question}")
        return enhanced_question
    
    def enhance_with_domain_keywords(self, question: str, analysis: Dict[str, Any]) -> str:
        """
        添加领域相关关键词
        
        Args:
            question: 时间增强后的问题
            analysis: 问题分析结果
            
        Returns:
            领域增强后的问题
        """
        detected_domain = analysis['detected_domain']
        
        if not detected_domain:
            return question
        
        domain_config = self.domain_config[detected_domain]
        boost_words = domain_config['boost_words']
        
        # 根据问题类型选择合适的增强词
        if analysis['question_type'] == 'analysis' and detected_domain == 'finance':
            enhanced_question = f"{question} {' '.join(boost_words[:2])}"
        elif analysis['question_type'] == 'trend' and detected_domain == 'market':
            enhanced_question = f"{question} {boost_words[0]}"
        elif detected_domain == 'technology':
            enhanced_question = f"{question} {boost_words[0]}"
        else:
            # 默认添加第一个增强词
            enhanced_question = f"{question} {boost_words[0]}"
        
        logger.debug(f"[领域增强-{detected_domain}] {question} → {enhanced_question}")
        return enhanced_question
    
    def add_search_operators(self, question: str, analysis: Dict[str, Any]) -> str:
        """
        添加搜索算子
        
        Args:
            question: 领域增强后的问题
            analysis: 问题分析结果
            
        Returns:
            添加搜索算子后的问题
        """
        question_lower = question.lower()
        operators = []
        
        # 站点限定
        if analysis['detected_domain'] == 'policy':
            operators.append("site:gov.cn")
        elif analysis['detected_domain'] == 'academic':
            operators.append("(site:edu.cn OR site:org)")
        elif analysis['detected_domain'] == 'technology':
            operators.append("(site:docs OR site:developer OR site:github.com)")
        elif analysis['detected_domain'] == 'news':
            # 构建新闻网站限定
            news_sites = []
            news_config = self.domain_config['news']['authority_sites']
            # 优先使用中文权威媒体
            news_sites.extend([f"site:{site}" for site in news_config['cn'][:3]])
            # 添加国际媒体
            news_sites.extend([f"site:{site}" for site in news_config['us'][:2]])
            # 如果是财经相关，添加财经媒体
            if any(kw in question_lower for kw in ['财经', '股票', '金融', '市场']):
                news_sites.extend([f"site:{site}" for site in news_config['finance'][:2]])
            if news_sites:
                operators.append(f"({' OR '.join(news_sites[:5])})")  # 限制最多5个网站
        
        # 时间限定
        if any(kw in question_lower for kw in ['最新', '2024', '2025']) and not analysis['has_time_context']:
            current_year = datetime.now().year
            operators.append(f"after:{current_year-1}")
        
        # 文件类型限定
        if analysis['detected_domain'] in ['finance', 'academic'] and analysis['complexity'] == 'complex':
            operators.append("filetype:pdf")
        
        # 精确匹配（对于特定术语）
        if analysis['detected_domain'] == 'finance' and any(kw in question_lower for kw in ['财报', 'roe']):
            # 为财报等关键词添加精确匹配
            pass  # 简化版本暂不添加引号，避免过度限制
        
        # 组合所有算子
        if operators:
            enhanced_question = f"{' '.join(operators)} {question}"
            logger.debug(f"[搜索算子] 添加: {operators}")
        else:
            enhanced_question = question
        
        return enhanced_question
    
    def optimize_search_query(self, question: str) -> Dict[str, Any]:
        """
        完整的搜索查询优化流程
        
        Args:
            question: 原始问题
            
        Returns:
            优化结果字典
        """
        # 1. 分析问题特征
        analysis = self.analyze_question(question)
        
        # 2. 逐步增强
        step1_time = self.enhance_with_time_context(question, analysis)
        step2_domain = self.enhance_with_domain_keywords(step1_time, analysis)
        step3_operators = self.add_search_operators(step2_domain, analysis)
        
        result = {
            'original_question': question,
            'optimized_question': step3_operators,
            'analysis': analysis,
            'optimization_steps': {
                'time_enhanced': step1_time,
                'domain_enhanced': step2_domain,
                'operator_enhanced': step3_operators
            }
        }
        
        logger.info(f"[搜索优化完成] {question} → {step3_operators}")
        
        return result
    
    def optimize_search_query_alternative(self, question: str) -> Dict[str, Any]:
        """
        备选搜索策略优化流程（用于重试）
        使用不同的优化策略：
        1. 更激进的关键词扩展
        2. 不同的搜索算子组合
        3. 更宽泛的时间范围
        
        Args:
            question: 原始问题
            
        Returns:
            优化结果字典
        """
        # 1. 分析问题特征
        analysis = self.analyze_question(question)
        
        # 2. 备选策略：更宽泛的搜索
        # 2.1 扩展时间范围（不限定具体年份）
        step1_time = question
        if any(kw in question for kw in ['最新', '最近', '当前']):
            step1_time = question + " recent latest 近期"
        
        # 2.2 添加更多领域同义词
        step2_domain = step1_time
        if analysis.get('detected_domain'):
            domain = analysis['detected_domain']
            config = self.domain_config.get(domain, {})
            
            # 添加更多同义词和相关词
            if domain == 'finance':
                step2_domain += " financial report earnings revenue 财务报告 业绩公告"
            elif domain == 'academic':
                step2_domain += " research paper study analysis 研究论文 学术报告"
            elif domain == 'technology':
                step2_domain += " documentation tutorial guide API docs 技术文档"
            elif domain == 'policy':
                step2_domain += " policy regulation official government 政策法规 官方文件"
            elif domain == 'market':
                step2_domain += " market analysis industry report 市场分析 行业研究"
            elif domain == 'news':
                step2_domain += " news breaking latest 新闻 最新报道 深度分析"
        
        # 2.3 使用不同的搜索算子组合
        step3_operators = step2_domain
        if analysis.get('detected_domain'):
            # 使用OR操作符扩大搜索范围
            if analysis['detected_domain'] == 'finance':
                step3_operators = f'("{question}" OR "财报" OR "年报" OR "financial report")'
            elif analysis['detected_domain'] == 'policy':
                # 不限定特定网站，扩大搜索范围
                step3_operators = f'"{question}" 政策 官方'
            elif analysis['detected_domain'] == 'technology':
                # 搜索多种文档类型
                step3_operators = f'"{question}" (documentation OR tutorial OR guide)'
            elif analysis['detected_domain'] == 'news':
                # 新闻类使用更宽泛的搜索，不限定特定网站
                step3_operators = f'"{question}" (news OR 新闻 OR 报道 OR breaking)'
        
        result = {
            'original_question': question,
            'optimized_question': step3_operators,
            'analysis': analysis,
            'strategy': 'alternative',
            'optimization_steps': {
                'time_enhanced': step1_time,
                'domain_enhanced': step2_domain,
                'operator_enhanced': step3_operators
            }
        }
        
        logger.info(f"[备选策略优化] {question} → {step3_operators}")
        
        return result
    
    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """
        获取指定领域的配置
        
        Args:
            domain: 领域名称
            
        Returns:
            领域配置字典
        """
        return self.domain_config.get(domain, {})
    
    def add_custom_domain(self, domain: str, config: Dict[str, Any]):
        """
        添加自定义领域配置
        
        Args:
            domain: 领域名称
            config: 领域配置
        """
        self.domain_config[domain] = config
        logger.info(f"添加自定义领域: {domain}")
    
    def update_domain_config(self, domain: str, updates: Dict[str, Any]):
        """
        更新领域配置
        
        Args:
            domain: 领域名称
            updates: 更新内容
        """
        if domain in self.domain_config:
            self.domain_config[domain].update(updates)
            logger.info(f"更新领域配置: {domain}")
        else:
            logger.warning(f"领域不存在: {domain}")


# 全局搜索策略实例
search_strategy = SearchStrategy()