"""Rule-driven self-healing.

Each rule inspects a HealthSample and, if it fires, returns an Action. Actions
are the codified operational knowledge an SRE would otherwise apply by hand at
3am — the whole point of the platform is to remove that manual toil.

Rules are pure and independently testable; the engine applies them and records
what it did. When healing is disabled the engine still evaluates and records,
so you can run it in "observe only" mode before trusting it in production.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

import psycopg

from . import metrics
from .config import CONFIG
from .probes import HealthSample

log = logging.getLogger("sentinel.healing")


@dataclass(frozen=True)
class Action:
    name: str
    reason: str
    # A callable that performs the remediation and returns rows/sessions affected.
    execute: Callable[[psycopg.Cursor], int]


# --------------------------------------------------------------------------- #
# Rules: HealthSample -> Action | None                                        #
# --------------------------------------------------------------------------- #

def rule_kill_idle_in_transaction(s: HealthSample) -> Action | None:
    """'idle in transaction' sessions hold locks and leak connections. Long-lived
    ones are almost always an abandoned client — terminate them."""
    if s.idle_in_transaction <= 0:
        return None

    def _execute(cur: psycopg.Cursor) -> int:
        cur.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE state = 'idle in transaction'
              AND now() - state_change > interval '%s seconds'
            """,
            (CONFIG.idle_in_txn_kill_seconds,),
        )
        return cur.rowcount

    return Action(
        name="kill_idle_in_transaction",
        reason=f"{s.idle_in_transaction} sessions idle in transaction past threshold",
        execute=_execute,
    )


def rule_relieve_connection_pressure(s: HealthSample) -> Action | None:
    """When connection utilization is dangerously high, reclaim capacity by
    terminating plain idle sessions (safe: they hold no transaction)."""
    if s.connection_utilization < CONFIG.connection_high_watermark:
        return None

    def _execute(cur: psycopg.Cursor) -> int:
        cur.execute(
            """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE state = 'idle'
              AND pid <> pg_backend_pid()
              AND now() - state_change > interval '30 seconds'
            """
        )
        return cur.rowcount

    return Action(
        name="relieve_connection_pressure",
        reason=(
            f"connection utilization {s.connection_utilization:.0%} "
            f">= {CONFIG.connection_high_watermark:.0%} watermark"
        ),
        execute=_execute,
    )


# The ordered rule set. First-match-wins per cycle keeps actions conservative.
RULES: list[Callable[[HealthSample], Action | None]] = [
    rule_kill_idle_in_transaction,
    rule_relieve_connection_pressure,
]


def evaluate(sample: HealthSample) -> Action | None:
    """Return the first action whose rule fires, or None."""
    for rule in RULES:
        action = rule(sample)
        if action is not None:
            return action
    return None


def apply(action: Action) -> int:
    """Execute a healing action against the database. Returns affected count.
    Honors the HEALING_ENABLED switch (observe-only when off)."""
    if not CONFIG.healing_enabled:
        log.info("healing disabled; would have run %s (%s)", action.name, action.reason)
        metrics.HEALING_ACTIONS.labels(action=action.name, outcome="skipped").inc()
        return 0
    try:
        with psycopg.connect(CONFIG.dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                affected = action.execute(cur)
        log.info("healed: %s affected=%d (%s)", action.name, affected, action.reason)
        metrics.HEALING_ACTIONS.labels(action=action.name, outcome="success").inc()
        return affected
    except Exception as exc:  # noqa: BLE001 - we want to record any failure
        log.error("healing action %s failed: %s", action.name, exc)
        metrics.HEALING_ACTIONS.labels(action=action.name, outcome="error").inc()
        return 0
