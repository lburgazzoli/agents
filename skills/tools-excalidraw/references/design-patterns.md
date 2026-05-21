# Design Patterns & Layout

## Design Process

### Step 0: Assess Depth

- **Simple/Conceptual**: abstract shapes, labels, relationships (mental models, overviews)
- **Comprehensive/Technical**: concrete examples, code snippets, real data (systems, architectures)

For technical diagrams, research actual specs, formats, and event names before drawing.

### Step 1: Understand

For each concept ask: what does it DO? What relationships exist? What's the core flow?

### Step 2: Map Concepts to Visual Patterns

| If the concept...              | Use this pattern                              |
|--------------------------------|-----------------------------------------------|
| Spawns multiple outputs        | **Fan-out** — radial arrows from center       |
| Combines inputs into one       | **Convergence** — arrows merging              |
| Has hierarchy/nesting          | **Tree** — lines + free-floating text         |
| Is a sequence of steps         | **Timeline** — line + dots + labels           |
| Loops or improves continuously | **Spiral/Cycle** — arrow returning            |
| Is an abstract state           | **Cloud** — overlapping ellipses              |
| Transforms input to output     | **Assembly line** — before → process → after  |
| Compares two things            | **Side-by-side** — parallel with contrast     |
| Separates into phases          | **Gap/Break** — visual separation             |

### Step 3: Ensure Variety

Each major concept must use a different visual pattern. No uniform cards or grids.

---

## Shape Meaning

| Concept Type                    | Shape                           |
|---------------------------------|---------------------------------|
| Labels, descriptions, details   | none (free-floating text)       |
| Section titles, annotations     | none (free-floating text)       |
| Markers on a timeline           | small `ellipse` (10-20px)       |
| Start, trigger, input           | `ellipse`                       |
| End, output, result             | `ellipse`                       |
| Decision, condition             | `diamond`                       |
| Process, action, step           | `rectangle`                     |
| Abstract state, context         | overlapping `ellipse`           |
| Hierarchy node                  | lines + text (no boxes)         |

Default to no container. Add shapes only when they carry meaning.

---

## Layout Principles

### Hierarchy Through Scale

| Level       | Size    | Role                    |
|-------------|---------|-------------------------|
| Hero        | 300x150 | Visual anchor, most important |
| Primary     | 180x90  | Main elements           |
| Secondary   | 120x60  | Supporting elements     |
| Small       | 60x40   | Minor details           |

### Whitespace = Importance

The most important element has the most empty space around it (200px+).

### Flow Direction

Left→right or top→bottom for sequences, radial for hub-and-spoke.

### Connections Required

If A relates to B, there must be an arrow. Position alone doesn't show relationships.

---

## Visual Pattern Details

### Fan-Out (One-to-Many)

Central element with arrows radiating to multiple targets. Use for sources, root causes, central hubs.

### Convergence (Many-to-One)

Multiple inputs merging through arrows to a single output. Use for aggregation, funnels, synthesis.

### Tree (Hierarchy)

Use `line` elements for trunk and branches, free-floating text for labels — no boxes needed.

### Timeline (Sequence)

Vertical or horizontal line with small marker dots (10-20px ellipses) at intervals, free-floating labels beside each dot.

### Spiral/Cycle (Continuous Loop)

Elements in sequence with arrow returning to start. Use for feedback loops, iterative processes.

### Assembly Line (Transformation)

Input → process box → output with clear before/after states.

### Side-by-Side (Comparison)

Two parallel structures with visual contrast. Use for before/after, options, trade-offs.

---

## Evidence Artifacts (Technical Diagrams)

For technical diagrams, include concrete examples that prove accuracy:

| Artifact Type    | When to Use                       | How to Render                          |
|------------------|-----------------------------------|----------------------------------------|
| Code snippets    | APIs, integrations                | Dark rectangle + syntax-colored text   |
| Data/JSON        | Data formats, schemas, payloads   | Dark rectangle + green text            |
| Event sequences  | Protocols, workflows              | Timeline pattern (line + dots + labels)|
| API/method names | Real function calls, endpoints    | Use actual names from docs             |

Use real content, not placeholders — show what things actually look like.

---

## Container vs Free-Floating Text

| Use a Container When...                        | Use Free-Floating Text When...              |
|-----------------------------------------------|---------------------------------------------|
| It's the focal point of a section              | It's a label or description                 |
| It needs visual grouping with other elements   | It's supporting detail or metadata          |
| Arrows need to connect to it                   | It describes something nearby               |
| The shape itself carries meaning               | It's a section title, subtitle, or annotation |
| It represents a distinct "thing" in the system | Typography alone creates sufficient hierarchy |

Use font size, weight, and color to create visual hierarchy without boxes.
