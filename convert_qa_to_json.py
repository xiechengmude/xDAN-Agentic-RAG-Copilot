#!/usr/bin/env python3
"""
将问答Markdown文件转换为JSON格式
"""

import json
import re

def parse_qa_markdown(file_path):
    """解析问答Markdown文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    qa_pairs = []
    
    # 分割文本为问答块
    # 使用正则表达式找到所有问题的开始位置
    pattern = r'^(\d+)[、．.]\s*(.+?)(?=\n\n\*\*A\*\*[：:]|$)'
    
    # 将内容按照问答对分割
    blocks = re.split(r'\n\n(?=\d+[、．.])', content.strip())
    
    for block in blocks:
        if not block.strip() or block.strip() == '问题：':
            continue
            
        lines = block.strip().split('\n')
        
        # 找到问题行
        question = None
        answer_lines = []
        in_answer = False
        
        for line in lines:
            # 匹配问题行
            question_match = re.match(r'^(\d+)[、．.]\s*(.+)$', line.strip())
            if question_match:
                question = question_match.group(2).strip()
                continue
            
            # 匹配答案开始
            if line.strip().startswith('**A**：') or line.strip().startswith('**A**:'):
                in_answer = True
                answer_text = line.replace('**A**：', '').replace('**A**:', '').strip()
                if answer_text:
                    answer_lines.append(answer_text)
                continue
            
            # 跳过引用行
            if line.strip().startswith('>'):
                continue
                
            # 收集答案内容
            if in_answer and line.strip():
                # 处理列表项
                if line.strip().startswith('会调用的接口：') or line.strip().startswith('不会调用的接口：'):
                    answer_lines.append('\n' + line.strip())
                elif re.match(r'^\s+\d+\.', line):  # 缩进的列表项
                    answer_lines.append(line.strip())
                else:
                    answer_lines.append(line.strip())
        
        if question and answer_lines:
            qa_pairs.append({
                "question": question,
                "reference_answer": ' '.join(answer_lines)
            })
    
    return qa_pairs

def main():
    # 输入文件路径
    input_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/data/阶段二/问题集/阶段二问答.md"
    output_file = "/Users/gump_m2/CascadeProjects/ragflow-api-client/data/阶段二/问题集/阶段二问答.json"
    
    # 解析问答
    qa_pairs = parse_qa_markdown(input_file)
    
    # 清理和格式化答案
    for qa in qa_pairs:
        # 移除多余的空行
        qa['reference_answer'] = re.sub(r'\n\s*\n', '\n', qa['reference_answer'])
        # 确保答案不为空
        if not qa['reference_answer']:
            qa['reference_answer'] = "答案待补充"
    
    # 保存为JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 成功转换 {len(qa_pairs)} 个问答对")
    print(f"📁 输出文件: {output_file}")
    
    # 显示前3个问答示例
    print("\n📋 示例内容:")
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"\n问题 {i}: {qa['question']}")
        print(f"答案: {qa['reference_answer'][:100]}...")

if __name__ == "__main__":
    main()