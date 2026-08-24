"""Health probes: read reliability signals from the target database.

Each probe is cheap and read-only. Together they form the feature vector the
anomaly detector consumes and the facts the healing engine acts on.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import psycopg

from . import metrics
from .config import CONFIG


@dataclass
class HealthSample:
    """One snapshot of database health at a point in time."""

    up: bool
    connections_active: int
    connections_max: int
    idle_in_transaction: int
    replica_lag_seconds: float
    probe_latency_seconds: float

    @property
    def connection_utilization(self) -> float:
        if self.connections_max <= 0:
            return 0.0
        return self.connections_active / self.connections_max

    def as_features(self) -> list[float]:
        """Feature vector for the anomaly detector."""
        return [
            float(self.connections_active),
            self.connection_utilization,
            float(self.idle_in_transaction),
            self.replica_lag_seconds,
            self.probe_latency_seconds,
        ]


def probe() -> HealthSample:
    """Run one full health probe. Never raises — a failure is a valid sample
    with up=False, because "the database didn't answer" is itself a signal."""
    metrics.PROBES_TOTAL.inc()
    started = time.perf_counter()
    try:
        with psycopg.connect(CONFIG.dsn) as conn:
            with conn.cursor() as cur:
                # Canary query — measures round-trip latency.
                cur.execute("SELECT 1")
                cur.fetchone()
                probe_latency = time.perf_counter() - started
                metrics.PROBE_LATENCY.observe(probe_latency)

                active = _active_connections(cur)
                idle_in_txn = _idle_in_transaction(cur)
                lag = _replica_lag_seconds(cur)

        sample = HealthSample(
            up=True,
            connections_active=active,
            connections_max=CONFIG.max_connections,
            idle_in_transaction=idle_in_txn,
            replica_lag_seconds=lag,
            probe_latency_seconds=probe_latency,
        )
        _publish(sample)
        return sample

    except Exception:
        metrics.PROBES_FAILED.inc()
        metrics.DB_UP.set(0)
        return HealthSample(
            up=False,
            connections_active=0,
            connections_max=CONFIG.max_connections,
            idle_in_transaction=0,
            replica_lag_seconds=0.0,
            probe_latency_seconds=time.perf_counter() - started,
        )


def _active_connections(cur: psycopg.Cursor) -> int:
    cur.execute("SELECT count(*) FROM pg_stat_activity WHERE state IS NOT NULL")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _idle_in_transaction(cur: psycopg.Cursor) -> int:
    cur.execute(
        """
        SELECT count(*) FROM pg_stat_activity
        WHERE state = 'idle in transaction'
          AND now() - state_change > interval '%s seconds'
        """,
        (CONFIG.idle_in_txn_kill_seconds,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def _replica_lag_seconds(cur: psycopg.Cursor) -> float:
    """On a primary with no replica this is 0. On a replica it reads the real
    lag. Kept defensive so it works on a single-node dev Postgres."""
    try:
        cur.execute("SELECT pg_is_in_recovery()")
        row = cur.fetchone()
        in_recovery = bool(row[0]) if row else False
        if not in_recovery:
            return 0.0
        cur.execute(
            "SELECT COALESCE(EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())), 0)"
        )
        row = cur.fetchone()
        return float(row[0]) if row else 0.0
    except Exception:
        return 0.0


def _publish(sample: HealthSample) -> None:
    metrics.DB_UP.set(1 if sample.up else 0)
    metrics.CONNECTIONS_ACTIVE.set(sample.connections_active)
    metrics.CONNECTIONS_MAX.set(sample.connections_max)
    metrics.CONNECTIONS_UTILIZATION.set(sample.connection_utilization)
    metrics.IDLE_IN_TXN.set(sample.idle_in_transaction)
    metrics.REPLICA_LAG_SECONDS.set(sample.replica_lag_seconds)
