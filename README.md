# QuantumDX

Hybrid quantum-classical ML platform for early disease detection (SIH PS 26139, Egreen Quanta).

> **Research Prototype — Not for Clinical Diagnosis.** Uses public benchmark data only.
> Quantum models run on a simulator. No claim of clinical validity, compliance, or absolute security.

## Status
Phase 1 (repo + dev environment) complete. See `docs/adr/0001-stack-and-versions.md`.

## Dev setup
```bash
cp .env.example .env            # then fill DATABASE_URL, SECRET_KEY, MODEL_SIGNING_KEY, POSTGRES_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(48))"   # run twice: two DIFFERENT secrets
docker compose -f docker-compose.dev.yml --env-file .env up -d db
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python ../scripts/phase0_verify.py   # must print PHASE0 QUANTUM SMOKE TEST: PASS
pytest
uvicorn app.main:app --reload       # GET http://127.0.0.1:8000/health
```
Frontend scaffold is created in Phase 1b/17 using the *current* official Next.js docs (not from memory).
Secret scan: `python scripts/scan_secrets.py` (working tree) and `gitleaks detect` (history).
