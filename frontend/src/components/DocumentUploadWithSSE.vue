<template>
  <div class="document-upload">
    <h3>文档上传（使用 SSE 状态跟踪）</h3>
    
    <!-- 文件上传区域 -->
    <div class="upload-area" @drop="handleDrop" @dragover.prevent>
      <input
        ref="fileInput"
        type="file"
        multiple
        @change="handleFileSelect"
        style="display: none"
      />
      <button @click="$refs.fileInput.click()">选择文件</button>
      <p>或拖拽文件到此处</p>
    </div>

    <!-- 文件列表 -->
    <div v-if="documents.length > 0" class="document-list">
      <h4>文档列表</h4>
      <div v-for="doc in documents" :key="doc.id" class="document-item">
        <div class="doc-info">
          <span class="doc-name">{{ doc.name }}</span>
          <span class="doc-status" :class="getStatusClass(doc.status)">
            {{ getStatusText(doc.status) }}
          </span>
        </div>
        
        <!-- 进度条 -->
        <div v-if="isProcessing(doc.status)" class="progress-bar">
          <div 
            class="progress-fill" 
            :style="{ width: `${doc.progress * 100}%` }"
          ></div>
          <span class="progress-text">{{ Math.round(doc.progress * 100) }}%</span>
        </div>
        
        <!-- 进度消息 -->
        <div v-if="doc.progressMsg" class="progress-msg">
          {{ doc.progressMsg }}
        </div>
        
        <!-- 操作按钮 -->
        <div class="doc-actions">
          <button 
            v-if="doc.status === 'UPLOAD_SUCCESS'" 
            @click="parseDocument(doc)"
          >
            开始解析
          </button>
          <button 
            v-if="doc.status === 'PARSE_SUCCESS'" 
            @click="downloadDocument(doc)"
          >
            下载
          </button>
          <button 
            @click="deleteDocument(doc)"
            :disabled="isProcessing(doc.status)"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { sseClient } from '@/services/sseClient'
import type { FileStatusUpdate } from '@/services/sseClient'

interface Document {
  id: string
  name: string
  status: string
  progress: number
  progressMsg?: string
  size: number
  unsubscribe?: () => void
}

const props = defineProps<{
  datasetId: string
}>()

const documents = ref<Document[]>([])
const fileInput = ref<HTMLInputElement>()

// 处理文件选择
const handleFileSelect = (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (files) {
    uploadFiles(Array.from(files))
  }
}

// 处理拖拽
const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  const files = event.dataTransfer?.files
  if (files) {
    uploadFiles(Array.from(files))
  }
}

// 上传文件
const uploadFiles = async (files: File[]) => {
  try {
    const formData = new FormData()
    files.forEach(file => {
      formData.append('files', file)
    })

    const response = await fetch(`/api/v1/datasets/${props.datasetId}/documents/upload`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error('上传失败')
    }

    const result = await response.json()
    
    // 添加到文档列表
    if (result.code === 0 && result.data) {
      result.data.forEach((doc: any) => {
        const document: Document = {
          id: doc.id,
          name: doc.name,
          status: 'UPLOAD_SUCCESS',
          progress: 0,
          size: doc.size
        }
        documents.value.push(document)
      })
    }
  } catch (error) {
    console.error('上传失败:', error)
    alert('文件上传失败')
  }
}

// 解析文档
const parseDocument = async (doc: Document) => {
  try {
    // 调用解析接口
    const response = await fetch(`/api/v1/datasets/${props.datasetId}/chunks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_ids: [doc.id]
      })
    })

    if (!response.ok) {
      throw new Error('解析请求失败')
    }

    // 更新状态为解析中
    doc.status = 'PARSING'
    doc.progress = 0

    // 订阅 SSE 状态更新
    doc.unsubscribe = sseClient.subscribeFileStatus(
      props.datasetId,
      doc.id,
      (update: FileStatusUpdate) => {
        handleStatusUpdate(doc, update)
      },
      (error) => {
        console.error('SSE 错误:', error)
        doc.status = 'PARSE_FAILED'
      }
    )
  } catch (error) {
    console.error('解析失败:', error)
    doc.status = 'PARSE_FAILED'
  }
}

// 处理状态更新
const handleStatusUpdate = (doc: Document, update: FileStatusUpdate) => {
  if (update.type === 'status') {
    doc.status = update.status || doc.status
    doc.progress = update.progress || 0
    doc.progressMsg = update.progress_msg
  } else if (update.type === 'complete') {
    doc.status = update.success ? 'PARSE_SUCCESS' : 'PARSE_FAILED'
    doc.progress = 1
    doc.progressMsg = undefined
    
    // 解析完成，取消订阅
    if (doc.unsubscribe) {
      doc.unsubscribe()
      doc.unsubscribe = undefined
    }
  } else if (update.type === 'error' || update.type === 'timeout') {
    doc.status = 'PARSE_FAILED'
    doc.progressMsg = update.error || '处理超时'
    
    if (doc.unsubscribe) {
      doc.unsubscribe()
      doc.unsubscribe = undefined
    }
  }
}

// 下载文档
const downloadDocument = async (doc: Document) => {
  try {
    const response = await fetch(
      `/api/v1/datasets/${props.datasetId}/documents/${doc.id}/download`
    )
    
    if (!response.ok) {
      throw new Error('下载失败')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = doc.name
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    alert('文件下载失败')
  }
}

// 删除文档
const deleteDocument = async (doc: Document) => {
  if (!confirm(`确定要删除文档 "${doc.name}" 吗？`)) {
    return
  }

  try {
    const response = await fetch(
      `/api/v1/datasets/${props.datasetId}/documents`,
      {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ids: [doc.id]
        })
      }
    )

    if (!response.ok) {
      throw new Error('删除失败')
    }

    // 如果有订阅，先取消
    if (doc.unsubscribe) {
      doc.unsubscribe()
    }

    // 从列表中移除
    const index = documents.value.findIndex(d => d.id === doc.id)
    if (index > -1) {
      documents.value.splice(index, 1)
    }
  } catch (error) {
    console.error('删除失败:', error)
    alert('文档删除失败')
  }
}

// 获取状态样式类
const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    UPLOADING: 'status-uploading',
    UPLOAD_SUCCESS: 'status-success',
    UPLOAD_FAILED: 'status-failed',
    PARSING: 'status-parsing',
    PARSE_SUCCESS: 'status-success',
    PARSE_FAILED: 'status-failed'
  }
  return statusMap[status] || ''
}

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    UPLOADING: '上传中',
    UPLOAD_SUCCESS: '上传成功',
    UPLOAD_FAILED: '上传失败',
    PARSING: '解析中',
    PARSE_SUCCESS: '解析成功',
    PARSE_FAILED: '解析失败'
  }
  return textMap[status] || status
}

// 判断是否正在处理中
const isProcessing = (status: string) => {
  return status === 'UPLOADING' || status === 'PARSING'
}

// 组件卸载时清理
onUnmounted(() => {
  // 取消所有 SSE 订阅
  documents.value.forEach(doc => {
    if (doc.unsubscribe) {
      doc.unsubscribe()
    }
  })
})
</script>

<style scoped>
.document-upload {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.upload-area {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  margin-bottom: 20px;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #666;
}

.document-list {
  margin-top: 20px;
}

.document-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  background: #f9f9f9;
}

.doc-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.doc-name {
  font-weight: 500;
  color: #333;
}

.doc-status {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-uploading,
.status-parsing {
  background: #e3f2fd;
  color: #1976d2;
}

.status-success {
  background: #e8f5e9;
  color: #388e3c;
}

.status-failed {
  background: #ffebee;
  color: #d32f2f;
}

.progress-bar {
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin: 8px 0;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: #1976d2;
  transition: width 0.3s ease;
}

.progress-text {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  color: #666;
}

.progress-msg {
  font-size: 12px;
  color: #666;
  margin: 4px 0;
}

.doc-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.doc-actions button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.doc-actions button:hover:not(:disabled) {
  background: #f5f5f5;
  border-color: #999;
}

.doc-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>