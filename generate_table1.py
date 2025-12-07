"""
Generate Table 1: Persona Fidelity Evaluation
从evaluation results中提取5个维度的平均分：Personality, Language, Recall, Confused, Realism
"""

import json
import os
from typing import Dict, List


def load_evaluation_results(json_file: str) -> List[Dict]:
    """
    加载评估结果JSON文件
    """
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found!")
        print("Please run evaluation first:")
        print("  python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json")
        return []
    
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    return results


def extract_scores(results: List[Dict]) -> Dict[str, List[float]]:
    """
    从评估结果中提取5个维度的分数
    
    Returns:
        Dict mapping criterion name to list of scores
    """
    scores = {
        'Personality': [],
        'Language': [],
        'Recall': [],
        'Confused': [],
        'Realism': []
    }
    
    for result in results:
        evaluations = result.get('evaluations', {})
        
        # Extract scores for each criterion (filter out None values)
        if 'Personality' in evaluations:
            score = evaluations['Personality'].get('score')
            if score is not None:
                scores['Personality'].append(score)
        
        if 'Language_Proficiency' in evaluations:
            score = evaluations['Language_Proficiency'].get('score')
            if score is not None:
                scores['Language'].append(score)
        
        if 'Recall_Consistency' in evaluations:
            score = evaluations['Recall_Consistency'].get('score')
            if score is not None:
                scores['Recall'].append(score)
        
        if 'Confusion_Consistency' in evaluations:
            score = evaluations['Confusion_Consistency'].get('score')
            if score is not None:
                scores['Confused'].append(score)
        
        if 'Clinical_Realism' in evaluations:
            score = evaluations['Clinical_Realism'].get('score')
            if score is not None:
                scores['Realism'].append(score)
    
    return scores


def calculate_averages(scores: Dict[str, List[float]]) -> Dict[str, float]:
    """
    计算每个维度的平均分（过滤None值）
    """
    averages = {}
    
    for criterion, score_list in scores.items():
        # Filter out None values
        valid_scores = [s for s in score_list if s is not None]
        
        if valid_scores:
            avg = sum(valid_scores) / len(valid_scores)
            averages[criterion] = round(avg, 2)
        else:
            averages[criterion] = 0.0
    
    # Calculate overall average (only from non-zero values)
    valid_averages = [v for v in averages.values() if v > 0]
    if valid_averages:
        overall_avg = sum(valid_averages) / len(valid_averages)
        averages['Avg.'] = round(overall_avg, 2)
    else:
        averages['Avg.'] = 0.0
    
    return averages


def print_table1(engine_name: str, averages: Dict[str, float], num_conversations: int):
    """
    打印 Table 1 格式的结果
    """
    print("\n" + "="*100)
    print("Table 1: Persona Fidelity Evaluation of Various LLMs Across Five Criteria")
    print("Each criterion is rated on a 4-point scale (0-4).")
    print("The average score (Avg.) summarizes overall performance.")
    print("="*100)
    print()
    
    # Header
    header = f"{'Engine':<35} {'Personality':>12} {'Language':>12} {'Recall':>12} {'Confused':>12} {'Realism':>12} {'Avg.':>12}"
    print(header)
    print("-"*100)
    
    # Data row
    row = f"{engine_name:<35}"
    row += f" {averages['Personality']:>11.2f}"
    row += f" {averages['Language']:>11.2f}"
    row += f" {averages['Recall']:>11.2f}"
    row += f" {averages['Confused']:>11.2f}"
    row += f" {averages['Realism']:>11.2f}"
    row += f" {averages['Avg.']:>11.2f}"
    print(row)
    
    print("="*100)
    print()
    print(f"Number of conversations evaluated: {num_conversations}")
    print()


def print_markdown_table(engine_name: str, averages: Dict[str, float], num_conversations: int):
    """
    打印 Markdown 格式的表格
    """
    print("\n## Table 1: Persona Fidelity Evaluation")
    print()
    print(f"Evaluated on {num_conversations} conversations. Each criterion is rated on a 4-point scale (0-4).")
    print()
    print("| Engine | Personality | Language | Recall | Confused | Realism | Avg. |")
    print("|--------|-------------|----------|--------|----------|---------|------|")
    
    row = f"| {engine_name}"
    row += f" | {averages['Personality']:.2f}"
    row += f" | {averages['Language']:.2f}"
    row += f" | {averages['Recall']:.2f}"
    row += f" | {averages['Confused']:.2f}"
    row += f" | {averages['Realism']:.2f}"
    row += f" | {averages['Avg.']:.2f} |"
    print(row)
    print()


def save_to_files(engine_name: str, averages: Dict[str, float], num_conversations: int):
    """
    保存表格到文件
    """
    # Save text format
    with open("table1_persona_fidelity.txt", 'w', encoding='utf-8') as f:
        import sys
        old_stdout = sys.stdout
        sys.stdout = f
        print_table1(engine_name, averages, num_conversations)
        sys.stdout = old_stdout
    
    # Save markdown format
    with open("table1_persona_fidelity.md", 'w', encoding='utf-8') as f:
        old_stdout = sys.stdout
        sys.stdout = f
        print_markdown_table(engine_name, averages, num_conversations)
        sys.stdout = old_stdout
    
    print("✅ Text format saved to: table1_persona_fidelity.txt")
    print("✅ Markdown format saved to: table1_persona_fidelity.md")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Table 1: Persona Fidelity Evaluation")
    parser.add_argument(
        "--input",
        type=str,
        default="evaluation_results.json",
        help="Input evaluation results JSON file"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="deepseek-r1:8b",
        help="LLM engine name"
    )
    
    args = parser.parse_args()
    
    print("\n🎯 Table 1 Generator: Persona Fidelity Evaluation")
    print(f"📁 Reading from: {args.input}")
    print(f"🤖 Engine: {args.engine}")
    
    # Load results
    results = load_evaluation_results(args.input)
    
    if not results:
        return
    
    print(f"✅ Loaded {len(results)} evaluation results")
    
    # Extract scores
    scores = extract_scores(results)
    
    # Show score counts
    print("\nScore counts per criterion:")
    for criterion, score_list in scores.items():
        print(f"  {criterion}: {len(score_list)} scores")
    
    # Calculate averages
    averages = calculate_averages(scores)
    
    print("\nCalculated averages:")
    for criterion, avg in averages.items():
        print(f"  {criterion}: {avg:.2f}")
    
    # Print tables
    print_table1(args.engine, averages, len(results))
    print_markdown_table(args.engine, averages, len(results))
    
    # Save to files
    save_to_files(args.engine, averages, len(results))


if __name__ == "__main__":
    main()
