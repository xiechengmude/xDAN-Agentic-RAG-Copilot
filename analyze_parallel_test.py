import json
from collections import defaultdict

# Load the JSON file
with open('parallel_test_report_20250630_001224.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find common questions across all versions
question_versions = defaultdict(list)
question_details = {}

for version_key, version_data in data['versions'].items():
    for result in version_data['results']:
        question_id = result['question_id']
        question_versions[question_id].append(version_key)
        if question_id not in question_details:
            question_details[question_id] = {
                'question': result['question'],
                'category': result['category'],
                'complexity': result['complexity']
            }

# Find questions that appear in all 3 versions
common_questions = {qid: versions for qid, versions in question_versions.items() if len(versions) == 3}

print(f"Found {len(common_questions)} questions tested in all 3 versions\n")

# Analyze 2 common questions in detail
analyzed_count = 0
for question_id in sorted(common_questions.keys())[:2]:
    analyzed_count += 1
    print(f"\n{'='*80}")
    print(f"Analysis #{analyzed_count}: {question_id}")
    print(f"Question: {question_details[question_id]['question'][:100]}...")
    print(f"Category: {question_details[question_id]['category']}")
    print(f"Complexity: {question_details[question_id]['complexity']}")
    print(f"{'='*80}\n")
    
    # Get responses from all versions
    for version_key, version_data in data['versions'].items():
        for result in version_data['results']:
            if result['question_id'] == question_id:
                print(f"\n### Version: {version_data['name']} ({version_key})")
                print(f"Response length: {result['response_length']} characters")
                print(f"Execution time: {result['execution_time']:.2f} seconds")
                print(f"Overall score: {result['overall_score']}")
                
                # Analyze response structure
                response = result['response_text']
                has_thinking = '<thinking>' in response
                has_search_complete = '<search_complete>' in response
                has_query = '<query>' in response or '<search_query>' in response
                
                print(f"\nStructure analysis:")
                print(f"- Has <thinking> tag: {has_thinking}")
                print(f"- Has <search_complete> tag: {has_search_complete}")
                print(f"- Has query tag: {has_query}")
                
                print(f"\nResponse content:")
                print("-" * 60)
                print(response[:500] + "..." if len(response) > 500 else response)
                print("-" * 60)