# MIMIC-IV ED Patient Data Extraction & Simulation Evaluation

从MIMIC-IV数据库中提取急诊科（ED）首次就诊患者记录，并提供完整的三层评估框架。

## 📁 项目结构

```
final_all_v1/
├── load_mimic4_data.py                      # MIMIC-IV数据加载器
├── extract_ed_patients_v2.py                # 提取ED患者记录
├── enrich_from_notes.py                     # 从临床笔记中提取信息
├── paitent_sim_autogen_v3.py               # 患者模拟生成器
├── Eval_sim.py                              # 三层评估系统 ⭐
├── ed_patient_records.json                  # 基础患者记录
├── ed_patient_records_enriched.json         # Enriched患者记录
├── simulation_outputs/                      # 模拟对话输出
│   ├── patient_*.txt                        # 对话文本
│   └── patient_*_evaluation.json            # 评估结果
├── EVALUATION_FRAMEWORK.md                  # 📖 完整评估框架文档
├── DIALOGUE_LEVEL_EVALUATION.md             # 📖 对话级别评估详解
└── EVALUATION_COMPARISON.md                 # 📖 评估方法对比
```

## 🎯 核心功能

### 1. 数据提取与丰富化
- 从MIMIC-IV-ED提取完整患者档案
- 包含pain评分、用药、主诉、病史等
- 支持CEFR语言分级和医学术语标注

### 2. 患者模拟生成
- 基于真实患者数据生成模拟对话
- 支持人格、回忆力、语言水平配置
- 使用AutoGen框架实现医患对话

### 3. 三层评估系统 ⭐

#### 📊 Conversation-Level（对话级别）
- 评估6个维度：人格、语言、回忆、混乱度、临床真实性、回应适当性
- 评分：0-4分/维度

#### 🔍 Sentence-Level（句子级别）
- 使用NLI验证事实准确性
- **核心指标：Entail(%)** = 被档案entail的信息句子百分比
- 实现论文Equation 2的完整计算

#### 📋 Dialogue-Level（档案提取级别）
- 从对话提取患者档案并与真实档案对比
- **双重评分**（Persona-Aware模式）：
  - Extraction Score: 信息完整性
  - Role-Play Score: 人格一致性
- 解决评估悖论：低提取分+高角色分 = 真实挑战性患者

## 🚀 快速开始

### 前置要求

1. MIMIC-IV数据集放置在 `../../mimic_4/` 目录下：
   - `../../mimic_4/hosp/` - 结构化医院数据
   - `../../mimic_4/ed/` - **急诊科数据（必需）**
   - `../../mimic_4/note/` - 临床笔记数据

2. Python环境：
```bash
pip install pandas autogen tqdm
```

### 完整工作流程

```powershell
# Step 1: 提取患者数据
python extract_ed_patients_v2.py
python enrich_from_notes.py

# Step 2: 生成患者模拟对话
python paitent_sim_autogen_v3.py

# Step 3: 三层评估
# 3a. 对话级别评估（6维度）
python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_conversation.json

# 3b. 句子级别评估（Entail%）
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_sentence.json --sentence_level

# 3c. 档案提取评估（双重评分）
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --output_file eval_dialogue.json --dialogue_level

# Step 4: 生成 Table 1 (Persona Fidelity Evaluation)
python generate_table1.py --input evaluation_results.json --engine "deepseek-r1:8b"
```

## 📊 生成 Table 1: Persona Fidelity Evaluation

评估完成后，生成论文风格的Table 1汇总：

```powershell
# 生成Table 1（需要先完成Step 3a的批量评估）
python generate_table1.py --input evaluation_results.json --engine "deepseek-r1:8b"
```

**输出示例：**
```
Engine                               Personality     Language       Recall     Confused      Realism         Avg.
----------------------------------------------------------------------------------------------------
deepseek-r1:8b                              3.45         3.52         3.61         3.78         3.23         3.52
```

**保存文件：**
- `table1_persona_fidelity.txt` - 文本格式
- `table1_persona_fidelity.md` - Markdown格式

详见：[HOW_TO_GENERATE_TABLE1.md](HOW_TO_GENERATE_TABLE1.md)

## 📖 详细文档

- **[EVALUATION_FRAMEWORK.md](EVALUATION_FRAMEWORK.md)** - 完整三层评估框架说明
- **[DIALOGUE_LEVEL_EVALUATION.md](DIALOGUE_LEVEL_EVALUATION.md)** - 对话级别评估详解
- **[EVALUATION_COMPARISON.md](EVALUATION_COMPARISON.md)** - Persona-Aware vs Simple评估对比

## 🎯 评估系统快速参考

### Conversation-Level
```powershell
python Eval_sim.py --simulation_folder simulation_outputs --output_file results.json
```
**输出**: 6维度评分（0-4分），平均总分

### Sentence-Level  
```powershell
python Eval_sim.py --conversation_file patient.txt --output_file results.json --sentence_level
```
**输出**: Entail(%) = 事实准确句子百分比

### Dialogue-Level (Persona-Aware)
```powershell
python Eval_sim.py --conversation_file patient.txt --output_file results.json --dialogue_level
```
**输出**: 
- Extraction Score (1-4): 信息完整性
- Role-Play Score (1-4): 角色真实性

## 📊 数据提取说明

### 使用MIMIC-IV-ED数据（推荐）
```powershell
python extract_ed_patients_v2.py
python enrich_from_notes.py
```
- 从MIMIC-IV-ED获取**pain评分**和**ED medication**
- 从triage表获取**chiefcomplaint**
- **筛选条件**：只选择有discharge note且包含完整History of Present Illness的患者
- **保证100%患者有present_illness_positive**
- 平均只有**9-10个null字段**
- 输出：`ed_patient_records_enriched.json` ✅

**方式2：仅使用MIMIC-IV hospital数据（备用）**
```powershell
python extract_ed_patients.py
python enrich_from_notes.py
```
- 不包含pain和ED-specific数据
- 平均11-12个null字段

## 📊 数据字段说明

### 可获得的字段（约16-18个/患者）

#### 从结构化表中提取（9个字段）
- ✅ `age` - 年龄
- ✅ `gender` - 性别
- ✅ `race` - 种族
- ✅ `marital_status` - 婚姻状况
- ✅ `insurance` - 保险类型
- ✅ `diagnosis` - 主要诊断
- ✅ `medical_history` - 既往病史（次要诊断）
- ✅ `disposition` - 出院去向
- ✅ `arrival_transport` - 到达方式

#### 从MIMIC-IV-ED中提取（3个字段）⭐ 新增
- ✅ `pain` - 疼痛评分（0-10）
- ✅ `medication` - ED药物对账
- ✅ `chiefcomplaint` - 主诉（来自triage）

#### 从Discharge Notes中提取（最多5个字段）
- ✅ `allergies` - 过敏史
- ✅ `present_illness_positive` - 现病史（阳性）**[100%覆盖]**
- ✅ `present_illness_negative` - 现病史（阴性）**[56%覆盖]**
- ✅ `family_medical_history` - 家族史
- ✅ `pain` - 疼痛描述（如果notes中有，补充triage评分）

### ⚠️ 无法获得的字段（约9个）

**原因：MIMIC-IV中Social History部分被完全脱敏（替换为"___"）**

- ❌ `occupation` - 职业
- ❌ `tobacco` - 吸烟史
- ❌ `alcohol` - 饮酒史
- ❌ `living_situation` - 居住情况
- ❌ `exercise` - 运动习惯
- ❌ `illicit_drug` - 非法药物使用
- ❌ `sexual_history` - 性史
- ❌ `children` - 子女情况
- ❌ `medical_device` - 医疗设备

### 词汇字段（9个）
- `cefr_A1`, `cefr_A2`, `cefr_B1`, `cefr_B2`, `cefr_C1`, `cefr_C2`
- `med_A`, `med_B`, `med_C`

## 📈 数据质量统计

- **总患者数**：50个首次ED就诊患者
- **平均填充字段**：17-18个（27个非文档字段中）
- **平均空字段**：9-10个
- **最佳患者**：18/27字段有数据
- **有discharge note的患者**：100% (50/50) ⭐
- **有present_illness_positive的患者**：100% (50/50) ⭐
- **有present_illness_negative的患者**：56% (28/50)
- **有pain评分的患者**：约95%
- **有medication的患者**：约85%

## 🔍 数据来源表

| 数据表 | 用途 |
|--------|------|
| **MIMIC-IV Hospital** | |
| `admissions.csv.gz` | 入院信息、保险、出院去向 |
| `patients.csv.gz` | 患者demographics |
| `diagnoses_icd.csv.gz` | ICD诊断代码 |
| `d_icd_diagnoses.csv.gz` | ICD诊断描述 |
| `discharge.csv.gz` | 出院总结笔记 |
| **MIMIC-IV-ED** ⭐ | |
| `edstays.csv.gz` | ED就诊记录、race、arrival、disposition |
| `triage.csv.gz` | 分诊信息、**chiefcomplaint**、**pain评分** |
| `medrecon.csv.gz` | **ED药物对账** |

## 💡 数据限制与建议

### MIMIC-IV数据限制
1. **Social History完全脱敏**：为保护隐私，所有社会历史信息被替换为"___"
2. **部分患者缺少笔记**：约20%的ED患者没有discharge note
3. **药物信息不完整**：部分患者的处方记录缺失

### 解决方案建议
1. **接受限制**：使用现有14-15个真实字段，其余标记为"Not available"
2. **合成数据**：基于age、diagnosis等使用规则或LLM生成合理的Social History
3. **其他数据源**：寻找包含完整Social History的数据集

## 📝 输出格式

```json
[
  {
    "hadm_id": "patient_24356178",
    "age": 73,
    "gender": "M",
    "race": "White",
    "marital_status": "Married",
    "insurance": "Medicare",
    "occupation": null,
    "tobacco": null,
    "alcohol": null,
    "allergies": "No known drug allergies",
    "family_medical_history": "Mother with breast cancer...",
    "medical_history": "Acute diastolic heart failure; Defibrination syndrome...",
    "chiefcomplaint": "ABNORMAL LABS",
    "pain": "0/10 pain scale",
    "medication": "aspirin, Lipitor, omeprazole, levothyroxine, loratadine",
    "arrival_transport": "WALK IN",
    "disposition": "Admitted",
    "diagnosis": "Acute myeloid leukemia, without mention of having achieved remission",
    "present_illness_positive": "Patient presents with fatigue...",
    "present_illness_negative": "denies chest pain, nausea...",
    "cefr_A1": "vacation, describe, funny...",
    ...
  }
]
```

## 🔧 辅助脚本

- `check_social_history.py` - 检查Social History脱敏情况
- `analyze_available_info.py` - 分析discharge notes可用信息
- `summarize_results.py` - 统计最终数据质量

## 📚 参考资料

- [MIMIC-IV Documentation](https://mimic.mit.edu/docs/iv/)
- [MIMIC-IV-Note Documentation](https://mimic.mit.edu/docs/iv/modules/note/)
- 数据版本：MIMIC-IV v3.1, MIMIC-IV-Note v2.2


python extract_ed_patients_v2.py
python enrich_from_notes.py

--------------

python .\paitent_sim_autogen_v3.py

--------------
# 方法1：评估simulation_outputs文件夹中的所有txt文件（推荐）
python Eval_sim.py --simulation_folder simulation_outputs --output_file evaluation_results.json

# 方法2：如果不指定参数，默认评估当前目录下的simulation_outputs文件夹
python Eval_sim.py

# 方法3：评估单个txt文件
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt

# 方法4：评估JSON/JSONL格式的对话文件（兼容旧格式）
python Eval_sim.py --conversation_file conversations.json

python Eval_sim.py --simulation_folder simulation_outputs --output_file eval_results.json


# Conversation-level评估 (4分制)
python Eval_sim.py --simulation_folder simulation_outputs

# Sentence-level评估 (按论文方法)
python Eval_sim.py --conversation_file simulation_outputs/patient_28651902.txt --sentence_level --output_file sentence_eval.json

# 完整评估流程 table 2
python Eval_sim.py --simulation_folder simulation_outputs --output_file conv.json  # 对话级
python Eval_sim.py --conversation_file patient.txt --output_file sent.json --sentence_level  # 句子级（Entail%）
python Eval_sim.py --conversation_file patient.txt --output_file dial.json --dialogue_level  # 档案级（双重评分）


----- Table 3
# Step 1: 运行 dialogue-level 评估（会花1-2小时，因为要提取50个profile）
python Eval_sim.py --dialogue_level --simulation_folder simulation_outputs --output_file dialogue_evaluation_results.json

# Step 2: 生成 Table 3
python generate_table3.py --input dialogue_evaluation_results.json --engine "deepseek-r1:8b"


## Table 1: Persona Fidelity Evaluation

Evaluated on 50 conversations. Each criterion is rated on a 4-point scale (0-4).

| Engine | Personality | Language | Recall | Confused | Realism | Avg. |
|--------|-------------|----------|--------|----------|---------|------|
| deepseek-r1:8b | 3.40 | 3.38 | 3.22 | 3.53 | 3.19 | 3.34 |

✅ Text format saved to: table1_persona_fidelity.txt
✅ Markdown format saved to: table1_persona_fidelity.md