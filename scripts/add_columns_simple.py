#!/usr/bin/env python3
"""Simply add index, xdan-rag-system, and 对比评价 columns to the JSON file"""
import json

# Read the original file
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'r', encoding='utf-8') as f:
    qa_data = json.load(f)

# Add columns
results = []
for idx, item in enumerate(qa_data, 1):
    result_item = {
        'index': idx,
        'question': item['question'],
        'answer_correct': item['answer_correct'],
        'xdan-rag-system': '',  # Empty for now
        '对比评价': ''  # Empty for now
    }
    results.append(result_item)

# Save the result
output_file = '/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_with_columns.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Added columns to {len(results)} items")
print(f"Saved to: {output_file}")