import json
import re
from collections import defaultdict

# Load the JSON file
with open('parallel_test_report_20250630_001224.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find common questions across all versions
question_versions = defaultdict(list)
for version_key, version_data in data['versions'].items():
    for result in version_data['results']:
        question_id = result['question_id']
        question_versions[question_id].append((version_key, result))

# Find questions that appear in all 3 versions
common_questions = {qid: results for qid, results in question_versions.items() if len(results) == 3}

print(f"Total common questions: {len(common_questions)}\n")

# Analyze structure patterns
structure_analysis = {
    'original': defaultdict(int),
    'lite': defaultdict(int),
    'full': defaultdict(int)
}

# Detailed analysis for 3 representative questions
selected_questions = ['data_analysis_1745567367_1', 'travel_planning_1745567367_44', 'programming_1745567367_28']

for q_idx, question_id in enumerate(selected_questions):
    if question_id not in common_questions:
        print(f"Question {question_id} not found in common questions")
        continue
        
    print(f"\n{'='*100}")
    print(f"Detailed Analysis #{q_idx + 1}: {question_id}")
    
    # Get question details from first occurrence
    first_result = common_questions[question_id][0][1]
    print(f"Question: {first_result['question'][:150]}...")
    print(f"Category: {first_result['category']}")
    print(f"{'='*100}\n")
    
    # Analyze each version
    version_responses = {}
    for version_key, result in common_questions[question_id]:
        version_responses[version_key] = result
    
    # Compare versions side by side
    print("Version Comparison:")
    print("-" * 100)
    print(f"{'Metric':<30} {'Original':<25} {'Lite':<25} {'Full':<25}")
    print("-" * 100)
    
    # Response length
    print(f"{'Response Length:':<30} {version_responses['original']['response_length']:<25} "
          f"{version_responses['lite']['response_length']:<25} {version_responses['full']['response_length']:<25}")
    
    # Execution time
    print(f"{'Execution Time (s):':<30} {version_responses['original']['execution_time']:<25.2f} "
          f"{version_responses['lite']['execution_time']:<25.2f} {version_responses['full']['execution_time']:<25.2f}")
    
    # Overall score
    print(f"{'Overall Score:':<30} {version_responses['original']['overall_score']:<25} "
          f"{version_responses['lite']['overall_score']:<25} {version_responses['full']['overall_score']:<25}")
    
    print("\nStructural Elements:")
    print("-" * 100)
    
    # Check for various tags and patterns
    patterns = {
        '<thinking>': 'Thinking tags',
        '<search_complete>': 'Search complete tag',
        '<query>': 'Query tag',
        '<search_query>': 'Search query tag',
        '<search_queries>': 'Search queries tag',
        '<important_info>': 'Important info tag',
        '<important_urls>': 'Important URLs tag',
        '<next_query>': 'Next query tag',
        '**Search/Select:**': 'Search/Select header',
        '[Current State]': 'Current State section',
        '[URL Analysis]': 'URL Analysis section',
        '[Decision]': 'Decision section'
    }
    
    for pattern, description in patterns.items():
        original_has = pattern in version_responses['original']['response_text']
        lite_has = pattern in version_responses['lite']['response_text']
        full_has = pattern in version_responses['full']['response_text']
        
        if original_has or lite_has or full_has:
            print(f"{description:<30} {'✓' if original_has else '✗':<25} "
                  f"{'✓' if lite_has else '✗':<25} {'✓' if full_has else '✗':<25}")
    
    print("\nResponse Excerpts:")
    print("-" * 100)
    
    for version_name, version_key in [('Original', 'original'), ('Lite', 'lite'), ('Full', 'full')]:
        print(f"\n{version_name} Version:")
        response = version_responses[version_key]['response_text']
        # Show first 400 characters or until first major tag closure
        excerpt = response[:400]
        if len(response) > 400:
            excerpt += "..."
        print(excerpt)

# Summary statistics across all common questions
print(f"\n\n{'='*100}")
print("SUMMARY STATISTICS ACROSS ALL COMMON QUESTIONS")
print("="*100)

for version_key in ['original', 'lite', 'full']:
    total_score = 0
    total_time = 0
    total_length = 0
    count = 0
    
    tag_counts = defaultdict(int)
    
    for qid, results in common_questions.items():
        for vkey, result in results:
            if vkey == version_key:
                total_score += result['overall_score']
                total_time += result['execution_time']
                total_length += result['response_length']
                count += 1
                
                # Count tags
                response = result['response_text']
                if '<thinking>' in response: tag_counts['thinking'] += 1
                if '<search_complete>' in response: tag_counts['search_complete'] += 1
                if '<query>' in response or '<search_query>' in response: tag_counts['query'] += 1
                if '<important_urls>' in response: tag_counts['important_urls'] += 1
                if '[Current State]' in response: tag_counts['current_state'] += 1
    
    print(f"\n{data['versions'][version_key]['name']} ({version_key}):")
    print(f"  Average Score: {total_score/count:.2f}")
    print(f"  Average Time: {total_time/count:.2f}s")
    print(f"  Average Response Length: {total_length/count:.0f} chars")
    print(f"  Tag Usage (out of {count} responses):")
    print(f"    - Thinking tags: {tag_counts['thinking']} ({tag_counts['thinking']/count*100:.1f}%)")
    print(f"    - Search complete: {tag_counts['search_complete']} ({tag_counts['search_complete']/count*100:.1f}%)")
    print(f"    - Query tags: {tag_counts['query']} ({tag_counts['query']/count*100:.1f}%)")
    print(f"    - Important URLs: {tag_counts['important_urls']} ({tag_counts['important_urls']/count*100:.1f}%)")
    print(f"    - Current State: {tag_counts['current_state']} ({tag_counts['current_state']/count*100:.1f}%)")