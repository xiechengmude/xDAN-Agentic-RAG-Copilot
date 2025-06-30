#!/usr/bin/env python3
"""
模式配置管理器
负责加载和管理deepsearch_modes.yaml中的丰富配置组合
对外暴露简化的flash/deep两种模式
"""

import os
import yaml
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ModeConfigManager:
    """DeepSearch模式配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，None时使用默认路径
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        
    def _find_config_file(self) -> str:
        """查找配置文件"""
        search_paths = [
            Path.cwd() / "config" / "deepsearch_modes.yaml",
            Path.cwd() / "deepsearch_modes.yaml", 
            Path(__file__).parent.parent.parent / "config" / "deepsearch_modes.yaml",
            Path.home() / ".deepsearch" / "deepsearch_modes.yaml"
        ]
        
        for path in search_paths:
            if path.exists():
                logger.info(f"找到模式配置文件: {path}")
                return str(path)
                
        logger.warning("未找到deepsearch_modes.yaml，使用默认配置")
        return None
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_path:
            return self._get_default_config()
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("模式配置加载成功")
            return config
        except Exception as e:
            logger.error(f"加载模式配置失败: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "api_modes": {
                "flash": {
                    "name": "Flash模式",
                    "description": "快速高效，30-60秒响应",
                    "internal_scenarios": ["quick_facts"]
                },
                "deep": {
                    "name": "Deep模式",
                    "description": "深度全面，2-5分钟分析", 
                    "internal_scenarios": ["academic_research"]
                }
            },
            "internal_scenarios": {
                "quick_facts": {
                    "name": "快速事实查询",
                    "max_rounds": 2,
                    "concurrent_strategy": "flash",
                    "max_parallel": 3,
                    "target_response_time": 45
                },
                "academic_research": {
                    "name": "学术研究分析",
                    "max_rounds": 8,
                    "concurrent_strategy": "smart",
                    "max_parallel": 2,
                    "target_response_time": 200
                }
            }
        }
    
    def get_api_modes(self) -> List[str]:
        """获取对外API支持的模式列表"""
        return list(self.config.get("api_modes", {}).keys())
    
    def get_mode_info(self, mode: str) -> Dict[str, Any]:
        """获取模式基本信息"""
        api_modes = self.config.get("api_modes", {})
        if mode not in api_modes:
            raise ValueError(f"不支持的模式: {mode}. 支持的模式: {list(api_modes.keys())}")
        return api_modes[mode]
    
    def select_internal_scenario(self, mode: str, question: str, 
                                context: Optional[Dict] = None) -> str:
        """
        智能选择内部场景
        
        Args:
            mode: API模式 (flash/deep)
            question: 用户问题
            context: 额外上下文信息
            
        Returns:
            选择的内部场景名称
        """
        mode_info = self.get_mode_info(mode)
        available_scenarios = mode_info.get("internal_scenarios", [])
        
        # 如果只有一个场景，直接返回
        if len(available_scenarios) == 1:
            return available_scenarios[0]
            
        # 智能选择逻辑
        selected_scenario = self._intelligent_scenario_selection(
            mode, question, available_scenarios, context
        )
        
        logger.info(f"为问题 '{question[:50]}...' 选择内部场景: {selected_scenario}")
        return selected_scenario
    
    def _intelligent_scenario_selection(self, mode: str, question: str, 
                                      available_scenarios: List[str],
                                      context: Optional[Dict] = None) -> str:
        """智能场景选择算法"""
        selection_rules = self.config.get("scenario_selection", {}).get(mode, {})
        
        question_lower = question.lower()
        question_length = len(question)
        
        # 计算每个场景的匹配分数
        scenario_scores = {}
        
        for scenario in available_scenarios:
            if scenario not in selection_rules:
                scenario_scores[scenario] = 0
                continue
                
            rules = selection_rules[scenario]
            score = 0
            
            # 关键词匹配
            keywords = rules.get("keywords", [])
            keyword_matches = sum(1 for kw in keywords if kw in question_lower)
            score += keyword_matches * 10
            
            # 问题长度匹配
            length_range = rules.get("question_length", [0, 1000])
            if length_range[0] <= question_length <= length_range[1]:
                score += 5
                
            # 时间敏感性检查
            if rules.get("time_sensitive", False):
                time_words = ["最新", "今天", "刚刚", "现在", "当前"]
                if any(word in question for word in time_words):
                    score += 15
                    
            # 产品名称检查
            if rules.get("has_product_names", False):
                # 简单的产品名称检测（可以扩展为更复杂的NER）
                product_indicators = ["vs", "对比", "比较", "iPhone", "Tesla", "比亚迪"]
                if any(indicator in question for indicator in product_indicators):
                    score += 10
                    
            # 公司名称检查
            if rules.get("has_company_names", False):
                company_indicators = ["公司", "股份", "集团", "Corp", "Inc", "Ltd"]
                if any(indicator in question for indicator in company_indicators):
                    score += 10
                    
            # 政府相关检查
            if rules.get("involves_government", False):
                gov_indicators = ["政府", "国家", "部门", "监管", "官方"]
                if any(indicator in question for indicator in gov_indicators):
                    score += 15
                    
            scenario_scores[scenario] = score
        
        # 选择得分最高的场景
        best_scenario = max(scenario_scores.items(), key=lambda x: x[1])[0]
        
        # 如果所有场景得分都为0，返回第一个默认场景
        if scenario_scores[best_scenario] == 0:
            return available_scenarios[0]
            
        return best_scenario
    
    def get_scenario_config(self, scenario_name: str) -> Dict[str, Any]:
        """获取内部场景的详细配置"""
        scenarios = self.config.get("internal_scenarios", {})
        if scenario_name not in scenarios:
            raise ValueError(f"未知的内部场景: {scenario_name}")
        return scenarios[scenario_name]
    
    def get_execution_config(self, mode: str, question: str, 
                           context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        获取完整的执行配置
        
        Args:
            mode: API模式
            question: 用户问题  
            context: 额外上下文
            
        Returns:
            执行配置字典
        """
        # 1. 选择内部场景
        scenario = self.select_internal_scenario(mode, question, context)
        
        # 2. 获取场景配置
        scenario_config = self.get_scenario_config(scenario)
        
        # 3. 合并其他相关配置
        execution_config = {
            "api_mode": mode,
            "internal_scenario": scenario,
            "scenario_name": scenario_config.get("name", scenario),
            **scenario_config
        }
        
        # 4. 添加并发策略详情
        concurrent_strategy = scenario_config.get("concurrent_strategy")
        if concurrent_strategy:
            strategies = self.config.get("concurrent_strategies", {})
            if concurrent_strategy in strategies:
                execution_config["concurrent_details"] = strategies[concurrent_strategy]
        
        # 5. 添加子查询方法详情
        subquery_method = scenario_config.get("subquery_method")
        if subquery_method:
            methods = self.config.get("subquery_methods", {})
            if subquery_method in methods:
                execution_config["subquery_details"] = methods[subquery_method]
        
        # 6. 添加质量控制配置
        quality_config = self.config.get("quality_control", {})
        global_quality = quality_config.get("global", {})
        scenario_quality = quality_config.get("by_scenario", {}).get(scenario, {})
        execution_config["quality_control"] = {**global_quality, **scenario_quality}
        
        logger.info(f"生成执行配置: {mode} -> {scenario} -> {scenario_config.get('name')}")
        return execution_config
    
    def get_performance_targets(self, mode: str) -> Dict[str, Any]:
        """获取性能目标"""
        monitoring = self.config.get("performance_monitoring", {})
        targets = monitoring.get("target_metrics", {})
        return targets.get(mode, {})
    
    def should_optimize(self, mode: str, current_metrics: Dict[str, float]) -> List[str]:
        """
        检查是否需要优化
        
        Args:
            mode: 当前模式
            current_metrics: 当前性能指标
            
        Returns:
            需要执行的优化动作列表
        """
        optimization_actions = []
        targets = self.get_performance_targets(mode)
        optimization_rules = self.config.get("performance_monitoring", {}).get("optimization_triggers", {})
        
        # 检查响应时间
        if "response_time" in current_metrics and "response_time" in targets:
            target_time = targets["response_time"]
            current_time = current_metrics["response_time"]
            threshold = optimization_rules.get("response_time_exceeded", {}).get("threshold", 1.5)
            
            if current_time > target_time * threshold:
                action = optimization_rules.get("response_time_exceeded", {}).get("action")
                if action:
                    optimization_actions.append(action)
        
        # 检查成功率
        if "success_rate" in current_metrics and "success_rate" in targets:
            target_rate = targets["success_rate"]
            current_rate = current_metrics["success_rate"]
            threshold = optimization_rules.get("low_success_rate", {}).get("threshold", 0.8)
            
            if current_rate < threshold:
                action = optimization_rules.get("low_success_rate", {}).get("action")
                if action:
                    optimization_actions.append(action)
        
        return optimization_actions
    
    def reload_config(self):
        """重新加载配置"""
        logger.info("重新加载模式配置...")
        self.config = self._load_config()
    
    def validate_config(self) -> List[str]:
        """验证配置完整性"""
        errors = []
        
        # 检查API模式配置
        api_modes = self.config.get("api_modes", {})
        if not api_modes:
            errors.append("缺少api_modes配置")
            
        # 检查内部场景配置
        internal_scenarios = self.config.get("internal_scenarios", {})
        if not internal_scenarios:
            errors.append("缺少internal_scenarios配置")
            
        # 检查API模式引用的场景是否存在
        for mode, mode_config in api_modes.items():
            scenarios = mode_config.get("internal_scenarios", [])
            for scenario in scenarios:
                if scenario not in internal_scenarios:
                    errors.append(f"API模式 {mode} 引用了不存在的场景: {scenario}")
        
        return errors


# 全局配置管理器实例
mode_config_manager = ModeConfigManager()