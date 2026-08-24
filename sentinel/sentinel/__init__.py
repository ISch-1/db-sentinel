"""db-sentinel: an SRE agent for managed databases.

Probes a database, exports metrics, detects anomalies with ML, and heals
common failure modes automatically. See the package modules:

    config   - environment-driven configuration
    metrics  - Prometheus instruments
    probes   - read database health signals
    anomaly  - ML anomaly detection over the signal stream
    healing  - rule-driven self-healing actions
    aws      - incident persistence in DynamoDB
    main     - the control loop + admin/metrics HTTP server
"""

__version__ = "0.1.0"
