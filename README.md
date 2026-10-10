# \# PaperPulse - Professional UI Edition

A Streamlit research-analysis workspace redesigned around the uploaded EduPath-AI demo's visual language: structured top navigation, large editorial hero, glowing research preview card, clear workflow sections, animated surfaces, and light/dark switching.

## Run on Windows

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

For Python 3.14:

```bash
py -3.14 -m pip install -r requirements.txt
py -3.14 -m streamlit run app.py
```

## API key

Open **Workspace settings** inside the app and enter an Gemini API key, or set `GEMINI\_API\_KEY` in Streamlit Secrets/environment variables.

The model field is editable so deployment can use a model available to the API project.

## Included modules

* Research Library
* Paper Intelligence
* Compare Papers
* Evidence Matrix
* Research Chat
* Literature Review
* Export Report
* How It Works
* Light / Dark theme switch

## UI structure

The `ui/` folder contains the visual design system and reusable components so the interface can be maintained separately from the research workflow logic.

## Important limitation

This prototype extracts selectable PDF text. Scanned PDFs require OCR, and figure/table understanding requires a multimodal document-analysis layer. AI-generated research output should always be verified against the original paper.

