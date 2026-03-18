# Design System — AI Content Studio

## Principles

- **Dark-first**: Deep near-black backgrounds with layered transparency
- **RTL-native**: All text, inputs, and layout default to right-to-left (Hebrew)
- **Glassmorphism**: Frosted-glass cards built with `backdrop-filter: blur()` and translucent borders
- **Purple/Blue/Green accent triad**: Consistent gradient accent used across buttons, highlights, and titles
- **Accessible contrast**: Interactive elements use at minimum `rgba(255,255,255,0.85)` text on dark surfaces

---

## Color Palette

### Backgrounds

| Name | Value | Usage |
|---|---|---|
| App background | `linear-gradient(135deg, #0a0a0f 0%, #0d0d1a 40%, #0a1628 100%)` | `.stApp` base |
| Sidebar | `rgba(255,255,255,0.03)` + `backdrop-filter: blur(20px)` | Sidebar panel |
| Input field | `#12122a` | All text inputs, textareas, number inputs |
| Dropdown menu | `#1a1a35` | Select popover and listbox |
| Glass card | `rgba(255,255,255,0.04)` | `.glass-card` container |

### Accent Colors

| Name | Hex / RGBA | Usage |
|---|---|---|
| Primary purple | `#7c3aed` | Buttons, progress bar, highlights |
| Primary blue | `#3b82f6` | Button gradient end, tab highlight |
| Accent green | `#34d399` | Success states, status pills |
| Light purple | `#a78bfa` | Section labels, hover borders |
| Gradient title | `#a78bfa → #60a5fa → #34d399` | Main title gradient text |

### Text Colors

| Role | Value |
|---|---|
| Primary text | `rgba(255,255,255,0.85)` |
| Secondary / label | `rgba(255,255,255,0.95)` (labels), `rgba(255,255,255,0.6)` (captions) |
| Placeholder | `rgba(255,255,255,0.3)` |
| Dimmed | `rgba(255,255,255,0.25)` |
| Full white | `#ffffff` (selected/active states) |

### Semantic Colors

| State | Color |
|---|---|
| Success | `rgba(52,211,153,0.9)` |
| Warning | `rgba(251,191,36,0.9)` |
| Error | `rgba(239,68,68,0.1)` background + `rgba(239,68,68,0.25)` border |
| Info | `rgba(255,255,255,0.8)` |

---

## Typography

### Font

```css
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;500;600;700&display=swap');
font-family: 'Assistant', sans-serif;
```

**Assistant** is an Israeli-designed typeface with excellent Hebrew + Latin support. Used at all weights.

### Scale

| Role | Size | Weight | Usage |
|---|---|---|---|
| Main title | `2.8rem` | 700 | Page hero title |
| Sidebar title | `1.4rem` | 700 | Sidebar header (removed) |
| Sub-title | `0.95rem` | 300 | Page subtitle |
| Sidebar section label | `0.78rem` | 700 | `.sidebar-section` uppercase headers |
| Widget label | `0.92rem` | 600 | All form labels |
| Section label | `0.7rem` | 600 | `.section-label` uppercase in tabs |
| Caption | `0.72rem–0.82rem` | 400–500 | Helper text, pill labels |
| Body / post display | `0.95rem` | 400 | Post output text |

### Text Direction

All text is RTL by default:
```css
.stApp { direction: rtl; }
```

Post display and textareas explicitly set `direction: rtl; text-align: right`.

---

## Spacing & Layout

### Page Layout
- Streamlit `layout="wide"` — full browser width
- Sidebar always expanded (`initial_sidebar_state="expanded"`)
- Main area uses `st.columns()` for 2-column layouts

### Spacing Tokens (CSS)

| Token | Value | Usage |
|---|---|---|
| Card padding | `1.8rem` | `.glass-card` |
| Section margin | `1.2rem 0 0.6rem 0` | `.sidebar-section` |
| Divider margin | `1.2rem 0` | `.custom-divider` |
| Border radius — large | `20–24px` | Cards, header |
| Border radius — medium | `12–14px` | Inputs, dropdowns, file uploaders |
| Border radius — small | `8–10px` | Buttons inside uploaders |

---

## Components

### `.glass-card`
Glassmorphism content container.
```css
background: rgba(255,255,255,0.04);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 20px;
padding: 1.8rem;
backdrop-filter: blur(10px);
transition: border-color 0.3s ease;
```
Hover: `border-color: rgba(167,139,250,0.3)`

### `.sidebar-section`
Uppercase section header label in sidebar.
```css
font-size: 0.78rem;
font-weight: 700;
letter-spacing: 0.12em;
color: rgba(255,255,255,0.9);
text-transform: uppercase;
margin: 1.2rem 0 0.6rem 0;
```

### `.section-label`
Smaller uppercase label inside tab content areas.
```css
font-size: 0.7rem;
font-weight: 600;
letter-spacing: 0.15em;
color: rgba(167,139,250,0.8);
text-transform: uppercase;
margin-bottom: 0.8rem;
```

### `.custom-divider`
Subtle horizontal rule between sections.
```css
height: 1px;
background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
margin: 1.2rem 0;
```

### `.main-title`
Hero gradient text.
```css
font-size: 2.8rem;
font-weight: 700;
background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

### `.status-pill`
Small badge for status indicators.
```css
/* green variant */
background: rgba(52,211,153,0.15);
border: 1px solid rgba(52,211,153,0.3);
color: #34d399;
border-radius: 100px;
padding: 0.2rem 0.8rem;
font-size: 0.72rem;
font-weight: 600;
letter-spacing: 0.08em;

/* purple variant (.status-pill-purple) */
background: rgba(167,139,250,0.15);
border-color: rgba(167,139,250,0.3);
color: #a78bfa;
```

---

## Interactive Elements

### Primary Button (`st.button`)
```css
background: linear-gradient(135deg, #7c3aed, #3b82f6);
color: white;
border: none;
border-radius: 14px;
font-weight: 600;
font-size: 1rem;
padding: 0.75rem 2rem;
box-shadow: 0 4px 20px rgba(124,58,237,0.35);
transition: all 0.3s ease;
```
Hover: `translateY(-2px)` + stronger shadow

### Download Button (`st.download_button`)
```css
background: rgba(255,255,255,0.06);
color: rgba(255,255,255,0.8);
border: 1px solid rgba(255,255,255,0.12);
border-radius: 12px;
```

### Text Input / Number Input
```css
background: #12122a;
border: 1px solid rgba(255,255,255,0.12);
border-radius: 12px;
color: rgba(255,255,255,0.88);
direction: rtl;
```
Placeholder: `rgba(255,255,255,0.3)`

### Textarea
Same as text input + `font-size: 0.93rem`, `line-height: 1.8`, `padding: 1rem`

### Select / Dropdown
- Box: `background: #12122a`, dark border, `direction: rtl`
- Open list: `background: #1a1a35`
- Hover option: `rgba(124,58,237,0.3)`
- Selected option: `rgba(124,58,237,0.4)`

### File Uploader
```css
/* outer wrapper */
background: rgba(255,255,255,0.02);
border: 1px dashed rgba(167,139,250,0.35);
border-radius: 14px;

/* inner dropzone */
background: rgba(255,255,255,0.04);
border: 1px dashed rgba(167,139,250,0.3);

/* browse button */
background: rgba(124,58,237,0.25);
border: 1px solid rgba(124,58,237,0.4);
```

### Custom Toggle (Add Text to Image)
Implemented as a stateful `st.button` (not `st.toggle`) for reliable styling:
- **Off state**: grey border `rgba(255,255,255,0.45)`, dim background, "⬜" prefix
- **On state**: purple gradient fill `linear-gradient(135deg,#7c3aed,#3b82f6)`, bright border, "✅" prefix

---

## Tab Bar

```css
/* bar */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 1px solid rgba(255,255,255,0.08);
}

/* inactive tab */
color: rgba(255,255,255,0.55)

/* active tab */
color: white

/* highlight bar under active tab */
background: linear-gradient(90deg, #7c3aed, #3b82f6)
```

---

## Header Banner

Full-width image banner using a base64-embedded JPEG:
```css
background-image: linear-gradient(rgba(5,5,15,0.15), rgba(5,5,20,0.2)),
                  url('data:image/jpeg;base64,...');
background-size: cover;
background-position: center center;
height: 280px;
border-radius: 0 0 20px 20px;
margin: -4rem -4rem 2rem -4rem;   /* bleeds edge-to-edge, flush to top */
overflow: hidden;
```

---

## Instructional Info Cards

Used at the top of "הגדרות תמונה" and "סגנון כתיבה" tabs:
```css
background: rgba(255,255,255,0.03);
border: 1px solid rgba(255,255,255,0.07);
border-radius: 18px;
padding: 1.8rem 2rem;
margin-bottom: 1.5rem;
direction: rtl;
text-align: right;
```
Body text: `color: rgba(255,255,255,0.65)`, `font-size: 0.92rem`, `line-height: 1.9`
Bold headings inside: `color: rgba(255,255,255,0.9)`

---

## Images

```css
[data-testid="stImage"] img {
    border-radius: 18px;
    border: 1px solid rgba(255,255,255,0.08);
}
```

---

## Progress Bar

```css
background: linear-gradient(90deg, #7c3aed, #3b82f6);
border-radius: 100px;
```

---

## RTL Guidelines

1. Set `direction: rtl` globally on `.stApp`
2. All inputs explicitly set `direction: rtl`
3. Labels use `text-align: right` and `display: block`
4. Hebrew text in content uses `text-align: right` on its container
5. The sidebar is on the right side (Streamlit default in RTL mode)
6. Column order in multi-column layouts: rightmost = primary content
