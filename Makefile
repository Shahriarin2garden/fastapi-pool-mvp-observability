.PHONY: lint preflight up down ps test traffic verify smoke k8s-up k8s-down alert-test demo evidence dashboards zip clean
lint:
	python3 scripts/lint-repo.py
preflight:
	bash scripts/preflight-ubuntu.sh
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
k8s-up:
	bash scripts/k8s-up.sh
k8s-down:
	bash scripts/k8s-down.sh
alert-test:
	bash scripts/alert-test.sh
demo:
	bash scripts/demo.sh
verify:
	bash scripts/verify.sh
smoke:
	bash scripts/ci-smoke.sh
evidence:
	bash scripts/collect-evidence.sh
dashboards:
	python scripts/generate_dashboards.py
zip:
	bash scripts/make-zip.sh CANDIDATE_ID
clean:
	@echo "Destructive: this removes named volumes. Use CONFIRM=yes."
	@test "$(CONFIRM)" = "yes"
	docker compose down -v
