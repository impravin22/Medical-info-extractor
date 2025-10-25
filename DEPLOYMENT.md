## Deployment Guide

This guide explains how to deploy and run the Medical Summary Builder using Nebius (primary) or Gemini (fallback).

### 1. Prerequisites
- Python 3.11+
- uv (package manager)
- A Nebius API key (primary) or Gemini API key (fallback)

### 2. Install Dependencies
```bash
uv sync --dev
```

### 3. Configure Environment
Create a `.env` file (do not commit this file):

Primary (Nebius):
```bash
MSB_LLM_BACKEND=nebius
MSB_NEBIUS_API_KEY=your_nebius_api_key_here
MSB_NEBIUS_MODEL=NousResearch/Hermes-4-405B
MSB_NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1/
```

Fallback (Gemini):
```bash
MSB_LLM_BACKEND=gemini
MSB_GEMINI_API_KEY=your_gemini_api_key_here
MSB_GEMINI_MODEL=gemini-1.5-flash
```

### 4. Run Extraction
```bash
uv run python -m src.app.cli \
  --pdf "Medical File.pdf" \
  --out "out/medical_summary_output.docx" \
  --md-out "out/medical_summary_output.md"
```

Notes:
- The system processes the entire PDF and extracts all valid medical events.
- Outputs are written to `out/` as DOCX and Markdown.
- Ensure `.env` is not committed; `.gitignore` already excludes it.

### 5. Verification Checklist
- out/medical_summary_output.docx exists and opens
- out/medical_summary_output.md exists and lists events with dates and page refs
- No secrets committed (check `.env` and commit diff)

### 6. Troubleshooting
- Missing API key: ensure `.env` is populated and not malformed
- HTTP 401/403: rotate/regenerate your Nebius or Gemini key
- Slow runs on large PDFs: network/API latency; rerun if needed

### 7. Security
- Never commit `.env` or API keys
- Use environment variables in CI/CD
