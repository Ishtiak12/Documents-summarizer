# Document Summarization Web Application

## Features
- Upload PDF/DOCX files for AI-powered summarization
- Adjustable summary length (10-90% of original)
- Web interface + REST API
- Download summaries as text files

## Quick Start
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install flask PyPDF2 python-docx transformers torch

# Run the application
python app.py# Documents-summarizer
