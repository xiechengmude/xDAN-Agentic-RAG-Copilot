/**
 * API相关的TypeScript类型定义
 * 基于测试结果的真实API响应格式
 */

// ============= 基础类型 =============

export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data?: T;
  meta?: {
    page?: number;
    size?: number;
    total?: number;
    has_next?: boolean;
    has_prev?: boolean;
  };
}

export interface PageParams {
  page?: number;
  page_size?: number;
}

// ============= 知识库相关类型 =============

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  avatar: string;
  document_count: number;
  chunk_count: number;
  token_num: number;
  embedding_model: string;
  chunk_method: string;
  status: string;
  language: string;
  similarity_threshold: number;
  vector_similarity_weight: number;
  pagerank: number;
  permission: string;
  tenant_id: string;
  created_by: string;
  create_date: string;
  create_time: number;
  update_date: string;
  update_time: number;
  parser_config: {
    chunk_token_num: number;
    delimiter: string;
    auto_keywords: number;
    auto_questions: number;
    pages?: number[][];
    html4excel?: boolean;
    layout_recognize?: string;
    graphrag?: {
      use_graphrag: boolean;
    };
    raptor?: {
      use_raptor: boolean;
    };
  };
}

export interface CreateDatasetDto {
  name: string;
  description?: string;
  embedding_model: string; // 格式: "模型名@提供商"，如 "BAAI/bge-m3@SILICONFLOW"
  chunk_method?: string;
  language?: string;
  similarity_threshold?: number;
  vector_similarity_weight?: number;
  parser_config?: {
    chunk_token_num?: number;
    delimiter?: string;
    auto_keywords?: number;
    auto_questions?: number;
  };
}

export interface UpdateDatasetDto {
  name?: string;
  description?: string;
  similarity_threshold?: number;
  vector_similarity_weight?: number;
  parser_config?: Partial<Dataset['parser_config']>;
}

export interface ListDatasetParams extends PageParams {
  name?: string;
}

// ============= 文档相关类型 =============

export interface Document {
  id: string;
  name: string;
  location: string;
  size: number;
  type: string;
  thumbnail: string;
  dataset_id: string;
  created_by: string;
  run: DocumentRunStatus;
  chunk_method: string;
  parser_config: Dataset['parser_config'];
}

export enum DocumentRunStatus {
  UNSTART = 'UNSTART',
  RUNNING = 'RUNNING',
  CANCEL = 'CANCEL',
  DONE = 'DONE',
  FAIL = 'FAIL'
}

export interface DocumentListResponse {
  docs: Document[];
  total: number;
}

export interface ListDocumentParams extends PageParams {
  status?: DocumentRunStatus;
}

export interface UploadDocumentResponse {
  id: string;
  name: string;
  size: number;
  type: string;
  dataset_id: string;
}

// ============= 对话相关类型 =============

export interface Chat {
  id: string;
  name: string;
  description: string;
  avatar: string;
  dataset_ids: string[];
  language: string;
  do_refer: string;
  permission: string;
  tenant_id: string;
  created_by: string;
  create_date: string;
  create_time: number;
  update_date: string;
  update_time: number;
  llm: {
    model_name: string;
    temperature: number;
    top_p: number;
    presence_penalty: number;
    frequency_penalty: number;
    max_tokens: number;
  };
}

export interface CreateChatDto {
  name: string;
  dataset_ids: string[];
  description?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  session_id?: string;
  reference?: {
    chunks: SearchResult[];
  };
}

export interface SendMessageDto {
  content: string;
  question?: string; // 备用字段名
}

// ============= SSE流式响应类型 =============

export interface ChatStreamMessage {
  code: number;
  message: string;
  data: {
    answer?: string;
    reference?: {
      chunks: SearchResult[];
    };
    session_id?: string;
    audio_binary?: any;
    id?: string | null;
  } | boolean; // 第二个data可能是boolean表示结束
}

export interface FileStatusUpdate {
  type: 'status' | 'progress' | 'complete' | 'error' | 'timeout';
  doc_id: string;
  status?: DocumentRunStatus;
  progress?: number;
  progress_msg?: string;
  error?: string;
  success?: boolean;
  timestamp?: string;
}

// ============= 检索相关类型 =============

export interface SearchResult {
  id: string;
  content_ltks: string;
  similarity: number;
  document_name?: string;
  dataset_id?: string;
  positions?: any[];
  [key: string]: any;
}

export interface RetrievalParams {
  question: string;
  dataset_ids: string[];
  page?: number;
  page_size?: number;
}

export interface RetrievalResponse {
  chunks: SearchResult[];
  total?: number;
}

// ============= 用户相关类型 =============

export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  role: string;
  tenant_id: string;
  create_date: string;
  status: string;
}

export interface LoginDto {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ============= 错误类型 =============

export interface ApiError {
  code: number;
  message: string;
  details?: any;
  trace_id?: string;
}

// ============= 统计和仪表板类型 =============

export interface DashboardStats {
  total_datasets: number;
  total_documents: number;
  total_chunks: number;
  total_chats: number;
  storage_used: number;
  storage_limit: number;
}

// ============= 任务相关类型 =============

export interface Task {
  id: string;
  type: 'parse' | 'upload' | 'embedding';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  message?: string;
  created_at: string;
  updated_at: string;
  dataset_id?: string;
  document_id?: string;
}

// ============= 配置相关类型 =============

export interface SystemConfig {
  max_file_size: number;
  allowed_file_types: string[];
  chunk_size_range: [number, number];
  embedding_models: {
    name: string;
    provider: string;
    description: string;
  }[];
  llm_models: {
    name: string;
    provider: string;
    description: string;
  }[];
}

// ============= 工具类型 =============

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequestWithPagination<T = {}> = T & PageParams;

export type ResponseWithPagination<T> = ApiResponse<T> & {
  meta: {
    page: number;
    size: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
};

// ============= 事件类型 =============

export interface SystemEvent {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  data?: any;
}

// ============= 权限相关类型 =============

export interface Permission {
  resource: string;
  action: string;
  allowed: boolean;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
}

// ============= 常量定义 =============

export const API_ENDPOINTS = {
  // 知识库
  DATASETS: '/api/v1/datasets',
  DATASET_DETAIL: (id: string) => `/api/v1/datasets/${id}`,
  
  // 文档
  DOCUMENTS: (datasetId: string) => `/api/v1/datasets/${datasetId}/documents`,
  DOCUMENT_DETAIL: (datasetId: string, docId: string) => `/api/v1/datasets/${datasetId}/documents/${docId}`,
  DOCUMENT_PARSE: (datasetId: string, docId: string) => `/api/v1/datasets/${datasetId}/documents/${docId}/run`,
  DOCUMENT_DOWNLOAD: (datasetId: string, docId: string) => `/api/v1/datasets/${datasetId}/documents/${docId}/download`,
  
  // 对话
  CHATS: '/api/v1/chats',
  CHAT_DETAIL: (id: string) => `/api/v1/chats/${id}`,
  CHAT_MESSAGES: (id: string) => `/api/v1/chats/${id}/messages`,
  CHAT_COMPLETIONS: (id: string) => `/api/v1/chats/${id}/completions`,
  
  // 检索
  RETRIEVAL: '/api/v1/retrieval',
  
  // 用户
  LOGIN: '/api/v1/auth/login',
  LOGOUT: '/api/v1/auth/logout',
  USER_PROFILE: '/api/v1/user/profile',
  
  // 系统
  SYSTEM_CONFIG: '/api/v1/system/config',
  DASHBOARD_STATS: '/api/v1/dashboard/stats',
} as const;

export const FILE_TYPES = {
  DOCUMENT: ['pdf', 'doc', 'docx', 'txt', 'md'],
  SPREADSHEET: ['xls', 'xlsx', 'csv'],
  PRESENTATION: ['ppt', 'pptx'],
  IMAGE: ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
  ALL_SUPPORTED: ['pdf', 'doc', 'docx', 'txt', 'md', 'xls', 'xlsx', 'csv', 'ppt', 'pptx'],
} as const;

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const DEFAULT_PAGE_SIZE = 20;

export const EMBEDDING_MODELS = [
  'BAAI/bge-m3@SILICONFLOW',
  'BAAI/bge-large-zh-v1.5@SILICONFLOW',
  'text-embedding-ada-002@OPENAI',
] as const;