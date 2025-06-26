# Import更新脚本使用说明

本脚本用于自动更新项目中的旧import语句，将其替换为新的模块名称。

## 需要替换的import映射

| 旧import | 新import |
|---------|----------|
| `from src.clients.litellm_sdk_client_v2` | `from src.clients.litellm_client` |
| `from src.clients.llm_client` | `from src.clients.litellm_client` |
| `from src.services.enhanced_s3_rag_service` | `from src.services.s3_service` |
| `from src.services.rag_service_v2` | `from src.services.s3_service` |
| `from src.clients.streaming_ragflow_client` | `from src.clients.ragflow_client` |

## 类名映射

| 旧类名 | 新类名 |
|--------|--------|
| `LiteLLMSDKClientV2` | `LiteLLMClient` |
| `LLMClient` | `LiteLLMClient` |
| `EnhancedS3RAGService` | `S3Service` |
| `RAGServiceV2` | `S3Service` |
| `StreamingRAGFlowClient` | `RAGFlowClient` |

## 使用方法

### 1. 预览模式（推荐先运行）

```bash
python3 update_imports.py --dry-run
```

这将显示所有将要进行的更改，但不会实际修改文件。

### 2. 执行更新（不创建备份）

```bash
python3 update_imports.py
```

### 3. 执行更新（创建备份）

```bash
python3 update_imports.py --backup
```

这将在修改每个文件之前，在同目录下的 `.import_update_backups` 文件夹中创建备份。

### 4. 指定特定目录

```bash
python3 update_imports.py --path /path/to/your/project --dry-run
```

### 5. 排除额外的目录

```bash
python3 update_imports.py --exclude tests docs --dry-run
```

## 默认排除的目录

- `__pycache__`
- `.git`
- `venv`
- `env`
- `.venv`
- `src_backup_20250626_201255`

## 输出说明

1. **更改预览**：显示每个文件的具体更改内容
2. **更改日志**：如果执行了实际更新，会在 `logs/` 目录下生成带时间戳的日志文件
3. **备份文件**：如果使用了 `--backup` 选项，备份文件会保存在各文件所在目录的 `.import_update_backups` 文件夹中

## 注意事项

1. 在执行实际更新之前，强烈建议先运行 `--dry-run` 模式查看更改
2. 建议使用 `--backup` 选项创建备份，以便在需要时可以恢复
3. 脚本会自动排除自身（`update_imports.py`）
4. 更改是原子性的 - 如果文件修改失败，会保持原始状态

## 恢复备份

如果需要恢复某个文件的备份：

```bash
# 查看备份
ls path/to/file/.import_update_backups/

# 恢复特定备份
cp path/to/file/.import_update_backups/filename_20250626_123456.py path/to/file/filename.py
```