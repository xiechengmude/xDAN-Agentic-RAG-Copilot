#!/usr/bin/env python3
"""
搜索算子适配器
根据下游系统生成合适的搜索格式
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class SearchOperatorAdapter:
    """搜索算子适配器 - 为不同搜索系统生成合适的格式"""
    
    def __init__(self):
        # Google搜索时间参数映射
        self.google_time_params = {
            'hour': 'qdr:h',      # 过去1小时
            'day': 'qdr:d',       # 过去24小时  
            'week': 'qdr:w',      # 过去一周
            'month': 'qdr:m',     # 过去一个月
            'year': 'qdr:y',      # 过去一年
        }
    
    def adapt_for_brightdata(self, query: str, time_range: Optional[Dict] = None) -> Dict[str, any]:
        """
        为BrightData适配查询（实际是Google搜索）
        
        Args:
            query: 原始查询
            time_range: 时间范围信息（包含start_date, end_date等）
            
        Returns:
            适配后的查询信息
        """
        adapted = {
            'query': query,
            'url_params': {},
            'search_options': {}
        }
        
        if time_range:
            # 方案1：使用Google的时间过滤参数
            tbs_param = self._generate_google_tbs(time_range)
            if tbs_param:
                adapted['url_params']['tbs'] = tbs_param
                logger.info(f"[BrightData适配] 添加时间参数: tbs={tbs_param}")
            
            # 方案2：在查询中添加时间关键词（更可靠）
            time_keywords = self._generate_time_keywords(time_range)
            if time_keywords:
                # 将时间关键词添加到查询中
                adapted['query'] = f"{query} {' '.join(time_keywords)}"
                logger.info(f"[BrightData适配] 查询增强: {adapted['query']}")
        
        return adapted
    
    def _generate_google_tbs(self, time_range: Dict) -> Optional[str]:
        """
        生成Google的tbs（时间）参数
        
        Google支持的格式：
        - tbs=qdr:d  过去24小时
        - tbs=qdr:w  过去一周
        - tbs=qdr:m  过去一个月
        - tbs=qdr:y  过去一年
        - tbs=cdr:1,cd_min:3/1/2025,cd_max:7/1/2025  自定义范围
        """
        if not time_range:
            return None
            
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        
        if not start_date or not end_date:
            return None
        
        # 计算时间差（处理时区）
        if hasattr(start_date, 'tzinfo') and start_date.tzinfo:
            # 如果start_date有时区，使用带时区的now
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            # 使用不带时区的now
            now = datetime.now()
        
        time_diff = now - start_date
        
        # 如果是标准时间范围，使用qdr参数
        if time_diff.days <= 1:
            return 'qdr:d'
        elif time_diff.days <= 7:
            return 'qdr:w'
        elif time_diff.days <= 30:
            return 'qdr:m'
        elif time_diff.days <= 365:
            return 'qdr:y'
        else:
            # 自定义时间范围
            # 格式：cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY
            start_str = start_date.strftime('%-m/%-d/%Y')  # 美式日期格式
            end_str = end_date.strftime('%-m/%-d/%Y')
            return f'cdr:1,cd_min:{start_str},cd_max:{end_str}'
    
    def _generate_time_keywords(self, time_range: Dict) -> List[str]:
        """
        生成时间关键词（更通用的方案）
        """
        keywords = []
        
        if not time_range:
            return keywords
            
        start_date = time_range.get('start_date')
        end_date = time_range.get('end_date')
        description = time_range.get('description', '')
        
        if start_date and end_date:
            # 年份
            year = start_date.year
            keywords.append(str(year))
            
            # 如果是季度
            if '季度' in description or 'quarter' in time_range.get('type', ''):
                quarter = (start_date.month - 1) // 3 + 1
                keywords.extend([
                    f'{year}Q{quarter}',
                    f'{year}年第{quarter}季度'
                ])
            
            # 如果是特定月份
            elif start_date.month == end_date.month:
                keywords.append(f'{year}年{start_date.month}月')
        
        return keywords[:2]  # 最多返回2个关键词，避免过度限制
    
    def adapt_for_google_direct(self, query: str, time_range: Optional[Dict] = None) -> str:
        """
        为直接Google搜索适配（生成完整URL）
        """
        # URL编码查询
        encoded_query = quote_plus(query)
        base_url = f"https://www.google.com/search?q={encoded_query}"
        
        params = []
        
        if time_range:
            # 添加时间参数
            tbs = self._generate_google_tbs(time_range)
            if tbs:
                params.append(f"tbs={tbs}")
        
        if params:
            return f"{base_url}&{'&'.join(params)}"
        
        return base_url
    
    def generate_universal_query(self, query: str, time_info: Dict) -> str:
        """
        生成通用的查询（不依赖特定算子）
        
        Args:
            query: 原始查询
            time_info: 时间信息（从EnhancedTimeAware返回）
            
        Returns:
            增强的查询字符串
        """
        # 从time_info中提取信息
        time_refs = time_info.get('time_references', [])
        financial_terms = time_info.get('financial_terms', [])
        
        # 构建查询部分
        query_parts = [query]
        
        # 添加时间关键词
        if time_refs:
            for ref in time_refs[:1]:  # 只使用第一个时间引用
                time_keywords = self._generate_time_keywords(ref.get('range', {}))
                query_parts.extend(time_keywords)
        
        # 添加财务相关词
        if financial_terms:
            # 使用括号包含OR逻辑
            query_parts.append(f"({' OR '.join(financial_terms[:2])})")
        
        return ' '.join(query_parts)
    
    def build_search_url_with_time(self, query: str, time_range: Optional[Dict] = None, 
                                  search_type: str = 'web', **kwargs) -> str:
        """
        构建包含时间过滤的搜索URL（供BrightData使用）
        """
        # 适配查询
        adapted = self.adapt_for_brightdata(query, time_range)
        
        # URL编码
        encoded_query = quote_plus(adapted['query'])
        
        # 基础URL
        if search_type == 'academic':
            base_url = f"https://scholar.google.com/scholar?q={encoded_query}"
        else:
            base_url = f"https://www.google.com/search?q={encoded_query}"
        
        # 添加参数
        params = []
        
        # 时间参数
        if 'tbs' in adapted['url_params']:
            params.append(f"tbs={adapted['url_params']['tbs']}")
        
        # 其他参数
        if 'num_results' in kwargs:
            params.append(f"num={kwargs['num_results']}")
        if 'language' in kwargs:
            params.append(f"hl={kwargs['language']}")
        
        if params:
            return f"{base_url}&{'&'.join(params)}"
        
        return base_url


# 集成到搜索策略
class TimeAwareSearchStrategy:
    """时间感知的搜索策略"""
    
    def __init__(self, time_aware, operator_adapter):
        self.time_aware = time_aware
        self.operator_adapter = operator_adapter
    
    def optimize_query_for_search(self, query: str) -> Dict[str, any]:
        """
        优化查询以适配搜索系统
        
        Returns:
            {
                'original': 原始查询,
                'brightdata': BrightData适配的查询,
                'universal': 通用查询（关键词增强）,
                'time_range': 时间范围信息,
                'search_url': 构建的搜索URL
            }
        """
        # 1. 使用增强时间感知分析查询
        time_info = self.time_aware.enhance_query_with_time(query)
        
        # 2. 获取时间范围
        time_range = None
        if time_info['time_references']:
            time_range = time_info['time_references'][0]['range']
        
        # 3. 为BrightData适配
        brightdata_adapted = self.operator_adapter.adapt_for_brightdata(query, time_range)
        
        # 4. 生成通用查询
        universal_query = self.operator_adapter.generate_universal_query(query, time_info)
        
        # 5. 构建搜索URL
        search_url = self.operator_adapter.build_search_url_with_time(
            query, time_range, num_results=12
        )
        
        return {
            'original': query,
            'brightdata': brightdata_adapted,
            'universal': universal_query,
            'time_range': time_range,
            'search_url': search_url,
            'time_info': time_info
        }


# 测试示例
if __name__ == "__main__":
    from enhanced_time_aware import EnhancedTimeAware
    
    # 创建实例
    time_aware = EnhancedTimeAware()
    adapter = SearchOperatorAdapter()
    strategy = TimeAwareSearchStrategy(time_aware, adapter)
    
    # 测试查询
    test_queries = [
        "比亚迪最近财报",
        "特斯拉上季度销量",
        "苹果公司今年业绩"
    ]
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        result = strategy.optimize_query_for_search(query)
        
        print(f"BrightData查询: {result['brightdata']['query']}")
        print(f"通用查询: {result['universal']}")
        print(f"搜索URL: {result['search_url']}")
        
        if result['time_range']:
            print(f"时间范围: {result['time_range']['start_str']} 至 {result['time_range']['end_str']}")