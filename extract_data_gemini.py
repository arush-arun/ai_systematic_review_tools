# Import necessary libraries
import os
import google.generativeai as genai
# import openai
# import anthropic
import fitz  # PyMuPDF
import pandas as pd
import json
from tqdm.notebook import tqdm
from getpass import getpass
import time
from dataclasses import dataclass
from typing import Optional

# --- 1. DATA CLASSES ---

@dataclass
class StudyIdentification:
    title: Optional[str] = None
    lead_author: Optional[str] = None
    year: Optional[str] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    country: Optional[str] = None

@dataclass
class StudyCharacteristics:
    study_aim: Optional[str] = None
    study_design: Optional[str] = None
    followup_duration: Optional[str] = None
    multisite_study: Optional[str] = None

@dataclass
class Participants:
    clinical_population: Optional[str] = None
    diagnosis: Optional[str] = None
    disease_duration: Optional[str] = None
    severity_scale: Optional[str] = None
    clinical_scores: Optional[str] = None
    control_group: Optional[str] = None
    total_participants: Optional[str] = None

@dataclass
class ExtractedData:
    filename: Optional[str] = None
    identification: Optional[StudyIdentification] = None
    characteristics: Optional[StudyCharacteristics] = None
    participants: Optional[Participants] = None
    error: Optional[str] = None
    
    def to_dict(self):
        """Convert to flat dictionary for CSV output"""
        result = {'filename': self.filename}
        
        if self.error:
            result['error'] = self.error
            return result
            
        if self.identification:
            result.update({
                'title': self.identification.title,
                'lead_author': self.identification.lead_author,
                'year': self.identification.year,
                'journal': self.identification.journal,
                'doi': self.identification.doi,
                'country': self.identification.country
            })
            
        if self.characteristics:
            result.update({
                'study_aim': self.characteristics.study_aim,
                'study_design': self.characteristics.study_design,
                'followup_duration': self.characteristics.followup_duration,
                'multisite_study': self.characteristics.multisite_study
            })
            
        if self.participants:
            result.update({
                'clinical_population': self.participants.clinical_population,
                'diagnosis': self.participants.diagnosis,
                'disease_duration': self.participants.disease_duration,
                'severity_scale': self.participants.severity_scale,
                'clinical_scores': self.participants.clinical_scores,
                'control_group': self.participants.control_group,
                'total_participants': self.participants.total_participants
            })
            
        return result

# --- 2. CONFIGURATION ---

# Choose the AI model. For this complex task, 'gemini' (with Pro) or 'claude' (with Sonnet/Opus) is recommended.
ANALYSIS_MODEL = 'gemini'


# --- IMPORTANT: Set the list of INCLUDED PDFs you want to extract data from ---
# Files will be read from files_to_process.txt
# To run on all files in the folder instead, set USE_FILE_LIST to False
USE_FILE_LIST = True
FILES_LIST_PATH = 'files_to_process.txt'

# Fallback list if file doesn't exist
SPECIFIC_FILES_TO_PROCESS = [ 'fw_003.pdf', 'fw_004.pdf'
    # 'fw_004.pdf',  # Example file from your previous results
    # 'fw_006.pdf',  # Another example
]

# --- Update this path to the folder containing your INCLUDED PDFs ---
PDF_FOLDER = '.'  # Current directory 

# The name of the final spreadsheet file.
OUTPUT_CSV = 'data_extraction_gemini_summary.csv'


# --- 2. API KEY and NEW PROMPT TEMPLATE ---

# Get API key from user input
try:
    API_KEY = getpass(f'Enter your {ANALYSIS_MODEL.title()} API Key: ')
except (EOFError, KeyboardInterrupt):
    # Fallback to direct input if getpass fails
    API_KEY = input(f'Enter your {ANALYSIS_MODEL.title()} API Key: ')

if not API_KEY or API_KEY.strip() == "":
    print("Error: No API key provided. Exiting.")
    exit(1)

# --- NEW DETAILED PROMPT ---
# This prompt is formatted for Gemini, instructing it to return a single JSON object.
DATA_EXTRACTION_PROMPT = """
You are a meticulous research assistant conducting systematic data extraction for a meta-analysis on free water diffusion MRI studies.
For each paper provided, extract the following information exactly as specified. If information is not available, write "Not reported" or "NR".

**STUDY IDENTIFICATION**
- Title: [Exact title from paper]
- Lead author: [First author surname, initials]
- Year of publication: [YYYY]
- Journal name: [Full journal name]
- DOI: [Complete DOI]
- Country: United States | UK | Canada | Australia | Other [specify if other]

**STUDY CHARACTERISTICS**
- Aim of study: [One sentence describing primary objective]
- Study design: Observational study | Interventional study | Longitudinal study | Other [specify]
- Follow-up duration: [If longitudinal, specify duration in months/years]
- Multi-site study: Yes | No

**PARTICIPANTS**
- Clinical population: Neurology | Psychiatry
- Clinical population diagnosis: [Specific condition, e.g., "Multiple sclerosis"]
- Disease duration: [Mean years ± SD if reported]
- Disease severity scale/assessment used: [Scale name, e.g., "EDSS", "HAMD"]
- Disease severity/Clinical scores: [Mean ± SD]
- Control group: Yes | No [If yes, specify type]
- Total number of participants: [Number]


Here is the full text of the paper:
---
{pdf_text}
---
"""

# --- 3. HELPER FUNCTIONS ---

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text, "Success"
    except Exception as e:
        return None, f"Error reading PDF: {e}"

def extract_data_with_gemini(text, model):
    prompt = DATA_EXTRACTION_PROMPT.format(pdf_text=text[:1_500_000])
    raw_response_text = "" # Initialize variable to hold the raw response
    try:
        response = model.generate_content(prompt, request_options={"timeout": 120})
        # Immediately store the raw text in case of an error
        raw_response_text = response.text if hasattr(response, 'text') else ""
        
        if not raw_response_text:
            return ExtractedData(error="The API returned an empty response, possibly due to a safety filter.")
            
        # Try to parse as JSON first
        try:
            cleaned_response_text = raw_response_text.strip().lstrip('```json').rstrip('```')
            json_data = json.loads(cleaned_response_text)
            return parse_json_response(json_data)
        except json.JSONDecodeError:
            # If JSON parsing fails, parse the structured text response
            return parse_structured_response(raw_response_text)
        
    except Exception as e:
        return ExtractedData(error=f"An unexpected API error occurred: {e}")

def parse_json_response(json_data):
    """Parse JSON response into structured data classes"""
    identification = StudyIdentification()
    characteristics = StudyCharacteristics()
    participants = Participants()
    
    # Map JSON fields to data class fields
    for key, value in json_data.items():
        if key in ['title', 'lead_author', 'year', 'journal', 'doi', 'country']:
            setattr(identification, key, value)
        elif key in ['study_aim', 'study_design', 'followup_duration', 'multisite_study']:
            setattr(characteristics, key, value)
        elif key in ['clinical_population', 'diagnosis', 'disease_duration', 'severity_scale', 
                    'clinical_scores', 'control_group', 'total_participants']:
            setattr(participants, key, value)
    
    return ExtractedData(
        identification=identification,
        characteristics=characteristics,
        participants=participants
    )

def parse_structured_response(text):
    """Parse structured text response into data classes"""
    identification = StudyIdentification()
    characteristics = StudyCharacteristics()
    participants = Participants()
    
    # Split text into lines and process
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('**') or line.startswith('---'):
            continue
            
        # Look for lines with format "- Field: Value"
        if line.startswith('- ') and ': ' in line:
            field_part, value_part = line[2:].split(': ', 1)
            field_name = field_part.strip()
            value = value_part.strip()
            
            # Map to appropriate data class
            if field_name == 'Title':
                identification.title = value
            elif field_name == 'Lead author':
                identification.lead_author = value
            elif field_name == 'Year of publication':
                identification.year = value
            elif field_name == 'Journal name':
                identification.journal = value
            elif field_name == 'DOI':
                identification.doi = value
            elif field_name == 'Country':
                identification.country = value
            elif field_name == 'Aim of study':
                characteristics.study_aim = value
            elif field_name == 'Study design':
                characteristics.study_design = value
            elif field_name == 'Follow-up duration':
                characteristics.followup_duration = value
            elif field_name == 'Multi-site study':
                characteristics.multisite_study = value
            elif field_name == 'Clinical population':
                participants.clinical_population = value
            elif field_name == 'Clinical population diagnosis':
                participants.diagnosis = value
            elif field_name == 'Disease duration':
                participants.disease_duration = value
            elif field_name == 'Disease severity scale/assessment used':
                participants.severity_scale = value
            elif field_name == 'Disease severity/Clinical scores':
                participants.clinical_scores = value
            elif field_name == 'Control group':
                participants.control_group = value
            elif field_name == 'Total number of participants':
                participants.total_participants = value
    
    return ExtractedData(
        identification=identification,
        characteristics=characteristics,
        participants=participants
    )

# --- 4. MAIN EXECUTION SCRIPT ---

# Configure and initialize the chosen API client
api_client = None
if ANALYSIS_MODEL == 'gemini':
    try:
        genai.configure(api_key=API_KEY)
        api_client = genai.GenerativeModel('gemini-1.5-pro-latest') # Use the Pro model
        print("Gemini API configured successfully with '2.5 Pro' model.")
    except Exception as e:
        print(f"Failed to configure Gemini API: {e}")
# Add other model configurations here if needed

if api_client:
    if not os.path.isdir(PDF_FOLDER):
        print(f"Error: The folder '{PDF_FOLDER}' does not exist.")
    else:
        if USE_FILE_LIST and os.path.exists(FILES_LIST_PATH):
            # Read files from text file
            with open(FILES_LIST_PATH, 'r') as f:
                files_to_process = [line.strip() for line in f.readlines() if line.strip()]
            print(f"--- FILE LIST MODE: Processing {len(files_to_process)} files from {FILES_LIST_PATH} ---")
        elif SPECIFIC_FILES_TO_PROCESS:
            files_to_process = SPECIFIC_FILES_TO_PROCESS
            print(f"--- SPECIFIC FILES MODE: Processing {len(files_to_process)} user-defined file(s). ---")
        else:
            files_to_process = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
            print(f"--- FULL FOLDER MODE: Processing all {len(files_to_process)} PDFs found. ---")

        all_results = []
        
        for filename in tqdm(files_to_process, desc="Extracting Data"):
            pdf_path = os.path.join(PDF_FOLDER, filename)
            if not os.path.exists(pdf_path):
                print(f"Warning: '{filename}' not found, skipping.")
                continue

            pdf_text, status = extract_text_from_pdf(pdf_path)
            
            if pdf_text:
                # Call the data extraction function
                extracted_data = extract_data_with_gemini(pdf_text, api_client)
                extracted_data.filename = filename # Add filename for reference
                all_results.append(extracted_data)
            else:
                error_data = ExtractedData(filename=filename, error=status)
                all_results.append(error_data)
            
            # Rate limiting
            time.sleep(5) 

        # --- NEW: Process and save all results at the end ---
        # Convert structured data to flat dictionaries for CSV
        flat_results = [result.to_dict() for result in all_results]
        final_df = pd.DataFrame(flat_results)
        final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')

        print(f"\n✅ Data extraction complete! Results saved to '{OUTPUT_CSV}'.")
        print("Here are the first few rows of your extracted data:")
        print(final_df.head())
