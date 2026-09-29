FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ml.txt ./
ARG WITH_ML=false
RUN pip install -r requirements.txt \
 && if [ "$WITH_ML" = "true" ]; then pip install -r requirements-ml.txt --extra-index-url https://download.pytorch.org/whl/cpu; fi

ARG SPACY_MODEL=en_core_web_lg
ENV SPACY_MODEL=${SPACY_MODEL}
RUN python -m spacy download ${SPACY_MODEL}

COPY . .
RUN chmod +x start.sh
EXPOSE 8000 8501
# default = single-container mode (like the live session); compose overrides per service
CMD ["./start.sh"]
