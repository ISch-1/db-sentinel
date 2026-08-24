"""ML anomaly detection over the health-signal stream.

Uses an Isolation Forest (scikit-learn) trained online on a rolling window of
recent samples. Isolation Forest isolates outliers with random splits — points
that are easy to isolate are anomalous. It needs no labels, which fits an SRE
setting where you rarely have labelled failures.

The detector is deliberately conservative: it warms up on a window of normal
traffic before it will flag anything, so a cold start doesn't page on-call.
"""

from __future__ import annotations

from collections import deque

import numpy as np
from sklearn.ensemble import IsolationForest

from . import metrics


class AnomalyDetector:
    def __init__(self, window: int = 120, contamination: float = 0.02, min_warmup: int = 30):
        self._window: deque[list[float]] = deque(maxlen=window)
        self._contamination = contamination
        self._min_warmup = min_warmup
        self._model: IsolationForest | None = None
        self._refit_every = 20
        self._since_fit = 0

    @property
    def warmed_up(self) -> bool:
        return len(self._window) >= self._min_warmup

    def observe(self, features: list[float]) -> tuple[bool, float]:
        """Record a sample and score it.

        Returns (is_anomaly, score) where score is higher for more anomalous
        points. During warm-up nothing is flagged.
        """
        self._window.append(features)

        if not self.warmed_up:
            metrics.ANOMALY_SCORE.set(0.0)
            metrics.ANOMALY_FLAG.set(0)
            return False, 0.0

        if self._model is None or self._since_fit >= self._refit_every:
            self._fit()
            self._since_fit = 0
        self._since_fit += 1

        x = np.asarray([features], dtype=float)
        # decision_function: negative => outlier. Flip so higher = more anomalous.
        raw = float(self._model.decision_function(x)[0])
        score = -raw
        is_anomaly = self._model.predict(x)[0] == -1

        metrics.ANOMALY_SCORE.set(score)
        metrics.ANOMALY_FLAG.set(1 if is_anomaly else 0)
        return bool(is_anomaly), score

    def _fit(self) -> None:
        data = np.asarray(self._window, dtype=float)
        self._model = IsolationForest(
            n_estimators=100,
            contamination=self._contamination,
            random_state=42,
        )
        self._model.fit(data)
