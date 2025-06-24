#!/usr/bin/env python3
"""
获取FastAPI接口文档并生成Markdown格式
"""

import requests
import json
from datetime import datetime

def fetch_openapi_spec(base_url="http://localhost:8050"):
    """获取OpenAPI规范"""
    try:
        response = requests.get(f"{base_url}/openapi.json")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"获取API文档失败: {e}")
        return None

def parse_openapi_to_markdown(spec):
    """将OpenAPI规范转换为Markdown格式"""
    if not spec:
        return "# API文档获取失败\n"
    
    md_content = []
    
    # 标题和基本信息
    md_content.append(f"# {spec.get('info', {}).get('title', 'API文档')}")
    md_content.append(f"\n**版本**: {spec.get('info', {}).get('version', 'N/A')}")
    md_content.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md_content.append("\n---\n")
    
    # 服务器信息
    servers = spec.get('servers', [])
    if servers:
        md_content.append("## 服务器信息")
        for server in servers:
            md_content.append(f"- {server.get('url', 'N/A')}")
        md_content.append("\n")
    
    # 接口列表
    paths = spec.get('paths', {})
    if paths:
        md_content.append("## 接口列表\n")
        
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    md_content.append(f"### {method.upper()} {path}")
                    
                    # 接口描述
                    summary = details.get('summary', '')
                    description = details.get('description', '')
                    if summary:
                        md_content.append(f"\n**摘要**: {summary}")
                    if description:
                        md_content.append(f"\n**描述**: {description}")
                    
                    # 标签
                    tags = details.get('tags', [])
                    if tags:
                        md_content.append(f"\n**标签**: {', '.join(tags)}")
                    
                    # 请求参数
                    parameters = details.get('parameters', [])
                    if parameters:
                        md_content.append("\n#### 请求参数")
                        md_content.append("| 参数名 | 位置 | 类型 | 必需 | 描述 |")
                        md_content.append("|--------|------|------|------|------|")
                        for param in parameters:
                            name = param.get('name', 'N/A')
                            in_type = param.get('in', 'N/A')
                            schema = param.get('schema', {})
                            param_type = schema.get('type', 'N/A')
                            required = "是" if param.get('required', False) else "否"
                            description = param.get('description', '')
                            md_content.append(f"| {name} | {in_type} | {param_type} | {required} | {description} |")
                    
                    # 请求体
                    request_body = details.get('requestBody', {})
                    if request_body:
                        md_content.append("\n#### 请求体")
                        content = request_body.get('content', {})
                        for content_type, schema_info in content.items():
                            md_content.append(f"\n**Content-Type**: {content_type}")
                            schema = schema_info.get('schema', {})
                            
                            # 如果有引用，尝试解析
                            if '$ref' in schema:
                                ref_path = schema['$ref'].split('/')[-1]
                                schema = spec.get('components', {}).get('schemas', {}).get(ref_path, schema)
                            
                            # 显示属性
                            properties = schema.get('properties', {})
                            required_fields = schema.get('required', [])
                            if properties:
                                md_content.append("\n| 字段名 | 类型 | 必需 | 描述 |")
                                md_content.append("|--------|------|------|------|")
                                for prop_name, prop_details in properties.items():
                                    prop_type = prop_details.get('type', 'N/A')
                                    if 'items' in prop_details:
                                        prop_type = f"array[{prop_details['items'].get('type', 'N/A')}]"
                                    required = "是" if prop_name in required_fields else "否"
                                    description = prop_details.get('description', '') or prop_details.get('title', '')
                                    default = prop_details.get('default', '')
                                    if default:
                                        description += f" (默认: {default})"
                                    md_content.append(f"| {prop_name} | {prop_type} | {required} | {description} |")
                    
                    # 响应
                    responses = details.get('responses', {})
                    if responses:
                        md_content.append("\n#### 响应")
                        for status_code, response_details in responses.items():
                            description = response_details.get('description', '')
                            md_content.append(f"\n**{status_code}**: {description}")
                            
                            content = response_details.get('content', {})
                            for content_type, schema_info in content.items():
                                md_content.append(f"\n**Content-Type**: {content_type}")
                    
                    md_content.append("\n---\n")
    
    # 数据模型
    schemas = spec.get('components', {}).get('schemas', {})
    if schemas:
        md_content.append("## 数据模型\n")
        for schema_name, schema_details in schemas.items():
            md_content.append(f"### {schema_name}")
            
            description = schema_details.get('description', '') or schema_details.get('title', '')
            if description:
                md_content.append(f"\n{description}\n")
            
            properties = schema_details.get('properties', {})
            required_fields = schema_details.get('required', [])
            if properties:
                md_content.append("| 字段名 | 类型 | 必需 | 描述 |")
                md_content.append("|--------|------|------|------|")
                for prop_name, prop_details in properties.items():
                    prop_type = prop_details.get('type', 'N/A')
                    if 'items' in prop_details:
                        prop_type = f"array[{prop_details['items'].get('type', 'N/A')}]"
                    required = "是" if prop_name in required_fields else "否"
                    description = prop_details.get('description', '') or prop_details.get('title', '')
                    default = prop_details.get('default', '')
                    if default:
                        description += f" (默认: {default})"
                    md_content.append(f"| {prop_name} | {prop_type} | {required} | {description} |")
            
            md_content.append("\n")
    
    return '\n'.join(md_content)

def main():
    print("正在获取API文档...")
    spec = fetch_openapi_spec()
    
    if spec:
        markdown_content = parse_openapi_to_markdown(spec)
        
        # 保存到文件
        output_file = "old_dev_api_docs.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"API文档已保存到: {output_file}")
    else:
        print("无法获取API文档")

if __name__ == "__main__":
    main()