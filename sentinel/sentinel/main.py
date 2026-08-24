"""Entry point: the control loop plus the metrics/admin HTTP server.

The loop is the beating heart of the platform:

    probe -> export metrics -> score for anomalies -> evaluate healing rules
          -> act -> record incident + MTTR -> repeat

The HTTP server exposes Prometheus metrics, a health check, and a chaos
endpoint used to demonstrate self-healing.
"""

from __future__ import annotations

import logging
import threading
import time

from flask import Flask, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from werkzeug.serving import make_server

from . import chaos, healing
from .anomaly import AnomalyDetector
from .aws import IncidentStore
from .config import CONFIG
from .probes import probe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
log = logging.getLogger("sentinel.main")

app = Flask(__name__)
_detector = AnomalyDetector(window=CONFIG.anomaly_window, contamination=CONFIG.anomaly_contamination)
_incidents = IncidentStore()
_stop = threading.Event()


@app.get("/health")
def health():
    return jsonify(status="ok", healing_enabled=CONFIG.healing_enabled)


@app.get("/metrics")
def metrics_endpoint():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.post("/admin/chaos")
def admin_chaos():
    body = request.get_json(force=True, silent=True) or {}
    fault = body.get("fault", "connection_flood")
    magnitude = int(body.get("magnitude", 50))
    try:
        detail = chaos.inject(fault, magnitude)
        return jsonify(injected=fault, magnitude=magnitude, detail=detail)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


def control_loop() -> None:
    """probe -> detect -> heal, once per interval, forever."""
    log.info(
        "sentinel starting: interval=%.1fs healing=%s target=%s:%s",
        CONFIG.probe_interval_s, CONFIG.healing_enabled, CONFIG.db_host, CONFIG.db_port,
    )
    while not _stop.is_set():
        cycle_start = time.perf_counter()
        try:
            _run_one_cycle()
        except Exception:  # noqa: BLE001 - the loop must never die
            log.exception("control loop cycle failed")
        elapsed = time.perf_counter() - cycle_start
        _stop.wait(max(0.0, CONFIG.probe_interval_s - elapsed))


def _run_one_cycle() -> None:
    sample = probe()

    # 1. If the database is down, that's an incident on its own.
    if not sample.up:
        _incidents.open_incident("appdb", "database_down", "health probe failed")
        return

    # 2. ML: is this sample anomalous relative to recent normal behaviour?
    is_anomaly, score = _detector.observe(sample.as_features())

    # 3. Rules: is there a known, fixable failure mode right now?
    action = healing.evaluate(sample)

    if action is None:
        # Healthy cycle. If we had opened incidents that are now clear, resolve.
        if _incidents.has_open:
            # Resolve the oldest tracked incident — the condition has cleared.
            for iid in list(_incidents._open.keys()):
                _incidents.resolve_incident(iid, "condition cleared")
        return

    # 4. There's a problem: open an incident, heal it, and (if the fix worked)
    #    the next healthy cycle resolves it and records MTTR.
    kind = "anomaly" if is_anomaly else "threshold"
    detail = f"{action.reason} (anomaly_score={score:.3f})"
    _incidents.open_incident("appdb", kind, detail)
    healing.apply(action)


class _Server(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self._srv = make_server("0.0.0.0", CONFIG.metrics_port, app)

    def run(self) -> None:
        self._srv.serve_forever()

    def shutdown(self) -> None:
        self._srv.shutdown()


def main() -> None:
    server = _Server()
    server.start()
    log.info("HTTP server listening on :%d (/metrics /health /admin/chaos)", CONFIG.metrics_port)
    try:
        control_loop()
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        _stop.set()
        server.shutdown()


if __name__ == "__main__":
    main()
