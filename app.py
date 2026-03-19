"""
app.py — AI Content Studio | 4 Tabs
הרצה: streamlit run app.py
"""
import base64 as _b64
import io
import json
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


def _get_aspect_ratio() -> str:
    """Always derive aspect ratio from the radio widget key — never stale session state."""
    label = st.session_state.get("ar_radio", "מרובע (1:1)")
    return ASPECT_RATIOS.get(label, "1:1")


# ── State persistence ─────────────────────────────────────────────────────────
SETTINGS_FILE = Path(__file__).parent / "user_settings.json"
SETTINGS_KEYS = [
    "brand_name", "domain", "profession", "target_audience_custom",
    "style_description", "char_description", "writing_style_mode",
    "writing_style_selected", "image_style_mode", "marketing_framework",
    "language", "content_type", "word_count", "preset_style",
]


def load_user_settings():
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            for k, v in data.items():
                if k not in st.session_state:
                    st.session_state[k] = v
        except Exception:
            pass


def save_user_settings():
    data = {k: st.session_state.get(k, "") for k in SETTINGS_KEYS}
    try:
        SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── Rotating tips shown under the progress bar during generation ──────────────
GENERATION_TIPS = [
    "פוסטים שמתחילים בשאלה מייצרים ב-25% יותר מעורבות.",
    "אנשים קונים מאנשים. שלבו סיפור אישי בתוך התוכן השיווקי.",
    "הקורא הממוצע מקדיש רק 1.7 שניות לפוסט לפני שהוא ממשיך לגלול. הכותרת היא הכל!",
    "חוק ה-80/20 בשיווק: 80% תוכן שנותן ערך ורק 20% תוכן מכירתי ישיר.",
    "שימוש במספרים בכותרת (למשל: \"5 טיפים ל...\") מעלה את אחוזי ההקלקה ב-36%.",
    "סיימו כל פוסט בהנעה לפעולה (CTA) ברורה. אל תתנו לקורא לנחש מה לעשות הלאה.",
    "יום שלישי ורביעי נחשבים לימים עם המעורבות הגבוהה ביותר ברשתות החברתיות.",
    "דברו על ה\"תועלת\" של הלקוח, לא על ה\"תכונות\" של המוצר שלכם.",
    "שימוש באימוג'י בפוסט יכול להעלות את המעורבות ב-33%.",
    "קהל היעד שלכם עמוס. כתבו משפטים קצרים ומרווחים לקריאה נוחה בנייד.",
    "רוצים פוסט שמוכר? בחרו במודל AIDA — הוא בנוי להעביר את הלקוח מסקרנות לרכישה.",
    "מרגישים שהטקסט לא \"אתם\"? העלו קובץ פוסטים קודמים בטאב \"סגנון כתיבה\" והמערכת תנתח את הקול שלכם.",
    "האתר מציע סגנונות כתיבה רבים. קראו את תיאור הסגנון לפני הבחירה.",
    "מודל ה-PAS (בעיה-הקצנה-פתרון) נחשב לאחד הכלים החזקים ביותר לשיווק.",
    "יש לכם כבר ניתוח סגנון מוכן? העלו אותו ישירות בטאב הסגנונות כדי לחסוך זמן.",
    "לחצו על \"הסבר על מודלים\" בסטודיו כדי להבין איזה מודל מתאים למטרה שלכם.",
    "השתמשו בסגנון \"המסביר הפשוט\" כדי להפוך מושגים מורכבים לתוכן שכל אחד מבין.",
    "כתיבה בגובה העיניים (סגנון \"חברי\") מייצרת בדרך כלל יותר תגובות מאשר כתיבה רשמית.",
    "אתם לא חייבים לייצר רעיונות כל פעם. העלו טבלת אקסל עם רעיונות משלכם ישירות לפאנל הימני.",
    "רוצים פוסט ארוך ומעמיק? הגדירו את כמות המילים ל-500+ ובחרו באפשרות \"מאמר/בלוג\" בסטודיו.",
    "העלו מספר תמונות בטאב \"סגנון התמונה\" כדי שהמערכת תלמד את השפה הויזואלית שלכם.",
    "תמונות עם פנים אנושיות מקבלות 38% יותר לייקים מתמונות ללא דמות.",
    "רוצים תמונה מקצועית יותר? סמנו את אפשרות Prompt Enhance והמערכת תשדרג את תיאור התמונה.",
    "צריכים פוסט ללינקדאין? אל תשכחו לשנות את יחס הגובה-רוחב בסטודיו לפני היצירה.",
    "טקסט קצר וקולע על התמונה עוצר את הגלילה. סמנו \"טקסט על תמונה\" בסטודיו.",
    "כדי שהדמות בתמונה תמיד תהיה אתם, ודאו שהעליתם תמונת ייחוס ברורה.",
    "רוצים אווירה ספציפית? תארו במילים \"תאורה חמה\" או \"משרד מודרני\" בטאב סגנון התמונה.",
    "צבעים כחולים משדרים אמינות, בעוד כתום משדר אנרגיה וחיוניות.",
    "אם יש לכם טקסט ספציפי שחשוב לכם שיופיע על התמונה, רשמו אותו ב\"הערות לתמונה\" בסטודיו.",
    "התמונה נוצרת באופן אוטומטי כך שתתאים בדיוק לתוכן הפוסט שנוצר עבורכם.",
    "תקועים בלי רעיון? מחולל הרעיונות מייצר לכם 30 זוויות שונות בלחיצה אחת.",
    "כתיבה על \"חששות של לקוחות\" בונה אמון ומקצרת את תהליך המכירה.",
    "לחצו על \"כתוב עוד רעיונות\" כדי לייצר בנק תכנים לחודש שלם קדימה בתוך דקות.",
    "תוכן שמעניק \"ידע שהלקוח לא ידע\" הופך אתכם לאוטוריטה בתחומכם.",
    "בחרו קהל יעד ספציפי מאוד במחולל הרעיונות — ככל שהקהל ממוקד יותר, הפוסט ימיר טוב יותר.",
    "נסו להגדיר קהל יעד חדש לגמרי במחולל הרעיונות וראו אילו זוויות חדשות תקבלו.",
    "לא מוצאים פוסט ישן? בדקו בטאב הארכיון — הכל נשמר שם באופן אוטומטי.",
    "אתם יכולים לייצר פוסט בכמה שפות. פשוט שנו את השפה בסטודיו וצרו גרסה חדשה.",
    "רוצים לשנות רק את התמונה? לחצו על \"צור תמונה\" בלבד מבלי לייצר מחדש את הטקסט.",
    "המערכת תומכת גם ביצירת מאמרים ארוכים. שנו את כמות המילים הרצויה ל-800+.",
    "אתם יכולים לכתוב רעיון לתוכן בטקסט חופשי בפאנל הימני מבלי להשתמש במחולל הרעיונות.",
    "סגנון ה-Storytelling מעלה את זמן השהייה של הקוראים בפוסט שלכם.",
    "השתמשו בתיבת ה\"הערות המיוחדות\" בסטודיו כדי לבקש מה-AI לשלב האשטאגים או בדיחה.",
    "כתיבה בפורמט של רשימה (Bullet points) הופכת את הפוסט להרבה יותר קריא.",
    "תמיד כדאי לעבור על הטקסט הסופי ולהוסיף לו נגיעה אישית אחרונה לפני הפרסום.",
    "נסו לתאר סגנון של סרט מוכר בתיאור סגנון התמונה כדי לקבל תוצאה ויזואלית מעניינת.",
    "פוסטים שכוללים נתון סטטיסטי נתפסים כאמינים יותר ב-75%.",
    "בצעו A/B Testing — צרו שני פוסטים על אותו רעיון עם סגנונות כתיבה שונים ותראו מה עובד.",
    "שילוב נכון בין סגנון הכתיבה למודל השיווקי הוא הסוד ליצירת תוכן שגם נשמע טוב וגם מוכר.",
    "בחרו \"סגנון אוטומטי\" כדי שהמערכת תבחר עבורכם את סגנון הכתיבה המתאים ביותר לרעיון.",
]


def _tips_rotator_html(font_b64: str = "") -> str:
    """Returns a full-page HTML document for _stc.html() that shows rotating tips.

    Uses the Assistant variable font when font_b64 is provided, otherwise
    falls back to Heebo from Google Fonts (both support Hebrew).
    Tips rotate every 7 seconds with a smooth slide-fade transition.
    """
    import json as _json
    tips_js = _json.dumps(GENERATION_TIPS, ensure_ascii=False)
    icons_js = _json.dumps(
        ["💡","✨","🚀","🎯","📱","🎨","📊","💬","🔥","⚡","🌟","💎","🧠","🎤","📣"],
        ensure_ascii=False,
    )
    font_face = (
        f"@font-face{{font-family:'Assistant';"
        f"src:url('data:font/truetype;base64,{font_b64}') format('truetype');"
        f"font-weight:100 900;}}"
        if font_b64
        else "@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700&display=swap');"
    )
    ff = "'Assistant','Heebo','Arial Hebrew',Arial,sans-serif"
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
{font_face}
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{
  width:100%;height:100%;
  background:transparent;
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}}
#wrap{{
  width:96%;max-width:780px;
  direction:rtl;
  font-family:{ff};
}}
#card{{
  position:relative;
  background:linear-gradient(135deg,rgba(109,40,217,0.18),rgba(30,64,175,0.14));
  border:1.5px solid rgba(167,139,250,0.40);
  border-radius:22px;
  padding:1.6rem 2.2rem 1.8rem;
  overflow:hidden;
  box-shadow:0 8px 32px rgba(109,40,217,0.22), inset 0 1px 0 rgba(255,255,255,0.06);
}}
/* animated glow border */
#card::before{{
  content:'';position:absolute;inset:-1px;border-radius:23px;
  background:conic-gradient(from var(--angle,0deg),
    transparent 60%,rgba(167,139,250,0.5) 75%,transparent 90%);
  animation:spin 4s linear infinite;z-index:0;
}}
@property --angle{{syntax:'<angle>';inherits:false;initial-value:0deg;}}
@keyframes spin{{to{{--angle:360deg;}}}}
#card-inner{{position:relative;z-index:1;}}
#icon{{
  font-size:2.4rem;
  display:block;
  text-align:center;
  margin-bottom:0.55rem;
  filter:drop-shadow(0 0 10px rgba(167,139,250,0.7));
  transition:opacity .45s ease,transform .45s ease;
}}
#text{{
  font-size:1.35rem;
  font-weight:600;
  line-height:1.65;
  color:rgba(255,255,255,0.93);
  text-align:center;
  direction:rtl;
  transition:opacity .45s ease,transform .45s ease;
  min-height:2.8rem;
}}
/* progress bar */
#prog-bar{{
  margin-top:1.1rem;
  height:3px;
  border-radius:3px;
  background:rgba(255,255,255,0.10);
  overflow:hidden;
}}
#prog-fill{{
  height:100%;width:100%;
  background:linear-gradient(90deg,#a78bfa,#60a5fa);
  border-radius:3px;
  transform-origin:left;
  animation:prog 7s linear;
}}
@keyframes prog{{from{{transform:scaleX(1);}}to{{transform:scaleX(0);}}}}
/* dots */
#dots{{display:flex;justify-content:center;gap:6px;margin-top:0.85rem;}}
.dot{{width:7px;height:7px;border-radius:50%;
  background:rgba(167,139,250,0.25);
  transition:background .3s,transform .3s;}}
.dot.on{{background:rgba(167,139,250,0.9);transform:scale(1.5);}}
</style></head><body>
<div id="wrap">
  <div id="card">
    <div id="card-inner">
      <span id="icon">💡</span>
      <div id="text"></div>
      <div id="prog-bar"><div id="prog-fill"></div></div>
      <div id="dots"></div>
    </div>
  </div>
</div>
<script>
var tips={tips_js};
var icons={icons_js};
var DOT_COUNT=7;
var INTERVAL=7000;
// shuffle
for(var i=tips.length-1;i>0;i--){{
  var j=Math.floor(Math.random()*(i+1));
  var t=tips[i];tips[i]=tips[j];tips[j]=t;
}}
var idx=0;
var iconEl=document.getElementById('icon');
var textEl=document.getElementById('text');
var fillEl=document.getElementById('prog-fill');
var dotsEl=document.getElementById('dots');
// build dots
for(var d=0;d<DOT_COUNT;d++){{
  var dot=document.createElement('div');
  dot.className='dot'+(d===0?' on':'');
  dot.id='d'+d;
  dotsEl.appendChild(dot);
}}
function showTip(){{
  // out
  iconEl.style.opacity='0';iconEl.style.transform='translateY(-6px)';
  textEl.style.opacity='0';textEl.style.transform='translateY(-8px)';
  setTimeout(function(){{
    textEl.innerHTML=tips[idx];
    iconEl.textContent=icons[idx%icons.length];
    // in
    iconEl.style.opacity='1';iconEl.style.transform='translateY(0)';
    textEl.style.opacity='1';textEl.style.transform='translateY(0)';
    // dots
    var prev=(idx-1+DOT_COUNT)%DOT_COUNT;
    var cur=idx%DOT_COUNT;
    var pEl=document.getElementById('d'+prev);
    var cEl=document.getElementById('d'+cur);
    if(pEl)pEl.classList.remove('on');
    if(cEl)cEl.classList.add('on');
    // restart progress
    fillEl.style.animation='none';
    void fillEl.offsetWidth;
    fillEl.style.animation='prog '+INTERVAL+'ms linear';
    idx=(idx+1)%tips.length;
  }},460);
}}
showTip();
setInterval(showTip,INTERVAL);
</script>
</body></html>
"""


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
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

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
[data-testid="stSidebar"] > div:first-child { padding-top: 0.5rem; }
/* Remove Streamlit default top padding so hero image reaches page top */
.block-container { padding-top: 0 !important; }
section[data-testid="stAppViewContainer"] > div:first-child { padding-top: 0 !important; }
/* Hide all sidebar collapse/expand controls and their icon labels */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[kind="header"],
[data-testid="stSidebarCollapseButton"] button {
    display: none !important;
}
/* Suppress icon-name text only inside the sidebar collapse/header control, not regular buttons */
[data-testid="stSidebar"] header span,
[data-testid="stSidebarCollapseButton"] span {
    font-size: 0 !important;
    visibility: hidden !important;
}

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
    margin-bottom: 1.5rem; letter-spacing: 0.05em;
}
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px; padding: 1.4rem;
    backdrop-filter: blur(10px); margin-bottom: 0.8rem;
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
    color: rgba(255,255,255,0.88); font-size: 1.05rem;
    line-height: 1.6; direction: rtl; text-align: right;
    min-height: 300px; white-space: pre-wrap;
    font-family: 'Assistant', sans-serif;
}
/* Generate button — larger and bolder */
#generate_post_btn,
button[data-testid="generate_post_btn"] {
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.02em !important;
    padding: 0.9rem 1rem !important;
    min-height: 54px !important;
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
    background: linear-gradient(135deg, rgba(124,58,237,0.7), rgba(59,130,246,0.7)) !important;
    color: white !important;
    border: 1px solid rgba(124,58,237,0.4) !important;
    border-radius: 14px !important; font-weight: 600 !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(124,58,237,0.2) !important;
}
.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #7c3aed, #3b82f6) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.4) !important;
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
.stTextArea textarea,
textarea,
[data-baseweb="textarea"] textarea,
[data-baseweb="textarea"] [data-baseweb="base-input"] textarea,
[data-baseweb="base-input"] textarea {
    background: #12122a !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    direction: rtl;
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
    padding: 1rem !important;
}
textarea::placeholder,
.stTextArea textarea::placeholder,
[data-baseweb="textarea"] textarea::placeholder,
[data-baseweb="base-input"] textarea::placeholder {
    color: rgba(255,255,255,0.38) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.38) !important;
    opacity: 1 !important;
}

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
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    direction: rtl;
}
input::placeholder,
.stTextInput input::placeholder,
[data-baseweb="input"] input::placeholder,
[data-baseweb="base-input"] input::placeholder {
    color: rgba(255,255,255,0.38) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.38) !important;
    opacity: 1 !important;
}

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
    gap: 0.25rem !important;
}
/* tabs — individual tab */
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: rgba(255,255,255,0.55) !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    padding: 0.65rem 1.1rem !important;
    border-radius: 10px 10px 0 0 !important;
    transition: color 0.18s ease, background 0.18s ease !important;
}
.stTabs [data-baseweb="tab"] span,
.stTabs [data-baseweb="tab"] div,
.stTabs [data-baseweb="tab"] p {
    color: rgba(255,255,255,0.55) !important;
    font-size: 1rem !important;
    transition: color 0.18s ease !important;
}
/* hover state */
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(124,58,237,0.12) !important;
    color: rgba(255,255,255,0.9) !important;
}
.stTabs [data-baseweb="tab"]:hover span,
.stTabs [data-baseweb="tab"]:hover div,
.stTabs [data-baseweb="tab"]:hover p {
    color: rgba(255,255,255,0.9) !important;
}
/* active tab */
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: white !important;
    background: rgba(124,58,237,0.08) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] span,
.stTabs [data-baseweb="tab"][aria-selected="true"] div,
.stTabs [data-baseweb="tab"][aria-selected="true"] p {
    color: white !important;
    font-weight: 600 !important;
}
/* tab highlight bar */
.stTabs [data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, #7c3aed, #3b82f6) !important;
    height: 3px !important;
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

/* ── Dialog / Modal overrides ──────────────────────────────────────────────── */
/* Base: dark text on white background, full RTL */
[data-testid="stDialog"] { direction: rtl !important; }
[data-testid="stDialog"] * {
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
}
/* Buttons: white text */
[data-testid="stDialog"] button,
[data-testid="stDialog"] button * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
/* All text blocks right-aligned */
[data-testid="stDialog"] p,
[data-testid="stDialog"] div,
[data-testid="stDialog"] span:not(input) {
    text-align: right !important;
    direction: rtl !important;
}
/* Category headers — bigger, bolder, more prominent */
[data-testid="stDialog"] strong {
    display: block !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #1a1040 !important;
    -webkit-text-fill-color: #1a1040 !important;
    border-bottom: 1px solid rgba(124,58,237,0.18) !important;
    padding-bottom: 0.15rem !important;
    margin-top: 0.7rem !important;
    margin-bottom: 0.05rem !important;
}
/* Compact checkbox rows */
[data-testid="stDialog"] [data-testid="stCheckbox"] {
    margin: 0 !important;
    padding: 0 !important;
    min-height: unset !important;
}
/* Checkbox label: RTL row — text on left, box on RIGHT */
[data-testid="stDialog"] [data-testid="stCheckbox"] label {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-end !important;
    gap: 0.45rem !important;
    direction: rtl !important;
    width: 100% !important;
    padding: 0.12rem 0 !important;
    margin: 0 !important;
    cursor: pointer !important;
    font-size: 0.87rem !important;
    font-weight: 400 !important;
    line-height: 1.25 !important;
    color: #222222 !important;
    -webkit-text-fill-color: #222222 !important;
}
/* The span holding the idea text — takes remaining space, right-aligned */
[data-testid="stDialog"] [data-testid="stCheckbox"] label span {
    flex: 1 !important;
    text-align: right !important;
    direction: rtl !important;
    color: #222222 !important;
    -webkit-text-fill-color: #222222 !important;
}
/* Checkbox input — appears on far RIGHT (first in RTL flex) */
[data-testid="stDialog"] [data-testid="stCheckbox"] input[type="checkbox"] {
    order: 1 !important;
    flex-shrink: 0 !important;
    width: 16px !important;
    height: 16px !important;
    accent-color: #7c3aed !important;
    margin: 0 !important;
    cursor: pointer !important;
}
/* Reduce gap between paragraphs */
[data-testid="stDialog"] p { margin-bottom: 0.25rem !important; }
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

/* Domain row: align confirm button to bottom of its column so it sits flush with the input */
div[data-testid="stHorizontalBlock"]:has(#ideas_domain_input) div[data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-end !important;
}
div[data-testid="stHorizontalBlock"]:has(#ideas_domain_input) div[data-testid="column"] > div {
    width: 100% !important;
}
/* Make the domain input field taller to match the button height */
div[data-testid="stHorizontalBlock"]:has(#ideas_domain_input) input#ideas_domain_input,
div[data-testid="stHorizontalBlock"]:has(#ideas_domain_input) [data-baseweb="input"] input,
div[data-testid="stHorizontalBlock"]:has(#ideas_domain_input) [data-baseweb="base-input"] input {
    padding-top: 0.65rem !important;
    padding-bottom: 0.75rem !important;
    min-height: 46px !important;
}

/* compact secondary buttons in columns */
div[data-testid="column"] button[data-testid="baseButton-secondary"] {
    padding: 0.3rem 0.8rem !important;
    font-size: 0.85rem !important;
    min-height: 38px !important;
    height: 38px !important;
    border-radius: 10px !important;
}

/* Expander — clean RTL separation, no overlap */
[data-testid="stExpander"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden !important;
    background: rgba(255,255,255,0.01) !important;
}
[data-testid="stExpander"] summary {
    direction: rtl !important;
    padding: 0.65rem 2.2rem 0.65rem 1rem !important;
    background: rgba(255,255,255,0.02) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: rgba(255,255,255,0.85) !important;
    list-style: none !important;
    cursor: pointer !important;
    position: relative !important;
}
[data-testid="stExpander"] summary::before {
    content: '▼' !important;
    position: absolute !important;
    left: 0.9rem !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 0.55rem !important;
    color: rgba(255,255,255,0.45) !important;
    transition: transform 0.2s ease !important;
    font-family: sans-serif !important;
}
[data-testid="stExpander"] details[open] > summary::before {
    content: '▲' !important;
    color: rgba(167,139,250,0.7) !important;
}
[data-testid="stExpander"] details[open] summary {
    border-bottom: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stExpander"] details > div {
    padding: 0.8rem 0.6rem !important;
}

/* ── Selectbox dropdown popup — contrast fix (best-effort; JS injection is authoritative) ── */
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] [data-baseweb="menu"],
ul[data-baseweb="menu"],
[role="listbox"] {
    background: #0e0e22 !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
}
[data-baseweb="menu"] [role="option"],
[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li,
[role="listbox"] [role="option"] {
    background: #0e0e22 !important;
    color: rgba(255,255,255,0.88) !important;
    -webkit-text-fill-color: rgba(255,255,255,0.88) !important;
    font-size: 0.92rem !important;
    direction: rtl !important;
    text-align: right !important;
}
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] li:hover,
ul[data-baseweb="menu"] li:hover,
[role="listbox"] [role="option"]:hover {
    background: #2d1f5e !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}
[data-baseweb="menu"] [aria-selected="true"],
[data-baseweb="menu"] li[aria-selected="true"],
[data-baseweb="menu"] [data-highlighted],
[data-baseweb="menu"] li[data-highlighted],
[role="listbox"] [aria-selected="true"],
[role="option"][aria-selected="true"],
[data-baseweb="menu"] li:focus,
[data-baseweb="menu"] [role="option"]:focus {
    background: #3b2070 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* ── Tooltip (full-text hover popup on truncated selectbox items) ── */
[data-baseweb="tooltip"],
[role="tooltip"],
[data-baseweb="tooltip"] > div,
[data-baseweb="tooltip"] [data-baseweb="block"] {
    background: #1a1040 !important;
    background-color: #1a1040 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid rgba(167,139,250,0.4) !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6) !important;
}
[data-baseweb="tooltip"] *,
[role="tooltip"] * {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    background: transparent !important;
    background-color: transparent !important;
}


/* Reset-all button — muted red tint to signal destructive action */
#reset_all_btn {
    background: linear-gradient(135deg, rgba(185,28,28,0.7), rgba(220,38,38,0.5)) !important;
    border: 1px solid rgba(239,68,68,0.4) !important;
    color: rgba(255,255,255,0.9) !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    opacity: 0.85 !important;
}
#reset_all_btn:hover {
    background: linear-gradient(135deg, rgba(185,28,28,0.9), rgba(220,38,38,0.75)) !important;
    opacity: 1 !important;
    transform: none !important;
}

/* Uniform button/download-button height in columns (archive cards etc.) */
div[data-testid="column"] .stButton > button,
div[data-testid="column"] .stDownloadButton > button {
    min-height: 40px !important;
}

/* Hide broken Material Icons SVG fallback */
[data-testid="stExpander"] summary svg {
    display: none !important;
}

/* Audience checkboxes — larger, RTL-aligned (checkbox on right = reading start) */
[data-testid="stCheckbox"] {
    padding: 0.3rem 0 !important;
}
[data-testid="stCheckbox"] label {
    display: flex !important;
    flex-direction: row !important;
    direction: rtl !important;
    align-items: center !important;
    gap: 0.6rem !important;
    cursor: pointer !important;
    line-height: 1.4 !important;
    font-size: 0.88rem !important;
    color: rgba(255,255,255,0.85) !important;
    width: 100% !important;
}
[data-testid="stCheckbox"] input[type="checkbox"] {
    width: 20px !important;
    height: 20px !important;
    min-width: 20px !important;
    cursor: pointer !important;
    accent-color: #7c3aed !important;
    flex-shrink: 0 !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── JS: (1) force dropdown contrast via inline styles  (2) hide expander icon text ──
import streamlit.components.v1 as _stc
_stc.html("""
<script>
(function() {
    var pdoc = window.parent.document;

    /* ── 1. Force dropdown/listbox contrast by directly setting inline styles ──
       BaseWeb (Styletron) injects CSS-in-JS !important rules after any <style> tag,
       so CSS-only fixes lose the specificity war. The only reliable override is
       element.style.setProperty(..., 'important') which always wins. */

    var BG_DEFAULT  = '#0e0e22';
    var BG_HOVER    = '#2d1f5e';
    var BG_SELECTED = '#3b2070';
    var TEXT_DEFAULT = 'rgba(255,255,255,0.9)';
    var TEXT_WHITE   = '#ffffff';

    function styleOption(el, bg, text) {
        el.style.setProperty('background',       bg,   'important');
        el.style.setProperty('background-color', bg,   'important');
        el.style.setProperty('color',            text, 'important');
        el.style.setProperty('-webkit-text-fill-color', text, 'important');
    }

    function applyDropdownStyles(root) {
        /* Container backgrounds */
        root.querySelectorAll(
            '[data-baseweb="popover"],[data-baseweb="menu"],[role="listbox"]'
        ).forEach(function(el) {
            el.style.setProperty('background',       BG_DEFAULT, 'important');
            el.style.setProperty('background-color', BG_DEFAULT, 'important');
        });

        /* Option rows */
        root.querySelectorAll(
            '[role="option"],[data-baseweb="menu"] li'
        ).forEach(function(opt) {
            /* determine initial state */
            var isSelected = opt.getAttribute('aria-selected') === 'true';
            styleOption(opt, isSelected ? BG_SELECTED : BG_DEFAULT, isSelected ? TEXT_WHITE : TEXT_DEFAULT);

            /* fix children — BaseWeb puts a <div> inside each li with its own bg */
            opt.querySelectorAll('*').forEach(function(child) {
                child.style.setProperty('background',       'transparent', 'important');
                child.style.setProperty('background-color', 'transparent', 'important');
                child.style.setProperty('color',            'inherit',     'important');
                child.style.setProperty('-webkit-text-fill-color', 'inherit', 'important');
            });

            if (opt._lirazBound) return;
            opt._lirazBound = true;

            opt.addEventListener('mouseenter', function() {
                styleOption(this, BG_HOVER, TEXT_WHITE);
            });
            opt.addEventListener('mouseleave', function() {
                var sel = this.getAttribute('aria-selected') === 'true';
                styleOption(this, sel ? BG_SELECTED : BG_DEFAULT, sel ? TEXT_WHITE : TEXT_DEFAULT);
            });
        });
    }

    /* ── Force white text on all inputs and textareas ── */
    function applyInputStyles(root) {
        root.querySelectorAll(
            'input[type="text"],input[type="number"],input[type="search"],textarea'
        ).forEach(function(el) {
            el.style.setProperty('color',                   '#ffffff', 'important');
            el.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
        });
    }
    applyInputStyles(pdoc);

    /* ── Also force-style tooltip popups (full-text hover on truncated items) ── */
    function applyTooltipStyles(root) {
        root.querySelectorAll('[data-baseweb="tooltip"],[role="tooltip"]').forEach(function(tip) {
            tip.style.setProperty('background',       '#1a1040', 'important');
            tip.style.setProperty('background-color', '#1a1040', 'important');
            tip.style.setProperty('color',            '#ffffff', 'important');
            tip.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
            tip.style.setProperty('border', '1px solid rgba(167,139,250,0.4)', 'important');
            tip.style.setProperty('border-radius', '8px', 'important');
            tip.querySelectorAll('*').forEach(function(child) {
                child.style.setProperty('background',       'transparent', 'important');
                child.style.setProperty('background-color', 'transparent', 'important');
                child.style.setProperty('color',            '#ffffff',     'important');
                child.style.setProperty('-webkit-text-fill-color', '#ffffff', 'important');
            });
        });
    }

    /* Run on every DOM mutation so we catch dynamically rendered portals */
    var dropdownObs = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType !== 1) return;
                applyDropdownStyles(node);
                applyTooltipStyles(node);
                applyInputStyles(node);
            });
        });
        /* Also re-apply to whole doc in case aria-selected changed */
        applyDropdownStyles(pdoc);
        applyTooltipStyles(pdoc);
        checkNavTrigger();
    });
    dropdownObs.observe(pdoc.body, { childList: true, subtree: true });
    applyDropdownStyles(pdoc);
    applyTooltipStyles(pdoc);

    /* ── 2. Tab navigation triggers ── */
    function _clickTab(textFragment) {
        var tabs = pdoc.querySelectorAll('button[role="tab"]');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].innerText.includes(textFragment)) {
                if (tabs[i].getAttribute('aria-selected') !== 'true') {
                    tabs[i].click();
                }
                break;
            }
        }
    }
    function checkNavTrigger() {
        if (pdoc.getElementById('liraz-nav-to-ideas'))  { _clickTab('מחולל רעיונות'); }
        if (pdoc.getElementById('liraz-nav-to-create'))  { _clickTab('יצירה'); }
    }

    /* ── 3. Hide Material Icon spans in expander summaries ── */
    function hideIconSpans() {
        pdoc.querySelectorAll('[data-testid="stExpander"] summary').forEach(function(summary) {
            summary.querySelectorAll('span').forEach(function(span) {
                var text = span.textContent.trim();
                if (text.length > 0 && /^[a-z][a-z_]*$/.test(text)) {
                    span.style.cssText = 'display:none!important;';
                }
            });
        });
    }
    hideIconSpans();
    var iconObs = new MutationObserver(hideIconSpans);
    iconObs.observe(pdoc.body, { childList: true, subtree: true });
})();
</script>
""", height=0, scrolling=False)

# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "post_text": "",
        "image_bytes": None,
        "style_guide": None,
        "post_ideas": None,
        "style_bytes": None,
        "ideas_bytes": None,
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
        "preset_style": "auto",
        "style_choice_explanation": "",
        "auto_chosen_style": "",
        "marketing_framework": "none",
        "post_notes": "",
        "image_notes": "",
        "archive": [],
        "archive_view_idx": None,
        "custom_content": "",
        "_jump_to_ideas": False,
        "_last_ideas_domain": "",
        "_pending_audience_gen": "",
        "_pending_table_gen": {},
        "_ideas_rerun_trigger": False,
        "free_style_text": "",
        "show_fw_guide": False,
        "generating": False,
        "settings_loaded": False,
        "reference_images": [None, None, None],
        "style_text_buffer": [],
        "pasted_sample_key": 0,
        "retry_feedback": "",
        "image_retry_feedback": "",
        "last_image_style": "",
        "prev_image_bytes": None,
        "_jump_to_create": False,
        "current_archive_idx": None,
        "style_usage_instructions": "",
        "selected_ideas": [],
        "bulk_queue": [],
        "bulk_total": 0,
        "bulk_running": False,
        "bulk_results": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.settings_loaded:
        load_user_settings()
        st.session_state.settings_loaded = True

init_state()


@st.dialog("✅ בחירת רעיונות", width="large")
def _show_ideas_modal(post_ideas: dict):
    st.markdown("סמן את הרעיונות שברצונך לייצר עבורם פוסטים ותמונות:")
    col_a, col_d, _ = st.columns([1, 1, 4])
    with col_a:
        if st.button("בחר הכל", key="modal_sel_all"):
            for _mcat, _mideas in post_ideas.items():
                for _mj in range(len(_mideas)):
                    st.session_state[f"_mcb_{_mcat}_{_mj}"] = True
            st.rerun()
    with col_d:
        if st.button("בטל הכל", key="modal_desel_all"):
            for _mcat, _mideas in post_ideas.items():
                for _mj in range(len(_mideas)):
                    st.session_state[f"_mcb_{_mcat}_{_mj}"] = False
            st.rerun()

    _existing_sel = {(d["category"], d["idea"]) for d in st.session_state.selected_ideas}
    for _mcat, _mideas in post_ideas.items():
        st.markdown(f"**{_mcat}**")
        for _mj, _mtext in enumerate(_mideas):
            _mkey = f"_mcb_{_mcat}_{_mj}"
            st.checkbox(_mtext, value=(_mcat, _mtext) in _existing_sel, key=_mkey)

    st.markdown("---")
    col_ok, col_cancel = st.columns([1, 1])
    with col_ok:
        if st.button("✅ אישור", key="modal_confirm", use_container_width=True):
            _result = []
            for _mcat, _mideas in post_ideas.items():
                for _mj, _mtext in enumerate(_mideas):
                    if st.session_state.get(f"_mcb_{_mcat}_{_mj}", False):
                        _result.append({"category": _mcat, "idea": _mtext})
            st.session_state.selected_ideas = _result
            st.rerun()
    with col_cancel:
        if st.button("ביטול", key="modal_cancel", use_container_width=True):
            st.rerun()


# Callback used by Ideas-tab widgets (checkboxes, etc.) to signal "stay on Ideas tab"
def _ideas_tab_action():
    st.session_state["_ideas_rerun_trigger"] = True


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


# ── Fallback variable defaults (used in tabs regardless of sidebar expander state) ──
category = None
idea = None
face_source = st.session_state.character_image_bytes

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if not check_api_keys():
        st.stop()

    default_style, default_ideas = load_default_data()
    style_guide = st.session_state.style_guide or default_style

    # ── 1. Ideas expander (expanded — visible by default) ──
    with st.expander("💡 רעיונות ובחירת תוכן", expanded=True):
        custom_content = st.text_input(
            "✏️ רעיון לפוסט",
            value=st.session_state.get("custom_content", ""),
            placeholder="כתוב בקצרה...",
            key="sb_custom_content",
        )
        st.session_state.custom_content = custom_content

        post_ideas = st.session_state.post_ideas
        if post_ideas:
            def _clear_custom_idea():
                # Clear both the logical key and the widget key so the text input visually resets
                st.session_state.custom_content = ""
                st.session_state["sb_custom_content"] = ""

            # When a selection is active, filter dropdowns to only selected ideas
            if st.session_state.selected_ideas:
                _active_cats = list(dict.fromkeys(d["category"] for d in st.session_state.selected_ideas))
                category = st.selectbox(
                    "קטגוריה", options=_active_cats, label_visibility="collapsed",
                    on_change=_clear_custom_idea,
                )
                _active_ideas = [d["idea"] for d in st.session_state.selected_ideas
                                 if d["category"] == category]
                idea = st.selectbox("רעיון מהרשימה", options=_active_ideas,
                                    label_visibility="collapsed", on_change=_clear_custom_idea)
            else:
                category = st.selectbox(
                    "קטגוריה", options=list(post_ideas.keys()), label_visibility="collapsed",
                    on_change=_clear_custom_idea,
                )
                ideas_list = post_ideas.get(category, [])
                idea = st.selectbox("רעיון מהרשימה", options=ideas_list, label_visibility="collapsed",
                                    on_change=_clear_custom_idea)

            if st.button("🗑 איפוס רעיונות", use_container_width=True, key="reset_ideas_btn"):
                st.session_state.post_ideas = None
                st.session_state.ideas_bytes = None
                st.session_state.ideas_table = {}
                st.session_state.ideas_tables_history = []
                st.session_state.ideas_table_idx = 0
                st.session_state.selected_ideas = []
                st.rerun()
        else:
            st.caption("טען רעיונות ממחולל הרעיונות או מקובץ")

        if st.button("💡 מחולל הרעיונות", use_container_width=True, key="goto_ideas_btn"):
            st.session_state["_jump_to_ideas"] = True
            st.rerun()

        uploaded_ideas = st.file_uploader("טען רעיונות (DOCX / XLSX / PDF)", type=["docx", "xlsx", "pdf"], key="ideas_upload")
        if uploaded_ideas:
            new_bytes = uploaded_ideas.read()
            if new_bytes != st.session_state.ideas_bytes:
                st.session_state.ideas_bytes = new_bytes
                _suffix = uploaded_ideas.name.rsplit(".", 1)[-1].lower()
                st.session_state.post_ideas = data_loader.load_post_ideas(new_bytes, suffix=_suffix)
                st.session_state.selected_ideas = []  # clear selection when new file loaded
                st.rerun()

        # ── Idea selection button ──
        if post_ideas:
            _n_sel = len(st.session_state.selected_ideas)
            _sel_label = f"✅ בחר רעיונות ({_n_sel} נבחרו)" if _n_sel else "✅ בחר רעיונות"
            _scol1, _scol2 = st.columns([4, 1])
            with _scol1:
                if st.button(_sel_label, key="open_ideas_modal_btn", use_container_width=True):
                    _show_ideas_modal(post_ideas)
            with _scol2:
                if _n_sel and st.button("✖", key="clear_idea_sel_btn", use_container_width=True):
                    st.session_state.selected_ideas = []
                    st.rerun()

    # ── 2. Special Notes (always visible) ──
    post_notes_val = st.text_area(
        "📝 הערות מיוחדות לפוסט",
        value=st.session_state.post_notes,
        height=70,
        key="sb_post_notes",
        placeholder="הנחיות ספציפיות, טון, אורך...",
    )
    st.session_state.post_notes = post_notes_val

    image_notes_val = st.text_area(
        "🖼 הערות לתמונה",
        value=st.session_state.image_notes,
        height=70,
        key="sb_image_notes",
        placeholder="הנחיות ספציפיות לתמונה...",
    )
    st.session_state.image_notes = image_notes_val

    # ── 3. Generate buttons ──
    _gen_disabled = st.session_state.get("generating", False)
    generate_btn = st.button(
        "✦ צור פוסט + תמונה",
        use_container_width=True,
        disabled=_gen_disabled,
        key="generate_post_btn",
    )
    if generate_btn:
        st.session_state["_jump_to_create"] = True
        st.session_state["_text_only"] = False

    generate_text_only_btn = st.button(
        "✍️ צור פוסט בלבד (ללא תמונה)",
        use_container_width=True,
        disabled=_gen_disabled,
        key="generate_text_only_btn",
    )
    if generate_text_only_btn:
        st.session_state["_jump_to_create"] = True
        st.session_state["_text_only"] = True

    # ── Bulk generation buttons ──
    _bulk_source = st.session_state.selected_ideas or [
        {"category": _bc, "idea": _bi}
        for _bc, _bil in (post_ideas or {}).items()
        for _bi in _bil
    ]
    if _bulk_source and face_source:
        _bulk_disabled = bool(st.session_state.get("generating") or st.session_state.get("bulk_running"))
        bulk_btn = st.button(
            f"🚀 צור הכל ({len(_bulk_source)} רעיונות)",
            use_container_width=True,
            key="bulk_generate_btn",
            disabled=_bulk_disabled,
        )
        if bulk_btn:
            st.session_state.bulk_queue = _bulk_source.copy()
            st.session_state.bulk_total = len(_bulk_source)
            st.session_state.bulk_results = []
            st.session_state.bulk_running = True
            st.session_state.bulk_text_only = False
            st.session_state["_jump_to_create"] = True
            st.rerun()

        bulk_text_only_btn = st.button(
            f"✍️ צור כל הפוסטים בלבד ({len(_bulk_source)} רעיונות)",
            use_container_width=True,
            key="bulk_text_only_btn",
            disabled=_bulk_disabled,
        )
        if bulk_text_only_btn:
            st.session_state.bulk_queue = _bulk_source.copy()
            st.session_state.bulk_total = len(_bulk_source)
            st.session_state.bulk_results = []
            st.session_state.bulk_running = True
            st.session_state.bulk_text_only = True
            st.session_state["_jump_to_create"] = True
            st.rerun()

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── 4. Reference image thumbnails ──
    active_refs = [r for r in st.session_state.reference_images if r]
    if active_refs:
        face_source = active_refs[0]["bytes"]
        thumb_cols = st.columns(len(active_refs))
        for ci, ref in enumerate(active_refs):
            with thumb_cols[ci]:
                st.image(ref["bytes"], width=55)
                st.caption(ref["label"][:5], unsafe_allow_html=False)
    else:
        st.info("העלה תמונת ייחוס בלשונית הגדרות תמונה")

    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── אקורדיון: סגנון כתיבה ──
    with st.expander("✍️ סגנון כתיבה", expanded=False):
        style_options = ["auto", "none"] + list(PRESET_STYLES.keys())
        _none_label = "סגנון מותאם (DOCX)" if st.session_state.style_bytes else "ללא (מהמחולל)"
        style_display = ["🤖 בחירת המערכת"] + [_none_label] + [PRESET_STYLES[k]["hebrew_name"] for k in PRESET_STYLES]
        cur_style_idx = style_options.index(st.session_state.preset_style) if st.session_state.preset_style in style_options else 0
        selected_style_idx = st.selectbox(
            "סגנון כתיבה",
            options=range(len(style_options)),
            format_func=lambda i: style_display[i],
            index=cur_style_idx,
            label_visibility="collapsed",
        )
        st.session_state.preset_style = style_options[selected_style_idx]
        if st.session_state.preset_style == "auto":
            st.caption("המערכת תבחר את סגנון הכתיבה המתאים ביותר לרעיון שלך באופן אוטומטי")
        elif st.session_state.preset_style != "none":
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
            st.session_state.preset_style not in ("none", "auto")
            or st.session_state.style_bytes
            or st.session_state.generated_style_guide
        )
        if _style_active:
            if st.button("🗑 איפוס סגנון כתיבה", use_container_width=True, key="reset_style_sidebar"):
                st.session_state.preset_style = "auto"
                st.session_state.style_bytes = None
                st.session_state.style_guide = None
                st.session_state.generated_style_guide = ""
                st.session_state.style_upload_key += 1
                st.rerun()

        if st.button("💾 שמור סגנון", use_container_width=True, key="save_style_btn"):
            save_user_settings()
            st.success("✓ נשמר")

    # ── אקורדיון: מודל כתיבה שיווקית ──
    with st.expander("📊 מודל כתיבה שיווקית", expanded=False):
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

        if st.button("💾 שמור מודל", use_container_width=True, key="save_fw_btn"):
            save_user_settings()
            st.success("✓ נשמר")

    # ── אקורדיון: הגדרות פוסט ──
    with st.expander("📋 הגדרות פוסט", expanded=False):
        selected_language = st.selectbox(
            "🌐 שפת פלט", options=LANGUAGES,
            index=LANGUAGES.index(st.session_state.language) if st.session_state.language in LANGUAGES else 0,
            key="sb_language",
        )
        st.session_state.language = selected_language

        ct_keys = list(CONTENT_TYPES.keys())
        selected_ct = st.selectbox(
            "📋 סוג תוכן", options=ct_keys,
            index=ct_keys.index(st.session_state.content_type) if st.session_state.content_type in ct_keys else 0,
            key="sb_content_type",
        )
        st.session_state.content_type = selected_ct
        st.caption(f"מומלץ: {CONTENT_TYPES[selected_ct]['words']} מילים")

        word_count_val = st.number_input(
            "כמות מילים מותאמת (0 = ברירת מחדל)",
            min_value=0, max_value=3000, value=st.session_state.word_count,
            step=50, key="sb_word_count",
        )
        st.session_state.word_count = word_count_val

        if st.button("💾 שמור הגדרות", use_container_width=True, key="save_post_settings_btn"):
            save_user_settings()
            st.success("✓ נשמר")

    # ── Reset all settings ──
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    if st.button("🔄 איפוס כל ההגדרות", use_container_width=True, key="reset_all_btn"):
        preserve = {"_jump_to_ideas", "_jump_to_create", "_ideas_rerun_trigger",
                    "settings_loaded"}
        for k in list(st.session_state.keys()):
            if k not in preserve:
                del st.session_state[k]
        st.rerun()


# ── Tab navigation: sidebar buttons OR tab-specific interactions ──────────────
if st.session_state.get("_jump_to_ideas") or st.session_state.get("_ideas_rerun_trigger"):
    st.session_state["_jump_to_ideas"] = False
    st.session_state["_ideas_rerun_trigger"] = False
    st.markdown('<div id="liraz-nav-to-ideas" style="display:none"></div>', unsafe_allow_html=True)

if st.session_state.get("_jump_to_create"):
    st.session_state["_jump_to_create"] = False
    st.markdown('<div id="liraz-nav-to-create" style="display:none"></div>', unsafe_allow_html=True)

# ── Bulk generation engine — processes one item per rerun ─────────────────────
if st.session_state.get("bulk_running") and st.session_state.get("bulk_queue"):
    _bitem = st.session_state.bulk_queue[0]
    _bcat  = _bitem["category"]
    _bidea = _bitem["idea"]

    _bstyle   = st.session_state.style_description.strip() or st.session_state.get("free_style_text", "").strip()
    _beff_sty = st.session_state.generated_style_guide or (st.session_state.style_guide or "")
    _bauto_key  = ""
    _bauto_expl = ""
    if st.session_state.preset_style == "auto":
        _bauto_key, _bauto_expl = generator.select_best_style(_bcat, _bidea)
        _bpreset = PRESET_STYLES[_bauto_key]["prompt_instruction"]
    elif st.session_state.preset_style != "none":
        _bpreset = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"]
    else:
        _bpreset = ""
    _bfw      = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] \
                if st.session_state.marketing_framework != "none" else ""
    _bnotes   = "\n".join(filter(None, [
        st.session_state.post_notes,
        f"הוראות ליישום הסגנון:\n{st.session_state.style_usage_instructions}"
        if st.session_state.style_usage_instructions else ""
    ]))
    _bextra   = [r["bytes"] for r in st.session_state.reference_images[1:] if r]
    _bwc      = st.session_state.word_count if st.session_state.word_count > 0 else None

    _bpost_text   = ""
    _bimage_bytes = None
    _bdone_so_far = len(st.session_state.bulk_results)
    _btotal_count = st.session_state.bulk_total or 1
    # Show patience message + tips during the blocking API calls
    st.markdown(f"""
<div style="direction:rtl;text-align:center;padding:0.7rem 1.2rem 0.2rem;
  background:linear-gradient(135deg,rgba(109,40,217,0.14),rgba(30,64,175,0.10));
  border:1px solid rgba(167,139,250,0.30);border-radius:16px;margin-bottom:0.5rem;">
  <div style="font-size:1.1rem;font-weight:700;color:rgba(255,255,255,0.95);
    font-family:'Assistant','Heebo',Arial,sans-serif;">
    ⏳ יוצר פוסט {_bdone_so_far + 1} מתוך {_btotal_count}: <em>{_bitem["idea"][:50]}</em>
  </div>
  <div style="font-size:0.85rem;color:rgba(255,255,255,0.60);margin-top:0.2rem;
    font-family:'Assistant','Heebo',Arial,sans-serif;">
    השאירו את החלון פתוח — נחזור אליכם בקרוב 🙏
  </div>
</div>""", unsafe_allow_html=True)
    _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)
    try:
        _bpost_text = generator.generate_post(
            _beff_sty, _bcat, _bidea,
            language=st.session_state.language,
            content_type=st.session_state.content_type,
            word_count=_bwc,
            preset_style_instruction=_bpreset,
            marketing_framework=_bfw,
            post_notes=_bnotes,
        )
        if not st.session_state.get("bulk_text_only"):
            _bscene = generator.generate_image_prompt(_bpost_text)
            if st.session_state.image_notes:
                _bscene = f"{_bscene}. Additional direction: {st.session_state.image_notes}"
            _bimage_bytes = generator.generate_image(
                face_source, _bscene,
                aspect_ratio=_get_aspect_ratio(),
                style_description=_bstyle,
                add_text=st.session_state.add_text_to_image,
                extra_reference_images=_bextra or None,
            )
    except Exception as _berr:
        st.warning(f"שגיאה ב-\"{_bidea[:40]}\": {_berr}")

    st.session_state.post_text   = _bpost_text
    st.session_state.image_bytes = _bimage_bytes

    _bentry = {
        "post_text": _bpost_text,
        "images": [_bimage_bytes] if _bimage_bytes else [],
        "category": _bcat, "idea": _bidea,
        "content_type": st.session_state.content_type,
        "language": st.session_state.language,
        "preset_style": PRESET_STYLES[st.session_state.preset_style]["hebrew_name"]
                        if st.session_state.preset_style not in ("none", "auto")
                        else (PRESET_STYLES[_bauto_key]["hebrew_name"] if _bauto_key else "ללא"),
        "marketing_framework": st.session_state.marketing_framework,
        "timestamp": int(time.time()),
        "timestamp_str": time.strftime("%d/%m/%Y %H:%M"),
        "auto_chosen_style": _bauto_key,
        "auto_style_explanation": _bauto_expl,
    }
    st.session_state.archive.append(_bentry)
    st.session_state.current_archive_idx = len(st.session_state.archive) - 1
    st.session_state.bulk_results.append(_bentry)
    if len(st.session_state.archive) > 50:
        st.session_state.archive = st.session_state.archive[-50:]

    st.session_state.bulk_queue = st.session_state.bulk_queue[1:]
    st.session_state["_jump_to_create"] = True
    st.rerun()

elif st.session_state.get("bulk_running") and not st.session_state.get("bulk_queue"):
    st.session_state.bulk_running = False

# ── HEADER ────────────────────────────────────────────────────────────────────
_img_b64 = _get_header_image_b64()
_bg_style = (
    f"background-image: linear-gradient(rgba(5,5,15,0.15), rgba(5,5,20,0.2)), url('data:image/jpeg;base64,{_img_b64}'); background-size: cover; background-position: center 40%;"
    if _img_b64
    else "background: linear-gradient(135deg, #0a0a0f, #0d0d1a);"
)
st.markdown(f"""
<div style="
    {_bg_style}
    border-radius: 0 0 20px 20px;
    margin: calc(-6rem - 50px) -4rem 2rem -4rem;
    border: none;
    overflow: hidden;
    height: 430px;
    width: calc(100% + 8rem);
    padding-top: 0;
"></div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_create, tab_ideas, tab_style, tab_visual, tab_archive, tab_guide = st.tabs([
    "🏠 יצירה",
    "💡 מחולל רעיונות",
    "✍️ סגנון כתיבה",
    "🎨 הגדרות תמונה",
    "🗂 ארכיון",
    "📖 הוראות שימוש",
])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — יצירה
# ═══════════════════════════════════════════════════════════════════════════════
with tab_create:
    # ── Bulk generation results ────────────────────────────────────────────────
    if st.session_state.get("bulk_running") or st.session_state.get("bulk_results"):
        _bdone  = len(st.session_state.bulk_results)
        _btotal = st.session_state.bulk_total or 1
        if st.session_state.bulk_running:
            _bnext_idea = st.session_state.bulk_queue[0]["idea"][:50] if st.session_state.bulk_queue else ""
            st.progress(_bdone / _btotal, text=f"מייצר {_bdone + 1} מתוך {_btotal}: {_bnext_idea}...")
            st.markdown("""
<div style="direction:rtl;text-align:center;margin:0.6rem 0 0.2rem 0;
    padding:0.8rem 1.4rem;border-radius:14px;
    background:rgba(124,58,237,0.10);border:1px solid rgba(124,58,237,0.25);">
  <div style="font-size:1.05rem;font-weight:700;color:rgba(255,255,255,0.95);margin-bottom:0.3rem;">
    ⏳ אנא המתינו — יצירת מספר גדול של פוסטים לוקחת זמן
  </div>
  <div style="font-size:0.88rem;color:rgba(255,255,255,0.70);line-height:1.5;">
    השאירו את החלון פתוח ונחזור אליכם בקרוב 🙏
  </div>
</div>""", unsafe_allow_html=True)
            _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)
        else:
            st.success(f"✅ הושלם! {_bdone} פוסטים ותמונות נוצרו בהצלחה")
            if st.button("🗑 נקה תוצאות", key="clear_bulk_results_btn"):
                st.session_state.bulk_results = []
                st.session_state.bulk_total   = 0
                st.rerun()

        for _ri, _res in enumerate(reversed(st.session_state.bulk_results)):
            _aidx = len(st.session_state.bulk_results) - 1 - _ri  # stable index into bulk_results
            _blabel = f"📄 {_res['category']} — {_res['idea'][:60]}"
            with st.expander(_blabel, expanded=(_ri == 0)):
                _rcol_p, _rcol_i = st.columns([1, 1])
                with _rcol_p:
                    st.text_area("", value=_res["post_text"], height=260,
                                 key=f"bulk_post_{_aidx}", label_visibility="collapsed")
                    st.download_button("⬇ טקסט", data=_res["post_text"].encode("utf-8"),
                        file_name=f"bulk_post_{_aidx}.txt", mime="text/plain",
                        use_container_width=True, key=f"bulk_dl_txt_{_aidx}")
                    if _res.get("auto_style_explanation") and _res.get("auto_chosen_style"):
                        _bcsname = PRESET_STYLES.get(_res["auto_chosen_style"], {}).get("hebrew_name", "")
                        st.markdown(f"""
<div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.25);
     border-radius:12px;padding:0.8rem 1rem;margin-top:0.6rem;direction:rtl;text-align:right;">
  <div style="font-size:0.75rem;font-weight:700;color:rgba(167,139,250,0.9);margin-bottom:0.3rem;">
      🤖 המערכת בחרה: {_bcsname}
  </div>
  <div style="font-size:0.82rem;color:rgba(255,255,255,0.72);line-height:1.5;">
      {_res["auto_style_explanation"]}
  </div>
</div>""", unsafe_allow_html=True)
                    # ── Per-item post retry ──
                    st.markdown('<div class="section-label" style="margin-top:0.7rem;">💬 הערות לשיפור הפוסט</div>', unsafe_allow_html=True)
                    _bpfb = st.text_area("", height=70, key=f"bulk_pfb_{_aidx}",
                        placeholder="למשל: קצר יותר, הוסף סטטיסטיקה, שנה טון...",
                        label_visibility="collapsed")
                    if st.button("🔄 צור פוסט מחדש", key=f"bulk_rp_{_aidx}", use_container_width=True):
                        _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)
                        with st.spinner(f"מחדש פוסט עבור: {_res['idea'][:40]}..."):
                            try:
                                _beff = st.session_state.generated_style_guide or (st.session_state.get("style_guide") or "")
                                _bprst = PRESET_STYLES.get(_res.get("auto_chosen_style") or st.session_state.preset_style, {}).get("prompt_instruction", "")
                                _bfw2 = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""
                                _new_post = generator.generate_post(
                                    _beff, _res["category"], _res["idea"],
                                    language=_res.get("language", st.session_state.language),
                                    content_type=_res.get("content_type", st.session_state.content_type),
                                    word_count=st.session_state.word_count or None,
                                    preset_style_instruction=_bprst,
                                    marketing_framework=_bfw2,
                                    retry_feedback=_bpfb,
                                )
                                st.session_state.bulk_results[_aidx]["post_text"] = _new_post
                            except Exception as _pe:
                                st.error(f"שגיאה: {_pe}")
                        st.rerun()

                with _rcol_i:
                    for _ji, _bimg in enumerate(_res.get("images") or []):
                        if _ji > 0:
                            st.markdown('<div style="margin-top:0.5rem; opacity:0.6; font-size:0.75rem; direction:rtl;">🖼 גרסה קודמת</div>', unsafe_allow_html=True)
                        st.image(_bimg, use_container_width=True)
                        st.download_button("⬇ תמונה", data=_bimg,
                            file_name=f"bulk_img_{_aidx}_{_ji}.png", mime="image/png",
                            use_container_width=True, key=f"bulk_dl_img_{_aidx}_{_ji}")
                    # ── Per-item image retry ──
                    st.markdown('<div class="section-label" style="margin-top:0.7rem;">💬 הערות לשיפור התמונה</div>', unsafe_allow_html=True)
                    _bifb = st.text_area("", height=70, key=f"bulk_ifb_{_aidx}",
                        placeholder="למשל: שנה רקע לטבע, הוסף תאורה דרמטית...",
                        label_visibility="collapsed")
                    if st.button("🔄 צור תמונה מחדש", key=f"bulk_ri_{_aidx}", use_container_width=True):
                        _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)
                        with st.spinner(f"מחדש תמונה עבור: {_res['idea'][:40]}..."):
                            try:
                                _bi_scene = generator.generate_image_prompt(_res["post_text"])
                                if st.session_state.image_notes:
                                    _bi_scene = f"{_bi_scene}. Additional direction: {st.session_state.image_notes}"
                                if _bifb:
                                    _bi_scene = f"{_bi_scene}. User feedback: {_bifb}"
                                _bi_style = st.session_state.get("last_image_style") or st.session_state.style_description or ""
                                _bextra2 = [r["bytes"] for r in st.session_state.reference_images[1:] if r]
                                _new_img = generator.generate_image(
                                    face_source, _bi_scene,
                                    aspect_ratio=_get_aspect_ratio(),
                                    style_description=_bi_style,
                                    add_text=st.session_state.add_text_to_image,
                                    extra_reference_images=_bextra2 or None,
                                )
                                st.session_state.bulk_results[_aidx]["images"].append(_new_img)
                            except Exception as _ie:
                                st.error(f"שגיאה: {_ie}")
                        st.rerun()

        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)

    # ── הגדרות תמונה ──
    col_settings, col_spacer = st.columns([2, 1])
    with col_settings:
        st.markdown("""
<div style="direction:rtl; text-align:right; margin-bottom:1.2rem; margin-top:0.2rem;">
    <div style="font-size:1.5rem; font-weight:800; color:white; letter-spacing:-0.01em; line-height:1.2;">
        🎨 הגדרות תמונה
    </div>
    <div style="width:3rem; height:3px; background:linear-gradient(90deg,#a78bfa,#3b82f6);
                border-radius:2px; margin-top:0.4rem; margin-right:0;"></div>
</div>""", unsafe_allow_html=True)
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
    if (generate_btn or generate_text_only_btn) and not st.session_state.get("generating", False):
        if not face_source:
            st.error("יש להעלות תמונת ייחוס בלשונית הגדרות תמונה")
            st.stop()

        # Resolve idea source: custom input overrides dropdown
        effective_idea = st.session_state.custom_content.strip() or idea or ""
        effective_category = category or "כללי"

        if not effective_idea:
            st.error("יש להזין רעיון — בחר מהרשימה או כתוב רעיון חופשי")
            st.stop()

        st.session_state.generating = True

        # ── Re-read all current inputs fresh at generation time ──────────────
        # Image style: prefer explicit style_description; fall back to whatever
        # is currently typed in the free-style textarea (even if not yet Applied)
        _this_gen_style = (
            st.session_state.style_description.strip()
            or st.session_state.get("free_style_text", "").strip()
        )
        st.session_state.last_image_style = _this_gen_style   # persist for image-only retries
        st.session_state.prev_image_bytes = None              # clear previous on full regeneration

        # Writing style: generated guide > uploaded DOCX guide
        # (both already in session_state, re-read here for clarity)
        # Preset writing style, marketing framework, language, content_type,
        # word_count, notes — all already current via sidebar widgets above
        try:
            wc = st.session_state.word_count if st.session_state.word_count > 0 else None
            effective_style = st.session_state.generated_style_guide or style_guide
            fw_instr = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""

            col_prog, _ = st.columns([2, 1])
            with col_prog:
                progress = st.progress(0, text="מתחיל...")
            _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)

            # Resolve writing style — auto mode calls Claude to pick the best fit
            if st.session_state.preset_style == "auto":
                progress.progress(5, text="🤖 בוחר סגנון כתיבה מתאים...")
                _auto_key, _auto_expl = generator.select_best_style(effective_category, effective_idea)
                preset_instr = PRESET_STYLES[_auto_key]["prompt_instruction"]
                st.session_state.auto_chosen_style = _auto_key
                st.session_state.style_choice_explanation = _auto_expl
            elif st.session_state.preset_style != "none":
                preset_instr = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"]
                st.session_state.auto_chosen_style = ""
                st.session_state.style_choice_explanation = ""
            else:
                preset_instr = ""
                st.session_state.auto_chosen_style = ""
                st.session_state.style_choice_explanation = ""

            _combined_notes = "\n".join(filter(None, [
                st.session_state.post_notes,
                f"הוראות ליישום הסגנון:\n{st.session_state.style_usage_instructions}"
                if st.session_state.style_usage_instructions else ""
            ]))
            progress.progress(15, text="✍️ כותב פוסט...")
            try:
                st.session_state.post_text = generator.generate_post(
                    effective_style, effective_category, effective_idea,
                    language=st.session_state.language,
                    content_type=st.session_state.content_type,
                    word_count=wc,
                    preset_style_instruction=preset_instr,
                    marketing_framework=fw_instr,
                    post_notes=_combined_notes,
                )
            except Exception as e:
                st.error(f"שגיאה ביצירת פוסט: {e}")
                st.stop()

            if not st.session_state.get("_text_only"):
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
                    _extra_refs = [r["bytes"] for r in st.session_state.reference_images[1:] if r]
                    st.session_state.image_bytes = generator.generate_image(
                        face_source, scene,
                        aspect_ratio=_get_aspect_ratio(),
                        style_description=_this_gen_style,
                        add_text=st.session_state.add_text_to_image,
                        text_content=image_text,
                        extra_reference_images=_extra_refs or None,
                    )
                except Exception as e:
                    st.error(f"שגיאה ביצירת תמונה: {e}")
            else:
                st.session_state.image_bytes = None

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
                    "images": [st.session_state.image_bytes] if st.session_state.image_bytes else [],
                    "category": effective_category,
                    "idea": effective_idea,
                    "content_type": st.session_state.content_type,
                    "language": st.session_state.language,
                    "preset_style": PRESET_STYLES[st.session_state.preset_style]["hebrew_name"]
                                    if st.session_state.preset_style not in ("none", "auto")
                                    else (PRESET_STYLES[st.session_state.auto_chosen_style]["hebrew_name"]
                                          if st.session_state.auto_chosen_style else "ללא"),
                    "marketing_framework": st.session_state.marketing_framework,
                    "timestamp": int(time.time()),
                    "timestamp_str": time.strftime("%d/%m/%Y %H:%M"),
                }
                st.session_state.archive.append(archive_entry)
                st.session_state.current_archive_idx = len(st.session_state.archive) - 1
                if len(st.session_state.archive) > 20:
                    st.session_state.archive = st.session_state.archive[-20:]
                    st.session_state.current_archive_idx = len(st.session_state.archive) - 1
        finally:
            st.session_state.generating = False

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
            st.markdown('<div class="section-label" style="margin-top:1rem;">💬 הערות לשיפור</div>', unsafe_allow_html=True)
            _retry_fb = st.text_area(
                "", value=st.session_state.get("retry_feedback", ""),
                height=80, key="retry_feedback_input",
                placeholder="הוסיפו הנחיות, שינויים, או בקשות לפני לחיצה על נסה שוב...",
                label_visibility="collapsed",
            )
            if _retry_fb != st.session_state.retry_feedback:
                st.session_state.retry_feedback = _retry_fb

            # Auto style explanation box
            if st.session_state.get("style_choice_explanation") and st.session_state.get("auto_chosen_style"):
                _csname = PRESET_STYLES.get(st.session_state.auto_chosen_style, {}).get("hebrew_name", "")
                st.markdown(f"""
<div style="background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.25);
     border-radius:12px;padding:0.9rem 1.2rem;margin-top:0.8rem;direction:rtl;text-align:right;">
  <div style="font-size:0.8rem;font-weight:700;color:rgba(167,139,250,0.9);margin-bottom:0.4rem;">
      🤖 המערכת בחרה: {_csname}
  </div>
  <div style="font-size:0.85rem;color:rgba(255,255,255,0.75);line-height:1.6;">
      {st.session_state.style_choice_explanation}
  </div>
</div>""", unsafe_allow_html=True)

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
                            preset_instr = PRESET_STYLES[st.session_state.preset_style]["prompt_instruction"] if st.session_state.preset_style not in ("none", "auto") else ""
                            fw_instr = MARKETING_FRAMEWORKS[st.session_state.marketing_framework]["structure"] if st.session_state.marketing_framework != "none" else ""
                            _retry_combined_notes = "\n".join(filter(None, [
                                st.session_state.post_notes,
                                f"הוראות ליישום הסגנון:\n{st.session_state.style_usage_instructions}"
                                if st.session_state.style_usage_instructions else ""
                            ]))
                            st.session_state.post_text = generator.generate_post(
                                effective_style, _retry_category, _retry_idea,
                                language=st.session_state.language,
                                content_type=st.session_state.content_type,
                                word_count=wc,
                                preset_style_instruction=preset_instr,
                                marketing_framework=fw_instr,
                                post_notes=_retry_combined_notes,
                                retry_feedback=st.session_state.retry_feedback,
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
            # Previous image (kept after retry)
            if st.session_state.prev_image_bytes:
                st.markdown('<div class="section-label" style="margin-top:1.2rem; opacity:0.7;">🖼 תמונה קודמת</div>', unsafe_allow_html=True)
                st.image(st.session_state.prev_image_bytes, use_container_width=True)
                st.download_button(
                    "⬇ הורד תמונה קודמת", data=st.session_state.prev_image_bytes,
                    file_name=f"prev_{dl_name_img}", mime="image/png",
                    use_container_width=True, key="dl_prev_img",
                )
            st.markdown('<div class="section-label" style="margin-top:0.8rem;">💬 הערות לשיפור התמונה</div>', unsafe_allow_html=True)
            _img_fb = st.text_area(
                "", value=st.session_state.get("image_retry_feedback", ""),
                height=90, key="image_retry_feedback_input",
                placeholder="לדוגמה: שנה את הרקע לטבע, הוסף תאורה דרמטית, שנה את הסגנון לסקיצה...",
                label_visibility="collapsed",
            )
            if _img_fb != st.session_state.image_retry_feedback:
                st.session_state.image_retry_feedback = _img_fb
            if st.button("🔄 נסה שוב — תמונה בלבד", key="retry_image_btn", use_container_width=True):
                if not face_source:
                    st.error("יש להעלות תמונת ייחוס")
                elif not st.session_state.post_text:
                    st.error("יש לצור פוסט תחילה")
                else:
                    _stc.html(_tips_rotator_html(_font_b64), height=220, scrolling=False)
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
                            if st.session_state.image_retry_feedback:
                                scene = f"{scene}. Image correction request: {st.session_state.image_retry_feedback}"
                            _extra_refs = [r["bytes"] for r in st.session_state.reference_images[1:] if r]
                            # Keep the previous image before replacing
                            st.session_state.prev_image_bytes = st.session_state.image_bytes
                            new_img = generator.generate_image(
                                face_source, scene,
                                aspect_ratio=_get_aspect_ratio(),
                                # Always reuse the style from the original generation
                                style_description=st.session_state.last_image_style,
                                add_text=st.session_state.add_text_to_image,
                                text_content=image_text,
                                extra_reference_images=_extra_refs or None,
                            )
                            st.session_state.image_bytes = new_img
                            # Append to the current archive entry so all images are accessible
                            _arc_idx = st.session_state.get("current_archive_idx")
                            if _arc_idx is not None and 0 <= _arc_idx < len(st.session_state.archive):
                                st.session_state.archive[_arc_idx]["images"].append(new_img)
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
        st.markdown('<div class="section-label">📸 תמונות ייחוס (עד 3)</div>', unsafe_allow_html=True)
        st.caption("העלה עד 3 תמונות ייחוס: דמות/פנים, אובייקט/מוצר, רקע/סביבה")
        ref_labels = ["דמות / פנים", "אובייקט / מוצר", "רקע / סביבה"]
        _did_rerun = False
        for slot_idx, slot_label in enumerate(ref_labels):
            uploaded_ref = st.file_uploader(
                slot_label,
                type=["jpg", "jpeg", "png", "webp"],
                key=f"ref_img_{slot_idx}",
            )
            if uploaded_ref:
                _ref_bytes = uploaded_ref.read()
                _current = st.session_state.reference_images[slot_idx]
                if _current is None or _current.get("bytes") != _ref_bytes:
                    st.session_state.reference_images[slot_idx] = {"label": slot_label, "bytes": _ref_bytes}
                    if slot_idx == 0:
                        st.session_state.character_image_bytes = _ref_bytes
                    _did_rerun = True

            existing_ref = st.session_state.reference_images[slot_idx]
            if existing_ref:
                col_thumb, col_rm = st.columns([3, 1])
                with col_thumb:
                    st.image(existing_ref["bytes"], width=90)
                with col_rm:
                    if st.button("🗑", key=f"rm_ref_{slot_idx}", help=f"הסר {slot_label}"):
                        st.session_state.reference_images[slot_idx] = None
                        if slot_idx == 0:
                            st.session_state.character_image_bytes = None
                        _did_rerun = True

        if _did_rerun:
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

    col_enhance, col_apply = st.columns([1, 1])
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
                        _err = str(e)
                        if "529" in _err or "overload" in _err.lower():
                            st.warning("השרת עמוס כרגע — נסה שוב בעוד מספר שניות.")
                        else:
                            st.error("שגיאה בשיפור הסגנון. נסה שוב.")
            else:
                st.warning("כתוב תיאור סגנון תחילה")
    with col_apply:
        if st.button("✅ החל סגנון חופשי", key="apply_free_style_btn", use_container_width=True):
            if free_style_text.strip():
                st.session_state.style_description = free_style_text.strip()
                st.success("✓ הסגנון עודכן")

    col_save_vis, col_reset_vis = st.columns(2)
    with col_save_vis:
        if st.button("💾 שמור הגדרות תמונה", use_container_width=True, key="save_visual_settings_btn"):
            save_user_settings()
            st.success("✓ נשמר")
    with col_reset_vis:
        if st.button("🗑 איפוס סגנון תמונה", use_container_width=True, key="reset_visual_style_btn"):
            st.session_state.style_description = ""
            st.session_state.free_style_text = ""
            st.session_state.style_image_list = []
            st.session_state.last_image_style = ""
            st.session_state["free_style_input"] = ""
            st.rerun()


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
    col_domain, col_confirm = st.columns([5, 1])
    with col_domain:
        domain_input = st.text_input(
            "מהו התחום שלך?",
            placeholder="למשל: פיזיותרפיה, שיווק דיגיטלי, בישול בריא...",
            key="ideas_domain_input",
        )
    with col_confirm:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        confirm_domain_btn = st.button("אישור ◀", key="confirm_domain_btn", use_container_width=True)

    # Auto-generate on input commit (Enter/blur) OR explicit button click.
    # Two-rerun strategy: Rerun 1 → navigate to Ideas tab; Rerun 2 → run the API call.
    # This prevents Streamlit from flashing the Creation tab during the spinner.
    _should_generate = domain_input and (
        domain_input != st.session_state.get("_last_ideas_domain", "") or confirm_domain_btn
    )
    if _should_generate:
        # Store intent and reset state, then hand off to a dedicated rerun
        st.session_state["_last_ideas_domain"] = domain_input
        st.session_state["_pending_audience_gen"] = domain_input
        st.session_state.target_audiences = []
        st.session_state.ideas_table = {}
        st.session_state.ideas_tables_history = []
        st.session_state.ideas_table_idx = 0
        st.session_state["_jump_to_ideas"] = True  # nav trigger fires at top of next rerun
        st.rerun()

    # Rerun 2: tab is already active, now run the pending API call
    if st.session_state.get("_pending_audience_gen"):
        _pending_domain = st.session_state["_pending_audience_gen"]
        st.session_state["_pending_audience_gen"] = ""
        with st.spinner("מייצר קהלי יעד..."):
            try:
                audiences = generator.generate_target_audiences(
                    _pending_domain, st.session_state.language
                )
                st.session_state.target_audiences = audiences
            except Exception as e:
                st.error(f"שגיאה: {e}")

    if st.session_state.get("_pending_table_gen"):
        _ptg = st.session_state["_pending_table_gen"]
        st.session_state["_pending_table_gen"] = {}
        _spinner_msg = "מייצר עוד רעיונות..." if _ptg.get("mode") == "append" else "מייצר טבלת רעיונות..."
        with st.spinner(_spinner_msg):
            try:
                table = generator.generate_ideas_table(
                    _ptg["domain"], _ptg["audience"], st.session_state.language
                )
                st.session_state.ideas_table = table
                st.session_state.ideas_tables_history.append(table)
                st.session_state.ideas_table_idx = len(st.session_state.ideas_tables_history) - 1
            except Exception as e:
                st.error(f"שגיאה: {e}")
        st.session_state["_jump_to_ideas"] = True
        st.rerun()

    # ── שלב 2: בחירת קהל יעד ──
    if st.session_state.target_audiences:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">👥 סוג הקהל שלך</div>', unsafe_allow_html=True)

        # Checkboxes — two columns
        checked_audiences = []
        audience_list = st.session_state.target_audiences
        aud_col1, aud_col2 = st.columns(2)
        for idx, aud in enumerate(audience_list):
            col = aud_col1 if idx % 2 == 0 else aud_col2
            with col:
                if st.checkbox(aud, key=f"aud_cb_{idx}", on_change=_ideas_tab_action):
                    checked_audiences.append(aud)

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
                st.session_state["_pending_table_gen"] = {
                    "domain": domain_input,
                    "audience": ", ".join(final_audience_list),
                    "mode": "new",
                }
                st.session_state["_jump_to_ideas"] = True
                st.rerun()
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
        _cat_meta = {
            "מוטיבציות":                  ("🎯", "rgba(52,211,153,0.15)",  "rgba(52,211,153,0.35)"),
            "חששות":                      ("😟", "rgba(239,68,68,0.1)",    "rgba(239,68,68,0.3)"),
            "דברים שאנשים לא יודעים":     ("💡", "rgba(251,191,36,0.1)",   "rgba(251,191,36,0.3)"),
        }
        for category, ideas_list in current_table.items():
            emoji, bg_tint, border_tint = _cat_meta.get(category, ("📌", "rgba(255,255,255,0.03)", "rgba(255,255,255,0.07)"))
            ideas_html = "".join(
                f'<div style="padding:0.45rem 0; border-bottom:1px solid rgba(255,255,255,0.06); color:rgba(255,255,255,0.88); font-size:1rem; line-height:1.65;">'
                f'<span style="color:rgba(167,139,250,0.8); font-weight:700; margin-left:0.5rem;">{i}.</span> {idea}'
                f'</div>'
                for i, idea in enumerate(ideas_list, 1)
            )
            st.markdown(f"""
<div style="background:{bg_tint}; border:1px solid {border_tint};
     border-radius:16px; padding:1.2rem 1.5rem; margin-bottom:1rem; direction:rtl; text-align:right;">
  <div style="font-size:1.1rem; font-weight:800; color:white; margin-bottom:0.9rem; letter-spacing:0.01em;">
      {emoji}&nbsp; {category}
  </div>
  {ideas_html}
</div>""", unsafe_allow_html=True)

        # Action buttons — row 1: download DOCX (full width)
        docx_bytes = data_loader.create_ideas_docx(current_table)
        st.download_button(
            "⬇ הורד DOCX", data=docx_bytes,
            file_name=f"ideas_table_{idx+1}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
            key=f"dl_ideas_{idx}",
        )
        # Row 2: equal-width Load + More
        col_load, col_more = st.columns([1, 1])
        with col_load:
            if st.button("📥 טען לאפליקציה", key=f"load_ideas_btn_{idx}", use_container_width=True):
                st.session_state.post_ideas = current_table
                st.rerun()
        with col_more:
            if st.button("➕ צור עוד 30 רעיונות", key="more_ideas_btn", use_container_width=True):
                if domain_input and (final_audience_list if st.session_state.target_audiences else domain_input):
                    st.session_state["_pending_table_gen"] = {
                        "domain": domain_input,
                        "audience": ", ".join(final_audience_list) if st.session_state.target_audiences else "",
                        "mode": "append",
                    }
                    st.session_state["_jump_to_ideas"] = True
                    st.rerun()
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
        # Build styled summary with bold+white sub-headers
        _summary_html = ""
        for _line in preset_data.get('summary', preset_data['description']).splitlines():
            if _line.startswith("### "):
                _summary_html += f'<div style="font-weight:700;color:rgba(255,255,255,0.95);font-size:0.9rem;margin-top:0.7rem;margin-bottom:0.2rem;">{_line[4:]}</div>'
            elif _line.startswith("## "):
                _summary_html += f'<div style="font-weight:700;color:rgba(167,139,250,0.9);font-size:0.92rem;margin-top:0.9rem;margin-bottom:0.2rem;">{_line[3:]}</div>'
            elif _line.startswith("# "):
                _summary_html += f'<div style="font-weight:700;color:white;font-size:0.95rem;margin-bottom:0.3rem;">{_line[2:]}</div>'
            elif _line.startswith("- "):
                _summary_html += f'<div style="color:rgba(255,255,255,0.7);font-size:0.88rem;line-height:1.6;padding-right:0.5rem;">• {_line[2:]}</div>'
            elif _line.strip():
                _summary_html += f'<div style="color:rgba(255,255,255,0.65);font-size:0.88rem;line-height:1.6;">{_line}</div>'
        st.markdown(f"""
        <div class="glass-card" style="direction:rtl;text-align:right;">
            <div style="font-size:1.05rem;font-weight:700;color:white;margin-bottom:0.3rem;">{preset_data['hebrew_name']} — {preset_data['name']}</div>
            <div style="color:rgba(167,139,250,0.85);font-size:0.9rem;margin-bottom:0.8rem;">{preset_data['description']}</div>
            {_summary_html}
        </div>
        """, unsafe_allow_html=True)
        if st.button("✅ החל סגנון זה", key="apply_preset_from_tab4"):
            st.session_state.preset_style = selected_preset_key
            st.session_state.style_mode = None  # close personal style generator
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
        if st.session_state.preset_style not in ("none", "auto"):
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

    if "style_mode" not in st.session_state:
        st.session_state.style_mode = None  # None | "analyze" | "upload"

    # Exclusion: if preset selected, hide personal generator
    if st.session_state.preset_style != "none":
        st.info("⚠️ סגנון מוכן פעיל — איפוס הסגנון יאפשר שימוש במחולל האישי")
    else:
        # ── בחירת מסלול ──
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
            st.info("העלה 4-5 תכנים שכתבת (פוסטים, מאמרים, בלוגים). ככל שהדוגמאות דומות יותר — הניתוח מדויק יותר.")

            # Paste area with Next/Finish accumulation
            pasted_text = st.text_area(
                "הדבק תוכן לדוגמה",
                height=180,
                key=f"pasted_writing_sample_{st.session_state.get('pasted_sample_key', 0)}",
                placeholder="הדבק פוסט, מאמר, או כל טקסט שכתבת...",
            )

            col_next, col_buf_info = st.columns([1, 1])
            with col_next:
                if st.button("הבא ←", key="style_next_btn", use_container_width=True):
                    if pasted_text.strip():
                        st.session_state.style_text_buffer.append(pasted_text.strip())
                        st.session_state.pasted_sample_key = st.session_state.get("pasted_sample_key", 0) + 1
                        st.rerun()
            with col_buf_info:
                buf_count = len(st.session_state.style_text_buffer)
                if buf_count > 0:
                    st.caption(f"✓ {buf_count} קטע{'ים' if buf_count != 1 else ''} נשמר{'ו' if buf_count != 1 else ''}")

            col_upload_s, col_clear_buf = st.columns([2, 1])
            with col_upload_s:
                uploaded_samples = st.file_uploader(
                    "או העלה קבצי טקסט (TXT / DOCX / PDF)",
                    type=["txt", "docx", "pdf"],
                    accept_multiple_files=True,
                    key="writing_samples_upload",
                )
            with col_clear_buf:
                if st.session_state.style_text_buffer:
                    if st.button("🗑 מחק זיכרון והתחל מחדש", key="clear_style_buf_btn", use_container_width=True):
                        st.session_state.style_text_buffer = []
                        st.rerun()

            # Collect file samples
            uploaded_file_samples = []
            if uploaded_samples:
                for uf in uploaded_samples:
                    try:
                        if uf.name.endswith(".txt"):
                            uploaded_file_samples.append(uf.read().decode("utf-8", errors="replace"))
                        elif uf.name.endswith(".docx"):
                            from docx import Document as _Doc
                            import io as _io
                            doc_obj = _Doc(_io.BytesIO(uf.read()))
                            text = "\n".join(p.text for p in doc_obj.paragraphs if p.text.strip())
                            uploaded_file_samples.append(text)
                        elif uf.name.endswith(".pdf"):
                            import io as _io
                            import pypdf as _pypdf
                            reader = _pypdf.PdfReader(_io.BytesIO(uf.read()))
                            text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                            if text:
                                uploaded_file_samples.append(text)
                    except Exception:
                        pass

            # Merge buffer + current paste + files
            all_samples = st.session_state.style_text_buffer + uploaded_file_samples
            if pasted_text.strip():
                all_samples = all_samples + [pasted_text.strip()]

            n = len(all_samples)
            if n > 0:
                color = "#34d399" if n >= 4 else "#f59e0b"
                st.markdown(
                    f'<div style="color:{color}; font-size:0.85rem; margin-bottom:0.5rem;">'
                    f'{"✓" if n >= 4 else "⚠"} {n} קטעים {"— מספיק לניתוח מדויק" if n >= 4 else "— מומלץ לפחות 4"}'
                    f"</div>",
                    unsafe_allow_html=True,
                )

                _analyze_label = "🔬 נתח וצור מדריך סגנון" if not st.session_state.style_text_buffer else "✅ סיום — נתח את כל הקטעים"
                if st.button(_analyze_label, key="analyze_writing_btn", use_container_width=True):
                    with st.spinner("מנתח סגנון כתיבה (תחביר, אוצר מילים, טון, דימויים, קצב)..."):
                        try:
                            guide = generator.generate_writing_style(all_samples)
                            st.session_state.generated_style_guide = guide
                            st.session_state.style_text_buffer = []
                            import re as _re
                            _usage_lines = [l for l in guide.splitlines()
                                            if _re.match(r'^[-•\d\*]', l.strip()) and len(l.strip()) > 10]
                            st.session_state.style_usage_instructions = "\n".join(_usage_lines[:15])
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

    # ── תצוגת מדריך סגנון (משותף לכל המסלולים) ──
    if st.session_state.generated_style_guide:
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">📖 מדריך סגנון כתיבה</div>', unsafe_allow_html=True)

        edited_guide = st.text_area(
            "", value=st.session_state.generated_style_guide,
            height=420, key="style_guide_editor", label_visibility="collapsed",
        )
        if edited_guide != st.session_state.generated_style_guide:
            st.session_state.generated_style_guide = edited_guide

        st.markdown('<div class="section-label" style="margin-top:1rem;">📋 הוראות שימוש לסגנון</div>', unsafe_allow_html=True)
        st.caption("כיצד המודל צריך ליישם את הסגנון — ניתן לערוך")
        _usage_instr_val = st.text_area(
            "", value=st.session_state.get("style_usage_instructions", ""),
            height=150, key="style_usage_instr_editor", label_visibility="collapsed",
            placeholder="לדוגמה: כתוב בגוף ראשון, משפטים קצרים, פתח בשאלה, הימנע מז'רגון...",
        )
        if _usage_instr_val != st.session_state.get("style_usage_instructions", ""):
            st.session_state.style_usage_instructions = _usage_instr_val

        col_apply, col_dl_style, col_clear = st.columns(3)
        with col_apply:
            if st.button("✅ החל סגנון", key="apply_style_btn", use_container_width=True):
                st.session_state.style_guide = st.session_state.generated_style_guide
                st.session_state.style_bytes = st.session_state.generated_style_guide.encode("utf-8")
                st.session_state.preset_style = "none"
                st.session_state.style_upload_key += 1
                save_user_settings()
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
                st.session_state.style_usage_instructions = ""
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

        # Check if we're viewing a specific entry
        view_idx = st.session_state.get("archive_view_idx", None)
        if view_idx is not None and 0 <= view_idx < len(archive):
            entry = archive[view_idx]
            safe_cat = _safe_filename(entry["category"])
            safe_idea = _safe_filename(entry["idea"])
            if st.button("← חזור לגלריה", key="arc_back_btn"):
                st.session_state.archive_view_idx = None
                st.rerun()
            st.markdown(f'<div style="color:rgba(255,255,255,0.5);font-size:0.8rem;margin-bottom:1rem;direction:rtl;">[{entry["timestamp_str"]}] {entry["category"]} — {entry["idea"][:80]}</div>', unsafe_allow_html=True)
            col_arc_post, col_arc_img = st.columns([1, 1], gap="large")
            with col_arc_post:
                st.markdown('<div class="section-label">📝 פוסט</div>', unsafe_allow_html=True)
                st.text_area("", value=entry["post_text"], height=400, key=f"arc_view_post_{view_idx}", label_visibility="collapsed")
                meta = f"{entry['content_type']} · {entry['language']} · {entry['preset_style']} · {entry['marketing_framework']}"
                st.caption(meta)
                st.download_button("⬇ הורד טקסט", data=entry["post_text"].encode("utf-8"),
                    file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}.txt",
                    mime="text/plain", use_container_width=True, key=f"arc_dl_post_view_{view_idx}")
            with col_arc_img:
                st.markdown('<div class="section-label">🖼 תמונות</div>', unsafe_allow_html=True)
                _view_imgs = entry.get("images") or ([entry["image_bytes"]] if entry.get("image_bytes") else [])
                for img_i, img_b in enumerate(_view_imgs):
                    if len(_view_imgs) > 1:
                        st.caption(f"תמונה {img_i + 1}")
                    st.image(img_b, use_container_width=True)
                    st.download_button(
                        f"⬇ הורד תמונה {img_i+1}" if len(_view_imgs) > 1 else "⬇ הורד תמונה",
                        data=img_b,
                        file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}_img{img_i+1}.png",
                        mime="image/png", use_container_width=True,
                        key=f"arc_dl_img_view_{view_idx}_{img_i}"
                    )
        else:
            # Gallery card grid — 3 columns
            cols = st.columns(3)
            for i, entry in enumerate(reversed(archive)):
                real_idx = len(archive) - 1 - i
                safe_cat = _safe_filename(entry["category"])
                safe_idea = _safe_filename(entry["idea"])
                preview_text = entry["post_text"][:130].replace("\n", " ")
                with cols[i % 3]:
                    _idea_short = entry['idea'][:50] + ("…" if len(entry['idea']) > 50 else "")
                    st.markdown(f"""
<div style="border:1px solid rgba(255,255,255,0.08);border-radius:14px;padding:1rem;
    margin-bottom:0.6rem;background:rgba(255,255,255,0.03);direction:rtl;text-align:right;">
    <div style="font-size:0.72rem;color:rgba(255,255,255,0.35);margin-bottom:0.3rem;">{entry.get('timestamp_str','')}</div>
    <div style="font-size:0.8rem;font-weight:700;color:rgba(255,255,255,0.9);margin-bottom:0.2rem;">{entry['category']}</div>
    <div style="font-size:0.78rem;color:rgba(167,139,250,0.85);margin-bottom:0.4rem;">{_idea_short}</div>
    <div style="font-size:0.78rem;color:rgba(255,255,255,0.5);line-height:1.5;">{preview_text}…</div>
</div>""", unsafe_allow_html=True)
                    # Buttons row
                    _imgs = entry.get("images") or ([entry["image_bytes"]] if entry.get("image_bytes") else [])
                    _n_imgs = len(_imgs)
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        if st.button("👁 צפה", key=f"arc_view_{real_idx}", use_container_width=True):
                            st.session_state.archive_view_idx = real_idx
                            st.rerun()
                    with c2:
                        st.download_button("📄 טקסט", data=entry["post_text"].encode("utf-8"),
                            file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}.txt",
                            mime="text/plain", use_container_width=True, key=f"arc_dl_txt_{real_idx}")
                    for img_i, img_b in enumerate(_imgs):
                        label = f"🖼 תמונה {img_i+1}" if _n_imgs > 1 else "🖼 תמונה"
                        st.download_button(label, data=img_b,
                            file_name=f"{safe_cat}_{safe_idea}_{entry['timestamp']}_img{img_i+1}.png",
                            mime="image/png", use_container_width=True,
                            key=f"arc_dl_img_{real_idx}_{img_i}")
                    if not _imgs:
                        st.button("🖼", disabled=True, use_container_width=True, key=f"arc_no_img_{real_idx}")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 6 — הוראות שימוש
# ═══════════════════════════════════════════════════════════════════════════════
with tab_guide:
    st.markdown("""
<div style="direction:rtl; text-align:right; max-width:800px; margin:0 auto;">

<div style="font-size:1.6rem; font-weight:700; color:white; margin-bottom:1.5rem;">
    📖 מדריך שימוש — מכונת התוכן
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 1 — הגדרת הבסיס</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        הגדרות המותג נמצאות בתפריט הצד, בלשוניות האקורדיון.<br>
        מלאו את שם המותג, הדומיין והתחום המקצועי.<br><br>
        <strong style="color:rgba(255,255,255,0.95);">מבנה תפריט הצד:</strong>
        <ul style="margin-top:0.5rem;padding-right:1.2rem;">
            <li><strong style="color:rgba(255,255,255,0.9);">💡 רעיונות ובחירת תוכן</strong> — הכניסו רעיון לפוסט, בחרו מהרשימה, או העלו תמונות ייחוס</li>
            <li><strong style="color:rgba(255,255,255,0.9);">הערות מיוחדות</strong> — הוסיפו הנחיות לפוסט ולתמונה (תמיד גלויות)</li>
            <li><strong style="color:rgba(255,255,255,0.9);">✦ צור פוסט + תמונה</strong> — כפתור הגנרציה הראשי</li>
            <li><strong style="color:rgba(255,255,255,0.9);">סגנון כתיבה / מודל שיווקי / הגדרות פוסט</strong> — אקורדיונים נפתחים לפי צורך</li>
        </ul>
    </div>
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 2 — סגנון כתיבה</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        בלשונית <strong style="color:rgba(255,255,255,0.95);">סגנון כתיבה</strong> תוכלו:
        <ul style="margin-top:0.5rem;padding-right:1.2rem;">
            <li>לבחור סגנון מוכן מתוך 10 הסגנונות</li>
            <li>לנתח סגנון אישי על ידי הדבקת קטעי טקסט (כפתור "הבא ←" לכל קטע, "סיום" לניתוח)</li>
            <li>לטעון קובץ סגנון שמור (DOCX / TXT)</li>
            <li>לשפר את הסגנון שנוצר בלחיצה על ✨ שפר את הסגנון שלי</li>
        </ul>
    </div>
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 3 — הגדרות תמונה</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        בלשונית <strong style="color:rgba(255,255,255,0.95);">הגדרות תמונה</strong> הגדירו:
        <ul style="margin-top:0.5rem;padding-right:1.2rem;">
            <li><strong style="color:rgba(255,255,255,0.9);">דמות / פנים</strong> — תמונת ייחוס לשמירת זהות (חובה לייצור תמונה)</li>
            <li><strong style="color:rgba(255,255,255,0.9);">אובייקט / מוצר</strong> — תמונת מוצר שתשולב בתמונה</li>
            <li><strong style="color:rgba(255,255,255,0.9);">רקע / סביבה</strong> — תמונת רקע לסגנון ויזואלי</li>
            <li>תיאור סגנון טקסטואלי + כפתור שיפור אוטומטי</li>
        </ul>
    </div>
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 4 — יצירת פוסט</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        בתפריט הצד (אקורדיון 💡 רעיונות), כתבו את נושא הפוסט בשדה "רעיון לפוסט".<br>
        הוסיפו הערות מיוחדות אם יש (טון, אורך, כיוון ספציפי).<br>
        לחצו על <strong style="color:rgba(255,255,255,0.95);">✦ צור פוסט + תמונה</strong> — המערכת תייצר פוסט ותמונה תואמת.
    </div>
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 5 — מחולל רעיונות</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        בלשונית <strong style="color:rgba(255,255,255,0.95);">מחולל רעיונות</strong> תוכלו לקבל השראה לנושאי פוסטים.<br>
        הגדירו תחום, בחרו קהל יעד ולחצו "צור טבלת רעיונות".<br>
        לחיצה על <strong style="color:rgba(255,255,255,0.95);">📥 טען לאפליקציה</strong> תעביר את הרעיונות לתפריט הצד.
    </div>
</div>

<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">שלב 6 — ארכיון</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:1.9;">
        כל פוסט שנוצר נשמר אוטומטית בלשונית <strong style="color:rgba(255,255,255,0.95);">ארכיון</strong>.<br>
        ניתן לצפות בכל פוסט בלחיצה על "👁 צפה" ולהוריד את הטקסט בלחיצה על "⬇ הורד".
    </div>
</div>

<div style="background:rgba(167,139,250,0.06);border:1px solid rgba(167,139,250,0.2);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.2rem;">
    <div style="font-size:0.85rem;font-weight:800;letter-spacing:0.12em;color:white;text-transform:uppercase;margin-bottom:0.8rem;">💡 טיפים</div>
    <div style="color:rgba(255,255,255,0.8);font-size:0.95rem;line-height:2.0;">
        • בחרו <strong style="color:rgba(255,255,255,0.95);">מודל כתיבה שיווקית</strong> (AIDA, PAS וכו') כדי להוסיף לפוסט כתיבה שיווקית ברורה יותר<br>
        • לחצו <strong style="color:rgba(255,255,255,0.95);">💾 שמור</strong> בכל קטגוריה בתפריט — הגדרות נשמרות לביקור הבא<br>
        • ניתן לשפר תיאור סגנון ויזואלי בלחיצה על <strong style="color:rgba(255,255,255,0.95);">✨ שפר סגנון</strong><br>
        • הכפתור "🔄 נסה שוב" מאפשר לרענן רק את הפוסט או רק את התמונה בנפרד
    </div>
</div>

</div>
""", unsafe_allow_html=True)
