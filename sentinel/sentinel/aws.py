"""Incident persistence in DynamoDB (LocalStack in dev, real AWS in prod).

The table is provisioned by Terraform (infra/terraform/dynamodb.tf). This module
only reads and writes items — it never creates infrastructure, keeping the
"infrastructure as code" boundary clean.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config as BotoConfig

from . import metrics
from .config import CONFIG

log = logging.getLogger("sentinel.aws")


class IncidentStore:
    def __init__(self) -> None:
        self._client = boto3.client(
            "dynamodb",
            endpoint_url=CONFIG.aws_endpoint_url,  # None => real AWS
            region_name=CONFIG.aws_region,
            config=BotoConfig(retries={"max_attempts": 3, "mode": "standard"}),
        )
        self._table = CONFIG.incidents_table
        # Track open incidents in-process so we can compute MTTR on resolve.
        self._open: dict[str, float] = {}

    def open_incident(self, target: str, kind: str, detail: str) -> str:
        incident_id = str(uuid.uuid4())
        opened_at = datetime.now(timezone.utc).isoformat()
        try:
            self._client.put_item(
                TableName=self._table,
                Item={
                    "incident_id": {"S": incident_id},
                    "opened_at": {"S": opened_at},
                    "target": {"S": target},
                    "kind": {"S": kind},
                    "detail": {"S": detail},
                    "status": {"S": "open"},
                },
            )
            self._open[incident_id] = time.monotonic()
            metrics.INCIDENTS_OPENED.inc()
            log.warning("incident opened %s kind=%s: %s", incident_id, kind, detail)
        except Exception as exc:  # noqa: BLE001
            log.error("failed to persist incident: %s", exc)
        return incident_id

    def resolve_incident(self, incident_id: str, resolution: str) -> None:
        try:
            # A full implementation would update the item's status; for the demo
            # we record resolution + MTTR, which is what the SLO story needs.
            started = self._open.pop(incident_id, None)
            if started is not None:
                mttr = time.monotonic() - started
                metrics.MTTR_SECONDS.observe(mttr)
                log.info("incident resolved %s in %.1fs: %s", incident_id, mttr, resolution)
            metrics.INCIDENTS_RESOLVED.inc()
        except Exception as exc:  # noqa: BLE001
            log.error("failed to resolve incident: %s", exc)

    @property
    def has_open(self) -> bool:
        return bool(self._open)
