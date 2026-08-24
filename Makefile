.PHONY: help up down clean logs tf-init tf-apply tf-destroy test-sentinel test-java chaos slo

help:
	@echo "Targets:"
	@echo "  up           Start the full stack (database, LocalStack, sentinel, control-plane, observability)"
	@echo "  down         Stop containers (keep volumes)"
	@echo "  clean        Stop and remove volumes"
	@echo "  logs         Tail all logs"
	@echo "  tf-init      terraform init (points at LocalStack)"
	@echo "  tf-apply     Provision DynamoDB tables + CloudWatch alarms in LocalStack"
	@echo "  tf-destroy   Tear the Terraform-managed resources down"
	@echo "  test-sentinel  Run the Python agent's unit tests"
	@echo "  test-java    Run the control-plane's tests"
	@echo "  chaos        Inject a fault to watch self-healing kick in"
	@echo "  slo          Print the current SLO / error-budget status"

up:
	docker compose up -d --build
	@echo "-> Control-plane API: http://localhost:8080/api/v1/slo"
	@echo "-> Sentinel metrics:  http://localhost:9200/metrics"
	@echo "-> Grafana:           http://localhost:3000  (Reliability dashboard)"
	@echo "-> Prometheus:        http://localhost:9090"

down:
	docker compose down

clean:
	docker compose down -v

logs:
	docker compose logs -f --tail=120 sentinel control-plane

tf-init:
	cd infra/terraform && terraform init

tf-apply:
	cd infra/terraform && terraform apply -auto-approve

tf-destroy:
	cd infra/terraform && terraform destroy -auto-approve

test-sentinel:
	cd sentinel && python -m pytest -q

test-java:
	cd control-plane && ./mvnw -q test

chaos:
	@echo "Injecting a connection-exhaustion fault..."
	curl -sf -X POST http://localhost:9200/admin/chaos \
	  -H 'Content-Type: application/json' \
	  -d '{"fault":"connection_flood","magnitude":90}' | jq

slo:
	curl -sf http://localhost:8080/api/v1/slo | jq
