# How to Generate All Evaluation Tables

This guide provides a complete workflow for generating **Table 1**, **Table 2**, and **Table 3** from the PatientSim evaluation results, matching the paper's format.

## Overview

| Table | Type | Metrics | Evaluation Level | Time Required |
|-------|------|---------|------------------|---------------|
| **Table 1** | Persona Fidelity | 5 criteria (0-4 scale) | Conversation-level | ~30-60 min for 50 conversations |
| **Table 2** | Sentence-Level Factuality | 6 metrics (Info%, Entail%, etc.) | Sentence-level | ~1-2 hours for 50 conversations |
| **Table 3** | Dialogue-Level Factuality | 2 metrics × 3 categories | Dialogue-level | ~1-2 hours for 50 conversations |

---

## Table 1: Persona Fidelity Evaluation

### What It Measures
Evaluates how well the simulated patient maintains their assigned persona across 5 criteria:
- **Personality** (e.g., Overanxious, Impatient, Pleasing)
- **Language** Proficiency (Basic/Intermediate/Advanced)
- **Recall** Consistency (High/Low recall ability)
- **Confused** (Normal/Highly Confused mental state)
- **Realism** (Clinical realism of symptoms)

### Step 1: Run Conversation-Level Evaluation
```bash
# Activate conda environment
conda activate AI_H_01

# Evaluate all 50 conversations (conversation-level evaluation)
conda run -n AI_H_01 python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json
```

**What this does:**
- Evaluates each conversation on 6 dimensions (includes the 5 criteria above + Response_Appropriateness)
- Saves results to `evaluation_results.json`
- Creates individual evaluation files: `simulation_outputs/patient_*_evaluation.json`

**Time:** ~30-60 minutes for 50 conversations

### Step 2: Generate Table 1
```bash
python generate_table1.py --input evaluation_results.json --engine "deepseek-r1:8b"
```

**Output:**
- Console display with formatted table
- `table1_persona_fidelity.txt` (text format)
- `table1_persona_fidelity.md` (markdown format)

**Example Output:**
```
Table 1: Persona Fidelity Evaluation
====================================================================================================
Engine                               Personality     Language       Recall     Confused      Realism         Avg.
----------------------------------------------------------------------------------------------------
deepseek-r1:8b                              3.45         3.78         2.89         3.12         3.56         3.36
====================================================================================================
```

---

## Table 2: Sentence-Level Factuality Evaluation

### What It Measures
Evaluates factual accuracy at the sentence level across 6 metrics:
- **Info(%)**: Percentage of information-type sentences
- **Supported(%)**: Sentences related to profile items
- **Unsupported(%)**: Sentences not in profile
- **Entail(%, ↑)**: Supported sentences that are entailed (accurate)
- **Contradict(%, ↓)**: Supported sentences that contradict profile
- **Plausibility(↑)**: Plausibility score for unsupported sentences (1-5)

### Step 1: Run Sentence-Level Evaluation

**Option A: Evaluate a single conversation (for testing)**
```bash
conda run -n AI_H_01 python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file sentence_eval_single.json --sentence_level
```

**Option B: Batch evaluate all 50 conversations**
```bash
# Batch evaluate all conversations in simulation_outputs/
conda run -n AI_H_01 python Eval_sim.py --sentence_level --simulation_folder simulation_outputs --output_file sentence_level_evaluation.json
```

**What this does:**
- Classifies each sentence as information/social/other
- Identifies related profile items
- Performs NLI (Natural Language Inference) for factual accuracy
- Calculates Entail(%) using Equation 2 from the paper

**Time:** ~2-3 minutes per conversation (1-2 hours for 50 conversations if done sequentially)

### Step 2: Generate Table 2
```bash
python generate_table2.py --input sentence_level_evaluation.json --engine "deepseek-r1:8b"
```

**Output:**
- Console display with formatted table
- `table2_sentence_factuality.txt` (text format)
- `table2_sentence_factuality.md` (markdown format)

**Example Output:**
```
Table 2: Sentence-Level Factuality Evaluation
================================================================================
Engine                    Info(%)      Supported(%)    Unsupported(%)   Entail(%, ↑)    Contradict(%, ↓)   Plausibility(↑)
------------------------------------------------------------------------------------------------------------------------
deepseek-r1:8b            0.972        0.763           0.237            0.978           0.022              3.953
================================================================================
```

---

## Table 3: Dialogue-Level Factuality Evaluation

### What It Measures
Evaluates profile extraction and consistency across 3 categories:
- **Social**: Social History (age, gender, occupation, tobacco, alcohol)
- **PMH**: Previous Medical History (medical_history, medications, allergies)
- **CurrentVisit**: Current Visit Info (chief_complaint, diagnosis, symptoms)

**Two Metrics:**
- **ICov (%)**: Information Coverage - percentage of items extracted
- **ICon (4-point)**: Information Consistency - consistency score (0-4)

### Step 1: Run Dialogue-Level Evaluation
```bash
# Batch evaluate all 50 conversations
conda run -n AI_H_01 python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json
```

**What this does:**
- Extracts patient profile from each dialogue using LLM (Figure D13 prompt)
- Compares extracted profile with ground truth
- Uses persona-aware dual scoring (extraction_score + roleplay_score)
- Categorizes profile items into Social/PMH/CurrentVisit
- Saves results to `dialogue_evaluation_results.json`
- Creates individual files: `simulation_outputs/patient_*_dialogue_eval.json`

**Time:** ~1-2 hours for 50 conversations (LLM-intensive)

### Step 2: Generate Table 3
```bash
python generate_table3.py --input dialogue_evaluation_results.json --engine "deepseek-r1:8b"
```

**Output:**
- Console display with formatted table
- `table3_dialogue_factuality.txt` (text format)
- `table3_dialogue_factuality.md` (markdown format)

**Example Output:**
```
Table 3: Dialogue-Level Factuality Evaluation
================================================================================
Engine                    Information Coverage (ICov) (%)                    Information Consistency (ICon) (4-point)
                          Social      PMH         CurrentVisit   Avg.        Social      PMH         CurrentVisit   Avg.
------------------------------------------------------------------------------------------------------------------------
deepseek-r1:8b            0.44        0.77        0.88           0.70        3.82        3.51        3.18           3.50
================================================================================
```

---

## Complete Workflow: Generate All Tables

### Prerequisites
```bash
# 1. Activate conda environment
conda activate AI_H_01

# 2. Ensure you have 50 conversation files in simulation_outputs/
ls simulation_outputs/*.txt | wc -l  # Should show 50
```

### Full Workflow

```bash
# =========================
# STEP 1: Conversation-Level Evaluation (for Table 1)
# =========================
conda run -n AI_H_01 python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json
# Time: ~30-60 minutes

# Generate Table 1
python generate_table1.py --input evaluation_results.json --engine "deepseek-r1:8b"
# Output: table1_persona_fidelity.txt, table1_persona_fidelity.md


# =========================
# STEP 2: Sentence-Level Evaluation (for Table 2)
# =========================
# Batch evaluate all 50 conversations
conda run -n AI_H_01 python Eval_sim.py --sentence_level --simulation_folder simulation_outputs --output_file sentence_level_evaluation.json
# Time: ~1-2 hours for 50 conversations

# Generate Table 2
python generate_table2.py --input sentence_level_evaluation.json --engine "deepseek-r1:8b"
# Output: table2_sentence_factuality.txt, table2_sentence_factuality.md


# =========================
# STEP 3: Dialogue-Level Evaluation (for Table 3)
# =========================
conda run -n AI_H_01 python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json
# Time: ~1-2 hours

# Generate Table 3
python generate_table3.py --input dialogue_evaluation_results.json --engine "deepseek-r1:8b"
# Output: table3_dialogue_factuality.txt, table3_dialogue_factuality.md
```

---

## Output Files Summary

After running all evaluations, you will have:

### Evaluation Results (JSON)
- `evaluation_results.json` - Conversation-level results for all 50 conversations
- `sentence_level_evaluation.json` - Sentence-level results for all 50 conversations
- `dialogue_evaluation_results.json` - Dialogue-level results for all 50 conversations
- `simulation_outputs/patient_*_evaluation.json` - Individual conversation-level results
- `simulation_outputs/patient_*_sentence_eval.json` - Individual sentence-level results
- `simulation_outputs/patient_*_dialogue_eval.json` - Individual dialogue-level results

### Table Files
- `table1_persona_fidelity.txt` / `table1_persona_fidelity.md`
- `table2_sentence_factuality.txt` / `table2_sentence_factuality.md`
- `table3_dialogue_factuality.txt` / `table3_dialogue_factuality.md`

---

## Understanding the Results

### Table 1: Persona Fidelity (0-4 scale)
- **4**: Excellent - Perfect persona consistency
- **3**: Good - Mostly consistent with minor deviations
- **2**: Fair - Some inconsistencies
- **1**: Poor - Significant inconsistencies
- **0**: Very Poor - Fails to maintain persona

**Good Performance:** Average score > 3.0 across all criteria

### Table 2: Sentence-Level Factuality
- **High Info(%)**: Most sentences contain medical information (~97%)
- **High Entail(%)**: Most supported sentences are accurate (~98%)
- **Low Contradict(%)**: Few contradictions (~2%)
- **High Plausibility**: Unsupported info is still medically reasonable (~4/5)

**Good Performance:** Entail > 0.95, Contradict < 0.05

### Table 3: Dialogue-Level Factuality
- **ICov varies by category:**
  - Social: 0.3-0.5 (low, expected - patients don't volunteer)
  - PMH: 0.6-0.8 (moderate-high - doctors ask actively)
  - CurrentVisit: 0.8-0.9 (high - main focus of visit)
- **ICon should be high:** > 3.0/4.0 for all categories

**Good Performance:** 
- CurrentVisit ICov > 0.8
- PMH ICov > 0.6
- All ICon > 3.0

---

## Troubleshooting

### Evaluation is too slow
- **Solution 1**: Use fewer conversations for testing (e.g., 10 instead of 50)
- **Solution 2**: Use a faster LLM model
- **Solution 3**: Run evaluations in parallel (modify scripts to use multiprocessing)

### Missing evaluation results
```bash
# Check if files exist
ls evaluation_results.json
ls sentence_level_evaluation.json
ls dialogue_evaluation_results.json

# If missing, re-run the corresponding evaluation step
```

### Table generation fails
```bash
# Check if input file exists and is valid JSON
cat evaluation_results.json | jq .  # Should show valid JSON

# Check script help
python generate_table1.py --help
python generate_table2.py --help
python generate_table3.py --help
```

### Scores seem wrong
- Check that the correct engine name is used (`--engine "deepseek-r1:8b"`)
- Verify that conversations were evaluated with the same LLM
- Review individual evaluation files in `simulation_outputs/`

---

## Advanced Usage

### Comparing Multiple Engines

To compare different LLMs, run evaluations separately:

```bash
# Engine 1: deepseek-r1:8b
conda run -n AI_H_01 python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_deepseek.json
python generate_table1.py --input eval_deepseek.json --engine "deepseek-r1:8b"

# Engine 2: gemini-2.5-flash
conda run -n AI_H_01 python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_gemini.json
python generate_table1.py --input eval_gemini.json --engine "gemini-2.5-flash"
```

Then manually combine the tables to show both engines in one table.

### Custom Metrics

To use custom evaluation metrics:

```bash
# Create custom metrics JSON file
cat > custom_metrics.json << EOF
{
  "Personality": {
    "dimension": "Personality",
    "description": "Custom personality evaluation",
    "scale": "0-4"
  }
}
EOF

# Use custom metrics
python Eval_sim.py --simulation_folder simulation_outputs --output_file results.json --metrics custom_metrics.json
```

---

## Quick Reference

| Task | Command | Time | Output |
|------|---------|------|--------|
| Conversation-level eval | `conda run -n AI_H_01 python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json` | 30-60 min | `evaluation_results.json` |
| Generate Table 1 | `python generate_table1.py` | <1 min | `table1_persona_fidelity.txt/md` |
| Sentence-level eval | `conda run -n AI_H_01 python Eval_sim.py --sentence_level --simulation_folder simulation_outputs --output_file sentence_level_evaluation.json` | 1-2 hours | `sentence_level_evaluation.json` |
| Generate Table 2 | `python generate_table2.py --input sentence_level_evaluation.json` | <1 min | `table2_sentence_factuality.txt/md` |
| Dialogue-level eval | `conda run -n AI_H_01 python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json` | 1-2 hours | `dialogue_evaluation_results.json` |
| Generate Table 3 | `python generate_table3.py` | <1 min | `table3_dialogue_factuality.txt/md` |

---

## Additional Resources

- **Detailed guides:**
  - `HOW_TO_GENERATE_TABLE1.md` - Table 1 detailed guide
  - `HOW_TO_GENERATE_TABLE2.md` - Table 2 detailed guide
  - `HOW_TO_GENERATE_TABLE3.md` - Table 3 detailed guide

- **Evaluation documentation:**
  - `EVALUATION_FRAMEWORK.md` - Complete evaluation system overview
  - `DIALOGUE_LEVEL_EVALUATION.md` - Dialogue-level evaluation details
  - `EVALUATION_COMPARISON.md` - Persona-aware vs simple consistency

- **Main README:**
  - `README.md` - Project overview and setup instructions

---

## Summary

1. **Table 1** measures **persona fidelity** across 5 criteria using conversation-level evaluation
2. **Table 2** measures **sentence-level factuality** using NLI and entailment analysis
3. **Table 3** measures **dialogue-level factuality** by extracting profiles and measuring coverage/consistency

All three tables can be generated from the same 50 conversation files, but require different evaluation modes. Total time: **2-4 hours** for complete evaluation pipeline.
