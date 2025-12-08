# MIMIC-IV Patient Simulation & Evaluation Framework

A comprehensive system for extracting ED patient data from MIMIC-IV and evaluating AI-generated patient simulations using a three-tier evaluation framework.

## 🎯 Overview

1. **Data Extraction**: Extract 50 ED patient profiles from MIMIC-IV (17-18 fields each)
2. **Patient Simulation**: Generate realistic doctor-patient conversations using AutoGen
3. **Three-Tier Evaluation**: Assess simulation quality at conversation, sentence, and dialogue levels

## 🚀 Quick Start

### Prerequisites

- MIMIC-IV dataset in `../../mimic_4/` directory
- Python 3.8+ with dependencies: `pip install -r requirements.txt`

### Complete Workflow

```bash
# Step 1: Extract patient data from MIMIC-IV
python extract_ed_patients_v2.py
python enrich_from_notes.py

# Step 2: Generate patient simulations (50 conversations)
python paitent_sim_autogen_v3.py

# Step 3: Evaluate simulations (choose evaluation type)

# Conversation-level: 6 dimensions (Personality, Language, Recall, etc.)
python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json

# Sentence-level: Factual accuracy using NLI (Entail%)
python Eval_sim.py --sentence_level --simulation_folder simulation_outputs --output_file sentence_level_evaluation.json

# Dialogue-level: Profile extraction with dual scoring
python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json

# Step 4: Generate evaluation tables
python generate_table1.py  # Persona Fidelity (5 criteria, 0-4 scale)
python generate_table2.py  # Sentence-Level Factuality (Entail%, Contradict%)
python generate_table3.py  # Dialogue-Level Factuality (ICov, ICon)
```

## 📊 Three-Tier Evaluation Framework

### 1. Conversation-Level Evaluation
- **Metrics**: 6 dimensions rated 0-4 (Personality, Language, Recall, Confusion, Realism, Appropriateness)
- **Output**: Average scores per dimension
- **Time**: ~30-60 minutes for 50 conversations

### 2. Sentence-Level Evaluation
- **Method**: Natural Language Inference (NLI) for factual accuracy
- **Key Metric**: **Entail(%)** - Percentage of information sentences entailed by patient profile
- **Implementation**: Follows paper's Equation 2
- **Time**: ~1-2 hours for 50 conversations

### 3. Dialogue-Level Evaluation
- **Dual Scoring System** (Persona-Aware):
  - **Extraction Score**: Information completeness
  - **Role-Play Score**: Personality consistency
- **Innovation**: Distinguishes information gaps (challenging scenario) vs. poor simulation quality
- **Time**: ~1-2 hours for 50 conversations

## 📈 Data Quality

- **50 ED patients** from MIMIC-IV
- **17-18 fields per patient** (out of 27 possible)
- **100% coverage** of Present Illness from discharge notes
- **95% coverage** of Pain scores from ED triage
- **85% coverage** of ED medications

### Available Fields (17-18 per patient)
✅ Demographics: age, gender, race, marital_status, insurance  
✅ Clinical: diagnosis, medical_history, allergies, family_medical_history  
✅ ED-specific: chief_complaint, pain, medication, arrival_transport  
✅ Presentation: present_illness_positive, present_illness_negative  

### Unavailable Fields (Social History)
❌ MIMIC-IV de-identification removes: occupation, tobacco, alcohol, living_situation, exercise, illicit_drug, sexual_history, children

## 📊 Example Results

**Table 1: Persona Fidelity Evaluation**
| Engine | Personality | Language | Recall | Confused | Realism | Avg. |
|--------|-------------|----------|--------|----------|---------|------|
| deepseek-r1:8b | 3.40 | 3.38 | 3.22 | 3.53 | 3.19 | 3.34 |

## 📖 Documentation

- **[`HOW_TO_GENERATE_ALL_TABLES.md`](HOW_TO_GENERATE_ALL_TABLES.md)** - Complete guide for generating Tables 1-3
- **[`EVALUATION_FRAMEWORK.md`](EVALUATION_FRAMEWORK.md)** - Three-tier evaluation details
- **[`DIALOGUE_LEVEL_EVALUATION.md`](DIALOGUE_LEVEL_EVALUATION.md)** - Dual scoring system explanation
- **[`EVALUATION_COMPARISON.md`](EVALUATION_COMPARISON.md)** - Persona-Aware vs Simple evaluation

## 🔧 Configuration

Copy `.env.example` to `.env` and add your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## 📁 Project Structure

```
final_all_v1/
├── extract_ed_patients_v2.py           # Extract patient records
├── enrich_from_notes.py                # Extract from clinical notes
├── paitent_sim_autogen_v3.py          # Patient simulation generator
├── Eval_sim.py                         # Three-tier evaluation system
├── generate_table1.py                  # Generate Table 1
├── generate_table2.py                  # Generate Table 2
├── generate_table3.py                  # Generate Table 3
├── simulation_outputs/                 # Simulation results
│   ├── patient_*.txt                   # Conversation transcripts
│   └── patient_*_evaluation.json       # Evaluation results
└── docs/                               # Documentation
```

## 🔒 Security

- API keys protected via `.env` (not tracked)
- Use `.env.example` as template
- Large data files excluded from repository

## 📝 License

MIT License - See `LICENSE` for details

## 🙏 Acknowledgments

Data from MIMIC-IV v3.1 and MIMIC-IV-Note v2.2

## 📚 References

- [MIMIC-IV Documentation](https://mimic.mit.edu/docs/iv/)
- [AutoGen Framework](https://microsoft.github.io/autogen/)

---

For detailed instructions, see [`HOW_TO_GENERATE_ALL_TABLES.md`](HOW_TO_GENERATE_ALL_TABLES.md)
