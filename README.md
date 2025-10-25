# Medical Summary Builder

A production-grade LLM-powered system for extracting structured medical information from disability case PDFs and generating formatted medical summaries.

## Overview

This project implements an AI-assisted medical document processing pipeline that:
- Extracts claimant information (name, SSN, dates, education) from PDF documents
- Identifies alleged medical impairments and conditions
- Extracts chronological medical visit history with provider details
- Generates structured output in both DOCX and Markdown formats
- Uses Google's Gemini API for intelligent text extraction

## Technical Architecture

### Design Principles
- **LLM-First Approach**: No hardcoded patterns or fallback values - all extraction is performed by Gemini LLM
- **Pure Prompt Engineering**: Uses carefully crafted prompts with examples to guide accurate extraction
- **Deterministic Output**: Structured data validation using Pydantic schemas
- **Clean Separation**: Distinct layers for PDF ingestion, LLM extraction, and document rendering

### Project Structure

```
medical-summary-builder/
├── src/
│   ├── app/
│   │   ├── cli.py              # Main CLI entry point
│   │   └── settings.py         # Configuration management with pydantic-settings
│   ├── domain/
│   │   ├── schema.py           # Pydantic models (Claimant, Event, Report)
│   │   └── layout.py           # Custom layout DSL parser
│   ├── ingest/
│   │   ├── pdf_reader.py       # PDF text extraction with pdfplumber
│   │   └── extractors.py       # Orchestration layer for LLM extraction
│   ├── llm/
│   │   ├── reason_summarizer.py  # Gemini LLM interface and prompts
│   │   └── hf_llm.py          # Hugging Face interface (alternative backend)
│   ├── render/
│   │   ├── docx_writer.py      # DOCX template rendering with python-docx
│   │   └── markdown_writer.py  # Markdown output generation
│   └── utils/
│       ├── dates.py            # Date parsing and age calculation
│       └── logging.py          # Structured logging configuration
├── tests/
│   ├── test_ingest.py          # PDF extraction tests
│   ├── test_llm_extraction.py  # LLM extraction unit tests
│   ├── test_render.py          # Document rendering tests
│   └── test_integration.py     # End-to-end pipeline tests
├── templates/
│   └── Medical Summary.docx    # Output template
├── pyproject.toml              # Project dependencies and tool configuration
├── .ruff.toml                  # Ruff linter configuration
└── .pre-commit-config.yaml     # Pre-commit hooks
```

## Installation

### Prerequisites
- Python 3.11 or higher
- uv package manager
- Google Gemini API key

### Setup

1. Clone the repository:
```bash
git clone git@github.com:impravin22/Medical-info-extractor.git
cd Medical-info-extractor
```

2. Install dependencies using uv:
```bash
uv sync --dev
```

3. Configure environment variables:
```bash
# Create .env file
echo "MSB_GEMINI_API_KEY=your_api_key_here" > .env
echo "MSB_GEMINI_MODEL=gemini-2.5-flash" >> .env
```

## Usage

### Basic Command

```bash
uv run python -m src.app.cli \
  --pdf "Medical File.pdf" \
  --template "Medical Summary.docx" \
  --out "out/summary.docx" \
  --md-out "out/summary.md"
```

### Command Line Options

- `--pdf`: Path to input PDF file (required)
- `--template`: Path to DOCX template file (optional)
- `--out`: Output DOCX file path (required)
- `--md-out`: Output Markdown file path (optional)
- `--layout`: Custom layout DSL string (optional)

### Example Output

The system extracts and formats:

**Header Information:**
- Claimant name, SSN, claim title
- Date of birth, alleged onset date, date last insured
- Ages (at onset and current)
- Education level and special education status

**Medical Information:**
- List of alleged impairments
- Chronological medical visit timeline with:
  - Visit date
  - Healthcare provider/facility
  - Specific medical reason for visit
  - Page reference from source document

## Development

### Code Quality Tools

The project uses industry-standard tools for code quality:

- **uv**: Fast Python package manager and environment management
- **Ruff**: Extremely fast Python linter and formatter
- **Pyright**: Static type checker with strict mode
- **pytest**: Testing framework with async support
- **pre-commit**: Git hooks for automated code quality checks

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_llm_extraction.py -v
```

### Code Formatting

```bash
# Format code with Ruff
uv run ruff format .

# Lint and fix issues
uv run ruff check --fix .

# Type checking
uv run pyright
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## LLM Backend Options

### Gemini API (Default)

The system uses Google's Gemini 2.5 Flash model by default for optimal balance of speed, cost, and accuracy.

Configuration:
```bash
MSB_LLM_BACKEND=gemini
MSB_GEMINI_API_KEY=your_api_key_here
MSB_GEMINI_MODEL=gemini-2.5-flash
```

### Open Source Models (Alternative)

The codebase includes support for Hugging Face Transformers for local inference:

```bash
MSB_LLM_BACKEND=hf
MSB_LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
```

**Note**: During development, open source model options (Llama 3.1, Qwen2.5, Phi-3.5) were tested but encountered local environment constraints (disk space limitations, compilation issues on macOS, quantization library compatibility). The Gemini API was selected as the primary backend for reliability and performance. The infrastructure for local model support remains in the codebase for future use when hardware constraints are resolved.

## Extraction Approach

### Prompt Engineering Strategy

The system uses detailed, example-driven prompts to guide Gemini:

1. **Claimant Extraction**: 
   - Explicitly defines search patterns (e.g., "after 'Claimant:'")
   - Provides format examples (e.g., "MM/DD/YYYY")
   - Includes calculation instructions (e.g., education level extraction)

2. **Impairment Extraction**:
   - Targets specific sections ("ALLEGATIONS OF IMPAIRMENTS")
   - Recognizes medical coding (e.g., "7150 - Osteoarthrosis")
   - Filters administrative noise

3. **Event Extraction**:
   - Normalizes provider names to canonical forms
   - Distinguishes clinical encounters from administrative records
   - Extracts specific medical reasons over generic document types

### Data Validation

All extracted data is validated through Pydantic models with:
- Type checking (dates, strings, booleans)
- Optional field handling
- Age calculation verification
- Chronological event sorting

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MSB_LLM_BACKEND` | LLM provider (gemini/hf) | gemini | No |
| `MSB_GEMINI_API_KEY` | Google Gemini API key | None | Yes (for Gemini) |
| `MSB_GEMINI_MODEL` | Gemini model name | gemini-2.5-flash | No |
| `MSB_LLM_MODEL` | Hugging Face model | Qwen/Qwen2.5-7B-Instruct | No |

### Settings File

Configuration is managed through `src/app/settings.py` using `pydantic-settings`:
- Automatic `.env` file loading
- Multiple environment variable aliases
- Type-safe configuration access

## Testing

### Test Coverage

- **Unit Tests**: Individual component validation
  - PDF text extraction
  - LLM prompt/response parsing
  - Date parsing and validation
  - Document rendering

- **Integration Tests**: End-to-end pipeline validation
  - Full extraction workflow
  - DOCX and Markdown generation
  - Error handling scenarios

- **Mocked LLM Tests**: Deterministic testing without API calls

### Test Data

Tests use fixture data and mocked responses to ensure:
- Fast execution without API dependencies
- Reproducible results
- Coverage of edge cases

## CI/CD

The project is configured for GitHub Actions with:
- Automated testing on push and pull requests
- Code quality checks (Ruff, Pyright)
- Test coverage reporting

## Security

- API keys managed through environment variables
- `.env` file excluded from version control
- No secrets in codebase or commit history
- Input validation and sanitization
- Type-safe configuration management

## Limitations and Future Improvements

### Current Limitations
- Requires external LLM API (Gemini)
- Limited to English language documents
- PDF must have extractable text (no OCR)
- Event extraction limited to first 50 pages (configurable in `src/ingest/extractors.py`)
  - For this technical assessment, processing 50 pages provides sufficient coverage
  - For production use with large PDFs (500+ pages), adjust the page limit in `extract_events()` function
  - Located at line 131: `for page_idx, page in enumerate(pages[:50], start=1):`
  - Change `[:50]` to `[:100]` or `[:]` for full PDF processing

### Potential Enhancements
- OCR support for scanned documents
- Multi-language support
- Confidence scoring for extracted fields
- Interactive correction/validation UI
- Batch processing for multiple files
- Enhanced error recovery and partial extraction
- Support for additional output formats (JSON, XML)
- Local model optimization for offline use

## Performance

- Average processing time: 1-3 minutes per document (depends on LLM API response time and page count)
- PDF parsing: < 1 second
- LLM extraction: 1-3 minutes (50 API calls for 50 pages)
- Document rendering: < 1 second

**Note**: Processing time scales with page count. For this assessment, 50 pages are processed. For production use with large PDFs(like this one has 504 pages), consider:
- Adjusting page limit based on document size(504 pages) and requirements. I did not process all the pages due to time and cost constraints. I could not use open source LLMs on my machine as I am using Macbook and it does not really has much of a storage.

## License

This project is developed as a technical assessment for a Superinsight.

