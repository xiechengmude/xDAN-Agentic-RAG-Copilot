# Prompt优化方案：激活Agent并明确职责划分

## 当前问题分析

### 功能重叠情况
1. **agent_system.txt** 和 **select_evaluation.txt** 都包含：
   - 搜索策略制定
   - 迭代搜索决策
   - 生成next_query

2. **searchmodel_system.txt** 和 **select_evaluation.txt** 都涉及：
   - 信息源评估
   - 搜索方向预测

## 优化后的职责划分

### 1. 🎯 **agent_system.txt** - 整体策略规划（新激活）
**时机**：搜索开始前，第一轮搜索之前
**职责**：
- 分析问题，制定整体搜索计划
- 确定搜索的主要方向和优先级
- 生成第一轮搜索查询
- 预估需要的搜索轮数

**输出**：
```xml
<strategy>
  <analysis>问题分析和搜索挑战</analysis>
  <search_plan>整体搜索计划（2-3步）</search_plan>
  <initial_query>{"query": "第一轮搜索查询"}</initial_query>
  <estimated_rounds>2-3</estimated_rounds>
</strategy>
```

### 2. 🔍 **searchmodel_system.txt** - SearchModel核心能力
**时机**：作为SearchModel的系统提示
**职责**：
- 定义SearchModel的核心能力
- 信息评估标准
- 搜索优化原则
- 不直接参与决策，只定义能力

### 3. 📊 **select_evaluation.txt** - 轮次评估决策
**时机**：每轮搜索后
**职责**：
- 评估当前轮次的搜索结果
- 选择Top 3 URL
- 判断信息是否充足
- 基于Agent的整体策略，调整下一轮查询

**输入增强**：
- 添加Agent的整体策略上下文
- 添加搜索历史（之前的查询）

### 4. 📝 **content_extraction.txt** - 信息提取
**职责不变**：
- 从网页提取关键信息
- 结构化组织内容

### 5. 🎨 **synthesize_system.txt** - 最终生成
**职责不变**：
- 整合所有信息
- 生成结构化报告

## 实施方案

### Phase 1: 激活Agent策略规划

```python
# 在 execute_deepsearch_workflow 开始时添加
async def plan_search_strategy(self, question: str) -> Dict[str, Any]:
    """使用Agent制定整体搜索策略"""
    
    # 获取Agent系统提示
    agent_system = self.prompt_manager.get_prompt(
        "agent_system",
        time_context=self._get_time_context()
    )
    
    messages = [
        {"role": "system", "content": agent_system},
        {"role": "user", "content": f"请为以下问题制定搜索策略：\n{question}"}
    ]
    
    # 调用模型
    response = await self.litellm_client.chat_completion(
        messages=messages,
        use_case="agent",
        temperature=0.1,
        max_tokens=1000
    )
    
    # 解析策略
    return self.extract_search_strategy(response.choices[0].message.content)
```

### Phase 2: 修改select_evaluation.txt

添加策略上下文：
```
**整体搜索策略：**
{search_strategy}

**搜索历史：**
{search_history}

请基于整体策略和当前结果，做出评估决策...
```

### Phase 3: 工作流集成

```python
# 修改后的工作流
async def execute_deepsearch_workflow(self, question, ...):
    # 1. Agent制定整体策略
    strategy = await self.plan_search_strategy(question)
    first_query = strategy.get("initial_query")
    
    # 2. 开始迭代搜索
    for round_num in range(1, max_rounds + 1):
        # 使用Agent策略指导的查询
        if round_num == 1:
            search_query = first_query
        else:
            search_query = decision.get("next_query", question)
        
        # 3. Select阶段传入策略上下文
        decision = await self.select_phase(
            question=question,
            search_results=search_results,
            round_num=round_num,
            search_strategy=strategy,  # 新增
            search_history=search_history  # 新增
        )
```

## 预期效果

1. **更清晰的职责划分**
   - Agent：宏观策略
   - SearchModel：评估能力
   - Select：微观决策

2. **更智能的搜索**
   - 有整体规划，不盲目搜索
   - 每轮决策都基于整体策略
   - 搜索历史避免重复

3. **更高效的执行**
   - 减少无效搜索轮次
   - 更快收敛到目标信息

## 实施优先级

1. **高优先级**：激活agent_system.txt用于策略规划
2. **中优先级**：修改select_evaluation.txt添加策略上下文
3. **低优先级**：优化其他prompt的细节