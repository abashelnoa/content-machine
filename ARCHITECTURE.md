# Architecture — AI Content Studio

## Overview

AI Content Studio is a single-page **Streamlit** web application that generates Hebrew social media posts and matching images. The user configures style, audience, and content parameters through a persistent sidebar; the main area contains five tabbed workspaces. All state is managed in `st.session_state` — there is no database or persistent backend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI framework | Streamlit ≥ 1.32 |
| Text generation | Anthropic Claude `claude-sonnet-4-6` |
| Image generation | Google Gemini `gemini-3.1-flash-image-preview` |
| Document parsing | `python-docx`, `openpyxl`, `pypdf` |
| Image handling | Pillow |
| Config | `python-dotenv` (.env file) |
| Language | Python 3.11+ |

---

## File Structure

```
test/
├── app.py                        # Streamlit entry point — all UI logic (~1825 lines)
├── generator.py                  # All AI generation functions (~580 lines)
├── data_loader.py                # File I/O — DOCX / XLSX / PDF parsing (~220 lines)
├── requirements.txt              # Python dependencies
├── .env                          # API keys (not committed)
├── .env.example                  # API key template
│
├── 10 writing styles/            # 10 .txt files with detailed writing instructions
│   └── תקציר 10 סגנונות כתיבה.txt  # Summary file — parsed for UI display
├── Writing style/                # Default style guide DOCX
│   └── liraz_style_guide (1).docx
├── header image/                 # Header banner image
├── my images/                    # User personal reference images (legacy)
├── style images/                 # Visual style reference images (legacy)
├── outputs/                      # Auto-saved generated posts + images
└── רעיונות לפוסטים.docx          # Default post ideas document
```

---

## Module Responsibilities

### `app.py`
Owns all UI rendering and user interaction. Responsibilities:
- CSS injection and global styling
- Session state initialization (`init_state()`)
- Sidebar: idea selection, free-text idea, language, content type, writing style, marketing framework, reference image, notes, generate button
- Tab 1 — **יצירה**: trigger generation, display post + image, retry buttons, archive
- Tab 2 — **הגדרות תמונה**: reference image upload, style images upload, style analysis, free-text style with AI enhancement
- Tab 3 — **מחולל רעיונות**: domain input, audience suggestion, ideas table generation, download/load
- Tab 4 — **סגנון כתיבה**: preset style browser, personal style analyzer (samples → guide), style guide upload
- Tab 5 — **ארכיון**: scrollable history of past generations with download

### `generator.py`
Owns all AI calls. No Streamlit imports — pure Python. Exports:

| Function | Model | Purpose |
|---|---|---|
| `generate_post()` | Claude | Create Hebrew social post |
| `generate_image_prompt()` | Claude | Describe scene for image model |
| `generate_text_for_image()` | Claude | Short text overlay phrase |
| `generate_image()` | Gemini | Generate image with identity preservation |
| `analyze_style_images()` | Claude (vision) | Batch-analyze up to 10 style images |
| `enhance_style_description()` | Claude | Rewrite free-text style as pro prompt |
| `generate_target_audiences()` | Claude | 10 audiences from a domain |
| `generate_ideas_table()` | Claude | Ideas by motivations / fears / unknowns |
| `generate_writing_style()` | Claude | Analyze writing samples → style guide |
| `save_outputs()` | — | Save post + image to `outputs/` |

Also exports configuration constants used by `app.py`:
`CONTENT_TYPES`, `LANGUAGES`, `PRESET_STYLES`, `MARKETING_FRAMEWORKS`, `ASPECT_RATIOS`

### `data_loader.py`
Owns all file I/O. No Streamlit imports — pure Python. Responsibilities:
- Load style guide from DOCX or PDF
- Load post ideas from DOCX, XLSX, or PDF → `dict[str, list[str]]`
- Return image file paths from `my images/` and `style images/`
- Create DOCX output from generated ideas or style guide
- Ensure `outputs/` directory exists

---

## Data Flow

### Post + Image Generation

```
Sidebar inputs
    │
    ├─ effective_idea  = custom_content.strip() OR dropdown idea
    ├─ effective_category = dropdown category OR "כללי"
    ├─ style_guide    = generated_style_guide OR uploaded DOCX/PDF OR default DOCX
    ├─ preset_instr   = PRESET_STYLES[preset_style]["prompt_instruction"]
    └─ fw_instr       = MARKETING_FRAMEWORKS[marketing_framework]["structure"]
         │
         ▼
generator.generate_post(style_guide, category, idea, language, content_type,
                        word_count, preset_style_instruction, marketing_framework,
                        post_notes)
         │
         ▼  post_text → st.session_state.post_text
         │
         ├─ (if add_text_to_image) generator.generate_text_for_image(post_text)
         │
         ▼
generator.generate_image_prompt(post_text)  → scene description
         │
         ▼
generator.generate_image(face_source, scene, aspect_ratio,
                         style_description, add_text, text_content)
         │
         ▼  image_bytes → st.session_state.image_bytes
         │
         ▼
generator.save_outputs(post_text, image_bytes, outputs_dir,
                       category=effective_category, idea=effective_idea)
         │
         ▼
st.session_state.archive.append(entry)   (max 20 entries)
```

### Writing Style Loading

```
Option A — Preset (10 styles from files):
  generator.py startup → _load_preset_styles()
      reads "10 writing styles/*.txt" + summary file
      → PRESET_STYLES dict (name, hebrew_name, description, prompt_instruction)
  User selects preset → st.session_state.preset_style = key
  At generation → PRESET_STYLES[key]["prompt_instruction"] injected into prompt

Option B — Upload DOCX/PDF:
  st.file_uploader → data_loader.load_style_guide(bytes, suffix)
      → st.session_state.style_guide (plain text)

Option C — AI-analyzed samples:
  User pastes 4-5 writing samples
  generator.generate_writing_style(samples) → guide text
      → st.session_state.generated_style_guide
      (takes priority over uploaded file at generation time)
```

### Ideas Loading

```
Option A — From ideas generator (Tab 3):
  domain + audience → generator.generate_ideas_table()
      → dict[audience → list[ideas]]
  User clicks "Load to sidebar" → st.session_state.post_ideas = dict

Option B — Upload DOCX / XLSX / PDF:
  st.file_uploader → data_loader.load_post_ideas(bytes, suffix)
      DOCX: reads table rows (col0 = category, rest = ideas)
      XLSX: reads active sheet rows (col0 = category, rest = ideas)
      PDF:  extracts text, heuristic parse (short line = category header)
      → st.session_state.post_ideas = dict[str, list[str]]

Option C — Free text (custom_content):
  User types in sidebar text input
  At generation: effective_idea = custom_content.strip() OR dropdown idea
```

---

## Session State Reference

| Key | Type | Description |
|---|---|---|
| `post_text` | str | Last generated post text |
| `image_bytes` | bytes\|None | Last generated image |
| `style_guide` | str\|None | Uploaded style guide text |
| `post_ideas` | dict\|None | Loaded ideas `{category: [ideas]}` |
| `style_bytes` | bytes\|None | Raw bytes of uploaded style file |
| `ideas_bytes` | bytes\|None | Raw bytes of uploaded ideas file |
| `character_image_bytes` | bytes\|None | Reference identity image |
| `style_description` | str | Visual style description (from analysis or free text) |
| `style_image_list` | list[bytes] | Uploaded style reference images |
| `language` | str | Output language (default "עברית") |
| `content_type` | str | Platform (LinkedIn, Instagram, etc.) |
| `word_count` | int | Custom word count (0 = platform default) |
| `aspect_ratio` | str | Image ratio (1:1, 16:9, 9:16, 2:3, 3:2) |
| `add_text_to_image` | bool | Whether to overlay text on image |
| `target_audiences` | list[str] | AI-suggested audiences for ideas tab |
| `ideas_table` | dict | Generated ideas table data |
| `generated_style_guide` | str | AI-analyzed style guide (highest priority) |
| `style_upload_key` | int | Counter to force file uploader widget reset |
| `preset_style` | str | Selected preset key or "none" |
| `marketing_framework` | str | Selected framework key or "none" |
| `post_notes` | str | Special instructions for post generation |
| `image_notes` | str | Special instructions for image generation |
| `archive` | list[dict] | Last 20 generated post+image pairs |
| `custom_content` | str | Free-text idea input (overrides dropdown) |
| `free_style_text` | str | Free-text visual style description |
| `_jump_to_ideas` | bool | Flag to trigger JS tab navigation |

---

## API Integration

### Anthropic (Claude)
- **Auth**: `ANTHROPIC_API_KEY` from `.env`
- **Model**: `claude-sonnet-4-6`
- **Usage**: All text generation, vision analysis, style learning
- **Client**: `anthropic.Anthropic()` instantiated per function call

### Google GenAI (Gemini)
- **Auth**: `GOOGLE_API_KEY` from `.env`
- **Model**: `gemini-3.1-flash-image-preview`
- **Usage**: Image generation with identity (face/object) preservation
- **Input**: Base64 reference image + text prompt
- **Output**: PNG bytes

---

## Key Constraints & Patterns

**Streamlit widget key uniqueness**: Widget keys must be unique per run. File uploaders that need programmatic reset use a counter suffix (`key=f"style_upload_{st.session_state.style_upload_key}"`).

**Sidebar renders before tabs**: Any session state set inside a tab is not visible to sidebar widgets on the same run. Workaround: `st.rerun()` after state changes that the sidebar must reflect.

**Tab navigation from sidebar**: JavaScript injection via `st.components.v1.html(height=0)` after sidebar close, triggered by `_jump_to_ideas` flag.

**Style priority at generation time**:
```
generated_style_guide  >  uploaded style_guide  >  default DOCX style_guide
preset_style instruction appended separately as additive layer
```

**Archive limit**: Capped at 20 entries (`st.session_state.archive[-20:]`) to avoid memory bloat in session.
