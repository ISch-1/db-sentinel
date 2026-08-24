# db-sentinel

[![CI](https://github.com/ISch-1/db-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/ISch-1/db-sentinel/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Java](https://img.shields.io/badge/Java-21-orange)](https://openjdk.org/projects/jdk/21/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC)](https://www.terraform.io/)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

> An SRE platform that keeps a managed database reliable **with code, not runbooks**. It probes the database, exports metrics, detects anomalies with machine learning, and heals common failure modes automatically — then measures its own SLOs, error budgets, and mean-time-to-recovery. Python agent + Java control plane, all infrastructure in Terraform, all of AWS emulated locally so it runs from `docker compose up` with no cloud account.

Built to mirror the work of a **Database Site Reliability Engineer**: reliability problems solved with software, not manual effort.

---

## What it does

```
probe -> export metrics -> score for anomalies (ML) -> evaluate healing rules
      -> act -> open/resolve incident -> record MTTR -> repeat
```

- **Probes** a Postgres database (standing in for RDS/Aurora) for the signals that predict incidents: connection utilization, sessions stuck idle-in-transaction, replica lag, query latency.
- **Detects anomalies** with an **Isolation Forest** over the whole signal vector — catching subtle combinations no single threshold would.
- **Heals automatically**: codified rules terminate leaked sessions and relieve connection pressure in seconds, with an observe-only safety mode.
- **Owns SLOs & error budgets**: a Java control plane reads SLO definitions from DynamoDB and live counts from Prometheus, and computes availability, error budget, and burn rate.
- **Is fully observable**: Prometheus metrics for every signal and action, a Grafana reliability dashboard, and CloudWatch alarms as code.

---

## Why it exists / who it's for

This project is aimed squarely at an **AWS Database SRE / Platform Services** role. Every capability maps to a real requirement — see the full table in [docs/architecture.md](docs/architecture.md):

| Requirement | How db-sentinel demonstrates it |
|---|---|
| Self-healing automation | Rule-driven healing engine (`sentinel/healing.py`) |
| Python **and** Java | Python agent + Java Spring Boot control plane |
| SLOs, error budgets, MTTR | `ErrorBudget.compute`, `dbs_mttr_seconds`, `GET /api/v1/slo` |
| AWS (DynamoDB, CloudWatch) | boto3 + AWS SDK for Java, provisioned by Terraform |
| AI/ML in the design | Isolation Forest anomaly detection |
| Infrastructure as code | Terraform for every cloud resource |
| Observability (Prometheus/Grafana) | Metrics, dashboard, alarms |

---

## Quickstart

Prerequisites: Docker (Compose v2), and — for local development outside containers — Python 3.12, JDK 21, Terraform. `curl` + `jq` for the demo.

```bash
# 1. Bring up everything: database, LocalStack (AWS), sentinel, control-plane, Prometheus, Grafana
make up

# 2. Provision the AWS resources (DynamoDB tables, CloudWatch alarms) in LocalStack
make tf-init
make tf-apply

# 3. Check the reliability status (SLOs + error budgets)
make slo
```

Landmarks:
- Control-plane API — <http://localhost:8080/api/v1/slo>
- Sentinel metrics + admin — <http://localhost:9200/metrics>
- Grafana → **Reliability — db-sentinel** dashboard — <http://localhost:3000>
- Prometheus — <http://localhost:9090>

---

## The money demo: watch it heal itself

This is the thing to show in an interview. In one terminal, watch the dashboard (or tail the logs):

```bash
make logs
```

In another, inject a connection-leak fault — 90 sessions left idle-in-transaction:

```bash
make chaos
```

Within a couple of probe cycles you'll see, end to end:
1. `dbs_idle_in_transaction` spikes and the **anomaly score** jumps.
2. An **incident opens** (`dbs_incidents_opened_total`).
3. The healing engine **terminates the leaked sessions** (`dbs_healing_actions_total{action="kill_idle_in_transaction"}`).
4. The next healthy cycle **resolves the incident** and records **MTTR** (`dbs_mttr_seconds`).

No human touched it. That's the whole point.

---

## Running the tests

```bash
make test-sentinel   # Python: healing rules + ML anomaly detector (no DB needed)
make test-java       # Java: error-budget math
```

- `sentinel/tests/test_healing.py` — every healing rule as a pure function.
- `sentinel/tests/test_anomaly.py` — the detector stays quiet during warm-up and flags a real outlier once trained.
- `control-plane/.../ErrorBudgetTest.java` — error-budget and burn-rate math, including the breach case.

---

## Repo layout

```
db-sentinel/
├── docker-compose.yml        # database + LocalStack + sentinel + control-plane + observability
├── Makefile                  # up / tf-apply / chaos / slo / test-*
│
├── infra/
│   ├── terraform/            # DynamoDB tables, CloudWatch alarms, SLO seeds (LocalStack or real AWS)
│   ├── postgres/init.sql     # the app database the platform watches
│   ├── prometheus/           # scrape config
│   └── grafana/              # provisioned datasource + Reliability dashboard
│
├── sentinel/                 # THE AGENT (Python)
│   └── sentinel/
│       ├── main.py           # control loop + /metrics /health /admin/chaos
│       ├── probes.py         # read health signals from the database
│       ├── anomaly.py        # Isolation Forest anomaly detection
│       ├── healing.py        # rule-driven self-healing (the core)
│       ├── aws.py            # incidents in DynamoDB (boto3)
│       ├── chaos.py          # fault injection for the demo
│       ├── metrics.py        # Prometheus instruments
│       └── config.py
│
├── control-plane/            # THE CONTROL PLANE (Java / Spring Boot)
│   └── src/main/java/com/dbsentinel/
│       ├── slo/              # ErrorBudget (pure math), SloService, DynamoDB + Prometheus gateways
│       ├── api/SloController.java
│       └── config/AwsConfig.java
│
├── docs/
│   ├── architecture.md       # diagrams + requirement-to-code map
│   └── adr/                  # 5 ADRs
│
└── .github/workflows/ci.yml  # python + java + terraform pipelines
```

---

## Going to real AWS

Everything defaults to LocalStack so it's free. To target a real account:

- **Terraform:** `terraform apply -var use_localstack=false` with real credentials configured.
- **Apps:** unset `AWS_ENDPOINT_URL`; the SDKs fall back to the default credential chain.

No code changes — the resource definitions and API calls are identical. The managed database would become a real RDS/Aurora instance (a `db.t3.micro` is Free Tier eligible).

---

## Roadmap

- [x] Probe → anomaly detection → self-healing loop
- [x] SLOs + error budgets + MTTR
- [x] Terraform (DynamoDB, CloudWatch) on LocalStack
- [x] Prometheus + Grafana + CI (python/java/terraform)
- [ ] More healing rules: runaway-query termination, autovacuum pressure, disk-fill projection
- [ ] Rolling-window PromQL so error budgets reflect the true SLO window
- [ ] Alertmanager wiring so burn-rate alerts actually page
- [ ] A second target engine (DynamoDB throttling / hot-partition detection)
- [ ] Real-AWS Terraform module with remote state (S3 + DynamoDB lock)

## License

MIT — see [LICENSE](LICENSE).
