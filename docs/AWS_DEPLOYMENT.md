# AWS Deployment Notes

The Docker Compose stack was deployed and tested on one EC2 instance during development. The instance was terminated after validation to avoid ongoing infrastructure costs.

## Deployment Shape

The application runs as three Compose services: Postgres with pgvector, FastAPI, and Streamlit. Expose only Streamlit port `8501` publicly. Keep Postgres port `5432` and FastAPI port `8000` private to the host or VPC.

## Tested Setup

1. Configure an AWS security group with SSH `22` restricted to the operator's IP and Streamlit `8501` restricted as appropriate. Do not expose `5432` or `8000` publicly.
2. Use Ubuntu 24.04 on an EC2 instance. A 4 GB instance is sufficient for the default hash/mock configuration; semantic embeddings require more memory and storage.
3. Install Docker, clone the repository, copy `.env.example` to `.env`, and configure `LLM_*`, `API_KEY`, and a strong `DB_PASSWORD`.
4. Start the stack:

   ```bash
   docker compose up -d --build
   ```

5. Verify `http://<EC2_IP>:8501` and the private API health endpoint.
6. Stop or terminate the instance when it is not in use. Release any Elastic IP and remove unused volumes to avoid residual charges.

## Production Hardening Still Required

- HTTPS through a reverse proxy or load balancer.
- Secrets Manager or an equivalent secret store instead of `.env` on the host.
- CloudWatch logging and alerting.
- Enterprise identity, RBAC, and authenticated audit subjects.
- Private networking and managed backups for the database.
- A formal security, privacy, and compliance review before handling real PHI.