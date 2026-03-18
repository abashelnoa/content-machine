"""
app.py — AI Content Studio | 4 Tabs
הרצה: streamlit run app.py
"""
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

st.set_page_config(
    page_title="AI Content Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d0d1a 40%, #0a1628 100%);
    font-family: 'Inter', sans-serif;
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
    font-family: 'Inter', sans-serif;
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

/* toggle */
.stToggle label, .stToggle span { color: rgba(255,255,255,0.85) !important; }

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
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.03em !important;
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
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.15em; color: rgba(167,139,250,0.85);
    text-transform: uppercase; margin: 1.2rem 0 0.6rem 0;
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
        "generated_style_guide": "",
        "preset_style": "none",
        "marketing_framework": "none",
        "post_notes": "",
        "image_notes": "",
        "archive": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


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


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div class="main-title" style="font-size:1.4rem; margin-bottom:0.1rem;">✦ AI Content Studio</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title" style="font-size:0.75rem; margin-bottom:1.5rem;">Content Generator</div>',
        unsafe_allow_html=True,
    )

    if not check_api_keys():
        st.stop()

    default_style, default_ideas = load_default_data()
    style_guide = st.session_state.style_guide or default_style
    post_ideas = st.session_state.post_ideas or default_ideas

    # ── בחירת רעיון (MOVED TO TOP) ──
    st.markdown('<div class="sidebar-section">💡 בחר רעיון</div>', unsafe_allow_html=True)
    if post_ideas:
        category = st.selectbox(
            "קטגוריה", options=list(post_ideas.keys()), label_visibility="collapsed"
        )
        ideas_list = post_ideas.get(category, [])
        idea = st.selectbox("רעיון", options=ideas_list, label_visibility="collapsed")
    else:
        st.warning("לא נמצאו רעיונות")
        st.stop()

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
    style_display = ["ללא (מהמחולל)"] + [PRESET_STYLES[k]["hebrew_name"] for k in PRESET_STYLES]
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

    # ── מסגרת שיווקית (NEW) ──
    st.markdown('<div class="sidebar-section">📊 מסגרת שיווקית</div>', unsafe_allow_html=True)
    fw_keys = list(MARKETING_FRAMEWORKS.keys())
    fw_display = [MARKETING_FRAMEWORKS[k]["name"] for k in fw_keys]
    cur_fw_idx = fw_keys.index(st.session_state.marketing_framework) if st.session_state.marketing_framework in fw_keys else 0
    selected_fw_idx = st.selectbox(
        "מסגרת שיווקית",
        options=range(len(fw_keys)),
        format_func=lambda i: fw_display[i],
        index=cur_fw_idx,
        label_visibility="collapsed",
        key="sb_marketing_fw",
    )
    st.session_state.marketing_framework = fw_keys[selected_fw_idx]
    if st.session_state.marketing_framework != "none":
        st.caption(MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["description"])

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

    # ── קבצי תוכן (MOVED TO BOTTOM) ──
    st.markdown('<div class="sidebar-section">📂 קבצי תוכן</div>', unsafe_allow_html=True)

    uploaded_style = st.file_uploader("סגנון כתיבה (DOCX)", type=["docx"], key="style_upload")
    if uploaded_style:
        new_bytes = uploaded_style.read()
        if new_bytes != st.session_state.style_bytes:
            st.session_state.style_bytes = new_bytes
            st.session_state.style_guide = data_loader.load_style_guide(new_bytes)
            st.success("✓ סגנון עודכן")

    uploaded_ideas = st.file_uploader("טבלת רעיונות (DOCX)", type=["docx"], key="ideas_upload")
    if uploaded_ideas:
        new_bytes = uploaded_ideas.read()
        if new_bytes != st.session_state.ideas_bytes:
            st.session_state.ideas_bytes = new_bytes
            st.session_state.post_ideas = data_loader.load_post_ideas(new_bytes)
            st.success("✓ רעיונות עודכנו")

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


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">✦ AI Content Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">צור תוכן · נהל סגנון · ייצר רעיונות</div>',
    unsafe_allow_html=True,
)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_create, tab_visual, tab_ideas, tab_style, tab_archive = st.tabs([
    "🏠 יצירה",
    "🎨 הגדרות ויזואל",
    "💡 מחולל רעיונות",
    "✍️ מחולל סגנון",
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
            add_text = st.toggle("הוסף טקסט לתמונה", key="add_text_toggle")
            st.session_state.add_text_to_image = add_text

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── יצירה ──
    if generate_btn:
        if not face_source:
            st.error("יש להעלות תמונת ייחוס בטאב הגדרות ויזואל")
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
                effective_style, category, idea,
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
                category=category, idea=idea,
            )
            archive_entry = {
                "post_text": st.session_state.post_text,
                "image_bytes": st.session_state.image_bytes,
                "category": category,
                "idea": idea,
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
                            wc = st.session_state.word_count if st.session_state.word_count > 0 else None
                            effective_style = st.session_state.generated_style_guide or style_guide
                            preset_instr = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"] if st.session_state.preset_style != "none" else ""
                            fw_instr = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""
                            st.session_state.post_text = generator.generate_post(
                                effective_style, category, idea,
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
        else:
            st.markdown("""
            <div class="glass-card" style="min-height:200px; display:flex; align-items:center; justify-content:center; text-align:center;">
                <div style="color:rgba(255,255,255,0.25); font-size:0.9rem;">העלה תמונת ייחוס — פנים, מוצר, אביזר, קבוצת אנשים, לוגו...</div>
            </div>
            """, unsafe_allow_html=True)

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


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — מחולל רעיונות
# ═══════════════════════════════════════════════════════════════════════════════
with tab_ideas:
    import pandas as pd

    st.markdown('<div class="section-label">💡 מחולל רעיונות לתוכן</div>', unsafe_allow_html=True)

    # ── שלב 1: תחום ──
    col_domain, col_lang_ideas = st.columns([3, 1])
    with col_domain:
        domain_input = st.text_input(
            "מהו התחום שלך?",
            placeholder="למשל: פיזיותרפיה, שיווק דיגיטלי, בישול בריא...",
            key="ideas_domain_input",
        )
    with col_lang_ideas:
        st.write("")
        st.caption(f"שפה: {st.session_state.language}")

    if domain_input:
        if st.button("🎯 הצע קהלי יעד", key="suggest_audiences_btn"):
            with st.spinner("מייצר קהלי יעד..."):
                try:
                    audiences = generator.generate_target_audiences(
                        domain_input, st.session_state.language
                    )
                    st.session_state.target_audiences = audiences
                    # reset table when domain/audiences change
                    st.session_state.ideas_table = {}
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
                # Build audience string for the prompt
                audience_str = ", ".join(final_audience_list)
                with st.spinner("מייצר טבלת רעיונות (מוטיבציות, חששות, דברים שלא יודעים)..."):
                    try:
                        table = generator.generate_ideas_table(
                            domain_input, audience_str, st.session_state.language
                        )
                        st.session_state.ideas_table = table
                    except Exception as e:
                        st.error(f"שגיאה: {e}")
        else:
            st.info("סמן לפחות קהל יעד אחד כדי להמשיך")

    # ── שלב 3: טבלת רעיונות ──
    if st.session_state.ideas_table:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📋 טבלת רעיונות</div>', unsafe_allow_html=True)

        # Build DataFrame: rows = categories, columns = 1..10
        table_data = st.session_state.ideas_table
        max_ideas = max((len(v) for v in table_data.values()), default=0)
        col_headers = [str(i) for i in range(1, max_ideas + 1)]
        df_dict = {}
        for category, ideas_list in table_data.items():
            df_dict[category] = ideas_list + [""] * (max_ideas - len(ideas_list))

        df = pd.DataFrame(df_dict, index=col_headers).T
        df.index.name = "קטגוריה"
        st.dataframe(df, use_container_width=True)

        col_dl, col_load = st.columns(2)
        with col_dl:
            docx_bytes = data_loader.create_ideas_docx(st.session_state.ideas_table)
            st.download_button(
                "⬇ הורד DOCX", data=docx_bytes,
                file_name="ideas_table.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        with col_load:
            if st.button("📥 טען לאפליקציה", key="load_ideas_btn", use_container_width=True):
                st.session_state.post_ideas = st.session_state.ideas_table
                st.success("✓ רעיונות נטענו! עבור ל-Tab יצירה")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — מחולל סגנון כתיבה
# ═══════════════════════════════════════════════════════════════════════════════
with tab_style:
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
        if st.session_state.preset_style != "none":
            if st.button("🗑 נקה סגנון מוכן", key="clear_preset_tab4"):
                st.session_state.preset_style = "none"
                st.rerun()
        st.info("בחר סגנון מוכן מהרשימה, או השתמש במחולל הסגנון האישי שלמטה.")

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
                "העלה קבצי טקסט (TXT / DOCX)",
                type=["txt", "docx"],
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
                if existing_guide_file.name.endswith(".txt"):
                    guide_text = existing_guide_file.read().decode("utf-8", errors="replace")
                else:
                    from docx import Document as _Doc
                    import io as _io
                    doc_obj = _Doc(_io.BytesIO(existing_guide_file.read()))
                    guide_text = "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
                st.session_state.generated_style_guide = guide_text
                st.success("✓ סגנון נטען בהצלחה")
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
                st.success("✓ הסגנון פעיל — יוחל על הפוסט הבא")
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
