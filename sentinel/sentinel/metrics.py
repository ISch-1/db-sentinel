"""Prometheus instruments. Everything the agent observes and does is a metric,
so the whole platform is visible in Grafana and alertable in Prometheus."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# --- Health signals the probes populate ---
DB_UP = Gauge("dbs_database_up", "1 if the database answered the probe, else 0")
CONNECTIONS_ACTIVE = Gauge("dbs_connections_active", "Active backend connections")
CONNECTIONS_MAX = Gauge("dbs_connections_max", "Configured max_connections")
CONNECTIONS_UTILIZATION = Gauge(
    "dbs_connections_utilization", "Active connections / max_connections (0..1)"
)
IDLE_IN_TXN = Gauge(
    "dbs_idle_in_transaction", "Sessions stuck 'idle in transaction'"
)
REPLICA_LAG_SECONDS = Gauge("dbs_replica_lag_seconds", "Replication lag in seconds")
PROBE_LATENCY = Histogram(
    "dbs_probe_query_seconds",
    "Latency of the canary probe query",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

# --- Anomaly detection ---
ANOMALY_SCORE = Gauge(
    "dbs_anomaly_score", "Anomaly score of the latest sample (higher = more anomalous)"
)
ANOMALY_FLAG = Gauge(
    "dbs_anomaly_detected", "1 if the latest sample was flagged anomalous"
)

# --- Self-healing ---
HEALING_ACTIONS = Counter(
    "dbs_healing_actions_total",
    "Automated healing actions taken",
    ["action", "outcome"],
)
INCIDENTS_OPENED = Counter("dbs_incidents_opened_total", "Incidents opened")
INCIDENTS_RESOLVED = Counter("dbs_incidents_resolved_total", "Incidents auto-resolved")
MTTR_SECONDS = Histogram(
    "dbs_mttr_seconds",
    "Mean time to recovery: incident open -> auto-resolved",
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)

# --- Availability accounting feeding the SLO ---
PROBES_TOTAL = Counter("dbs_probes_total", "Health probes attempted")
PROBES_FAILED = Counter("dbs_probes_failed_total", "Health probes that failed")
