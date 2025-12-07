# Dialogue-Level Evaluation Guide

## Overview
Dialogue-level evaluation extracts a patient profile from the conversation and compares it with the ground truth profile to measure consistency.

**IMPORTANT**: This evaluation now supports **dual-scoring mode** to distinguish between:
- **Information Extraction Quality** (How much data was captured?)
- **Role-Play Consistency** (Is missing data realistic given the patient's persona?)

## The Evaluation Paradox

### Problem
Traditional evaluation measures profile extraction completeness:
- **Low score** = Missing/incorrect information → Appears to be "bad" quality
- But what if the patient is **intentionally** withholding information due to persona (e.g., low recall, pleasing personality)?

### Solution: Dual-Scoring System

#### Mode 1: Persona-Aware (DEFAULT - Recommended)
```powershell
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file results.json --dialogue_level
```

**Provides TWO scores for each profile item:**

1. **Extraction Score (1-4)**: Information completeness
   - Score 4: Complete and accurate extraction
   - Score 3: Partial extraction with key details
   - Score 2: Minimal extraction, mostly missing
   - Score 1: Completely missing or incorrect

2. **Role-Play Score (1-4)**: Persona consistency
   - Score 4: Patient behavior perfectly matches persona (e.g., low recall → vague answers)
   - Score 3: Patient behavior mostly matches persona
   - Score 2: Patient behavior partially matches persona
   - Score 1: Patient behavior contradicts persona (e.g., low recall but perfect memory)

**Example Output:**
```json
{
  "conversation_id": "patient_28651902",
  "evaluation_mode": "persona_aware",
  "persona_config": {
    "personality": "pleasing",
    "recall_level": "low"
  },
  "consistency_evaluation": {
    "alcohol": {
      "extraction_reason": "Patient only mentioned 'occasional drinking', omitting alcohol dependence and Antabuse treatment. Information extraction is incomplete.",
      "extraction_score": 3,
      "roleplay_reason": "Given the pleasing personality and low recall, it is realistic for the patient to minimize alcohol problems and avoid mentioning sensitive treatment details.",
      "roleplay_score": 4
    }
  },
  "summary": {
    "average_extraction_score": 1.71,  // Low = Missing data
    "average_roleplay_score": 2.57,    // Higher = Realistic behavior
    "interpretation": {
      "extraction_score": "Measures information completeness (low = missing data)",
      "roleplay_score": "Measures persona consistency (high = realistic patient behavior)"
    }
  }
}
```

#### Mode 2: Simple Consistency (Original Figure D14)
```powershell
python Eval_sim.py --conversation_file file.txt --output_file results.json --dialogue_level --simple_consistency
```

**Provides single score** measuring semantic similarity only (ignores persona).

## Interpretation Guide

| Extraction Score | Role-Play Score | Interpretation |
|-----------------|----------------|----------------|
| Low (1-2) | High (3-4) | ✅ **Realistic Patient** - Successfully portrays persona (e.g., low recall, pleasing) |
| High (3-4) | High (3-4) | ✅ **Ideal Simulation** - Complete information + realistic behavior |
| Low (1-2) | Low (1-2) | ❌ **Poor Simulation** - Missing info + inconsistent with persona |
| High (3-4) | Low (1-2) | ⚠️ **Unrealistic** - Patient reveals too much despite persona constraints |

## Real Example Analysis

### Case: Patient with "Pleasing + Low Recall" Persona

**Alcohol History:**
- **Ground Truth**: Alcohol dependence, taking Antabuse
- **Patient Said**: "I drink occasionally, once or twice a week"
- **Extraction Score**: 3/4 (partial - mentioned drinking but not dependence)
- **Role-Play Score**: 4/4 (realistic - pleasing personality minimizes problems)

**Medications:**
- **Ground Truth**: 10 medications including Antabuse, Cymbalta, fluoxetine
- **Patient Said**: Vague references to "blood pressure medicine"
- **Extraction Score**: 1/4 (almost complete failure to extract)
- **Role-Play Score**: 2/4 (somewhat realistic but omits too much)

**Conclusion**: 
- Average Extraction: 1.71/4 → Poor information capture (challenges doctor's skills)
- Average Role-Play: 2.57/4 → Moderately realistic persona consistency
- Overall: Patient simulator successfully creates a **challenging but realistic** scenario

## Method (from Paper)
1. **Profile Extraction** (Figure D13): Extract derived profile from dialogue
2. **Semantic Similarity** (Figure D14): Compare each extracted item with original
3. **Scoring**: Rate consistency on 1-4 scale for each profile field
4. **NEW - Persona Awareness**: Evaluate if missing information is appropriate

## Usage Examples
## Usage Examples

### 1. Persona-Aware Evaluation (Recommended)
```powershell
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file profile_persona_aware.json --dialogue_level
```

### 2. Simple Consistency (Ignore Persona)
```powershell
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file profile_simple.json --dialogue_level --simple_consistency
```

### 3. Batch Workflow
```powershell
# Run simulation
python paitent_sim_autogen_v3.py

# Conversation-level evaluation (6 dimensions)
python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_conversation.json

# Dialogue-level evaluation (profile consistency with persona awareness)
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_dialogue.json --dialogue_level

# Sentence-level evaluation (factual accuracy)
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_sentence.json --sentence_level
```

## Comparison with Other Evaluation Types

| Evaluation Type | Purpose | Scoring | Command |
|----------------|---------|---------|---------|
| **Conversation-Level** | Evaluate 6 dimensions (personality, language, etc.) | 0-4 scale per dimension | `--simulation_folder` (default) |
| **Sentence-Level** | Verify factual accuracy of each sentence | **Entail(%)** = % of info sentences entailed by profile | `--sentence_level` |
| **Dialogue-Level (Persona-Aware)** | Extract profile + dual scoring | Extraction score + Roleplay score (1-4 each) | `--dialogue_level` (default) |
| **Dialogue-Level (Simple)** | Extract profile + consistency only | Single consistency score (1-4) | `--dialogue_level --simple_consistency` |

## Sentence-Level Evaluation: Entail(%) Metric

### Formula (Equation 2 from Paper)

```
Entail(D_i) = Σ_t Σ_m [C(s_tm) = info] · max_k r_k · [NLI(s_tm, x_k) = entail]
              ────────────────────────────────────────────────────────────
                          Σ_t Σ_m [C(s_tm) = info]
```

Where:
- `C(s_tm)`: Sentence type classifier (Step 1)
- `r_k`: Related profile item indicator (Step 2) - 1 if related, 0 otherwise
- `NLI(s_tm, x_k)`: Natural Language Inference result (Step 3)
  - **1** = entailment (consistent)
  - **0** = neutral (unrelated)
  - **-1** = contradiction (inconsistent)

### Interpretation

**Entail(%) = (# info sentences with ≥1 entailment) / (# total info sentences) × 100**

- **High Entail(%)** (>80%): Patient provides factually accurate information
- **Medium Entail(%)** (50-80%): Mix of accurate and inaccurate/vague information
- **Low Entail(%)** (<50%): Patient provides contradictory or unverifiable information

### Example

**Conversation:**
1. Patient: "I'm 65 years old" (Type: information)
   - Related: age profile item (r_k=1)
   - NLI: Entailment (1) ✓ **Counted as entailed**

2. Patient: "Hello doctor" (Type: politeness)
   - Not information type → **Excluded from calculation**

3. Patient: "I have chest pain" (Type: information)
   - Related: chief_complaint (r_k=1)
   - NLI: Entailment (1) ✓ **Counted as entailed**

4. Patient: "I never drink" (Type: information)
   - Related: alcohol history (r_k=1)
   - NLI: Contradiction (-1) ✗ **Not counted**

**Calculation:**
- Total information sentences: 3 (sentences 1, 3, 4)
- Entailed sentences: 2 (sentences 1, 3)
- **Entail(%) = 2/3 × 100 = 66.67%**

### Output Format

```json
{
  "conversations": [
    {
      "conversation_id": "patient_123",
      "sentence_evaluations": [...],
      "factual_accuracy_metrics": {
        "total_information_sentences": 15,
        "entailed_sentences": 12,
        "entail_percentage": 80.0
      }
    }
  ],
  "overall_statistics": {
    "total_conversations": 1,
    "total_information_sentences": 15,
    "total_entailed_sentences": 12,
    "overall_entail_percentage": 80.0
  }
}
```

## Notes

- Persona-aware mode is **default** for dialogue-level evaluation (use `--simple_consistency` to disable)
- Dual-scoring helps distinguish between:
  - **Doctor's information gathering skill** (extraction score)
  - **Patient simulator's realism** (roleplay score)
- Low extraction + High roleplay = Successful challenging patient simulation
- Results include detailed reasoning for each score
- Medical knowledge is used to assess semantic equivalence
