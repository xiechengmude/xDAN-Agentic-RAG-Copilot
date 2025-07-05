#!/usr/bin/env python3
"""Fix all types of smart quotes in JSON file"""
import re

# Read the file
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all types of smart quotes
# Double quotes
content = content.replace('"', '"').replace('"', '"')
content = content.replace('"', '"').replace('"', '"')
# Single quotes (if any)
content = content.replace(''', "'").replace(''', "'")
content = content.replace(''', "'").replace(''', "'")

# Also fix escaped quotes inside JSON strings
# This pattern finds quotes that should be escaped in JSON values
content = re.sub(r'("answer_correct":\s*"[^"]*)"([^"]*"[^"]*")', r'\1\\"\\2', content)
content = re.sub(r'("question":\s*"[^"]*)"([^"]*"[^"]*")', r'\1\\"\\2', content)

# Write back
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all smart quotes in JSON file")