Deployment checklist — SkillNavigator

This file lists the steps and required environment variables to run SkillNavigator in production (supabase/Postgres on Render or similar).

1) Required environment variables (minimum for production)
- DATABASE_URL: Postgres connection string (e.g. postgresql://user:pass@host:5432/dbname?sslmode=require)
- SECRET_KEY: strong random secret for JWT and encryption
- OPENAI_API_KEY: API key for OpenAI (if ENABLE_AI_SCORING=true)
- EMAIL_HOST / EMAIL_PORT / EMAIL_USERNAME / EMAIL_PASSWORD: for SMTP (if email features enabled)

2) Optional but recommended
- FRONTEND_URL: frontend origin for CORS
- SENTRY_DSN: error tracking
- REDIS_URL: background task caching
- AWS_* or SUPABASE storage keys if using cloud storage for uploads

3) Postgres / Supabase notes
- Ensure `psycopg2-binary` is installed (it's listed in `requirements.txt`).
- For Supabase, use the provided Postgres connection string and append `?sslmode=require` if needed.
- Run migrations or allow SQLAlchemy to create tables at startup. You can run a one-off initializer:

  . \.venv\Scripts\Activate.ps1
  python -c "from backend.database.db_connection import database; import asyncio; asyncio.run(database.initialize())"

4) Deployment steps (Render example)
- Add repo to Render and set service as a Web Service.
- Set env vars on Render (DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, etc.).
- Build command: `pip install -r requirements.txt`
- Start command: `python run_backend.py`
- After deploy, check: `https://<YOUR_APP>/api/health` and `https://<YOUR_APP>/api/docs`

5) Smoke test sequence
- Register a test user via `/api/user/register`.
- Upload a resume via `/api/user/resume/{user_id}`.
- Update preferences via `/api/user/preferences/{user_id}` and confirm rescoring.
- Trigger a search via `/api/trigger-job-search` and inspect job insertion and scoring.

6) Security hardening
- Do not commit `.env` with secrets. Add `.env` to `.gitignore`.
- Restrict CORS to your frontend origin(s) in production.
- Rotate API keys and set least-privilege credentials on Supabase.

7) Backups and monitoring
- Enable backups in Supabase or schedule dumps.
- Configure log aggregation and alerts (Sentry/Prometheus).

If you want, I can:
- Add an Alembic migration scaffold and a tiny `manage.py` to run migrations.
- Create a `scripts/check_supabase.py` to test DB connectivity locally (requires you to set `DATABASE_URL` in env).

Tell me which of the above (migrations, connectivity tests, deploy run) you want me to implement next.
