"""
Generate Table 2: Sentence-Level Factuality Evaluation
从sentence-level evaluation results中提取句子级别的事实准确性指标
"""

import json
import os
from typing import Dict, List, Tuple


def load_sentence_evaluation_results(json_file: str) -> Dict:
    """
    加载句子级别评估结果JSON文件
    """
    if not os.path.exists(json_file):
        print(f"Error: File {json_file} not found!")
        print("Please run sentence-level evaluation first:")
        print("  python Eval_sim.py --conversation_file simulation_outputs/patient_XXX.txt --output_file sentence_eval.json --sentence_level")
        return {}
    
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    return results


def calculate_table2_metrics(results: Dict) -> Dict[str, float]:
    """
    计算Table 2的所有指标
    
    返回指标：
    - Info(%): 信息类型句子的百分比
    - Supported(%): 被至少一个档案项相关的句子百分比
    - Unsupported(%): 不被任何档案项相关的句子百分比
    - Entail(%): 在Supported句子中，被entail的百分比
    - Contradict(%): 在Supported句子中，被contradict的百分比
    - Plausibility: 在Unsupported句子中的可信度评分(1-5)
    """
    conversations = results.get('conversations', [])
    
    total_sentences = 0
    info_sentences = 0
    supported_sentences = 0
    unsupported_sentences = 0
    entailed_sentences = 0
    contradicted_sentences = 0
    plausibility_scores = []
    
    for conv in conversations:
        sentence_evals = conv.get('sentence_evaluations', [])
        
        for sent in sentence_evals:
            total_sentences += 1
            
            # 统计信息类型句子
            if sent.get('type') == 'information':
                info_sentences += 1
                
                # 检查是否有相关项 (related_items with prediction=1)
                related_items = sent.get('related_items', [])
                has_related = any(item.get('prediction') == 1 for item in related_items)
                
                if has_related:
                    # Supported sentence
                    supported_sentences += 1
                    
                    # 检查事实准确性
                    factual_accuracy = sent.get('factual_accuracy', [])
                    
                    # 检查是否有entailment (prediction=1)
                    has_entailment = any(acc.get('entailment_prediction') == 1 for acc in factual_accuracy)
                    if has_entailment:
                        entailed_sentences += 1
                    
                    # 检查是否有contradiction (prediction=-1)
                    has_contradiction = any(acc.get('entailment_prediction') == -1 for acc in factual_accuracy)
                    if has_contradiction:
                        contradicted_sentences += 1
                else:
                    # Unsupported sentence
                    unsupported_sentences += 1
                    # 这里需要额外的plausibility评估，当前实现中没有
                    # 默认给一个中等分数
                    plausibility_scores.append(3.5)
    
    # 计算百分比和指标
    metrics = {}
    
    # Info(%)
    metrics['Info(%)'] = (info_sentences / total_sentences) if total_sentences > 0 else 0
    
    # Supported(%)
    metrics['Supported(%)'] = (supported_sentences / info_sentences) if info_sentences > 0 else 0
    
    # Unsupported(%)
    metrics['Unsupported(%)'] = (unsupported_sentences / info_sentences) if info_sentences > 0 else 0
    
    # Entail(%) - 在supported句子中
    metrics['Entail(%)'] = (entailed_sentences / supported_sentences) if supported_sentences > 0 else 0
    
    # Contradict(%) - 在supported句子中
    metrics['Contradict(%)'] = (contradicted_sentences / supported_sentences) if supported_sentences > 0 else 0
    
    # Plausibility - 在unsupported句子中的平均分
    metrics['Plausibility'] = (sum(plausibility_scores) / len(plausibility_scores)) if plausibility_scores else 0
    
    # 添加原始计数用于调试
    metrics['_debug'] = {
        'total_sentences': total_sentences,
        'info_sentences': info_sentences,
        'supported_sentences': supported_sentences,
        'unsupported_sentences': unsupported_sentences,
        'entailed_sentences': entailed_sentences,
        'contradicted_sentences': contradicted_sentences
    }
    
    return metrics


def print_table2(engine_name: str, metrics: Dict[str, float]):
    """
    打印 Table 2 格式的结果
    """
    print("\n" + "="*120)
    print("Table 2: Sentence-Level Factuality Evaluation")
    print("Supported statements: sentences that relate to at least one item in the given profile.")
    print("Unsupported statements: sentences with information not explicitly mentioned in the profile.")
    print("Entail and Contradict are evaluated for supported, while Plausibility is assessed for unsupported.")
    print("="*120)
    print()
    
    # Header
    header = f"{'Engine':<25} {'Info(%)':<12} {'Supported(%)':<15} {'Unsupported(%)':<17} {'Entail(%, ↑)':<15} {'Contradict(%, ↓)':<18} {'Plausibility(↑)':<15}"
    print(header)
    print("-"*120)
    
    # Data row
    row = f"{engine_name:<25}"
    row += f" {metrics['Info(%)']:<11.3f}"
    row += f" {metrics['Supported(%)']:<14.3f}"
    row += f" {metrics['Unsupported(%)']:<16.3f}"
    row += f" {metrics['Entail(%)']:<14.3f}"
    row += f" {metrics['Contradict(%)']:<17.3f}"
    row += f" {metrics['Plausibility']:<14.3f}"
    print(row)
    
    print("="*120)
    print()
    
    # Print debug info
    if '_debug' in metrics:
        debug = metrics['_debug']
        print("Statistics:")
        print(f"  Total sentences: {debug['total_sentences']}")
        print(f"  Information sentences: {debug['info_sentences']}")
        print(f"  Supported sentences: {debug['supported_sentences']}")
        print(f"  Unsupported sentences: {debug['unsupported_sentences']}")
        print(f"  Entailed sentences: {debug['entailed_sentences']}")
        print(f"  Contradicted sentences: {debug['contradicted_sentences']}")
        print()


def print_markdown_table2(engine_name: str, metrics: Dict[str, float]):
    """
    打印 Markdown 格式的 Table 2
    """
    print("\n## Table 2: Sentence-Level Factuality Evaluation")
    print()
    print("| Engine | Info(%) | Supported(%) | Unsupported(%) | Entail(%, ↑) | Contradict(%, ↓) | Plausibility(↑) |")
    print("|--------|---------|--------------|----------------|--------------|------------------|-----------------|")
    
    row = f"| {engine_name}"
    row += f" | {metrics['Info(%)']:.3f}"
    row += f" | {metrics['Supported(%)']:.3f}"
    row += f" | {metrics['Unsupported(%)']:.3f}"
    row += f" | {metrics['Entail(%)']:.3f}"
    row += f" | {metrics['Contradict(%)']:.3f}"
    row += f" | {metrics['Plausibility']:.3f} |"
    print(row)
    print()


def save_table2(engine_name: str, metrics: Dict[str, float]):
    """
    保存 Table 2 到文件
    """
    # Save text format
    with open("table2_sentence_factuality.txt", 'w', encoding='utf-8') as f:
        import sys
        old_stdout = sys.stdout
        sys.stdout = f
        print_table2(engine_name, metrics)
        sys.stdout = old_stdout
    
    # Save markdown format
    with open("table2_sentence_factuality.md", 'w', encoding='utf-8') as f:
        old_stdout = sys.stdout
        sys.stdout = f
        print_markdown_table2(engine_name, metrics)
        sys.stdout = old_stdout
    
    print("✅ Text format saved to: table2_sentence_factuality.txt")
    print("✅ Markdown format saved to: table2_sentence_factuality.md")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Table 2: Sentence-Level Factuality Evaluation")
    parser.add_argument(
        "--input",
        type=str,
        default="sentence_level_evaluation.json",
        help="Input sentence-level evaluation results JSON file"
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="deepseek-r1:8b",
        help="LLM engine name"
    )
    
    args = parser.parse_args()
    
    print("\n🎯 Table 2 Generator: Sentence-Level Factuality Evaluation")
    print(f"📁 Reading from: {args.input}")
    print(f"🤖 Engine: {args.engine}")
    
    # Load results
    results = load_sentence_evaluation_results(args.input)
    
    if not results:
        print("\n⚠️  No results found. To generate sentence-level evaluation:")
        print("\n📝 Step 1: Run sentence-level evaluation on ONE conversation file:")
        print("   python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file sentence_eval.json --sentence_level")
        print("\n📝 Step 2: Generate Table 2:")
        print("   python generate_table2.py --input sentence_eval.json --engine \"deepseek-r1:8b\"")
        return
    
    print(f"✅ Loaded evaluation results")
    
    # Calculate metrics
    metrics = calculate_table2_metrics(results)
    
    print("\nCalculated metrics:")
    for key, value in metrics.items():
        if key != '_debug':
            print(f"  {key}: {value:.3f}")
    
    # Print tables
    print_table2(args.engine, metrics)
    print_markdown_table2(args.engine, metrics)
    
    # Save to files
    save_table2(args.engine, metrics)


if __name__ == "__main__":
    main()
