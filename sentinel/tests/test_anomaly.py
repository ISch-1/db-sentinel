"""Tests for the ML anomaly detector.

These are deterministic (fixed RNG seed): we feed a stream of 'normal' samples
then a clear outlier, and assert the detector stays quiet during warm-up and
flags the outlier once trained.

The normal samples carry small Gaussian noise on every feature — real database
metrics always fluctuate, and an Isolation Forest needs that variance to learn
a meaningful "normal". Perfectly constant features are a degenerate case that
doesn't occur with live telemetry.
"""

import numpy as np

from sentinel.anomaly import AnomalyDetector

_rng = np.random.default_rng(42)


def normal_features(i: int) -> list[float]:
    # Realistic baseline: ~10 active conns, low utilization/latency, near-zero lag,
    # each with a little noise like a real metric stream.
    return [
        10.0 + _rng.normal(0, 1.0),          # active connections
        0.10 + _rng.normal(0, 0.01),         # utilization
        abs(_rng.normal(0, 0.05)),           # idle-in-transaction
        abs(_rng.normal(0, 0.02)),           # replica lag
        0.002 + abs(_rng.normal(0, 0.0005)), # probe latency
    ]


def test_stays_quiet_during_warmup():
    d = AnomalyDetector(window=120, contamination=0.02, min_warmup=30)
    flagged = any(d.observe(normal_features(i))[0] for i in range(29))
    assert not flagged
    assert not d.warmed_up


def test_warms_up_after_min_samples():
    d = AnomalyDetector(window=120, contamination=0.02, min_warmup=30)
    for i in range(30):
        d.observe(normal_features(i))
    assert d.warmed_up


def test_flags_a_clear_outlier():
    d = AnomalyDetector(window=200, contamination=0.02, min_warmup=30)
    for i in range(80):
        d.observe(normal_features(i))
    # A dramatic spike: connections maxed, high latency, replica lag.
    is_anomaly, score = d.observe([98.0, 0.98, 15.0, 1.5, 2.0])
    assert is_anomaly
    assert score > 0


def test_normal_sample_after_training_not_flagged():
    d = AnomalyDetector(window=200, contamination=0.02, min_warmup=30)
    for i in range(80):
        d.observe(normal_features(i))
    is_anomaly, _ = d.observe(normal_features(81))
    assert not is_anomaly
