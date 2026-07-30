# CV Template Selector — Design Spec
**Date:** 2026-07-30  
**Project:** TailorIQ (JDCVMatcherAI)  
**Status:** Approved

---

## 1. Overview

Users can pick from 15 professional CV templates after analysis completes. Selecting a card immediately rerenders the on-screen CV preview in that template's style. The Download button generates and returns a DOCX in the selected template.

---

## 2. Templates

| # | ID | Name | Style |
|---|---|---|---|
| 1 | `ats_classic` | ATS Classic | Single-col, Calibri, black rules |
| 2 | `microsoft_modern` | Microsoft Modern | Navy `#2b579a` header band |
| 3 | `corporate_blue` | Corporate Blue | Navy `#1a3a5c` gradient rule |
| 4 | `executive_dark` | Executive Dark | Dark `#1a1a2e` sidebar, indigo tags |
| 5 | `clean_minimal` | Clean Minimal | Helvetica, hairline rules, light grey |
| 6 | `charcoal_gold` | Charcoal Gold | Dark `#1e2a3a` header, gold `#c9a84c` accent |
| 7 | `elegant_serif` | Elegant Serif | Georgia, warm `#2c1810`, ornament divider |
| 8 | `tech_pro` | Tech Pro | Dark `#0d1117` bg, monospace, blue `#79c0ff` headings |
| 9 | `creative_teal` | Creative Teal | Teal-to-cyan `#0d9488→#0891b2` gradient header |
| 10 | `linkedin_style` | LinkedIn Style | `#0077b5` bar, avatar initials, card sections |
| 11 | `harvard_classic` | Harvard Classic | Times New Roman, crimson `#a51c30` headings |
| 12 | `compact_dense` | Compact Dense | Arial, slate `#334155` heading pills, max density |
| 13 | `two_column_split` | Two Column Split | Navy `#1e3a5f` left col, skill bars, right content |
| 14 | `green_professional` | Green Professional | Forest green `#14532d`, gradient accent bar |
| 15 | `purple_modern` | Purple Modern | Purple gradient `#4c1d95→#a855f7` header, dot bullets |

Default on page load: `ats_classic`.

---

## 3. UI — Frontend

### 3.1 Placement

The template selector replaces the current bare "Tailored Resume Preview" section heading. It renders above the CV preview inside the same `<section class="card">`.

```
┌─ Tailored Resume Preview ─────────────────────────────────────┐
│                                                                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │
│  │ mini   │ │ mini   │ │ mini   │ │ mini   │ │ mini   │      │
│  │preview │ │preview │ │preview │ │preview │ │preview │      │
│  │ card   │ │ card   │ │ card   │ │ card   │ │ card   │      │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘      │
│  … 3 rows × 5 columns = 15 total (scrollable on mobile)       │
│                                                                │
│  Selected: Microsoft Modern       [ ⬇ Download DOCX ]         │
│                                                                │
│  ┌─────────────────── CV Preview ────────────────────────┐    │
│  │  Renders with selected template's CSS styling          │    │
│  └───────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Interaction

- **Click card** → selected card gets indigo border + checkmark badge; `selectedTemplate` Zustand state updates → CV preview below immediately rerenders. No Apply button.
- **Download DOCX** → calls `GET /analysis/{run_id}/cv-download?template=<id>` → triggers file download. Button shows spinner while waiting.
- Only one card selected at a time (radio behaviour).

### 3.3 Component structure

```
frontend/src/components/dashboard/
  TemplateSelector/
    index.tsx              ← grid of TemplateCard components + Download button
    TemplateCard.tsx       ← mini CV preview card (CSS-in-JS or Tailwind)
    templateDefinitions.ts ← array of { id, name, description, previewClass }
  TailoredResumePreview.tsx  ← updated: accepts selectedTemplate prop, applies CSS class
```

### 3.4 Zustand state addition

```typescript
// analysisStore.ts
selectedTemplate: string          // template ID, default 'ats_classic'
setSelectedTemplate: (id: string) => void
```

### 3.5 Template CSS

Each template is a CSS class `.tmpl-<id>` applied to the preview container. CSS variables control: `--tmpl-accent`, `--tmpl-heading-color`, `--tmpl-header-bg`, `--tmpl-font`. The 15 template CSS definitions live in `frontend/src/styles/cv-templates.css`.

Two-column templates (executive_dark, two_column_split) use CSS `display: flex` in the preview. The preview faithfully renders the two-column layout.

---

## 4. Backend — DOCX Generation

### 4.1 New endpoint

```
GET /analysis/{run_id}/cv-download?template=ats_classic
```

- Auth: JWT required (existing `get_current_user` dependency)
- Validates `run_id` belongs to user, status is `completed` or `partial`
- Calls `generate_cv_docx(tailored_resume, template_id)` → returns `bytes`
- Response: `StreamingResponse` with `Content-Disposition: attachment; filename="cv_<template_id>.docx"`

### 4.2 Template renderer

```
backend/app/agents/
  cv_templates/
    __init__.py
    base.py             ← CVTemplateBase: shared helpers (add_heading, add_bullet, add_contact)
    ats_classic.py      ← render_ats_classic(doc, resume_data)
    microsoft_modern.py
    corporate_blue.py
    executive_dark.py   ← uses borderless 2-col Table
    clean_minimal.py
    charcoal_gold.py
    elegant_serif.py
    tech_pro.py
    creative_teal.py
    linkedin_style.py
    harvard_classic.py
    compact_dense.py
    two_column_split.py ← uses borderless 2-col Table
    green_professional.py
    purple_modern.py
    registry.py         ← TEMPLATE_REGISTRY: dict mapping id → render function
```

### 4.3 Template definition (shared)

```python
# registry.py
TEMPLATE_REGISTRY: dict[str, TemplateRenderer] = {
    "ats_classic":       render_ats_classic,
    "microsoft_modern":  render_microsoft_modern,
    # … all 15
}
```

### 4.4 Two-column DOCX limitation

`executive_dark` and `two_column_split` use a borderless `Table` with 2 cells — left cell for sidebar content (skills, certs), right cell for experience/summary. This approximates the two-column layout. Exact pixel parity with the browser preview is not guaranteed.

### 4.5 Existing package_generation.py

The existing `generate_package_zip` flow (used by the current Download ZIP endpoint) continues to use the **default template** (`ats_classic`) for the CV DOCX inside the ZIP. The new `/cv-download` endpoint is additive; the ZIP flow is unchanged.

---

## 5. Data Flow

```
User clicks template card
  → selectedTemplate state updated (Zustand)
  → TailoredResumePreview re-renders with new CSS class
  → (no API call)

User clicks Download DOCX
  → GET /analysis/{run_id}/cv-download?template=microsoft_modern
  → backend: fetch MatchResult, extract tailored_resume JSON
  → call render_microsoft_modern(doc, tailored_resume)
  → return DOCX bytes as attachment
  → browser saves file: cv_microsoft_modern.docx
```

---

## 6. Error Handling

- **Template ID not in registry**: 400 Bad Request — `"Unknown template: <id>"`
- **Run not found / not owned**: 404 — existing pattern
- **Run not completed**: 400 — `"Analysis not yet complete"`
- **DOCX generation error**: 500 — log exception, return `"CV generation failed"`
- **Download button**: shows spinner; on error shows inline toast "Download failed — try again"

---

## 7. Out of Scope

- PDF export (future work)
- Template preview using the user's *actual* resume text inside the mini card (cards show static sample text)
- User-saved template preference (no persistence — defaults to ATS Classic on each page load)
- Modifying the ZIP download to use the selected template

---

## 8. File Changes Summary

**Frontend**
- `src/components/dashboard/TemplateSelector/index.tsx` — new
- `src/components/dashboard/TemplateSelector/TemplateCard.tsx` — new
- `src/components/dashboard/TemplateSelector/templateDefinitions.ts` — new
- `src/styles/cv-templates.css` — new (15 template CSS classes)
- `src/components/dashboard/TailoredResumePreview.tsx` — updated (accept template prop)
- `src/store/analysisStore.ts` — updated (add selectedTemplate state)
- `src/pages/Dashboard.tsx` — updated (render TemplateSelector, pass selectedTemplate)

**Backend**
- `backend/app/agents/cv_templates/` — new package (16 files)
- `backend/app/api/analysis.py` — add `/cv-download` endpoint
