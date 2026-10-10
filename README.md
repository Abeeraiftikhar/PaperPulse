# \# PaperPulse - Professional UI Edition

# 

# A Streamlit research-analysis workspace that turns research-paper PDFs into structured insight: extract methods, results and gaps, compare studies, build evidence matrices, chat across your library, draft literature reviews, and export Markdown or PDF reports. It uses the Gemini API and supports light and dark themes.

# 

# \## Run on Windows

# 

# ```

# py -m pip install -r requirements.txt

# py -m streamlit run app.py

# ```

# 

# \## API key

# 

# Create a file `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`) and add:

# 

# ```

# GEMINI\_API\_KEY = "your\_key\_here"

# GEMINI\_MODEL = "gemini-3.6-flash"

# ```

# 

# On Streamlit Cloud, paste the same two lines in \*\*Advanced settings -> Secrets\*\*. Never upload your real key to GitHub.

# 

# \## Included modules

# 

# \* Research Library

# \* Paper Intelligence

# \* Compare Papers

# \* Evidence Matrix

# \* Research Chat

# \* Literature Review

# \* Export Report

# \* How It Works

# \* Light / Dark theme switch

# 

# \## UI structure

# 

# The `ui/` folder contains the visual design system and reusable components so the interface can be maintained separately from the research workflow logic.

# 

# \## Important limitation

# 

# This prototype extracts selectable PDF text. Scanned PDFs require OCR, and figure/table understanding requires a multimodal document-analysis layer. AI-generated research output should always be verified against the original paper.

