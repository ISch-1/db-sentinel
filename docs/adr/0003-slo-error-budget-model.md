# 0003 — SLOs + error budgets as the reliability contract

**Status:** Accepted
**Date:** 2026-08-05

## Context

"Is the database healthy?" is not a yes/no question at scale — everything fails sometimes. The role calls for owning **SLOs and error budgets**, which turn reliability into a measurable, agreed contract instead of a vibe.

## Decision

Model reliability as **SLOs with error budgets**:

- An **SLO** is a target success ratio over a window (e.g. 99.9% of health probes succeed over 30 days). SLO definitions live in DynamoDB, provisioned by Terraform.
- The **error budget** is the failure the SLO permits: `1 - target`. If the target is 99.9%, the budget is 0.1% of events.
- **Burn rate** is how fast the budget is being spent: `observed_failure_rate / allowed_failure_rate`. A burn rate > 1 means you'll breach if it continues.

The control-plane (Java) reads SLO definitions from DynamoDB, pulls live counts from Prometheus, and computes the budget. The math lives in a pure `ErrorBudget.compute(...)` so it's fully unit-tested.

## Consequences

**Positive**
- Reliability becomes a number you can query (`GET /api/v1/slo`), alert on, and put on a dashboard.
- Burn rate distinguishes "a blip" from "we're about to breach" — the basis for sensible alerting.
- The definition (DynamoDB) is separate from the measurement (Prometheus), so targets change without redeploying code.

**Negative**
- Meaningful SLOs need real traffic history; a fresh system reports a full budget until events accumulate. Handled explicitly (`total <= 0` => full budget).
- The demo reads lifetime counters, not a true rolling window. Documented; production would scope the PromQL to the SLO window (`increase(...[30d])`).

## References
- Google SRE Book — Service Level Objectives; Embracing Risk.
