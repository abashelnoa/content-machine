"""
generator.py — יצירת פוסט טקסט + תמונה
"""
import base64
import io
import json
import os
import re
import time
from pathlib import Path

import anthropic
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_MODEL = "claude-sonnet-4-6"
IMAGEN_MODEL = "gemini-3.1-flash-image-preview"

CONTENT_TYPES = {
    "LinkedIn":    {"label": "💼 LinkedIn",   "words": "150–300"},
    "Instagram":   {"label": "📷 Instagram",  "words": "50–150"},
    "Facebook":    {"label": "📘 Facebook",   "words": "100–250"},
    "X (Twitter)": {"label": "𝕏 Twitter/X",  "words": "50–100"},
    "Blog":        {"label": "📝 בלוג",        "words": "800–1500"},
    "Article":     {"label": "📰 מאמר",        "words": "500–1000"},
}

LANGUAGES = ["עברית", "English", "Español", "Français", "العربية", "Deutsch"]

ASPECT_RATIOS = {
    "מרובע (1:1)":  "1:1",
    "רחב (16:9)":   "16:9",
    "לאורך (9:16)": "9:16",
    "2:3 לאורך":    "2:3",
    "3:2 לרוחב":    "3:2",
}

STYLE_WRAPPER = (
    "Generate a professional portrait photo of this exact person. {scene}. "
    "Cinematic lighting, dark teal and electric blue color palette, "
    "futuristic AI/tech atmosphere, bokeh background with subtle digital patterns, "
    "photorealistic, studio quality, sharp focus on face. "
    "Keep the person's exact facial features, age, and appearance."
    "{aspect_ratio_instruction}"
    "{style_instruction}"
    "{text_instruction}"
)


def generate_post(style_guide: str, category: str, idea: str,
                  language: str = "עברית",
                  content_type: str = "LinkedIn",
                  word_count: int | None = None) -> str:
    """מייצר פוסט בשפה ובסגנון הנבחרים."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    ct_info = CONTENT_TYPES.get(content_type, {})
    word_range = ct_info.get("words", "150–300")
    word_instruction = f"{word_count}" if word_count else word_range

    prompt = f"""You are a professional content writer creating a {content_type} post.

Style guide:
{style_guide}

Category: {category}
Post idea: {idea}

Instructions:
- Write in {language}
- Target length: approximately {word_instruction} words
- Platform: {content_type}
- Follow the style guide closely

Structure:
1. Personal short story from daily life (concrete situation, dialogue, memory)
2. Emotional moment — confusion, doubt, small surprise
3. Natural transition to professional insight (psychology, behavior, AI)
4. Sharp closing sentence the reader takes with them

Rules:
- Short paragraphs (2-4 lines), lots of white space
- Rhetorical questions
- Don't preach — let the insight grow from the story
- Rich but not formal language
- Return only the post text, no titles or explanations"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_image_prompt(post_text: str) -> str:
    """מייצר prompt באנגלית לתמונה."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Based on the following post, write ONE sentence describing a scene for a portrait photo.

Rules:
- Middle-aged professional person as subject
- Background/scene should metaphorically represent the post's theme
- Style: cinematic, dark teal and electric blue palette, futuristic AI/tech atmosphere, photorealistic
- Under 25 words. Return only the scene description in English, nothing else.

Examples:
- "sitting at a glowing laptop with holographic data streams floating in background"
- "standing confidently before a large digital dashboard with flowing light patterns"

Post:
{post_text}"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_text_for_image(post_text: str, language: str = "עברית") -> str:
    """מייצר ביטוי קצר (3-6 מילים) לשילוב בתמונה."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Based on the following post, create a short phrase of 3-6 words to overlay on the image.

Rules:
- Language: {language}
- Must capture the post's core message
- Short, punchy, memorable
- Return ONLY the phrase, nothing else

Post:
{post_text}"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_image(face_image, scene_description: str,
                   aspect_ratio: str = "1:1",
                   style_description: str = "",
                   add_text: bool = False,
                   text_content: str = "") -> bytes:
    """
    מייצר תמונה עם שמירת זהות דרך Google Gemini.
    face_image: Path | str | bytes
    """
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    aspect_ratio_instruction = (
        f" Generate with {aspect_ratio} aspect ratio." if aspect_ratio != "1:1" else ""
    )
    style_instruction = f" Additional style: {style_description}." if style_description else ""
    text_instruction = (
        f" Incorporate this text creatively into the image design: '{text_content}'."
        if add_text and text_content else ""
    )

    image_prompt = STYLE_WRAPPER.format(
        scene=scene_description,
        aspect_ratio_instruction=aspect_ratio_instruction,
        style_instruction=style_instruction,
        text_instruction=text_instruction,
    )

    if isinstance(face_image, bytes):
        face_img = Image.open(io.BytesIO(face_image))
    else:
        face_img = Image.open(face_image)

    response = client.models.generate_content(
        model=IMAGEN_MODEL,
        contents=[image_prompt, face_img],
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            return part.inline_data.data

    raise RuntimeError("לא התקבלה תמונה מהמודל")


def _detect_media_type(img_bytes: bytes) -> str:
    if img_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if img_bytes[:2] == b'\xff\xd8':
        return "image/jpeg"
    if b'WEBP' in img_bytes[:12]:
        return "image/webp"
    return "image/jpeg"


def _analyze_batch(client, images: list[bytes], batch_num: int, total_batches: int) -> str:
    """מנתח קבוצה אחת של תמונות."""
    content = []
    for i, img_bytes in enumerate(images, 1):
        img_b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        content.append({"type": "text", "text": f"תמונה {i}:"})
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": _detect_media_type(img_bytes),
                "data": img_b64,
            },
        })

    content.append({
        "type": "text",
        "text": """אתה אמן ומנתח ויזואלי מומחה עם עין חדה לפרטים אסתטיים.

נתח את התמונות האלה בעיני אמן מקצועי וכתב ניתוח מעמיק הכולל:

1. **פלטת צבעים** — צבעים דומיננטיים, טמפרטורת צבע (חמה/קרה/ניטרלית), רוויה, ניגודיות, האם יש צבע signature בולט
2. **תאורה** — סוג התאורה (סטודיו, טבעית, דרמטית, רכה, נקודתית), כיוון האור, צללים, הייליטים, bokeh
3. **קומפוזיציה** — כלל השלישים, עומק שדה, זווית צילום, מרחק מהנושא, שימוש ברקע
4. **אווירה ומצב רוח** — התחושה הכללית שהתמונות מעבירות (מסתורי, מקצועי, חם, עתידני, ארטיסטי)
5. **סגנון אמנותי** — ציאנמטי, פוטוריאליסטי, עיצובי, דוקומנטרי, פנטסטי וכו'
6. **מרקם ואיכות** — חדות, גרין, גלואו, עיבוד צבע (LUT/grading), פרטי טקסצ'ר
7. **אלמנטים חוזרים** — מה מופיע שוב ושוב ויוצר זהות ויזואלית עקבית

בסוף תן **סיכום בשורה אחת** שניתן להשתמש בו ישירות כ-style prompt לגנרציית תמונה.
כתב באנגלית — הסיכום חייב להיות באנגלית לשימוש ב-prompt.""",
    })

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text.strip()


def analyze_style_images(image_bytes_list: list[bytes]) -> str:
    """
    מנתח תמונות סגנון בקבוצות (מקסימום 4 בכל קריאה) ומאחד את הניתוחים.
    מחזיר תיאור סגנון מקיף מעיני אמן.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    BATCH_SIZE = 3
    batches = [
        image_bytes_list[i:i + BATCH_SIZE]
        for i in range(0, len(image_bytes_list), BATCH_SIZE)
    ]

    batch_analyses = []
    for idx, batch in enumerate(batches, 1):
        analysis = _analyze_batch(client, batch, idx, len(batches))
        batch_analyses.append(analysis)

    # אם יש רק קבוצה אחת — מחזיר ישירות
    if len(batch_analyses) == 1:
        return batch_analyses[0]

    # מאחד את כל הניתוחים לדוח אחד
    combined = "\n\n---\n\n".join(
        f"ניתוח קבוצה {i}:\n{a}" for i, a in enumerate(batch_analyses, 1)
    )
    merge_message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1200,
        messages=[{
            "role": "user",
            "content": f"""להלן ניתוחים של קבוצות תמונות מאותה סדרה.
אחד אותם לדוח סגנון אחד מקיף ועקבי, תוך הדגשת האלמנטים החוזרים בכל הקבוצות.
שמור על אותה מבנה (פלטת צבעים, תאורה, קומפוזיציה, אווירה, סגנון, מרקם, אלמנטים חוזרים + סיכום באנגלית).

{combined}""",
        }],
    )
    return merge_message.content[0].text.strip()


def generate_target_audiences(domain: str, language: str = "עברית") -> list[str]:
    """מייצר 10 קהלי יעד מתאימים לתחום."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Generate 10 specific target audiences for content in the domain of: {domain}

Output language: {language}

Rules:
- Each audience should be specific and actionable
- Think about different demographics, roles, pain points
- Return ONLY a JSON array of 10 strings, nothing else

Format: ["audience 1", "audience 2", ...]"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return []


def generate_ideas_table(domain: str, audience: str, language: str = "עברית") -> dict:
    """
    מייצר טבלת רעיונות: 10 מוטיבציות, 10 חששות, 10 דברים שאנשים לא יודעים.
    מחזיר dict: {"מוטיבציות": [...], "חששות": [...], "דברים שאנשים לא יודעים": [...]}
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""אני רוצה שתהיה בתפקיד של מומחה לכתיבת תוכן עבור רשתות חברתיות וכתיבה באופן כללי כגון פוסטים, בלוגים, מאמרים וכו'. אני עוסק בתחום {domain}.

אני רוצה רעיונות שיעניינו את הקהל שלי שהוא {audience}.

אני רוצה שתיתן לי עשר מוטיבציות, עשר חששות, ועשרה דברים שאנשים שאינם מהתחום לא יודעים על התחום הספציפי שלי.

החזר את המידע כ-JSON בלבד, ללא טקסט נוסף, בפורמט הבא:
{{
  "מוטיבציות": ["רעיון 1", "רעיון 2", "רעיון 3", "רעיון 4", "רעיון 5", "רעיון 6", "רעיון 7", "רעיון 8", "רעיון 9", "רעיון 10"],
  "חששות": ["רעיון 1", "רעיון 2", "רעיון 3", "רעיון 4", "רעיון 5", "רעיון 6", "רעיון 7", "רעיון 8", "רעיון 9", "רעיון 10"],
  "דברים שאנשים לא יודעים": ["רעיון 1", "רעיון 2", "רעיון 3", "רעיון 4", "רעיון 5", "רעיון 6", "רעיון 7", "רעיון 8", "רעיון 9", "רעיון 10"]
}}

שפת הפלט: {language}"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


def generate_writing_style(samples: list[str]) -> str:
    """Claude מנתח דוגמאות כתיבה → מחזיר מדריך סגנון מלא לפי 5 קטגוריות."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    combined = "\n\n---\n\n".join(samples)

    prompt = f"""אתה מומחה לשפות- לכתיבה, דקדוק ותחביר.

אני רוצה שתנתח את סגנון הכתיבה שלי בקטגוריות הבאות:
- תחביר ודקדוק
- אוצר מילים ודיקציה
- טון וקול
- דימויים ושפה פיגורטיבית
- קצב וזרימה

להלן דוגמאות הכתיבה שלי:

{combined}

---

לאחר שסיימת לקרוא את הדוגמאות שאני נותן לך תן לי סט הוראות מפורט שאני יכול להשתמש בו כדי לכתוב בדיוק באותו טון, סגנון כתיבה, רמת קריאה והגשה.

בנה את הדוח כך:
1. פתח בסיכום קצר של הסגנון הכללי (3-4 משפטים)
2. נתח כל קטגוריה בנפרד עם דוגמאות מהטקסט
3. סיים בסט הוראות מפורט — רשימת כללים ברורה שניתן לפעול לפיה"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def save_outputs(post_text: str, image_bytes: bytes, outputs_dir: Path) -> tuple[Path, Path]:
    """שומר פוסט ותמונה לתיקיית outputs."""
    timestamp = int(time.time())
    post_path = outputs_dir / f"post_{timestamp}.txt"
    image_path = outputs_dir / f"image_{timestamp}.png"

    post_path.write_text(post_text, encoding="utf-8")
    image_path.write_bytes(image_bytes)

    return post_path, image_path
