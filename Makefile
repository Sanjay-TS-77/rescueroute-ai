.PHONY: test eval serve smoke preflight

test:
	pytest -q

eval:
	python -m rescueroute.evaluate

serve:
	uvicorn rescueroute.web:app --host 0.0.0.0 --port 8000

smoke:
	python scripts/smoke_test.py

preflight:
	python scripts/preflight.py
