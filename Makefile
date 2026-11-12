.PHONY: lint preflight up down ps test traffic verify smoke k8s-up k8s-down alert-test demo evidence dashboards zip clean aws-bootstrap aws-up aws-deploy aws-down ec2-up ec2-stop ec2-resume ec2-destroy lightsail-up lightsail-stop lightsail-resume lightsail-destroy
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
CANDIDATE_ID ?=
zip:
	@test -n "$(CANDIDATE_ID)" || { echo "usage: make zip CANDIDATE_ID=<candidate-id>" >&2; exit 2; }
	bash scripts/make-zip.sh "$(CANDIDATE_ID)"
clean:
	@echo "Destructive: this removes named volumes. Use CONFIRM=yes."
	@test "$(CONFIRM)" = "yes"
	docker compose down -v
aws-bootstrap:
	bash scripts/aws-bootstrap.sh $(EMAIL) $(REPO)
aws-up:
	AWS_UP_YES=$(AWS_UP_YES) bash scripts/aws-up.sh
aws-deploy:
	bash scripts/aws-deploy.sh
aws-down:
	CONFIRM=$(CONFIRM) bash scripts/aws-down.sh
ec2-up:
	AWS_EC2_YES=$(AWS_EC2_YES) bash scripts/ec2-up.sh
ec2-stop:
	bash scripts/ec2-stop.sh
ec2-resume:
	bash scripts/ec2-resume.sh
ec2-destroy:
	CONFIRM=$(CONFIRM) bash scripts/ec2-destroy.sh
lightsail-up:
	bash scripts/lightsail-up.sh
lightsail-stop:
	bash scripts/lightsail-stop.sh
lightsail-resume:
	bash scripts/lightsail-resume.sh
lightsail-destroy:
	CONFIRM=$(CONFIRM) bash scripts/lightsail-destroy.sh
