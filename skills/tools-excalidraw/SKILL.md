---
name: tools-excalidraw
description: Create Excalidraw diagram JSON files for Obsidian. Use when the user wants to visualize workflows, architectures, or concepts as diagrams.
user-invocable: true
---

# Excalidraw Diagram Creator

Generate `.excalidraw.md` files (Obsidian-compatible) that argue visually, not just display information.

**References** — read these before generating any diagram:
- [style](references/style.md) — mandatory style defaults (stroke, fill, roughness, arrowheads)
- [color-palette](references/color-palette.md) — semantic color palette (single source of truth for all colors)
- [element-templates](references/element-templates.md) — copy-paste JSON templates for each element type
- [design-patterns](references/design-patterns.md) — visual patterns, layout principles, and design process
- [obsidian-export](references/obsidian-export.md) — Obsidian Excalidraw plugin format and label binding

---

## When to Use Excalidraw vs Mermaid

Obsidian renders Mermaid natively (no plugin needed). Mermaid is also much cheaper in tokens.

| Use Mermaid when...                        | Use Excalidraw when...                      |
|--------------------------------------------|---------------------------------------------|
| Simple flowcharts, sequences, class diagrams | Layout control and precise positioning matter |
| The diagram is for documentation/reference  | Visual polish or custom styling is needed    |
| Quick sketch, structure over aesthetics     | Freeform composition (timelines, fan-outs)   |
| Token budget is tight                       | The shape itself should carry meaning        |

---

## Style Defaults (Primary)

These style rules always apply and override any other defaults. See [style](references/style.md) for details.

- **Arrowheads**: always `"triangle"`
- **Stroke width**: thin (`strokeWidth: 1`)
- **Stroke style**: `"solid"` or `"dotted"` depending on context
- **Sloppiness**: architect (`roughness: 0`)
- **Fill style**: `"solid"` or `"cross-hatch"` depending on context
- **Opacity**: always `100`

---

## Core Philosophy

Diagrams should argue, not display. The shape should be the meaning.

**Isomorphism test**: if you removed all text, would the structure alone communicate the concept? If not, redesign.

**Container test**: for each boxed element, ask "would this work as free-floating text?" If yes, remove the container. Aim for <30% of text elements inside containers.

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

---

## Text Sizing Heuristic

Excalidraw expects explicit `width`/`height` on text elements. Since we cannot measure text, use these approximations:

- **Width**: `charCount * fontSize * 0.6`
- **Height**: `lineCount * fontSize * 1.25`

Excalidraw reflows text on open, so approximate values self-correct.

---

## Large Diagram Strategy

For comprehensive diagrams, build JSON one section at a time:

1. **Create the base file** with JSON wrapper and the first section of elements
2. **Add one section per edit** — namespace seeds by section (100xxx, 200xxx, etc.)
3. **Use descriptive string IDs** (e.g., `"trigger_rect"`, `"arrow_fan_left"`)
4. **Update cross-section bindings** as you go

---

## Output Format

Always output as `.excalidraw.md` for Obsidian compatibility. The format wraps the JSON in Obsidian comment delimiters:

```markdown
---
excalidraw-plugin: raw
tags: [excalidraw]
---
%%
## Drawing
```json
{ ... full excalidraw scene JSON ... }
```
%%
```

See `references/obsidian-export.md` for label binding details.
