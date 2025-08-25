# AI-Powered Systematic Review Tools for Free Water Diffusion MRI

This repository contains automated tools for conducting systematic reviews of Free Water diffusion MRI literature using multiple AI models (Claude, OpenAI GPT, and Google Gemini).

## 📋 Overview

The toolkit includes three main scripts:
1. **`systematic_review_ai.py`** - Automated paper screening (Include/Exclude decisions)
2. **`extract_data_gemini.py`** - Basic data extraction from included papers
3. **`extract_data_hybrid_docling_pymupdf.py`** - ⭐ **Advanced hybrid extraction with dual AI support**

## 🚀 Quick Start

### Prerequisites

```bash
# Install required Python packages
pip install anthropic openai google-generativeai PyMuPDF pandas tqdm python-dotenv dataclasses typing

# For hybrid extraction (recommended)
pip install docling
```

### API Keys Setup

You'll need API keys for the AI models you want to use:

- **Claude (Anthropic)**: Get from [Anthropic Console](https://console.anthropic.com/)
- **OpenAI GPT**: Get from [OpenAI Platform](https://platform.openai.com/)
- **Google Gemini**: Get from [Google AI Studio](https://aistudio.google.com/)

#### Option 1: Environment Variables (Recommended)
```bash
export ANTHROPIC_API_KEY="your_claude_api_key"
export OPENAI_API_KEY="your_openai_api_key"  
export GEMINI_API_KEY="your_gemini_api_key"

# For hybrid extraction script
export CLAUDE_API_KEY="your_claude_api_key"    # Same as ANTHROPIC_API_KEY
```

#### Option 2: Manual Input
The scripts will prompt you to enter API keys if environment variables are not found.

## 📁 File Structure

```
PDFs_only/
├── systematic_review_ai.py                    # Main screening script
├── extract_data_gemini.py                     # Basic data extraction script
├── extract_data_hybrid_docling_pymupdf.py     # ⭐ Advanced hybrid extraction
├── compare_reviews.py                         # Compare AI reviewer results
├── conflict_resolution_workflow.py            # Handle disagreements
├── papers_to_screen.txt                       # List of PDFs to screen
├── files_to_process.txt                       # List of PDFs for data extraction
├── new_test_pdfs/                             # PDF files directory
├── docling_out/                               # Intermediate extraction files
└── extraction_template.csv                    # Data extraction template
```

## 🔍 Tool 1: Paper Screening (`systematic_review_ai.py`)

Automatically screens papers for inclusion/exclusion based on Free Water diffusion MRI criteria.

### Usage

```bash
python3 systematic_review_ai.py
```

### Interactive Setup
1. **Select AI Model**: Choose from Claude, OpenAI, or Gemini
2. **File Input**: Reads from `papers_to_screen.txt` by default
3. **Progress Tracking**: Automatically resumes interrupted runs

### Input File Format
Create `papers_to_screen.txt` with one PDF filename per line:
```
fw_001.pdf
fw_002.pdf
fw_003.pdf
```

### Output
- CSV file: `systematic_review_{model}_{timestamp}.csv`
- Columns: Filename, Title, Year, Decision, Justification

### Screening Criteria

**✅ Inclusion Criteria:**
- Human studies
- Free Water modeling applied to diffusion MRI
- Quantitative FW metrics reported (e.g., FW fraction, FW-corrected FA)
- Peer-reviewed publication

**❌ Exclusion Criteria:**
- Non-human studies
- No mention of FW modeling or metrics
- Conference abstracts, reviews, or editorials

## 📊 Tool 2: Basic Data Extraction (`extract_data_gemini.py`)

Extracts structured data from papers that passed screening.

### Usage

```bash
python3 extract_data_gemini.py
```

### Interactive Setup
1. **API Key**: Enter your Gemini API key when prompted
2. **File Input**: Reads from `files_to_process.txt` by default

### Input File Format
Create `files_to_process.txt` with one PDF filename per line:
```
fw_003.pdf
fw_004.pdf
fw_005.pdf
```

### Output
- CSV file: `data_extraction_gemini_summary_subset_4.csv`
- **Structured columns** instead of clunky text format:
  - `filename`, `title`, `lead_author`, `year`, `journal`, `doi`, `country`
  - `study_aim`, `study_design`, `followup_duration`, `multisite_study`
  - `clinical_population`, `diagnosis`, `disease_duration`, `severity_scale`
  - `clinical_scores`, `control_group`, `total_participants`

### Extracted Data Fields

**Study Identification:**
- Title, Lead author, Year, Journal, DOI, Country

**Study Characteristics:**
- Study aim, Study design, Follow-up duration, Multi-site study

**Participants:**
- Clinical population, Diagnosis, Disease duration
- Severity scales, Clinical scores, Control groups, Sample sizes

## 🚀 Tool 3: Advanced Hybrid Extraction (`extract_data_hybrid_docling_pymupdf.py`)

**⭐ RECOMMENDED** - The most advanced extraction tool combining multiple PDF processing methods with dual AI support.

### Key Features

- 🤖 **Dual AI Support**: Choose between Gemini or Claude AI
- 📊 **Hybrid Processing**: Combines Docling (tables) + PyMuPDF (text) extraction
- 🧠 **Intelligent Merging**: Field-specific prioritization for optimal results
- 📈 **Numerical Values**: Extracts actual table values (not "See Table X")
- 📋 **Template-Based**: Follows standardized extraction template

### Usage

```bash
python extract_data_hybrid_docling_pymupdf.py
```

**Interactive Setup:**
1. Select AI model (1=Gemini, 2=Claude)
2. Script validates API keys automatically
3. Processes files with hybrid approach

### Output Files

- **Gemini**: `hybrid_docling_pymupdf_gemini_extraction_results.csv`
- **Claude**: `hybrid_docling_pymupdf_claude_extraction_results.csv`
- **Tables**: `docling_out/{filename}-table-{N}.csv`

### Extraction Process

```
PDF Input → [Docling Tables] + [PyMuPDF Text] → AI Analysis → Intelligent Merge → CSV Output
```

1. **Docling Processing**: Extracts structured tables as CSV
2. **PyMuPDF Processing**: Comprehensive text extraction
3. **AI Analysis**: Gemini/Claude processes both data sources
4. **Intelligent Merging**: Combines results using field priorities

### Field Prioritization

| Field Type | Preferred Method | Reason |
|------------|------------------|---------|
| Scanner specs | Docling | Better table parsing |
| Free water values | PyMuPDF | Often in text/captions |
| Demographics | Either | Uses best available |

### AI Model Comparison

| Model | Strengths | Best For | Speed | Cost |
|-------|-----------|----------|-------|------|
| **Gemini** | Fast, good tables | High-volume processing | Fast | Lower |
| **Claude** | Superior analysis | Complex papers | Medium | Higher |

### Configuration

Edit the script to customize:

```python
# Files to process
SPECIFIC_FILES_TO_PROCESS = [
    'Zhou2021.pdf', 
    'Burciu2017.pdf', 
    'Chang2021.pdf'
]

# Input/output paths
PDF_FOLDER = 'new_test_pdfs/'
```

### Extracted Data Fields (Complete Template)

**Study Identification**
- Title, Lead Author, Year, Journal, DOI, Country

**Study Characteristics**
- Study aim, Follow-up duration, Multi-site study

**Participants**
- Clinical population, Sample sizes (patient/control/overall)
- Age statistics (mean ± SD, ranges)
- Gender distribution

**MRI Acquisition**
- Scanner strength, Manufacturer
- b-values, Gradient directions, Reverse phase-encoding
- Voxel size, TR, TE, Acquisition time

**Analysis Methods**
- Preprocessing steps, Analysis software, Analysis approach
- Free-water method, Regions analyzed, Metrics reported
- Atlas information, ROI definition method

**Free Water Results** ⭐
- **Clinical group FW values**: Exact numerical values from tables
- **Control group FW values**: Exact numerical values from tables  
- **Group comparison p-values**: Statistical significance

**Correlations & Key Findings**
- Correlation coefficients, Longitudinal data
- Primary findings, Main interpretation, Limitations

## 🔧 Configuration

### File Lists
- **`papers_to_screen.txt`**: PDFs for inclusion/exclusion screening
- **`files_to_process.txt`**: PDFs for data extraction

### Model Selection
All scripts support interactive model selection:
- **Screening script**: Claude, OpenAI, or Gemini
- **Basic extraction**: Gemini only
- **Hybrid extraction**: Gemini or Claude (user choice)
- Output files named according to selected model

### Processing Options
- **File list mode**: Read from text files (default)
- **Specific files mode**: Hardcoded file lists in scripts
- **Full folder mode**: Process all PDFs in directory

## 📈 Additional Tools

### Compare Reviews (`compare_reviews.py`)
```bash
python3 compare_reviews.py
```
- Compares results between different AI models
- Generates statistical analysis and combined CSV
- Identifies disagreements for manual review

### Conflict Resolution (`conflict_resolution_workflow.py`)
- Handles disagreements between AI reviewers
- Organizes papers by agreement status
- Facilitates manual review workflow

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure valid API keys are set
   - Check quota limits and billing status

2. **PDF Reading Errors**
   - Some PDFs may be corrupted or password-protected
   - Check PDF file paths and permissions

3. **Memory Issues**
   - Large PDFs may exceed text limits
   - Script automatically truncates text to model limits

4. **Rate Limiting**
   - Scripts include automatic rate limiting (5-second delays)
   - Adjust `RATE_LIMIT_DELAY` in config if needed

### Debug Mode
Add `--verbose` flag or modify logging level in scripts for detailed output.

## 📝 Example Workflow

### Option A: Complete Workflow (Recommended)
1. **Prepare PDF files** in `new_test_pdfs/` directory
2. **Create file lists** (`papers_to_screen.txt`, `files_to_process.txt`)
3. **Run screening**:
   ```bash
   python3 systematic_review_ai.py
   ```
4. **Review results** and resolve conflicts
5. **Extract data** with advanced hybrid method:
   ```bash
   python3 extract_data_hybrid_docling_pymupdf.py
   # Choose: 1 (Gemini) or 2 (Claude)
   ```
6. **Analyze results** using generated CSV files

### Option B: Quick Test (5 papers)
```bash
# 1. Set API keys
export GEMINI_API_KEY="your_key_here"
export CLAUDE_API_KEY="your_key_here"

# 2. Run hybrid extraction
python3 extract_data_hybrid_docling_pymupdf.py
# Choose: 2 (Claude recommended)

# 3. View results
cat hybrid_docling_pymupdf_claude_extraction_results.csv
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Anthropic for Claude API
- OpenAI for GPT models
- Google for Gemini API
- PyMuPDF for PDF processing

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Open an issue on GitHub
3. Review API documentation for your chosen model

---

**Note**: This tool is designed for research purposes. Always verify AI-generated decisions and extracted data manually for critical systematic reviews.