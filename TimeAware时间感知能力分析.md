# Time Aware 时间感知原生功能分析

## 一、当前实现的时间感知能力

### 1.1 TimeAwarePrompt 类功能

```python
class TimeAwarePrompt:
    """时间感知提示类"""
```

**提供的时间信息**：
1. **北京时间**：当前精确时间 (YYYY-MM-DD HH:MM:SS)
2. **当前日期**：YYYY-MM-DD
3. **星期信息**：中文星期几
4. **本周范围**：周一到周日的日期范围
5. **本月范围**：月初到月末的日期范围
6. **市场状态**：
   - 交易时间 (9:00-15:00)
   - 盘后时间 (15:00-20:00)
   - 休市时间 (其他时间)

### 1.2 实际使用方式

在 DeepSearchFramework 中的集成：

```python
def _get_time_context(self) -> str:
    """获取时间上下文信息用于增强提示"""
    if not self.enable_time_aware:
        return ""
    
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
```

## 二、现有能力的局限性

### 2.1 只提供绝对时间，不理解相对时间

**当前能力**：
- ✅ 知道今天是2025年7月1日
- ✅ 知道本周是6月30日-7月6日
- ❌ 不理解"最近"意味着什么时间范围
- ❌ 不能将"最近"转换为具体的日期范围

### 2.2 时间信息只用于LLM提示，不用于搜索优化

**使用方式**：
```python
# 仅在LLM生成时添加时间上下文
system_prompt = self.DEEPSEARCH_AGENT_PROMPT + self._get_time_context()
```

**问题**：
- 时间信息只是告诉LLM当前时间
- 没有用于搜索查询的优化
- 没有转换相对时间词为搜索算子

### 2.3 缺少的关键能力

| 需要的能力 | 当前状态 | 缺失功能 |
|-----------|---------|----------|
| 相对时间理解 | ❌ | "最近"→最近3个月 |
| 时间范围计算 | ❌ | "今年"→2025-01-01至今 |
| 季度/半年理解 | ❌ | Q2、H1等时间概念 |
| 时间搜索算子 | ❌ | after:、before:等 |
| 财报周期理解 | ❌ | 季报、年报发布规律 |

## 三、时间感知的实际应用场景

### 3.1 当前使用场景

1. **LLM推理增强**：
   - 告诉模型当前时间，帮助判断信息时效性
   - 例如：2023年的数据相对于2025年7月是"过时的"

2. **市场状态判断**：
   - 判断当前是否在交易时间
   - 可能影响实时数据的可用性

### 3.2 未充分利用的潜力

1. **搜索查询优化**：
   ```python
   # 应该有的功能
   if '最近' in query and self.time_aware:
       # 计算最近3个月的范围
       three_months_ago = current_date - timedelta(days=90)
       query += f" after:{three_months_ago.strftime('%Y-%m-%d')}"
   ```

2. **财报周期理解**：
   ```python
   # 应该有的功能
   def get_latest_report_period(self):
       current_month = self.now.month
       current_quarter = (current_month - 1) // 3 + 1
       
       # 财报通常有1-2个月延迟
       if current_month <= 2:  # 1-2月
           return f"{self.now.year-1}年第四季度"
       else:
           last_quarter = current_quarter - 1
           return f"{self.now.year}年第{last_quarter}季度"
   ```

## 四、改进建议

### 4.1 增强 TimeAwarePrompt 类

```python
class EnhancedTimeAwarePrompt(TimeAwarePrompt):
    """增强的时间感知提示类"""
    
    def get_relative_time_range(self, relative_term: str) -> Dict[str, Any]:
        """将相对时间词转换为具体日期范围"""
        mappings = {
            '最近': {'days': 90, 'desc': '最近3个月'},
            '最新': {'days': 30, 'desc': '最近1个月'},
            '近期': {'days': 180, 'desc': '最近半年'},
            '今年': {'ytd': True, 'desc': '今年至今'}
        }
        
        if relative_term in mappings:
            config = mappings[relative_term]
            if config.get('ytd'):
                start_date = self.now.replace(month=1, day=1)
                end_date = self.now
            else:
                start_date = self.now - datetime.timedelta(days=config['days'])
                end_date = self.now
                
            return {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
                'description': config['desc'],
                'search_operators': [
                    f'after:{start_date.strftime("%Y-%m-%d")}',
                    f'before:{end_date.strftime("%Y-%m-%d")}'
                ]
            }
    
    def get_financial_period(self) -> Dict[str, str]:
        """获取当前应该查询的财报周期"""
        current_quarter = (self.now.month - 1) // 3 + 1
        
        # 考虑财报发布延迟（通常1-2个月）
        if self.now.month % 3 <= 1:  # 季度初
            report_quarter = current_quarter - 1 if current_quarter > 1 else 4
            report_year = self.now.year if current_quarter > 1 else self.now.year - 1
        else:
            report_quarter = current_quarter
            report_year = self.now.year
            
        return {
            'latest_quarter': f'{report_year}Q{report_quarter}',
            'latest_quarter_cn': f'{report_year}年第{report_quarter}季度',
            'search_terms': [
                f'"{report_year}年第{report_quarter}季度"',
                f'"{report_year} Q{report_quarter}"',
                f'"{report_year}年{report_quarter}季报"'
            ]
        }
```

### 4.2 在搜索策略中集成

```python
# 在 search_strategy.py 中集成时间感知
def optimize_with_time_aware(self, question: str, time_aware: TimeAwarePrompt) -> str:
    """使用时间感知优化查询"""
    
    # 检测相对时间词
    for term in ['最近', '最新', '近期', '今年']:
        if term in question:
            time_range = time_aware.get_relative_time_range(term)
            if time_range:
                # 添加时间搜索算子
                operators = time_range['search_operators']
                return f"{' '.join(operators)} {question}"
    
    # 财报查询特殊处理
    if any(word in question for word in ['财报', '财务', '业绩']):
        period = time_aware.get_financial_period()
        search_terms = ' OR '.join(period['search_terms'])
        return f"{question} ({search_terms})"
    
    return question
```

## 五、总结

### 当前 Time Aware 能力：
1. ✅ 提供当前时间信息（北京时间）
2. ✅ 计算周/月范围
3. ✅ 判断市场状态
4. ✅ 增强LLM的时间理解

### 缺失的关键能力：
1. ❌ 相对时间词的理解和转换
2. ❌ 时间范围的动态计算
3. ❌ 搜索查询的时间优化
4. ❌ 财报周期的智能推断
5. ❌ 时间相关的搜索算子生成

### 改进方向：
将时间感知从"告知LLM当前时间"升级为"智能理解和转换时间概念"，真正实现时间敏感的搜索优化。