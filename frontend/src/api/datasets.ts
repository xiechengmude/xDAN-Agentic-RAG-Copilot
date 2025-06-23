/**
 * 知识库管理API
 * 基于测试验证的真实API接口
 */

import { apiClient } from './client';
import type {
  Dataset,
  CreateDatasetDto,
  UpdateDatasetDto,
  ListDatasetParams,
  ApiResponse,
  API_ENDPOINTS,
} from './types';

export class DatasetAPI {
  /**
   * 获取知识库列表
   */
  async list(params: ListDatasetParams = {}): Promise<ApiResponse<Dataset[]>> {
    const queryParams = {
      page: params.page || 1,
      page_size: params.page_size || 20,
      ...(params.name && { name: params.name }),
    };

    return apiClient.get<Dataset[]>('/api/v1/datasets', queryParams);
  }

  /**
   * 创建知识库
   */
  async create(data: CreateDatasetDto): Promise<ApiResponse<Dataset>> {
    // 确保embedding_model格式正确
    const payload = {
      ...data,
      embedding_model: data.embedding_model.includes('@') 
        ? data.embedding_model 
        : `${data.embedding_model}@SILICONFLOW`,
      chunk_method: data.chunk_method || 'naive',
      parser_config: {
        chunk_token_num: 512,
        delimiter: '\n',
        auto_keywords: 0,
        auto_questions: 0,
        ...data.parser_config,
      },
    };

    return apiClient.post<Dataset>('/api/v1/datasets', payload);
  }

  /**
   * 获取知识库详情
   */
  async get(id: string): Promise<ApiResponse<Dataset>> {
    return apiClient.get<Dataset>(`/api/v1/datasets/${id}`);
  }

  /**
   * 更新知识库
   */
  async update(id: string, data: UpdateDatasetDto): Promise<ApiResponse<Dataset>> {
    return apiClient.put<Dataset>(`/api/v1/datasets/${id}`, data);
  }

  /**
   * 删除知识库
   */
  async delete(id: string): Promise<ApiResponse<void>> {
    return apiClient.delete<void>(`/api/v1/datasets/${id}`);
  }

  /**
   * 批量删除知识库
   */
  async batchDelete(ids: string[]): Promise<ApiResponse<void>> {
    const promises = ids.map(id => this.delete(id));
    await Promise.allSettled(promises);
    return { code: 0, message: '批量删除完成' };
  }

  /**
   * 搜索知识库
   */
  async search(query: string, params: ListDatasetParams = {}): Promise<ApiResponse<Dataset[]>> {
    return this.list({ ...params, name: query });
  }

  /**
   * 获取知识库统计信息
   */
  async getStats(id: string): Promise<ApiResponse<{
    document_count: number;
    chunk_count: number;
    token_count: number;
    last_update: string;
  }>> {
    try {
      const response = await this.get(id);
      if (response.code === 0 && response.data) {
        const dataset = response.data;
        return {
          code: 0,
          message: 'Success',
          data: {
            document_count: dataset.document_count,
            chunk_count: dataset.chunk_count,
            token_count: dataset.token_num,
            last_update: dataset.update_date,
          },
        };
      }
      throw new Error('获取知识库信息失败');
    } catch (error) {
      throw error;
    }
  }

  /**
   * 复制知识库
   */
  async clone(id: string, newName: string, newDescription?: string): Promise<ApiResponse<Dataset>> {
    try {
      // 先获取原知识库信息
      const originalResponse = await this.get(id);
      if (originalResponse.code !== 0 || !originalResponse.data) {
        throw new Error('获取原知识库信息失败');
      }

      const original = originalResponse.data;
      
      // 创建新知识库
      const cloneData: CreateDatasetDto = {
        name: newName,
        description: newDescription || `${original.description} (副本)`,
        embedding_model: original.embedding_model,
        chunk_method: original.chunk_method,
        parser_config: original.parser_config,
      };

      return this.create(cloneData);
    } catch (error) {
      throw error;
    }
  }

  /**
   * 检查知识库名称是否可用
   */
  async checkNameAvailable(name: string): Promise<boolean> {
    try {
      const response = await this.list({ name, page_size: 1 });
      if (response.code === 0 && response.data) {
        // 检查是否有完全匹配的名称
        return !response.data.some(dataset => dataset.name === name);
      }
      return true;
    } catch (error) {
      console.error('检查名称可用性失败:', error);
      return true; // 出错时假设可用
    }
  }

  /**
   * 获取推荐的embedding模型
   */
  async getRecommendedModels(): Promise<{
    name: string;
    provider: string;
    description: string;
    recommended: boolean;
  }[]> {
    // 这里可以后续从API获取，现在返回硬编码的推荐列表
    return [
      {
        name: 'BAAI/bge-m3@SILICONFLOW',
        provider: 'SILICONFLOW',
        description: '多语言通用模型，支持中英文',
        recommended: true,
      },
      {
        name: 'BAAI/bge-large-zh-v1.5@SILICONFLOW',
        provider: 'SILICONFLOW', 
        description: '中文优化的大模型',
        recommended: false,
      },
      {
        name: 'text-embedding-ada-002@OPENAI',
        provider: 'OPENAI',
        description: 'OpenAI的高质量embedding模型',
        recommended: false,
      },
    ];
  }
}

// 导出单例实例
export const datasetAPI = new DatasetAPI();