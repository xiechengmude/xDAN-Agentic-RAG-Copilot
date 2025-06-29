# v1.2多轮搜索修复总结

## 问题描述
用户反馈v1.2版本的多轮搜索机制不工作，系统只进行了1轮搜索就停止，即使Agent判断需要继续搜索。

## 根本原因
经过深入调试，发现问题出在`extract_deepsearch_decision`方法中：
- v1.2的提示词使用`<next_query>`标签来包含下一轮搜索查询
- 但代码中仍在寻找旧版本的`<query>`标签
- 导致即使Agent生成了新查询，系统也无法正确提取

## 修复方案
在`src/core/deepsearch_framework.py`的第346-359行，修改了`extract_deepsearch_decision`方法：

```python
# 提取下一个查询 - 支持两种标签格式
if not decision["search_complete"]:
    # 先尝试 <next_query> 标签（v1.2使用）
    query_match = re.search(r'<next_query>(.*?)</next_query>', agent_response, re.DOTALL)
    if not query_match:
        # 兼容旧版本的 <query> 标签
        query_match = re.search(r'<query>(.*?)</query>', agent_response, re.DOTALL)
    
    if query_match:
        try:
            query_json = json.loads(query_match.group(1).strip())
            decision["next_query"] = query_json.get("query", "")
        except json.JSONDecodeError:
            decision["next_query"] = query_match.group(1).strip()
```

## 修复效果
1. **向后兼容**：同时支持v1.2的`<next_query>`标签和旧版本的`<query>`标签
2. **正确提取**：现在能正确提取Agent生成的下一轮搜索查询
3. **多轮搜索恢复**：系统能够根据Agent的决策进行多轮迭代搜索

## 验证结果
- ✅ v1.2格式的`<next_query>`标签能正确解析
- ✅ 旧格式的`<query>`标签仍然兼容
- ✅ Agent生成的复杂查询（包含JSON格式）能正确提取
- ✅ 多轮搜索机制恢复正常工作

## 其他发现
1. **SearchModel配置正确**：v1.2的SearchModel系统提示保持了90%以上的原始训练配置
2. **Agent提示优化**：v1.2的Agent提示词已经优化，支持更灵活的搜索策略
3. **性能问题**：LiteLLM对deepseek-chat模型的成本计算存在警告，但不影响功能

## 建议
1. 在提示词版本管理中明确标注标签格式的变化
2. 考虑为不同版本的提示词创建对应的解析器
3. 添加单元测试覆盖不同格式的响应解析