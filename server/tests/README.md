# FlashSearch 测试套件

本目录包含FlashSearch API和MCP服务的测试文件。

## 测试文件说明

### 核心测试脚本

1. **test_comprehensive_modes.py**
   - 综合测试所有三种模式（fast/normal/deep）
   - 测试API和MCP服务
   - 使用test_sample_50.json中的问题

2. **test_modes_simple.py**
   - 简化版测试，每种模式测试3个问题
   - 快速验证模式功能
   - 生成性能分析报告

3. **test_search_modes.py**
   - 搜索模式配置测试
   - 验证不同模式的参数应用
   - 模式切换功能测试

4. **test_servers.py**
   - 服务器健康检查和启动测试
   - API和MCP服务连接性测试
   - 服务端点验证

### 测试报告

1. **comprehensive_test_report.md**
   - 完整的测试结果分析
   - 性能瓶颈识别
   - 优化建议

2. **final_mode_analysis.md**
   - 最终的模式性能分析
   - 实际vs目标性能对比
   - 架构改进建议

## 运行测试

### 运行所有测试
```bash
python test_comprehensive_modes.py
```

### 快速测试
```bash
python test_modes_simple.py
```

### 服务器测试
```bash
python test_servers.py
```

## 测试配置

- API服务地址: http://127.0.0.1:8060
- MCP服务地址: http://127.0.0.1:9060/sse/
- 测试数据: /questions/search/test_sample_50.json

## 性能基准

基于实际测试结果：

| 模式 | 目标时间 | 实际时间 | 状态 |
|------|----------|----------|------|
| Fast | 15秒 | 45-60秒 | 需优化 |
| Normal | 60秒 | 80秒 | 基本达标 |
| Deep | 120秒 | 139秒 | 接近目标 |