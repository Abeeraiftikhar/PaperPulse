import os
import io
import re
import json
import time
import hashlib
from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch

from ui.styles import theme_tokens, inject_css
from ui.components import page_header, section_head, footer

st.set_page_config(page_title="AI Research Intelligence", page_icon=None, layout="wide", initial_sidebar_state="collapsed")


# =====================================================================
# secrets
# =====================================================================
def get_secret(name, default=""):
    """Read a value from .streamlit/secrets.toml (or Streamlit Cloud Secrets), then from environment variables."""
    try:
        value = st.secrets[name]
        if value not in (None, ""):
            return value
    except Exception:
        pass
    return os.getenv(name, default)


# The ONE shared API key. Read from secrets / environment only, never shown in the UI.
API_KEY = str(get_secret("GEMINI_API_KEY", "") or get_secret("GOOGLE_API_KEY", "")).strip()

try:
    MAX_AI_CALLS = int(get_secret("MAX_AI_CALLS_PER_SESSION", 60))
except Exception:
    MAX_AI_CALLS = 60


# =====================================================================
# models
# =====================================================================
# Defaults + models your key can really use (asked from the API) + automatic fallback on 404.
# To force one model, set GEMINI_MODEL = "model-name" in .streamlit/secrets.toml.
DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-flash-latest"]
_SKIP_WORDS = ("image", "tts", "live", "audio", "native", "robotics", "computer-use", "embedding", "imagen", "veo")


@st.cache_data(ttl=3600, show_spinner=False)
def list_available_models(key):
    if not key:
        return []
    try:
        tmp = genai.Client(api_key=key)
        names = []
        for m in tmp.models.list():
            name = (getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if (
                name.startswith("gemini")
                and "flash" in name
                and ("generateContent" in actions or not actions)
                and not any(w in name for w in _SKIP_WORDS)
            ):
                names.append(name)
        return sorted(set(names), reverse=True)[:8]
    except Exception:
        return []


MODELS = list(DEFAULT_MODELS)
for _m in list_available_models(API_KEY):
    if _m not in MODELS:
        MODELS.append(_m)
_env_model = str(get_secret("GEMINI_MODEL", "")).strip()
if _env_model:
    if _env_model in MODELS:
        MODELS.remove(_env_model)
    MODELS.insert(0, _env_model)

# Analysis depth = how much paper text is sent to the AI. Less text = much faster.
DEPTHS = {"Fast (recommended)": 50000, "Balanced": 110000, "Thorough (slow)": 220000}


# =====================================================================
# state
# =====================================================================
DEFAULTS = {
    "theme": "dark",
    "page": "Research Library",
    "papers": {},
    "analyses": {},
    "comparison": "",
    "chat": [],
    "evidence_df": None,
    "model": MODELS[0],
    "depth": "Fast (recommended)",
    "ai_calls": 0,
    "cache": {},
    "thinking_cfg_rejected": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value
if st.session_state.model not in MODELS:
    st.session_state.model = MODELS[0]
if st.session_state.depth not in DEPTHS:
    st.session_state.depth = "Fast (recommended)"

tokens = theme_tokens(st.session_state.theme)
st.markdown(inject_css(tokens), unsafe_allow_html=True)

NOT_CONFIGURED = (
    "The AI service is not configured yet. The site owner needs to add GEMINI_API_KEY "
    "to .streamlit/secrets.toml (or the hosting platform's Secrets) and restart the app."
)


# =====================================================================
# PDF / text helpers
# =====================================================================
def extract_pdf(uploaded):
    reader = PdfReader(uploaded)
    pages = []
    for i, page in enumerate(reader.pages, 1):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        pages.append(f"\n--- PAGE {i} ---\n{txt}")
    text = "\n".join(pages).strip()
    return text, len(reader.pages)


def trim_text(text, limit):
    """Keep the beginning (abstract/intro/methods) and the end (results/conclusion) of long papers."""
    if len(text) <= limit:
        return text
    head = int(limit * 0.6)
    tail = limit - head
    return text[:head] + "\n\n[... middle of paper omitted for speed ...]\n\n" + text[-tail:]


def depth_chars():
    return DEPTHS.get(st.session_state.depth, 50000)


def paper_context(papers):
    """Build the multi-paper context. The total size is shared between papers."""
    n = max(1, len(papers))
    per_paper = max(6000, depth_chars() // n)
    return "\n".join(
        f"\n===== PAPER: {name} | {data['pages']} pages =====\n{trim_text(data['text'], per_paper)}"
        for name, data in papers.items()
    )


def make_pdf(title, body):
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=.65*inch, leftMargin=.65*inch, topMargin=.65*inch, bottomMargin=.65*inch)
        styles = getSampleStyleSheet()
        story = [Paragraph(title, styles["Title"]), Spacer(1, 12), Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]), Spacer(1, 16)]
        for block in body.split("\n"):
            if block.strip():
                safe = block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                safe = safe.encode("cp1252", "replace").decode("cp1252")
                story += [Paragraph(safe, styles["BodyText"]), Spacer(1, 7)]
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return None


def process_uploads(uploads):
    progress = st.progress(0)
    ok = 0
    for i, file in enumerate(uploads, 1):
        try:
            text, pages = extract_pdf(file)
            if not text.replace("--- PAGE", "").strip():
                st.warning(f"{file.name}: no selectable text found (scanned PDF?). OCR is not included.")
            st.session_state.papers[file.name] = {"text": text, "pages": pages, "chars": len(text)}
            ok += 1
        except Exception as exc:
            st.error(f"{file.name}: {exc}")
        progress.progress(i / len(uploads))
    if ok:
        st.success(f"Library updated: {len(st.session_state.papers)} paper(s) loaded.")


def go(page):
    st.session_state.page = page
    st.rerun()


# =====================================================================
# AI layer (fast + never crashes the page)
# =====================================================================
@st.cache_resource(show_spinner=False)
def get_client(key):
    if not key:
        return None
    try:
        # 90 s timeout so a request can never hang forever
        return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=90000))
    except Exception:
        return genai.Client(api_key=key)


def _classify(exc):
    msg = str(exc)
    low = msg.lower()
    if "404" in msg or "not_found" in low or "no longer available" in low or "is not found" in low:
        return "missing"
    if "think" in low and ("400" in msg or "invalid_argument" in low):
        return "thinking"
    if any(t in msg for t in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL", "DEADLINE")) or any(
        t in low for t in ("timeout", "timed out", "readtimeout", "connection")
    ):
        return "temporary"
    return "fatal"


def _make_config(thinking_off, json_mode):
    kwargs = {"temperature": 0.3, "max_output_tokens": 8192}
    if json_mode:
        kwargs["response_mime_type"] = "application/json"
    if thinking_off:
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)  # no hidden "thinking" = much faster
        except Exception:
            pass
    return types.GenerateContentConfig(**kwargs)


def _generate(client, model, prompt, cfg, placeholder):
    if placeholder is None:
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        return getattr(resp, "text", None) or ""
    text = ""
    for chunk in client.models.generate_content_stream(model=model, contents=prompt, config=cfg):
        piece = getattr(chunk, "text", None)
        if piece:
            text += piece
            placeholder.markdown(text + " ▌")
    placeholder.markdown(text)
    return text


def call_ai(client, prompt, model, placeholder=None, json_mode=False, max_chars=260000):
    """Send a prompt. Streams to `placeholder` if given. Falls back to other models on 404.
    Raises an exception only after everything has been tried; callers catch it and show a message."""
    if st.session_state.ai_calls >= MAX_AI_CALLS:
        raise RuntimeError(f"Session limit of {MAX_AI_CALLS} AI requests reached. Refresh the page to start a new session.")

    prompt = prompt[:max_chars]
    cache_key = hashlib.md5((("J" if json_mode else "T") + prompt).encode("utf-8", "ignore")).hexdigest()
    if cache_key in st.session_state.cache:
        text = st.session_state.cache[cache_key]
        if placeholder is not None:
            placeholder.markdown(text)
        return text

    candidates = [model] + [m for m in MODELS if m != model]
    last_exc = None
    for cand in candidates[:4]:
        thinking_off = not st.session_state.thinking_cfg_rejected
        retried = False
        while True:
            try:
                text = _generate(client, cand, prompt, _make_config(thinking_off, json_mode), placeholder)
                if not text.strip():
                    raise RuntimeError("The AI returned an empty response (it may have been blocked). Please try again.")
                st.session_state.ai_calls += 1
                st.session_state.cache[cache_key] = text
                if cand != model:
                    st.session_state.model = cand
                return text
            except Exception as exc:
                last_exc = exc
                kind = _classify(exc)
                if kind == "thinking" and thinking_off:
                    st.session_state.thinking_cfg_rejected = True
                    thinking_off = False
                    continue
                if kind == "temporary" and not retried:
                    retried = True
                    time.sleep(3)
                    continue
                if kind in ("missing", "temporary"):
                    break  # try the next model
                raise
    raise last_exc if last_exc else RuntimeError("No AI model could be reached.")


def ai_error(exc):
    """Friendly message + technical details. Never raises."""
    try:
        print(f"[AI request failed] {exc}")
    except Exception:
        pass
    msg = str(exc)
    low = msg.lower()
    if "429" in msg or "resource_exhausted" in low or "quota" in low:
        st.error("The AI service hit its free usage limit (per-minute or daily). Wait a minute and try again.")
    elif "api key" in low or "api_key_invalid" in low or "permission_denied" in low or "403" in msg or "401" in msg:
        st.error("The API key is invalid or not allowed. Check GEMINI_API_KEY in .streamlit/secrets.toml.")
    elif "404" in msg or "not_found" in low:
        st.error("None of the AI models are available for this key. Set GEMINI_MODEL in .streamlit/secrets.toml to a model your key supports, then restart.")
    elif "timeout" in low or "timed out" in low:
        st.error("The AI took too long. Set Analysis depth to 'Fast' in Workspace settings and try again.")
    else:
        st.error("The AI request failed. Open 'Technical details' below to see why.")
    with st.expander("Technical details"):
        st.code(msg[:1500])


def run_ai(prompt, placeholder=None, json_mode=False):
    """Wrapper used by every page: returns text or None (error already shown)."""
    client = get_client(API_KEY)
    if client is None:
        st.error(NOT_CONFIGURED)
        return None
    try:
        return call_ai(client, prompt, st.session_state.model, placeholder=placeholder, json_mode=json_mode)
    except Exception as exc:
        if placeholder is not None:
            try:
                placeholder.empty()
            except Exception:
                pass
        ai_error(exc)
        return None


def parse_matrix(raw):
    """Turn the AI answer (JSON preferred, CSV as backup) into a DataFrame. Returns None if impossible."""
    cols = ["Paper", "Research Problem", "Objective", "Methodology", "Dataset/Sample", "Key Finding", "Limitation", "Research Gap"]
    cleaned = re.sub(r"^```(?:json|csv)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [data])
        df = pd.DataFrame(data)
        for c in cols:
            if c not in df.columns:
                df[c] = "Not stated"
        return df[cols + [c for c in df.columns if c not in cols]]
    except Exception:
        pass
    try:
        lines = [x.strip() for x in cleaned.splitlines() if x.strip()]
        start = next((i for i, x in enumerate(lines) if x.lstrip('"').startswith("Paper")), None)
        if start is not None:
            return pd.read_csv(StringIO("\n".join(lines[start:])), on_bad_lines="skip")
    except Exception:
        pass
    return None


# =====================================================================
# header
# =====================================================================
with st.container(key="ari_nav"):
    st.markdown('''<div class="ari-brand"><div class="ari-mark">AI</div><div class="ari-brand-text"><div class="ari-brand-name">AI Research Intelligence</div><div class="ari-brand-sub"><span class="ari-brand-platform">AI Research Platform</span><span class="ari-brand-dot"></span><span class="ari-brand-tag">Evidence to insight to synthesis</span></div></div></div>''', unsafe_allow_html=True)

with st.container(key="ari_menu"):
    m1, m2, m3, m4, m5 = st.columns([1, 1.15, 1.45, .8, 3.6], vertical_alignment="center")
    with m1:
        if st.button("Discover", key="nav_discover", width="stretch"): go("Research Library")
    with m2:
        if st.button("How it works", key="nav_how", width="stretch"): go("How It Works")
    with m3:
        if st.button("Open workspace", key="nav_workspace", type="primary", width="stretch"): go("Library")
    with m4:
        theme_text = "Light" if st.session_state.theme == "dark" else "Dark"
        if st.button(theme_text, key="theme_switch", width="stretch"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

# --------------------------- workspace settings ---------------------------
with st.expander("Workspace settings", expanded=False):
    s1, s2, s3 = st.columns([1.4, 1, 1])
    with s1:
        if API_KEY:
            st.caption("AI service connected. No API key needed.")
        else:
            st.caption("AI service not configured. The site owner must set GEMINI_API_KEY in secrets.")
        if st.button("Test AI connection", key="test_ai"):
            with st.spinner("Testing..."):
                out = run_ai("Reply with the single word: OK")
            if out:
                st.success(f"Connected. Model in use: {st.session_state.model}")
    with s2:
        _current = st.session_state.model if st.session_state.model in MODELS else MODELS[0]
        st.session_state.model = st.selectbox("AI model", MODELS, index=MODELS.index(_current))
    with s3:
        _d = list(DEPTHS)
        st.session_state.depth = st.selectbox("Analysis depth", _d, index=_d.index(st.session_state.depth))

# =====================================================================
# landing page
# =====================================================================
if st.session_state.page == "Research Library":
    st.markdown(f'''
    <div class="ari-hero">
      <div>
        <div class="ari-kicker">AI-POWERED RESEARCH INTELLIGENCE</div>
        <h1 class="ari-title">Turn research papers into <span class="accent">structured intelligence.</span></h1>
        <p class="ari-copy">Upload a paper or a small literature set. Extract evidence, understand methods and findings, compare studies, identify research gaps, and build a literature-review synthesis from one focused workspace.</p>
      </div>
      <div class="ari-preview">
        <div class="ari-glow"></div>
        <div class="ari-preview-card">
          <span class="ari-status">Workspace ready</span>
          <div class="ari-eyebrow">Research intelligence workspace</div>
          <div class="ari-preview-title">From papers to evidence</div>
          <div class="ari-preview-sub">A guided workflow for academic analysis</div>
          <div class="ari-metrics"><div class="ari-metric"><strong>01</strong><small>Extract</small></div><div class="ari-metric"><strong>02</strong><small>Analyze</small></div><div class="ari-metric"><strong>03</strong><small>Compare</small></div><div class="ari-metric"><strong>04</strong><small>Synthesize</small></div></div>
          <div class="ari-list"><div class="ari-list-row"><span class="ari-num">01</span> Research problem and objective</div><div class="ari-list-row"><span class="ari-num">02</span> Methods, evidence and findings</div><div class="ari-list-row"><span class="ari-num">03</span> Limitations and research gaps</div><div class="ari-list-row"><span class="ari-num">04</span> Cross-paper synthesis</div></div>
        </div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        if st.button("Build research workspace", type="primary", width="stretch"):
            go("Library")
    with b:
        if st.button("See how it works", width="stretch"): go("How It Works")

    st.markdown('''<div class="ari-checks"><span>Evidence-focused analysis</span><span>Multi-paper comparison</span><span>Research-gap discovery</span><span>Portable reports</span></div>''', unsafe_allow_html=True)

    section_head("What the workspace does", "A focused set of tools that move from document extraction to structured research reasoning.")
    cols = st.columns(4)
    cards = [
        ("01", "Paper intelligence", "Extract research questions, methodology, results, limitations and contributions from individual studies."),
        ("02", "Compare studies", "Place multiple papers into one analytical frame and surface agreement, disagreement and methodological differences."),
        ("03", "Evidence matrix", "Turn a literature set into a structured table for review planning and research-gap analysis."),
        ("04", "Literature synthesis", "Build a cross-paper narrative and export the work as a reusable research report."),
    ]
    for col, (num, title, copy) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="ari-card"><div class="ari-card-number">{num}</div><div class="ari-card-title">{title}</div><div class="ari-card-copy">{copy}</div></div>', unsafe_allow_html=True)

    section_head("How it works", "Five clear stages keep the research workflow understandable from upload to final synthesis.")
    flow = [
        ("01", "Upload", "Add one or more selectable-text research papers."),
        ("02", "Extract", "Create a searchable text context from each document."),
        ("03", "Analyze", "Inspect questions, methods, results, limitations and gaps."),
        ("04", "Compare", "Connect studies through evidence and methodological differences."),
        ("05", "Synthesize", "Build a literature narrative and export the result."),
    ]
    flow_html = '<div class="ari-flow">'
    for n, title, copy in flow:
        flow_html += f'<div class="ari-step"><div class="ari-step-dot">{n}</div><div class="ari-step-title">{title}</div><div class="ari-step-copy">{copy}</div></div>'
    flow_html += '</div>'
    st.markdown(flow_html, unsafe_allow_html=True)

    section_head("Research workflow modules", "Click a module to open it. Load your papers in the library first.")
    tools = [
        ("Paper Intelligence", "Deep analysis of one selected paper."),
        ("Compare Papers", "Cross-study methodological and result comparison."),
        ("Evidence Matrix", "Structured evidence table for review planning."),
        ("Research Chat", "Ask questions across the uploaded library."),
        ("Literature Review", "Generate a synthesis draft from the library."),
        ("Export Report", "Package analysis into Markdown or PDF."),
    ]
    st.markdown("""
    <style>
    [class*="st-key-tool_"] { position: relative; gap: 0 !important; cursor: pointer; transition: transform .15s ease; }
    [class*="st-key-tool_"]:hover { transform: translateY(-2px); }
    [class*="st-key-tool_"] [data-testid="stButton"],
    [class*="st-key-tool_"] .stButton {
        position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important; margin: 0 !important;
    }
    [class*="st-key-tool_"] [data-testid="stButton"] button,
    [class*="st-key-tool_"] .stButton button {
        width: 100% !important; height: 100% !important; opacity: 0 !important; cursor: pointer !important;
    }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for i, (title, copy) in enumerate(tools):
        with cols[i % 3]:
            with st.container(key=f"tool_{i}"):
                st.markdown(f'<div class="ari-tool"><div class="ari-tool-title">{title}</div><div class="ari-tool-copy">{copy}</div></div>', unsafe_allow_html=True)
                if st.button(title, key=f"tool_btn_{i}", width="stretch"):
                    go(title)

    section_head("Start with your literature", "The library is the working foundation for every analysis module.")
    uploads = st.file_uploader("Upload research papers", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed", key="landing_uploader")
    if uploads:
        if st.button("Process uploaded papers", type="primary", width="stretch", key="landing_process"):
            process_uploads(uploads)

    if st.session_state.papers:
        cols = st.columns(3)
        cols[0].metric("Papers", len(st.session_state.papers))
        cols[1].metric("Pages", sum(x["pages"] for x in st.session_state.papers.values()))
        cols[2].metric("Extracted characters", f"{sum(x['chars'] for x in st.session_state.papers.values()):,}")
        rows = [{"Paper": name, "Pages": data["pages"], "Text characters": data["chars"]} for name, data in st.session_state.papers.items()]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.info("Upload one or more papers to activate the research workspace.")

# =====================================================================
# how it works
# =====================================================================
elif st.session_state.page == "How It Works":
    page_header("WORKFLOW", "From document to research insight.", "AI Research Intelligence separates the research task into clear stages so users can understand what is happening at every point of the workflow.")
    steps = [
        ("01", "Build the library", "Upload one or more selectable-text PDF papers. Each document is stored in the current session as a research source."),
        ("02", "Extract evidence", "The system extracts page-level text and preserves page markers so the analysis has a traceable document context."),
        ("03", "Run focused analysis", "Choose a research question, methodology, results, limitations, novelty or research-gap analysis for an individual paper."),
        ("04", "Compare the literature", "Select multiple papers to identify shared problems, methodological differences, agreement, disagreement and cross-study gaps."),
        ("05", "Build structured evidence", "Generate an evidence matrix that turns the literature set into a reusable research-planning table."),
        ("06", "Synthesize and export", "Ask questions across the library, draft a literature review, and export the working result as Markdown or PDF."),
    ]
    cols = st.columns(3)
    for i, (num, title, copy) in enumerate(steps):
        with cols[i % 3]:
            st.markdown(f'<div class="ari-card" style="margin-bottom:14px"><div class="ari-card-number">{num}</div><div class="ari-card-title">{title}</div><div class="ari-card-copy">{copy}</div></div>', unsafe_allow_html=True)
    section_head("What happens to your papers", "The current prototype is deliberately transparent: document text is extracted first, then passed into the selected analysis workflow.")
    st.markdown('''<div class="ari-tools"><div class="ari-tool"><div class="ari-tool-title">Document layer</div><div class="ari-tool-copy">PDF text extraction and page markers.</div></div><div class="ari-tool"><div class="ari-tool-title">Reasoning layer</div><div class="ari-tool-copy">Focused prompts for evidence-based research analysis.</div></div><div class="ari-tool"><div class="ari-tool-title">Synthesis layer</div><div class="ari-tool-copy">Cross-paper comparison and literature-review drafting.</div></div><div class="ari-tool"><div class="ari-tool-title">Output layer</div><div class="ari-tool-copy">Tables, Markdown reports and PDF reports.</div></div></div>''', unsafe_allow_html=True)

# =====================================================================
# workspace pages
# =====================================================================
elif st.session_state.page in {"Library", "Paper Intelligence", "Compare Papers", "Evidence Matrix", "Research Chat", "Literature Review", "Export Report", "About"}:
    page = st.session_state.page
    labels = ["Library", "Paper Intelligence", "Compare Papers", "Evidence Matrix", "Research Chat", "Literature Review", "Export Report", "About"]
    nav_cols = st.columns(len(labels))
    for i, label in enumerate(labels):
        with nav_cols[i]:
            if st.button(label, key=f"workspace_{i}", width="stretch"): go(label)
    st.markdown("<hr>", unsafe_allow_html=True)

    # ------------------------------------------------------------ Library
    if page == "Library":
        page_header("RESEARCH LIBRARY", "Your literature workspace.", "Load the papers you want to analyze. Every downstream module uses the documents stored here.")
        uploads = st.file_uploader("Upload research papers", type=["pdf"], accept_multiple_files=True, key="library_uploader")
        if uploads and st.button("Process uploaded papers", type="primary", width="stretch", key="library_process"):
            process_uploads(uploads)
        if st.session_state.papers:
            rows = [{"Paper": n, "Pages": d["pages"], "Extracted characters": d["chars"]} for n, d in st.session_state.papers.items()]
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("No papers loaded yet.")

    # ------------------------------------------------------------ Paper Intelligence
    elif page == "Paper Intelligence":
        page_header("ANALYSIS", "Paper intelligence.", "Turn one paper into a structured research profile without mixing it with unrelated documents.")
        if not st.session_state.papers:
            st.warning("Upload and process at least one paper first.")
        elif not API_KEY:
            st.error(NOT_CONFIGURED)
        else:
            selected = st.selectbox("Select paper", list(st.session_state.papers))
            actions = {
                "Executive summary": "Create an executive research summary with problem, significance, approach, main result, contribution and one-sentence takeaway.",
                "Research question": "Extract the main research question, hypotheses if present, objectives and motivation. Distinguish explicit statements from interpretation.",
                "Methodology": "Create a reproducible methodology breakdown covering study design, data/sample, preprocessing, experiments/computation, tools, evaluation and statistics when available.",
                "Results": "Summarize the most important reported results and preserve meaningful numerical comparisons only when present in the source.",
                "Limitations": "List author-stated limitations, then separate cautious evidence-based methodological limitations. Never present speculation as fact.",
                "Research gaps": "Identify unanswered questions, limitations that create opportunities, future work and specific research gaps supported by the paper.",
                "Novelty and contribution": "Assess what is new. Separate explicit author claims from cautious assessment and explain the contribution to the field.",
            }
            choice = st.selectbox("Analysis module", list(actions))
            live = st.empty()  # streaming output appears here
            if st.button("Run intelligence analysis", type="primary", width="stretch"):
                prompt = (
                    "You are an expert research analyst. Analyze the supplied paper for an academic user. "
                    "Do not invent information. Use only evidence present in the supplied text. Be concise and well structured.\n\n"
                    f"TASK:\n{actions[choice]}\n\nPAPER:\n{trim_text(st.session_state.papers[selected]['text'], depth_chars())}"
                )
                answer = run_ai(prompt, placeholder=live)
                if answer:
                    st.session_state.analyses.setdefault(selected, {})[choice] = answer
                    st.rerun()
            for title, answer in st.session_state.analyses.get(selected, {}).items():
                st.markdown(f'<div class="ari-card"><div class="ari-card-title">{title}</div></div>', unsafe_allow_html=True)
                st.markdown(answer)

    # ------------------------------------------------------------ Compare Papers
    elif page == "Compare Papers":
        page_header("COMPARATIVE ANALYSIS", "Compare papers with context.", "Move from isolated summaries to a structured view of how studies differ in questions, methods, findings and gaps.")
        if len(st.session_state.papers) < 2:
            st.info("Upload at least two papers to activate comparative analysis.")
        elif not API_KEY:
            st.error(NOT_CONFIGURED)
        else:
            selected = st.multiselect("Select papers", list(st.session_state.papers), default=list(st.session_state.papers)[:min(3, len(st.session_state.papers))])
            clicked = len(selected) >= 2 and st.button("Generate comparative analysis", type="primary", width="stretch")
            live = st.empty()
            if clicked:
                prompt = (
                    "You are a comparative literature analyst. Compare the selected research papers using ONLY the supplied text. "
                    "Be concise. Produce these sections: shared research problem; objective differences; methodology comparison; "
                    "dataset/sample comparison; key findings comparison; strengths and limitations; agreement/disagreement; "
                    "cross-paper research gap; short literature-rpy -3.14 -m streamlit run app.pyeview synthesis.\n\n"
                    f"PAPERS:\n{paper_context({k: st.session_state.papers[k] for k in selected})}"
                )
                result = run_ai(prompt, placeholder=live)
                if result:
                    st.session_state.comparison = result
                    st.rerun()
            elif st.session_state.comparison:
                live.markdown(st.session_state.comparison)

    # ------------------------------------------------------------ Evidence Matrix
    elif page == "Evidence Matrix":
        page_header("STRUCTURED EVIDENCE", "Evidence matrix.", "Create a research-planning table that makes methods, findings, limitations and gaps easier to compare.")
        if not st.session_state.papers:
            st.warning("Upload papers first.")
        elif not API_KEY:
            st.error(NOT_CONFIGURED)
        else:
            if st.button("Build evidence matrix", type="primary", width="stretch"):
                prompt = (
                    "Create an evidence matrix for the supplied research papers. Return ONLY a JSON array with one object per paper. "
                    'Each object must have exactly these keys: "Paper", "Research Problem", "Objective", "Methodology", '
                    '"Dataset/Sample", "Key Finding", "Limitation", "Research Gap". Keep every value to one or two short sentences. '
                    'Use "Not stated" when information is absent. Do not invent information.\n\n'
                    f"PAPERS:\n{paper_context(st.session_state.papers)}"
                )
                with st.spinner("Building evidence matrix..."):
                    raw = run_ai(prompt, json_mode=True)
                if raw:
                    df = parse_matrix(raw)
                    if df is not None:
                        st.session_state.evidence_df = df
                    else:
                        st.session_state.evidence_df = None
                        st.warning("The AI answered in an unexpected format. Raw answer shown below.")
                        st.code(raw)
            if st.session_state.evidence_df is not None:
                st.dataframe(st.session_state.evidence_df, width="stretch", hide_index=True)
                st.download_button("Download evidence matrix CSV", st.session_state.evidence_df.to_csv(index=False), file_name="research_evidence_matrix.csv", mime="text/csv", width="stretch")

    # ------------------------------------------------------------ Research Chat
    elif page == "Research Chat":
        page_header("RESEARCH CHAT", "Ask across your literature.", "Use the uploaded research library as the context for focused questions. If the sources do not contain enough information, the assistant is instructed to say so.")
        if not st.session_state.papers:
            st.warning("Upload papers first.")
        elif not API_KEY:
            st.error(NOT_CONFIGURED)
        else:
            for item in st.session_state.chat:
                with st.chat_message(item["role"]):
                    st.markdown(item["content"])
            question = st.chat_input("Ask about your research library")
            if question:
                st.session_state.chat.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    live = st.empty()
                    history = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat[-7:-1])
                    prompt = (
                        "Answer the user's research question using ONLY the supplied papers. Name relevant papers when useful. "
                        "If the papers do not contain enough information, say so instead of guessing. Be concise.\n\n"
                        f"EARLIER CONVERSATION:\n{history or '(none)'}\n\nQUESTION:\n{question}\n\nRESEARCH LIBRARY:\n{paper_context(st.session_state.papers)}"
                    )
                    ans = run_ai(prompt, placeholder=live)
                    if ans:
                        st.session_state.chat.append({"role": "assistant", "content": ans})

    # ------------------------------------------------------------ Literature Review
    elif page == "Literature Review":
        page_header("SYNTHESIS", "Literature review builder.", "Move from individual paper notes to a structured cross-paper synthesis for your next research draft.")
        if not st.session_state.papers:
            st.warning("Upload papers first.")
        elif not API_KEY:
            st.error(NOT_CONFIGURED)
        else:
            clicked = st.button("Generate literature-review synthesis", type="primary", width="stretch")
            live = st.empty()
            if clicked:
                prompt = (
                    "You are an academic literature-review assistant. Using ONLY the supplied papers, create a structured literature-review draft "
                    "covering: research-area overview; major themes; methodological patterns; agreement; disagreement; evolution/contrast; "
                    "research gaps; future research directions; coherent synthesis paragraph. Do not fabricate references. "
                    "Identify papers by filename when bibliographic details are unavailable.\n\n"
                    f"PAPERS:\n{paper_context(st.session_state.papers)}"
                )
                result = run_ai(prompt, placeholder=live)
                if result:
                    st.session_state.analyses["__literature_review__"] = {"Synthesis": result}
                    st.rerun()
            review = st.session_state.analyses.get("__literature_review__", {}).get("Synthesis", "")
            if review and not clicked:
                live.markdown(review)
            if review:
                st.download_button("Download literature review TXT", review, file_name="literature_review_synthesis.txt", mime="text/plain", width="stretch")

    # ------------------------------------------------------------ Export Report
    elif page == "Export Report":
        page_header("OUTPUT", "Export your research report.", "Package the current session into a portable Markdown or PDF report.")
        if not st.session_state.papers:
            st.warning("Analyze at least one paper first.")
        else:
            parts = ["# AI Research Intelligence Report", "", f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", "", "## Research Library"]
            for name, data in st.session_state.papers.items():
                parts.append(f"- {name} — {data['pages']} pages")
            for paper, modules in st.session_state.analyses.items():
                if paper.startswith("__"):
                    continue
                parts.append(f"\n## {paper}")
                for title, answer in modules.items():
                    parts.append(f"\n### {title}\n{answer}")
            if st.session_state.comparison:
                parts.append("\n## Comparative Synthesis\n" + st.session_state.comparison)
            review = st.session_state.analyses.get("__literature_review__", {}).get("Synthesis", "")
            if review:
                parts.append("\n## Literature Review\n" + review)
            report = "\n".join(parts)
            st.text_area("Report preview", report, height=480)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("Download Markdown report", report, file_name="ai_research_intelligence_report.md", mime="text/markdown", width="stretch")
            with c2:
                pdf_bytes = make_pdf("AI Research Intelligence Report", report)
                if pdf_bytes:
                    st.download_button("Download PDF report", pdf_bytes, file_name="ai_research_intelligence_report.pdf", mime="application/pdf", width="stretch")
                else:
                    st.caption("PDF could not be generated for this content. Use the Markdown download.")

    # ------------------------------------------------------------ About
    else:
        page_header("ABOUT", "Built for structured research thinking.", "AI Research Intelligence is designed to help researchers move from reading papers to organizing evidence, comparing studies and drafting synthesis.")
        st.markdown('''<div class="ari-tools"><div class="ari-tool"><div class="ari-tool-title">Research library</div><div class="ari-tool-copy">Work with a focused collection of papers in one session.</div></div><div class="ari-tool"><div class="ari-tool-title">Evidence-first prompts</div><div class="ari-tool-copy">Analysis instructions explicitly discourage unsupported claims.</div></div><div class="ari-tool"><div class="ari-tool-title">Cross-paper reasoning</div><div class="ari-tool-copy">Compare methods, findings, limitations and research gaps.</div></div><div class="ari-tool"><div class="ari-tool-title">Transparent limits</div><div class="ari-tool-copy">Current prototype uses selectable PDF text; scanned-document OCR is not included.</div></div></div>''', unsafe_allow_html=True)

footer()