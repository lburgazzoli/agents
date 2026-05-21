# Style Defaults

These rules always apply and override any other defaults.

| Property         | Value                                                                 |
|------------------|-----------------------------------------------------------------------|
| `endArrowhead`   | `"triangle"` — always                                                 |
| `strokeWidth`    | `1` — thin                                                            |
| `strokeStyle`    | `"solid"` for primary relationships; `"dotted"` for optional/async/secondary |
| `roughness`      | `0` — architect (clean lines, not rigid)                              |
| `roundness`      | `{"type": 1}` — minimal rounding                                     |
| `fillStyle`      | `"solid"` for primary elements; `"cross-hatch"` for emphasis or secondary groups |
| `opacity`        | `100` — always                                                        |
| `fontFamily`     | `3` — monospace                                                       |

## When to Use Solid vs Dotted Stroke

- **Solid**: primary flows, direct dependencies, synchronous calls, structural relationships
- **Dotted**: optional paths, async communication, secondary connections, fallback flows

## When to Use Solid vs Cross-Hatch Fill

- **Solid**: primary elements, main actors, core components
- **Cross-hatch**: secondary groups, emphasis areas, background regions, supporting elements
