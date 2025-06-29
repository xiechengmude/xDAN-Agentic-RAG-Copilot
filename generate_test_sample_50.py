#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成50个不同类型的测试问题样本
"""

import json
import random
from datetime import datetime

# 定义不同类型的问题模板
question_templates = {
    "数据分析能力": [
        "作为财务分析师，请分析{company}在近2年的{metric}表现，重点计算{calculation_target}。请同时与行业内Top 3竞争对手的数据进行对比分析。",
        "请对{industry}行业的{metric}进行深度分析，包括历史趋势、影响因素和未来预测。",
        "分析{company}的财务健康状况，重点关注{metric}指标，并提供投资建议。"
    ],
    "文献分析能力": [
        "作为{field}研究员，请对'{topic}'相关研究进行系统性文献综述，包括理论框架、方法论创新和跨文化视角。",
        "请综述{field}领域中关于{topic}的最新研究进展，分析主要理论观点和争议。",
        "对{topic}领域的研究现状进行元分析，总结研究共识和未来方向。"
    ],
    "市场研究能力": [
        "作为{role}，请对{industry}行业的{product}进行全面的市场调研，包括市场规模、竞争分析、消费者洞察和战略建议。",
        "分析{product}在{market}市场的发展机会，提供市场进入策略和营销建议。",
        "对{industry}行业进行深度市场分析，重点关注{aspect}方面的发展趋势。"
    ],
    "技术分析能力": [
        "作为{role}，设计一个{system_type}系统，需要实现{features}功能，使用{tech_stack}技术栈开发。",
        "请设计{product}的技术架构，包括前端、后端、数据库和部署方案。",
        "分析{technology}在{application_domain}领域的应用前景和技术挑战。"
    ],
    "业务分析能力": [
        "分析{company}的商业模式，评估其竞争优势和潜在风险。",
        "对{industry}行业的数字化转型趋势进行分析，提供企业转型建议。",
        "评估{business_model}在{market}市场的可行性和盈利前景。"
    ],
    "政策分析能力": [
        "分析{policy}政策对{industry}行业的影响，评估其实施效果和改进建议。",
        "研究{region}地区的{policy_area}政策框架，分析其优势和不足。",
        "评估{regulation}法规对{sector}的监管效果和合规要求。"
    ],
    "教育培训能力": [
        "设计一套关于{subject}的完整培训课程，包括课程大纲、教学方法和评估体系。",
        "制定{skill}技能的学习路径，提供详细的学习资源和实践项目。",
        "分析{education_field}教育领域的发展趋势和创新方法。"
    ],
    "健康医疗能力": [
        "分析{disease}的预防和治疗方案，提供基于循证医学的建议。",
        "评估{treatment}在{condition}治疗中的效果和安全性。",
        "研究{health_topic}的最新医学进展和临床应用。"
    ]
}

# 定义填充变量的选项
fill_options = {
    "company": ["苹果公司", "微软", "谷歌", "亚马逊", "特斯拉", "Meta", "阿里巴巴", "腾讯", "字节跳动", "小米"],
    "metric": ["毛利率", "净利润率", "ROE", "营收增长率", "市场份额", "用户增长率", "研发投入比"],
    "calculation_target": ["未来两个季度的预测值", "同比增长率", "环比变化趋势", "行业排名变化"],
    "industry": ["人工智能", "新能源汽车", "生物医药", "金融科技", "电子商务", "云计算", "物联网"],
    "field": ["计算机科学", "心理学", "经济学", "管理学", "教育学", "医学", "社会学"],
    "topic": ["人工智能伦理", "数字化转型", "可持续发展", "用户体验", "数据隐私", "创新管理"],
    "role": ["市场分析师", "产品经理", "技术架构师", "业务顾问", "数据科学家", "战略规划师"],
    "product": ["智能手机", "电动汽车", "智能家居", "在线教育平台", "医疗设备", "金融服务"],
    "market": ["中国", "美国", "欧洲", "东南亚", "全球", "新兴市场"],
    "system_type": ["电商平台", "CRM系统", "数据分析平台", "智慧城市", "在线学习", "医疗管理"],
    "features": ["用户管理、数据分析、实时监控", "支付处理、订单管理、库存控制", "数据可视化、报表生成、预警系统"],
    "tech_stack": ["Vue.js和Express", "React和Node.js", "Python和Django", "Java Spring Boot"],
    "technology": ["区块链", "人工智能", "5G", "边缘计算", "量子计算", "AR/VR"],
    "application_domain": ["金融服务", "医疗健康", "智能制造", "智慧城市", "教育培训", "零售电商"],
    "business_model": ["订阅制", "平台模式", "共享经济", "B2B2C", "SaaS", "电商直销"],
    "policy": ["碳中和", "数据安全法", "反垄断", "创新驱动", "数字经济", "绿色发展"],
    "policy_area": ["科技创新", "环境保护", "金融监管", "教育改革", "医疗卫生", "城市规划"],
    "region": ["中国", "欧盟", "美国", "日本", "韩国", "新加坡"],
    "regulation": ["GDPR", "网络安全法", "金融监管", "食品安全", "环保法规", "反垄断法"],
    "sector": ["互联网企业", "金融机构", "制造业", "医疗行业", "教育机构", "能源企业"],
    "subject": ["数据科学", "人工智能", "项目管理", "数字营销", "产品设计", "领导力"],
    "skill": ["Python编程", "数据分析", "产品管理", "用户体验设计", "数字营销", "项目管理"],
    "education_field": ["在线教育", "职业培训", "高等教育", "K12教育", "企业培训", "终身学习"],
    "disease": ["糖尿病", "高血压", "心脏病", "癌症", "阿尔茨海默病", "抑郁症"],
    "treatment": ["免疫疗法", "基因治疗", "精准医疗", "远程医疗", "AI辅助诊断", "个性化治疗"],
    "condition": ["慢性病管理", "急性病治疗", "预防保健", "康复治疗", "心理健康", "老年护理"],
    "health_topic": ["精准医疗", "数字健康", "远程医疗", "AI医疗", "基因治疗", "再生医学"],
    "aspect": ["技术创新", "商业模式", "用户体验", "市场竞争", "监管政策", "投资趋势"]
}

def generate_question(category, template, question_id):
    """生成单个问题"""
    # 随机填充模板变量
    filled_template = template
    for key, options in fill_options.items():
        if f"{{{key}}}" in filled_template:
            filled_template = filled_template.replace(f"{{{key}}}", random.choice(options))
    
    # 生成评估维度
    evaluation_dimensions = generate_evaluation_dimensions(category)
    
    question = {
        "id": f"{category.lower().replace('：', '_').replace(' ', '_')}_{random.randint(1000000000, 9999999999)}_{question_id}",
        "category": category,
        "question": filled_template,
        "target": f"测试搜索智能体在{category}方面的综合能力，包括信息检索、数据分析、逻辑推理和结果呈现等多个维度。",
        "verify": {
            "scoring_guide": "每个维度按1-5分评分，1分为不满足要求，3分为基本满足要求，5分为卓越表现。总分为各维度得分的平均值。",
            "evaluation_dimensions": evaluation_dimensions
        }
    }
    
    return question

def generate_evaluation_dimensions(category):
    """根据类别生成评估维度"""
    base_dimensions = {
        "信息检索能力": {
            "description": "评估是否能够准确检索到相关的高质量信息源，包括数据的完整性、准确性和权威性。",
            "scoring_criteria": {
                "1分": "未能检索到相关信息，或信息严重不准确",
                "2分": "检索到部分相关信息，但质量不高或来源不可靠",
                "3分": "检索到基本相关的信息，来源较为可靠",
                "4分": "检索到高质量的相关信息，来源权威可靠",
                "5分": "检索到全面且高质量的信息，来源多样且权威"
            }
        },
        "分析深度": {
            "description": "评估分析的深度和质量，包括逻辑推理、因果关系分析和洞察发现。",
            "scoring_criteria": {
                "1分": "分析极其肤浅，缺乏逻辑性",
                "2分": "分析较为表面，逻辑不够清晰",
                "3分": "分析有一定深度，逻辑基本清晰",
                "4分": "分析深入，逻辑清晰，有一定洞察",
                "5分": "分析非常深入，逻辑严密，洞察独到"
            }
        },
        "结果呈现": {
            "description": "评估结果的呈现质量，包括结构清晰度、可读性和可视化效果。",
            "scoring_criteria": {
                "1分": "结果呈现混乱，难以理解",
                "2分": "结果呈现基本可读，但结构不够清晰",
                "3分": "结果呈现清晰，结构合理",
                "4分": "结果呈现专业，结构清晰，易于理解",
                "5分": "结果呈现卓越，结构完美，具有很强的可读性和说服力"
            }
        }
    }
    
    # 根据不同类别添加特定维度
    if "数据分析" in category:
        base_dimensions["数据处理能力"] = {
            "description": "评估数据处理和计算的准确性，包括统计方法的选择和应用。",
            "scoring_criteria": {
                "1分": "数据处理有严重错误",
                "2分": "数据处理有明显错误",
                "3分": "数据处理基本正确",
                "4分": "数据处理准确专业",
                "5分": "数据处理非常精确，方法选择最优"
            }
        }
    
    if "技术" in category:
        base_dimensions["技术可行性"] = {
            "description": "评估技术方案的可行性和创新性。",
            "scoring_criteria": {
                "1分": "技术方案不可行或存在重大缺陷",
                "2分": "技术方案基本可行但有明显不足",
                "3分": "技术方案可行，设计合理",
                "4分": "技术方案优秀，具有创新性",
                "5分": "技术方案卓越，极具创新性和实用性"
            }
        }
    
    return base_dimensions

def main():
    """主函数"""
    questions = []
    question_id = 1
    
    # 为每个类别生成问题
    questions_per_category = 50 // len(question_templates)
    remaining_questions = 50 % len(question_templates)
    
    for category, templates in question_templates.items():
        # 每个类别生成基础数量的问题
        for i in range(questions_per_category):
            template = random.choice(templates)
            question = generate_question(category, template, question_id)
            questions.append(question)
            question_id += 1
        
        # 为前几个类别生成额外问题
        if remaining_questions > 0:
            template = random.choice(templates)
            question = generate_question(category, template, question_id)
            questions.append(question)
            question_id += 1
            remaining_questions -= 1
    
    # 保存到文件
    output_file = "questions/search/test_sample_50.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"已生成50个测试问题，保存到: {output_file}")
    print(f"问题类别分布:")
    category_count = {}
    for q in questions:
        category = q['category']
        category_count[category] = category_count.get(category, 0) + 1
    
    for category, count in category_count.items():
        print(f"  {category}: {count}个问题")

if __name__ == "__main__":
    main() 