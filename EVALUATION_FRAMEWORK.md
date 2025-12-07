# Complete Evaluation Framework for Patient Simulation

## Three-Level Evaluation System

### Overview

This evaluation framework implements the complete methodology from the research paper, providing three complementary evaluation approaches:

```
┌─────────────────────────────────────────────────────────┐
│                  Evaluation Levels                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. CONVERSATION-LEVEL (Holistic)                      │
│     ├─ Personality Consistency                         │
│     ├─ Language Proficiency Match                      │
│     ├─ Recall Level Consistency                        │
│     ├─ Confusion Level Appropriateness                 │
│     ├─ Clinical Realism                                │
│     └─ Response Appropriateness                        │
│     Score: 0-4 per dimension                           │
│                                                         │
│  2. SENTENCE-LEVEL (Micro - Factual Accuracy)          │
│     ├─ Step 1: Classify sentence type                  │
│     ├─ Step 2: Identify related profile items          │
│     └─ Step 3: Verify NLI (entailment/neutral/contra)  │
│     Metric: Entail(%) = % factually accurate sentences │
│                                                         │
│  3. DIALOGUE-LEVEL (Profile Extraction)                │
│     ├─ Extract patient profile from dialogue           │
│     ├─ Compare with ground truth                       │
│     └─ Persona-aware dual scoring:                     │
│         • Extraction Score (1-4): Info completeness    │
│         • Role-Play Score (1-4): Persona consistency   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Conversation-Level Evaluation

### Purpose
Holistic assessment of patient simulation quality across 6 key dimensions.

### Usage
```powershell
# Single file
python Eval_sim.py --conversation_file patient.txt --output_file results.json

# Batch mode (all files in folder)
python Eval_sim.py --simulation_folder simulation_outputs --output_file results.json
```

### Scoring
- **Scale**: 0-4 for each dimension
- **Overall**: Average across all dimensions

### Dimensions Evaluated
1. **Personality**: Consistency with assigned traits (pleasing, agreeable, etc.)
2. **Language Proficiency**: Match with CEFR level (A1-C2)
3. **Recall Consistency**: Memory performance matches setting (low/normal/high)
4. **Confusion Consistency**: Confusion level matches configuration
5. **Clinical Realism**: Medical accuracy and believability
6. **Response Appropriateness**: Context-appropriate responses

### Output
```json
{
  "conversation_id": "patient_123",
  "evaluations": {
    "Personality": {
      "score": 3,
      "analysis": "...",
      "feedback": "..."
    },
    ...
  },
  "overall_score": 3.5
}
```

---

## 2. Sentence-Level Evaluation

### Purpose
Measure factual accuracy using Natural Language Inference (NLI) - **Equation 2 from paper**.

### Usage
```powershell
python Eval_sim.py --conversation_file patient.txt --output_file sentence_eval.json --sentence_level
```

### Three-Step Process

#### Step 1: Classify Sentence Type
Categorize each patient sentence:
- **politeness**: Greetings, thanks
- **emotion**: Feelings, concerns
- **inquiry**: Questions
- **meta-information**: Communication comments
- **information**: Medical facts (→ proceed to Steps 2-3)

#### Step 2: Identify Related Profile Items
For "information" sentences, determine which profile categories are mentioned:
- `r_k = 1`: Category mentioned (age, medications, etc.)
- `r_k = 0`: Category not mentioned

#### Step 3: Verify Factual Accuracy (NLI)
For each related item (`r_k = 1`), evaluate consistency:
- **+1**: Entailment (sentence consistent with profile)
- **0**: Neutral (unrelated or unclear)
- **-1**: Contradiction (sentence conflicts with profile)

### Key Metric: Entail(%)

**Formula (Equation 2):**
```
Entail(%) = (# info sentences with ≥1 entailment) / (# total info sentences) × 100
```

**Interpretation:**
- **>80%**: High factual accuracy
- **50-80%**: Moderate accuracy
- **<50%**: Low accuracy (many contradictions/unverifiable claims)

### Output
```json
{
  "conversations": [
    {
      "conversation_id": "patient_123",
      "sentence_evaluations": [
        {
          "turn": 5,
          "sentence": "I'm 65 years old",
          "type": "information",
          "related_items": [{"category": "age", "prediction": 1}],
          "factual_accuracy": [
            {
              "profile": "age: 65",
              "entailment_prediction": 1,
              "explanation": "Exact match"
            }
          ]
        }
      ],
      "factual_accuracy_metrics": {
        "total_information_sentences": 15,
        "entailed_sentences": 12,
        "entail_percentage": 80.0
      }
    }
  ],
  "overall_statistics": {
    "overall_entail_percentage": 80.0
  }
}
```

---

## 3. Dialogue-Level Evaluation

### Purpose
Assess profile extraction quality and simulation realism with **persona-aware dual scoring**.

### Usage

#### Persona-Aware Mode (Default - Recommended)
```powershell
python Eval_sim.py --conversation_file patient.txt --output_file dialogue_eval.json --dialogue_level
```

#### Simple Consistency Mode
```powershell
python Eval_sim.py --conversation_file patient.txt --output_file dialogue_eval.json --dialogue_level --simple_consistency
```

### Two-Step Process

#### Step 1: Profile Extraction (Figure D13)
Extract patient information from dialogue:
- Age, gender, race
- Chief complaint, diagnosis
- Medical history, medications
- Allergies, family history
- Social history (alcohol, tobacco)

#### Step 2: Consistency Evaluation

**Persona-Aware Mode (Dual Scoring):**
For each profile item:
1. **Extraction Score (1-4)**: How much information was captured?
2. **Role-Play Score (1-4)**: Is incomplete disclosure appropriate given persona?

**Simple Mode (Single Score):**
- Semantic similarity between extracted and ground truth (1-4)

### Persona-Aware Interpretation

| Extraction | Role-Play | Meaning |
|-----------|-----------|---------|
| Low (1-2) | High (3-4) | ✅ Realistic challenging patient (e.g., low recall) |
| High (3-4) | High (3-4) | ✅ Ideal simulation (complete + realistic) |
| Low (1-2) | Low (1-2) | ❌ Poor simulation (missing + unrealistic) |
| High (3-4) | Low (1-2) | ⚠️ Unrealistic (too cooperative) |

### Output
```json
{
  "conversation_id": "patient_123",
  "evaluation_mode": "persona_aware",
  "persona_config": {
    "personality": "pleasing",
    "recall_level": "low"
  },
  "consistency_evaluation": {
    "alcohol": {
      "extraction_reason": "Patient mentioned 'occasional drinking', omitted dependence",
      "extraction_score": 2,
      "roleplay_reason": "Pleasing personality realistically minimizes problems",
      "roleplay_score": 4
    }
  },
  "summary": {
    "average_extraction_score": 1.71,
    "average_roleplay_score": 2.57
  }
}
```

---

## Complete Workflow Example

```powershell
# Step 1: Generate patient simulation
python paitent_sim_autogen_v3.py

# Step 2: Conversation-level evaluation (holistic quality)
python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_conversation.json

# Step 3: Sentence-level evaluation (factual accuracy)
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_sentence.json --sentence_level

# Step 4: Dialogue-level evaluation (profile extraction + persona awareness)
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_dialogue.json --dialogue_level
```

---

## When to Use Each Evaluation

| Use Case | Recommended Evaluation |
|----------|----------------------|
| Overall simulation quality assessment | **Conversation-Level** |
| Verify patient statements are factually consistent | **Sentence-Level** |
| Test doctor's information gathering skills | **Dialogue-Level (Extraction Score)** |
| Assess patient realism with persona constraints | **Dialogue-Level (Role-Play Score)** |
| Medical student training feedback | **All Three** |
| Research paper metrics | **All Three** |

---

## Key Differences Summary

| Aspect | Conversation | Sentence | Dialogue |
|--------|-------------|----------|----------|
| **Granularity** | Holistic | Per-sentence | Per-profile-item |
| **Main Metric** | 0-4 scores | Entail(%) | Extraction + Roleplay |
| **Evaluates** | Overall quality | Factual accuracy | Profile completeness |
| **Best For** | General assessment | NLI verification | Information extraction |
| **Paper Reference** | Section 3.2 | Equation 2, Figure 2 | Figure D13-D14 |

---

## Implementation Notes

- All three evaluations use the same LLM (deepseek-r1:14b via Ollama)
- Sentence-level and dialogue-level use specialized prompts from the paper
- Persona-aware mode is unique extension addressing evaluation paradox
- Results are saved in JSON format for further analysis
