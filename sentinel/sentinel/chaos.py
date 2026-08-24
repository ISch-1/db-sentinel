"""Fault injection so self-healing can be demonstrated on demand.

Real SREs practice with game days and chaos experiments. These faults create
exactly the conditions the healing rules are designed to fix, so you can watch
the loop detect, act, and recover — end to end — in under a minute.
"""

from __future__ import annotations

import logging
import threading

import psycopg

from .config import CONFIG

log = logging.getLogger("sentinel.chaos")


def connection_flood(magnitude: int) -> str:
    """Open `magnitude` sessions and leave them 'idle in transaction'. This is
    the classic connection-leak incident — the healing engine should reclaim
    them via rule_kill_idle_in_transaction / relieve_connection_pressure."""
    held: list[psycopg.Connection] = []

    def _hold() -> None:
        for _ in range(magnitude):
            try:
                conn = psycopg.connect(CONFIG.dsn)
                conn.autocommit = False
                cur = conn.cursor()
                cur.execute("BEGIN")
                cur.execute("SELECT 1")  # now 'idle in transaction'
                held.append(conn)
            except Exception as exc:  # noqa: BLE001
                log.warning("chaos: could not open connection: %s", exc)
        log.warning("chaos: opened %d idle-in-transaction sessions", len(held))

    threading.Thread(target=_hold, daemon=True).start()
    return f"opened up to {magnitude} idle-in-transaction sessions"


FAULTS = {
    "connection_flood": connection_flood,
}


def inject(fault: str, magnitude: int) -> str:
    fn = FAULTS.get(fault)
    if fn is None:
        raise ValueError(f"unknown fault '{fault}'. known: {sorted(FAULTS)}")
    return fn(magnitude)
