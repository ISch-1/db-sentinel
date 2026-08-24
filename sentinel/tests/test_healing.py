"""Unit tests for the healing rules — pure functions, no database needed."""

from sentinel.config import CONFIG
from sentinel.healing import (
    evaluate,
    rule_kill_idle_in_transaction,
    rule_relieve_connection_pressure,
)
from sentinel.probes import HealthSample


def sample(**overrides) -> HealthSample:
    base = dict(
        up=True,
        connections_active=10,
        connections_max=100,
        idle_in_transaction=0,
        replica_lag_seconds=0.0,
        probe_latency_seconds=0.002,
    )
    base.update(overrides)
    return HealthSample(**base)


def test_healthy_sample_triggers_no_action():
    assert evaluate(sample()) is None


def test_idle_in_transaction_fires_kill_rule():
    action = rule_kill_idle_in_transaction(sample(idle_in_transaction=3))
    assert action is not None
    assert action.name == "kill_idle_in_transaction"


def test_no_idle_in_transaction_does_not_fire():
    assert rule_kill_idle_in_transaction(sample(idle_in_transaction=0)) is None


def test_connection_pressure_fires_above_watermark():
    # 90/100 = 90% >= 80% default watermark
    action = rule_relieve_connection_pressure(sample(connections_active=90))
    assert action is not None
    assert action.name == "relieve_connection_pressure"


def test_connection_pressure_quiet_below_watermark():
    action = rule_relieve_connection_pressure(sample(connections_active=50))
    assert action is None


def test_evaluate_prefers_idle_in_transaction_first():
    # Both conditions true; ordered rule set returns the idle-in-txn fix first.
    s = sample(connections_active=95, idle_in_transaction=2)
    action = evaluate(s)
    assert action is not None
    assert action.name == "kill_idle_in_transaction"


def test_utilization_computation():
    assert sample(connections_active=25, connections_max=100).connection_utilization == 0.25


def test_watermark_boundary_is_inclusive():
    threshold = int(CONFIG.connection_high_watermark * 100)
    action = rule_relieve_connection_pressure(sample(connections_active=threshold))
    assert action is not None
