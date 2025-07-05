#!/usr/bin/env python3
"""Fix smart quotes in JSON file"""

# Read the file
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace smart quotes with regular quotes
content = content.replace('"', '"').replace('"', '"')

# Write back
with open('/Users/gump_m2/CascadeProjects/ragflow-api-client/questions/test2/阶段二问答.json', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed smart quotes in JSON file")