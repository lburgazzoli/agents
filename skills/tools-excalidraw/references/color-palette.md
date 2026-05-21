# Color Palette

Single source of truth for all colors. Do not invent new colors — if a concept doesn't fit an existing category, use Primary/Neutral or Secondary.

Always pair a darker stroke with a lighter fill for contrast.

---

## Shape Colors (Semantic)

| Semantic Purpose    | Fill      | Stroke    |
|---------------------|-----------|-----------|
| Primary/Neutral     | `#3b82f6` | `#1e3a5f` |
| Secondary           | `#60a5fa` | `#1e3a5f` |
| Tertiary            | `#93c5fd` | `#1e3a5f` |
| Start/Trigger       | `#fed7aa` | `#c2410c` |
| End/Success         | `#a7f3d0` | `#047857` |
| Warning/Reset       | `#fee2e2` | `#dc2626` |
| Decision            | `#fef3c7` | `#b45309` |
| AI/LLM             | `#ddd6fe` | `#6d28d9` |
| Inactive/Disabled   | `#dbeafe` | `#1e40af` (use dotted stroke) |
| Error               | `#fecaca` | `#b91c1c` |

---

## Text Colors (Hierarchy)

| Level           | Color     | Use For                              |
|-----------------|-----------|--------------------------------------|
| Title           | `#1e40af` | Section headings, major labels       |
| Subtitle        | `#3b82f6` | Subheadings, secondary labels        |
| Body/Detail     | `#64748b` | Descriptions, annotations, metadata  |
| On light fills  | `#374151` | Text inside light-colored shapes     |
| On dark fills   | `#ffffff` | Text inside dark-colored shapes      |

---

## Evidence Artifact Colors

| Artifact         | Background | Text Color                        |
|------------------|-----------|-----------------------------------|
| Code snippet     | `#1e293b` | Syntax-colored (language-appropriate) |
| JSON/data example| `#1e293b` | `#22c55e` (green)                 |

---

## Arrows and Lines

| Element                              | Color                                      |
|--------------------------------------|--------------------------------------------|
| Arrows                               | Stroke color of the source element's semantic purpose |
| Structural lines (dividers, timelines) | Primary stroke (`#1e3a5f`) or slate (`#64748b`) |
| Marker dots (fill + stroke)          | Primary fill (`#3b82f6`)                   |

---

## Background

| Property          | Value     |
|-------------------|-----------|
| Canvas background | `#ffffff` |

---

## Color Consistency Rules

- Assign colors by semantic role — reuse the same color for elements of the same category
- Limit the palette to 3-5 tones per diagram to keep it readable
