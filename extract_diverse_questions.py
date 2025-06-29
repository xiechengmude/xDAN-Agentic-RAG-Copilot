#!/usr/bin/env python3
"""
Script to extract 50 diverse questions from generated_questions_1000.json
"""

import json
import random
from collections import defaultdict

def extract_diverse_questions(input_file, output_file, target_count=50):
    """
    Extract diverse questions covering different categories, complexity levels, and domains
    """
    
    # Read the full JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
    
    print(f"Total questions loaded: {len(all_questions)}")
    
    # Group questions by category
    categories = defaultdict(list)
    for question in all_questions:
        categories[question['category']].append(question)
    
    print(f"Categories found: {len(categories)}")
    for category, questions in categories.items():
        print(f"  - {category}: {len(questions)} questions")
    
    # Extract diverse questions
    selected_questions = []
    
    # Calculate how many questions to take from each category for balance
    category_names = list(categories.keys())
    questions_per_category = target_count // len(category_names)
    remaining_questions = target_count % len(category_names)
    
    print(f"\nTarget extraction strategy:")
    print(f"Questions per category: {questions_per_category}")
    print(f"Remaining questions to distribute: {remaining_questions}")
    
    # Select questions from each category
    for i, category in enumerate(category_names):
        # Determine how many questions to take from this category
        questions_to_take = questions_per_category
        if i < remaining_questions:
            questions_to_take += 1
            
        # Get questions from this category
        category_questions = categories[category]
        
        # Sample questions to ensure diversity within category
        if len(category_questions) <= questions_to_take:
            # Take all questions if category has fewer than needed
            selected_from_category = category_questions
        else:
            # Sample evenly distributed questions from the category
            # This ensures we get questions from different parts of the category
            step = len(category_questions) // questions_to_take
            selected_from_category = []
            for j in range(questions_to_take):
                index = (j * step) % len(category_questions)
                selected_from_category.append(category_questions[index])
        
        selected_questions.extend(selected_from_category)
        print(f"Selected {len(selected_from_category)} questions from '{category}'")
    
    # Shuffle the final selection to mix categories
    random.shuffle(selected_questions)
    
    # Ensure we have exactly the target count
    selected_questions = selected_questions[:target_count]
    
    print(f"\nFinal selection: {len(selected_questions)} questions")
    
    # Analyze the diversity of selected questions
    selected_categories = defaultdict(int)
    complexity_indicators = defaultdict(int)
    question_types = defaultdict(int)
    
    for question in selected_questions:
        selected_categories[question['category']] += 1
        
        # Analyze complexity based on question length and keywords
        q_text = question['question'].lower()
        if any(word in q_text for word in ['详细', '全面', '系统性', '综合', '深入', '复杂', '多维度']):
            complexity_indicators['complex'] += 1
        elif any(word in q_text for word in ['分析', '比较', '评估', '研究']):
            complexity_indicators['medium'] += 1
        else:
            complexity_indicators['simple'] += 1
            
        # Analyze question types based on keywords
        if any(word in q_text for word in ['文献综述', '综述', '研究现状']):
            question_types['literature_review'] += 1
        elif any(word in q_text for word in ['数据分析', '财报', '计算', '预测']):
            question_types['data_analysis'] += 1
        elif any(word in q_text for word in ['市场调研', '市场分析', '竞争对手']):
            question_types['market_research'] += 1
        elif any(word in q_text for word in ['设计', '规划', '方案']):
            question_types['design_planning'] += 1
        elif any(word in q_text for word in ['编程', '代码', '算法']):
            question_types['programming'] += 1
        else:
            question_types['search_retrieval'] += 1
    
    print("\nDiversity Analysis:")
    print("Categories distribution:")
    for category, count in selected_categories.items():
        print(f"  - {category}: {count}")
    
    print("\nComplexity distribution:")
    for complexity, count in complexity_indicators.items():
        print(f"  - {complexity}: {count}")
        
    print("\nQuestion types distribution:")
    for q_type, count in question_types.items():
        print(f"  - {q_type}: {count}")
    
    # Save the selected questions
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_questions, f, ensure_ascii=False, indent=2)
    
    print(f"\nSelected questions saved to: {output_file}")
    
    return selected_questions

if __name__ == "__main__":
    input_file = "questions/search/generated_questions_1000.json"
    output_file = "questions/search/diverse_questions_50.json"
    
    # Set random seed for reproducible results
    random.seed(42)
    
    selected_questions = extract_diverse_questions(input_file, output_file, 50)
    
    print("\nExtraction completed successfully!")
    print(f"Selected {len(selected_questions)} diverse questions covering:")
    print("- Different categories (literature review, data analysis, market research, etc.)")
    print("- Different complexity levels (simple, medium, complex)")
    print("- Different domains (finance, technology, science, business, etc.)")
    print("- Different question types (analysis, comparison, prediction, synthesis, etc.)")