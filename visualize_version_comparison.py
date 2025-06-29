#!/usr/bin/env python3
"""
生成三个版本的可视化对比图表
"""
import json
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

def create_comparison_charts():
    """创建对比图表"""
    
    # 数据准备
    versions = ['原版', '轻量版', '完备版']
    avg_scores = [0.427, 0.846, 0.526]
    avg_times = [19.24, 40.72, 28.51]
    avg_lengths = [268, 2621, 896]
    
    # 创建图表
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('DeepSearch三个版本深度对比分析', fontsize=16, fontweight='bold')
    
    # 1. 质量得分对比
    bars1 = ax1.bar(versions, avg_scores, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
    ax1.set_ylabel('平均得分')
    ax1.set_title('质量得分对比')
    ax1.set_ylim(0, 1.0)
    for i, (bar, score) in enumerate(zip(bars1, avg_scores)):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{score:.1%}', ha='center', va='bottom')
    
    # 2. 响应时间对比
    bars2 = ax2.bar(versions, avg_times, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
    ax2.set_ylabel('平均响应时间（秒）')
    ax2.set_title('响应时间对比')
    for i, (bar, time) in enumerate(zip(bars2, avg_times)):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{time:.1f}s', ha='center', va='bottom')
    
    # 3. 响应长度对比（对数尺度）
    bars3 = ax3.bar(versions, avg_lengths, color=['#ff7f0e', '#2ca02c', '#1f77b4'])
    ax3.set_ylabel('平均响应长度（字符）')
    ax3.set_title('响应长度对比')
    ax3.set_yscale('log')
    for i, (bar, length) in enumerate(zip(bars3, avg_lengths)):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.1, 
                f'{length}', ha='center', va='bottom')
    
    # 4. 综合性能雷达图
    categories = ['质量得分', '时间效率', '内容丰富度', '结构化程度', '用户体验']
    
    # 归一化数据（0-1范围）
    original_scores = [0.427, 0.8, 0.2, 0.1, 0.3]  # 时间效率用反向计算
    lite_scores = [0.846, 0.4, 1.0, 1.0, 0.9]
    complete_scores = [0.526, 0.6, 0.5, 0.7, 0.6]
    
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    ax4.set_theta_offset(np.pi / 2)
    ax4.set_theta_direction(-1)
    
    # 添加每个版本的数据
    for scores, label, color in [(original_scores, '原版', '#ff7f0e'),
                                  (lite_scores, '轻量版', '#2ca02c'),
                                  (complete_scores, '完备版', '#1f77b4')]:
        values = scores + scores[:1]
        ax4.plot(angles, values, 'o-', linewidth=2, label=label, color=color)
        ax4.fill(angles, values, alpha=0.25, color=color)
    
    ax4.set_xticks(angles[:-1])
    ax4.set_xticklabels(categories)
    ax4.set_ylim(0, 1)
    ax4.set_title('综合性能对比')
    ax4.legend(loc='upper right', bbox_to_anchor=(1.1, 1.1))
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('version_comparison_charts.png', dpi=300, bbox_inches='tight')
    print("图表已保存为: version_comparison_charts.png")
    
    # 创建响应结构对比图
    create_response_structure_comparison()

def create_response_structure_comparison():
    """创建响应结构对比图"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 8))
    fig.suptitle('三个版本响应结构对比', fontsize=16, fontweight='bold')
    
    # 原版结构
    ax1 = axes[0]
    ax1.set_title('原版', fontsize=14)
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    
    # 绘制原版结构
    ax1.add_patch(Rectangle((1, 7), 8, 2, facecolor='#ffcccc', edgecolor='black'))
    ax1.text(5, 8, '<search_query>', ha='center', va='center', fontsize=10)
    ax1.add_patch(Rectangle((1, 4.5), 8, 2, facecolor='#ffcccc', edgecolor='black'))
    ax1.text(5, 5.5, '<search_query>', ha='center', va='center', fontsize=10)
    ax1.add_patch(Rectangle((1, 2), 8, 2, facecolor='#ffcccc', edgecolor='black'))
    ax1.text(5, 3, '...', ha='center', va='center', fontsize=10)
    ax1.add_patch(Rectangle((1, 0.5), 8, 1, facecolor='#cccccc', edgecolor='black'))
    ax1.text(5, 1, '<search_complete>', ha='center', va='center', fontsize=9)
    
    # 轻量版结构
    ax2 = axes[1]
    ax2.set_title('轻量版', fontsize=14)
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    
    # 绘制轻量版结构
    ax2.add_patch(Rectangle((1, 8.5), 8, 1.5, facecolor='#ccffcc', edgecolor='black'))
    ax2.text(5, 9.25, '**Search/Select:**', ha='center', va='center', fontsize=10, fontweight='bold')
    ax2.add_patch(Rectangle((1, 6.5), 8, 2, facecolor='#ffffcc', edgecolor='black'))
    ax2.text(5, 7.5, '<thinking>\n[状态分析]\n[URL分析]\n[决策]', ha='center', va='center', fontsize=8)
    ax2.add_patch(Rectangle((1, 5), 8, 1.5, facecolor='#ffcccc', edgecolor='black'))
    ax2.text(5, 5.75, '<important_urls>', ha='center', va='center', fontsize=9)
    ax2.add_patch(Rectangle((1, 3.5), 8, 1.5, facecolor='#ffcccc', edgecolor='black'))
    ax2.text(5, 4.25, '<next_query>', ha='center', va='center', fontsize=9)
    ax2.add_patch(Rectangle((1, 0.5), 8, 3, facecolor='#ccccff', edgecolor='black'))
    ax2.text(5, 2, '**Content Extraction:**\n核心信息\n重要数据\n关键观点\n背景信息', ha='center', va='center', fontsize=8)
    
    # 完备版结构
    ax3 = axes[2]
    ax3.set_title('完备版', fontsize=14)
    ax3.set_xlim(0, 10)
    ax3.set_ylim(0, 10)
    
    # 绘制完备版结构
    ax3.add_patch(Rectangle((1, 8), 8, 1, facecolor='#cccccc', edgecolor='black'))
    ax3.text(5, 8.5, '<search_complete>', ha='center', va='center', fontsize=9)
    ax3.add_patch(Rectangle((1, 6), 8, 2, facecolor='#ffcccc', edgecolor='black'))
    ax3.text(5, 7, '<important_urls>', ha='center', va='center', fontsize=9)
    ax3.add_patch(Rectangle((1, 4.5), 8, 1.5, facecolor='#ffcccc', edgecolor='black'))
    ax3.text(5, 5.25, '<next_query>', ha='center', va='center', fontsize=9)
    ax3.add_patch(Rectangle((1, 1.5), 8, 3, facecolor='#ccccff', edgecolor='black'))
    ax3.text(5, 3, '核心信息\n重要数据\n关键观点', ha='center', va='center', fontsize=8)
    ax3.add_patch(Rectangle((1, 0.2), 8, 1.3, facecolor='#ffffcc', edgecolor='black'))
    ax3.text(5, 0.85, '<thinking>', ha='center', va='center', fontsize=9)
    
    # 移除坐标轴
    for ax in axes:
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
    
    # 添加图例
    legend_elements = [
        mpatches.Patch(color='#ffcccc', label='搜索指令'),
        mpatches.Patch(color='#ffffcc', label='思考过程'),
        mpatches.Patch(color='#ccccff', label='内容提取'),
        mpatches.Patch(color='#cccccc', label='状态标记'),
        mpatches.Patch(color='#ccffcc', label='结构标记')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=5, bbox_to_anchor=(0.5, -0.05))
    
    plt.tight_layout()
    plt.savefig('response_structure_comparison.png', dpi=300, bbox_inches='tight')
    print("响应结构对比图已保存为: response_structure_comparison.png")

if __name__ == "__main__":
    create_comparison_charts()