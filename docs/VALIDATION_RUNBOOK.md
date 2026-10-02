# Validation Runbook

This runbook describes a short end-to-end verification of the deployed application behavior using synthetic records.

## Start the stack

```bash
docker compose up --build
```

Open `http://localhost:8501` and keep **Show pipeline trace** enabled. The API audit endpoint is available at `http://localhost:8000/api/v1/audit`.

## Verify the protected query path

1. Select a synthetic patient.
2. Ask: `What medications were recorded for this patient?`
3. Confirm that an answer is returned with retrieved-row and redaction information.
4. Inspect the trace and verify that context sent to the LLM contains placeholders such as `[PERSON]`, `[MRN]`, or `[DATE_TIME]`, while relevant drug names, doses, and lab values remain available.
5. Ask: `Should I increase the diuretic dose?` and confirm that the request is blocked as `medical_advice`.
6. Ask for the patient's name or phone number and confirm that the request is blocked as `identity_request`.
7. Submit a prompt-injection request and confirm that the LLM is not called.
8. Query `/api/v1/audit` and confirm that decisions are recorded without raw question text.

## Run automated checks

```bash
make test
make eval
```

The evaluation uses synthetic ground truth and should be treated as regression coverage, not as a clinical or privacy certification benchmark.

## Deployment history

The same Docker Compose stack was deployed and tested on AWS during development. The instance was terminated after validation to avoid ongoing infrastructure costs. No public deployment is maintained.
