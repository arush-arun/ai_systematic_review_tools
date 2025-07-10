# Usage Guide

⚠️ **COST WARNING**: These tools consume API credits. Start with small batches (5-10 papers) to test costs. Monitor your API usage dashboards regularly.

## Step-by-Step Tutorial

### 1. Initial Setup

```bash
# Clone or download the repository
git clone <repository-url>
cd systematic-review-tools

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
```

**Method B: Create .env file**
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
echo "OPENAI_API_KEY=sk-..." >> .env
echo "GEMINI_API_KEY=AI..." >> .env
```

### 3. Prepare Your PDF Files

Place your PDF files in the same directory as the scripts:
```
systematic-review-tools/
├── fw_001.pdf
├── fw_002.pdf
├── fw_003.pdf
└── ...
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

Update `files_to_process.txt` with papers marked as "Include", then:

```bash
python3 extract_data_gemini.py
```

**Output:** `data_extraction_gemini_summary_subset_4.csv`

### 8. Analyze Results

The data extraction CSV contains structured columns:
- Study identification (title, author, year, journal)
- Study characteristics (design, duration, aims)
- Participant details (population, sample size, controls)

## Cost Estimation

**Before starting, estimate your costs:**

| Papers | Screening Cost | Extraction Cost | Total (est.) |
|--------|---------------|-----------------|--------------|
| 10     | $0.10-$0.50   | $0.20-$1.00     | $0.30-$1.50  |
| 50     | $0.50-$2.50   | $1.00-$5.00     | $1.50-$7.50  |
| 100    | $1.00-$5.00   | $2.00-$10.00    | $3.00-$15.00 |
| 500    | $5.00-$25.00  | $10.00-$50.00   | $15.00-$75.00|

**Recommendations:**
- **Gemini**: Cheapest option, has free tier
- **Claude**: Most accurate but most expensive
- **OpenAI**: Middle ground for cost/quality

## Example Workflow

```bash
# 1. Setup
python3 setup.py

# 2. Edit file lists (START SMALL!)
nano papers_to_screen.txt  # Add 5-10 PDF filenames first

# 3. Screen papers
python3 systematic_review_ai.py
# Choose: 3 (Gemini) for cost-effective testing
# Wait for processing...

# 4. Review results
cat systematic_review_claude_*.csv

# 5. Update extraction list
nano files_to_process.txt  # Add included papers

# 6. Extract data
python3 extract_data_gemini.py
# Enter API key when prompted

# 7. View structured data
cat data_extraction_gemini_*.csv
```

## Tips for Best Results

### Paper Screening
- **Claude**: Most accurate, best for final reviews
- **OpenAI**: Good balance of speed and accuracy
- **Gemini**: Fastest, good for large initial screenings

### Data Extraction
- Currently uses Gemini (most cost-effective)
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