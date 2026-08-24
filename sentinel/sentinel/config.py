"""Environment-driven configuration. Sensible local defaults; override via env."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    # Target database (stands in for RDS / Aurora)
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = _int("DB_PORT", 5432)
    db_user: str = os.getenv("DB_USER", "app")
    db_password: str = os.getenv("DB_PASSWORD", "app")
    db_name: str = os.getenv("DB_NAME", "appdb")

    # AWS / LocalStack
    aws_endpoint_url: str | None = os.getenv("AWS_ENDPOINT_URL") or None
    aws_region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    incidents_table: str = os.getenv("INCIDENTS_TABLE", "dbs-incidents")

    # Loop + server
    probe_interval_s: float = _float("PROBE_INTERVAL_S", 5.0)
    metrics_port: int = _int("METRICS_PORT", 9200)

    # Reliability thresholds (also encoded in Terraform CloudWatch alarms)
    max_connections: int = _int("MAX_CONNECTIONS", 100)
    connection_high_watermark: float = _float("CONNECTION_HIGH_WATERMARK", 0.80)
    idle_in_txn_kill_seconds: int = _int("IDLE_IN_TXN_KILL_SECONDS", 60)
    replica_lag_threshold_s: float = _float("REPLICA_LAG_THRESHOLD_S", 10.0)

    # Self-healing master switch. Off => detect and record, but take no action.
    healing_enabled: bool = _bool("HEALING_ENABLED", True)

    # Anomaly detector
    anomaly_window: int = _int("ANOMALY_WINDOW", 120)
    anomaly_contamination: float = _float("ANOMALY_CONTAMINATION", 0.02)

    @property
    def dsn(self) -> str:
        return (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={self.db_user} password={self.db_password} connect_timeout=3"
        )


CONFIG = Config()
