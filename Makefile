COMPOSE := docker compose -f infra/compose/docker-compose.yml

.PHONY: up down reset eval build ps logs verify

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v

eval:
	$(COMPOSE) run --rm eval python3 /app/eval/harness.py

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

verify:
	$(COMPOSE) exec clickhouse clickhouse-client --password clickhouse --query "SELECT ServiceName, MetricName, count() AS rows FROM telemetry.otel_metrics_sum GROUP BY ServiceName, MetricName ORDER BY ServiceName, MetricName"
