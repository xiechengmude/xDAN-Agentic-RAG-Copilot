#!/usr/bin/env python3
"""
增强的时间感知系统
从"时间告知者"升级为"时间理解者"
支持相对时间解析、日期范围计算、搜索算子生成
"""

import datetime
from typing import Dict, List, Optional, Tuple
from datetime import datetime as dt, timedelta
import re
import logging

logger = logging.getLogger(__name__)


class EnhancedTimeAware:
    """增强的时间感知类 - 真正理解时间语义"""
    
    def __init__(self):
        self.now = dt.now()
        self.beijing_tz = datetime.timezone(timedelta(hours=8))
        self.beijing_time = self.now.astimezone(self.beijing_tz)
        
        # 相对时间词映射
        self.relative_time_mappings = {
            # 近期时间词
            '最近': {'days': 90, 'type': 'past', 'desc': '最近3个月'},
            '最新': {'days': 30, 'type': 'past', 'desc': '最近1个月'},
            '近期': {'days': 180, 'type': 'past', 'desc': '最近半年'},
            '近日': {'days': 7, 'type': 'past', 'desc': '最近一周'},
            '昨天': {'days': 1, 'type': 'past', 'desc': '昨天'},
            '前天': {'days': 2, 'type': 'past', 'desc': '前天'},
            
            # 周期时间词
            '本周': {'type': 'current_week', 'desc': '本周'},
            '上周': {'type': 'last_week', 'desc': '上周'},
            '本月': {'type': 'current_month', 'desc': '本月'},
            '上月': {'type': 'last_month', 'desc': '上月'},
            '今年': {'type': 'ytd', 'desc': '今年至今'},
            '去年': {'type': 'last_year', 'desc': '去年全年'},
            
            # 季度时间词
            '本季度': {'type': 'current_quarter', 'desc': '本季度'},
            '上季度': {'type': 'last_quarter', 'desc': '上季度'},
            '一季度': {'type': 'q1', 'desc': '第一季度'},
            '二季度': {'type': 'q2', 'desc': '第二季度'},
            '三季度': {'type': 'q3', 'desc': '第三季度'},
            '四季度': {'type': 'q4', 'desc': '第四季度'},
        }
        
        # 财报发布延迟规则（月份）
        self.financial_report_delay = {
            'quarterly': 1,  # 季报通常延迟1个月发布
            'annual': 3,     # 年报通常延迟3个月发布
        }
        
    def parse_relative_time(self, text: str) -> List[Dict[str, any]]:
        """
        解析文本中的相对时间词
        
        Args:
            text: 包含相对时间词的文本
            
        Returns:
            解析出的时间信息列表
        """
        results = []
        
        for term, config in self.relative_time_mappings.items():
            if term in text:
                time_range = self._calculate_time_range(term, config)
                if time_range:
                    results.append({
                        'term': term,
                        'config': config,
                        'range': time_range,
                        'position': text.find(term)
                    })
        
        # 按出现位置排序
        results.sort(key=lambda x: x['position'])
        
        logger.info(f"[时间解析] 从'{text}'中识别到{len(results)}个时间词")
        return results
    
    def _calculate_time_range(self, term: str, config: Dict) -> Optional[Dict[str, any]]:
        """
        计算具体的日期范围
        
        Args:
            term: 时间词
            config: 时间配置
            
        Returns:
            日期范围信息
        """
        time_type = config.get('type')
        
        if time_type == 'past':
            # 过去N天
            days = config['days']
            end_date = self.beijing_time
            start_date = end_date - timedelta(days=days)
            
        elif time_type == 'current_week':
            # 本周
            weekday = self.beijing_time.weekday()
            start_date = self.beijing_time - timedelta(days=weekday)
            end_date = start_date + timedelta(days=6)
            
        elif time_type == 'last_week':
            # 上周
            weekday = self.beijing_time.weekday()
            end_date = self.beijing_time - timedelta(days=weekday+1)
            start_date = end_date - timedelta(days=6)
            
        elif time_type == 'current_month':
            # 本月
            start_date = self.beijing_time.replace(day=1)
            # 下月第一天的前一天
            if self.beijing_time.month == 12:
                end_date = self.beijing_time.replace(year=self.beijing_time.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = self.beijing_time.replace(month=self.beijing_time.month+1, day=1) - timedelta(days=1)
                
        elif time_type == 'last_month':
            # 上月
            if self.beijing_time.month == 1:
                start_date = self.beijing_time.replace(year=self.beijing_time.year-1, month=12, day=1)
                end_date = self.beijing_time.replace(day=1) - timedelta(days=1)
            else:
                start_date = self.beijing_time.replace(month=self.beijing_time.month-1, day=1)
                end_date = self.beijing_time.replace(day=1) - timedelta(days=1)
                
        elif time_type == 'ytd':
            # 今年至今
            start_date = self.beijing_time.replace(month=1, day=1)
            end_date = self.beijing_time
            
        elif time_type == 'last_year':
            # 去年全年
            start_date = self.beijing_time.replace(year=self.beijing_time.year-1, month=1, day=1)
            end_date = self.beijing_time.replace(year=self.beijing_time.year-1, month=12, day=31)
            
        elif time_type == 'current_quarter':
            # 本季度
            quarter = (self.beijing_time.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = self.beijing_time.replace(month=start_month, day=1)
            
            end_month = quarter * 3
            if end_month == 12:
                end_date = self.beijing_time.replace(month=12, day=31)
            else:
                end_date = self.beijing_time.replace(month=end_month+1, day=1) - timedelta(days=1)
                
        elif time_type == 'last_quarter':
            # 上季度
            current_quarter = (self.beijing_time.month - 1) // 3 + 1
            if current_quarter == 1:
                # 上季度是去年Q4
                start_date = self.beijing_time.replace(year=self.beijing_time.year-1, month=10, day=1)
                end_date = self.beijing_time.replace(year=self.beijing_time.year-1, month=12, day=31)
            else:
                last_quarter = current_quarter - 1
                start_month = (last_quarter - 1) * 3 + 1
                start_date = self.beijing_time.replace(month=start_month, day=1)
                
                end_month = last_quarter * 3
                end_date = self.beijing_time.replace(month=end_month+1, day=1) - timedelta(days=1)
                
        elif time_type in ['q1', 'q2', 'q3', 'q4']:
            # 特定季度
            quarter_num = int(time_type[1])
            year = self.beijing_time.year
            
            # 如果当前时间早于该季度，可能指去年
            current_quarter = (self.beijing_time.month - 1) // 3 + 1
            if quarter_num > current_quarter:
                year -= 1
                
            start_month = (quarter_num - 1) * 3 + 1
            start_date = dt(year, start_month, 1).astimezone(self.beijing_tz)
            
            end_month = quarter_num * 3
            if end_month == 12:
                end_date = dt(year, 12, 31).astimezone(self.beijing_tz)
            else:
                end_date = dt(year, end_month+1, 1).astimezone(self.beijing_tz) - timedelta(days=1)
        else:
            return None
            
        return {
            'start_date': start_date,
            'end_date': end_date,
            'start_str': start_date.strftime('%Y-%m-%d'),
            'end_str': end_date.strftime('%Y-%m-%d'),
            'description': config['desc']
        }
    
    def generate_search_operators(self, time_ranges: List[Dict]) -> List[str]:
        """
        生成时间搜索算子
        
        Args:
            time_ranges: 时间范围列表
            
        Returns:
            搜索算子列表
        """
        operators = []
        
        for time_info in time_ranges:
            range_data = time_info['range']
            
            # 生成after和before算子
            operators.append(f"after:{range_data['start_str']}")
            operators.append(f"before:{range_data['end_str']}")
            
            # 对于季度，额外生成季度搜索词
            if 'quarter' in time_info['config'].get('type', ''):
                quarter_terms = self._generate_quarter_terms(range_data)
                operators.extend(quarter_terms)
                
        return list(set(operators))  # 去重
    
    def _generate_quarter_terms(self, time_range: Dict) -> List[str]:
        """生成季度相关的搜索词"""
        start_date = time_range['start_date']
        year = start_date.year
        quarter = (start_date.month - 1) // 3 + 1
        
        terms = [
            f'"{year}年第{quarter}季度"',
            f'"{year}年Q{quarter}"',
            f'"{year} Q{quarter}"',
            f'"{year}年{quarter}季报"'
        ]
        
        # 中文数字
        quarter_cn = ['一', '二', '三', '四'][quarter-1]
        terms.append(f'"{year}年第{quarter_cn}季度"')
        
        return terms
    
    def get_financial_period(self, report_type: str = 'quarterly') -> Dict[str, any]:
        """
        获取应该查询的财报周期（考虑发布延迟）
        
        Args:
            report_type: 报告类型 (quarterly/annual)
            
        Returns:
            财报周期信息
        """
        delay_months = self.financial_report_delay.get(report_type, 1)
        check_date = self.beijing_time - timedelta(days=delay_months * 30)
        
        if report_type == 'quarterly':
            # 计算最新可获得的季报
            quarter = (check_date.month - 1) // 3 + 1
            year = check_date.year
            
            # 如果是Q1且在1-2月，返回去年Q4
            if quarter == 1 and self.beijing_time.month <= 2:
                quarter = 4
                year -= 1
                
            return {
                'year': year,
                'quarter': quarter,
                'period_cn': f'{year}年第{quarter}季度',
                'period_en': f'{year} Q{quarter}',
                'search_terms': self._generate_quarter_terms({
                    'start_date': dt(year, (quarter-1)*3+1, 1).astimezone(self.beijing_tz)
                })
            }
            
        elif report_type == 'annual':
            # 年报通常在次年3-4月发布
            if self.beijing_time.month <= 4:
                year = self.beijing_time.year - 2
            else:
                year = self.beijing_time.year - 1
                
            return {
                'year': year,
                'period_cn': f'{year}年年报',
                'period_en': f'{year} Annual Report',
                'search_terms': [
                    f'"{year}年年报"',
                    f'"{year}年年度报告"',
                    f'"{year} Annual Report"'
                ]
            }
    
    def enhance_query_with_time(self, query: str) -> Dict[str, any]:
        """
        使用时间理解增强查询
        
        Args:
            query: 原始查询
            
        Returns:
            增强后的查询信息
        """
        # 1. 解析相对时间词
        time_refs = self.parse_relative_time(query)
        
        # 2. 生成搜索算子
        search_operators = []
        time_descriptions = []
        
        if time_refs:
            search_operators = self.generate_search_operators(time_refs)
            time_descriptions = [ref['config']['desc'] for ref in time_refs]
        
        # 3. 检测是否是财报查询
        is_financial = any(word in query for word in ['财报', '财务', '业绩', '营收', '利润', '年报', '季报'])
        
        financial_terms = []
        if is_financial:
            # 如果没有明确的时间词，添加最新财报周期
            if not time_refs or all('季' not in ref['term'] for ref in time_refs):
                period_info = self.get_financial_period()
                financial_terms = period_info['search_terms']
        
        # 4. 构建增强查询
        enhanced_parts = []
        
        # 添加搜索算子
        if search_operators:
            enhanced_parts.extend(search_operators[:2])  # 只使用前两个避免过长
            
        # 添加原始查询
        enhanced_parts.append(query)
        
        # 添加财报搜索词
        if financial_terms:
            enhanced_parts.append(f"({' OR '.join(financial_terms[:3])})")
        
        enhanced_query = ' '.join(enhanced_parts)
        
        result = {
            'original_query': query,
            'enhanced_query': enhanced_query,
            'time_references': time_refs,
            'search_operators': search_operators,
            'time_descriptions': time_descriptions,
            'is_financial': is_financial,
            'financial_terms': financial_terms,
            'current_time': self.beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        logger.info(f"[时间增强] {query} → {enhanced_query}")
        
        return result
    
    def get_time_context_prompt(self) -> str:
        """
        生成时间上下文提示（兼容原有功能）
        """
        time_info = self.get_current_time_info()
        
        # 添加时间理解能力说明
        return f"""
当前时间上下文：
- 北京时间：{time_info['beijing_time']} ({time_info['weekday_cn']})
- 本周范围：{time_info['week_start']} 至 {time_info['week_end']}
- 本月范围：{time_info['month_start']} 至 {time_info['month_end']}
- 市场状态：{time_info['market_status']}

时间理解能力：
- 我能理解"最近"通常指最近3个月
- 我能理解"最新"通常指最近1个月
- 对于财报查询，我会考虑发布延迟（季报延迟1个月，年报延迟3个月）
- 我能将相对时间转换为具体日期范围进行搜索
"""
    
    def get_current_time_info(self) -> Dict[str, str]:
        """获取当前时间信息（保持向后兼容）"""
        # 计算本周和本月范围
        weekday = self.beijing_time.weekday()
        week_start = self.beijing_time - timedelta(days=weekday)
        week_end = week_start + timedelta(days=6)
        
        month_start = self.beijing_time.replace(day=1)
        if self.beijing_time.month == 12:
            month_end = self.beijing_time.replace(year=self.beijing_time.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = self.beijing_time.replace(month=self.beijing_time.month + 1, day=1) - timedelta(days=1)
        
        # 市场状态判断
        hour = self.beijing_time.hour
        if 9 <= hour < 15:
            market_status = "交易时间"
        elif 15 <= hour < 20:
            market_status = "盘后时间"
        else:
            market_status = "休市时间"
        
        # 星期中文
        weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday_cn = weekdays_cn[weekday]
        
        return {
            "beijing_time": self.beijing_time.strftime("%Y-%m-%d %H:%M:%S"),
            "current_date": self.beijing_time.strftime("%Y-%m-%d"),
            "weekday_cn": weekday_cn,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "month_start": month_start.strftime("%Y-%m-%d"),
            "month_end": month_end.strftime("%Y-%m-%d"),
            "market_status": market_status
        }


# 使用示例
if __name__ == "__main__":
    # 创建增强的时间感知实例
    time_aware = EnhancedTimeAware()
    
    # 测试查询
    test_queries = [
        "比亚迪最近财务收入分析一下",
        "特斯拉最新财报数据",
        "苹果公司上季度业绩",
        "今年新能源汽车市场分析",
        "本月科技股表现"
    ]
    
    for query in test_queries:
        print(f"\n原始查询: {query}")
        result = time_aware.enhance_query_with_time(query)
        print(f"增强查询: {result['enhanced_query']}")
        if result['time_descriptions']:
            print(f"时间理解: {', '.join(result['time_descriptions'])}")
        if result['search_operators']:
            print(f"搜索算子: {', '.join(result['search_operators'][:2])}")