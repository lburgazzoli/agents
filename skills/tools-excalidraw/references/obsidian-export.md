# Obsidian Excalidraw Export

## Format

The Obsidian Excalidraw plugin uses `.excalidraw.md` files. We use `raw` mode with uncompressed JSON:

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

The `%%` markers are Obsidian comment delimiters. The `## Drawing` section must be inside the `%%...%%` block so it's hidden from markdown rendering and only processed by the Excalidraw plugin.

### Raw mode

With `excalidraw-plugin: raw`, the plugin reads uncompressed JSON directly from the `` ```json `` code block. No `## Text Elements` section or LZ-string compression is needed - the plugin handles everything from the JSON.

### Labels on Shapes/Arrows

Labels are separate bound text elements in the JSON:

1. **Parent** gets `boundElements: [{"type": "text", "id": "label_id"}]`
2. **Label** becomes a text element with `containerId: "parent_id"`, `textAlign: "center"`, `verticalAlign: "middle"`
