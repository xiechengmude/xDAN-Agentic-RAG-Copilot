# xDAN RAG API Curl 测试示例

本文档提供了详细的curl命令示例，用于测试xDAN RAG API的各种功能。

## 🚀 基础测试

### 1. 服务状态检查

```bash
# 检查API服务是否运行
curl -X GET "http://localhost:8060/"

# 健康检查
curl -X GET "http://localhost:8060/api/v1/health"

# 查看API文档（浏览器访问）
# http://localhost:8060/docs
```

### 2. 基础搜索测试

```bash
# 简单问题测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "什么是人工智能？",
    "mode": "flash",
    "max_rounds": 1
  }'

# 技术问题测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Python和Java的区别",
    "mode": "standard",
    "max_rounds": 2
  }'
```

## 💼 财经分析场景

### 1. 股票分析

```bash
# 比亚迪股票分析
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "比亚迪最新季度财报表现如何？",
    "mode": "standard",
    "max_rounds": 3,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'

# 特斯拉vs比亚迪对比
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "特斯拉和比亚迪在新能源汽车市场的竞争格局分析",
    "mode": "deep",
    "max_rounds": 4,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'
```

### 2. 市场趋势分析

```bash
# 新能源汽车行业趋势
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024年新能源汽车行业发展趋势和挑战",
    "mode": "deep",
    "max_rounds": 5,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'

# 科技股投资建议
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "当前值得关注的科技股有哪些？投资策略建议",
    "mode": "deep",
    "max_rounds": 4,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'
```

## ⏰ 时间感知功能测试

### 1. 相对时间查询

```bash
# "最近"时间词测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "最近比亚迪的股价表现",
    "mode": "standard",
    "max_rounds": 3,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'

# "最新"时间词测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "最新的AI政策法规有哪些？",
    "mode": "standard",
    "max_rounds": 3
  }'

# "本季度"时间词测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "本季度科技行业表现分析",
    "mode": "deep",
    "max_rounds": 4
  }'
```

### 2. 财报时间感知

```bash
# 财报查询（自动时间推断）
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "比亚迪最新财报数据分析",
    "mode": "standard",
    "max_rounds": 3,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'

# 季度财报对比
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "比亚迪本季度vs上季度财报对比",
    "mode": "deep",
    "max_rounds": 4,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'
```

## 🔍 深度搜索场景

### 1. 技术对比分析

```bash
# AI模型对比
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "ChatGPT、Claude和Gemini在代码生成能力方面的详细对比",
    "mode": "deep",
    "max_rounds": 6
  }'

# 编程框架对比
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "React、Vue和Angular在企业级应用开发中的优劣对比",
    "mode": "deep",
    "max_rounds": 5
  }'
```

### 2. 复杂多维分析

```bash
# 多行业AI应用分析
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "人工智能在金融、医疗、教育、制造业四个领域的应用现状、挑战和发展前景对比分析",
    "mode": "deep",
    "max_rounds": 8
  }'

# 全球经济影响分析
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "分析全球经济不确定性对中国科技企业的影响，包括政策、资金、技术、市场等多个维度",
    "mode": "deep",
    "max_rounds": 7,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'
```

## 🌊 流式搜索测试

### 1. 基础流式请求

```bash
# 简单流式搜索
curl -N -X POST "http://localhost:8060/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "question": "什么是区块链技术？",
    "mode": "flash",
    "max_rounds": 1
  }'

# 标准模式流式搜索
curl -N -X POST "http://localhost:8060/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "question": "云计算的发展趋势和挑战",
    "mode": "standard",
    "max_rounds": 3
  }'
```

### 2. 复杂流式查询

```bash
# 深度分析流式搜索
curl -N -X POST "http://localhost:8060/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "question": "量子计算对现有加密技术的威胁和应对策略分析",
    "mode": "deep",
    "max_rounds": 5
  }'

# 财经流式分析
curl -N -X POST "http://localhost:8060/api/v1/search/stream" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "question": "比亚迪在全球新能源汽车市场的竞争优势分析",
    "mode": "deep",
    "max_rounds": 4,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }'
```

## 🧪 错误处理和边界测试

### 1. 参数验证测试

```bash
# 空问题测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "",
    "mode": "flash"
  }'

# 无效模式测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "测试问题",
    "mode": "invalid_mode"
  }'

# 超大轮数测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "测试问题",
    "mode": "standard",
    "max_rounds": 1000
  }'
```

### 2. 极限场景测试

```bash
# 超长问题测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题这是一个非常长的问题",
    "mode": "flash",
    "max_rounds": 1
  }'

# 特殊字符测试
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "测试特殊字符：@#$%^&*(){}[]|\\:;\"'"'"'<>?/~`",
    "mode": "flash",
    "max_rounds": 1
  }'
```

## 📊 性能压力测试

### 1. 并发请求测试

```bash
# 启动5个并发请求
for i in {1..5}; do
  (
    echo "启动并发请求 $i"
    time curl -X POST "http://localhost:8060/api/v1/search" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "并发测试问题 '$i'",
        "mode": "flash",
        "max_rounds": 1
      }' \
      -w "请求 $i 完成，HTTP状态: %{http_code}，总时间: %{time_total}s\n" \
      -o /dev/null -s
  ) &
done
wait
echo "所有并发请求完成"
```

### 2. 连续请求测试

```bash
# 连续发送10个请求测试稳定性
for i in {1..10}; do
  echo "发送请求 $i/10"
  curl -X POST "http://localhost:8060/api/v1/search" \
    -H "Content-Type: application/json" \
    -d '{
      "question": "连续测试问题 '$i'",
      "mode": "flash",
      "max_rounds": 1
    }' \
    -w "请求 $i - HTTP: %{http_code}, 时间: %{time_total}s, 大小: %{size_download}bytes\n" \
    -o /dev/null -s
  sleep 1
done
```

## 🔧 调试和监控

### 1. 详细响应分析

```bash
# 获取详细响应信息
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "人工智能的未来发展趋势",
    "mode": "standard",
    "max_rounds": 3,
    "debug": true
  }' \
  -w "\n\n=== 连接信息 ===\n查找时间: %{time_namelookup}s\n连接时间: %{time_connect}s\n预传输时间: %{time_pretransfer}s\n开始传输时间: %{time_starttransfer}s\n总时间: %{time_total}s\nHTTP状态码: %{http_code}\n响应大小: %{size_download}bytes\n" \
  | jq .
```

### 2. 响应时间监控

```bash
# 创建curl时间格式文件
cat > curl-format.txt << 'EOF'
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
EOF

# 使用格式文件监控性能
curl -w "@curl-format.txt" -o /dev/null -s \
  -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "性能监控测试",
    "mode": "standard",
    "max_rounds": 2
  }'
```

## 🎯 实际使用场景示例

### 1. 投资研究场景

```bash
# 投资决策支持
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "分析比亚迪的财务健康状况、市场地位和未来增长潜力，给出投资建议",
    "mode": "deep",
    "max_rounds": 6,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }' | jq '.answer, .rounds | length, .total_duration'
```

### 2. 技术调研场景

```bash
# 技术选型支持
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "为大型电商网站选择前端框架，对比React、Vue、Angular的性能、生态、学习成本和维护成本",
    "mode": "deep",
    "max_rounds": 5
  }' | jq '.answer, .sources | length'
```

### 3. 市场分析场景

```bash
# 竞品分析
curl -X POST "http://localhost:8060/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "新能源汽车充电桩行业的主要玩家、市场份额、技术路线对比和发展趋势",
    "mode": "deep",
    "max_rounds": 5,
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }' | jq '.rounds[].query'
```

## 📱 客户端集成示例

### 1. JavaScript/Node.js

```javascript
// fetch API示例
async function searchWithAPI(question, mode = 'standard') {
  try {
    const response = await fetch('http://localhost:8060/api/v1/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        mode: mode,
        max_rounds: 3
      })
    });
    
    const result = await response.json();
    console.log('搜索结果:', result.answer);
    return result;
  } catch (error) {
    console.error('搜索失败:', error);
  }
}

// 使用示例
searchWithAPI('什么是机器学习？', 'flash');
```

### 2. Python requests

```python
import requests
import json

def search_with_api(question, mode='standard', max_rounds=3):
    url = 'http://localhost:8060/api/v1/search'
    data = {
        'question': question,
        'mode': mode,
        'max_rounds': max_rounds
    }
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"搜索结果: {result['answer']}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"搜索失败: {e}")
        return None

# 使用示例
result = search_with_api('比亚迪最新财报分析', 'deep', 4)
```

## 🚀 快速开始脚本

保存以下脚本为 `quick_test.sh` 并运行：

```bash
#!/bin/bash
API_BASE="http://localhost:8060"

echo "=== xDAN RAG API 快速测试 ==="

# 1. 健康检查
echo "1. 健康检查..."
curl -s "$API_BASE/api/v1/health" | jq '.status'

# 2. 简单搜索
echo "2. 简单搜索测试..."
curl -s -X POST "$API_BASE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是AI？", "mode": "flash"}' \
  | jq '.answer | length'

# 3. 财经分析
echo "3. 财经分析测试..."
curl -s -X POST "$API_BASE/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "比亚迪股票分析",
    "mode": "standard",
    "dataset_id": "7e8d9e924cde11f0afc90242ac140006"
  }' | jq '.rounds | length'

echo "=== 测试完成 ==="
```

---

**使用说明**:
1. 确保API服务器在 `http://localhost:8060` 运行
2. 根据需要修改 `dataset_id` 参数
3. 使用 `jq` 工具可以更好地格式化JSON响应
4. 流式请求需要支持Server-Sent Events的客户端

**性能建议**:
- Flash模式适合快速查询，1-2轮搜索
- Standard模式适合一般查询，2-4轮搜索
- Deep模式适合复杂分析，4-8轮搜索
- 并发请求不要超过服务器处理能力