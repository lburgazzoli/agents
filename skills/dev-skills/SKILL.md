---
name: dev-skills
description: Guidance for creating and modifying Claude Code skills. Triggers when authoring new skills, improving existing ones, or reviewing skill quality.
user-invocable: false
---

# Skill Authoring Guide

## Example Repositories

Consult these as sources of good skill examples:

- **agent-eval-harness**: https://github.com/opendatahub-io/agent-eval-harness
- **rfe-creator**: https://github.com/jwforres/rfe-creator
- **odh-test-gen**: https://github.com/opendatahub-io/odh-test-gen

Clone under `.context/repos/<org>/` if you need to inspect their skill files (follow cloning rules from `dev-context`).

## Principles

Based on https://generativeprogrammer.com/p/9-principles-that-separate-useful

### Getting Selected

1. **Metadata is the gate** — The `description` field is how skills get discovered. Write precise activation triggers and exclusion clauses, not vague summaries. If the description doesn't fire the skill when needed and block it when inappropriate, nothing else matters.

2. **Disclose progressively** — Keep frontmatter lean. Reference external files (`resources/`, `scripts/`) instead of embedding everything. Every token in the skill competes with conversation history.

3. **Process over prose** — Structure skills as workflows with checkpoints, not reference essays. Use checklists with exit criteria. The reader should know exactly what to do next.

### Running Reliably

4. **Explain the why** — Pair every rule with its reasoning so the model can handle edge cases the skill didn't explicitly cover. The principle becomes the rubric for unanticipated situations.

5. **Anticipate the excuse** — Preemptively address rationalizations the model might use to skip critical steps. Write rebuttals directly into the skill — the model struggles to argue past counter-arguments in its own context.

6. **Code over inference** — Move deterministic work into scripts (`scripts/`). Invoke via Bash; only output enters context. Keeps behavior consistent and source hidden.

7. **Stay in scope** — Touch only what the skill is asked to touch. No adjacent refactors, no modernization side-quests. Narrow diffs are reviewable and mergeable.

### Surviving Contact with Reality

8. **Skills decay** — Treat skills as living artifacts. Libraries update, APIs change, stale guidance produces confident wrong output. Exercise skills against current tasks periodically.

9. **Run before you ship** — Debug skills through observed test runs, not imagination. Promote repeatedly-written helpers to scripts, document gotchas from real runs, add rebuttals based on actual rationalizations.
