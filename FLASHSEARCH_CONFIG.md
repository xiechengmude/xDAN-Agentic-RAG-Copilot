# FlashSearch API 端口配置说明

## 统一端口配置

为避免端口硬编码问题，FlashSearch API 现在支持通过环境变量灵活配置端口：

### 设置默认端口

```bash
# 通过环境变量设置默认端口
export FLASHSEARCH_PORT=9090

# 所有脚本将使用该端口
./start.sh              # 使用 9090
./0708-0130.sh          # 使用 9090
./example.sh            # 连接到 9090
```

### 端口配置优先级

1. **命令行参数**（最高优先级）
   ```bash
   ./0708-0130.sh 0.0.0.0 8080  # 使用 8080
   ```

2. **PORT 环境变量**
   ```bash
   export PORT=8070
   ./start.sh  # 使用 8070
   ```

3. **FLASHSEARCH_PORT 环境变量**
   ```bash
   export FLASHSEARCH_PORT=8060
   ./start.sh  # 使用 8060
   ```

4. **默认值**: 8060

### 已更新的文件

- `start.sh` - 统一启动脚本
- `0708-0130.sh` - 部署脚本
- `example.sh` - API示例脚本
- `example-quick.sh` - 快速测试脚本
- `example.py` - Python客户端

所有脚本现在都使用相同的端口配置逻辑，确保一致性。

### 使用示例

```bash
# 开发环境（使用默认端口 8060）
./start.sh

# 测试环境（使用自定义端口）
FLASHSEARCH_PORT=8080 ./0708-0130.sh

# 生产环境（通过参数指定）
./0708-0130.sh 0.0.0.0 80 info 4
```