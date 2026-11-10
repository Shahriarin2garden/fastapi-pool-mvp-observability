.PHONY: up down ps test traffic verify evidence dashboards zip
up:
	docker compose up -d --build
down:
	docker compose down
ps:
	docker compose ps
test:
	pytest
traffic:
	bash scripts/traffic-test.sh all
verify:
	bash scripts/verify.sh
evidence:
	bash scripts/collect-evidence.sh
dashboards:
	python scripts/generate_dashboards.py
zip:
	bash scripts/make-zip.sh CANDIDATE_ID
