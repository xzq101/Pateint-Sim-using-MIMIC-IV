"""
Enrich patient records with information extracted from discharge notes
"""

import pandas as pd
import json
import re


def extract_section(text, start_key, end_keys):
    """Extract section between start_key and first occurrence of end_keys"""
    text_lower = text.lower()
    start_idx = text_lower.find(start_key.lower())
    
    if start_idx == -1:
        return None
    
    # Find first occurrence of any end key
    end_positions = [text_lower.find(key.lower()) for key in end_keys]
    valid_positions = [pos for pos in end_positions if pos > start_idx]
    
    if not valid_positions:
        return None
    
    end_idx = min(valid_positions)
    section = text[start_idx + len(start_key):end_idx]
    return section.replace('\n', ' ').strip()


def extract_note_sections(note_text):
    """Extract structured sections from discharge note"""
    sections = {}
    
    # Define section keys (based on note_preprocessing.py)
    section_map = {
        'Allergies': ('Allergies:', ['Attending:', 'Chief Complaint:', 'Major Surgical']),
        'Chief Complaint': ('Chief Complaint:', ['Major Surgical', 'History of Present Illness:']),
        'History of Present Illness': ('History of Present Illness:', ['Past Medical History:', 'PMH:']),
        'Past Medical History': ('Past Medical History:', ['Social History:', 'Family History:']),
        'Social History': ('Social History:', ['Family History:', 'Physical Exam:']),
        'Family History': ('Family History:', ['Physical Exam:', 'Pertinent Results:']),
        'Physical Exam': ('Physical Exam:', ['Pertinent Results:', 'Brief Hospital Course:', 'Discharge Medications:']),
        'Discharge Medications': ('Discharge Medications:', ['Discharge Disposition:', 'Discharge Diagnosis:', 'Discharge Condition:'])
    }
    
    for section_name, (start_key, end_keys) in section_map.items():
        sections[section_name] = extract_section(note_text, start_key, end_keys)
    
    return sections


def extract_from_social_history(social_text):
    """Extract structured fields from social history"""
    if not social_text:
        return {}
    
    text_lower = social_text.lower()
    fields = {}
    
    # Tobacco
    if 'never smok' in text_lower or 'non-smok' in text_lower or 'non smok' in text_lower or 'denies tobacco' in text_lower:
        fields['tobacco'] = 'Never smoker'
    elif 'quit' in text_lower and 'smok' in text_lower:
        match = re.search(r'quit.{0,30}(\d+)\s*(year|yr)', text_lower)
        if match:
            fields['tobacco'] = f'Former smoker (quit {match.group(1)} years ago)'
        else:
            fields['tobacco'] = 'Former smoker'
    elif 'former' in text_lower and 'smok' in text_lower:
        fields['tobacco'] = 'Former smoker'
    elif 'smok' in text_lower:
        # Extract pack-year if available
        match = re.search(r'(\d+)\s*pack', text_lower)
        if match:
            fields['tobacco'] = f'Current smoker ({match.group(1)} pack-years)'
        else:
            fields['tobacco'] = 'Current smoker'
    
    # Alcohol
    if 'no alcohol' in text_lower or 'denies alcohol' in text_lower or 'does not drink' in text_lower:
        fields['alcohol'] = 'No alcohol use'
    elif 'quit' in text_lower and 'alcohol' in text_lower:
        fields['alcohol'] = 'Former alcohol use'
    elif 'occasional' in text_lower and ('drink' in text_lower or 'alcohol' in text_lower):
        fields['alcohol'] = 'Occasional alcohol use'
    elif 'social' in text_lower and ('drink' in text_lower or 'alcohol' in text_lower):
        fields['alcohol'] = 'Social drinker'
    elif 'alcohol' in text_lower and ('abuse' in text_lower or 'depend' in text_lower or 'heavy' in text_lower):
        fields['alcohol'] = 'Alcohol abuse history'
    elif 'drink' in text_lower or 'etoh' in text_lower:
        fields['alcohol'] = 'Alcohol use'
    
    # Illicit drugs
    if 'no drug' in text_lower or 'denies drug' in text_lower or 'no illicit' in text_lower or 'no ivdu' in text_lower:
        fields['illicit_drug'] = 'No illicit drug use'
    elif 'drug' in text_lower and ('abuse' in text_lower or 'use' in text_lower):
        fields['illicit_drug'] = 'Drug use history'
    
    # Occupation
    occupation_patterns = [
        (r'retired\s+(\w+)', lambda m: f'Retired {m.group(1)}'),
        (r'works?\s+as\s+(?:a\s+)?(\w+(?:\s+\w+)?)', lambda m: m.group(1).title()),
        (r'employed\s+as\s+(?:a\s+)?(\w+(?:\s+\w+)?)', lambda m: m.group(1).title()),
        (r'\b(teacher|nurse|engineer|manager|construction worker|driver|student|homemaker|disabled|unemployed|retired)\b', 
         lambda m: m.group(1).title())
    ]
    
    for pattern, formatter in occupation_patterns:
        match = re.search(pattern, text_lower)
        if match:
            fields['occupation'] = formatter(match)
            break
    
    # Living situation
    if 'lives with' in text_lower:
        match = re.search(r'lives with ([\w\s,]+?)(?:\.|in |at |$)', text_lower)
        if match:
            living_with = match.group(1).strip().rstrip(',')
            fields['living_situation'] = f'Lives with {living_with}'
    elif 'lives alone' in text_lower:
        fields['living_situation'] = 'Lives alone'
    elif 'nursing home' in text_lower or 'nursing facility' in text_lower or 'snf' in text_lower:
        fields['living_situation'] = 'Nursing facility'
    elif 'assisted living' in text_lower:
        fields['living_situation'] = 'Assisted living'
    
    return fields


def extract_from_other_sections(sections):
    """Extract fields from other note sections"""
    fields = {}
    
    # Chief complaint
    if sections.get('Chief Complaint'):
        cc = sections['Chief Complaint'].strip()
        # Clean up common patterns
        cc = re.sub(r'^\s*:\s*', '', cc)
        cc = re.sub(r'\s+', ' ', cc)
        if len(cc) > 5 and len(cc) < 200:
            fields['chiefcomplaint'] = cc
    
    # Allergies
    if sections.get('Allergies'):
        allergy_text = sections['Allergies'].lower().strip()
        if 'nkda' in allergy_text or 'no known drug allergies' in allergy_text:
            fields['allergies'] = 'No known drug allergies'
        elif 'nka' in allergy_text or 'no known allergies' in allergy_text:
            fields['allergies'] = 'No known allergies'
        elif len(allergy_text) > 5:
            # Extract actual allergies
            allergy_clean = sections['Allergies'][:200].strip()
            fields['allergies'] = allergy_clean
    
    # Family history
    if sections.get('Family History'):
        fh = sections['Family History'].strip()
        if 'non-contrib' not in fh.lower() and 'unknown' not in fh.lower() and len(fh) > 10:
            fields['family_medical_history'] = fh[:300]
    
    # History of present illness
    if sections.get('History of Present Illness'):
        hpi = sections['History of Present Illness']
        
        # Positive findings
        if len(hpi) > 10:
            fields['present_illness_positive'] = hpi[:400]
        
        # Negative findings
        negatives = []
        hpi_lower = hpi.lower()
        
        # Look for denial patterns with more flexible matching
        denial_patterns = [
            r'denies[^.!?]{5,150}[.!?]',  # More flexible
            r'denied[^.!?]{5,150}[.!?]',
            r'no\s+\w+(?:\s+\w+){0,8}[,.]',  # Match "no X" patterns
            r'negative for[^.!?]{5,100}[.!?]',
            r'without\s+\w+(?:\s+\w+){0,8}[,.]',
            r'absent[^.!?]{5,100}[.!?]',
            r'reports no[^.!?]{5,100}[.!?]',
        ]
        
        for pattern in denial_patterns:
            matches = re.findall(pattern, hpi_lower)
            for match in matches[:3]:  # Take up to 3 matches per pattern
                clean = match.strip()
                if len(clean) > 10:  # Avoid very short matches
                    negatives.append(clean)
        
        if negatives:
            # Deduplicate and combine
            unique_negatives = []
            seen = set()
            for neg in negatives:
                if neg[:30] not in seen:  # Check first 30 chars to avoid duplicates
                    unique_negatives.append(neg)
                    seen.add(neg[:30])
            fields['present_illness_negative'] = ' '.join(unique_negatives[:3])[:300]
        elif any(keyword in hpi_lower for keyword in ['denies', 'denied', 'no ', 'negative', 'without']):
            # If we found negative keywords but no matches, provide a generic statement
            fields['present_illness_negative'] = 'Patient denies relevant negative symptoms (see full HPI)'
    
    # Discharge Medications
    if sections.get('Discharge Medications'):
        meds_text = sections['Discharge Medications'].strip()
        if len(meds_text) > 10 and meds_text != '___':
            # Extract medication names (numbered list format)
            med_lines = []
            for line in meds_text.split('\n')[:15]:  # Take first 15 medications
                line = line.strip()
                # Match numbered medication lines like "1. Acetaminophen 500 mg PO Q6H"
                match = re.match(r'\d+\.\s+([A-Za-z][A-Za-z\s\-]+?)(?:\s+\d+|\s+PO|\s+IV|\s+\(|$)', line)
                if match:
                    med_name = match.group(1).strip()
                    if len(med_name) > 2:
                        med_lines.append(med_name)
            
            if med_lines:
                fields['medication'] = ', '.join(med_lines[:10])  # Max 10 medications
    
    # Medical devices - search in PMH and throughout note
    device_info = extract_medical_devices(sections)
    if device_info:
        fields['medical_device'] = device_info
    
    return fields


def extract_medical_devices(sections):
    """Extract medical device information from note sections"""
    # Common medical devices
    device_keywords = {
        'pacemaker': 'Pacemaker',
        'icd': 'Implantable cardioverter-defibrillator (ICD)',
        'aicd': 'Automatic implantable cardioverter-defibrillator',
        'defibrillator': 'Defibrillator',
        'coronary stent': 'Coronary stent',
        'cardiac stent': 'Cardiac stent',
        'stent': 'Stent',
        'prosthetic valve': 'Prosthetic heart valve',
        'artificial valve': 'Artificial heart valve',
        'insulin pump': 'Insulin pump',
        'g-tube': 'Gastrostomy tube (G-tube)',
        'j-tube': 'Jejunostomy tube (J-tube)',
        'peg tube': 'PEG tube',
        'feeding tube': 'Feeding tube',
        'tracheostomy': 'Tracheostomy',
        'trach': 'Tracheostomy',
        'colostomy': 'Colostomy',
        'ileostomy': 'Ileostomy',
        'ostomy': 'Ostomy',
        'port-a-cath': 'Port-a-cath',
        'mediport': 'Mediport',
        'picc line': 'PICC line',
        'central line': 'Central line',
        'foley catheter': 'Foley catheter',
        'foley': 'Foley catheter',
        'home oxygen': 'Home oxygen',
        'cpap': 'CPAP',
        'bipap': 'BiPAP',
    }
    
    # Search in Past Medical History first
    search_text = ''
    if sections.get('Past Medical History'):
        search_text = sections['Past Medical History'].lower()
    
    # Also search in History of Present Illness
    if sections.get('History of Present Illness'):
        search_text += ' ' + sections['History of Present Illness'].lower()
    
    if not search_text:
        return "None"
    
    # Find all matching devices
    found_devices = []
    for keyword, device_name in device_keywords.items():
        if keyword.lower() in search_text:
            # Avoid duplicates (e.g., "stent" and "coronary stent")
            if not any(d.lower() in device_name.lower() for d in found_devices):
                found_devices.append(device_name)
    
    if found_devices:
        # Return up to 3 devices
        return ', '.join(found_devices[:3])
    
    return "None"
    pain_info = extract_pain_info(sections)
    if pain_info:
        fields['pain'] = pain_info
    
    return fields


def extract_pain_info(sections):
    """Extract pain information from note sections"""
    # Search in Chief Complaint, HPI, and Physical Exam
    search_sections = []
    if sections.get('Chief Complaint'):
        search_sections.append(sections['Chief Complaint'])
    if sections.get('History of Present Illness'):
        search_sections.append(sections['History of Present Illness'])
    if sections.get('Physical Exam'):
        search_sections.append(sections['Physical Exam'])
    
    combined_text = ' '.join(search_sections).lower()
    
    # Pattern 1: Pain scale (e.g., "8/10 pain", "pain 7/10")
    pain_scale_match = re.search(r'(\d+)/10\s*pain|pain\s*(\d+)/10', combined_text)
    if pain_scale_match:
        score = pain_scale_match.group(1) or pain_scale_match.group(2)
        return f"{score}/10 pain scale"
    
    # Pattern 2: Verbal pain descriptions
    if 'severe pain' in combined_text or 'worst pain' in combined_text:
        return "Severe pain reported"
    elif 'moderate pain' in combined_text:
        return "Moderate pain reported"
    elif 'mild pain' in combined_text or 'minimal pain' in combined_text:
        return "Mild pain reported"
    
    # Pattern 3: Pain denial
    if 'denies pain' in combined_text or 'no pain' in combined_text or 'pain-free' in combined_text:
        return "Denies pain"
    
    # Pattern 4: Specific pain locations with descriptors
    pain_descriptors = re.findall(r'(sharp|dull|stabbing|burning|aching|throbbing|cramping)\s+pain', combined_text)
    if pain_descriptors:
        return f"{pain_descriptors[0].capitalize()} pain reported"
    
    return None


def load_discharge_notes(hadm_ids, note_path='../../mimic_4/note/discharge.csv.gz'):
    """Load discharge notes for specified admissions"""
    print(f"Loading discharge notes from {note_path}...")
    
    notes_df = pd.read_csv(note_path)
    print(f"Loaded {len(notes_df)} total discharge notes")
    
    # Filter for our admissions
    notes_df = notes_df[notes_df['hadm_id'].isin(hadm_ids)]
    print(f"Found notes for {len(notes_df)} out of {len(hadm_ids)} admissions")
    
    return notes_df


def enrich_patient_records(patient_records, notes_df):
    """Enrich patient records with information from notes"""
    enriched_records = []
    
    for i, record in enumerate(patient_records, 1):
        # Extract hadm_id
        hadm_id = int(record['hadm_id'].replace('patient_', ''))
        
        # Find matching note
        note_rows = notes_df[notes_df['hadm_id'] == hadm_id]
        
        if len(note_rows) == 0:
            print(f"  Patient {i}: No note found")
            enriched_records.append(record)
            continue
        
        # Take first note if multiple
        note_text = note_rows.iloc[0]['text']
        
        # Extract sections
        sections = extract_note_sections(note_text)
        
        # Count nulls before
        exclude_fields = ['hadm_id', 'cefr_A1', 'cefr_A2', 'cefr_B1', 'cefr_B2', 'cefr_C1', 'cefr_C2', 'med_A', 'med_B', 'med_C']
        nulls_before = sum(1 for k, v in record.items() if k not in exclude_fields and v is None)
        
        # Extract from social history
        if sections.get('Social History'):
            social_fields = extract_from_social_history(sections['Social History'])
            for key, value in social_fields.items():
                if record.get(key) is None:
                    record[key] = value
        
        # Extract from other sections
        other_fields = extract_from_other_sections(sections)
        for key, value in other_fields.items():
            if record.get(key) is None:
                record[key] = value
        
        # Count nulls after
        nulls_after = sum(1 for k, v in record.items() if k not in exclude_fields and v is None)
        filled = nulls_before - nulls_after
        
        if filled > 0:
            print(f"  Patient {i}: Filled {filled} fields (nulls: {nulls_before} → {nulls_after})")
        else:
            print(f"  Patient {i}: No additional fields filled")
        
        enriched_records.append(record)
    
    return enriched_records


def main():
    print("="*80)
    print("Enriching Patient Records from Discharge Notes")
    print("="*80)
    
    # Load existing patient records
    print("\n1. Loading existing patient records...")
    with open('ed_patient_records.json', 'r', encoding='utf-8') as f:
        patient_records = json.load(f)
    print(f"   Loaded {len(patient_records)} patient records")
    
    # Get hadm_ids
    hadm_ids = [int(r['hadm_id'].replace('patient_', '')) for r in patient_records]
    
    # Load discharge notes
    print("\n2. Loading discharge notes...")
    notes_df = load_discharge_notes(hadm_ids)
    
    if len(notes_df) == 0:
        print("\n❌ No discharge notes found!")
        return
    
    # Enrich records
    print("\n3. Extracting information from notes...")
    enriched_records = enrich_patient_records(patient_records, notes_df)
    
    # Save enriched records
    output_file = 'ed_patient_records_enriched.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_records, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"✓ Saved enriched records to {output_file}")
    
    # Summary statistics
    print("\n4. Summary:")
    exclude_fields = ['hadm_id', 'cefr_A1', 'cefr_A2', 'cefr_B1', 'cefr_B2', 'cefr_C1', 'cefr_C2', 'med_A', 'med_B', 'med_C']
    
    total_orig_nulls = 0
    total_enriched_nulls = 0
    
    for orig, enriched in zip(patient_records, enriched_records):
        orig_nulls = sum(1 for k, v in orig.items() if k not in exclude_fields and v is None)
        enriched_nulls = sum(1 for k, v in enriched.items() if k not in exclude_fields and v is None)
        total_orig_nulls += orig_nulls
        total_enriched_nulls += enriched_nulls
    
    total_filled = total_orig_nulls - total_enriched_nulls
    print(f"   Total null fields before: {total_orig_nulls}")
    print(f"   Total null fields after: {total_enriched_nulls}")
    print(f"   Total fields filled: {total_filled}")
    print(f"   Average nulls per patient: {total_enriched_nulls / len(enriched_records):.1f}")
    print("="*80)


if __name__ == "__main__":
    main()
