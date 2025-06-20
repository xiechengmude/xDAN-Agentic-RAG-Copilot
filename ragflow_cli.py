#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAGFlow 命令行工具

这个脚本提供了一个命令行界面，用于与 RAGFlow API 进行交互。
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from src.clients.ragflow_client import RAGFlowClient

# 加载环境变量
load_dotenv()

def print_json(obj):
    """美化打印 JSON 对象"""
    print(json.dumps(obj, ensure_ascii=False, indent=2))

def list_datasets(client: RAGFlowClient, args):
    """列出数据集"""
    response = client.list_datasets(
        page=args.page,
        page_size=args.page_size,
        orderby=args.orderby,
        desc=not args.asc,
        name=args.name,
        id=args.id
    )
    print_json(response)

def create_dataset(client: RAGFlowClient, args):
    """创建数据集"""
    response = client.create_dataset(
        name=args.name,
        description=args.description,
        embedding_model=args.embedding_model,
        permission=args.permission,
        chunk_method=args.chunk_method
    )
    print_json(response)

def delete_dataset(client: RAGFlowClient, args):
    """删除数据集"""
    response = client.delete_datasets(ids=[args.id])
    print_json(response)

def list_documents(client: RAGFlowClient, args):
    """列出文档"""
    response = client.list_documents(
        dataset_id=args.dataset_id,
        page=args.page,
        page_size=args.page_size,
        orderby=args.orderby,
        desc=not args.asc,
        keywords=args.keywords,
        id=args.id,
        name=args.name
    )
    print_json(response)

def upload_document(client: RAGFlowClient, args):
    """上传文档"""
    response = client.upload_documents(
        dataset_id=args.dataset_id,
        file_paths=[args.file_path]
    )
    print_json(response)

def delete_document(client: RAGFlowClient, args):
    """删除文档"""
    response = client.delete_documents(
        dataset_id=args.dataset_id,
        document_ids=[args.document_id]
    )
    print_json(response)

def parse_document(client: RAGFlowClient, args):
    """解析文档"""
    response = client.parse_documents(
        dataset_id=args.dataset_id,
        document_ids=[args.document_id]
    )
    print_json(response)

def retrieve(client: RAGFlowClient, args):
    """检索文本块"""
    response = client.retrieve_chunks(
        question=args.question,
        dataset_ids=[args.dataset_id] if args.dataset_id else None,
        document_ids=[args.document_id] if args.document_id else None,
        page=args.page,
        page_size=args.page_size,
        similarity_threshold=args.similarity_threshold,
        vector_similarity_weight=args.vector_similarity_weight,
        top_k=args.top_k,
        keyword=args.keyword,
        highlight=args.highlight
    )
    print_json(response)

def chat(client: RAGFlowClient, args):
    """与聊天助手交互"""
    messages = [{"role": "user", "content": args.message}]
    response = client.create_chat_completion(
        chat_id=args.chat_id,
        model=args.model,
        messages=messages,
        stream=False
    )
    print_json(response)

def agent(client: RAGFlowClient, args):
    """与 Agent 交互"""
    messages = [{"role": "user", "content": args.message}]
    response = client.create_agent_completion(
        agent_id=args.agent_id,
        model=args.model,
        messages=messages,
        stream=False
    )
    print_json(response)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="RAGFlow 命令行工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 数据集相关命令
    
    # list-datasets
    parser_list_datasets = subparsers.add_parser("list-datasets", help="列出数据集")
    parser_list_datasets.add_argument("--page", type=int, default=1, help="页码")
    parser_list_datasets.add_argument("--page-size", type=int, default=30, help="每页大小")
    parser_list_datasets.add_argument("--orderby", default="create_time", choices=["create_time", "update_time"], help="排序字段")
    parser_list_datasets.add_argument("--asc", action="store_true", help="升序排序")
    parser_list_datasets.add_argument("--name", help="按名称过滤")
    parser_list_datasets.add_argument("--id", help="按 ID 过滤")
    
    # create-dataset
    parser_create_dataset = subparsers.add_parser("create-dataset", help="创建数据集")
    parser_create_dataset.add_argument("--name", required=True, help="数据集名称")
    parser_create_dataset.add_argument("--description", help="数据集描述")
    parser_create_dataset.add_argument("--embedding-model", help="嵌入模型")
    parser_create_dataset.add_argument("--permission", default="me", choices=["me", "team"], help="权限")
    parser_create_dataset.add_argument("--chunk-method", default="naive", 
                                     choices=["naive", "book", "email", "laws", "manual", "one", 
                                              "paper", "picture", "presentation", "qa", "table", "tag"], 
                                     help="分块方法")
    
    # delete-dataset
    parser_delete_dataset = subparsers.add_parser("delete-dataset", help="删除数据集")
    parser_delete_dataset.add_argument("--id", required=True, help="数据集 ID")
    
    # 文档相关命令
    
    # list-documents
    parser_list_documents = subparsers.add_parser("list-documents", help="列出文档")
    parser_list_documents.add_argument("--dataset-id", required=True, help="数据集 ID")
    parser_list_documents.add_argument("--page", type=int, default=1, help="页码")
    parser_list_documents.add_argument("--page-size", type=int, default=30, help="每页大小")
    parser_list_documents.add_argument("--orderby", default="create_time", choices=["create_time", "update_time"], help="排序字段")
    parser_list_documents.add_argument("--asc", action="store_true", help="升序排序")
    parser_list_documents.add_argument("--keywords", help="关键词过滤")
    parser_list_documents.add_argument("--id", help="按 ID 过滤")
    parser_list_documents.add_argument("--name", help="按名称过滤")
    
    # upload-document
    parser_upload_document = subparsers.add_parser("upload-document", help="上传文档")
    parser_upload_document.add_argument("--dataset-id", required=True, help="数据集 ID")
    parser_upload_document.add_argument("--file-path", required=True, help="文件路径")
    
    # delete-document
    parser_delete_document = subparsers.add_parser("delete-document", help="删除文档")
    parser_delete_document.add_argument("--dataset-id", required=True, help="数据集 ID")
    parser_delete_document.add_argument("--document-id", required=True, help="文档 ID")
    
    # parse-document
    parser_parse_document = subparsers.add_parser("parse-document", help="解析文档")
    parser_parse_document.add_argument("--dataset-id", required=True, help="数据集 ID")
    parser_parse_document.add_argument("--document-id", required=True, help="文档 ID")
    
    # 检索相关命令
    
    # retrieve
    parser_retrieve = subparsers.add_parser("retrieve", help="检索文本块")
    parser_retrieve.add_argument("--question", required=True, help="问题")
    parser_retrieve.add_argument("--dataset-id", help="数据集 ID")
    parser_retrieve.add_argument("--document-id", help="文档 ID")
    parser_retrieve.add_argument("--page", type=int, default=1, help="页码")
    parser_retrieve.add_argument("--page-size", type=int, default=10, help="每页大小")
    parser_retrieve.add_argument("--similarity-threshold", type=float, default=0.2, help="相似度阈值")
    parser_retrieve.add_argument("--vector-similarity-weight", type=float, default=0.3, help="向量相似度权重")
    parser_retrieve.add_argument("--top-k", type=int, default=1024, help="参与向量余弦计算的块数")
    parser_retrieve.add_argument("--keyword", action="store_true", help="启用关键词匹配")
    parser_retrieve.add_argument("--highlight", action="store_true", help="高亮匹配项")
    
    # 聊天相关命令
    
    # chat
    parser_chat = subparsers.add_parser("chat", help="与聊天助手交互")
    parser_chat.add_argument("--chat-id", required=True, help="聊天助手 ID")
    parser_chat.add_argument("--model", default="default", help="模型名称")
    parser_chat.add_argument("--message", required=True, help="消息内容")
    
    # agent
    parser_agent = subparsers.add_parser("agent", help="与 Agent 交互")
    parser_agent.add_argument("--agent-id", required=True, help="Agent ID")
    parser_agent.add_argument("--model", default="default", help="模型名称")
    parser_agent.add_argument("--message", required=True, help="消息内容")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有指定命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return
    
    # 创建 RAGFlow 客户端
    client = RAGFlowClient()
    
    # 根据命令执行相应的函数
    commands = {
        "list-datasets": list_datasets,
        "create-dataset": create_dataset,
        "delete-dataset": delete_dataset,
        "list-documents": list_documents,
        "upload-document": upload_document,
        "delete-document": delete_document,
        "parse-document": parse_document,
        "retrieve": retrieve,
        "chat": chat,
        "agent": agent
    }
    
    if args.command in commands:
        try:
            commands[args.command](client, args)
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
