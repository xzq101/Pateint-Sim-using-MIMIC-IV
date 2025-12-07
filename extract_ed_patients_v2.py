"""
Extract first-time ED visit patients from MIMIC-IV-ED data
Enhanced version using MIMIC-IV-ED for pain, chiefcomplaint, and medication data
"""

import pandas as pd
import json
import numpy as np
from load_mimic4_data import MIMIC4DataLoader


def get_first_ed_visits_enhanced(loader, n_patients=50, n_candidates=1000):
    """
    Get first ED visits with enhanced data from MIMIC-IV-ED
    Filter for patients with discharge notes containing present illness information
    """
    print("="*80)
    print("Loading MIMIC-IV and MIMIC-IV-ED data...")
    print("="*80)
    
    # Load hospital data
    admissions = loader.load_admissions()
    patients = loader.load_patients()
    diagnoses_icd = loader.load_diagnoses_icd()
    d_icd_diagnoses = loader.load_d_icd_diagnoses()
    
    # Load discharge notes to filter for patients with present illness
    print("Loading discharge notes for filtering...")
    try:
        import os
        note_path = '../../mimic_4/note/discharge.csv.gz'
        notes_df = pd.read_csv(note_path)
        print(f"Loaded {len(notes_df)} discharge notes")
        has_notes = True
    except Exception as e:
        print(f"⚠️  Could not load discharge notes: {e}")
        print("   Cannot filter for present illness information")
        has_notes = False
    
    # Load ED-specific data
    try:
        edstays = loader.load_ed_stays()
        triage = loader.load_ed_triage()
        medrecon = loader.load_ed_medrecon()
        has_ed_data = True
        print("✓ ED data loaded successfully")
    except Exception as e:
        print(f"⚠️  ED data not available: {e}")
        print("   Please ensure ../../mimic_4/ed/ directory exists with:")
        print("   - edstays.csv.gz")
        print("   - triage.csv.gz")
        print("   - medrecon.csv.gz")
        return None, None, None
    
    # Calculate age
    admissions = admissions.merge(
        patients[['subject_id', 'gender', 'anchor_age', 'anchor_year']], 
        on='subject_id'
    )
    admissions['admit_year'] = pd.to_datetime(admissions['admittime']).dt.year
    admissions['age_at_admission'] = admissions['anchor_age'] + (
        admissions['admit_year'] - admissions['anchor_year']
    )
    
    # Merge with ED stays
    print(f"\nMerging admissions with ED stays...")
    ed_data = admissions.merge(
        edstays[['subject_id', 'hadm_id', 'stay_id', 'race', 'arrival_transport', 'disposition']],
        on=['subject_id', 'hadm_id'],
        how='inner',
        suffixes=('_hosp', '_ed')
    )
    print(f"ED admissions with stays: {len(ed_data)}")
    
    # Use ED race if available, fallback to hospital race
    if 'race_ed' in ed_data.columns:
        ed_data['race'] = ed_data['race_ed'].fillna(ed_data.get('race_hosp', ''))
    elif 'race_hosp' in ed_data.columns:
        ed_data['race'] = ed_data['race_hosp']
    
    # Merge with triage (pain and chiefcomplaint)
    ed_data = ed_data.merge(
        triage[['stay_id', 'chiefcomplaint', 'pain']],
        on='stay_id',
        how='left'
    )
    print(f"After triage merge: {len(ed_data)}")
    
    # Merge with medication reconciliation
    print("Processing medication reconciliation...")
    medrecon_grouped = medrecon.groupby('stay_id')['name'].apply(
        lambda x: ', '.join(x.dropna().unique()[:10])
    ).reset_index()
    medrecon_grouped.columns = ['stay_id', 'ed_medications']
    ed_data = ed_data.merge(medrecon_grouped, on='stay_id', how='left')
    print(f"After medrecon merge: {len(ed_data)}")
    
    # Apply filters
    print(f"\n{'='*80}")
    print("Applying filters...")
    print(f"{'='*80}")
    
    # Age filter
    ed_data = ed_data[
        (ed_data['age_at_admission'] >= 18) & 
        (ed_data['age_at_admission'] <= 89)
    ]
    print(f"After age filter (18-89): {len(ed_data)}")
    
    # Gender filter
    ed_data = ed_data[ed_data['gender'].isin(['M', 'F'])]
    print(f"After gender filter: {len(ed_data)}")
    
    # Race filter
    ed_data = ed_data[
        (ed_data['race'].notna()) & 
        (ed_data['race'] != 'UNKNOWN') &
        (ed_data['race'] != 'UNABLE TO OBTAIN') &
        (~ed_data['race'].str.contains('PATIENT DECLINED', na=False))
    ]
    print(f"After race filter: {len(ed_data)}")
    
    # Marital status filter
    ed_data = ed_data[ed_data['marital_status'].notna()]
    print(f"After marital status filter: {len(ed_data)}")
    
    # Insurance filter
    ed_data = ed_data[ed_data['insurance'].notna()]
    print(f"After insurance filter: {len(ed_data)}")
    
    # Chief complaint filter
    ed_data = ed_data[
        (ed_data['chiefcomplaint'].notna()) &
        (~ed_data['chiefcomplaint'].str.lower().str.contains(
            'transfer|ams|altered mental status|confusion|slurred speech|dysarthria|aphasia',
            na=False
        ))
    ]
    print(f"After chiefcomplaint filter: {len(ed_data)}")
    
    # Pain filter (0-10 or null)
    ed_data['pain'] = pd.to_numeric(ed_data['pain'], errors='coerce')
    ed_data = ed_data[
        (ed_data['pain'].isna()) | 
        ((ed_data['pain'] >= 0) & (ed_data['pain'] <= 10))
    ]
    print(f"After pain filter (0-10 or null): {len(ed_data)}")
    
    # Get first ED visit per patient
    print(f"\nFinding first ED visit per patient...")
    ed_data = ed_data.sort_values(['subject_id', 'admittime'])
    first_visits = ed_data.groupby('subject_id').first().reset_index()
    print(f"First ED visits: {len(first_visits)}")
    
    # Filter for patients with discharge notes containing HPI
    if has_notes:
        print(f"\nFiltering for patients with History of Present Illness in notes...")
        # Get notes for these admissions
        candidate_notes = notes_df[notes_df['hadm_id'].isin(first_visits['hadm_id'])].copy()
        
        # Check for HPI section
        candidate_notes['has_hpi'] = candidate_notes['text'].str.contains(
            'History of Present Illness:', 
            case=False, 
            na=False
        )
        
        # Check that HPI section has substantial content (>50 chars)
        def check_hpi_content(text):
            if pd.isna(text) or 'History of Present Illness:' not in text:
                return False
            try:
                import re
                match = re.search(
                    r'History of Present Illness:\s*\n(.*?)(?:\nPast Medical History:|\nPMH:)',
                    text,
                    re.DOTALL | re.IGNORECASE
                )
                if match:
                    hpi_text = match.group(1).strip()
                    return len(hpi_text) > 50
            except:
                pass
            return False
        
        candidate_notes['has_hpi_content'] = candidate_notes['text'].apply(check_hpi_content)
        
        valid_hadm_ids = candidate_notes[candidate_notes['has_hpi_content']]['hadm_id'].unique()
        
        print(f"  Admissions with discharge notes: {len(candidate_notes)}")
        print(f"  Admissions with HPI section: {candidate_notes['has_hpi'].sum()}")
        print(f"  Admissions with substantial HPI content: {len(valid_hadm_ids)}")
        
        # Filter first_visits to only include those with valid HPI
        first_visits = first_visits[first_visits['hadm_id'].isin(valid_hadm_ids)]
        print(f"  Filtered to patients with HPI: {len(first_visits)}")
        
        if len(first_visits) == 0:
            print("\n❌ No patients found with substantial HPI content!")
            return None, None, None
    
    # Sample n_candidates
    if len(first_visits) > n_candidates:
        first_visits = first_visits.sample(n=n_candidates, random_state=42)
        print(f"\nSampled {n_candidates} candidates with HPI")
    
    # Get diagnoses
    print(f"\nLoading diagnoses...")
    visit_diagnoses = diagnoses_icd[diagnoses_icd['hadm_id'].isin(first_visits['hadm_id'])]
    visit_diagnoses = visit_diagnoses.merge(
        d_icd_diagnoses[['icd_code', 'icd_version', 'long_title']], 
        on=['icd_code', 'icd_version']
    )
    print(f"Diagnoses loaded: {len(visit_diagnoses)}")
    
    return first_visits, visit_diagnoses, None


def create_patient_records_enhanced(selected_visits, visit_diagnoses, vocab_words):
    """Create patient records with ED data"""
    
    # Value mappings
    race_mapping = {
        'WHITE': 'White',
        'BLACK/AFRICAN AMERICAN': 'Black or African American',
        'HISPANIC/LATINO': 'Hispanic or Latino',
        'ASIAN': 'Asian',
        'OTHER': 'Other',
    }
    
    insurance_mapping = {
        'Medicare': 'Medicare',
        'Medicaid': 'Medicaid',
        'Other': 'Private insurance',
    }
    
    marital_mapping = {
        'MARRIED': 'Married',
        'SINGLE': 'Single',
        'DIVORCED': 'Divorced',
        'WIDOWED': 'Widowed',
        'SEPARATED': 'Separated',
    }
    
    patient_records = []
    
    print(f"\n{'='*80}")
    print(f"Creating patient records...")
    print(f"{'='*80}")
    
    for idx, row in selected_visits.iterrows():
        hadm_id = row['hadm_id']
        
        # Get diagnoses
        patient_diags = visit_diagnoses[visit_diagnoses['hadm_id'] == hadm_id]
        primary_diagnosis = patient_diags[patient_diags['seq_num'] == 1]['long_title'].values
        diagnosis_text = primary_diagnosis[0] if len(primary_diagnosis) > 0 else None
        
        # Medical history from secondary diagnoses
        secondary_diags = patient_diags[patient_diags['seq_num'] > 1]['long_title'].values
        medical_history_text = None
        if len(secondary_diags) > 0:
            medical_history_text = '; '.join(secondary_diags[:5])
        
        # Get ED medications
        medication_text = row.get('ed_medications')
        if pd.isna(medication_text) or medication_text == '':
            medication_text = None
        
        # Get pain score
        pain_value = row.get('pain')
        pain_text = None
        if pd.notna(pain_value):
            pain_text = f"{int(pain_value)}/10 pain scale"
        
        # Get chiefcomplaint
        chiefcomplaint_text = row.get('chiefcomplaint')
        if pd.isna(chiefcomplaint_text):
            chiefcomplaint_text = None
        
        # Map values
        race = race_mapping.get(row['race'], row['race']) if pd.notna(row['race']) else None
        insurance = insurance_mapping.get(row['insurance'], 'Private insurance') if pd.notna(row['insurance']) else None
        marital = marital_mapping.get(row['marital_status'], row['marital_status']) if pd.notna(row['marital_status']) else None
        arrival = row.get('arrival_transport', 'Emergency Room')
        disposition = row.get('disposition', row.get('discharge_location'))
        if pd.notna(disposition):
            disposition = disposition.replace('_', ' ').title()
        
        # Create record
        record = {
            "hadm_id": f"patient_{int(hadm_id)}",
            "age": int(row['age_at_admission']) if pd.notna(row['age_at_admission']) else None,
            "gender": row['gender'].capitalize() if pd.notna(row['gender']) else None,
            "race": race,
            "marital_status": marital,
            "insurance": insurance,
            "occupation": None,  # Not available in MIMIC
            "living_situation": None,
            "children": None,
            "exercise": None,
            "tobacco": None,  # Social History redacted
            "alcohol": None,
            "illicit_drug": None,
            "sexual_history": None,
            "allergies": None,  # Will be filled from notes
            "family_medical_history": None,
            "medical_device": None,
            "medical_history": medical_history_text,
            "chiefcomplaint": chiefcomplaint_text,
            "pain": pain_text,
            "medication": medication_text,
            "arrival_transport": arrival,
            "disposition": disposition,
            "diagnosis": diagnosis_text,
            "present_illness_positive": None,  # Will be filled from notes
            "present_illness_negative": None,
            "cefr_A1": vocab_words['cefr_A1'],
            "cefr_A2": vocab_words['cefr_A2'],
            "cefr_B1": vocab_words['cefr_B1'],
            "cefr_B2": vocab_words['cefr_B2'],
            "cefr_C1": vocab_words['cefr_C1'],
            "cefr_C2": vocab_words['cefr_C2'],
            "med_A": vocab_words['med_A'],
            "med_B": vocab_words['med_B'],
            "med_C": vocab_words['med_C']
        }
        
        patient_records.append(record)
    
    return patient_records


def main():
    # Initialize loader with ED directory
    loader = MIMIC4DataLoader(
        data_dir='../../mimic_4/hosp',
        ed_dir='../../mimic_4/ed'
    )
    
    # Vocabulary words
    vocab_words = {
        "cefr_A1": "vacation, describe, funny, dirty, easy, page, apron, eighteen, leader, p.m./p.m./pm/pm, goal, hair, difficult, child, must, bath, river, foggy, fairy, real",
        "cefr_A2": "hunter, without, proper, choice, physically, uneasy, image, cheque, appearance, bench, extremely, convenience, complain, hardly, reveal, nervous, sauce, weekday, scientific, journey",
        "cefr_B1": "sickness, organization/organisation, unexpectedly, resolve, deed, signature, shame, slogan, desperate, favorable/favourable, furthermore, virus, edition, mathematician, referee, impressive, emperor, aside, attract, gown",
        "cefr_B2": "owing to, mango, tricky, exclusion, compress, kangaroo, preferably, revenue, pillowcase, inexperienced, edit, urban, rubble, humanize/humanise, dissident, scientifically, retina, repression, sprint, understanding",
        "cefr_C1": "tranquil, viciously, dramatist, stretching, dutifully, exotically, compromised, impersonator, claustrophobia, provisions, beforehand, collaboration, chiselled, preach, connoisseur, appliance, reenact, beguilingly, trampoline, darkroom",
        "cefr_C2": "edification, ingenuous, interrogation, opulently, telescopic, magnanimity, confrontational, integration, verily, unexceptional, tetchy, minster, lament, clinch, tenaciously, embed, disseminate, ephemeral, incongruous, porten",
        "med_A": "neck, back, healthy, patient, pain, fever, sleep, hospital, eye, doctor, medicine, arm, clinic, nurse, body, headache, ambulance, rest, foot, head",
        "med_B": "allergy, vitamins, surgeon, glucose, bruise, diabetes, diagnosis, throat, disease, antibiotics, sore, dull, emergency, referral, prescription, prevention, cholesterol, heart disease, bacteria, sneeze",
        "med_C": "psychosomatic, anesthesia, psychiatry, endocrinology, iatrogenic, dermatologist, constipation, pathophysiology, pharmacodynamics, nephrology, immunization, hyperglycemia, arrhythmia, metastasis, electrocardiogram, echocardiogram, intravenous, hemorrhage, prophylaxis, tomography"
    }
    
    # Get ED visits
    candidates, visit_diagnoses, _ = get_first_ed_visits_enhanced(
        loader, 
        n_patients=50, 
        n_candidates=1000
    )
    
    if candidates is None:
        print("\n❌ Failed to load ED data. Please check data directory.")
        return
    
    # Create all records
    all_records = create_patient_records_enhanced(candidates, visit_diagnoses, vocab_words)
    
    # Count nulls and select best
    exclude_fields = ['hadm_id', 'cefr_A1', 'cefr_A2', 'cefr_B1', 'cefr_B2', 'cefr_C1', 'cefr_C2', 'med_A', 'med_B', 'med_C']
    
    print(f"\n{'='*80}")
    print("Analyzing data completeness...")
    print(f"{'='*80}")
    
    records_with_nulls = []
    for record in all_records:
        non_doc_fields = {k: v for k, v in record.items() if k not in exclude_fields}
        null_count = sum(1 for v in non_doc_fields.values() if v is None)
        records_with_nulls.append((null_count, record))
    
    records_with_nulls.sort(key=lambda x: x[0])
    
    null_counts = [x[0] for x in records_with_nulls]
    print(f"\nNull count statistics:")
    print(f"  Min: {min(null_counts)}, Max: {max(null_counts)}, Avg: {sum(null_counts)/len(null_counts):.1f}")
    print(f"  Patients with <15 nulls: {sum(1 for n in null_counts if n < 15)}")
    print(f"  Patients with <16 nulls: {sum(1 for n in null_counts if n < 16)}")
    
    # Take top 50
    good_records = [record for _, record in records_with_nulls[:50]]
    
    print(f"\n{'='*80}")
    print(f"Selected {len(good_records)} patients with most complete data")
    print(f"{'='*80}")
    
    # Show summary
    for i, record in enumerate(good_records[:5], 1):
        non_doc_fields = {k: v for k, v in record.items() if k not in exclude_fields}
        null_count = sum(1 for v in non_doc_fields.values() if v is None)
        filled_count = len(non_doc_fields) - null_count
        
        print(f"\nPatient {i} ({record['hadm_id']}):")
        print(f"  Filled: {filled_count}/27, Nulls: {null_count}/27")
        print(f"  Age: {record['age']}, Gender: {record['gender']}, Pain: {record['pain']}")
        if record['chiefcomplaint']:
            cc = record['chiefcomplaint'][:60]
            print(f"  Chief Complaint: {cc}...")
    
    # Save
    output_file = 'ed_patient_records.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(good_records, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✓ Saved {len(good_records)} patient records to {output_file}")
    print(f"{'='*80}")
    
    return good_records


if __name__ == "__main__":
    records = main()
