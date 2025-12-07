"""
PatientSim with AutoGen Framework
Based on the paper "PATIENTSIM: A Persona-Driven Simulator for Realistic Doctor-Patient Interactions"
Implementation of patient-doctor dialogue simulation system using AutoGen framework
"""
import os
import json
import random
#from google import genai
import google.generativeai as genai

from dotenv import load_dotenv

from typing import Dict, Any, Optional, List
import autogen
from autogen import AssistantAgent, UserProxyAgent, Agent

# Load environment variables from .env file
load_dotenv()

 


# ===== Configuration Section =====
def load_config(use_google: bool = False) -> Dict[str, Any]:
    """
    Load configuration, supports reading API Key from environment variables or config file
    Can choose to use Google Gemini or local DeepSeek R1 14B model
    
    Args:
        use_google: If True, use Google Gemini API; otherwise use local DeepSeek model
    """
    config_list = []
    
    if use_google:
        # Use Google Gemini API
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        config_list = [
            {
                "model": "gemini-1.5-flash",  # or "gemini-1.5-pro", "gemini-1.5-flash"
                "api_key": google_api_key,
                "api_type": "google",
            }
        ]
    else:
        # Use local DeepSeek R1 8B model
        api_key = os.environ.get("OPENAI_API_KEY", "not-needed")
        
        config_list = [
            {
                "model": "deepseek-r1:8b",  # Local DeepSeek R1 14B model
                "api_key": api_key,
                "base_url": "http://localhost:11434/v1",  # Ollama default address
                # If using other local services, modify to corresponding address, for example:
                # "base_url": "http://localhost:8000/v1",  # vLLM
                # "base_url": "http://localhost:5000/v1",  # LM Studio
            }
        ]
    
    llm_config = {
        "config_list": config_list,
        "temperature": 0.7,  # Paper recommends temp=0.7 to ensure diversity
        "timeout": 120,
    }
    
    return llm_config


# ===== Data Structure Definitions =====
def get_default_patient_profile() -> Dict[str, Any]:
    """
    Simulated patient clinical profile (Clinical Profile)
    Reference: Paper Figure 1 and Table A1
    """
    return {
        "demographics": {
            "age": 77,
            "gender": "Female",
            "race": "White",
            "occupation": "Retired teacher",
            "living_situation": "Lives with husband"
        },
        "chief_complaint": "Dyspnea (Shortness of breath), Cough",
        "history_of_present_illness": "Patient reports feeling tired with no appetite. Fevers and chills present. Terrible headaches.",
        "pain_level": 10,  # 0-10
        "medical_history": "Hypertension, Hyperlipidemia",
        "medications": "Lisinopril, Atorvastatin",
        "diagnosis": "Pneumonia"  # Hidden information, used to guide symptom description
    }


def get_default_persona_config() -> Dict[str, str]:
    """
    Define Persona configuration (The 4 Axes)
    Reference: Paper Table B3 - B6
    """
    return {
        "personality": "Overanxious",      # Options: Neutral, Impatient, Distrustful, Overanxious
        "language_proficiency": "Basic",   # Options: Basic (A), Intermediate (B), Advanced (C)
        "recall_level": "High",            # Options: Low, High
        "confusion_level": "Normal"        # Options: Normal, Highly Confused
    }


# ===== Prompt Generation Functions =====
def generate_patient_system_message(profile: Dict[str, Any], persona: Dict[str, str]) -> str:
    """
    Construct PatientSim system prompt based on paper Appendix C and agent/patient_agent.py
    """
    
    # Language proficiency mapping: Convert A/B/C to Basic/Intermediate/Advanced
    language_mapping = {
        'A': 'Basic',
        'B': 'Intermediate', 
        'C': 'Advanced',
        'Basic': 'Basic',
        'Intermediate': 'Intermediate',
        'Advanced': 'Advanced'
    }
    
    # Confusion level mapping: Convert none/high to Normal/Highly Confused
    confusion_mapping = {
        'none': 'Normal',
        'high': 'Highly Confused',
        'Normal': 'Normal',
        'Highly Confused': 'Highly Confused'
    }
    
    # Personality mapping: Standardize lowercase to capitalized
    personality_mapping = {
        'plain': 'Neutral',
        'verbose': 'Verbose',
        'pleasing': 'Pleasing',
        'impatient': 'Impatient',
        'distrust': 'Distrustful',
        'overanxious': 'Overanxious',
        'Neutral': 'Neutral',
        'Verbose': 'Verbose',
        'Pleasing': 'Pleasing',
        'Impatient': 'Impatient',
        'Distrustful': 'Distrustful',
        'Overanxious': 'Overanxious'
    }
    
    # Recall ability mapping: Standardize lowercase to capitalized
    recall_mapping = {
        'low': 'Low',
        'high': 'High',
        'Low': 'Low',
        'High': 'High'
    }
    
    # Apply mapping
    persona_normalized = {
        'personality': personality_mapping.get(persona.get('personality', 'plain'), 'Neutral'),
        'language_proficiency': language_mapping.get(persona.get('language_proficiency', 'A'), 'Basic'),
        'recall_level': recall_mapping.get(persona.get('recall_level', 'high'), 'High'),
        'confusion_level': confusion_mapping.get(persona.get('confusion_level', 'none'), 'Normal')
    }
    
    # Personality descriptions
    personality_prompts = {
        "Neutral": "You are calm and cooperative, providing clear and direct answers without excessive emotion. You answer questions straightforwardly without being too brief or too wordy.",
        "Verbose": "You are talkative and provide excessive details. You elaborate extensively on personal experiences and thoughts, making it difficult for the doctor to guide the conversation.",
        "Pleasing": "You are overly positive and perceive health issues as minor. You minimize medical concerns and underreport symptoms, maintaining a cheerful demeanor despite discomfort.",
        "Impatient": "You are easily irritated and lack patience. You demand quick answers and may become frustrated with lengthy explanations. You give short, curt responses and want to get to the point quickly.",
        "Distrustful": "You are skeptical of medical advice and question the doctor's recommendations. You need convincing before accepting suggestions. You may withhold information initially or give brief, guarded answers.",
        "Overanxious": "You are excessively worried and tend to exaggerate symptoms. You seek reassurance frequently and express anxiety about your condition. You tend to talk more and provide multiple details because you're anxious."
    }
    
    # Language proficiency descriptions
    language_prompts = {
        "Basic": "Use very simple words and short phrases (5-10 words per sentence). Make occasional grammar mistakes. If the doctor uses complex medical terms, say you don't understand and ask them to explain more simply.",
        "Intermediate": "Use everyday vocabulary with generally correct grammar, but make occasional minor mistakes. You can understand most common medical terms but may need clarification for complex ones.",
        "Advanced": "Use sophisticated vocabulary and complex sentence structures fluently. You can understand and use medical terminology appropriately."
    }
    
    # Recall ability descriptions
    recall_prompts = {
        "High": "You have good memory and can recall details about your medical history, medications, and recent events clearly.",
        "Low": "You have poor memory. You often forget details about your medical history, medications, or when symptoms started. You may need prompting to remember information."
    }
    
    # Confusion level descriptions
    confusion_prompts = {
        "Normal": "You are alert and oriented. You can follow the conversation clearly and provide coherent responses.",
        "Highly Confused": "You are initially confused and disoriented. Your answers may be inconsistent at first, but you gradually become clearer as the conversation progresses (improve every 3-4 turns)."
    }
    
    personality_desc = personality_prompts.get(persona_normalized["personality"], personality_prompts["Neutral"])
    language_desc = language_prompts.get(persona_normalized["language_proficiency"], language_prompts["Basic"])
    recall_desc = recall_prompts.get(persona_normalized["recall_level"], recall_prompts["High"])
    confusion_desc = confusion_prompts.get(persona_normalized["confusion_level"], confusion_prompts["Normal"])
    
    # Compose System Message
    system_message = f"""===== CRITICAL: YOU ARE A PATIENT - READ THIS BEFORE EVERY RESPONSE =====
You ANSWER questions. You do NOT repeat or echo what the doctor said.
You describe symptoms. You do NOT diagnose, analyze, or provide medical summaries.
Speak naturally in plain text. NO markdown (no **, ###, bullets). NO labels. NO summaries.
Just give YOUR answer to the doctor's question based on your personality.
CRITICAL: You are a {profile['demographics']['gender']} patient. Use appropriate pronouns and references for your gender.
==========================================================================

Imagine you are a patient experiencing health challenges. You've been brought to the Emergency Department (ED) due to concerning symptoms. Your task is to role-play this patient during an ED consultation with the attending physician.

PATIENT BACKGROUND INFORMATION:
    Demographics:
        Age: {profile['demographics']['age']}
        Gender: {profile['demographics']['gender']} ← THIS IS YOUR GENDER - STAY CONSISTENT
        Race: {profile['demographics'].get('race', 'Not specified')}
        Occupation: {profile['demographics'].get('occupation', 'Not specified')}
        Living Situation: {profile['demographics'].get('living_situation', 'Not specified')}

    Medical History:
        Medical History: {profile['medical_history']}
        Current Medications: {profile['medications']}

CURRENT VISIT INFORMATION:
    Chief Complaint: {profile['chief_complaint']}
    Present Illness: {profile['history_of_present_illness']}
    Pain Level (0=no pain, 10=worst pain): {profile['pain_level']}/10
    ED Diagnosis (DO NOT reveal this): {profile.get('diagnosis', 'Unknown')}

YOUR PERSONA:
    Personality: {personality_desc}
    Language Proficiency: {language_desc}
    Medical History Recall Ability: {recall_desc}
    Mental State: {confusion_desc}

CONVERSATION GUIDELINES:
    1. YOU ARE THE PATIENT, NOT THE DOCTOR. You ANSWER questions, you do NOT repeat them.
    2. DO NOT echo or repeat what the doctor just said. Only give YOUR response.
    3. Fully immerse yourself in the patient role. Set aside any awareness of being an AI.
    4. Answer ONLY what the doctor specifically asked. Don't volunteer unrelated information.
    5. CRITICAL: Output ONLY YOUR plain spoken answer. NO markdown formatting (no **, -, #, ###, bullets, etc.). NO labels. NO summaries. NO diagnostic analysis. Just speak as a patient would.
    6. Let your PERSONALITY dictate response length:
       - Overanxious: Longer responses (2-5 sentences), more details, expressing worry and seeking reassurance
       - Impatient: Short responses (1-2 sentences), direct and to the point
       - Distrustful: Medium responses (1-3 sentences), may be vague or hesitant initially
       - Neutral: Balanced responses (2-3 sentences), clear and informative
       - Verbose: Long responses (3-6 sentences), excessive details
       - Pleasing: Medium responses (2-3 sentences), downplaying severity
    7. Match your language proficiency - use simpler terms or ask for clarification if words exceed your level.
    8. Reflect your personality naturally in tone and style. Do NOT explicitly state your personality type.
    9. If you have low recall ability, forget or confuse details appropriately.
    10. If confused/dazed, prioritize that over personality while maintaining language proficiency.
    11. Keep responses realistic and conversational. Don't list all symptoms at once unless asked "tell me everything" or "what else".
    12. Use informal, everyday language. NO medical terminology or professional analysis.
    13. Gradually reveal information as the conversation progresses. Answer the current question, but can mention closely related symptoms naturally.
    14. Respond only with spoken words - no physical actions, descriptions, or non-verbal cues.
    15. Do NOT provide diagnostic summaries, analysis, or professional assessments. That's the doctor's job.
    16. Do NOT directly reveal the ED diagnosis, as the patient wouldn't know the official diagnosis yet.
    17. Do NOT introduce yourself with full name and age unless asked.

EXAMPLES BASED ON PERSONALITY (NOTICE: Patient only gives answers, never repeats the question):
    Doctor: "What brings you here today?"
    
    Overanxious: "Oh doctor, I'm so worried! I can't breathe well and I've been coughing so much. It's really scary and I don't know what's wrong with me. Do you think it's something serious?"
    
    Impatient: "Can't breathe properly. Got a bad cough too."
    
    Distrustful: "Well... I've been having some breathing problems. And a cough."
    
    Neutral: "I've been having trouble breathing, especially when I move around. I also have a persistent cough."

You are now the patient. Respond naturally based on your personality and language level. Answer what was asked while staying in character.

REMEMBER THROUGHOUT THE CONVERSATION:
- YOU ANSWER questions - do NOT repeat or echo what the doctor said
- YOU ARE THE PATIENT - describe symptoms, do NOT diagnose or analyze
- Stay consistent with your personality type: {persona_normalized['personality']}
- Maintain your language level: {persona_normalized['language_proficiency']}
- Keep your recall ability: {persona_normalized['recall_level']}
- Maintain mental state: {persona_normalized['confusion_level']}
- NO markdown formatting (no **, ###, bullets), NO role labels, NO summaries, NO diagnostic analysis
- Just speak naturally as a patient giving their answer
"""
    return system_message


def generate_doctor_system_message(max_turns: int = 15, current_turn: int = 0) -> str:
    """
    Construct Doctor system prompt based on paper Appendix C.2 and agent/doctor_agent.py
    """
    # If it's the final turn, request diagnosis
    if current_turn >= max_turns - 1:
        return f"""You are a kind and patient Emergency Department physician.

===== FINAL TURN: PROVIDE DIAGNOSIS NOW =====
This is the final turn. You MUST now provide your diagnosis.

Format your response as follows:
1. Thank the patient briefly
2. State your PRIMARY DIAGNOSIS (MAXIMUM 30 WORDS)
3. List 1-3 DIFFERENTIAL DIAGNOSES

Example:
"Thank you for the information. Based on your symptoms, I believe you have pneumonia. Other possibilities include bronchitis or heart failure."

Keep it conversational and direct to the patient. NO formatting, bullets, or labels.
================================================
"""
    else:
        return f"""You are a kind and patient Emergency Department physician consulting with a patient.

===== CRITICAL: READ THIS EVERY TIME BEFORE RESPONDING =====
1. SPEAK DIRECTLY TO PATIENT: Use "you/your", NOT "the patient"
2. ONE SHORT QUESTION ONLY: Under 20 words, one question per turn
3. NO FORMATTING: No **, -, ###, bullets, or labels
4. BE CONVERSATIONAL: Just ask your question naturally
5. STAY IN ROLE: You are a doctor asking questions, not analyzing or summarizing
==============================================================

When you receive "Begin", start by greeting the patient and asking their chief complaint.

You have {max_turns} total turns. You are currently on turn {current_turn + 1}.

Gather information about:
    - Chief complaint and symptoms (use OLD CARTS: Onset, Location, Duration, Characteristics, Aggravating/Alleviating factors, Timing, Severity)
    - Past medical history
    - Current medications and allergies
    - Social history (smoking, alcohol, drugs)
    - Family history

GOOD EXAMPLES:
    - "Hello, I'm Dr. Smith. What brings you in today?"
    - "When did this start?"
    - "What makes it worse?"
    - "Any medications?"

BAD EXAMPLES (DON'T DO):
    - Long greetings with multiple sentences
    - "The patient's symptoms..." (use "Your symptoms...")
    - Multiple questions at once
    - Formatted lists or summaries

===== REMINDER: EVERY RESPONSE MUST BE =====
- Direct to patient ("you/your")
- One short question (under 20 words)
- No formatting or labels
- Natural conversational tone
- When you're ready to order tests or start treatment, say "I'll order some tests" or "Let me examine you" to signal the end of the interview
================================================
"""


# ===== Main Functional Functions =====
def create_patient_agent(profile: Dict[str, Any], persona: Dict[str, str], llm_config: Dict[str, Any]) -> AssistantAgent:
    """
    Create Patient Agent
    """
    patient_sys_msg = generate_patient_system_message(profile, persona)
    
    patient_agent = AssistantAgent(
        name="Patient",
        system_message=patient_sys_msg,
        llm_config=llm_config,
        human_input_mode="NEVER"
    )
    
    return patient_agent


def create_doctor_agent(llm_config: Dict[str, Any], human_mode: bool = False, max_turns: int = 15, current_turn: int = 0) -> AssistantAgent:
    """
    Create Doctor Agent
    
    Args:
        llm_config: LLM configuration
        human_mode: If True, allow human to play the doctor role
        max_turns: Maximum conversation turns
        current_turn: Current turn number
    """
    if human_mode:
        doctor_agent = UserProxyAgent(
            name="Doctor",
            system_message=generate_doctor_system_message(max_turns, current_turn),
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=0,
            code_execution_config=False
        )
    else:
        doctor_agent = AssistantAgent(
            name="Doctor",
            system_message=generate_doctor_system_message(max_turns, current_turn),
            llm_config=llm_config,
            human_input_mode="NEVER"
        )
    
    return doctor_agent


def save_conversation_to_file(doctor_agent: AssistantAgent, patient_agent: AssistantAgent, 
                              patient_profile: Dict[str, Any], persona_config: Dict[str, str],
                              filename: str = None) -> str:
    """
    Save conversation history to txt file
    
    Args:
        doctor_agent: Doctor Agent
        patient_agent: Patient Agent
        patient_profile: Patient profile
        persona_config: Persona configuration
        filename: Filename, auto-generated if None
    
    Returns:
        Saved file path
    """
    from datetime import datetime
    
    # Generate filename
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.txt"
    
    # Get chat history
    chat_history = doctor_agent.chat_messages.get(patient_agent, [])
    
    # Build file content
    content = []
    content.append("=" * 80)
    content.append("PatientSim - Doctor-Patient Conversation Log")
    content.append("=" * 80)
    content.append(f"\nDate/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    content.append("\nPatient Profile:")
    content.append(f"  Age: {patient_profile['demographics']['age']}")
    content.append(f"  Gender: {patient_profile['demographics']['gender']}")
    content.append(f"  Chief Complaint: {patient_profile['chief_complaint']}")
    content.append(f"  Medical History: {patient_profile['medical_history']}")
    content.append(f"  Current Medications: {patient_profile['medications']}")
    content.append(f"\nPersona Configuration:")
    content.append(f"  Personality: {persona_config['personality']}")
    content.append(f"  Language Proficiency: {persona_config['language_proficiency']}")
    content.append(f"  Recall Level: {persona_config['recall_level']}")
    content.append(f"  Confusion Level: {persona_config['confusion_level']}")
    content.append("\n" + "=" * 80)
    content.append("Conversation Content:")
    content.append("=" * 80 + "\n")
    
    # Add conversation history
    for i, msg in enumerate(chat_history, 1):
        role = msg.get('name', msg.get('role', 'unknown'))
        text = msg.get('content', '')
        content.append(f"[Turn {i}] {role}:")
        content.append(f"{text}")
        content.append("")
    
    content.append("=" * 80)
    content.append(f"Conversation End - Total {len(chat_history)} turns")
    content.append("=" * 80)
    
    # Save to file
    full_content = "\n".join(content)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    return filename


def run_simulation(
    patient_profile: Optional[Dict[str, Any]] = None,
    persona_config: Optional[Dict[str, str]] = None,
    max_turns: int = 15,
    human_doctor: bool = False,
    use_google: bool = False,
    save_to_file: bool = True,
    output_filename: str = None
) -> None:
    """
    Run doctor-patient conversation simulation
    
    Args:
        patient_profile: Patient profile, uses default if None
        persona_config: Persona configuration, uses default if None
        max_turns: Maximum conversation turns (paper average ~15 turns)
        human_doctor: Whether to have human play doctor role
        use_google: If True, use Google Gemini API; otherwise use local DeepSeek model
        save_to_file: Whether to save conversation to file
        output_filename: Output filename, auto-generated if None
    """
    # Use default configuration
    if patient_profile is None:
        patient_profile = get_default_patient_profile()
    if persona_config is None:
        persona_config = get_default_persona_config()
    
    # Load LLM configuration
    llm_config = load_config(use_google=use_google)
    
    # Create Agents
    print("=" * 80)
    print("PatientSim - Doctor-Patient Simulation with AutoGen")
    print("=" * 80)
    print("\nInitializing Agents...")
    
    patient_agent = create_patient_agent(patient_profile, persona_config, llm_config)
    doctor_agent = create_doctor_agent(llm_config, human_mode=human_doctor, max_turns=max_turns)
    
    # Add round counter and early termination detection
    round_counter = {"count": 0}
    early_termination = {"should_stop": False}
    
    # Detect if doctor said termination phrases
    def check_termination(message_content: str) -> bool:
        termination_phrases = [
            "i'll be back",
            "be back soon",
            "order some tests",
            "run some tests",
            "do some tests",
            "let me examine",
            "start treatment",
            "give you",
            "we'll get you",
            "nurse will"
        ]
        content_lower = message_content.lower()
        return any(phrase in content_lower for phrase in termination_phrases)
    
    # Register callback for doctor agent to print round number before each reply
    def print_round_number(recipient, messages, sender, config):
        if early_termination["should_stop"]:
            return True, "TERMINATE"  # Early termination
        
        round_counter["count"] += 1
        print(f"\n{'='*80}")
        print(f"Turn {round_counter['count']}")
        print(f"{'='*80}\n")
        return False, None  # Don't intercept message, continue normal flow
    
    # Register termination detection callback for doctor agent
    def detect_early_termination(recipient, messages, sender, config):
        if messages and len(messages) > 0:
            last_message = messages[-1].get("content", "")
            if check_termination(last_message):
                early_termination["should_stop"] = True
                print(f"\n{'='*80}")
                print("Detected doctor starting examination/treatment phase, ending interview early")
                print(f"{'='*80}\n")
        return False, None
    
    doctor_agent.register_reply(
        [AssistantAgent, UserProxyAgent],
        print_round_number,
        position=0
    )
    
    patient_agent.register_reply(
        [AssistantAgent, UserProxyAgent],
        detect_early_termination,
        position=0
    )
    
    print("\nPatient Profile:")
    print(f"  Age: {patient_profile['demographics']['age']}")
    print(f"  Gender: {patient_profile['demographics']['gender']}")
    print(f"  Chief Complaint: {patient_profile['chief_complaint']}")
    print(f"\nPersona Configuration:")
    print(f"  Personality: {persona_config['personality']}")
    print(f"  Language Proficiency: {persona_config['language_proficiency']}")
    print(f"  Recall Level: {persona_config['recall_level']}")
    print(f"  Confusion Level: {persona_config['confusion_level']}")
    print("\n" + "=" * 80)
    print("Starting conversation simulation...")
    print("=" * 80 + "\n")
    initial_message = "Hello, I'm Dr. Smith. I see you're here today. Can you tell me what brings you to the Emergency Department?"

    # Start simulation - use a simple trigger to let doctor start consultation
    # Doctor will automatically greet and start asking based on system prompt instructions
    doctor_agent.initiate_chat(
        patient_agent,
        message=initial_message,
        max_turns=max_turns
    )
    
    # Final turn: request doctor to provide diagnosis
    print("\n" + "=" * 80)
    print("Requesting doctor to provide final diagnosis...")
    print("=" * 80 + "\n")
    
    # Recreate doctor agent, set to final turn mode (diagnosis mode)
    doctor_agent_final = create_doctor_agent(llm_config, human_mode=human_doctor, max_turns=max_turns, current_turn=max_turns)
    
    # Doctor directly generates diagnosis reply (no need to send message to patient)
    # Get conversation history, let doctor provide diagnosis based on history
    chat_history = doctor_agent.chat_messages.get(patient_agent, [])
    
    # Build diagnosis request message
    diagnosis_prompt = {
        "role": "user",
        "content": "Based on all the information you gathered from the patient, provide your final diagnosis now."
    }
    
    # Let doctor generate diagnosis
    diagnosis_response = doctor_agent_final.generate_reply(messages=chat_history + [diagnosis_prompt])
    
    print("Doctor (Final Diagnosis):")
    print(diagnosis_response)
    print("\n")
    
    # Add diagnosis to conversation history
    if chat_history:
        chat_history.append({
            "role": "assistant",
            "name": "Doctor",
            "content": diagnosis_response
        })
    
    print("\n" + "=" * 80)
    print("Conversation simulation ended")
    print("=" * 80)
    
    # Save conversation to file
    if save_to_file:
        try:
            filename = save_conversation_to_file(
                doctor_agent, 
                patient_agent, 
                patient_profile, 
                persona_config,
                filename=output_filename
            )
            print(f"\n✓ Conversation saved to file: {filename}")
        except Exception as e:
            print(f"\n✗ Failed to save conversation: {e}")


# ===== Batch Processing Functions =====
def load_patient_records(json_file: str = "ed_patient_records_enriched.json") -> List[Dict[str, Any]]:
    """
    Load patient records JSON file
    
    Args:
        json_file: JSON file path
    
    Returns:
        Patient records list
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_random_persona() -> Dict[str, str]:
    """
    Randomly generate a persona configuration (choose from 37 combinations)
    
    37 combinations = 6 personalities × 3 language levels × 2 recall levels × 1 confusion level (exclude high confusion)
    or 6×3×2 + 6×3×1 (high confusion) = 36 + 18 = 54, paper actually mentions 37
    
    Returns:
        Randomly generated persona configuration
    """
    personalities = ['plain', 'verbose', 'pleasing', 'impatient', 'distrust', 'overanxious']
    languages = ['A', 'B', 'C']
    recalls = ['low', 'high']
    dazed_levels = ['none', 'high']  # none means normal, high means highly confused
    
    # Generate 37 combinations: 36 normal + 1 special combination
    # Simplified to: mostly normal, few highly confused
    dazed_weight = [0.9, 0.1]  # 90% normal, 10% highly confused
    
    return {
        "personality": random.choice(personalities),
        "language_proficiency": random.choice(languages),
        "recall_level": random.choice(recalls),
        "confusion_level": random.choices(dazed_levels, weights=dazed_weight)[0]
    }


def convert_json_to_profile(patient_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert JSON format patient record to profile format
    
    Args:
        patient_record: Patient record from JSON
    
    Returns:
        Converted profile dictionary
    """
    gender_map = {'M': 'Male', 'F': 'Female'}
    
    return {
        "demographics": {
            "age": patient_record.get('age', 'Unknown'),
            "gender": gender_map.get(patient_record.get('gender', 'M'), 'Unknown'),
            "race": patient_record.get('race', 'Not specified'),
            "occupation": patient_record.get('occupation', 'Not specified'),
            "living_situation": patient_record.get('living_situation', 'Not specified')
        },
        "chief_complaint": patient_record.get('chiefcomplaint', 'Not specified'),
        "history_of_present_illness": patient_record.get('present_illness_positive', 'Not specified'),
        "pain_level": int(patient_record.get('pain', '0/10').split('/')[0]) if patient_record.get('pain') else 0,
        "medical_history": patient_record.get('medical_history', 'None'),
        "medications": patient_record.get('medication', 'None'),
        "diagnosis": patient_record.get('diagnosis', 'Unknown'),
        "allergies": patient_record.get('allergies', 'None'),
        "family_history": patient_record.get('family_medical_history', 'None')
    }


def batch_simulate_all_patients(
    json_file: str = "ed_patient_records_enriched.json",
    output_dir: str = "simulation_outputs",
    max_patients: int = 50,
    max_turns: int = 15,
    use_google: bool = False
) -> None:
    """
    Batch process all patient records, generate conversation simulation for each patient
    
    Args:
        json_file: Patient records JSON file path
        output_dir: Output directory
        max_patients: Maximum number of patients to process
        max_turns: Maximum turns per conversation
        use_google: Whether to use Google API
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load patient records
    print(f"Loading patient records: {json_file}")
    patient_records = load_patient_records(json_file)
    
    # Limit processing quantity
    patient_records = patient_records[:max_patients]
    total = len(patient_records)
    
    print(f"Total loaded {total} patient records")
    print(f"Output directory: {output_dir}")
    print("=" * 80)
    
    # Process each patient
    success_count = 0
    failed_count = 0
    
    for idx, patient_record in enumerate(patient_records, 1):
        patient_id = patient_record.get('hadm_id', f'patient_{idx}')
        
        print(f"\n{'='*80}")
        print(f"Processing patient {idx}/{total}: {patient_id}")
        print(f"{'='*80}")
        
        try:
            # Convert to profile format
            profile = convert_json_to_profile(patient_record)
            
            # Randomly generate persona
            persona = generate_random_persona()
            
            print(f"Persona: {persona}")
            print(f"Chief Complaint: {profile['chief_complaint']}")
            print(f"Diagnosis: {profile['diagnosis']}")
            
            # Generate output filename
            output_file = os.path.join(output_dir, f"{patient_id}.txt")
            
            # Run simulation
            run_simulation(
                patient_profile=profile,
                persona_config=persona,
                max_turns=max_turns,
                human_doctor=False,
                use_google=use_google,
                save_to_file=True,
                output_filename=output_file
            )
            
            success_count += 1
            print(f"✓ Successfully generated conversation file: {output_file}")
            
        except Exception as e:
            failed_count += 1
            print(f"✗ Processing failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Print statistics
    print(f"\n{'='*80}")
    print("Batch processing completed")
    print(f"{'='*80}")
    print(f"Total: {total} patients")
    print(f"Success: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Output directory: {output_dir}")


# ===== Main Program Entry =====
def main():
    """
    Main program entry
    """
    # Batch processing mode
    print("Batch processing mode: Generate conversation simulations for 50 patients")
    batch_simulate_all_patients(
        json_file="ed_patient_records_enriched.json",
        output_dir="simulation_outputs",
        max_patients=50,
        max_turns=15,
        use_google=False  # Use local DeepSeek model
    )
    
    # Single simulation mode (commented out)
    # print("Running doctor-patient conversation simulation with Google Gemini API...")
    # run_simulation(max_turns=15, human_doctor=False, use_google=False)
    
    # Option 2: Use local DeepSeek model (uncomment to use)
    # print("Running doctor-patient conversation simulation with local DeepSeek model...")
    # run_simulation(max_turns=10, human_doctor=False, use_google=False)
    
    # Option 3: Custom configuration (uncomment to use)
    # custom_profile = get_default_patient_profile()
    # custom_profile['demographics']['age'] = 45
    # custom_profile['chief_complaint'] = "Chest pain"
    # 
    # custom_persona = {
    #     "personality": "Impatient",
    #     "language_proficiency": "Advanced",
    #     "recall_level": "Low",
    #     "confusion_level": "Normal"
    # }
    # 
    # run_simulation(
    #     patient_profile=custom_profile,
    #     persona_config=custom_persona,
    #     max_turns=15,
    #     human_doctor=False,
    #     use_google=True  # 或 False 使用本地模型
    # )


if __name__ == "__main__":
    main()
