# PaperPulse

**AI-powered research paper analysis workspace.**

PaperPulse is a Streamlit app that turns research-paper PDFs into structured insight. Upload papers, extract key information, compare studies, and draft literature-review notes in one place. It uses the Gemini API and supports light and dark themes.

## Features

- **Research Library**: upload and manage PDF papers
- **Paper Intelligence**: research question, methods, results, limitations and gaps
- **Compare Papers**: side-by-side comparison across studies
- **Evidence Matrix**: structured table, downloadable as CSV
- **Research Chat**: ask questions across your uploaded papers
- **Literature Review**: cross-paper synthesis draft
- **Export Report**: download as Markdown or PDF
- **Light / Dark theme**

## Quick Start

```bash
git clone https://github.com/Abeeraiftikhar/PaperPulse.git
cd PaperPulse
pip install -r requirements.txt
streamlit run app.py
```

On Windows you can also use `py -m pip install -r requirements.txt` and `py -m streamlit run app.py`.

## API Key Setup

Create a file `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`) and add:

```toml
GEMINI_API_KEY
GEMINI_MODEL = "gemini-3.6-flash"
```

## Project Structure

```
app.py                 main Streamlit app
ui/                    design system and reusable components
.streamlit/            Streamlit config and secrets template
requirements.txt       Python dependencies
```

## Limitations

- Only selectable-text PDFs are supported. Scanned PDFs need OCR.
- Figures and tables are not interpreted.
- AI output can contain mistakes, so always verify it against the original paper.

## Credits

Powered by BioCode Innovators. Developed by Abeera Iftikhar.
