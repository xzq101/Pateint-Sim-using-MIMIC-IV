"""
Generate Table 3: Dialogue-Level Factuality Evaluation
从dialogue-level evaluation results中提取Information Coverage和Information Consistency指标
"""

import json
import os
from typing import Dict, List, Tuple


def load_dialogue_evaluation_results(json_file: str) -> List[Dict]:
    """
    加载dialogue-level评估结果JSON文件
    """
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found!")
        print("Please run dialogue-level evaluation first:")
        print("  python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json")
        return []
    
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    return results


def categorize_profile_item(key: str) -> str:
    """
    将profile项分类为三个类别：Social History, PMH, Current Visit
    
    Args:
        key: Profile项的键名
    
    Returns:
        类别名称
    """
    social_fields = [
        'age', 'gender', 'race', 'occupation', 'marital_status', 
        'living_situation', 'tobacco', 'alcohol', 'illicit_drug',
        'exercise', 'sexual_history', 'children'
    ]
    
    pmh_fields = [
        'medical_history', 'medication', 'allergies',
        'family_medical_history', 'medical_device'
    ]
    
    current_visit_fields = [
        'chief_complaint', 'diagnosis', 'present_illness',
        'pain', 'present_illness_positive', 'present_illness_negative'
    ]
    
    key_lower = key.lower()
    
    if key_lower in social_fields:
        return 'Social'
    elif key_lower in pmh_fields:
        return 'PMH'
    elif key_lower in current_visit_fields:
        return 'CurrentVisit'
    else:
        # 默认归类
        if 'history' in key_lower or 'medication' in key_lower or 'allerg' in key_lower:
            return 'PMH'
        elif 'complaint' in key_lower or 'diagnosis' in key_lower or 'illness' in key_lower:
            return 'CurrentVisit'
        else:
            return 'Social'


def calculate_table3_metrics(results: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    计算Table 3的所有指标
    
    返回指标：
    - Information Coverage (ICov) (%): 被提取到的信息项百分比
    - Information Consistency (ICon) (4-point): 信息一致性评分
    
    按三个类别统计：Social, PMH, CurrentVisit
    """
    # 统计每个类别的数据
    category_stats = {
        'Social': {'total_items': 0, 'extracted_items': 0, 'consistency_scores': []},
        'PMH': {'total_items': 0, 'extracted_items': 0, 'consistency_scores': []},
        'CurrentVisit': {'total_items': 0, 'extracted_items': 0, 'consistency_scores': []}
    }
    
    for conv in results:
        gt_profile = conv.get('ground_truth_profile', {})
        extracted_profile = conv.get('extracted_profile', {})
        consistency_eval = conv.get('consistency_evaluation', {})
        
        # 遍历ground truth profile中的所有项
        for key, value in gt_profile.items():
            # 跳过嵌套的full_record字典
            if key == 'full_record' or isinstance(value, dict):
                continue
            
            # 分类
            category = categorize_profile_item(key)
            
            # 统计total items
            category_stats[category]['total_items'] += 1
            
            # 检查是否被提取到（extracted_profile中有这个key且值不为空）
            extracted_value = extracted_profile.get(key)
            if extracted_value and str(extracted_value).strip() and str(extracted_value).lower() not in ['none', 'null', 'n/a', 'unknown', 'not specified']:
                category_stats[category]['extracted_items'] += 1
            
            # 获取consistency score
            if key in consistency_eval:
                item_eval = consistency_eval[key]
                
                # 根据evaluation mode获取score
                if 'extraction_score' in item_eval and 'roleplay_score' in item_eval:
                    # Persona-aware mode: 使用extraction_score作为coverage指标
                    # 使用roleplay_score作为consistency指标（因为它评估的是一致性）
                    score = item_eval.get('roleplay_score', 0)
                elif 'score' in item_eval:
                    # Simple consistency mode
                    score = item_eval.get('score', 0)
                else:
                    score = 0
                
                if score > 0:
                    category_stats[category]['consistency_scores'].append(score)
    
    # 计算每个类别的指标
    metrics = {}
    
    for category in ['Social', 'PMH', 'CurrentVisit']:
        stats = category_stats[category]
        
        # Information Coverage (%)
        if stats['total_items'] > 0:
            coverage = stats['extracted_items'] / stats['total_items']
        else:
            coverage = 0
        
        # Information Consistency (4-point scale)
        if stats['consistency_scores']:
            consistency = sum(stats['consistency_scores']) / len(stats['consistency_scores'])
        else:
            consistency = 0
        
        metrics[category] = {
            'ICov': coverage,
            'ICon': consistency,
            '_debug': {
                'total_items': stats['total_items'],
                'extracted_items': stats['extracted_items'],
                'consistency_scores_count': len(stats['consistency_scores'])
            }
        }
    
    # 计算平均值
    avg_icov = (metrics['Social']['ICov'] + metrics['PMH']['ICov'] + metrics['CurrentVisit']['ICov']) / 3
    avg_icon = (metrics['Social']['ICon'] + metrics['PMH']['ICon'] + metrics['CurrentVisit']['ICon']) / 3
    
    metrics['Average'] = {
        'ICov': avg_icov,
        'ICon': avg_icon
    }
    
    return metrics


def print_table3(engine_name: str, metrics: Dict[str, Dict[str, float]]):
    """
    打印 Table 3 格式的结果
    """
    print("\n" + "="*120)
    print("Table 3: Dialogue-Level Factuality Evaluation")
    print("Information Coverage (ICov) measures percentage of information extracted from dialogues.")
    print("Information Consistency (ICon) evaluates consistency between extracted and ground truth profiles.")
    print("Categories: Social History (Social), Previous Medical History (PMH), Current Visit Information (CurrentVisit)")
    print("="*120)
    print()
    
    # Header
    print(f"{'Engine':<25} {'Information Coverage (ICov) (%)':<50} {'Information Consistency (ICon) (4-point)':<50}")
    print(f"{'':<25} {'-'*50} {'-'*50}")
    print(f"{'':<25} {'Social':<12} {'PMH':<12} {'CurrentVisit':<14} {'Avg.':<12} {'Social':<12} {'PMH':<12} {'CurrentVisit':<14} {'Avg.':<12}")
    print("-"*120)
    
    # Data row
    row = f"{engine_name:<25}"
    
    # ICov columns
    row += f" {metrics['Social']['ICov']:<11.2f}"
    row += f" {metrics['PMH']['ICov']:<11.2f}"
    row += f" {metrics['CurrentVisit']['ICov']:<13.2f}"
    row += f" {metrics['Average']['ICov']:<11.2f}"
    
    # ICon columns
    row += f" {metrics['Social']['ICon']:<11.2f}"
    row += f" {metrics['PMH']['ICon']:<11.2f}"
    row += f" {metrics['CurrentVisit']['ICon']:<13.2f}"
    row += f" {metrics['Average']['ICon']:<11.2f}"
    
    print(row)
    print("="*120)
    print()
    
    # Print debug info
    print("Statistics by Category:")
    for category in ['Social', 'PMH', 'CurrentVisit']:
        if '_debug' in metrics[category]:
            debug = metrics[category]['_debug']
            print(f"\n{category}:")
            print(f"  Total items in ground truth: {debug['total_items']}")
            print(f"  Extracted items: {debug['extracted_items']}")
            print(f"  Coverage: {metrics[category]['ICov']:.2%}")
            print(f"  Consistency scores count: {debug['consistency_scores_count']}")
            print(f"  Average consistency: {metrics[category]['ICon']:.2f}/4.0")
    print()


def print_markdown_table3(engine_name: str, metrics: Dict[str, Dict[str, float]]):
    """
    打印 Markdown 格式的 Table 3
    """
    print("\n## Table 3: Dialogue-Level Factuality Evaluation")
    print()
    print("| Engine | **Information Coverage (ICov) (%)** ||| | **Information Consistency (ICon) (4-point)** ||| |")
    print("|--------|---------|---------|---------------|---------|---------|---------|---------------|---------|")
    print("|        | Social  | PMH     | CurrentVisit  | Avg.    | Social  | PMH     | CurrentVisit  | Avg.    |")
    
    row = f"| {engine_name}"
    row += f" | {metrics['Social']['ICov']:.2f}"
    row += f" | {metrics['PMH']['ICov']:.2f}"
    row += f" | {metrics['CurrentVisit']['ICov']:.2f}"
    row += f" | {metrics['Average']['ICov']:.2f}"
    row += f" | {metrics['Social']['ICon']:.2f}"
    row += f" | {metrics['PMH']['ICon']:.2f}"
    row += f" | {metrics['CurrentVisit']['ICon']:.2f}"
    row += f" | {metrics['Average']['ICon']:.2f} |"
    print(row)
    print()


def save_table3(engine_name: str, metrics: Dict[str, Dict[str, float]]):
    """
    保存 Table 3 到文件
    """
    # Save text format
    with open("table3_dialogue_factuality.txt", 'w', encoding='utf-8') as f:
        import sys
        old_stdout = sys.stdout
        sys.stdout = f
        print_table3(engine_name, metrics)
        sys.stdout = old_stdout
    
    # Save markdown format
    with open("table3_dialogue_factuality.md", 'w', encoding='utf-8') as f:
        old_stdout = sys.stdout
        sys.stdout = f
        print_markdown_table3(engine_name, metrics)
        sys.stdout = old_stdout
    
    print("✅ Text format saved to: table3_dialogue_factuality.txt")
    print("✅ Markdown format saved to: table3_dialogue_factuality.md")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Table 3: Dialogue-Level Factuality Evaluation")
    parser.add_argument(
        "--input",
        type=str,
        default="dialogue_evaluation_results.json",
        help="Input dialogue-level evaluation results JSON file"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="deepseek-r1:8b",
        help="LLM engine name"
    )
    
    args = parser.parse_args()
    
    print("\n🎯 Table 3 Generator: Dialogue-Level Factuality Evaluation")
    print(f"📁 Reading from: {args.input}")
    print(f"🤖 Engine: {args.engine}")
    
    # Load results
    results = load_dialogue_evaluation_results(args.input)
    
    if not results:
        print("\n⚠️  No results found. To generate dialogue-level evaluation:")
        print("\n📝 Step 1: Run dialogue-level evaluation on all conversations:")
        print("   python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json")
        print("\n📝 Step 2: Generate Table 3:")
        print("   python generate_table3.py --input dialogue_evaluation_results.json --engine \"deepseek-r1:8b\"")
        return
    
    print(f"✅ Loaded {len(results)} conversation evaluations")
    
    # Calculate metrics
    metrics = calculate_table3_metrics(results)
    
    print("\nCalculated metrics:")
    for category in ['Social', 'PMH', 'CurrentVisit', 'Average']:
        print(f"  {category}:")
        print(f"    ICov: {metrics[category]['ICov']:.2%}")
        print(f"    ICon: {metrics[category]['ICon']:.2f}/4.0")
    
    # Print tables
    print_table3(args.engine, metrics)
    print_markdown_table3(args.engine, metrics)
    
    # Save to files
    save_table3(args.engine, metrics)


if __name__ == "__main__":
    main()
