# 0002 — Self-healing as code, not runbooks

**Status:** Accepted
**Date:** 2026-08-05

## Context

The job this platform imitates is keeping a database fleet reliable "with code rather than manual effort." The traditional approach is a runbook: a human gets paged, reads a wiki page, and types commands. That doesn't scale, is slow (bad for MTTR), and encodes knowledge in prose that goes stale.

## Decision

Encode operational knowledge as **rules and actions in code** (`sentinel/healing.py`). Each rule is a pure function `HealthSample -> Action | None`; each action is an executable remediation. The control loop evaluates rules every cycle and applies the first that fires. A master switch (`HEALING_ENABLED`) runs the engine in **observe-only** mode first, so you can trust it before letting it act.

## Consequences

**Positive**
- Remediation happens in seconds without a human, directly improving MTTR — which the platform measures (`dbs_mttr_seconds`).
- Rules are pure functions, so they're unit-tested without a database (`tests/test_healing.py`).
- The runbook *is* the code — it can't go stale relative to what actually runs.

**Negative**
- An incorrect rule could take a harmful action automatically. Mitigated by: conservative first-match-wins ordering, observe-only mode, actions that only ever terminate clearly-safe sessions (idle / idle-in-transaction past a threshold), and every action recorded as a metric.
- Not every incident is auto-fixable; those still open an incident for a human. Automation handles the toil, not the judgement calls.

## Alternatives considered

1. **Wiki runbooks + manual response.** The status quo it's designed to replace.
2. **Alert-only (page a human, take no action).** Half the value. We still alert, but we act on the known, safe cases first.
