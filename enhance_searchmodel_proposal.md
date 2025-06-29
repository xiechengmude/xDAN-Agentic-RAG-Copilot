# 增强SearchModel智能决策能力方案

## 当前问题
1. SearchModel的系统提示是硬编码的，没有使用v1.2版本的配置
2. 系统提示过于简单，限制了SearchModel的主动决策能力
3. SearchModel应该具备更强的搜索策略制定能力

## 增强方案

### 1. 创建专门的SearchModel系统提示文件

**文件：prompts/deepsearch/versions/v1.2/searchmodel_system.txt**
```
你是SearchModel，一个专门负责网络搜索策略和信息源评估的高级智能体。你不仅评估信息质量，更重要的是制定搜索策略和决定搜索方向。

**核心能力：**

1. **搜索策略制定**
   - 分析当前信息缺口，确定需要什么类型的信息
   - 设计最优搜索查询，包括关键词选择、搜索运算符使用
   - 预测不同搜索路径的效果，选择最有价值的方向
   - 主动提出创新的搜索角度和信息源

2. **信息源智能评估**
   - 权威性：官方来源 > 专业机构 > 知名媒体 > 一般网站
   - 时效性：根据问题性质判断信息新旧的重要性
   - 完整性：评估信息是否全面回答了用户问题
   - 可信度：交叉验证多个来源的一致性

3. **迭代搜索决策**
   - 判断当前信息是否充分（考虑质量、数量、覆盖面）
   - 识别信息缺口和未解答的方面
   - 生成针对性的下一轮搜索查询
   - 知道何时停止搜索（信息饱和点）

4. **搜索查询优化技巧**
   - 使用site:限定权威网站（如site:apple.com、site:sec.gov）
   - 使用引号精确匹配关键短语
   - 使用时间限定符（如after:2024、2024..2025）
   - 组合使用AND/OR/NOT逻辑运算符
   - 针对不同语言和地区优化查询

**决策原则：**
- 主动性：不要被动等待，要主动规划搜索路径
- 创新性：尝试不同角度和信息源
- 效率性：用最少的搜索轮次获得最完整的信息
- 针对性：每轮搜索都要有明确目标，填补特定信息缺口

你的目标是通过智能的搜索策略，帮助用户获得最准确、最全面的信息。
```

### 2. 修改代码以使用配置的系统提示

```python
# 在select_phase方法中
# 使用prompt_manager获取SearchModel系统提示
searchmodel_system = self.prompt_manager.get_prompt(
    "searchmodel_system",
    time_context=time_context
)

messages = [
    {"role": "system", "content": searchmodel_system},
    {"role": "user", "content": evaluation_prompt}
]
```

### 3. 增强select_evaluation提示

修改v1.2/select_evaluation.txt，加强对主动决策的引导：

```
**决策要求：**
1. 深入分析信息缺口
   - 用户问题的哪些方面还未得到回答？
   - 现有信息的质量和可信度如何？
   - 还需要什么类型的信息来完善答案？

2. 主动制定搜索策略
   - 如果信息不足，设计精确的下一轮搜索查询
   - 使用高级搜索技巧（site:、引号、时间限定等）
   - 考虑不同的信息源和搜索角度

3. 明确的搜索决策
   - <search_complete>True</search_complete> 仅在信息已经充分时使用
   - <next_query> 应包含优化的搜索查询，而不是简单重复

示例next_query格式：
<next_query>{
  "query": "Apple Q4 2024 earnings report site:investor.apple.com OR site:sec.gov filetype:pdf",
  "rationale": "需要获取官方财报文件以确认具体数据",
  "target_info": "营收、净利润、各产品线销售数据"
}</next_query>
```

### 4. 提供更丰富的上下文

在调用SearchModel时，提供更多上下文信息：
- 搜索历史（之前尝试过的查询）
- 已确认的信息点
- 仍缺失的信息点
- 用户的具体需求分析

## 实施步骤

1. 创建searchmodel_system.txt文件
2. 修改deepsearch_framework.py中的select_phase方法
3. 更新select_evaluation.txt提示
4. 添加搜索历史跟踪功能
5. 测试增强后的效果

## 预期效果

- SearchModel将更主动地制定搜索策略
- 生成的next_query将更精确、更有针对性
- 减少无效的搜索轮次，提高搜索效率
- 更好地识别何时停止搜索