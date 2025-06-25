#!/bin/bash

# 日志轮转脚本 - 自动管理和压缩旧日志

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
ARCHIVE_DIR="$LOG_DIR/archive"
MAX_AGE_DAYS=7  # 保留原始日志天数
MAX_ARCHIVE_DAYS=30  # 保留压缩日志天数

# 创建归档目录
mkdir -p "$ARCHIVE_DIR"

echo "🔄 开始日志轮转..."
echo "日志目录: $LOG_DIR"

# 压缩旧日志
find "$LOG_DIR" -name "*.log" -type f -mtime +$MAX_AGE_DAYS | while read -r log_file; do
    if [[ ! "$log_file" =~ archive ]]; then
        filename=$(basename "$log_file")
        echo "压缩: $filename"
        gzip -c "$log_file" > "$ARCHIVE_DIR/${filename}.gz"
        rm "$log_file"
    fi
done

# 清理过期的压缩日志
find "$ARCHIVE_DIR" -name "*.gz" -type f -mtime +$MAX_ARCHIVE_DAYS -delete

# 显示日志统计
echo ""
echo "📊 日志统计:"
echo "活动日志: $(find "$LOG_DIR" -name "*.log" -type f | wc -l) 个"
echo "归档日志: $(find "$ARCHIVE_DIR" -name "*.gz" -type f | wc -l) 个"
echo "总大小: $(du -sh "$LOG_DIR" | cut -f1)"
echo ""
echo "✅ 日志轮转完成"