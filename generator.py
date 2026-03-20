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

LANGUAGES = ["עברית", "English", "Español", "Français", "العربية", "Deutsch", "Русский"]

def _parse_summaries(summary_path: Path) -> dict:
    """Extract each style's summary block from the summary file. Returns {hebrew_name: summary_text}."""
    try:
        content = summary_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    # Split on numbered headings like "## 1. " ... "## 2. "
    sections = re.split(r'\n## \d+\.', content)
    result = {}
    for section in sections[1:]:
        lines = section.strip().splitlines()
        first_line = lines[0].strip()
        # Hebrew name is before the opening parenthesis, e.g. "המספר סיפור (Story-driven)"
        m = re.match(r'^(.+?)\s*\(', first_line)
        if m:
            hebrew_name = m.group(1).strip()
            result[hebrew_name] = section.strip()
    return result


def _load_preset_styles() -> dict:
    """Loads writing styles from the '10 writing styles' folder."""
    styles_dir = Path(__file__).parent / "10 writing styles"

    # (key, filename_hebrew, english_name, summary_lookup_key)
    # summary_lookup_key is the name as it appears in the summary file (may differ from filename)
    STYLE_META = [
        ("story_driven",      "המספר סיפור",         "Story-driven Authority", None),
        ("myth_breaker",      "המפצח מיתוסים",        "Myth Breaker",           None),
        ("action_driver",     "המפעיל לפעולה",        "Action Driver",          None),
        ("simple_explainer",  "המסביר הפשוט",         "Complex → Simple",       None),
        ("thought_provoker",  "הפרובוקטור החכם",      "Thought Provoker",       None),
        ("reflection",        "המראה",                "Reflection Writer",      None),
        ("proof_driven",      "המוכיח",               "Proof-driven",           None),
        ("framework_builder", "המבנה",                "Framework Builder",      None),
        ("twist_story",       "סיפור עם טוויסט",      "Expectation Breaker",    "הסיפור עם הטוויסט"),
        ("smart_sarcasm",     "הומור סרקסטי חכם",     "Smart Sarcasm",          None),
    ]

    summaries = _parse_summaries(styles_dir / "תקציר 10 סגנונות כתיבה.txt")

    result = {}
    for key, hebrew_name, english_name, summary_key in STYLE_META:
        # Full detailed instructions used for generation
        file_path = styles_dir / f"{hebrew_name}.txt"
        try:
            instruction = file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            instruction = f"Write in the style of '{hebrew_name}'."
        # Brief summary shown in the UI — look up by summary_key if filename differs
        lookup = summary_key or hebrew_name
        summary = summaries.get(lookup, "")
        # One-liner description: the "מהות" line from the summary block
        m = re.search(r'### מהות\s*\n(.+)', summary)
        description = m.group(1).strip() if m else ""
        result[key] = {
            "name": english_name,
            "hebrew_name": hebrew_name,
            "description": description,   # one-liner for sidebar caption
            "summary": summary,           # full summary block for Tab 4 UI
            "prompt_instruction": instruction,  # detailed instructions for generation only
        }
    return result

PRESET_STYLES = _load_preset_styles()

MARKETING_FRAMEWORKS = {
    "none": {
        "name": "ללא מודל כתיבה שיווקית",
        "description": "ללא מסגרת שיווקית ספציפית",
        "structure": "",
    },
    "AIDA": {
        "name": "AIDA",
        "description": "Attention → Interest → Desire → Action",
        "structure": (
            "Structure the post using AIDA: "
            "1. Attention — grab attention with a bold opening line or question. "
            "2. Interest — build interest by presenting the problem or an intriguing angle. "
            "3. Desire — create desire by showing the transformation or benefit. "
            "4. Action — close with a clear call to action."
        ),
    },
    "PAS": {
        "name": "PAS",
        "description": "Problem → Agitate → Solution",
        "structure": (
            "Structure the post using PAS: "
            "1. Problem — identify a specific, relatable problem the reader faces. "
            "2. Agitate — intensify the pain by exploring the consequences of not solving it. "
            "3. Solution — present the insight or solution clearly and compellingly."
        ),
    },
    "FAB": {
        "name": "FAB",
        "description": "Features → Advantages → Benefits",
        "structure": (
            "Structure the post using FAB: "
            "1. Features — describe what it is or what happened (the fact). "
            "2. Advantages — explain why that matters or what it enables. "
            "3. Benefits — connect it to the reader's life and the personal value they receive."
        ),
    },
    "BAB": {
        "name": "Before-After-Bridge (BAB)",
        "description": "Before → After → Bridge",
        "structure": (
            "Structure the post using Before-After-Bridge (BAB): "
            "1. Before — describe the reader's current painful or frustrating situation. "
            "2. After — paint a vivid picture of the desired outcome after the problem is solved. "
            "3. Bridge — present the path (your insight, product, or approach) that gets them there."
        ),
    },
    "4Ps": {
        "name": "4Ps",
        "description": "Promise → Picture → Proof → Push",
        "structure": (
            "Structure the post using 4Ps: "
            "1. Promise — open with a bold, specific promise or key benefit. "
            "2. Picture — help the reader vividly imagine the result in their life. "
            "3. Proof — back it up with a fact, testimonial, stat, or real example. "
            "4. Push — close with a direct, compelling call to action."
        ),
    },
}

ASPECT_RATIOS = {
    "מרובע (1:1)":              "1:1",
    "רחב (16:9)":               "16:9",
    "לאורך (9:16)":             "9:16",
    "4:5 לאורך (Portrait)":     "4:5",
    "4:5 לרוחב (Landscape)":    "5:4",
}

IDEA_TYPE_CATEGORY_MAP = {
    "emotional":  ["מוטיבציות", "חששות", "תובנות שאנשים לא יודעים"],
    "practical":  ["שימושים ומשימות", "חיסכון בזמן", "לפני ואחרי (עם/בלי)"],
    "mistakes":   ["טעויות נפוצות", "מיתוסים", "גישות שגויות"],
    "authority":  ["תובנות מומחה", "ידע מקצועי מתקדם", "בידול מקצועי"],
    "comparison": ["לפני מול אחרי", "ישן מול חדש", "בלי מול עם"],
}

# Human-readable orientation hint for each ratio (used in prompt)
_AR_HINT = {
    "1:1":  "square format — equal width and height",
    "16:9": "landscape/horizontal — significantly wider than tall",
    "9:16": "portrait/vertical — significantly taller than wide",
    "4:5":  "portrait/vertical — slightly taller than wide",
    "5:4":  "landscape/horizontal — slightly wider than tall",
}

_DEFAULT_STYLE = (
    "Carefully analyze the visual style, lighting, color palette, photography technique, "
    "mood, and overall aesthetic of the uploaded reference photo. "
    "Generate the new image in exactly the same visual style as the reference — "
    "if it is photorealistic, generate photorealistically; if it has a specific artistic "
    "style (illustration, sketch, vintage, etc.), match that style precisely. "
    "Do not apply any unrelated default style."
)

# When the user specifies a style, it takes full priority — the default is dropped entirely.
_PROMPT_WITH_STYLE = (
    "{aspect_ratio_instruction}"
    "Generate a portrait of this exact person. {scene}. "
    "VISUAL STYLE — apply this exactly and ignore any default style: {style_instruction} "
    "If style reference images are provided below, match their color palette, lighting, mood, "
    "and overall aesthetic precisely. "
    "Preserve the person's exact facial features, age, and appearance. "
    "If any additional people (other than the main subject) appear in the scene, "
    "they should look like real people from contemporary Israeli society — "
    "natural, diverse, and modern, with everyday Israeli style and energy. "
    "Avoid generic international stock-photo looks or exaggerated cultural clichés."
    "{text_instruction}"
)

_PROMPT_DEFAULT = (
    "{aspect_ratio_instruction}"
    "Generate a professional portrait photo of this exact person. {scene}. "
    "{default_style} "
    "Keep the person's exact facial features, age, and appearance. "
    "If any additional people (other than the main subject) appear in the scene, "
    "they should look like real people from contemporary Israeli society — "
    "natural, diverse, and modern, with everyday Israeli style and energy. "
    "Avoid generic international stock-photo looks or exaggerated cultural clichés."
    "{text_instruction}"
)


def generate_post(style_guide: str, category: str, idea: str,
                  language: str = "עברית",
                  content_type: str = "LinkedIn",
                  word_count: int | None = None,
                  preset_style_instruction: str = "",
                  marketing_framework: str = "",
                  post_notes: str = "",
                  retry_feedback: str = "") -> str:
    """מייצר פוסט בשפה ובסגנון הנבחרים."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    ct_info = CONTENT_TYPES.get(content_type, {})
    word_range = ct_info.get("words", "150–300")
    word_instruction = f"{word_count}" if word_count else word_range

    style_block = f"\nAdditional Style Layer:\n{preset_style_instruction}" if preset_style_instruction else ""
    notes_block = f"\nSpecial Notes for This Post:\n{post_notes}" if post_notes else ""
    feedback_block = f"\nUser Feedback / Improvement Request (apply to this version):\n{retry_feedback}" if retry_feedback else ""

    if marketing_framework:
        structure_block = f"""
Post Structure (Marketing Model):
The post must be structured according to the following marketing model, applied THROUGH the writer's personal voice and style — not as a template, but as the underlying logic that shapes the arc of the post:
{marketing_framework}

The writing should feel personal, human, and consistent with the style guide above. The marketing model provides the skeleton; the style guide provides the flesh. Do not label the sections — let the structure emerge naturally from the writing."""
    else:
        structure_block = """
Post Structure:
1. Personal short story from daily life (concrete situation, dialogue, memory)
2. Emotional moment — confusion, doubt, small surprise
3. Natural transition to professional insight (psychology, behavior, AI)
4. Sharp closing sentence the reader takes with them"""

    prompt = f"""You are a professional content writer creating a {content_type} post.

Style guide (voice, tone, and writing DNA — follow closely):
{style_guide}

Category: {category}
Post idea: {idea}

Instructions:
- Write in {language}
- Target length: approximately {word_instruction} words
- Platform: {content_type}
- The style guide is the primary authority on voice and tone
{structure_block}

Rules:
- Short paragraphs (2-4 lines), lots of white space
- Rhetorical questions where natural
- Don't preach — let the insight emerge from the story
- Rich but not formal language
{style_block}{notes_block}{feedback_block}
- Return only the post text, no titles, labels, or explanations"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_image_prompt(post_text: str) -> str:
    """מייצר prompt באנגלית לתמונה."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Based on the following post, write ONE sentence describing a scene or setting for a portrait photo.

Rules:
- Describe only the subject's pose/action and background/environment — do NOT specify any color palette, lighting style, or artistic style (those are set separately)
- Background/scene should metaphorically represent the post's theme
- Under 25 words. Return only the scene description in English, nothing else.

Examples:
- "sitting at a desk surrounded by open books and scattered notes"
- "standing confidently before a large crowd in an open amphitheater"

Post:
{post_text}"""

    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def select_best_style(category: str, idea: str) -> tuple[str, str]:
    """
    Picks the best preset writing style for the given category+idea.
    Returns (style_key, explanation_hebrew).
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    styles_block = "\n".join(
        f"- Key: {key} | Style: {meta['name']} ({meta['hebrew_name']}) | {meta['description']}"
        for key, meta in PRESET_STYLES.items()
    )

    prompt = f"""You are a professional content strategy expert.
A content creator wants to write a post about the following:
Category: {category}
Idea: {idea}

Here are 10 available writing styles:
{styles_block}

Task:
1. Choose the single best style key for this specific idea.
2. Write a short explanation in Hebrew (2-3 sentences) explaining why this style fits this idea best.

Respond ONLY in this exact JSON format (no markdown, no extra text):
{{"key": "<style_key>", "explanation": "<Hebrew explanation>"}}"""

    last_exc = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                key = data.get("key", "")
                explanation = data.get("explanation", "")
                if key in PRESET_STYLES:
                    return key, explanation
            return list(PRESET_STYLES.keys())[0], ""
        except Exception as e:
            last_exc = e
            if "529" in str(e) or "overload" in str(e).lower():
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_exc


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


def improve_style_guide(raw_guide: str) -> str:
    """מקבל מדריך סגנון ומחזיר גרסה משופרת — ברורה, ממוקדת, וניתנת לפעולה יותר."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""You received a writing style guide created by analyzing someone's writing samples.
Your task: rewrite it to be clearer, more actionable, and better structured.

Rules:
- Keep the same 5-category structure (תחביר, אוצר מילים, טון, דימויים, קצב)
- Make each guideline concrete and actionable (e.g. "use short sentences of 10-15 words" not "writes briefly")
- Remove redundancy and vague language
- Preserve the person's unique voice characteristics
- Output ONLY the improved guide, no explanations

Guide to improve:
{raw_guide}"""
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_image(face_image, scene_description: str,
                   aspect_ratio: str = "1:1",
                   style_description: str = "",
                   add_text: bool = False,
                   text_content: str = "",
                   extra_reference_images: list | None = None) -> bytes:
    """
    מייצר תמונה עם שמירת זהות דרך Google Gemini.
    face_image: Path | str | bytes
    """
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Always enforce aspect ratio explicitly — even for 1:1 — so the model never guesses.
    _ar_hint = _AR_HINT.get(aspect_ratio, "")
    aspect_ratio_instruction = (
        f"CRITICAL: Output image MUST use exactly {aspect_ratio} aspect ratio "
        f"({_ar_hint}). Do not crop, pad, or alter this ratio for any reason. "
    )
    print(f"[generate_image] aspect_ratio={aspect_ratio!r}  hint={_ar_hint!r}")

    text_instruction = (
        f" Incorporate this text creatively into the image design: '{text_content}'."
        if add_text and text_content else ""
    )

    has_style = bool(style_description.strip()) or bool(
        extra_reference_images and any(extra_reference_images)
    )

    # Collect valid extra reference images first (needed to build has_style)
    valid_refs = []
    if extra_reference_images:
        for img_bytes in extra_reference_images:
            if img_bytes:
                try:
                    valid_refs.append(Image.open(io.BytesIO(img_bytes)))
                except Exception:
                    pass

    has_style = bool(style_description.strip()) or bool(valid_refs)

    # Build ref-inclusion clause for the prompt
    ref_clause = (
        " All additional reference images provided must appear as visual elements in the generated image."
        if valid_refs else ""
    )

    if has_style:
        style_str = style_description.strip() if style_description.strip() else "match the visual style of the reference images"
        image_prompt = _PROMPT_WITH_STYLE.format(
            scene=scene_description,
            style_instruction=style_str + ref_clause,
            aspect_ratio_instruction=aspect_ratio_instruction,
            text_instruction=text_instruction,
        )
    else:
        image_prompt = _PROMPT_DEFAULT.format(
            scene=scene_description,
            default_style=_DEFAULT_STYLE,
            aspect_ratio_instruction=aspect_ratio_instruction,
            text_instruction=text_instruction,
        )

    if isinstance(face_image, bytes):
        face_img = Image.open(io.BytesIO(face_image))
    else:
        face_img = Image.open(face_image)

    # Build contents with explicit labels so the model knows each image's role
    contents = [image_prompt, "Subject — preserve this person's exact face and identity:", face_img]

    if valid_refs:
        contents.append(
            "Reference images — incorporate ALL of these as visual elements in the generated image "
            "(objects, people, props, environments, and/or visual style shown here):"
        )
        contents.extend(valid_refs)

    response = client.models.generate_content(
        model=IMAGEN_MODEL,
        contents=contents,
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


def enhance_style_description(raw_description: str) -> str:
    """
    מקבל תיאור סגנון ויזואלי בכתיבה חופשית ומחזיר גרסה משופרת,
    מנוסחת כהנחיה מקצועית לייצור תמונה (image generation prompt style).
    Retries up to 3 times on overload (529) errors with exponential backoff.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""You are an expert AI image prompt engineer.
The user has written a rough style description for images they want to generate.
Your task: rewrite it as a rich, professional visual style description that works perfectly as an image generation style guide.

User's raw description:
{raw_description}

Rules:
- Expand and enrich: add lighting details, color palette specifics, mood, atmosphere, composition style, texture, and cinematic qualities
- Keep the user's original intent and aesthetic direction
- Write in English (image generation models work best with English style prompts)
- Be specific and vivid — no vague words like "nice" or "good"
- Output ONLY the enhanced description, no explanations or headers
- Length: 3-5 sentences, dense with visual detail"""

    last_exc = None
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            last_exc = e
            if "529" in str(e) or "overload" in str(e).lower():
                time.sleep(2 ** attempt)  # 1s, 2s, 4s
                continue
            raise
    raise last_exc


def generate_target_audiences(domain: str, language: str = "עברית",
                               audience_types: list | None = None) -> list[str]:
    """מייצר 10 קהלי יעד מתאימים לתחום."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    _type_labels = {
        "individuals": "individuals / private people",
        "small_biz":   "small business owners",
        "companies":   "companies and organizations",
        "nonprofits":  "nonprofits and public sector",
    }
    audience_filter = ""
    if audience_types and audience_types != ["not_sure"]:
        types_str = ", ".join(
            _type_labels.get(t, t) for t in audience_types if t != "not_sure"
        )
        if types_str:
            audience_filter = f"\nFocus specifically on audiences that are: {types_str}"

    prompt = f"""Generate 10 specific target audiences for content in the domain of: {domain}{audience_filter}

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


def generate_ideas_table(domain: str, audience: str, language: str = "עברית",
                          idea_types: list | None = None) -> dict:
    """
    מייצר טבלת רעיונות לפי סוגי הרעיונות שנבחרו.
    מחזיר dict שמפתחותיו שמות הקטגוריות וערכיו רשימות של 10 רעיונות כל אחת.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    effective_types = idea_types if idea_types else ["emotional", "practical"]
    all_categories: list[str] = []
    for t in effective_types:
        for cat in IDEA_TYPE_CATEGORY_MAP.get(t, []):
            if cat not in all_categories:
                all_categories.append(cat)

    cats_instruction = "\n".join(f"- {cat} (10 רעיונות)" for cat in all_categories)
    json_template_lines = [
        f'  "{cat}": ["רעיון 1", "רעיון 2", "רעיון 3", "רעיון 4", "רעיון 5", '
        f'"רעיון 6", "רעיון 7", "רעיון 8", "רעיון 9", "רעיון 10"]'
        for cat in all_categories
    ]
    json_template = "{\n" + ",\n".join(json_template_lines) + "\n}"

    prompt = f"""אני רוצה שתהיה בתפקיד של מומחה לכתיבת תוכן עבור רשתות חברתיות וכתיבה באופן כללי כגון פוסטים, בלוגים, מאמרים וכו'. אני עוסק בתחום {domain}.

אני רוצה רעיונות שיעניינו את הקהל שלי שהוא {audience}.

אני רוצה שתיתן לי 10 רעיונות לכל אחת מהקטגוריות הבאות:
{cats_instruction}

החזר את המידע כ-JSON בלבד, ללא טקסט נוסף, בפורמט הבא:
{json_template}

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


def save_outputs(post_text: str, image_bytes: bytes, outputs_dir: Path,
                 category: str = "", idea: str = "") -> tuple[Path, Path]:
    """שומר פוסט ותמונה לתיקיית outputs."""
    timestamp = int(time.time())

    def _sanitize(s: str) -> str:
        return re.sub(r'[\\/:*?"<>|]', '_', s.strip())[:30]

    if category and idea:
        slug = f"{_sanitize(category)}_{_sanitize(idea)}_{timestamp}"
    else:
        slug = str(timestamp)

    post_path = outputs_dir / f"post_{slug}.txt"
    image_path = outputs_dir / f"image_{slug}.png"

    post_path.write_text(post_text, encoding="utf-8")
    image_path.write_bytes(image_bytes)

    return post_path, image_path
