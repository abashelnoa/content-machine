"""
app.py — AI Content Studio | 4 Tabs
הרצה: streamlit run app.py
"""
import base64 as _b64
import io
import os
import re
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from PIL import Image

import data_loader
import generator
from generator import ASPECT_RATIOS, CONTENT_TYPES, LANGUAGES, PRESET_STYLES, MARKETING_FRAMEWORKS

load_dotenv()


@st.cache_data
def _get_font_b64() -> str:
    font_path = Path(__file__).parent / "font" / "Assistant-VariableFont_wght.ttf"
    try:
        return _b64.b64encode(font_path.read_bytes()).decode()
    except FileNotFoundError:
        return ""


st.set_page_config(
    page_title="AI Content Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
_font_b64 = _get_font_b64()
_font_face = f"""@font-face {{
    font-family: 'Assistant';
    src: url('data:font/truetype;base64,{_font_b64}') format('truetype');
    font-weight: 100 900;
    font-style: normal;
}}""" if _font_b64 else "@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;500;600;700&display=swap');"

st.markdown("<style>" + _font_face + """

*:not([data-testid="collapsedControl"]):not(.material-symbols-rounded):not(.material-symbols-outlined):not([class*="material"]) {
    font-family: 'Assistant', sans-serif !important;
}
.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d0d1a 40%, #0a1628 100%);
    font-family: 'Assistant', sans-serif;
    direction: rtl;
}
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.03) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }

.main-title {
    font-size: 2.8rem; font-weight: 700;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; text-align: center;
    margin-bottom: 0.2rem; letter-spacing: -0.02em;
}
.sub-title {
    text-align: center; color: rgba(255,255,255,0.4);
    font-size: 0.95rem; font-weight: 300;
    margin-bottom: 2.5rem; letter-spacing: 0.05em;
}
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px; padding: 1.8rem;
    backdrop-filter: blur(10px); margin-bottom: 1.2rem;
    transition: border-color 0.3s ease;
}
.glass-card:hover { border-color: rgba(167,139,250,0.3); }
.section-label {
    font-size: 0.7rem; font-weight: 600;
    letter-spacing: 0.15em; color: rgba(167,139,250,0.8);
    text-transform: uppercase; margin-bottom: 0.8rem;
}
.post-display {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px; padding: 1.6rem 2rem;
    color: rgba(255,255,255,0.88); font-size: 0.95rem;
    line-height: 1.9; direction: rtl; text-align: right;
    min-height: 300px; white-space: pre-wrap;
    font-family: 'Assistant', sans-serif;
}
.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #3b82f6) !important;
    color: white !important; border: none !important;
    border-radius: 14px !important; font-weight: 600 !important;
    font-size: 1rem !important; padding: 0.75rem 2rem !important;
    transition: all 0.3s ease !important; letter-spacing: 0.02em !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.35) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(124,58,237,0.5) !important;
}
.stDownloadButton > button {
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.8) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important; font-weight: 500 !important;
    transition: all 0.2s ease !important; box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.25) !important;
    transform: translateY(-1px) !important;
}
/* ── כל הטקסטים לבנים ── */
*, p, span, div, label, li {
    color: rgba(255,255,255,0.85);
}
.stApp, .stApp * {
    color: rgba(255,255,255,0.85);
}

/* selectbox — תיבה */
.stSelectbox > div > div,
[data-baseweb="select"] > div {
    background: #12122a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.88) !important;
    direction: rtl;
}
.stSelectbox span,
.stSelectbox [data-baseweb="select"] span,
[data-baseweb="select"] span {
    color: rgba(255,255,255,0.88) !important;
}

/* selectbox — dropdown רשימה נפתחת */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[role="listbox"],
[role="listbox"] {
    background: #1a1a35 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
}
[role="option"],
[data-baseweb="menu"] li,
li[role="option"] {
    background: #1a1a35 !important;
    color: rgba(255,255,255,0.85) !important;
}
[role="option"]:hover,
[data-baseweb="menu"] li:hover,
li[role="option"]:hover {
    background: rgba(124,58,237,0.3) !important;
    color: white !important;
}
[aria-selected="true"][role="option"] {
    background: rgba(124,58,237,0.4) !important;
    color: white !important;
}

/* textarea */
.stTextArea > div > div > textarea,
textarea,
[data-baseweb="textarea"] textarea,
[data-baseweb="base-input"] textarea {
    background: #12122a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.88) !important;
    direction: rtl;
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
    padding: 1rem !important;
}
textarea::placeholder { color: rgba(255,255,255,0.3) !important; }

/* text input + number input — כהה עם טקסט לבן */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
input[type="text"],
input[type="number"],
input[type="search"],
[data-baseweb="input"] input,
[data-baseweb="base-input"] input {
    background: #12122a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: rgba(255,255,255,0.88) !important;
    direction: rtl;
}
input::placeholder,
.stTextInput input::placeholder { color: rgba(255,255,255,0.3) !important; }

/* radio */
.stRadio label, .stRadio span, .stRadio div {
    color: rgba(255,255,255,0.85) !important;
}
.stRadio [data-testid="stMarkdownContainer"] p { color: rgba(255,255,255,0.85) !important; }

/* checkbox */
.stCheckbox label, .stCheckbox span {
    color: rgba(255,255,255,0.85) !important;
}

/* toggle (unused — replaced with custom button) */
.stToggle label, .stToggle span { color: rgba(255,255,255,0.9) !important; }

/* multiselect */
.stMultiSelect > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    color: white !important;
}
.stMultiSelect span { color: white !important; }

/* all labels */
label, .stSelectbox label, .stTextArea label, .stFileUploader label,
.stTextInput label, .stNumberInput label, .stRadio label,
.stCheckbox label, .stMultiSelect label, .stToggle label {
    color: rgba(255,255,255,0.95) !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    text-align: right !important;
    display: block !important;
}

/* number input — spinner buttons dark */
.stNumberInput button,
[data-baseweb="input"] button {
    background: #1a1a35 !important;
    color: rgba(255,255,255,0.85) !important;
    border: none !important;
}
.stNumberInput > div {
    background: #12122a !important;
    border-radius: 12px !important;
}

/* caption & info text */
.stCaption, small, .stCaption p { color: rgba(255,255,255,0.45) !important; }
.stInfo, .stInfo p, .stInfo div { color: rgba(255,255,255,0.8) !important; }
.stSuccess, .stSuccess p { color: rgba(52,211,153,0.9) !important; }
.stWarning, .stWarning p { color: rgba(251,191,36,0.9) !important; }

/* markdown text */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {
    color: rgba(255,255,255,0.85) !important;
}

/* tabs — bar background */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.08) !important;
}
/* tabs — individual tab */
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.55) !important;
}
.stTabs [data-baseweb="tab"] span,
.stTabs [data-baseweb="tab"] div,
.stTabs [data-baseweb="tab"] p {
    color: rgba(255,255,255,0.55) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: white !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] span,
.stTabs [data-baseweb="tab"][aria-selected="true"] div,
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
    color: white !important;
}
/* tab highlight bar */
.stTabs [data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, #7c3aed, #3b82f6) !important;
}
/* tab border */
.stTabs [data-baseweb="tab-border"] {
    background: rgba(255,255,255,0.08) !important;
}

/* file uploader — outer wrapper */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(167,139,250,0.35) !important;
    border-radius: 14px !important;
    padding: 0.5rem !important;
    transition: border-color 0.3s ease;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(167,139,250,0.7) !important; }

/* file uploader — inner dropzone (the white box) */
[data-testid="stFileUploaderDropzone"],
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section > div,
[data-testid="stFileUploader"] [data-baseweb="file-uploader"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px dashed rgba(167,139,250,0.3) !important;
    border-radius: 10px !important;
}

/* file uploader — all text inside */
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] div,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] div {
    color: rgba(255,255,255,0.6) !important;
}

/* Browse files button */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploaderDropzone"] button {
    background: rgba(124,58,237,0.25) !important;
    color: rgba(255,255,255,0.85) !important;
    border: 1px solid rgba(124,58,237,0.4) !important;
    border-radius: 8px !important;
}

/* dataframe */
[data-testid="stDataFrame"] { color: white !important; }
.dvn-scroller { color: white !important; }
.custom-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    margin: 1.2rem 0;
}
.status-pill {
    display: inline-block;
    background: rgba(52,211,153,0.15);
    border: 1px solid rgba(52,211,153,0.3);
    color: #34d399; border-radius: 100px;
    padding: 0.2rem 0.8rem; font-size: 0.72rem;
    font-weight: 600; letter-spacing: 0.08em;
}
.status-pill-purple {
    background: rgba(167,139,250,0.15);
    border-color: rgba(167,139,250,0.3); color: #a78bfa;
}
[data-testid="stImage"] img { border-radius: 18px; border: 1px solid rgba(255,255,255,0.08); }
.stProgress > div > div {
    background: linear-gradient(90deg, #7c3aed, #3b82f6) !important;
    border-radius: 100px !important;
}
.stAlert {
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.25) !important;
    border-radius: 14px !important; color: rgba(255,255,255,0.8) !important;
}
.sidebar-section {
    font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.12em; color: rgba(255,255,255,0.9);
    text-transform: uppercase; margin: 1.2rem 0 0.6rem 0;
}
/* hide "Press Enter to apply" hint on all text inputs */
[data-testid="InputInstructions"] { display: none !important; }

/* compact confirm button — same height as text input (~38px) */
div[data-testid="stButton"]:has(button[kind="secondary"]#apply_domain_btn) > button,
button[key="apply_domain_btn"],
div[data-testid="column"] button[data-testid="baseButton-secondary"] {
    padding: 0.3rem 0.8rem !important;
    font-size: 0.85rem !important;
    min-height: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        # existing
        "post_text": "",
        "image_bytes": None,
        "style_guide": None,
        "post_ideas": None,
        "style_bytes": None,
        "ideas_bytes": None,
        # new
        "character_image_bytes": None,
        "style_description": "",
        "style_image_list": [],
        "language": "עברית",
        "content_type": "LinkedIn",
        "word_count": 0,
        "aspect_ratio": "1:1",
        "add_text_to_image": False,
        "target_audiences": [],
        "ideas_table": {},
        "ideas_tables_history": [],
        "ideas_table_idx": 0,
        "generated_style_guide": "",
        "style_upload_key": 0,
        "preset_style": "none",
        "marketing_framework": "none",
        "post_notes": "",
        "image_notes": "",
        "archive": [],
        "custom_content": "",
        "_jump_to_ideas": False,
        "free_style_text": "",
        "show_fw_guide": False,
        "show_welcome_modal": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Welcome Modal ─────────────────────────────────────────────────────────────
@st.dialog(" ", width="large")
def _show_welcome_dialog():
    st.markdown("""
<style>
[data-testid="stDialog"] > div > div {
    background: linear-gradient(145deg, #0f0f24 0%, #0d1628 100%) !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
    border-radius: 28px !important;
    max-width: 900px !important;
    width: 90vw !important;
}
/* Hide the native header area entirely — we render our own title */
[data-testid="stDialogHeader"] {
    display: none !important;
}
/* Body direction */
[data-testid="stDialogBody"] { direction: rtl; text-align: right; }
/* "בואו נתחיל" button */
[data-testid="stDialog"] .stButton > button {
    font-size: 1.35rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.03em !important;
}
/* Blur entire background behind modal */
[data-testid="stMain"],
[data-testid="stSidebar"],
header[data-testid="stHeader"] {
    filter: blur(6px) brightness(0.55) !important;
    pointer-events: none !important;
    transition: filter 0.3s ease !important;
}
</style>
""", unsafe_allow_html=True)

    # Custom title — full control over alignment and styling
    st.markdown("""
<div style="
    direction: rtl;
    text-align: right;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1.2rem;
    line-height: 1.3;
">✦ ברוך הבא!</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="direction:rtl;text-align:right;color:rgba(255,255,255,0.88);font-size:1.15rem;line-height:2.1;">
כאן תוכל לייצר תוכן לכל פלטפורמה – פוסטים, מאמרים ובלוגים – בצורה פשוטה ומהירה.
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="direction:rtl;text-align:right;color:rgba(255,255,255,0.75);font-size:1.08rem;line-height:2.1;margin-top:0.8rem;">
אם אין לך רעיונות, לא בטוח איך לכתוב, או שאין לך תמונות מתאימות – המערכת הזו בדיוק בשבילך.<br>
היא מציעה לך רעיונות לתוכן לפי סוג העסק שלך וקהל היעד שלך, כך שהתוכן תמיד יהיה רלוונטי ומעניין.
</div>
""", unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(167,139,250,0.25);margin:1.2rem 0;">', unsafe_allow_html=True)

    st.markdown("""
<div style="direction:rtl;text-align:right;color:rgba(255,255,255,0.75);font-size:1.08rem;line-height:2.1;">
בנוסף, תוכל ליצור לעצמך <strong style="color:rgba(167,139,250,0.95);">סגנון כתיבה ייחודי</strong>:<br>
לאמן את המערכת על סגנון קיים, לבחור סגנון מתוך אפשרויות קיימות, או לבנות סגנון משלך מאפס.<br><br>
אפשר גם להעלות תמונות שלך או של המוצרים שלך, ולהתאים אותן לתוכן בצורה חכמה, כך שהמסר שלך יהיה אחיד וברור.
</div>
""", unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid rgba(96,165,250,0.2);margin:1.2rem 0;">', unsafe_allow_html=True)

    st.markdown("""
<div style="direction:rtl;text-align:right;color:rgba(255,255,255,0.92);font-size:1.15rem;line-height:2.1;font-weight:600;">
מה שהופך עסק למותג הוא עקביות –<br>
<span style="color:rgba(255,255,255,0.6);font-weight:400;">בסגנון הכתיבה, בנראות ובמסרים.</span>
</div>
<div style="direction:rtl;text-align:right;color:rgba(255,255,255,0.75);font-size:1.08rem;line-height:2.1;margin-top:0.6rem;margin-bottom:1.4rem;">
וזה בדיוק מה שהמערכת הזו באה לפתור:<br>
לעזור לך לייצר תוכן אחיד, מדויק ומעניין – שמדבר לקהל שלך ומחזק את המותג שלך.
</div>
""", unsafe_allow_html=True)

    if st.button("✦ **בואו נתחיל**", use_container_width=True, key="welcome_start_btn"):
        st.rerun()


if st.session_state.show_welcome_modal:
    st.session_state.show_welcome_modal = False
    _show_welcome_dialog()


def _safe_filename(s: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]', '_', s.strip())[:40]


def check_api_keys() -> bool:
    missing = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("GOOGLE_API_KEY"):
        missing.append("GOOGLE_API_KEY")
    if missing:
        st.error(f"חסרים מפתחות API: {', '.join(missing)}")
        return False
    return True


@st.cache_data
def load_default_data():
    style_guide = data_loader.load_style_guide()
    post_ideas = data_loader.load_post_ideas()
    return style_guide, post_ideas


@st.cache_data
def _get_header_image_b64() -> str:
    img_path = Path(__file__).parent / "header image" / "hf_20260318_171639_be6b15c6-ea77-4826-b82f-cd93de1ee6eb.jpeg"
    try:
        return _b64.b64encode(img_path.read_bytes()).decode()
    except FileNotFoundError:
        return ""


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if not check_api_keys():
        st.stop()

    default_style, default_ideas = load_default_data()
    style_guide = st.session_state.style_guide or default_style
    post_ideas = st.session_state.post_ideas

    # ── בחירת רעיון (MOVED TO TOP) ──
    st.markdown('<div class="sidebar-section">💡 בחירת רעיון ממחולל הרעיונות</div>', unsafe_allow_html=True)
    if post_ideas:
        category = st.selectbox(
            "קטגוריה", options=list(post_ideas.keys()), label_visibility="collapsed"
        )
        ideas_list = post_ideas.get(category, [])
        idea = st.selectbox("רעיון", options=ideas_list, label_visibility="collapsed")
        selected_idea_source = "dropdown"
        if st.button("🗑 איפוס רעיונות", use_container_width=True, key="reset_ideas_btn"):
            st.session_state.post_ideas = None
            st.session_state.ideas_bytes = None
            st.session_state.ideas_table = {}
            st.session_state.ideas_tables_history = []
            st.session_state.ideas_table_idx = 0
            st.rerun()
    else:
        st.caption("טען רעיונות ממחולל הרעיונות או מקובץ DOCX")
        category = None
        idea = None
        selected_idea_source = "none"

    if st.button("💡 מחולל הרעיונות", use_container_width=True, key="goto_ideas_btn"):
        st.session_state["_jump_to_ideas"] = True

    uploaded_ideas = st.file_uploader("טען רעיונות (DOCX / XLSX / PDF)", type=["docx", "xlsx", "pdf"], key="ideas_upload")
    if uploaded_ideas:
        new_bytes = uploaded_ideas.read()
        if new_bytes != st.session_state.ideas_bytes:
            st.session_state.ideas_bytes = new_bytes
            _suffix = uploaded_ideas.name.rsplit(".", 1)[-1].lower()
            st.session_state.post_ideas = data_loader.load_post_ideas(new_bytes, suffix=_suffix)
            st.rerun()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── רעיון חופשי ──
    st.markdown('<div class="sidebar-section">✏️ רעיון חופשי</div>', unsafe_allow_html=True)
    custom_content = st.text_input(
        "מה הרעיון שלך לתוכן?",
        value=st.session_state.get("custom_content", ""),
        placeholder="כתוב בקצרה",
        label_visibility="visible",
        key="sb_custom_content",
    )
    st.session_state.custom_content = custom_content

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── שפה ──
    st.markdown('<div class="sidebar-section">🌐 שפה</div>', unsafe_allow_html=True)
    selected_language = st.selectbox(
        "שפת פלט", options=LANGUAGES,
        index=LANGUAGES.index(st.session_state.language),
        label_visibility="collapsed", key="sb_language",
    )
    st.session_state.language = selected_language

    # ── סוג תוכן ──
    st.markdown('<div class="sidebar-section">📋 סוג תוכן</div>', unsafe_allow_html=True)
    ct_keys = list(CONTENT_TYPES.keys())
    selected_ct = st.selectbox(
        "סוג תוכן", options=ct_keys,
        index=ct_keys.index(st.session_state.content_type),
        label_visibility="collapsed", key="sb_content_type",
    )
    st.session_state.content_type = selected_ct
    st.caption(f"מומלץ: {CONTENT_TYPES[selected_ct]['words']} מילים")
    word_count_val = st.number_input(
        "כמות מילים מותאמת (0 = ברירת מחדל)",
        min_value=0, max_value=3000, value=st.session_state.word_count,
        step=50, key="sb_word_count",
    )
    st.session_state.word_count = word_count_val

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── סגנון כתיבה (NEW) ──
    st.markdown('<div class="sidebar-section">✍️ סגנון כתיבה</div>', unsafe_allow_html=True)
    style_options = ["none"] + list(PRESET_STYLES.keys())
    _none_label = "סגנון מותאם (DOCX)" if st.session_state.style_bytes else "ללא (מהמחולל)"
    style_display = [_none_label] + [PRESET_STYLES[k]["hebrew_name"] for k in PRESET_STYLES]
    cur_style_idx = style_options.index(st.session_state.preset_style) if st.session_state.preset_style in style_options else 0
    selected_style_idx = st.selectbox(
        "סגנון כתיבה",
        options=range(len(style_options)),
        format_func=lambda i: style_display[i],
        index=cur_style_idx,
        label_visibility="collapsed",
    )
    st.session_state.preset_style = style_options[selected_style_idx]
    if st.session_state.preset_style != "none":
        st.caption(PRESET_STYLES[st.session_state.preset_style]["description"])

    uploaded_style = st.file_uploader("העלה סגנון כתיבה (DOCX / PDF)", type=["docx", "pdf"], key=f"style_upload_{st.session_state.style_upload_key}")
    if uploaded_style:
        new_bytes = uploaded_style.read()
        if new_bytes != st.session_state.style_bytes:
            st.session_state.style_bytes = new_bytes
            _style_suffix = uploaded_style.name.rsplit(".", 1)[-1].lower()
            st.session_state.style_guide = data_loader.load_style_guide(new_bytes, suffix=_style_suffix)
            st.session_state.preset_style = "none"
            st.rerun()

    _style_active = (
        st.session_state.preset_style != "none"
        or st.session_state.style_bytes
        or st.session_state.generated_style_guide
    )
    if _style_active:
        if st.button("🗑 איפוס סגנון כתיבה", use_container_width=True, key="reset_style_sidebar"):
            st.session_state.preset_style = "none"
            st.session_state.style_bytes = None
            st.session_state.style_guide = None
            st.session_state.generated_style_guide = ""
            st.session_state.style_upload_key += 1
            st.rerun()

    # ── מודל כתיבה שיווקית (NEW) ──
    st.markdown('<div class="sidebar-section">📊 מודל כתיבה שיווקית</div>', unsafe_allow_html=True)
    fw_keys = list(MARKETING_FRAMEWORKS.keys())
    fw_display = [MARKETING_FRAMEWORKS[k]["name"] for k in fw_keys]
    cur_fw_idx = fw_keys.index(st.session_state.marketing_framework) if st.session_state.marketing_framework in fw_keys else 0
    selected_fw_idx = st.selectbox(
        "מודל כתיבה שיווקית",
        options=range(len(fw_keys)),
        format_func=lambda i: fw_display[i],
        index=cur_fw_idx,
        label_visibility="collapsed",
        key="sb_marketing_fw",
    )
    st.session_state.marketing_framework = fw_keys[selected_fw_idx]
    if st.session_state.marketing_framework != "none":
        st.caption(MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["description"])

    if st.button("📖 מה הם מודלי כתיבה שיווקית?", key="toggle_fw_guide_btn", use_container_width=True):
        st.session_state.show_fw_guide = not st.session_state.show_fw_guide

    if st.session_state.show_fw_guide:
        try:
            fw_guide_path = Path(__file__).parent / "frameworks" / "מודלי כתיבה שיווקית.txt"
            fw_guide_text = fw_guide_path.read_text(encoding="utf-8")
            lines_html = ""
            for line in fw_guide_text.splitlines():
                if line.startswith("## "):
                    lines_html += f'<div style="font-size:0.88rem;font-weight:700;color:rgba(167,139,250,0.95);margin-top:1rem;margin-bottom:0.3rem;">{line[3:]}</div>'
                elif line.startswith("### "):
                    lines_html += f'<div style="font-size:0.8rem;font-weight:600;color:rgba(255,255,255,0.75);margin-top:0.6rem;">{line[4:]}</div>'
                elif line.startswith("# "):
                    lines_html += f'<div style="font-size:1rem;font-weight:700;color:white;margin-bottom:0.5rem;">{line[2:]}</div>'
                elif line.startswith("---"):
                    lines_html += '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:0.8rem 0;">'
                elif line.startswith("- "):
                    lines_html += f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.65);padding:0.15rem 0 0.15rem 0.5rem;">• {line[2:]}</div>'
                elif line.strip():
                    lines_html += f'<div style="font-size:0.8rem;color:rgba(255,255,255,0.6);line-height:1.7;margin-top:0.2rem;">{line}</div>'
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:14px;padding:1.2rem 1.4rem;margin-top:0.5rem;direction:rtl;text-align:right;">'
                f'{lines_html}</div>',
                unsafe_allow_html=True,
            )
        except FileNotFoundError:
            st.warning("קובץ המדריך לא נמצא")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── תמונת ייחוס (SIMPLIFIED — no my_images gallery) ──
    st.markdown('<div class="sidebar-section">🖼 תמונת ייחוס</div>', unsafe_allow_html=True)
    if st.session_state.character_image_bytes:
        st.image(st.session_state.character_image_bytes, use_container_width=True)
        st.caption("✓ תמונת ייחוס פעילה — עדכון בטאב הגדרות ויזואל")
        face_source = st.session_state.character_image_bytes
    else:
        st.info("העלה תמונת ייחוס בטאב הגדרות ויזואל")
        face_source = None

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── הערות מיוחדות (NEW) ──
    st.markdown('<div class="sidebar-section">📝 הערות מיוחדות</div>', unsafe_allow_html=True)
    post_notes_val = st.text_area(
        "הערות לפוסט",
        value=st.session_state.post_notes,
        height=80,
        key="sb_post_notes",
        placeholder="הוסף הנחיות ספציפיות לפוסט...",
    )
    st.session_state.post_notes = post_notes_val

    image_notes_val = st.text_area(
        "הערות לתמונה",
        value=st.session_state.image_notes,
        height=80,
        key="sb_image_notes",
        placeholder="הוסף הנחיות ספציפיות לתמונה...",
    )
    st.session_state.image_notes = image_notes_val

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── כפתור יצירה ──
    generate_btn = st.button("✦ צור פוסט + תמונה", use_container_width=True)

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        label = "סגנון מותאם" if st.session_state.style_bytes or st.session_state.generated_style_guide else "סגנון ברירת מחדל"
        pill_cls = "status-pill-purple" if (st.session_state.style_bytes or st.session_state.generated_style_guide) else "status-pill"
        st.markdown(f'<div class="{pill_cls}">{label}</div>', unsafe_allow_html=True)
    with col_s2:
        label2 = "רעיונות מותאמים" if st.session_state.ideas_bytes else "רעיונות ברירת מחדל"
        pill_cls2 = "status-pill-purple" if st.session_state.ideas_bytes else "status-pill"
        st.markdown(f'<div class="{pill_cls2}">{label2}</div>', unsafe_allow_html=True)


# ── Tab navigation via JS ─────────────────────────────────────────────────────
if st.session_state.get("_jump_to_ideas"):
    st.session_state["_jump_to_ideas"] = False
    st.components.v1.html("""
    <script>
    (function() {
        const tabs = window.parent.document.querySelectorAll('button[role="tab"]');
        for (let t of tabs) {
            if (t.innerText.includes('מחולל רעיונות')) { t.click(); break; }
        }
    })();
    </script>
    """, height=0)

# ── HEADER ────────────────────────────────────────────────────────────────────
_img_b64 = _get_header_image_b64()
_bg_style = (
    f"background-image: linear-gradient(rgba(5,5,15,0.15), rgba(5,5,20,0.2)), url('data:image/jpeg;base64,{_img_b64}'); background-size: cover; background-position: center center;"
    if _img_b64
    else "background: linear-gradient(135deg, #0a0a0f, #0d0d1a);"
)
st.markdown(f"""
<div style="
    {_bg_style}
    border-radius: 0 0 20px 20px;
    margin: -4rem -4rem 2rem -4rem;
    border: none;
    overflow: hidden;
    height: 280px;
    width: calc(100% + 8rem);
"></div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_create, tab_visual, tab_ideas, tab_style, tab_archive = st.tabs([
    "🏠 יצירה",
    "🎨 הגדרות תמונה",
    "💡 מחולל רעיונות",
    "✍️ סגנון כתיבה",
    "🗂 ארכיון",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — יצירה
# ═══════════════════════════════════════════════════════════════════════════════
with tab_create:
    # ── הגדרות תמונה ──
    col_settings, col_spacer = st.columns([2, 1])
    with col_settings:
        st.markdown('<div class="section-label">⚙️ הגדרות תמונה</div>', unsafe_allow_html=True)
        col_ar, col_txt = st.columns([2, 1])
        with col_ar:
            ar_label = st.radio(
                "יחס גובה-רוחב",
                options=list(ASPECT_RATIOS.keys()),
                horizontal=True,
                key="ar_radio",
            )
            st.session_state.aspect_ratio = ASPECT_RATIOS[ar_label]
        with col_txt:
            _txt_on = st.session_state.add_text_to_image
            _btn_bg = "linear-gradient(135deg,#7c3aed,#3b82f6)" if _txt_on else "rgba(255,255,255,0.07)"
            _btn_border = "#a78bfa" if _txt_on else "rgba(255,255,255,0.45)"
            _btn_label = "✅ הוסף טקסט לתמונה" if _txt_on else "⬜ הוסף טקסט לתמונה"
            st.markdown(f"""
            <style>
            div[data-testid="stButton"] > button#add_text_btn {{
                background: {_btn_bg} !important;
                border: 2px solid {_btn_border} !important;
                border-radius: 10px !important;
                font-size: 0.8rem !important;
                padding: 0.45rem 0.6rem !important;
                line-height: 1.3 !important;
                white-space: normal !important;
                min-height: 56px !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            if st.button(_btn_label, key="add_text_btn", use_container_width=True):
                st.session_state.add_text_to_image = not _txt_on
                st.rerun()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── יצירה ──
    if generate_btn:
        if not face_source:
            st.error("יש להעלות תמונת ייחוס בטאב הגדרות ויזואל")
            st.stop()

        # Resolve idea source: custom input overrides dropdown
        effective_idea = st.session_state.custom_content.strip() or idea or ""
        effective_category = category or "כללי"

        if not effective_idea:
            st.error("יש להזין רעיון — בחר מהרשימה או כתוב רעיון חופשי")
            st.stop()

        wc = st.session_state.word_count if st.session_state.word_count > 0 else None
        effective_style = st.session_state.generated_style_guide or style_guide
        preset_instr = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"] if st.session_state.preset_style != "none" else ""
        fw_instr = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""

        col_prog, _ = st.columns([2, 1])
        with col_prog:
            progress = st.progress(0, text="מתחיל...")

        progress.progress(10, text="✍️ כותב פוסט...")
        try:
            st.session_state.post_text = generator.generate_post(
                effective_style, effective_category, effective_idea,
                language=st.session_state.language,
                content_type=st.session_state.content_type,
                word_count=wc,
                preset_style_instruction=preset_instr,
                marketing_framework=fw_instr,
                post_notes=st.session_state.post_notes,
            )
        except Exception as e:
            st.error(f"שגיאה ביצירת פוסט: {e}")
            st.stop()

        image_text = ""
        if st.session_state.add_text_to_image and st.session_state.post_text:
            progress.progress(35, text="💬 יוצר טקסט לתמונה...")
            try:
                image_text = generator.generate_text_for_image(
                    st.session_state.post_text, st.session_state.language
                )
            except Exception:
                image_text = ""

        progress.progress(50, text="🎨 מייצר תמונה (30-60 שניות)...")
        try:
            scene = generator.generate_image_prompt(st.session_state.post_text)
            if st.session_state.image_notes:
                scene = f"{scene}. Additional direction: {st.session_state.image_notes}"
            st.session_state.image_bytes = generator.generate_image(
                face_source, scene,
                aspect_ratio=st.session_state.aspect_ratio,
                style_description=st.session_state.style_description,
                add_text=st.session_state.add_text_to_image,
                text_content=image_text,
            )
        except Exception as e:
            st.error(f"שגיאה ביצירת תמונה: {e}")

        progress.progress(100, text="✓ הושלם!")
        progress.empty()

        outputs_dir = data_loader.ensure_outputs_dir()
        if st.session_state.post_text and st.session_state.image_bytes:
            generator.save_outputs(
                st.session_state.post_text, st.session_state.image_bytes, outputs_dir,
                category=effective_category, idea=effective_idea,
            )
            archive_entry = {
                "post_text": st.session_state.post_text,
                "image_bytes": st.session_state.image_bytes,
                "category": effective_category,
                "idea": effective_idea,
                "content_type": st.session_state.content_type,
                "language": st.session_state.language,
                "preset_style": PRESET_STYLES[st.session_state.preset_style]["hebrew_name"] if st.session_state.preset_style != "none" else "ללא",
                "marketing_framework": st.session_state.marketing_framework,
                "timestamp": int(time.time()),
                "timestamp_str": time.strftime("%d/%m/%Y %H:%M"),
            }
            st.session_state.archive.append(archive_entry)
            if len(st.session_state.archive) > 20:
                st.session_state.archive = st.session_state.archive[-20:]

    # ── תצוגת תוצאות ──
    col_post, col_img = st.columns([1, 1], gap="large")

    with col_post:
        st.markdown('<div class="section-label">📝 הפוסט</div>', unsafe_allow_html=True)
        if st.session_state.post_text:
            edited = st.text_area(
                "", value=st.session_state.post_text,
                height=480, key="editor", label_visibility="collapsed",
            )
            c1, c2 = st.columns(2)
            with c1:
                dl_name_post = f"{_safe_filename(category)}_{_safe_filename(idea)}.txt" if 'category' in dir() else "post.txt"
                st.download_button(
                    "⬇ הורד טקסט", data=edited.encode("utf-8"),
                    file_name=dl_name_post, mime="text/plain", use_container_width=True,
                )
            with c2:
                if st.button("📋 העתק", use_container_width=True):
                    st.write("הועתק!")
            if st.button("🔄 נסה שוב — פוסט בלבד", key="retry_post_btn", use_container_width=True):
                if not face_source:
                    st.error("יש להעלות תמונת ייחוס")
                else:
                    with st.spinner("מחדש פוסט..."):
                        try:
                            _retry_idea = st.session_state.custom_content.strip() or idea or ""
                            _retry_category = category or "כללי"
                            wc = st.session_state.word_count if st.session_state.word_count > 0 else None
                            effective_style = st.session_state.generated_style_guide or style_guide
                            preset_instr = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"] if st.session_state.preset_style != "none" else ""
                            fw_instr = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""
                            st.session_state.post_text = generator.generate_post(
                                effective_style, _retry_category, _retry_idea,
                                language=st.session_state.language,
                                content_type=st.session_state.content_type,
                                word_count=wc,
                                preset_style_instruction=preset_instr,
                                marketing_framework=fw_instr,
                                post_notes=st.session_state.post_notes,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"שגיאה: {e}")
        else:
            st.markdown("""
            <div class="glass-card" style="min-height:480px; display:flex; align-items:center; justify-content:center; text-align:center;">
                <div>
                    <div style="font-size:3rem; margin-bottom:1rem; opacity:0.3;">✍️</div>
                    <div style="color:rgba(255,255,255,0.25); font-size:0.9rem;">הפוסט יופיע כאן לאחר הגנרציה</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_img:
        st.markdown('<div class="section-label">🖼 התמונה</div>', unsafe_allow_html=True)
        if st.session_state.image_bytes:
            st.image(st.session_state.image_bytes, use_container_width=True)
            dl_name_img = f"{_safe_filename(category)}_{_safe_filename(idea)}.png" if 'category' in dir() else "post_image.png"
            st.download_button(
                "⬇ הורד תמונה", data=st.session_state.image_bytes,
                file_name=dl_name_img, mime="image/png", use_container_width=True,
            )
            if st.button("🔄 נסה שוב — תמונה בלבד", key="retry_image_btn", use_container_width=True):
                if not face_source:
                    st.error("יש להעלות תמונת ייחוס")
                elif not st.session_state.post_text:
                    st.error("יש לצור פוסט תחילה")
                else:
                    with st.spinner("מחדש תמונה (30-60 שניות)..."):
                        try:
                            image_text = ""
                            if st.session_state.add_text_to_image:
                                image_text = generator.generate_text_for_image(
                                    st.session_state.post_text, st.session_state.language
                                )
                            scene = generator.generate_image_prompt(st.session_state.post_text)
                            if st.session_state.image_notes:
                                scene = f"{scene}. Additional direction: {st.session_state.image_notes}"
                            st.session_state.image_bytes = generator.generate_image(
                                face_source, scene,
                                aspect_ratio=st.session_state.aspect_ratio,
                                style_description=st.session_state.style_description,
                                add_text=st.session_state.add_text_to_image,
                                text_content=image_text,
                            )
                            st.rerun()
                        except Exception as e:
                            st.error(f"שגיאה: {e}")
        else:
            st.markdown("""
            <div class="glass-card" style="min-height:480px; display:flex; align-items:center; justify-content:center; text-align:center;">
                <div>
                    <div style="font-size:3rem; margin-bottom:1rem; opacity:0.3;">🖼️</div>
                    <div style="color:rgba(255,255,255,0.25); font-size:0.9rem;">התמונה תופיע כאן לאחר הגנרציה</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — הגדרות ויזואל
# ═══════════════════════════════════════════════════════════════════════════════
with tab_visual:
    st.markdown("""
<div style="
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    direction: rtl;
    text-align: right;
">
    <div style="color:rgba(255,255,255,0.65); font-size:0.92rem; line-height:1.9;">
        בעמוד זה תוכלו להגדיר את השפה הוויזואלית של התוכן שלכם. כאן ניתן לבחור תמונת ייחוס (כגון דמות ספציפית, קבוצת אנשים או מוצר מסוים) כדי לשמור על עקביות. בנוסף, תוכלו להגדיר את סגנון התמונות על ידי העלאת דוגמאות ויזואליות קיימות או על ידי כתיבת תיאור חופשי של הסגנון המבוקש. המערכת מאפשרת גם לשפר ולדייק את תיאור הסגנון שכתבתם בלחיצת כפתור אחת.
    </div>
</div>
""", unsafe_allow_html=True)
    col_char, col_style_img = st.columns(2, gap="large")

    with col_char:
        st.markdown('<div class="section-label">📸 תמונת ייחוס</div>', unsafe_allow_html=True)
        uploaded_char = st.file_uploader(
            "העלה תמונת ייחוס (פנים, אביזר, מוצר, אנשים...)",
            type=["jpg", "jpeg", "png", "webp"],
            key="char_upload",
        )
        if uploaded_char:
            char_bytes = uploaded_char.read()
            if char_bytes != st.session_state.character_image_bytes:
                st.session_state.character_image_bytes = char_bytes
                st.rerun()  # rerun so sidebar renders with the new image

        if st.session_state.character_image_bytes:
            st.image(st.session_state.character_image_bytes, use_container_width=True)
            if st.button("🗑 הסר תמונה", key="remove_char"):
                st.session_state.character_image_bytes = None
                st.rerun()

    with col_style_img:
        st.markdown('<div class="section-label">🎨 תמונות סגנון</div>', unsafe_allow_html=True)
        uploaded_styles = st.file_uploader(
            "העלה תמונות סגנון (עד 10)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
            key="style_img_upload",
        )
        if uploaded_styles:
            style_bytes_list = [f.read() for f in uploaded_styles][:10]
            st.session_state.style_image_list = style_bytes_list
            st.caption(f"{len(style_bytes_list)}/10 תמונות הועלו")

        if st.session_state.style_image_list:
            if st.button("🔍 נתח סגנון", key="analyze_style_btn", use_container_width=True):
                with st.spinner("מנתח סגנון ויזואלי..."):
                    try:
                        desc = generator.analyze_style_images(st.session_state.style_image_list)
                        st.session_state.style_description = desc
                        st.success("✓ ניתוח הושלם")
                    except Exception as e:
                        st.error(f"שגיאה בניתוח: {e}")

        if st.session_state.style_description:
            st.markdown('<div class="section-label">📝 תיאור סגנון</div>', unsafe_allow_html=True)
            edited_style_desc = st.text_area(
                "", value=st.session_state.style_description,
                height=200, key="style_desc_editor", label_visibility="collapsed",
            )
            if edited_style_desc != st.session_state.style_description:
                st.session_state.style_description = edited_style_desc
            if st.button("🗑 נקה סגנון", key="clear_style_desc"):
                st.session_state.style_description = ""
                st.rerun()

    # ── תיאור סגנון בטקסט חופשי ──────────────────────────────────────────────
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">✍️ תיאור סגנון ויזואלי בכתיבה חופשית</div>', unsafe_allow_html=True)
    st.caption("אין לך תמונות סגנון? תאר את הסגנון הוויזואלי שאתה רוצה — הצבעים, האווירה, התאורה, הסביבה...")
    free_style_text = st.text_area(
        "תיאור סגנון חופשי",
        value=st.session_state.get("free_style_text", ""),
        height=130,
        placeholder="למשל: תמונות בסגנון קינמטי, תאורה דרמטית, צבעים כהים עם הדגשות כחולות, אווירה עתידנית...",
        label_visibility="collapsed",
        key="free_style_input",
    )
    st.session_state.free_style_text = free_style_text

    col_apply, col_enhance = st.columns([1, 1])
    with col_apply:
        if st.button("✅ החל סגנון חופשי", key="apply_free_style_btn", use_container_width=True):
            if free_style_text.strip():
                st.session_state.style_description = free_style_text.strip()
                st.success("✓ הסגנון עודכן")
    with col_enhance:
        if st.button("✨ שפר סגנון", key="enhance_style_btn", use_container_width=True):
            if free_style_text.strip():
                with st.spinner("משפר תיאור סגנון..."):
                    try:
                        enhanced = generator.enhance_style_description(free_style_text.strip())
                        st.session_state.free_style_text = enhanced
                        st.session_state.style_description = enhanced
                        st.rerun()
                    except Exception as e:
                        st.error(f"שגיאה: {e}")
            else:
                st.warning("כתוב תיאור סגנון תחילה")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — מחולל רעיונות
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ideas:
    import pandas as pd

    st.markdown("""
<div style="
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    direction: rtl;
    text-align: right;
">
    <div style="font-size:1.5rem; font-weight:700; color:white; margin-bottom:0.6rem;">
        מחולל הרעיונות שלכם
    </div>
    <div style="color:rgba(255,255,255,0.65); font-size:0.92rem; line-height:1.8;">
        כאן תוכלו לייצר בקלות מגוון רעיונות לתוכן שמותאמים בדיוק לתחום העיסוק ולקהלי היעד שלכם.<br>
        פשוט כתבו את התחום שבו אתם עוסקים ובחרו את קהל היעד – המערכת תייצר עבורכם רשימה של 30 רעיונות שונים לתוכן שניתן לטעון ישירות למערכת.<br><br>
        לאחר מכן, תוכלו לעבור בין הרעיונות שבחרתם וליצור תכנים איכותיים בכמויות גדולות ובמהירות.
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="section-label">💡 מחולל רעיונות לתוכן</div>', unsafe_allow_html=True)

    # ── שלב 1: תחום ──
    col_domain, col_apply_domain = st.columns([4, 1])
    with col_domain:
        domain_input = st.text_input(
            "מהו התחום שלך?",
            placeholder="למשל: פיזיותרפיה, שיווק דיגיטלי, בישול בריא...",
            key="ideas_domain_input",
        )
    with col_apply_domain:
        st.markdown('<div style="height:1.9rem"></div>', unsafe_allow_html=True)
        apply_domain_btn = st.button("אישור ◀", key="apply_domain_btn", use_container_width=True)

    if domain_input:
        if st.button("🎯 הצע קהלי יעד", key="suggest_audiences_btn") or apply_domain_btn:
            with st.spinner("מייצר קהלי יעד..."):
                try:
                    audiences = generator.generate_target_audiences(
                        domain_input, st.session_state.language
                    )
                    st.session_state.target_audiences = audiences
                    st.session_state.ideas_table = {}
                    st.session_state.ideas_tables_history = []
                    st.session_state.ideas_table_idx = 0
                except Exception as e:
                    st.error(f"שגיאה: {e}")

    # ── שלב 2: בחירת קהל יעד ──
    if st.session_state.target_audiences:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">👥 סוג הקהל שלך</div>', unsafe_allow_html=True)

        # Checkboxes for each suggested audience
        checked_audiences = []
        cols_per_row = 2
        audience_list = st.session_state.target_audiences
        for i in range(0, len(audience_list), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j, col in enumerate(row_cols):
                idx = i + j
                if idx < len(audience_list):
                    with col:
                        if st.checkbox(audience_list[idx], key=f"aud_cb_{idx}"):
                            checked_audiences.append(audience_list[idx])

        custom_audience = st.text_input(
            "✏️ קהל יעד ספציפי אחר (אופציונלי)",
            key="custom_audience",
            placeholder="למשל: גברים גמלאים מעל גיל 65",
        )

        final_audience_list = checked_audiences + ([custom_audience.strip()] if custom_audience.strip() else [])

        # Display selected summary
        if final_audience_list:
            st.caption(f"נבחרו: {', '.join(final_audience_list)}")

            if st.button("📊 צור טבלת רעיונות", key="gen_ideas_table_btn", use_container_width=True):
                audience_str = ", ".join(final_audience_list)
                with st.spinner("מייצר טבלת רעיונות (מוטיבציות, חששות, דברים שלא יודעים)..."):
                    try:
                        table = generator.generate_ideas_table(
                            domain_input, audience_str, st.session_state.language
                        )
                        st.session_state.ideas_table = table
                        st.session_state.ideas_tables_history.append(table)
                        st.session_state.ideas_table_idx = len(st.session_state.ideas_tables_history) - 1
                    except Exception as e:
                        st.error(f"שגיאה: {e}")
        else:
            st.info("סמן לפחות קהל יעד אחד כדי להמשיך")

    # ── שלב 3: טבלת רעיונות ──
    if st.session_state.ideas_tables_history:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

        history = st.session_state.ideas_tables_history
        total_sets = len(history)
        idx = st.session_state.ideas_table_idx

        # Navigation header
        col_lbl, col_prev, col_counter, col_next = st.columns([4, 1, 1, 1])
        with col_lbl:
            st.markdown('<div class="section-label">📋 רעיונות שנוצרו</div>', unsafe_allow_html=True)
        with col_prev:
            if st.button("◀", key="ideas_prev_btn", use_container_width=True, disabled=(idx == 0)):
                st.session_state.ideas_table_idx -= 1
                st.rerun()
        with col_counter:
            st.markdown(
                f'<div style="text-align:center;color:rgba(255,255,255,0.7);padding-top:0.4rem;">{idx+1} / {total_sets}</div>',
                unsafe_allow_html=True,
            )
        with col_next:
            if st.button("▶", key="ideas_next_btn", use_container_width=True, disabled=(idx == total_sets - 1)):
                st.session_state.ideas_table_idx += 1
                st.rerun()

        current_table = history[st.session_state.ideas_table_idx]

        # Render each category as a plain-text card
        for category, ideas_list in current_table.items():
            ideas_html = "".join(
                f'<div style="padding:0.35rem 0; border-bottom:1px solid rgba(255,255,255,0.05); color:rgba(255,255,255,0.82); font-size:0.93rem; line-height:1.6;">'
                f'<span style="color:rgba(167,139,250,0.7); font-weight:600; margin-left:0.5rem;">{i}.</span> {idea}'
                f'</div>'
                for i, idea in enumerate(ideas_list, 1)
            )
            st.markdown(f"""
<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.07);
     border-radius:16px; padding:1.2rem 1.5rem; margin-bottom:1rem; direction:rtl; text-align:right;">
  <div style="font-size:0.78rem; font-weight:700; letter-spacing:0.12em; color:rgba(167,139,250,0.9);
       text-transform:uppercase; margin-bottom:0.8rem;">{category}</div>
  {ideas_html}
</div>""", unsafe_allow_html=True)

        # Action buttons
        col_dl, col_load, col_more = st.columns(3)
        with col_dl:
            docx_bytes = data_loader.create_ideas_docx(current_table)
            st.download_button(
                "⬇ הורד DOCX", data=docx_bytes,
                file_name=f"ideas_table_{idx+1}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                key=f"dl_ideas_{idx}",
            )
        with col_load:
            if st.button("📥 טען לאפליקציה", key=f"load_ideas_btn_{idx}", use_container_width=True):
                st.session_state.post_ideas = current_table
                st.rerun()
        with col_more:
            if st.button("➕ צור עוד 30 רעיונות", key="more_ideas_btn", use_container_width=True):
                if domain_input and final_audience_list if st.session_state.target_audiences else domain_input:
                    audience_str = ", ".join(final_audience_list) if st.session_state.target_audiences else ""
                    with st.spinner("מייצר עוד רעיונות..."):
                        try:
                            new_table = generator.generate_ideas_table(
                                domain_input, audience_str, st.session_state.language
                            )
                            st.session_state.ideas_table = new_table
                            st.session_state.ideas_tables_history.append(new_table)
                            st.session_state.ideas_table_idx = len(st.session_state.ideas_tables_history) - 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"שגיאה: {e}")
                else:
                    st.warning("יש להזין תחום כדי לייצר עוד רעיונות")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — מחולל סגנון כתיבה
# ═══════════════════════════════════════════════════════════════════════════════
with tab_style:
    st.markdown("""
<div style="
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    direction: rtl;
    text-align: right;
">
    <div style="color:rgba(255,255,255,0.65); font-size:0.92rem; line-height:1.9;">
        בעמוד זה תוכלו להגדיר את הדרך שבה המערכת תכתוב עבורכם. קיימות שלוש אפשרויות:<br><br>
        <strong style="color:rgba(255,255,255,0.9);">בחירה מתוך רשימה:</strong> בחירה מתוך 10 סגנונות הכתיבה המובילים והאפקטיביים ביותר ליצירת תוכן.<br><br>
        <strong style="color:rgba(255,255,255,0.9);">ניתוח סגנון אישי:</strong> העלאת מספר תכנים שכתבתם (מומלץ 4-5 תכנים באותו סגנון) והמערכת תנתח ותלמד את הטון הייחודי שלכם.<br><br>
        <strong style="color:rgba(255,255,255,0.9);">טעינת סגנון קיים:</strong> אם כבר יש לכם קובץ הגדרות של סגנון הכתיבה שלכם, תוכלו לטעון אותו ישירות לכאן.
    </div>
</div>
""", unsafe_allow_html=True)
    # ── סגנונות מוכנים (NEW) ──
    st.markdown('<div class="section-label">✦ סגנונות כתיבה מוכנים</div>', unsafe_allow_html=True)

    preset_options_tab = ["none"] + list(PRESET_STYLES.keys())
    preset_display_tab = ["ללא — השתמש במחולל הסגנון שלמטה"] + [
        f"{PRESET_STYLES[k]['hebrew_name']} ({PRESET_STYLES[k]['name']})"
        for k in PRESET_STYLES
    ]
    cur_preset_tab_idx = preset_options_tab.index(st.session_state.preset_style) if st.session_state.preset_style in preset_options_tab else 0
    selected_preset_tab_idx = st.selectbox(
        "בחר סגנון כתיבה מוכן",
        options=range(len(preset_options_tab)),
        format_func=lambda i: preset_display_tab[i],
        index=cur_preset_tab_idx,
        key="tab4_preset_select",
        label_visibility="collapsed",
    )
    selected_preset_key = preset_options_tab[selected_preset_tab_idx]

    if selected_preset_key != "none":
        preset_data = PRESET_STYLES[selected_preset_key]
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:1.05rem; font-weight:600; margin-bottom:0.4rem;">{preset_data['hebrew_name']} — {preset_data['name']}</div>
            <div style="color:rgba(255,255,255,0.6); font-size:0.88rem; margin-bottom:0.6rem;">{preset_data['description']}</div>
            <div style="color:rgba(255,255,255,0.55); font-size:0.82rem; white-space:pre-wrap; direction:rtl; text-align:right;">{preset_data.get('summary', preset_data['description'])}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✅ החל סגנון זה", key="apply_preset_from_tab4"):
            st.session_state.preset_style = selected_preset_key
            st.rerun()
    else:
        st.info("בחר סגנון מוכן מהרשימה, או השתמש במחולל הסגנון האישי שלמטה.")

    _tab_style_active = (
        st.session_state.preset_style != "none"
        or st.session_state.style_bytes
        or st.session_state.generated_style_guide
    )
    if _tab_style_active:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        _active_parts = []
        if st.session_state.preset_style != "none":
            _active_parts.append(f"סגנון מוכן: {PRESET_STYLES[st.session_state.preset_style]['hebrew_name']}")
        if st.session_state.style_bytes:
            _active_parts.append("קובץ סגנון מועלה")
        if st.session_state.generated_style_guide:
            _active_parts.append("סגנון שנוצר מניתוח")
        st.caption("סגנון פעיל: " + " · ".join(_active_parts))
        if st.button("🗑 איפוס כל הגדרות הסגנון", use_container_width=True, key="reset_style_tab"):
            st.session_state.preset_style = "none"
            st.session_state.style_bytes = None
            st.session_state.style_guide = None
            st.session_state.generated_style_guide = ""
            st.session_state.style_upload_key += 1
            st.rerun()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-label">✍️ מחולל סגנון אישי</div>', unsafe_allow_html=True)

    # ── בחירת מסלול ──
    if "style_mode" not in st.session_state:
        st.session_state.style_mode = None  # None | "analyze" | "upload"

    col_btn_analyze, col_btn_upload = st.columns(2, gap="large")
    with col_btn_analyze:
        st.markdown("""
        <div class="glass-card" style="text-align:center; min-height:110px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:2rem; margin-bottom:0.4rem;">🔬</div>
            <div style="color:rgba(255,255,255,0.8); font-weight:600; margin-bottom:0.3rem;">זיהוי סגנון כתיבה</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.82rem;">העלה דוגמאות — AI ינתח את הסגנון</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("בחר", key="mode_analyze_btn", use_container_width=True):
            st.session_state.style_mode = "analyze"
            st.rerun()

    with col_btn_upload:
        st.markdown("""
        <div class="glass-card" style="text-align:center; min-height:110px; display:flex; flex-direction:column; align-items:center; justify-content:center;">
            <div style="font-size:2rem; margin-bottom:0.4rem;">📂</div>
            <div style="color:rgba(255,255,255,0.8); font-weight:600; margin-bottom:0.3rem;">טעינת סגנון קיים</div>
            <div style="color:rgba(255,255,255,0.4); font-size:0.82rem;">יש לך כבר סט הוראות? העלה אותו</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("בחר", key="mode_upload_btn", use_container_width=True):
            st.session_state.style_mode = "upload"
            st.rerun()

    # ── מסלול א: זיהוי סגנון ──
    if st.session_state.style_mode == "analyze":
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">🔬 זיהוי סגנון כתיבה</div>', unsafe_allow_html=True)
        st.info("העלה 4-5 תכנים שכתבת (פוסטים, מאמרים, בלוגים) שדומים בסגנונם. ככל שהדוגמאות יותר דומות — הניתוח יהיה מדויק יותר.")

        col_upload_s, col_paste_s = st.columns(2, gap="large")
        with col_upload_s:
            uploaded_samples = st.file_uploader(
                "העלה קבצי טקסט (TXT / DOCX / PDF)",
                type=["txt", "docx", "pdf"],
                accept_multiple_files=True,
                key="writing_samples_upload",
            )
        with col_paste_s:
            pasted_text = st.text_area(
                "או הדבק טקסט ישירות",
                height=200,
                key="pasted_writing_sample",
                placeholder="הדבק כאן תוכן לדוגמה...",
            )

        # Collect samples
        samples_to_analyze = []
        if uploaded_samples:
            for uf in uploaded_samples:
                try:
                    if uf.name.endswith(".txt"):
                        samples_to_analyze.append(uf.read().decode("utf-8", errors="replace"))
                    elif uf.name.endswith(".docx"):
                        from docx import Document as _Doc
                        import io as _io
                        doc_obj = _Doc(_io.BytesIO(uf.read()))
                        text = "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
                        samples_to_analyze.append(text)
                    elif uf.name.endswith(".pdf"):
                        import io as _io
                        import pypdf as _pypdf
                        reader = _pypdf.PdfReader(_io.BytesIO(uf.read()))
                        text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                        if text:
                            samples_to_analyze.append(text)
                except Exception:
                    pass
        if pasted_text.strip():
            samples_to_analyze.append(pasted_text.strip())

        n = len(samples_to_analyze)
        if n > 0:
            color = "#34d399" if n >= 4 else "#f59e0b"
            st.markdown(
                f'<div style="color:{color}; font-size:0.85rem; margin-bottom:0.5rem;">'
                f'{"✓" if n >= 4 else "⚠"} {n} דוגמאות {"— מספיק לניתוח מדויק" if n >= 4 else "— מומלץ לפחות 4"}'
                f"</div>",
                unsafe_allow_html=True,
            )

            if st.button("🔬 נתח וצור מדריך סגנון", key="analyze_writing_btn", use_container_width=True):
                with st.spinner("מנתח סגנון כתיבה (תחביר, אוצר מילים, טון, דימויים, קצב)..."):
                    try:
                        guide = generator.generate_writing_style(samples_to_analyze)
                        st.session_state.generated_style_guide = guide
                        st.success("✓ מדריך סגנון נוצר")
                    except Exception as e:
                        st.error(f"שגיאה: {e}")

        if st.button("← חזור", key="back_from_analyze"):
            st.session_state.style_mode = None
            st.rerun()

    # ── מסלול ב: טעינת סגנון קיים ──
    elif st.session_state.style_mode == "upload":
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📂 טעינת סגנון קיים</div>', unsafe_allow_html=True)
        st.info("העלה קובץ DOCX או TXT שמכיל סט הוראות לסגנון כתיבה.")

        existing_guide_file = st.file_uploader(
            "העלה קובץ סגנון כתיבה",
            type=["txt", "docx"],
            key="existing_style_upload",
        )
        if existing_guide_file:
            try:
                raw_bytes = existing_guide_file.read()
                if existing_guide_file.name.endswith(".txt"):
                    guide_text = raw_bytes.decode("utf-8", errors="replace")
                else:
                    from docx import Document as _Doc
                    import io as _io
                    doc_obj = _Doc(_io.BytesIO(raw_bytes))
                    guide_text = "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
                st.session_state.generated_style_guide = guide_text
                # sync sidebar selectbox
                st.session_state.style_bytes = raw_bytes
                st.session_state.style_guide = guide_text
                st.session_state.preset_style = "none"
                st.session_state.style_upload_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"שגיאה בקריאת הקובץ: {e}")

        if st.button("← חזור", key="back_from_upload"):
            st.session_state.style_mode = None
            st.rerun()

    # ── תצוגת מדריך סגנון (משותף לשני מסלולים) ──
    if st.session_state.generated_style_guide:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📖 מדריך סגנון כתיבה</div>', unsafe_allow_html=True)

        edited_guide = st.text_area(
            "", value=st.session_state.generated_style_guide,
            height=420, key="style_guide_editor", label_visibility="collapsed",
        )
        if edited_guide != st.session_state.generated_style_guide:
            st.session_state.generated_style_guide = edited_guide

        col_apply, col_dl_style, col_clear = st.columns(3)
        with col_apply:
            if st.button("✅ החל סגנון", key="apply_style_btn", use_container_width=True):
                st.session_state.style_guide = st.session_state.generated_style_guide
                st.session_state.style_bytes = st.session_state.generated_style_guide.encode("utf-8")
                st.session_state.preset_style = "none"
                st.session_state.style_upload_key += 1
                st.rerun()
        with col_dl_style:
            docx_bytes = data_loader.save_style_guide_docx(st.session_state.generated_style_guide)
            st.download_button(
                "⬇ הורד DOCX", data=docx_bytes,
                file_name="style_guide.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with col_clear:
            if st.button("🗑 נקה", key="clear_style_guide_btn", use_container_width=True):
                st.session_state.generated_style_guide = ""
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 — ארכיון
# ═══════════════════════════════════════════════════════════════════════════════
with tab_archive:
    st.markdown('<div class="section-label">🗂 ארכיון גנרציות</div>', unsafe_allow_html=True)

    archive = st.session_state.archive

    if not archive:
        st.markdown("""
        <div class="glass-card" style="text-align:center; min-height:200px; display:flex; align-items:center; justify-content:center;">
            <div>
                <div style="font-size:3rem; opacity:0.3; margin-bottom:1rem;">🗂</div>
                <div style="color:rgba(255,255,255,0.25); font-size:0.9rem;">הגנרציות יופיעו כאן לאחר שתייצר תוכן</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_arc_hdr, col_arc_clear = st.columns([3, 1])
        with col_arc_hdr:
            st.caption(f"{len(archive)} גנרציות בארכיון")
        with col_arc_clear:
            if st.button("🗑 נקה ארכיון", key="clear_archive_btn"):
                st.session_state.archive = []
                st.rerun()

        for i, entry in enumerate(reversed(archive)):
            idx = len(archive) - 1 - i
            expander_label = f"[{entry['timestamp_str']}] {entry['category']} — {entry['idea'][:50]}"
            with st.expander(expander_label, expanded=(i == 0)):
                col_arc_post, col_arc_img = st.columns([1, 1], gap="large")

                with col_arc_post:
                    st.markdown('<div class="section-label">📝 פוסט</div>', unsafe_allow_html=True)
                    st.text_area(
                        "",
                        value=entry["post_text"],
                        height=300,
                        key=f"arc_post_{idx}",
                        label_visibility="collapsed",
                    )
                    meta = f"{entry['content_type']} · {entry['language']} · {entry['preset_style']} · {entry['marketing_framework']}"
                    st.caption(meta)
                    safe_cat = _safe_filename(entry["category"])
                    safe_idea = _safe_filename(entry["idea"])
                    st.download_button(
                        "⬇ הורד טקסט",
                        data=entry["post_text"].encode("utf-8"),
                        file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"arc_dl_post_{idx}",
                    )

                with col_arc_img:
                    st.markdown('<div class="section-label">🖼 תמונה</div>', unsafe_allow_html=True)
                    if entry.get("image_bytes"):
                        st.image(entry["image_bytes"], use_container_width=True)
                        st.download_button(
                            "⬇ הורד תמונה",
                            data=entry["image_bytes"],
                            file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"arc_dl_img_{idx}",
                        )
