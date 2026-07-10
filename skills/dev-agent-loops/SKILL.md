---
name: dev-agent-loops
description: Use when designing agentic loops or recurring workflows — choosing between turn-based, goal-based, time-based, or proactive loop types; writing stop conditions to prevent runaway agents; encoding verification into skills; or managing token cost for iterative automation.
---

# Agent Loop Design

## Overview

Loops are agents repeating cycles of work until a stop condition is met. The four key design decisions are: **trigger**, **stop condition**, **task primitive**, and **verification strategy**.

## Loop Types

| Type | Trigger | Stop Condition | Command |
|------|---------|---------------|---------|
| **Turn-based** | User prompt | Task complete or needs input | (default) |
| **Goal-based** | Manual start | Goal achieved or turn cap hit | `/goal` |
| **Time-based** | Interval/schedule | Cancelled or work done | `/loop`, `/schedule` |
| **Proactive** | Event / schedule | Routine turned off | hooks / cron |

**Choosing a type:**
- One-shot task with checkpoints → turn-based
- Open-ended objective with unknowns → goal-based (`/goal`)
- Recurring maintenance, polling, monitoring → time-based (`/loop`)
- React to external events (git push, email, file change) → proactive

## Stop Condition Design

Always set an explicit stop condition. Never rely on the agent deciding when it is done.

- **Turn cap** — prevents runaway cost; set conservatively, raise if needed
- **Objective measure** — test count, score threshold, file diff empty
- **External signal** — webhook, file presence, API status field

Avoid subjective stops ("when it looks right"). They fail non-deterministically.

## Verification-as-Skills Pattern

Rather than having a loop hand back unverified output, encode self-checks in a SKILL.md:

1. Write the acceptance criterion as a deterministic check (test suite, score ≥ N, diff clean)
2. Put the check in the skill the agent calls on each iteration
3. The loop continues until the check passes or turn cap is hit

This keeps verification consistent across iterations and makes success observable.

## Second-Agent Review

For quality-sensitive loops, bring in a second agent with fresh context to review the primary agent's output. A reviewer that didn't produce the work is less biased and catches rationalizations the primary agent makes.

Pattern: primary agent produces → reviewer agent scores/approves → loop exits on approval or re-queues.

## Cost Hygiene

- Match model to task complexity — don't use a large model for a trivial iteration step
- Pilot on a small slice before running the full loop at scale
- Prefer deterministic scripts over having the agent re-derive steps each iteration
- Use `/usage` to review token spend after a loop completes
- Set `/schedule` frequency no higher than the rate of meaningful change
