# E2E Backend Testing Framework

## 📁 目录结构

```
tests/e2e_backend/
├── traces/          # 完整trace.json文件
├── analysis/        # LLM分析结果  
├── logs/           # 批次测试日志
├── test_runner.py  # 主测试运行器
├── simple_test.py  # 简化测试验证
└── README.md       # 本说明文档
```

## 🎯 核心功能

1. **逐个问题处理** - 读取diverse_questions_50_formatted.json，一个问题一个问题测试
2. **完整trace保存** - 每个问题保存详细的执行trace.json
3. **LLM自动分析** - 用deepseek-chat分析每个trace结果，无需手动创建代码
4. **KISS & DRY原则** - 代码简洁，复用现有框架

## 🚀 使用方法

### 环境准备
```bash
# 激活虚拟环境
source venv/bin/activate

# 确保环境变量配置
export DEEPSEEK_API_KEY="your_key"
export BRIGHTDATA_API_KEY="your_key" 
export FIRECRAWL_API_KEY="your_key"
```

### 运行测试

#### 1. 简单验证测试
```bash
python tests/e2e_backend/simple_test.py
```

#### 2. 批量问题测试
```bash
# 测试前3个问题 (推荐首次测试)
python tests/e2e_backend/test_runner.py questions/search/diverse_questions_50_formatted.json 0 3

# 测试指定范围问题
python tests/e2e_backend/test_runner.py questions/search/diverse_questions_50_formatted.json 3 5

# 测试所有50个问题 (需要较长时间)
python tests/e2e_backend/test_runner.py questions/search/diverse_questions_50_formatted.json 0 50
```

## 📊 输出文件

### Trace文件 (traces/)
每个问题生成一个完整的执行记录：
```json
{
  "question_id": "market_research_1745567367_16",
  "question": "问题内容...",
  "category": "问题分类",
  "start_time": "2025-06-30T16:14:00.203340",
  "end_time": "2025-06-30T16:19:45.123456", 
  "duration_seconds": 345.67,
  "result": {
    "question": "...",
    "rounds": [...],
    "final_answer": "...",
    "extracted_content": [...],
    "workflow_completed": true
  },
  "success": true,
  "error": null
}
```

### 分析文件 (analysis/)
LLM对每个trace的自动分析：
```json
{
  "question_id": "market_research_1745567367_16",
  "analysis_time": "2025-06-30T16:20:00.123456",
  "success": true,
  "scores": {
    "答案质量": 4,
    "搜索效率": 3,
    "信息相关性": 5,
    "综合表现": 4
  },
  "detailed_analysis": "详细分析内容...",
  "llm_raw_response": "LLM原始响应..."
}
```

### 批次日志 (logs/)
批量测试的汇总结果：
```json
{
  "batch_info": {
    "start_index": 0,
    "end_index": 3,
    "total_tested": 3,
    "timestamp": "2025-06-30T16:14:00.206563"
  },
  "results": [
    {
      "question_index": 0,
      "trace": {...},
      "analysis": {...}
    }
  ]
}
```

## ⚙️ 配置说明

### 测试参数
- `max_rounds`: 每个问题的最大搜索轮数 (默认3轮)
- `timeout`: 单个问题超时时间 (默认5分钟)
- `concurrent`: 是否启用并发搜索策略

### 环境要求
- Python 3.8+
- 有效的API密钥 (DeepSeek, BrightData, FireCrawl)
- 稳定的网络连接

## 🔍 测试策略

### 问题类型覆盖
- 市场研究能力 (产品与行业分析)
- 学术文献检索 (论文查找与总结)
- 数据分析能力 (统计与可视化)
- 长尾知识检索 (专业术语解释)
- 编程技术查询 (代码示例与文档)

### 评估维度
1. **答案质量** - 回答是否准确、全面、有用
2. **搜索效率** - 搜索轮数是否合理，信息获取是否高效  
3. **信息相关性** - 搜索到的信息是否与问题相关
4. **综合表现** - 整体表现评价

## 📈 结果分析

### 成功指标
- 测试成功率 > 90%
- 平均执行时间 < 3分钟
- 答案质量评分 > 3.5/5
- 信息相关性评分 > 4/5

### 故障诊断
- 检查API密钥是否有效
- 确认网络连接稳定
- 查看具体错误日志
- 验证问题格式正确性

## 🛠️ 扩展功能

### 自定义分析
可以修改`test_runner.py`中的分析提示词来调整评估维度

### 批量报告
运行完成后可以聚合所有分析结果生成综合报告

### 性能监控
可以添加更详细的性能指标收集和分析

---

**注意**: 每个问题的测试时间可能较长(1-5分钟)，建议先用小批量测试验证系统正常工作。