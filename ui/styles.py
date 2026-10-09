"""Visual design system for AI Research Intelligence."""


def theme_tokens(mode: str):
    dark = mode == "dark"
    if dark:
        return {
            "bg": "#070914", "bg2": "#0B1020", "surface": "#10162A", "surface2": "#141C33",
            "surface3": "#0D1324", "text": "#F5F7FF", "muted": "#9AA6BF", "subtle": "#737F99",
            "border": "#27314B", "primary": "#6D5DF6", "primary2": "#8B7CFF", "cyan": "#39D8FF",
            "green": "#43D49B", "danger": "#FF6B7A", "shadow": "rgba(0,0,0,.34)",
        }
    return {
        "bg": "#F6F8FC", "bg2": "#EEF2F9", "surface": "#FFFFFF", "surface2": "#F2F5FB",
        "surface3": "#EAF0F8", "text": "#101A33", "muted": "#65728B", "subtle": "#8792A8",
        "border": "#DCE3EF", "primary": "#5D52E8", "primary2": "#766AF5", "cyan": "#149FC8",
        "green": "#129D73", "danger": "#D94D61", "shadow": "rgba(29,43,72,.10)",
    }


def inject_css(t):
    c = t
    return f"""
<style>
:root {{ --ari-bg:{c['bg']}; --ari-bg2:{c['bg2']}; --ari-surface:{c['surface']}; --ari-surface2:{c['surface2']};
--ari-surface3:{c['surface3']}; --ari-text:{c['text']}; --ari-muted:{c['muted']}; --ari-subtle:{c['subtle']};
--ari-border:{c['border']}; --ari-primary:{c['primary']}; --ari-primary2:{c['primary2']}; --ari-cyan:{c['cyan']};
--ari-green:{c['green']}; --ari-danger:{c['danger']}; --ari-shadow:{c['shadow']}; }}

/* ---------- App shell ---------- */
.stApp {{
  background:
    radial-gradient(circle at 83% 5%, {c['primary']}20 0, transparent 25%),
    radial-gradient(circle at 10% 38%, {c['cyan']}10 0, transparent 24%),
    linear-gradient(135deg, {c['bg']} 0%, {c['bg2']} 100%) !important;
  color:{c['text']};
}}
.stApp::before {{
  content:""; position:fixed; inset:0; pointer-events:none; opacity:.28; z-index:0;
  background-image:linear-gradient({c['border']}12 1px, transparent 1px),linear-gradient(90deg,{c['border']}12 1px,transparent 1px);
  background-size:48px 48px; mask-image:linear-gradient(to bottom, black, transparent 72%);
}}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background:transparent !important; }}
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{ display:none !important; }}
[data-testid="stToolbar"], [data-testid="stDeployButton"], [data-testid="stHeaderActionElements"], #MainMenu {{ display:none !important; }}
.stMarkdown h1 a, .stMarkdown h2 a {{ display:none !important; }}
.block-container {{ max-width:1180px; padding-top:1.2rem; padding-bottom:3.5rem; position:relative; z-index:1; }}

/* ---------- Top navigation ---------- */
.st-key-ari_nav {{
  padding:16px 20px; margin-bottom:34px;
  border:1px solid {c['border']}; border-radius:18px;
  background:linear-gradient(135deg,{c['surface']}E8,{c['surface2']}D8);
  backdrop-filter:blur(20px); box-shadow:0 18px 50px {c['shadow']};
  animation:navIn .7s ease both;
}}
.st-key-ari_nav [data-testid="stHorizontalBlock"] {{ align-items:center; gap:12px; }}
.ari-brand {{ display:flex; align-items:center; gap:14px; min-width:0; }}
.ari-mark {{
  width:46px; height:46px; flex:none; border-radius:14px; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,{c['primary']},{c['cyan']}); color:#fff; font-weight:900; font-size:14px;
  box-shadow:0 8px 24px {c['primary']}38; position:relative; overflow:hidden;
}}
.ari-mark::after {{ content:""; position:absolute; width:70px; height:18px; background:#fff3; transform:rotate(-35deg) translateX(-55px); animation:shine 4s infinite; }}
.ari-brand-text {{ line-height:1.3; }}
.ari-brand-name {{ font-size:17px; font-weight:850; letter-spacing:-.01em; color:{c['text']}; white-space:nowrap; }}
.ari-brand-platform {{ font-size:11px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:{c['primary2']}; margin-top:3px; }}
.ari-brand-tag {{ font-size:11px; color:{c['muted']}; margin-top:2px; }}

/* ---------- Buttons ---------- */
.stButton > button, [data-testid="stPopover"] > div > button {{
  border-radius:12px !important; border:1px solid {c['border']} !important; background:{c['surface']} !important;
  color:{c['text']} !important; font-weight:700 !important; min-height:42px !important; transition:all .22s ease !important;
}}
.stButton > button:hover, [data-testid="stPopover"] > div > button:hover {{
  transform:translateY(-2px); border-color:{c['primary2']} !important; box-shadow:0 10px 24px {c['shadow']};
}}
.stButton > button[kind="primary"] {{
  background:linear-gradient(135deg,{c['primary']},{c['primary2']}) !important; color:#fff !important; border:0 !important;
  box-shadow:0 12px 28px {c['primary']}38 !important;
}}

/* ---------- Hero ---------- */
.ari-hero {{ display:grid; grid-template-columns:1.05fr .95fr; gap:38px; align-items:center; margin-top:8px; margin-bottom:58px; animation:fadeUp .75s ease both; }}
.ari-kicker {{ color:{c['primary2']}; font-size:11px; letter-spacing:.18em; font-weight:850; text-transform:uppercase; margin-bottom:13px; }}
.ari-title {{ font-size:clamp(42px,5.2vw,67px); line-height:.98; letter-spacing:-.055em; color:{c['text']}; font-weight:850; margin:0 0 18px; }}
.ari-title .accent {{ background:linear-gradient(90deg,{c['primary2']},{c['cyan']}); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.ari-copy {{ color:{c['muted']}; font-size:16px; line-height:1.75; max-width:650px; margin:0 0 24px; }}
.ari-checks {{ display:flex; flex-wrap:wrap; gap:10px 22px; color:{c['muted']}; font-size:12px; margin-top:17px; }}
.ari-checks span::before {{ content:""; display:inline-block; width:6px; height:6px; border-radius:50%; background:{c['cyan']}; margin-right:8px; box-shadow:0 0 10px {c['cyan']}; }}

/* ---------- Preview card ---------- */
.ari-preview {{ position:relative; min-height:355px; }}
.ari-glow {{ position:absolute; width:230px; height:230px; border-radius:50%; background:{c['primary']}22; filter:blur(45px); right:8%; top:6%; animation:float 6s ease-in-out infinite; }}
.ari-preview-card {{ position:relative; background:linear-gradient(145deg,{c['surface']},{c['surface2']}); border:1px solid {c['border']}; border-radius:23px; padding:24px; box-shadow:0 24px 70px {c['shadow']}; animation:float 7s ease-in-out infinite; }}
.ari-eyebrow {{ font-size:10px; letter-spacing:.16em; text-transform:uppercase; color:{c['subtle']}; font-weight:800; }}
.ari-preview-title {{ font-size:25px; line-height:1.15; font-weight:820; color:{c['text']}; margin:10px 0 6px; }}
.ari-preview-sub {{ font-size:12px; color:{c['muted']}; }}
.ari-status {{ float:right; font-size:10px; color:{c['green']}; border:1px solid {c['green']}55; background:{c['green']}12; padding:5px 9px; border-radius:999px; }}
.ari-metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:22px 0; }}
.ari-metric {{ padding:12px; border:1px solid {c['border']}; border-radius:13px; background:{c['surface3']}; }}
.ari-metric strong {{ display:block; font-size:20px; color:{c['text']}; }}
.ari-metric small {{ font-size:9px; color:{c['muted']}; text-transform:uppercase; letter-spacing:.07em; }}
.ari-list {{ display:grid; gap:10px; margin-top:14px; }}
.ari-list-row {{ display:flex; align-items:center; gap:10px; color:{c['muted']}; font-size:12px; }}
.ari-num {{ width:22px; height:22px; flex:none; border:1px solid {c['primary2']}; border-radius:50%; display:flex; align-items:center; justify-content:center; color:{c['primary2']}; font-size:9px; }}

/* ---------- Sections / cards ---------- */
.ari-section-head {{ display:flex; justify-content:space-between; align-items:end; gap:20px; margin:68px 0 22px; }}
.ari-section-title {{ font-size:28px; line-height:1.05; color:{c['text']}; font-weight:840; letter-spacing:-.03em; }}
.ari-section-copy {{ color:{c['muted']}; font-size:13px; line-height:1.6; max-width:520px; }}
.ari-card {{ height:100%; padding:22px; border:1px solid {c['border']}; border-radius:18px; background:linear-gradient(145deg,{c['surface']},{c['surface2']}); box-shadow:0 12px 36px {c['shadow']}; transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease; animation:fadeUp .65s ease both; }}
.ari-card:hover {{ transform:translateY(-5px); border-color:{c['primary2']}88; box-shadow:0 18px 48px {c['shadow']}; }}
.ari-card-number {{ font-size:11px; color:{c['primary2']}; font-weight:850; letter-spacing:.12em; }}
.ari-card-title {{ font-size:17px; font-weight:800; color:{c['text']}; margin:12px 0 7px; }}
.ari-card-copy {{ font-size:12.5px; color:{c['muted']}; line-height:1.65; }}

/* ---------- How it works ---------- */
.ari-flow {{ display:grid; grid-template-columns:repeat(5,1fr); gap:0; position:relative; margin-top:25px; }}
.ari-flow::before {{ content:""; position:absolute; left:7%; right:7%; top:31px; height:1px; background:linear-gradient(90deg,transparent,{c['primary']}88,{c['cyan']}88,transparent); }}
.ari-step {{ position:relative; text-align:center; padding:0 8px; animation:fadeUp .7s ease both; }}
.ari-step-dot {{ width:62px; height:62px; margin:0 auto 15px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:{c['surface']}; border:1px solid {c['border']}; box-shadow:0 0 0 7px {c['bg']}ee,0 10px 28px {c['shadow']}; color:{c['primary2']}; font-weight:850; font-size:12px; position:relative; z-index:2; }}
.ari-step-dot::after {{ content:""; position:absolute; inset:-4px; border-radius:50%; border:1px solid {c['primary2']}44; animation:pulse 2.6s ease-out infinite; }}
.ari-step-title {{ font-size:13px; font-weight:800; color:{c['text']}; margin-bottom:5px; }}
.ari-step-copy {{ font-size:11.5px; color:{c['muted']}; line-height:1.55; }}

/* ---------- Tool strip ---------- */
.ari-tools {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-top:22px; }}
.ari-tool {{ padding:17px; border:1px solid {c['border']}; border-radius:15px; background:{c['surface']}; }}
.ari-tool-title {{ font-size:13px; font-weight:800; color:{c['text']}; margin-bottom:5px; }}
.ari-tool-copy {{ font-size:11.5px; line-height:1.5; color:{c['muted']}; }}

/* ---------- Page headers ---------- */
.ari-page-head {{ padding:30px 0 26px; margin-bottom:25px; border-bottom:1px solid {c['border']}; animation:fadeUp .55s ease both; }}
.ari-page-title {{ font-size:42px; line-height:1; color:{c['text']}; font-weight:850; letter-spacing:-.045em; margin:0 0 10px; }}
.ari-page-copy {{ font-size:14px; color:{c['muted']}; max-width:720px; line-height:1.7; margin:0; }}
.ari-label {{ font-size:10px; text-transform:uppercase; letter-spacing:.14em; color:{c['primary2']}; font-weight:850; margin-bottom:8px; }}

/* ---------- Streamlit controls ---------- */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {{
  background:{c['surface']} !important; color:{c['text']} !important; border-color:{c['border']} !important;
}}
label, [data-testid="stWidgetLabel"] p {{ color:{c['muted']} !important; font-size:12px !important; }}
.stCaption, [data-testid="stCaptionContainer"] {{ color:{c['muted']} !important; }}
[data-testid="stFileUploader"] {{ background:{c['surface']}; border:1px dashed {c['border']}; border-radius:16px; }}
[data-testid="stDataFrame"] {{ border:1px solid {c['border']}; border-radius:14px; overflow:hidden; }}
.stAlert {{ border-radius:14px !important; }}
hr {{ border-color:{c['border']} !important; }}

/* ---------- Footer ---------- */
.ari-footer {{ margin-top:76px; padding:30px 0 10px; border-top:1px solid {c['border']}; text-align:center; color:{c['muted']}; font-size:11px; line-height:1.9; }}
.ari-footer strong {{ color:{c['text']}; font-size:13px; }}

/* ---------- Animations ---------- */
@keyframes navIn {{ from{{opacity:0;transform:translateY(-12px)}} to{{opacity:1;transform:none}} }}
@keyframes fadeUp {{ from{{opacity:0;transform:translateY(16px)}} to{{opacity:1;transform:none}} }}
@keyframes float {{ 0%,100%{{transform:translateY(0)}} 50%{{transform:translateY(-8px)}} }}
@keyframes pulse {{ 0%{{transform:scale(.92);opacity:.7}} 70%,100%{{transform:scale(1.18);opacity:0}} }}
@keyframes shine {{ 0%{{transform:translateX(-80px) rotate(-35deg)}} 45%,100%{{transform:translateX(280px) rotate(-35deg)}} }}

/* ---------- Mobile ---------- */
@media (max-width:900px) {{
  .ari-hero {{ grid-template-columns:1fr; }}
  .ari-flow {{ grid-template-columns:1fr; gap:25px; }}
  .ari-flow::before {{ display:none; }}
  .ari-tools {{ grid-template-columns:1fr 1fr; }}
  .ari-metrics {{ grid-template-columns:1fr 1fr; }}
  .ari-brand-name {{ white-space:normal; }}
}}
</style>
"""