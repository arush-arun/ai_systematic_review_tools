# Usage Guide

## Step-by-Step Tutorial

### 1. Initial Setup

```bash
# Clone or download the repository
git clone <repository-url>
cd systematic-review-tools

# Install dependencies
pip install docling anthropic google-generativeai PyMuPDF pandas tqdm

# Run setup script
python3 setup.py
```

### 2. Configure API Keys

Choose one method:

**Method A: Environment Variables**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="AI..."

# For hybrid extraction (use same Claude key)
export CLAUDE_API_KEY="sk-ant-..."
```

**Method B: Create .env file**
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
echo "GEMINI_API_KEY=AI..." >> .env
echo "CLAUDE_API_KEY=sk-ant-..." >> .env
```

### 3. Prepare Your PDF Files

Place your PDF files in the `new_test_pdfs/` directory:
```
systematic-review-tools/
├── new_test_pdfs/
│   ├── Zhou2021.pdf
│   ├── Chang2021.pdf
│   ├── Burciu2017.pdf
│   └── ...
└── scripts...
```

### 4. Create File Lists

**For screening (papers_to_screen.txt):**
```
fw_001.pdf
fw_002.pdf
fw_003.pdf
fw_004.pdf
fw_005.pdf
```

**For data extraction (files_to_process.txt):**
```
fw_003.pdf
fw_004.pdf
fw_005.pdf
```

### 5. Run Paper Screening

```bash
python3 systematic_review_ai.py
```

**Interactive prompts:**
1. Select AI model (1-3)
2. Script will show files to be processed
3. Processing begins with progress tracking

**Output:** `systematic_review_claude_20250110_143022.csv`

### 6. Review Screening Results

Open the CSV file to see:
- Filename: PDF file name
- Title: Extracted paper title
- Year: Publication year
- Decision: Include/Exclude
- Justification: AI reasoning

### 7. Extract Data from Included Papers

**Option A: Basic Extraction (Gemini only)**
```bash
python3 extract_data_gemini.py
```
**Output:** `data_extraction_gemini_summary_subset_4.csv`

**Option B: Advanced Hybrid Extraction (RECOMMENDED)**
```bash
python3 extract_data_hybrid_docling_pymupdf.py
```

**Interactive prompts:**
1. Select AI model:
   ```
   Available AI models:
   1. Gemini (Google)
   2. Claude (Anthropic)
   Select AI model (1 for Gemini, 2 for Claude): 2
   ```
2. Script processes with hybrid approach
3. Shows progress for each PDF

**Output:** 
- `hybrid_docling_pymupdf_gemini_extraction_results.csv` (if Gemini selected)
- `hybrid_docling_pymupdf_claude_extraction_results.csv` (if Claude selected)
- `docling_out/` folder with extracted tables

### 8. Analyze Results

The hybrid extraction CSV contains comprehensive structured columns:

**Study Identification:** title, lead_author, year, journal, doi, country
**Study Characteristics:** study_aim, followup_duration, multisite_study  
**Participants:** clinical_population, n_patient_group, n_control_group, n_overall, age/gender stats
**MRI Acquisition:** scanner_strength, scanner_manufacturer, b_values, gradient_directions, voxel_size, tr, te
**Analysis Methods:** preprocessing_steps, analysis_software, free_water_method, regions_analyzed
**Free Water Results:** clinical_group_fw_values, control_group_fw_values, group_comparison_p_value ⭐
**Key Findings:** primary_finding, main_interpretation, key_limitations

## Example Workflow

### Complete Workflow
```bash
# 1. Setup
python3 setup.py

# 2. Edit file lists
nano papers_to_screen.txt  # Add your PDF filenames

# 3. Screen papers
python3 systematic_review_ai.py
# Choose: 1 (Claude)
# Wait for processing...

# 4. Review results
cat systematic_review_claude_*.csv

# 5. Update extraction list
nano files_to_process.txt  # Add included papers

# 6. Extract data with hybrid method (RECOMMENDED)
python3 extract_data_hybrid_docling_pymupdf.py
# Choose: 2 (Claude)
# Wait for processing...

# 7. View comprehensive structured data
cat hybrid_docling_pymupdf_claude_extraction_results.csv
```

### Quick Test (5 Pre-selected Papers)
```bash
# 1. Set API keys
export GEMINI_API_KEY="your_key"
export CLAUDE_API_KEY="your_key"

# 2. Run hybrid extraction directly
python3 extract_data_hybrid_docling_pymupdf.py
# Choose: 2 (Claude recommended)

# 3. Check results
head -3 hybrid_docling_pymupdf_claude_extraction_results.csv
```

## Tips for Best Results

### Paper Screening
- **Claude**: Most accurate, best for final reviews
- **OpenAI**: Good balance of speed and accuracy
- **Gemini**: Fastest, good for large initial screenings

### Data Extraction
- **Hybrid method** (RECOMMENDED): Best accuracy, extracts actual numerical values
- **Basic method**: Fast but less comprehensive
- **AI Model Choice**: 
  - **Claude**: Superior for complex papers, better text analysis
  - **Gemini**: Faster, good for high-volume processing
- Review extracted data for accuracy
- Some fields may show "Not reported" if information unavailable

### File Management
- Keep PDF filenames simple (avoid spaces, special characters)
- Use consistent naming patterns (e.g., fw_001.pdf, fw_002.pdf)
- Backup your PDF files before processing

### Error Handling
- Scripts automatically resume if interrupted
- Check error messages for specific guidance
- Some PDFs may fail extraction (corrupted/protected files)

## Troubleshooting Quick Fixes

**"No files found"**: Check file paths and permissions
**"API key invalid"**: Verify API key format and quotas
**"PDF extraction failed"**: Some PDFs may be image-based or corrupted
**"Rate limit exceeded"**: Wait and retry, or adjust delay settings

For detailed troubleshooting, see README.md