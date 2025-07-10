# AI-Powered Systematic Review Tools for Free Water Diffusion MRI

This repository contains automated tools for conducting systematic reviews of Free Water diffusion MRI literature using multiple AI models (Claude, OpenAI GPT, and Google Gemini).

## 📋 Overview

The toolkit includes two main scripts:
1. **`systematic_review_ai.py`** - Automated paper screening (Include/Exclude decisions)
2. **`extract_data_gemini.py`** - Structured data extraction from included papers

## 🚀 Quick Start

### Prerequisites

```bash
# Install required Python packages
pip install anthropic openai google-generativeai PyMuPDF pandas tqdm python-dotenv dataclasses typing
```

### API Keys Setup

⚠️ **IMPORTANT**: These tools make API calls that will consume credits/tokens from your AI provider accounts. **Monitor your usage carefully** to avoid unexpected charges.

#### Step 1: Create Accounts and Get API Keys

**Claude (Anthropic)**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up for an account
3. Go to **API Keys** section
4. Click **Create Key** and copy the key (starts with `sk-ant-`)
5. **Usage**: $3-$15 per 1M tokens (varies by model)

**OpenAI GPT**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up for an account  
3. Go to **API Keys** section
4. Click **Create new secret key** and copy the key (starts with `sk-`)
5. **Usage**: $2.50-$10 per 1M tokens (varies by model)

**Google Gemini**
1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Sign in with Google account
3. Click **Get API Key** → **Create API Key**
4. Copy the key (starts with `AI`)
5. **Usage**: Free tier available, then $0.125-$2 per 1M tokens

#### Step 2: Set Up API Keys

**Option 1: Environment Variables (Recommended)**
```bash
export ANTHROPIC_API_KEY="sk-ant-your_claude_api_key"
export OPENAI_API_KEY="sk-your_openai_api_key"  
export GEMINI_API_KEY="AIyour_gemini_api_key"
```

**Option 2: Manual Input**
The scripts will prompt you to enter API keys if environment variables are not found.

#### ⚠️ Usage Monitoring & Cost Control

**Before Processing Large Datasets:**
- **Start small**: Test with 5-10 papers first
- **Check pricing**: Review current API pricing on provider websites
- **Set billing limits**: Configure spending limits in your API accounts
- **Monitor usage**: Check your usage dashboards regularly

**Estimated Costs (approximate):**
- **Screening**: $0.01-$0.05 per paper (varies by length and model)
- **Data extraction**: $0.02-$0.10 per paper (more detailed analysis)
- **100 papers**: Roughly $3-$15 total (depending on model and paper length)

**Cost-Saving Tips:**
- Use **Gemini** for large datasets (lowest cost, free tier available)
- Use **Claude** for final/critical reviews (highest accuracy)
- Process in small batches to monitor costs
- Set up billing alerts in your API accounts

## 📁 File Structure

```
PDFs_only/
├── systematic_review_ai.py          # Main screening script
├── extract_data_gemini.py           # Data extraction script
├── compare_reviews.py               # Compare AI reviewer results
├── conflict_resolution_workflow.py  # Handle disagreements
├── papers_to_screen.txt             # List of PDFs to screen
├── files_to_process.txt             # List of PDFs for data extraction
├── fw_001.pdf                       # PDF files
├── fw_002.pdf
└── ...
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

## 📊 Tool 2: Data Extraction (`extract_data_gemini.py`)

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

## 🔧 Configuration

### File Lists
- **`papers_to_screen.txt`**: PDFs for inclusion/exclusion screening
- **`files_to_process.txt`**: PDFs for data extraction

### Model Selection
Both scripts support interactive model selection:
- Available models detected automatically
- User prompted to choose preferred AI model
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
   - Verify API key format (Claude: `sk-ant-`, OpenAI: `sk-`, Gemini: `AI`)

2. **Unexpected Charges**
   - **Monitor your API dashboards regularly**
   - Set up billing alerts in your provider accounts
   - Start with small test batches (5-10 papers)
   - Check current pricing before large runs

3. **PDF Reading Errors**
   - Some PDFs may be corrupted or password-protected
   - Check PDF file paths and permissions
   - Image-based PDFs may not extract text properly

4. **Memory Issues**
   - Large PDFs may exceed text limits
   - Script automatically truncates text to model limits
   - Very long papers may result in incomplete analysis

5. **Rate Limiting**
   - Scripts include automatic rate limiting (5-second delays)
   - Adjust `RATE_LIMIT_DELAY` in config if needed
   - Some providers have stricter limits for new accounts

### Debug Mode
Add `--verbose` flag or modify logging level in scripts for detailed output.

## 📝 Example Workflow

1. **Prepare PDF files** in the directory
2. **Create file lists** (`papers_to_screen.txt`, `files_to_process.txt`)
3. **Run screening**:
   ```bash
   python3 systematic_review_ai.py
   ```
4. **Review results** and resolve conflicts
5. **Extract data** from included papers:
   ```bash
   python3 extract_data_gemini.py
   ```
6. **Analyze results** using generated CSV files

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