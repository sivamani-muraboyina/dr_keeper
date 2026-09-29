.PHONY: install setup api ui test eval up down
PY ?= python
export PYTHONPATH := src

install:            ## deps + spaCy model
	$(PY) -m pip install -r requirements.txt && $(PY) -m spacy download en_core_web_lg
setup:              ## load data + pgvector schema + embeddings into a running local Postgres
	$(PY) scripts/bootstrap.py
api:
	$(PY) -m uvicorn ehr.api:app --port 8000
ui:
	$(PY) -m streamlit run ui/app.py
test:
	$(PY) -m pytest -q tests
eval:               ## measured redaction / guardrail / latency numbers
	$(PY) scripts/07_evaluate.py
up:                 ## full stack in Docker
	docker compose up --build
down:
	docker compose down
