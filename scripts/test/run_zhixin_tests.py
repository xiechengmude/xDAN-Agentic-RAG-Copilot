#!/usr/bin/env python3
"""
运行智信问题测试并观察S3链路
"""
import requests
import json
import time

# 配置信息 - 请根据你的远程服务器修改
REMOTE_API_URL = "http://your-remote-server:8050"  # 🔧 请修改为你的服务器地址
API_KEY = "ragflow-IjJhMGY5YTgwMDNhNzExZWZhZGFkMDI0Mm"

# 精确的智信测试问题
ZHIXIN_QUESTIONS = [
    {
        "id": 1,
        "question": "什么是智信平台？它主要有哪些功能？",
        "expected_keywords": ["智信贷款平台", "奇富借条", "连接用户和机构", "推荐机构"],
        "description": "基础平台介绍问题"
    },
    {
        "id": 2, 
        "question": "在智信平台有哪些类型的机构，他们的模式是怎么样的？",
        "expected_keywords": ["机构绑卡扣款模式", "辅助扣款模式", "绑卡", "扣款"],
        "description": "机构模式分类问题"
    },
    {
        "id": 3,
        "question": "一个用户想在智信平台上借款，需要经过哪些主体流程？",
        "expected_keywords": ["授信路由", "用户申请", "绑定银行卡", "借款申请"],
        "description": "业务流程详解问题"
    }
]

def run_zhixin_tests():
    """运行智信问题测试"""
    print("="*80)
    print("🔍 智信问题 - S3架构完整链路观察测试")
    print("="*80)
    print(f"🌐 远程服务器: {REMOTE_API_URL}")
    print(f"📋 测试问题数: {len(ZHIXIN_QUESTIONS)}")
    print()
    
    print("📖 日志观察指南:")
    print("请在远程服务器上同时运行以下命令来观察实时日志:")
    print()
    print("🔍 方法1 - 查看S3完整链路:")
    print("   tail -f logs/api_server_*.log | grep '\\[S3_TRACE\\]'")
    print()
    print("🔍 方法2 - 查看所有相关日志:")
    print("   tail -f logs/api_server_*.log | grep -E '(S3_TRACE|智能体|Search|Select|Synthesize)'")
    print()
    print("🔍 方法3 - 如果使用systemd:")
    print("   journalctl -u your-api-service -f | grep '\\[S3_TRACE\\]'")
    print("="*80)
    print()
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    # 创建测试对话
    print("🚀 步骤1: 创建智信测试对话...")
    create_chat_url = f"{REMOTE_API_URL}/api/v1/chats"
    create_chat_data = {
        "name": "智信S3链路观察测试",
        "description": "观察S3架构处理智信问题的完整执行链路",
        "dataset_ids": ["7e8d9e924cde11f0afc90242ac140006"],  # 智信知识库
        "llm_config": {
            "model": "deepseek-chat"
        }
    }
    
    try:
        response = requests.post(create_chat_url, json=create_chat_data, headers=headers, timeout=30)
        if response.status_code == 200:
            chat_info = response.json()
            chat_id = chat_info["data"]["id"]
            print(f"✅ 对话创建成功")
            print(f"   📍 Chat ID: {chat_id}")
            print(f"   📚 数据集: {create_chat_data['dataset_ids']}")
            print()
        else:
            print(f"❌ 对话创建失败: {response.status_code}")
            print(f"   📄 响应: {response.text}")
            return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print(f"请检查远程服务器地址: {REMOTE_API_URL}")
        return
    
    # 运行智信问题测试
    print("🎯 步骤2: 运行智信问题测试...")
    print("💡 现在开始观察服务器日志，你将看到完整的S3执行链路！")
    print()
    
    chat_url = f"{REMOTE_API_URL}/api/v1/chats/{chat_id}/completions"
    results = []
    
    for i, question_info in enumerate(ZHIXIN_QUESTIONS, 1):
        print(f"📝 问题 {i}/{len(ZHIXIN_QUESTIONS)}: {question_info['description']}")
        print(f"🎯 问题内容: {question_info['question']}")
        print(f"🔍 期望关键词: {', '.join(question_info['expected_keywords'][:2])}...")
        print("-" * 60)
        
        chat_data = {
            "content": question_info['question'],
            "stream": False
        }
        
        print("⏳ 发送请求中... (请观察服务器日志中的S3链路)")
        print("🔄 日志观察要点:")
        print("   1. [S3_TRACE] Chat completion started")
        print("   2. [S3_TRACE] S3 enhancement conditions met")  
        print("   3. [S3_TRACE] S3-Search阶段：检索问题")
        print("   4. [S3_TRACE] S3-Search成功：找到文档")
        print("   5. 智能体选择重要文档的思考过程")
        print("   6. [S3_TRACE] S3 workflow completed successfully")
        print()
        
        start_time = time.time()
        
        try:
            response = requests.post(chat_url, json=chat_data, headers=headers, timeout=180)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                reference = data.get("reference", {})
                answer = data.get("answer", "")
                
                print(f"✅ 请求完成 ({duration:.1f}秒)")
                print(f"📊 S3架构执行结果:")
                print(f"   🔍 检索文档数: {reference.get('total', 0)}")
                print(f"   🔄 搜索轮次: {reference.get('search_rounds', 0)}")
                print(f"   📋 搜索过程: {len(reference.get('search_process', []))}步")
                
                # 显示搜索过程
                search_process = reference.get("search_process", [])
                if search_process:
                    print(f"   🎯 搜索详情:")
                    for step in search_process:
                        print(f"      • {step}")
                
                # 检查关键词覆盖
                found_keywords = []
                for keyword in question_info['expected_keywords']:
                    if keyword in answer:
                        found_keywords.append(keyword)
                
                # 答案质量评估
                if answer and "抱歉，没有找到相关信息" not in answer:
                    print(f"   ✅ 答案质量: 优秀 ({len(answer)}字符)")
                    print(f"   🎯 关键词覆盖: {len(found_keywords)}/{len(question_info['expected_keywords'])}")
                    if found_keywords:
                        print(f"   ✅ 匹配关键词: {', '.join(found_keywords)}")
                    print(f"   📄 答案预览: {answer[:200]}...")
                else:
                    print(f"   ⚠️  答案质量: 需要改进")
                
                # 记录结果
                results.append({
                    'question_id': question_info['id'],
                    'duration': duration,
                    'documents_found': reference.get('total', 0),
                    'search_rounds': reference.get('search_rounds', 0),
                    'answer_quality': 'good' if found_keywords else 'poor',
                    'keywords_matched': len(found_keywords),
                    'keywords_total': len(question_info['expected_keywords'])
                })
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   📄 错误信息: {response.text}")
        
        except Exception as e:
            print(f"❌ 请求异常: {e}")
        
        print()
        if i < len(ZHIXIN_QUESTIONS):
            print("⏸️  等待5秒后继续下一个问题...")
            time.sleep(5)
    
    # 测试总结
    print("="*80)
    print("📊 智信问题S3链路测试总结")
    print("="*80)
    
    if results:
        successful_tests = len([r for r in results if r['documents_found'] > 0])
        good_answers = len([r for r in results if r['answer_quality'] == 'good'])
        avg_duration = sum(r['duration'] for r in results) / len(results)
        total_docs = sum(r['documents_found'] for r in results)
        total_keywords = sum(r['keywords_matched'] for r in results)
        possible_keywords = sum(r['keywords_total'] for r in results)
        
        print(f"🎯 测试统计:")
        print(f"   ✅ 成功执行: {successful_tests}/{len(ZHIXIN_QUESTIONS)} ({successful_tests/len(ZHIXIN_QUESTIONS)*100:.0f}%)")
        print(f"   🏆 优质答案: {good_answers}/{len(ZHIXIN_QUESTIONS)} ({good_answers/len(ZHIXIN_QUESTIONS)*100:.0f}%)")
        print(f"   ⏱️  平均耗时: {avg_duration:.1f}秒")
        print(f"   📚 总检索文档: {total_docs}个")
        print(f"   🎯 关键词覆盖: {total_keywords}/{possible_keywords} ({total_keywords/possible_keywords*100:.0f}%)")
        
        print(f"\n📋 详细结果:")
        for i, r in enumerate(results, 1):
            quality_icon = "✅" if r['answer_quality'] == 'good' else "⚠️"
            print(f"   问题{i}: {quality_icon} {r['duration']:.1f}s | 文档{r['documents_found']} | 关键词{r['keywords_matched']}/{r['keywords_total']}")
    
    print(f"\n🔍 日志分析建议:")
    print(f"   grep -E '\\[S3_TRACE\\].*智信' logs/api_server_*.log")
    print(f"   grep 'workflow completed successfully' logs/api_server_*.log")
    print(f"   grep 'S3-Search成功' logs/api_server_*.log")
    print("="*80)

if __name__ == "__main__":
    print("🚀 准备运行智信S3链路观察测试")
    print("📝 请先修改脚本中的REMOTE_API_URL为你的实际服务器地址")
    print("🔍 然后在远程服务器上准备好日志查看命令")
    print()
    input("按Enter键开始测试...")
    run_zhixin_tests()