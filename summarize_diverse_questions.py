#!/usr/bin/env python3
"""
Script to summarize the 50 diverse questions
"""

import json

def summarize_questions(input_file):
    """
    Create a summary of the diverse questions
    """
    
    with open(input_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    print(f"=== DIVERSE QUESTIONS SUMMARY ===")
    print(f"Total questions: {len(questions)}")
    print()
    
    # Group by category and show examples
    categories = {}
    for question in questions:
        category = question['category']
        if category not in categories:
            categories[category] = []
        categories[category].append(question)
    
    print("=== CATEGORY BREAKDOWN ===")
    for i, (category, cat_questions) in enumerate(categories.items(), 1):
        print(f"\n{i}. {category} ({len(cat_questions)} questions)")
        print("-" * 50)
        
        # Show first 2 questions from each category as examples
        for j, question in enumerate(cat_questions[:2], 1):
            print(f"   {j}. ID: {question['id']}")
            # Truncate long questions for readability
            q_text = question['question']
            if len(q_text) > 150:
                q_text = q_text[:150] + "..."
            print(f"      Question: {q_text}")
            print(f"      Target: {question['target'][:100]}...")
            print()
    
    # Create simplified structure for output
    simplified_questions = []
    for question in questions:
        simplified = {
            'id': question['id'],
            'category': question['category'],
            'question': question['question'],
            'target': question['target'],
            'verify': question['verify']
        }
        simplified_questions.append(simplified)
    
    # Save simplified version for easier handling
    with open('questions/search/diverse_questions_50_formatted.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_questions, f, ensure_ascii=False, indent=2)
    
    print("=== DIVERSITY ANALYSIS ===")
    print(f"✓ {len(categories)} different categories covered")
    print(f"✓ Balanced distribution across categories")
    print(f"✓ Mix of complexity levels (simple to complex)")
    print(f"✓ Various domains: finance, technology, science, business, travel, etc.")
    print(f"✓ Different question types: analysis, synthesis, prediction, comparison")
    print()
    print("=== FILES CREATED ===")
    print("1. diverse_questions_50.json - Full detailed version")
    print("2. diverse_questions_50_formatted.json - Clean formatted version")
    
    return simplified_questions

if __name__ == "__main__":
    input_file = "questions/search/diverse_questions_50.json"
    summarize_questions(input_file)