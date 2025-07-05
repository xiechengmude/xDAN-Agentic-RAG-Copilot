#!/usr/bin/env python3
"""Restore the original JSON structure from S3 results file"""
import json

# Read the S3 results file
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答_S3结果_batch_6_20250703_121150.json', 'r', encoding='utf-8') as f:
    s3_data = json.load(f)

# Extract only question and answer_correct fields
original_data = []
for item in s3_data:
    original_item = {
        'question': item['question'],
        'answer_correct': item['answer_correct']
    }
    original_data.append(original_item)

# Write to the original file
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'w', encoding='utf-8') as f:
    json.dump(original_data, f, ensure_ascii=False, indent=2)

print(f"Restored {len(original_data)} items to the original file")