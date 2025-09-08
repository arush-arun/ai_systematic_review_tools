#!/usr/bin/env python3
"""
Hybrid data extraction using Docling + PyMuPDF + AI (Gemini or Claude)
Combines structured table extraction with comprehensive text processing for robust extraction
"""

import warnings
# Suppress Pydantic warnings from Docling
warnings.filterwarnings("ignore", message="Field.*has conflict with protected namespace.*model_.*")

import os
import pandas as pd
import json
import fitz  # PyMuPDF
from tqdm.notebook import tqdm
from getpass import getpass
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

# AI API imports
import google.generativeai as genai
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("Warning: anthropic package not installed. Claude AI will not be available.")
    print("Install with: pip install anthropic")

# Docling imports
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode

# Use same data classes from extract_data_docling_gemini_v2.py
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
    followup_duration: Optional[str] = None
    multisite_study: Optional[str] = None

@dataclass
class Participants:
    clinical_population: Optional[str] = None
    n_patient_group: Optional[str] = None
    n_control_group: Optional[str] = None
    n_overall: Optional[str] = None
    mean_age_patient: Optional[str] = None
    sd_age_patient: Optional[str] = None
    mean_age_control: Optional[str] = None
    sd_age_control: Optional[str] = None
    age_range_patient: Optional[str] = None
    age_range_control: Optional[str] = None
    gender_distribution_patient: Optional[str] = None
    gender_distribution_control: Optional[str] = None

@dataclass
class MRIAcquisition:
    scanner_strength: Optional[str] = None
    scanner_manufacturer: Optional[str] = None
    b_values: Optional[str] = None
    gradient_directions: Optional[str] = None
    reverse_phase_encoding: Optional[str] = None
    voxel_size: Optional[str] = None
    tr: Optional[str] = None
    te: Optional[str] = None
    acquisition_time: Optional[str] = None

@dataclass
class AnalysisMethods:
    preprocessing_steps: Optional[str] = None
    analysis_software: Optional[str] = None
    analysis_approach: Optional[str] = None
    free_water_method: Optional[str] = None
    regions_analyzed: Optional[str] = None
    free_water_metrics_reported: Optional[str] = None
    if_atlas_name_of_atlas: Optional[str] = None
    roi_definition_method: Optional[str] = None

@dataclass
class FreeWaterResults:
    clinical_group_fw_values: Optional[str] = None
    control_group_fw_values: Optional[str] = None
    group_comparison_p_value: Optional[str] = None

@dataclass
class Correlations:
    correlations_reported: Optional[str] = None
    correlation_coefficients: Optional[str] = None

@dataclass
class KeyFindings:
    longitudinal_data_available: Optional[str] = None
    longitudinal_data_results: Optional[str] = None
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
    free_water_results: Optional[FreeWaterResults] = None
    correlations: Optional[Correlations] = None
    key_findings: Optional[KeyFindings] = None
    error: Optional[str] = None
    extraction_method: Optional[str] = None  # Track which method was used
    
    def to_dict(self):
        """Convert to flat dictionary for CSV output"""
        result = {'filename': self.filename, 'extraction_method': self.extraction_method}
        
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
                'followup_duration': self.characteristics.followup_duration,
                'multisite_study': self.characteristics.multisite_study
            })
            
        if self.participants:
            result.update({
                'clinical_population': self.participants.clinical_population,
                'n_patient_group': self.participants.n_patient_group,
                'n_control_group': self.participants.n_control_group,
                'n_overall': self.participants.n_overall,
                'mean_age_patient': self.participants.mean_age_patient,
                'sd_age_patient': self.participants.sd_age_patient,
                'mean_age_control': self.participants.mean_age_control,
                'sd_age_control': self.participants.sd_age_control,
                'age_range_patient': self.participants.age_range_patient,
                'age_range_control': self.participants.age_range_control,
                'gender_distribution_patient': self.participants.gender_distribution_patient,
                'gender_distribution_control': self.participants.gender_distribution_control
            })
            
        if self.mri_acquisition:
            result.update({
                'scanner_strength': self.mri_acquisition.scanner_strength,
                'scanner_manufacturer': self.mri_acquisition.scanner_manufacturer,
                'b_values': self.mri_acquisition.b_values,
                'gradient_directions': self.mri_acquisition.gradient_directions,
                'reverse_phase_encoding': self.mri_acquisition.reverse_phase_encoding,
                'voxel_size': self.mri_acquisition.voxel_size,
                'tr': self.mri_acquisition.tr,
                'te': self.mri_acquisition.te,
                'acquisition_time': self.mri_acquisition.acquisition_time
            })
            
        if self.analysis_methods:
            result.update({
                'preprocessing_steps': self.analysis_methods.preprocessing_steps,
                'analysis_software': self.analysis_methods.analysis_software,
                'analysis_approach': self.analysis_methods.analysis_approach,
                'free_water_method': self.analysis_methods.free_water_method,
                'regions_analyzed': self.analysis_methods.regions_analyzed,
                'free_water_metrics_reported': self.analysis_methods.free_water_metrics_reported,
                'if_atlas_name_of_atlas': self.analysis_methods.if_atlas_name_of_atlas,
                'ROI_definition_method': self.analysis_methods.roi_definition_method
            })
            
        if self.free_water_results:
            result.update({
                'clinical_group_fw_values': self.free_water_results.clinical_group_fw_values,
                'control_group_fw_values': self.free_water_results.control_group_fw_values,
                'group_comparison_p_value': self.free_water_results.group_comparison_p_value
            })
            
        if self.correlations:
            result.update({
                'correlations_reported': self.correlations.correlations_reported,
                'correlation_coefficients': self.correlations.correlation_coefficients
            })
            
        if self.key_findings:
            result.update({
                'longitudinal_data_available': self.key_findings.longitudinal_data_available,
                'longitudinal_data_results': self.key_findings.longitudinal_data_results,
                'primary_finding': self.key_findings.primary_finding,
                'main_interpretation': self.key_findings.main_interpretation,
                'key_limitations': self.key_findings.key_limitations,
                'other_measures': self.key_findings.other_measures
            })
            
        return result

# Configuration
USE_FILE_LIST = True  # Process files from text file
SPECIFIC_FILES_TO_PROCESS = []  # Will be loaded from file
PDF_FOLDER = r'/home/uqahonne/uq/FW_systematic_review/systematic_review/PDFs_only/confirmed_pdfs'
FILE_LIST_PATH = '/home/uqahonne/uq/FW_systematic_review/systematic_review/PDFs_only/Z_files_to_process.txt'
OUTPUT_CSV = 'Z_hybrid_docling_pymupdf_extraction_results.csv'
DOCLING_OUTPUT_FOLDER = "docling_out"
DOCLING_OUTPUT_DIR = Path(DOCLING_OUTPUT_FOLDER)

# AI Model Selection
def select_ai_model():
    """Allow user to select AI model and validate API keys"""
    print("Available AI models:")
    print("1. Gemini (Google)")
    if CLAUDE_AVAILABLE:
        print("2. Claude (Anthropic)")
    else:
        print("2. Claude (Anthropic) - NOT AVAILABLE (install anthropic package)")
    
    while True:
        choice = input("Select AI model (1 for Gemini, 2 for Claude): ").strip()
        
        if choice == '1':
            # Check Gemini API key
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                print("Error: GEMINI_API_KEY environment variable not set.")
                print("Please run: export GEMINI_API_KEY='your_api_key_here'")
                continue
            print("✅ Gemini selected with API key configured")
            return 'gemini', gemini_key
            
        elif choice == '2':
            if not CLAUDE_AVAILABLE:
                print("❌ Claude not available. Install anthropic package first.")
                continue
            # Check Claude API key
            claude_key = os.getenv('CLAUDE_API_KEY')
            if not claude_key:
                print("Error: CLAUDE_API_KEY environment variable not set.")
                print("Please run: export CLAUDE_API_KEY='your_api_key_here'")
                continue
            print("✅ Claude selected with API key configured")
            return 'claude', claude_key
        else:
            print("Invalid choice. Please enter 1 or 2.")

# Select AI model and validate API key
AI_MODEL, API_KEY = select_ai_model()

# Docling prompt (emphasizes table data)
DOCLING_EXTRACTION_PROMPT = """
You are a meticulous research assistant conducting systematic data extraction for a meta-analysis on free water diffusion MRI studies.

CRITICAL INSTRUCTION: You have access to both the full paper text AND extracted table data. Use BOTH sources to extract the most accurate information. For numerical values, prioritize the table data which contains exact values.

Extract the following information from the provided paper. Write "Not reported" if unavailable.

**STUDY IDENTIFICATION**
- Title: [Exact title]
- Lead author: [First author surname, initials]
- Year: [YYYY]
- Journal: [Full name]
- DOI: [Complete DOI]
- Country: [specify]

**STUDY CHARACTERISTICS**
- Study aim: [One sentence describing primary objective]
- Follow-up duration: [If longitudinal, specify duration]
- Multi-site study: [Yes/No]

**PARTICIPANTS**
- Clinical population: [Specific clinical condition/disease]
- N patient group: [Number of patients]
- N control group: [Number of controls]
- N overall: [Total number of participants]
- Mean age patient: [Mean age of patient group]
- SD age patient: [Standard deviation of patient age]
- Mean age control: [Mean age of control group]
- SD age control: [Standard deviation of control age]
- Age range patient: [Age range of patient group, e.g., "25-65 years"]
- Age range control: [Age range of control group]
- Gender distribution patient: [e.g., "12M/8F" or "60% male"]
- Gender distribution control: [e.g., "10M/10F" or "50% male"]

**MRI ACQUISITION**
- Scanner strength: [1.5T/3T/7T]
- Scanner manufacturer: [Siemens/GE/Philips/Other]
- b-values: [List all b-values used, e.g., "0, 1000, 2000 s/mm²"]
- Gradient directions: [Total number of gradient directions]
- Reverse phase-encoding: [Yes/No]
- Voxel size: [e.g., "2×2×2 mm³"]
- TR: [milliseconds]
- TE: [milliseconds]
- Acquisition time: [minutes]

**ANALYSIS METHODS**
- Preprocessing steps: [Software/methods used for preprocessing, e.g., "FSL", "SPM"]
- Analysis software: [Software used for analysis, e.g., "MATLAB", "Python"]
- Analysis approach: [Whole-brain/ROI/Tract-based/Voxel-wise]
- Free-water method: [Free-water imaging/NODDI/DBSI/Other - specify method]
- Regions analyzed: [List specific brain regions/tracts analyzed]
- Free-water metrics reported: [Specific metrics like "FW fraction", "ISOVF", "ICVF" etc.]
- If atlas name of atlas: [If brain atlas was used, specify name e.g., "JH-ICBM-DTI-81", "AAL", "Harvard-Oxford", or "Not reported"]
- ROI definition method: [How ROIs were defined, e.g., "Manual", "Atlas-based", "Automated"]

**FREE WATER RESULTS - USE TABLE DATA**
CRITICAL: Use the extracted table data to provide exact numerical values for each brain region.

- Clinical group FW values: [Extract exact values from table data for each region, format: "Region: Mean ± SD" for all regions]
- Control group FW values: [Extract exact values from table data for each region, format: "Region: Mean ± SD" for all regions]  
- Group comparison p-value: [Extract p-values from table data]

**CORRELATIONS**
- Correlations reported: [Yes/No - whether correlations with clinical measures were reported]
- Correlation coefficients: [If correlations reported, list the correlation values and associated measures]

**KEY FINDINGS**
- Longitudinal data available: [Yes/No - whether the study collected longitudinal data]
- Longitudinal data results: [If longitudinal data available, summarize key longitudinal findings]
- Primary finding: [One sentence summary of main result]
- Main interpretation: [Authors' conclusion]
- Key limitations: [Main limitations mentioned]
- Other measures: [ROC AUC, mediation, effect sizes etc. if reported]

Here is the full text of the paper:
---
{paper_text}
---

Here are the extracted tables (CSV format):
---
{table_data}
---

REMEMBER: Use the table data to extract exact numerical values for free water measurements and demographics. Combine information from both the paper text and the structured table data for the most accurate extraction.
"""

# PyMuPDF prompt (emphasizes comprehensive text analysis)
PYMUPDF_EXTRACTION_PROMPT = """
You are a meticulous research assistant conducting systematic data extraction for a meta-analysis on free water diffusion MRI studies.

CRITICAL INSTRUCTION: Focus on extracting information from the complete text, including values that may be embedded in paragraphs, figure captions, or results sections. Pay special attention to free water values that may be described in text rather than tables.

Extract the following information from the provided paper. Write "Not reported" if unavailable.

**STUDY IDENTIFICATION**
- Title: [Exact title]
- Lead author: [First author surname, initials]
- Year: [YYYY]
- Journal: [Full name]
- DOI: [Complete DOI]
- Country: [specify]

**STUDY CHARACTERISTICS**
- Study aim: [One sentence describing primary objective]
- Follow-up duration: [If longitudinal, specify duration]
- Multi-site study: [Yes/No]

**PARTICIPANTS**
- Clinical population: [Specific clinical condition/disease]
- N patient group: [Number of patients]
- N control group: [Number of controls]
- N overall: [Total number of participants]
- Mean age patient: [Mean age of patient group]
- SD age patient: [Standard deviation of patient age]
- Mean age control: [Mean age of control group]
- SD age control: [Standard deviation of control age]
- Age range patient: [Age range of patient group, e.g., "25-65 years"]
- Age range control: [Age range of control group]
- Gender distribution patient: [e.g., "12M/8F" or "60% male"]
- Gender distribution control: [e.g., "10M/10F" or "50% male"]

**MRI ACQUISITION**
- Scanner strength: [1.5T/3T/7T]
- Scanner manufacturer: [Siemens/GE/Philips/Other]
- b-values: [List all b-values used, e.g., "0, 1000, 2000 s/mm²"]
- Gradient directions: [Total number of gradient directions]
- Reverse phase-encoding: [Yes/No]
- Voxel size: [e.g., "2×2×2 mm³"]
- TR: [milliseconds]
- TE: [milliseconds]
- Acquisition time: [minutes]

**ANALYSIS METHODS**
- Preprocessing steps: [Software/methods used for preprocessing, e.g., "FSL", "SPM"]
- Analysis software: [Software used for analysis, e.g., "MATLAB", "Python"]
- Analysis approach: [Whole-brain/ROI/Tract-based/Voxel-wise]
- Free-water method: [Free-water imaging/NODDI/DBSI/Other - specify method]
- Regions analyzed: [List specific brain regions/tracts analyzed]
- Free-water metrics reported: [Specific metrics like "FW fraction", "ISOVF", "ICVF" etc.]
- If atlas name of atlas: [If brain atlas was used, specify name e.g., "JH-ICBM-DTI-81", "AAL", "Harvard-Oxford", or "Not reported"]
- ROI definition method: [How ROIs were defined, e.g., "Manual", "Atlas-based", "Automated"]

**FREE WATER RESULTS - COMPREHENSIVE TEXT SEARCH**
CRITICAL: Look for free water values anywhere in the text - in results sections, figure captions, tables, or embedded in paragraphs. Include exact numerical values with error bars.

- Clinical group FW values: [Search entire text for patient/clinical group free water values, include exact numbers with standard deviations]
- Control group FW values: [Search entire text for control group free water values, include exact numbers with standard deviations]
- Group comparison p-value: [Search for p-values related to group comparisons]

**CORRELATIONS**
- Correlations reported: [Yes/No - whether correlations with clinical measures were reported]
- Correlation coefficients: [If correlations reported, list the correlation values and associated measures]

**KEY FINDINGS**
- Longitudinal data available: [Yes/No - whether the study collected longitudinal data]
- Longitudinal data results: [If longitudinal data available, summarize key longitudinal findings]
- Primary finding: [One sentence summary of main result]
- Main interpretation: [Authors' conclusion]
- Key limitations: [Main limitations mentioned]
- Other measures: [ROC AUC, mediation, effect sizes etc. if reported]

Here is the full text of the paper:
---
{paper_text}
---

REMEMBER: Focus on comprehensive text analysis. Extract any numerical values mentioned anywhere in the document, especially free water measurements that may be embedded in results paragraphs or figure descriptions.
"""


def extract_text_from_pdf_pymupdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        text = ""
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text += page.get_text()
        
        pdf_document.close()
        print(f"PyMuPDF extracted: {len(text)} characters")
        return text, "Success"
        
    except Exception as e:
        return None, f"Error with PyMuPDF extraction: {e}"

def extract_with_docling(pdf_path):
    """Extract text and tables from PDF using Docling"""
    try:
        out_dir = DOCLING_OUTPUT_DIR
        out_dir.mkdir(exist_ok=True)
        
        # Configure docling
        opts = PdfPipelineOptions()
        opts.do_ocr = False  # Set True for scanned PDFs
        opts.do_table_structure = True
        opts.table_structure_options.mode = TableFormerMode.ACCURATE
        opts.images_scale = 2.0
        opts.generate_page_images = False  # Skip images for speed
        opts.generate_picture_images = False
        opts.generate_table_images = False
        
        converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )
        
        result = converter.convert(pdf_path)
        doc = result.document
        docname = result.input.file.stem
        
        # Save markdown
        md_path = out_dir / f"{docname}.md"
        doc.save_as_markdown(md_path, image_mode=ImageRefMode.REFERENCED)
        
        # Read markdown content
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        # Extract and save tables
        table_data = ""
        table_count = 0
        for i, table in enumerate(doc.tables, start=1):
            df = table.export_to_dataframe()
            if df.empty:
                continue
            table_count += 1
            csv_path = out_dir / f"{docname}-table-{i}.csv"
            df.to_csv(csv_path, index=False)
            
            # Add table to combined data
            table_data += f"\n\nTable {i}:\n"
            table_data += df.to_csv(index=False)
        
        print(f"Docling extracted: {len(markdown_text)} characters text, {table_count} tables")
        return markdown_text, table_data, "Success"
        
    except Exception as e:
        return None, None, f"Error with Docling extraction: {e}"

def extract_data_with_ai(text, table_data, ai_client, ai_model, method="docling"):
    """Extract data using AI (Gemini or Claude) with method-specific prompt"""
    if method == "docling":
        prompt = DOCLING_EXTRACTION_PROMPT.format(
            paper_text=text[:1_200_000],  # Leave room for table data
            table_data=table_data[:300_000] if table_data else ""
        )
    else:  # pymupdf
        prompt = PYMUPDF_EXTRACTION_PROMPT.format(
            paper_text=text[:1_500_000]  # Full text focus
        )
    
    try:
        if ai_model == 'gemini':
            response = ai_client.generate_content(prompt, request_options={"timeout": 120})
            raw_response_text = response.text if hasattr(response, 'text') else ""
        
        elif ai_model == 'claude':
            response = ai_client.messages.create(
                #model="claude-3-5-sonnet-20241022",
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            raw_response_text = response.content[0].text if response.content else ""
        
        else:
            return ExtractedData(error=f"Unsupported AI model: {ai_model}")
        
        if not raw_response_text:
            return ExtractedData(error="The AI API returned an empty response, possibly due to a safety filter.")
            
        # Try to parse as JSON first
        try:
            cleaned_response_text = raw_response_text.strip().lstrip('```json').rstrip('```')
            json_data = json.loads(cleaned_response_text)
            return parse_json_response(json_data)
        except json.JSONDecodeError:
            # If JSON parsing fails, parse the structured text response
            return parse_structured_response(raw_response_text)
        
    except Exception as e:
        return ExtractedData(error=f"An unexpected AI API error occurred: {e}")

def is_meaningful_value(value):
    """Check if a field contains meaningful data (not empty, 'Not reported', etc.)"""
    if not value or value == "Not reported" or value == "NR" or value.strip() == "":
        return False
    return True

def merge_extraction_results(docling_result, pymupdf_result, filename):
    """
    Merge results from both extraction methods using intelligent prioritization
    """
    # Field-specific priorities
    FIELD_PRIORITIES = {
        # Prefer docling for structured/technical data
        'scanner_strength': 'docling',
        'scanner_manufacturer': 'docling', 
        'b_values': 'docling',
        'gradient_directions': 'docling',
        'voxel_size': 'docling',
        'tr': 'docling',
        'te': 'docling',
        
        # Prefer pymupdf for text-embedded values
        'clinical_group_fw_values': 'pymupdf',
        'control_group_fw_values': 'pymupdf',
        'group_comparison_p_value': 'pymupdf',
        'correlation_coefficients': 'pymupdf',
        'key_limitations': 'pymupdf',
        'main_interpretation': 'pymupdf',
        
        # Use whichever has data for these fields
        'title': 'prefer_non_empty',
        'study_aim': 'prefer_non_empty',
        'regions_analyzed': 'prefer_non_empty',
        'primary_finding': 'prefer_non_empty'
    }
    
    # Start with docling result as base
    merged = ExtractedData()
    merged.filename = filename
    merged.extraction_method = "hybrid"
    
    # Handle errors
    if docling_result.error and pymupdf_result.error:
        merged.error = f"Both methods failed: Docling: {docling_result.error}, PyMuPDF: {pymupdf_result.error}"
        return merged
    elif docling_result.error:
        merged = pymupdf_result
        merged.extraction_method = "pymupdf_only"
        return merged
    elif pymupdf_result.error:
        merged = docling_result
        merged.extraction_method = "docling_only"
        return merged
    
    # Merge each data class
    for attr_name in ['identification', 'characteristics', 'participants', 'mri_acquisition', 
                      'analysis_methods', 'free_water_results', 'correlations', 'key_findings']:
        
        docling_attr = getattr(docling_result, attr_name)
        pymupdf_attr = getattr(pymupdf_result, attr_name)
        
        if docling_attr is None and pymupdf_attr is None:
            continue
            
        # Create new instance of the appropriate class
        if docling_attr:
            merged_attr = type(docling_attr)()
        elif pymupdf_attr:
            merged_attr = type(pymupdf_attr)()
        else:
            continue
            
        # Merge fields within each data class
        if docling_attr:
            for field_name in docling_attr.__annotations__:
                docling_value = getattr(docling_attr, field_name)
                pymupdf_value = getattr(pymupdf_attr, field_name) if pymupdf_attr else None
                
                # Apply field-specific priority rules
                priority = FIELD_PRIORITIES.get(field_name, 'prefer_non_empty')
                
                if priority == 'docling':
                    final_value = docling_value if is_meaningful_value(docling_value) else pymupdf_value
                elif priority == 'pymupdf':
                    final_value = pymupdf_value if is_meaningful_value(pymupdf_value) else docling_value
                else:  # prefer_non_empty
                    if is_meaningful_value(docling_value) and is_meaningful_value(pymupdf_value):
                        # Both have data, prefer longer/more detailed answer
                        final_value = docling_value if len(str(docling_value)) >= len(str(pymupdf_value)) else pymupdf_value
                    elif is_meaningful_value(docling_value):
                        final_value = docling_value
                    elif is_meaningful_value(pymupdf_value):
                        final_value = pymupdf_value
                    else:
                        final_value = None
                
                setattr(merged_attr, field_name, final_value)
        
        setattr(merged, attr_name, merged_attr)
    
    return merged

# Parsing functions (same as v2 script)
def parse_json_response(json_data):
    """Parse JSON response into structured data classes"""
    identification = StudyIdentification()
    characteristics = StudyCharacteristics()
    participants = Participants()
    mri_acquisition = MRIAcquisition()
    analysis_methods = AnalysisMethods()
    free_water_results = FreeWaterResults()
    correlations = Correlations()
    key_findings = KeyFindings()
    
    # Map JSON fields to data class fields
    for key, value in json_data.items():
        if key in ['title', 'lead_author', 'year', 'journal', 'doi', 'country']:
            setattr(identification, key, value)
        elif key in ['study_aim', 'followup_duration', 'multisite_study']:
            setattr(characteristics, key, value)
        elif key in ['clinical_population', 'n_patient_group', 'n_control_group', 'n_overall',
                    'mean_age_patient', 'sd_age_patient', 'mean_age_control', 'sd_age_control',
                    'age_range_patient', 'age_range_control', 'gender_distribution_patient', 
                    'gender_distribution_control']:
            setattr(participants, key, value)
        elif key in ['scanner_strength', 'scanner_manufacturer', 'b_values', 'gradient_directions', 
                    'reverse_phase_encoding', 'voxel_size', 'tr', 'te', 'acquisition_time']:
            setattr(mri_acquisition, key, value)
        elif key in ['preprocessing_steps', 'analysis_software', 'analysis_approach', 
                    'free_water_method', 'regions_analyzed', 'free_water_metrics_reported',
                    'if_atlas_name_of_atlas', 'roi_definition_method']:
            setattr(analysis_methods, key, value)
        elif key in ['clinical_group_fw_values', 'control_group_fw_values', 'group_comparison_p_value']:
            setattr(free_water_results, key, value)
        elif key in ['correlations_reported', 'correlation_coefficients']:
            setattr(correlations, key, value)
        elif key in ['longitudinal_data_available', 'longitudinal_data_results', 'primary_finding',
                    'main_interpretation', 'key_limitations', 'other_measures']:
            setattr(key_findings, key, value)
    
    return ExtractedData(
        identification=identification,
        characteristics=characteristics,
        participants=participants,
        mri_acquisition=mri_acquisition,
        analysis_methods=analysis_methods,
        free_water_results=free_water_results,
        correlations=correlations,
        key_findings=key_findings
    )

def parse_structured_response(text):
    """Parse structured text response into data classes"""
    identification = StudyIdentification()
    characteristics = StudyCharacteristics()
    participants = Participants()
    mri_acquisition = MRIAcquisition()
    analysis_methods = AnalysisMethods()
    free_water_results = FreeWaterResults()
    correlations = Correlations()
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
            
            # Map to appropriate data class
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
            elif field_name in ['Study aim', 'Aim']:
                characteristics.study_aim = value
            elif field_name == 'Follow-up duration':
                characteristics.followup_duration = value
            elif field_name == 'Multi-site study':
                characteristics.multisite_study = value
            elif field_name == 'Clinical population':
                participants.clinical_population = value
            elif field_name == 'N patient group':
                participants.n_patient_group = value
            elif field_name == 'N control group':
                participants.n_control_group = value
            elif field_name == 'N overall':
                participants.n_overall = value
            elif field_name == 'Mean age patient':
                participants.mean_age_patient = value
            elif field_name == 'SD age patient':
                participants.sd_age_patient = value
            elif field_name == 'Mean age control':
                participants.mean_age_control = value
            elif field_name == 'SD age control':
                participants.sd_age_control = value
            elif field_name == 'Age range patient':
                participants.age_range_patient = value
            elif field_name == 'Age range control':
                participants.age_range_control = value
            elif field_name == 'Gender distribution patient':
                participants.gender_distribution_patient = value
            elif field_name == 'Gender distribution control':
                participants.gender_distribution_control = value
            # MRI Acquisition
            elif field_name == 'Scanner strength':
                mri_acquisition.scanner_strength = value
            elif field_name == 'Scanner manufacturer':
                mri_acquisition.scanner_manufacturer = value
            elif field_name == 'b-values':
                mri_acquisition.b_values = value
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
            # Analysis Methods
            elif field_name == 'Preprocessing steps':
                analysis_methods.preprocessing_steps = value
            elif field_name == 'Analysis software':
                analysis_methods.analysis_software = value
            elif field_name == 'Analysis approach':
                analysis_methods.analysis_approach = value
            elif field_name == 'Free-water method':
                analysis_methods.free_water_method = value
            elif field_name == 'Regions analyzed':
                analysis_methods.regions_analyzed = value
            elif field_name == 'Free-water metrics reported':
                analysis_methods.free_water_metrics_reported = value
            elif field_name == 'If atlas name of atlas':
                analysis_methods.if_atlas_name_of_atlas = value
            elif field_name == 'ROI definition method':
                analysis_methods.roi_definition_method = value
            # Free Water Results
            elif field_name == 'Clinical group FW values':
                free_water_results.clinical_group_fw_values = value
            elif field_name == 'Control group FW values':
                free_water_results.control_group_fw_values = value
            elif field_name == 'Group comparison p-value':
                free_water_results.group_comparison_p_value = value
            # Correlations
            elif field_name == 'Correlations reported':
                correlations.correlations_reported = value
            elif field_name == 'Correlation coefficients':
                correlations.correlation_coefficients = value
            # Key Findings
            elif field_name == 'Longitudinal data available':
                key_findings.longitudinal_data_available = value
            elif field_name == 'Longitudinal data results':
                key_findings.longitudinal_data_results = value
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
        free_water_results=free_water_results,
        correlations=correlations,
        key_findings=key_findings
    )

def extract_data_hybrid(pdf_path, ai_client, ai_model, filename):
    """
    Hybrid extraction: Docling + PyMuPDF with intelligent merging
    """
    print(f"\n=== Hybrid Extraction for {filename} using {ai_model.upper()} ===")
    
    # Method 1: Docling (best for structured tables)
    print("Step 1: Extracting with Docling...")
    markdown_text, table_data, docling_status = extract_with_docling(pdf_path)
    
    if markdown_text and table_data is not None:
        docling_result = extract_data_with_ai(markdown_text, table_data, ai_client, ai_model, method="docling")
        docling_result.extraction_method = "docling"
        print("✅ Docling extraction successful")
    else:
        docling_result = ExtractedData(error=docling_status, extraction_method="docling_failed")
        print(f"❌ Docling extraction failed: {docling_status}")
    
    # Method 2: PyMuPDF (best for text-embedded values)
    print("Step 2: Extracting with PyMuPDF...")
    pymupdf_text, pymupdf_status = extract_text_from_pdf_pymupdf(pdf_path)
    
    if pymupdf_text:
        pymupdf_result = extract_data_with_ai(pymupdf_text, None, ai_client, ai_model, method="pymupdf")
        pymupdf_result.extraction_method = "pymupdf"
        print("✅ PyMuPDF extraction successful")
    else:
        pymupdf_result = ExtractedData(error=pymupdf_status, extraction_method="pymupdf_failed")
        print(f"❌ PyMuPDF extraction failed: {pymupdf_status}")
    
    # Method 3: Intelligent merging
    print("Step 3: Merging results...")
    final_result = merge_extraction_results(docling_result, pymupdf_result, filename)
    final_result.filename = filename
    
    print(f"✅ Hybrid extraction complete - Method: {final_result.extraction_method}")
    return final_result

# Main execution
if __name__ == "__main__":
    # Configure AI API based on selected model
    try:
        if AI_MODEL == 'gemini':
            genai.configure(api_key=API_KEY)
            ai_client = genai.GenerativeModel('gemini-2.5-pro')
            print("Gemini API configured successfully with '2.5 Pro' model.")
        elif AI_MODEL == 'claude':
            ai_client = anthropic.Anthropic(api_key=API_KEY)
            print("Claude API configured successfully with 'claude-3-5-sonnet' model.")
        else:
            print(f"Unsupported AI model: {AI_MODEL}")
            exit(1)
    except Exception as e:
        print(f"Failed to configure {AI_MODEL.upper()} API: {e}")
        exit(1)

    if not os.path.isdir(PDF_FOLDER):
        print(f"Error: The folder '{PDF_FOLDER}' does not exist.")
        exit(1)

    # Load files to process from text file
    if USE_FILE_LIST:
        try:
            with open(FILE_LIST_PATH, 'r') as f:
                files_to_process = [line.strip() for line in f.readlines() if line.strip()]
            print(f"Loaded {len(files_to_process)} files from {FILE_LIST_PATH}")
        except FileNotFoundError:
            print(f"Error: File list '{FILE_LIST_PATH}' not found.")
            exit(1)
    else:
        files_to_process = SPECIFIC_FILES_TO_PROCESS
    
    print(f"--- Processing {len(files_to_process)} file(s) with Hybrid Docling + PyMuPDF + {AI_MODEL.upper()} ---")

    all_results = []
    
    for filename in tqdm(files_to_process, desc=f"Extracting Data with Hybrid Method ({AI_MODEL.upper()})"):
        pdf_path = os.path.join(PDF_FOLDER, filename)
        if not os.path.exists(pdf_path):
            print(f"Warning: '{filename}' not found, skipping.")
            continue

        # Hybrid extraction
        extracted_data = extract_data_hybrid(pdf_path, ai_client, AI_MODEL, filename)
        all_results.append(extracted_data)
        
        # Rate limiting
        time.sleep(5)

    # Process and save results
    flat_results = [result.to_dict() for result in all_results]
    final_df = pd.DataFrame(flat_results)
    
    # Save results using configured output filename
    final_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')

    print(f"\n✅ Hybrid extraction complete! Results saved to '{OUTPUT_CSV}'.")
    print("Here are the key results:")
    print(f"Columns available: {list(final_df.columns)}")
    
    # Show extraction method summary
    if 'extraction_method' in final_df.columns:
        print("\nExtraction method summary:")
        print(final_df['extraction_method'].value_counts())
        
    # Show free water extraction results
    if 'clinical_group_fw_values' in final_df.columns:
        print("\nFree water extraction success:")
        fw_success = final_df['clinical_group_fw_values'].notna() & (final_df['clinical_group_fw_values'] != 'Not reported')
        print(f"{fw_success.sum()}/{len(final_df)} files had successful clinical FW value extraction")
        
    print(final_df[['filename', 'extraction_method', 'clinical_group_fw_values']].head())