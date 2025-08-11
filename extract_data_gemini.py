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
class MRIAcquisition:
    field_strength: Optional[str] = None
    manufacturer: Optional[str] = None
    b_values: Optional[str] = None
    num_b_shells: Optional[str] = None
    gradient_directions: Optional[str] = None
    reverse_phase_encoding: Optional[str] = None
    voxel_size: Optional[str] = None
    tr: Optional[str] = None
    te: Optional[str] = None
    acquisition_time: Optional[str] = None

@dataclass
class AnalysisMethods:
    preprocessing: Optional[str] = None
    analysis_software: Optional[str] = None
    free_water_method: Optional[str] = None
    free_water_metrics: Optional[str] = None
    analysis_approach: Optional[str] = None
    tissue_analyzed: Optional[str] = None
    regions_analyzed: Optional[str] = None

@dataclass
class StatisticalAnalysis:
    multiple_comparison_correction: Optional[str] = None

@dataclass
class FreeWaterResults:
    clinical_group_fw_values: Optional[str] = None
    control_group_fw_values: Optional[str] = None
    group_comparison_p_value: Optional[str] = None

@dataclass
class Associations:
    clinical_measure_associations: Optional[str] = None
    measure_name: Optional[str] = None
    association_type: Optional[str] = None
    association_statistics: Optional[str] = None

@dataclass
class Biomarkers:
    biomarker_measured: Optional[str] = None
    biomarker_details: Optional[str] = None
    biomarker_associations: Optional[str] = None

@dataclass
class KeyFindings:
    primary_finding: Optional[str] = None
    main_interpretation: Optional[str] = None
    key_limitations: Optional[str] = None
    other_measures: Optional[str] = None

@dataclass
class ExtractedData:
    filename: Optional[str] = None
    identification: Optional[StudyIdentification] = None
    characteristics: Optional[StudyCharacteristics] = None
    participants: Optional[Participants] = None
    mri_acquisition: Optional[MRIAcquisition] = None
    analysis_methods: Optional[AnalysisMethods] = None
    statistical_analysis: Optional[StatisticalAnalysis] = None
    free_water_results: Optional[FreeWaterResults] = None
    associations: Optional[Associations] = None
    biomarkers: Optional[Biomarkers] = None
    key_findings: Optional[KeyFindings] = None
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
            
        if self.mri_acquisition:
            result.update({
                'field_strength': self.mri_acquisition.field_strength,
                'manufacturer': self.mri_acquisition.manufacturer,
                'b_values': self.mri_acquisition.b_values,
                'num_b_shells': self.mri_acquisition.num_b_shells,
                'gradient_directions': self.mri_acquisition.gradient_directions,
                'reverse_phase_encoding': self.mri_acquisition.reverse_phase_encoding,
                'voxel_size': self.mri_acquisition.voxel_size,
                'tr': self.mri_acquisition.tr,
                'te': self.mri_acquisition.te,
                'acquisition_time': self.mri_acquisition.acquisition_time
            })
            
        if self.analysis_methods:
            result.update({
                'preprocessing': self.analysis_methods.preprocessing,
                'analysis_software': self.analysis_methods.analysis_software,
                'free_water_method': self.analysis_methods.free_water_method,
                'free_water_metrics': self.analysis_methods.free_water_metrics,
                'analysis_approach': self.analysis_methods.analysis_approach,
                'tissue_analyzed': self.analysis_methods.tissue_analyzed,
                'regions_analyzed': self.analysis_methods.regions_analyzed
            })
            
        if self.statistical_analysis:
            result.update({
                'multiple_comparison_correction': self.statistical_analysis.multiple_comparison_correction
            })
            
        if self.free_water_results:
            result.update({
                'clinical_group_fw_values': self.free_water_results.clinical_group_fw_values,
                'control_group_fw_values': self.free_water_results.control_group_fw_values,
                'group_comparison_p_value': self.free_water_results.group_comparison_p_value
            })
            
        if self.associations:
            result.update({
                'clinical_measure_associations': self.associations.clinical_measure_associations,
                'measure_name': self.associations.measure_name,
                'association_type': self.associations.association_type,
                'association_statistics': self.associations.association_statistics
            })
            
        if self.biomarkers:
            result.update({
                'biomarker_measured': self.biomarkers.biomarker_measured,
                'biomarker_details': self.biomarkers.biomarker_details,
                'biomarker_associations': self.biomarkers.biomarker_associations
            })
            
        if self.key_findings:
            result.update({
                'primary_finding': self.key_findings.primary_finding,
                'main_interpretation': self.key_findings.main_interpretation,
                'key_limitations': self.key_findings.key_limitations,
                'other_measures': self.key_findings.other_measures
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
PDF_FOLDER = r'/home/uqahonne/uq/FW_systematic_review/systematic_review/PDFs_only' 

# The name of the final spreadsheet file.
OUTPUT_CSV = 'test2_extraction_gemini_summary_subset_5.csv'


# --- 2. API KEY and NEW PROMPT TEMPLATE ---

# Get API key from environment variable or user input
API_KEY = os.getenv('GEMINI_API_KEY')

if not API_KEY:
    try:
        API_KEY = getpass(f'Enter your {ANALYSIS_MODEL.title()} API Key: ')
    except (EOFError, KeyboardInterrupt):
        # Fallback to direct input if getpass fails
        API_KEY = input(f'Enter your {ANALYSIS_MODEL.title()} API Key: ')

if not API_KEY or API_KEY.strip() == "":
    print("Error: No API key provided. Set GEMINI_API_KEY environment variable or enter when prompted. Exiting.")
    exit(1)

# --- NEW DETAILED PROMPT ---
# This prompt is formatted for Gemini, instructing it to return a single JSON object.
DATA_EXTRACTION_PROMPT = """
You are a meticulous research assistant conducting systematic data extraction for a meta-analysis on free water diffusion MRI studies.
For each paper provided, extract the following information exactly as specified. If information is not available, write "Not reported" or "NR".

**DATA EXTRACTION - PART 1: STUDY & PARTICIPANT DETAILS**

Extract the following information from the provided paper. Write "Not reported" if unavailable.

**STUDY IDENTIFICATION**
- Title: [Exact title]
- Lead author: [First author surname, initials]
- Year: [YYYY]
- Journal: [Full name]
- DOI: [Complete DOI]
- Country: United States | UK | Canada | Australia | Other [specify]

**STUDY CHARACTERISTICS**
- Aim: [One sentence describing primary objective]
- Study design: Observational study | Interventional study | Longitudinal study | Other
- Follow-up duration: [If longitudinal, specify duration]
- Multi-site study: Yes | No

**PARTICIPANTS**
- Clinical population: Neurology | Psychiatry
- Diagnosis: [Specific condition]
- Disease duration: [Mean ± SD years]
- Severity scale used: [Scale name]
- Clinical scores: [Mean ± SD]
- Control group: Yes | No [specify type if yes]
- Total N: [Number]

**DATA EXTRACTION - PART 2: MRI PARAMETERS & METHODS**

Extract technical details from the provided paper. Write "Not reported" if unavailable.

**MRI ACQUISITION**
- Scanner field strength: 1.5T | 3T | 7T
- Manufacturer: Siemens | GE | Philips | Other [specify]
- b-values: [List all values]
- Number of b-shells: 1 | 2 | 3 | 4 | 5+
- Gradient directions: [Total number]
- Reverse phase-encoding: Yes | No
- Voxel size: [e.g., "2×2×2 mm³"]
- TR: [milliseconds]
- TE: [milliseconds]
- Acquisition time: [minutes]

**ANALYSIS METHODS**
- Preprocessing: [List: Denoising | Motion correction | Distortion correction | Other]
- Analysis software: [List: FSL | MATLAB | Python | FreeSurfer | Other]
- Free-water method: Free-water imaging | NODDI | DBSI | Other [specify]
- Free-water metrics: FW fraction | ISOVF/VISO/FISO | ICVF | Other [specify]
- Analysis approach: Whole-brain | ROI | Tract-based | Voxel-wise
- Tissue analyzed: White matter | Gray matter | Lesions | Other
- Regions analyzed: [List specific brain regions/tracts]

**DATA EXTRACTION - PART 3: RESULTS & FINDINGS**

Extract statistical results and findings from the provided paper. Write "Not reported" if unavailable.

**STATISTICAL ANALYSIS**
- Multiple comparison correction: Bonferroni | FDR | FWE | None | Other

**FREE WATER RESULTS**
- Clinical group FW values: [Mean ± SD, N]
- Control group FW values: [Mean ± SD, N] 
- Group comparison p-value: [If reported]

**ASSOCIATIONS**
- Clinical measure associations: Yes | No
- Measure name: [e.g., "EDSS", "HAMD"]
- Association type: Pearson | Spearman | Regression | Other
- Association statistics: [r/β value, p-value]

**BIOMARKERS**
- Biomarker measured: CSF | PET | Blood | Genetics | None
- Biomarker details: [e.g., "CSF tau"]
- Biomarker associations: [Statistics if reported]

**KEY FINDINGS**
- Primary finding: [One sentence summary]
- Main interpretation: [Authors' conclusion]
- Key limitations: [Main limitations mentioned]
- Other measures: [ROC AUC, mediation etc. if reported]

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
    mri_acquisition = MRIAcquisition()
    analysis_methods = AnalysisMethods()
    statistical_analysis = StatisticalAnalysis()
    free_water_results = FreeWaterResults()
    associations = Associations()
    biomarkers = Biomarkers()
    key_findings = KeyFindings()
    
    # Map JSON fields to data class fields
    for key, value in json_data.items():
        if key in ['title', 'lead_author', 'year', 'journal', 'doi', 'country']:
            setattr(identification, key, value)
        elif key in ['study_aim', 'study_design', 'followup_duration', 'multisite_study']:
            setattr(characteristics, key, value)
        elif key in ['clinical_population', 'diagnosis', 'disease_duration', 'severity_scale', 
                    'clinical_scores', 'control_group', 'total_participants']:
            setattr(participants, key, value)
        elif key in ['field_strength', 'manufacturer', 'b_values', 'num_b_shells', 'gradient_directions',
                    'reverse_phase_encoding', 'voxel_size', 'tr', 'te', 'acquisition_time']:
            setattr(mri_acquisition, key, value)
        elif key in ['preprocessing', 'analysis_software', 'free_water_method', 'free_water_metrics',
                    'analysis_approach', 'tissue_analyzed', 'regions_analyzed']:
            setattr(analysis_methods, key, value)
        elif key in ['multiple_comparison_correction']:
            setattr(statistical_analysis, key, value)
        elif key in ['clinical_group_fw_values', 'control_group_fw_values', 'group_comparison_p_value']:
            setattr(free_water_results, key, value)
        elif key in ['clinical_measure_associations', 'measure_name', 'association_type', 'association_statistics']:
            setattr(associations, key, value)
        elif key in ['biomarker_measured', 'biomarker_details', 'biomarker_associations']:
            setattr(biomarkers, key, value)
        elif key in ['primary_finding', 'main_interpretation', 'key_limitations', 'other_measures']:
            setattr(key_findings, key, value)
    
    return ExtractedData(
        identification=identification,
        characteristics=characteristics,
        participants=participants,
        mri_acquisition=mri_acquisition,
        analysis_methods=analysis_methods,
        statistical_analysis=statistical_analysis,
        free_water_results=free_water_results,
        associations=associations,
        biomarkers=biomarkers,
        key_findings=key_findings
    )

def parse_structured_response(text):
    """Parse structured text response into data classes"""
    identification = StudyIdentification()
    characteristics = StudyCharacteristics()
    participants = Participants()
    mri_acquisition = MRIAcquisition()
    analysis_methods = AnalysisMethods()
    statistical_analysis = StatisticalAnalysis()
    free_water_results = FreeWaterResults()
    associations = Associations()
    biomarkers = Biomarkers()
    key_findings = KeyFindings()
    
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
            
            # Map to appropriate data class - Part 1
            if field_name == 'Title':
                identification.title = value
            elif field_name == 'Lead author':
                identification.lead_author = value
            elif field_name in ['Year', 'Year of publication']:
                identification.year = value
            elif field_name in ['Journal', 'Journal name']:
                identification.journal = value
            elif field_name == 'DOI':
                identification.doi = value
            elif field_name == 'Country':
                identification.country = value
            elif field_name in ['Aim', 'Aim of study']:
                characteristics.study_aim = value
            elif field_name == 'Study design':
                characteristics.study_design = value
            elif field_name == 'Follow-up duration':
                characteristics.followup_duration = value
            elif field_name == 'Multi-site study':
                characteristics.multisite_study = value
            elif field_name == 'Clinical population':
                participants.clinical_population = value
            elif field_name in ['Diagnosis', 'Clinical population diagnosis']:
                participants.diagnosis = value
            elif field_name == 'Disease duration':
                participants.disease_duration = value
            elif field_name in ['Severity scale used', 'Disease severity scale/assessment used']:
                participants.severity_scale = value
            elif field_name in ['Clinical scores', 'Disease severity/Clinical scores']:
                participants.clinical_scores = value
            elif field_name == 'Control group':
                participants.control_group = value
            elif field_name in ['Total N', 'Total number of participants']:
                participants.total_participants = value
            # Part 2 - MRI Acquisition
            elif field_name == 'Scanner field strength':
                mri_acquisition.field_strength = value
            elif field_name == 'Manufacturer':
                mri_acquisition.manufacturer = value
            elif field_name == 'b-values':
                mri_acquisition.b_values = value
            elif field_name == 'Number of b-shells':
                mri_acquisition.num_b_shells = value
            elif field_name == 'Gradient directions':
                mri_acquisition.gradient_directions = value
            elif field_name == 'Reverse phase-encoding':
                mri_acquisition.reverse_phase_encoding = value
            elif field_name == 'Voxel size':
                mri_acquisition.voxel_size = value
            elif field_name == 'TR':
                mri_acquisition.tr = value
            elif field_name == 'TE':
                mri_acquisition.te = value
            elif field_name == 'Acquisition time':
                mri_acquisition.acquisition_time = value
            # Part 2 - Analysis Methods
            elif field_name == 'Preprocessing':
                analysis_methods.preprocessing = value
            elif field_name == 'Analysis software':
                analysis_methods.analysis_software = value
            elif field_name == 'Free-water method':
                analysis_methods.free_water_method = value
            elif field_name == 'Free-water metrics':
                analysis_methods.free_water_metrics = value
            elif field_name == 'Analysis approach':
                analysis_methods.analysis_approach = value
            elif field_name == 'Tissue analyzed':
                analysis_methods.tissue_analyzed = value
            elif field_name == 'Regions analyzed':
                analysis_methods.regions_analyzed = value
            # Part 3 - Statistical Analysis
            elif field_name == 'Multiple comparison correction':
                statistical_analysis.multiple_comparison_correction = value
            # Part 3 - Free Water Results
            elif field_name == 'Clinical group FW values':
                free_water_results.clinical_group_fw_values = value
            elif field_name == 'Control group FW values':
                free_water_results.control_group_fw_values = value
            elif field_name == 'Group comparison p-value':
                free_water_results.group_comparison_p_value = value
            # Part 3 - Associations
            elif field_name == 'Clinical measure associations':
                associations.clinical_measure_associations = value
            elif field_name == 'Measure name':
                associations.measure_name = value
            elif field_name == 'Association type':
                associations.association_type = value
            elif field_name == 'Association statistics':
                associations.association_statistics = value
            # Part 3 - Biomarkers
            elif field_name == 'Biomarker measured':
                biomarkers.biomarker_measured = value
            elif field_name == 'Biomarker details':
                biomarkers.biomarker_details = value
            elif field_name == 'Biomarker associations':
                biomarkers.biomarker_associations = value
            # Part 3 - Key Findings
            elif field_name == 'Primary finding':
                key_findings.primary_finding = value
            elif field_name == 'Main interpretation':
                key_findings.main_interpretation = value
            elif field_name == 'Key limitations':
                key_findings.key_limitations = value
            elif field_name == 'Other measures':
                key_findings.other_measures = value
    
    return ExtractedData(
        identification=identification,
        characteristics=characteristics,
        participants=participants,
        mri_acquisition=mri_acquisition,
        analysis_methods=analysis_methods,
        statistical_analysis=statistical_analysis,
        free_water_results=free_water_results,
        associations=associations,
        biomarkers=biomarkers,
        key_findings=key_findings
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