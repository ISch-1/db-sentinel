# 0004 — Isolation Forest for unsupervised anomaly detection

**Status:** Accepted
**Date:** 2026-08-05

## Context

Threshold rules catch known failure modes ("connections above 80%"). But many incidents are subtle combinations that no single threshold captures — latency creeping up *while* connections rise *while* lag grows. The role explicitly asks to "incorporate AI as part of the design." I want to catch anomalies I didn't write a rule for.

## Decision

Run an **Isolation Forest** (scikit-learn) over the stream of health samples. It's an unsupervised model that isolates outliers with random splits — points easy to isolate are anomalous. It fits SRE reality because it needs **no labelled failures**, which you rarely have.

Design choices:
- **Feature vector**: active connections, connection utilization, idle-in-transaction count, replica lag, probe latency — the model sees the *combination*, not one metric.
- **Online training**: refit periodically on a rolling window of recent samples, so "normal" adapts to the current workload.
- **Warm-up guard**: flags nothing until it has seen a minimum of normal samples, so a cold start doesn't page on-call.

The anomaly score and flag are exported as metrics (`dbs_anomaly_score`, `dbs_anomaly_detected`) and, when combined with a firing rule, raise a higher-severity incident.

## Consequences

**Positive**
- Catches multivariate anomalies that no hand-written threshold would.
- Unsupervised — works from day one without a labelled dataset.
- Cheap: an Isolation Forest on a small window trains in milliseconds.

**Negative**
- Unsupervised models produce false positives. Mitigated with a conservative contamination setting, the warm-up guard, and by using the ML signal to *raise severity*, not to take destructive action on its own.
- "Normal" drift can hide a slow regression. Acceptable for this scope; a production system would complement it with longer-horizon trend checks.

## Alternatives considered

1. **Rolling z-score per metric.** Simple, but univariate — misses combinations. Isolation Forest sees the whole vector.
2. **A supervised classifier.** Needs labelled incidents we don't have.
3. **A deep model (LSTM autoencoder).** Overkill for five features; far more to train and operate.
