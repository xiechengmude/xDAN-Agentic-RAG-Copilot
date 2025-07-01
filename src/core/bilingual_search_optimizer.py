#!/usr/bin/env python3
"""
双语搜索优化器
支持中英文查询的智能转换和优化
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class BilingualSearchOptimizer:
    """双语搜索优化器 - 支持中英文查询"""
    
    def __init__(self):
        # 财务术语映射
        self.finance_terms = {
            '财报': ['financial report', 'earnings report', '财务报告'],
            '年报': ['annual report', '年度报告'],
            '季报': ['quarterly report', '季度报告'],
            '营收': ['revenue', '收入'],
            '利润': ['profit', 'earnings', '净利润'],
            '市值': ['market cap', 'market capitalization', '市场价值'],
            '股价': ['stock price', 'share price', '股票价格'],
            'ROE': ['return on equity', '净资产收益率'],
            '财务数据': ['financial data', 'financial metrics', '财务指标']
        }
        
        # 时间术语映射
        self.time_terms = {
            '最近': ['recent', 'latest', '近期'],
            '最新': ['latest', 'newest', '最新的'],
            '今年': ['this year', 'current year', str(datetime.now().year)],
            '去年': ['last year', 'previous year', str(datetime.now().year - 1)],
            '本月': ['this month', 'current month'],
            '上月': ['last month', 'previous month'],
            '本季度': ['this quarter', 'current quarter', 'Q' + str((datetime.now().month - 1) // 3 + 1)],
            '上季度': ['last quarter', 'previous quarter'],
            '第一季度': ['Q1', 'first quarter', '1st quarter'],
            '第二季度': ['Q2', 'second quarter', '2nd quarter'],
            '第三季度': ['Q3', 'third quarter', '3rd quarter'],
            '第四季度': ['Q4', 'fourth quarter', '4th quarter']
        }
        
        # 公司名称映射
        self.company_names = {
            '比亚迪': ['BYD', 'Build Your Dreams', '比亚迪汽车'],
            '特斯拉': ['Tesla', 'TSLA', 'Tesla Motors'],
            '苹果': ['Apple', 'AAPL', 'Apple Inc'],
            '谷歌': ['Google', 'GOOGL', 'Alphabet'],
            '微软': ['Microsoft', 'MSFT', 'Microsoft Corporation'],
            '阿里巴巴': ['Alibaba', 'BABA', 'Alibaba Group'],
            '腾讯': ['Tencent', 'TCEHY', '腾讯控股'],
            '百度': ['Baidu', 'BIDU', '百度公司']
        }
        
        # 领域术语映射
        self.domain_terms = {
            # 新能源汽车
            '新能源汽车': ['new energy vehicle', 'NEV', 'electric vehicle', 'EV'],
            '电动汽车': ['electric vehicle', 'EV', 'electric car'],
            '销量': ['sales', 'sales volume', '销售量'],
            '市场份额': ['market share', 'market percentage'],
            
            # AI领域
            '人工智能': ['artificial intelligence', 'AI'],
            '机器学习': ['machine learning', 'ML'],
            '深度学习': ['deep learning', 'DL'],
            '大语言模型': ['large language model', 'LLM'],
            
            # 通用商业术语
            '分析': ['analysis', 'analyze', '研究'],
            '报告': ['report', 'research', '研报'],
            '趋势': ['trend', 'tendency', '走势'],
            '预测': ['forecast', 'prediction', '预估']
        }
        
        logger.info("双语搜索优化器初始化完成")
    
    def optimize_bilingual_query(self, query: str, target_language: str = 'auto') -> Dict[str, any]:
        """
        优化双语查询
        
        Args:
            query: 原始查询
            target_language: 目标语言 (auto/zh/en/both)
            
        Returns:
            优化后的查询信息
        """
        # 检测查询语言
        query_language = self._detect_language(query)
        
        # 识别关键实体
        entities = self._extract_entities(query)
        
        # 根据目标语言生成查询
        if target_language == 'auto':
            # 自动决定：如果是中文查询，生成双语版本
            if query_language == 'zh':
                target_language = 'both'
            else:
                target_language = query_language
        
        result = {
            'original': query,
            'language': query_language,
            'entities': entities,
            'queries': {}
        }
        
        if target_language in ['zh', 'both']:
            result['queries']['zh'] = self._generate_chinese_query(query, entities)
        
        if target_language in ['en', 'both']:
            result['queries']['en'] = self._generate_english_query(query, entities)
        
        if target_language == 'both':
            result['queries']['combined'] = self._generate_combined_query(
                result['queries']['zh'],
                result['queries']['en'],
                entities
            )
        
        return result
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 简单的中英文检测
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 'unknown'
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'zh'
        else:
            return 'en'
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """提取查询中的关键实体"""
        entities = {
            'companies': [],
            'finance_terms': [],
            'time_terms': [],
            'domain_terms': []
        }
        
        query_lower = query.lower()
        
        # 提取公司名
        for zh_name, variations in self.company_names.items():
            if zh_name in query or any(v.lower() in query_lower for v in variations):
                entities['companies'].append(zh_name)
        
        # 提取财务术语
        for zh_term, variations in self.finance_terms.items():
            if zh_term in query or any(v.lower() in query_lower for v in variations):
                entities['finance_terms'].append(zh_term)
        
        # 提取时间术语
        for zh_term, variations in self.time_terms.items():
            if zh_term in query or any(v.lower() in query_lower for v in variations):
                entities['time_terms'].append(zh_term)
        
        # 提取领域术语
        for zh_term, variations in self.domain_terms.items():
            if zh_term in query or any(v.lower() in query_lower for v in variations):
                entities['domain_terms'].append(zh_term)
        
        return entities
    
    def _generate_chinese_query(self, original: str, entities: Dict) -> str:
        """生成中文优化查询"""
        # 如果原始查询已经是中文，进行优化
        if self._detect_language(original) == 'zh':
            query_parts = [original]
            
            # 添加相关中文关键词
            if entities['finance_terms']:
                # 添加更多财务相关词
                additional_terms = ['财务分析', '业绩', '财务状况']
                query_parts.extend([t for t in additional_terms if t not in original])
            
            return ' '.join(query_parts[:3])  # 限制关键词数量
        
        else:
            # 英文转中文
            translated_parts = []
            
            # 翻译公司名
            for company in entities['companies']:
                if company in self.company_names:
                    translated_parts.append(company)
            
            # 翻译财务术语
            for term in entities['finance_terms']:
                # 反向查找中文
                for zh_term, variations in self.finance_terms.items():
                    if term in variations:
                        translated_parts.append(zh_term)
                        break
            
            # 保留时间信息
            for time_term in entities['time_terms']:
                for zh_term, variations in self.time_terms.items():
                    if time_term in variations:
                        translated_parts.append(zh_term)
                        break
            
            return ' '.join(translated_parts)
    
    def _generate_english_query(self, original: str, entities: Dict) -> str:
        """生成英文优化查询"""
        if self._detect_language(original) == 'en':
            # 已经是英文，进行优化
            query_parts = [original]
            
            # 添加相关英文关键词
            if entities['finance_terms']:
                additional_terms = ['financial analysis', 'performance']
                query_parts.extend([t for t in additional_terms if t not in original.lower()])
            
            return ' '.join(query_parts[:3])
        
        else:
            # 中文转英文
            translated_parts = []
            remaining_text = original
            
            # 替换已识别的实体
            replacements = []
            
            # 处理公司名
            for company in entities['companies']:
                if company in self.company_names:
                    # 使用英文名（第一个变体）
                    english_name = self.company_names[company][0]
                    replacements.append((company, english_name))
            
            # 处理财务术语
            for term in entities['finance_terms']:
                if term in self.finance_terms:
                    english_term = self.finance_terms[term][0]
                    replacements.append((term, english_term))
            
            # 处理时间术语
            for term in entities['time_terms']:
                if term in self.time_terms:
                    english_term = self.time_terms[term][0]
                    replacements.append((term, english_term))
            
            # 处理领域术语
            for term in entities['domain_terms']:
                if term in self.domain_terms:
                    english_term = self.domain_terms[term][0]
                    replacements.append((term, english_term))
            
            # 应用替换
            for zh_term, en_term in replacements:
                remaining_text = remaining_text.replace(zh_term, en_term)
            
            return remaining_text
    
    def _generate_combined_query(self, zh_query: str, en_query: str, entities: Dict) -> str:
        """生成中英文组合查询"""
        # 策略1：核心词汇使用双语，提高召回率
        combined_parts = []
        
        # 公司名使用双语
        for company in entities['companies']:
            if company in self.company_names:
                zh_name = company
                en_name = self.company_names[company][0]
                combined_parts.append(f"({zh_name} OR {en_name})")
        
        # 关键财务术语使用双语
        for term in entities['finance_terms'][:2]:  # 限制数量
            if term in self.finance_terms:
                zh_term = term
                en_term = self.finance_terms[term][0]
                combined_parts.append(f"({zh_term} OR {en_term})")
        
        # 时间信息使用统一格式
        if entities['time_terms']:
            # 使用数字格式，如 2025 Q2
            year = datetime.now().year
            for term in entities['time_terms']:
                if '季度' in term or 'quarter' in term.lower():
                    # 提取季度信息
                    if '第一' in term or 'Q1' in term or 'first' in term.lower():
                        combined_parts.append(f"{year} Q1")
                    elif '第二' in term or 'Q2' in term or 'second' in term.lower():
                        combined_parts.append(f"{year} Q2")
                    elif '第三' in term or 'Q3' in term or 'third' in term.lower():
                        combined_parts.append(f"{year} Q3")
                    elif '第四' in term or 'Q4' in term or 'fourth' in term.lower():
                        combined_parts.append(f"{year} Q4")
                elif '今年' in term or 'this year' in term.lower():
                    combined_parts.append(str(year))
        
        return ' '.join(combined_parts)
    
    def suggest_search_variants(self, query: str) -> List[Dict[str, str]]:
        """建议多个搜索变体"""
        base_optimization = self.optimize_bilingual_query(query, 'both')
        variants = []
        
        # 变体1：纯中文
        if 'zh' in base_optimization['queries']:
            variants.append({
                'type': 'chinese',
                'query': base_optimization['queries']['zh'],
                'description': '中文搜索（国内资源）'
            })
        
        # 变体2：纯英文
        if 'en' in base_optimization['queries']:
            variants.append({
                'type': 'english',
                'query': base_optimization['queries']['en'],
                'description': '英文搜索（国际资源）'
            })
        
        # 变体3：双语组合
        if 'combined' in base_optimization['queries']:
            variants.append({
                'type': 'bilingual',
                'query': base_optimization['queries']['combined'],
                'description': '双语搜索（最大覆盖）'
            })
        
        # 变体4：专业搜索（添加专业术语）
        professional_query = self._generate_professional_query(query, base_optimization['entities'])
        if professional_query:
            variants.append({
                'type': 'professional',
                'query': professional_query,
                'description': '专业搜索（深度内容）'
            })
        
        return variants
    
    def _generate_professional_query(self, query: str, entities: Dict) -> Optional[str]:
        """生成专业搜索查询"""
        if not entities['finance_terms'] and not entities['domain_terms']:
            return None
        
        professional_parts = []
        
        # 添加专业财务术语
        if entities['finance_terms']:
            professional_parts.extend([
                'financial statement',
                'investor relations',
                'SEC filing',
                '投资者关系'
            ])
        
        # 添加来源限定
        if entities['companies']:
            professional_parts.append('(site:pdf OR filetype:pdf OR site:investor)')
        
        # 组合原始查询和专业术语
        return f"{query} {' '.join(professional_parts[:3])}"


# 集成到搜索策略
class BilingualSearchStrategy:
    """双语搜索策略"""
    
    def __init__(self, search_strategy, bilingual_optimizer):
        self.search_strategy = search_strategy
        self.bilingual_optimizer = bilingual_optimizer
    
    def optimize_for_language(self, query: str, target_language: str = 'auto') -> Dict[str, any]:
        """
        为特定语言优化查询
        
        Returns:
            {
                'original': 原始查询,
                'variants': 查询变体列表,
                'recommended': 推荐的查询,
                'search_strategy': 搜索策略
            }
        """
        # 1. 基础搜索优化
        base_optimization = self.search_strategy.optimize_search_query(query)
        
        # 2. 双语优化
        bilingual_optimization = self.bilingual_optimizer.optimize_bilingual_query(
            query, target_language
        )
        
        # 3. 生成搜索变体
        variants = self.bilingual_optimizer.suggest_search_variants(query)
        
        # 4. 选择推荐查询
        # 根据实体识别结果推荐最合适的变体
        recommended = self._select_recommended_query(
            bilingual_optimization['entities'],
            variants
        )
        
        return {
            'original': query,
            'variants': variants,
            'recommended': recommended,
            'optimization': {
                'search': base_optimization,
                'bilingual': bilingual_optimization
            }
        }
    
    def _select_recommended_query(self, entities: Dict, variants: List[Dict]) -> str:
        """选择推荐的查询"""
        # 如果有公司名和财务术语，推荐双语搜索
        if entities['companies'] and entities['finance_terms']:
            bilingual_variant = next(
                (v for v in variants if v['type'] == 'bilingual'), 
                None
            )
            if bilingual_variant:
                return bilingual_variant['query']
        
        # 如果只有中文实体，推荐中文搜索
        if self._has_chinese_entities(entities):
            chinese_variant = next(
                (v for v in variants if v['type'] == 'chinese'), 
                None
            )
            if chinese_variant:
                return chinese_variant['query']
        
        # 默认推荐第一个变体
        return variants[0]['query'] if variants else ''
    
    def _has_chinese_entities(self, entities: Dict) -> bool:
        """检查是否包含中文实体"""
        for category in entities.values():
            for entity in category:
                if re.search(r'[\u4e00-\u9fff]', entity):
                    return True
        return False


# 测试示例
if __name__ == "__main__":
    optimizer = BilingualSearchOptimizer()
    
    test_queries = [
        "比亚迪最近财报",
        "Tesla Q2 earnings report",
        "苹果公司今年市值",
        "新能源汽车销量分析",
        "AI大模型最新进展"
    ]
    
    for query in test_queries:
        print(f"\n原始查询: {query}")
        result = optimizer.optimize_bilingual_query(query, 'both')
        
        print(f"检测语言: {result['language']}")
        print(f"识别实体: {result['entities']}")
        
        if 'zh' in result['queries']:
            print(f"中文查询: {result['queries']['zh']}")
        if 'en' in result['queries']:
            print(f"英文查询: {result['queries']['en']}")
        if 'combined' in result['queries']:
            print(f"双语查询: {result['queries']['combined']}")
        
        print("\n搜索变体建议:")
        variants = optimizer.suggest_search_variants(query)
        for v in variants:
            print(f"  - {v['description']}: {v['query']}")