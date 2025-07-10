#!/usr/bin/env python3
"""
AI-Powered Systematic Review Script for Free Water Diffusion MRI Literature

This script automates the systematic review process for research papers on Free Water 
diffusion MRI by analyzing full-text PDFs using multiple AI models (Claude, OpenAI, Gemini).

Date: 2025-01-03
Version: 1.0

Features:
- Multi-model AI support (Claude, OpenAI, Gemini)
- Robust PDF text extraction and metadata parsing
- Progress tracking and resume functionality
- Comprehensive error handling
- Standardized JSON output format
- Rate limiting compliance
- Selective file processing

Usage:
    python systematic_review_ai.py
    
Dependencies:
    pip install anthropic openai google-generativeai PyMuPDF pandas tqdm python-dotenv

Environment Variables (recommended):
    ANTHROPIC_API_KEY=your_claude_api_key
    OPENAI_API_KEY=your_openai_api_key
    GEMINI_API_KEY=your_gemini_api_key
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Third-party imports
import fitz  # PyMuPDF for PDF processing
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv

# AI Model imports (with graceful error handling)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Claude model will not be available.")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. OpenAI models will not be available.")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai package not installed. Gemini model will not be available.")


# ===========================================================================================
# CONFIGURATION SECTION
# ===========================================================================================

class Config:
    """Configuration settings for the systematic review script."""
    
    # Model Selection - Will be set by user input
    ANALYSIS_MODEL = None
    
    # File and Directory Paths
    PDF_FOLDER = '.'  # Current directory
    OUTPUT_CSV = None  # Will be set based on model selection
    PROGRESS_FILE = 'review_progress.json'
    
    # File List Configuration
    USE_FILE_LIST = True
    FILES_LIST_PATH = 'papers_to_screen.txt'
    
    # Processing Configuration
    # Fallback list if file doesn't exist
    SPECIFIC_FILES_TO_PROCESS = []
    
    # API Rate Limiting (seconds between requests)
    RATE_LIMIT_DELAY = 5
    
    # Text Processing Limits (characters)
    TEXT_LIMITS = {
        'claude': 180000,    # Claude 3.5 Sonnet safe limit
        'openai': 120000,    # GPT-4 safe limit  
        'gemini': 1500000    # Gemini Pro safe limit
    }
    
    # Model Versions
    MODEL_VERSIONS = {
        'claude': 'claude-3-5-sonnet-20241022',
        'openai': 'gpt-4o',
        'gemini': 'gemini-2.5-pro-latest'
    }


# ===========================================================================================
# PROMPT TEMPLATES
# ===========================================================================================

class PromptTemplates:
    """Standardized prompt templates for each AI model."""
    
    # Inclusion/Exclusion Criteria (shared across all models)
    CRITERIA = """
    **Inclusion criteria:**
    - Human studies
    - Free Water modeling applied to diffusion MRI
    - Quantitative FW metrics reported (e.g., FW fraction, FW-corrected FA)
    - Peer-reviewed publication

    **Exclusion criteria:**
    - Non-human studies
    - No mention of FW modeling or metrics
    - Conference abstracts, reviews, or editorials
    """
    
    # Claude System Prompt
    CLAUDE_SYSTEM = f"""
    You are an expert assistant conducting a full-text review for a systematic review on Free Water diffusion MRI.
    Your task is to determine if a research paper meets the specified criteria based on its full text.
    
    {CRITERIA}
    
    Your response must ONLY be a single, valid JSON object with no additional text, explanations, 
    or markdown formatting. The JSON object must have exactly two keys:
    - "decision": either "Include" or "Exclude"
    - "justification": a 2-3 sentence explanation for the decision
    
    Example response:
    {{"decision": "Include", "justification": "This is a peer-reviewed human study that explicitly applies free-water modeling to diffusion MRI data and reports quantitative FW metrics including FW fraction."}}
    """
    
    # OpenAI System Prompt
    OPENAI_SYSTEM = f"""
    You are an expert assistant conducting a full-text review for a systematic review on Free Water diffusion MRI.
    Analyze the provided research paper text against the specified criteria.
    
    {CRITERIA}
    
    You must respond ONLY with a valid JSON object containing:
    - "decision": either "Include" or "Exclude"
    - "justification": a 2-3 sentence explanation for the decision
    """
    
    # Gemini Prompt Template
    GEMINI_TEMPLATE = f"""
    You are an expert assistant conducting a full-text review for a systematic review on Free Water diffusion MRI.
    
    {CRITERIA}
    
    Given the following full-text content, does this paper meet the inclusion criteria?
    Your entire response must be in JSON format with two keys: "decision" (either "Include" or "Exclude") 
    and "justification" (2-3 sentence explanation).
    
    Example response format:
    {{"decision": "Include", "justification": "This is a peer-reviewed human study that applies free-water modeling and reports quantitative FW metrics."}}
    
    Here is the full text:
    ---
    {{pdf_text}}
    ---
    """


# ===========================================================================================
# UTILITY FUNCTIONS
# ===========================================================================================

def load_environment_variables() -> None:
    """Load environment variables from .env file if present."""
    load_dotenv()

def get_api_key(service: str) -> Optional[str]:
    """
    Retrieve API key for the specified service.
    
    Args:
        service: The AI service name ('claude', 'openai', 'gemini')
        
    Returns:
        API key string or None if not found
    """
    env_var_map = {
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'gemini': 'GEMINI_API_KEY'
    }
    
    api_key = os.getenv(env_var_map.get(service))
    if not api_key:
        print(f"Warning: {env_var_map.get(service)} not found in environment variables.")
        api_key = input(f"Enter your {service.title()} API key: ").strip()
    
    return api_key if api_key else None

def find_year_in_text(text: str) -> str:
    """
    Extract the most likely publication year from text.
    
    Args:
        text: Text to search for publication year
        
    Returns:
        Publication year as string or "Year not found"
    """
    current_year = datetime.now().year
    # Find 4-digit years between 1980 and current year + 1
    years = re.findall(r'(19[89]\d|20\d\d)', text)
    
    if years:
        # Convert to integers, filter for plausible years, return most recent
        valid_years = [int(y) for y in years if 1980 <= int(y) <= current_year + 1]
        if valid_years:
            return str(max(valid_years))
    
    return "Year not found"

def extract_title_from_text(text: str) -> str:
    """
    Extract title from the first page of text using heuristics.
    
    Args:
        text: First page text from PDF
        
    Returns:
        Extracted title or "Title not found"
    """
    lines = text.split('\n')
    
    # Look for lines that could be titles (between 10-200 characters, not all caps)
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if 10 <= len(line) <= 200 and not line.isupper() and len(line.split()) > 3:
            # Skip common headers/footers
            skip_patterns = ['page', 'doi:', 'http', 'www.', 'journal', 'volume', 'issue']
            if not any(pattern in line.lower() for pattern in skip_patterns):
                return line
    
    return "Title not found"


# ===========================================================================================
# PDF PROCESSING FUNCTIONS
# ===========================================================================================

def extract_info_from_pdf(pdf_path: str) -> Tuple[Optional[str], str, str, str]:
    """
    Extract text, title, and year from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (full_text, title, year, status_message)
    """
    try:
        doc = fitz.open(pdf_path)
        
        # Extract metadata title first
        title = doc.metadata.get('title', '').strip()
        
        # Extract full text
        full_text = ""
        first_page_text = ""
        
        for i, page in enumerate(doc):
            page_text = page.get_text()
            full_text += page_text
            if i == 0:
                first_page_text = page_text
        
        doc.close()
        
        # If no metadata title, try to extract from first page
        if not title or title.lower() in ['untitled', 'title not found']:
            title = extract_title_from_text(first_page_text)
        
        # Extract publication year
        year = find_year_in_text(first_page_text)
        
        # Validate extracted text
        if len(full_text.strip()) < 100:
            return None, title, year, "Warning: Very little text extracted. PDF may be image-based or corrupted."
        
        return full_text, title, year, "Success"
        
    except Exception as e:
        return None, "Extraction Error", "Extraction Error", f"Error: Failed to process PDF - {str(e)}"


# ===========================================================================================
# AI MODEL INTERFACE FUNCTIONS
# ===========================================================================================

def analyze_text_with_claude(text: str, client: Any) -> Dict[str, str]:
    """
    Analyze text using Anthropic's Claude model.
    
    Args:
        text: Full text content from PDF
        client: Anthropic client instance
        
    Returns:
        Dictionary with 'decision' and 'justification' keys
    """
    try:
        # Truncate text to safe limit
        truncated_text = text[:Config.TEXT_LIMITS['claude']]
        
        response = client.messages.create(
            model=Config.MODEL_VERSIONS['claude'],
            max_tokens=400,
            system=PromptTemplates.CLAUDE_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": truncated_text
                }
            ]
        )
        
        # Parse JSON response
        result = json.loads(response.content[0].text)
        
        # Validate required keys
        if 'decision' not in result or 'justification' not in result:
            return {"decision": "Parse Error", "justification": "Missing required keys in model response"}
        
        # Validate decision value
        if result['decision'] not in ['Include', 'Exclude']:
            return {"decision": "Parse Error", "justification": f"Invalid decision value: {result['decision']}"}
        
        return result
        
    except json.JSONDecodeError as e:
        return {"decision": "JSON Error", "justification": f"Invalid JSON response from Claude: {str(e)}"}
    except Exception as e:
        return {"decision": "API Error", "justification": f"Claude API error: {str(e)}"}

def analyze_text_with_openai(text: str, client: Any) -> Dict[str, str]:
    """
    Analyze text using OpenAI's GPT model.
    
    Args:
        text: Full text content from PDF
        client: OpenAI client instance
        
    Returns:
        Dictionary with 'decision' and 'justification' keys
    """
    try:
        # Truncate text to safe limit
        truncated_text = text[:Config.TEXT_LIMITS['openai']]
        
        response = client.chat.completions.create(
            model=Config.MODEL_VERSIONS['openai'],
            messages=[
                {"role": "system", "content": PromptTemplates.OPENAI_SYSTEM},
                {"role": "user", "content": truncated_text}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        
        # Parse JSON response
        result = json.loads(response.choices[0].message.content)
        
        # Validate required keys
        if 'decision' not in result or 'justification' not in result:
            return {"decision": "Parse Error", "justification": "Missing required keys in model response"}
        
        # Validate decision value
        if result['decision'] not in ['Include', 'Exclude']:
            return {"decision": "Parse Error", "justification": f"Invalid decision value: {result['decision']}"}
        
        return result
        
    except json.JSONDecodeError as e:
        return {"decision": "JSON Error", "justification": f"Invalid JSON response from OpenAI: {str(e)}"}
    except Exception as e:
        return {"decision": "API Error", "justification": f"OpenAI API error: {str(e)}"}

def analyze_text_with_gemini(text: str, model: Any) -> Dict[str, str]:
    """
    Analyze text using Google's Gemini model.
    
    Args:
        text: Full text content from PDF
        model: Gemini model instance
        
    Returns:
        Dictionary with 'decision' and 'justification' keys
    """
    try:
        # Truncate text to safe limit
        truncated_text = text[:Config.TEXT_LIMITS['gemini']]
        
        prompt = PromptTemplates.GEMINI_TEMPLATE.format(pdf_text=truncated_text)
        
        response = model.generate_content(prompt)
        
        # Clean response text (remove markdown formatting)
        cleaned_response = response.text.strip().lstrip('```json').rstrip('```').strip()
        
        # Parse JSON response
        result = json.loads(cleaned_response)
        
        # Validate required keys
        if 'decision' not in result or 'justification' not in result:
            return {"decision": "Parse Error", "justification": "Missing required keys in model response"}
        
        # Validate decision value
        if result['decision'] not in ['Include', 'Exclude']:
            return {"decision": "Parse Error", "justification": f"Invalid decision value: {result['decision']}"}
        
        return result
        
    except json.JSONDecodeError as e:
        return {"decision": "JSON Error", "justification": f"Invalid JSON response from Gemini: {str(e)}"}
    except Exception as e:
        return {"decision": "API Error", "justification": f"Gemini API error: {str(e)}"}


# ===========================================================================================
# PROGRESS TRACKING FUNCTIONS
# ===========================================================================================

def save_progress(results_list: List[Dict], progress_file: str = Config.PROGRESS_FILE) -> None:
    """
    Save current progress to JSON file.
    
    Args:
        results_list: List of processing results
        progress_file: Path to progress file
    """
    try:
        with open(progress_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'processed_count': len(results_list),
                'results': results_list
            }, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save progress: {e}")

def load_progress(progress_file: str = Config.PROGRESS_FILE) -> List[Dict]:
    """
    Load previous progress from JSON file.
    
    Args:
        progress_file: Path to progress file
        
    Returns:
        List of previously processed results
    """
    if not os.path.exists(progress_file):
        return []
    
    try:
        with open(progress_file, 'r') as f:
            data = json.load(f)
            return data.get('results', [])
    except Exception as e:
        print(f"Warning: Could not load progress file: {e}")
        return []

def get_processed_filenames(results_list: List[Dict]) -> set:
    """
    Get set of already processed filenames.
    
    Args:
        results_list: List of processing results
        
    Returns:
        Set of processed filenames
    """
    return {result['Filename'] for result in results_list}


# ===========================================================================================
# MAIN EXECUTION FUNCTIONS
# ===========================================================================================

def initialize_ai_client(model_name: str) -> Optional[Any]:
    """
    Initialize the AI client for the specified model.
    
    Args:
        model_name: Name of the AI model ('claude', 'openai', 'gemini')
        
    Returns:
        Initialized client or None if initialization failed
    """
    api_key = get_api_key(model_name)
    if not api_key:
        print(f"Error: No API key provided for {model_name}")
        return None
    
    try:
        if model_name == 'claude':
            if not ANTHROPIC_AVAILABLE:
                print("Error: anthropic package not installed")
                return None
            client = anthropic.Anthropic(api_key=api_key)
            print("✅ Claude (Anthropic) API configured successfully")
            return client
            
        elif model_name == 'openai':
            if not OPENAI_AVAILABLE:
                print("Error: openai package not installed")
                return None
            client = openai.OpenAI(api_key=api_key)
            print("✅ OpenAI API configured successfully")
            return client
            
        elif model_name == 'gemini':
            if not GEMINI_AVAILABLE:
                print("Error: google-generativeai package not installed")
                return None
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(Config.MODEL_VERSIONS['gemini'])
            print("✅ Gemini API configured successfully")
            return model
            
        else:
            print(f"Error: Unknown model '{model_name}'. Choose from: claude, openai, gemini")
            return None
            
    except Exception as e:
        print(f"Error: Failed to configure {model_name} API: {e}")
        return None

def get_files_to_process(pdf_folder: str, specific_files: List[str]) -> List[str]:
    """
    Get list of PDF files to process.
    
    Args:
        pdf_folder: Path to folder containing PDFs
        specific_files: List of specific files to process (empty = all files)
        
    Returns:
        List of PDF filenames to process
    """
    if specific_files:
        print(f"📂 Specific file mode: Processing {len(specific_files)} specified files")
        return specific_files
    else:
        all_pdfs = [f for f in os.listdir(pdf_folder) if f.lower().endswith('.pdf')]
        print(f"📂 Full folder mode: Processing all {len(all_pdfs)} PDFs found")
        return all_pdfs

def process_single_pdf(
    filename: str, 
    pdf_folder: str, 
    ai_client: Any, 
    model_name: str
) -> Dict[str, str]:
    """
    Process a single PDF file.
    
    Args:
        filename: Name of the PDF file
        pdf_folder: Path to folder containing PDFs
        ai_client: Initialized AI client
        model_name: Name of the AI model being used
        
    Returns:
        Dictionary with processing results
    """
    pdf_path = os.path.join(pdf_folder, filename)
    
    # Check if file exists
    if not os.path.exists(pdf_path):
        return {
            'Filename': filename,
            'Title': 'File Not Found',
            'Year': 'Error',
            'Decision': 'File Error',
            'Justification': f'File {filename} not found in {pdf_folder}'
        }
    
    # Extract text and metadata from PDF
    pdf_text, title, year, status = extract_info_from_pdf(pdf_path)
    
    # Analyze with AI if text extraction was successful
    if pdf_text:
        if model_name == 'claude':
            analysis_result = analyze_text_with_claude(pdf_text, ai_client)
        elif model_name == 'openai':
            analysis_result = analyze_text_with_openai(pdf_text, ai_client)
        elif model_name == 'gemini':
            analysis_result = analyze_text_with_gemini(pdf_text, ai_client)
        else:
            analysis_result = {"decision": "Model Error", "justification": f"Unknown model: {model_name}"}
    else:
        analysis_result = {"decision": "Extraction Error", "justification": status}
    
    return {
        'Filename': filename,
        'Title': title,
        'Year': year,
        'Decision': analysis_result.get('decision', 'Parse Error'),
        'Justification': analysis_result.get('justification', 'Could not parse model response')
    }

def get_user_model_choice():
    """Get AI model choice from user input."""
    available_models = []
    
    if ANTHROPIC_AVAILABLE:
        available_models.append('claude')
    if OPENAI_AVAILABLE:
        available_models.append('openai') 
    if GEMINI_AVAILABLE:
        available_models.append('gemini')
    
    if not available_models:
        print("❌ Error: No AI models are available. Please install required packages.")
        sys.exit(1)
    
    print("Available AI models:")
    for i, model in enumerate(available_models, 1):
        print(f"  {i}. {model.title()}")
    
    while True:
        try:
            choice = input(f"\nSelect AI model (1-{len(available_models)}): ").strip()
            model_index = int(choice) - 1
            if 0 <= model_index < len(available_models):
                return available_models[model_index]
            else:
                print(f"Please enter a number between 1 and {len(available_models)}")
        except (ValueError, KeyboardInterrupt):
            print("Please enter a valid number")

def get_files_list():
    """Get list of files to process from file or directory."""
    if Config.USE_FILE_LIST and os.path.exists(Config.FILES_LIST_PATH):
        # Read files from text file
        with open(Config.FILES_LIST_PATH, 'r') as f:
            files_list = [line.strip() for line in f.readlines() if line.strip()]
        print(f"📄 Reading {len(files_list)} files from {Config.FILES_LIST_PATH}")
        if len(files_list) <= 10:
            print(f"   Files: {', '.join(files_list)}")
        else:
            print(f"   First 5 files: {', '.join(files_list[:5])}...")
        return files_list
    elif Config.SPECIFIC_FILES_TO_PROCESS:
        print(f"📄 Processing {len(Config.SPECIFIC_FILES_TO_PROCESS)} specific files")
        return Config.SPECIFIC_FILES_TO_PROCESS
    else:
        # Get all PDF files from folder
        all_files = [f for f in os.listdir(Config.PDF_FOLDER) if f.lower().endswith('.pdf')]
        print(f"📄 Processing all {len(all_files)} PDF files in folder")
        return all_files

def main():
    """Main execution function."""
    print("🔬 AI-Powered Systematic Review Script for Free Water Diffusion MRI")
    print("=" * 70)
    
    # Get user model choice
    Config.ANALYSIS_MODEL = get_user_model_choice()
    Config.OUTPUT_CSV = f'systematic_review_{Config.ANALYSIS_MODEL}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print(f"\n✅ Selected model: {Config.ANALYSIS_MODEL.title()}")
    print(f"📊 Output file: {Config.OUTPUT_CSV}")
    
    # Load environment variables
    load_environment_variables()
    
    # Validate configuration
    if not os.path.isdir(Config.PDF_FOLDER):
        print(f"❌ Error: PDF folder '{Config.PDF_FOLDER}' does not exist")
        print("Please update the PDF_FOLDER path in the Config class")
        sys.exit(1)
    
    # Initialize AI client
    print(f"🤖 Initializing {Config.ANALYSIS_MODEL.title()} AI model...")
    ai_client = initialize_ai_client(Config.ANALYSIS_MODEL)
    if not ai_client:
        print(f"❌ Failed to initialize {Config.ANALYSIS_MODEL} client")
        sys.exit(1)
    
    # Get files to process
    files_to_process = get_files_list()
    if not files_to_process:
        print("❌ No PDF files found to process")
        sys.exit(1)
    
    # Load previous progress
    print("📋 Checking for previous progress...")
    results_list = load_progress()
    processed_files = get_processed_filenames(results_list)
    
    # Filter out already processed files
    remaining_files = [f for f in files_to_process if f not in processed_files]
    
    if processed_files:
        print(f"✅ Found {len(processed_files)} previously processed files")
        print(f"📝 {len(remaining_files)} files remaining to process")
    else:
        print("📝 Starting fresh - no previous progress found")
    
    if not remaining_files:
        print("🎉 All files have already been processed!")
        # Save final results
        results_df = pd.DataFrame(results_list)
        results_df.to_csv(Config.OUTPUT_CSV, index=False, encoding='utf-8')
        print(f"📊 Results saved to: {Config.OUTPUT_CSV}")
        return
    
    # Process remaining files
    print(f"\n🚀 Starting analysis with {Config.ANALYSIS_MODEL.title()} model...")
    print(f"⏱️  Rate limit: {Config.RATE_LIMIT_DELAY} seconds between requests")
    print("-" * 50)
    
    for i, filename in enumerate(tqdm(remaining_files, desc="Processing PDFs")):
        # Process single PDF
        result = process_single_pdf(filename, Config.PDF_FOLDER, ai_client, Config.ANALYSIS_MODEL)
        results_list.append(result)
        
        # Save progress every 10 files
        if (i + 1) % 10 == 0:
            save_progress(results_list)
            print(f"💾 Progress saved ({len(results_list)} files processed)")
        
        # Rate limiting
        if i < len(remaining_files) - 1:  # Don't sleep after the last file
            time.sleep(Config.RATE_LIMIT_DELAY)
    
    # Save final results
    print("\n💾 Saving final results...")
    results_df = pd.DataFrame(results_list)
    results_df.to_csv(Config.OUTPUT_CSV, index=False, encoding='utf-8')
    
    # Generate summary statistics
    print("\n📊 ANALYSIS COMPLETE!")
    print("=" * 50)
    print(f"📁 Total files processed: {len(results_list)}")
    print(f"📄 Results saved to: {Config.OUTPUT_CSV}")
    
    # Decision summary
    decision_counts = results_df['Decision'].value_counts()
    print(f"\n📈 Decision Summary:")
    for decision, count in decision_counts.items():
        percentage = (count / len(results_df)) * 100
        print(f"   {decision}: {count} ({percentage:.1f}%)")
    
    # Clean up progress file
    if os.path.exists(Config.PROGRESS_FILE):
        os.remove(Config.PROGRESS_FILE)
        print(f"🧹 Cleaned up progress file")
    
    print(f"\n✅ Systematic review analysis completed successfully!")
    print(f"🔬 Model used: {Config.ANALYSIS_MODEL.title()} ({Config.MODEL_VERSIONS[Config.ANALYSIS_MODEL]})")


# ===========================================================================================
# SCRIPT ENTRY POINT
# ===========================================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        print("📋 Progress has been saved and can be resumed by running the script again")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)