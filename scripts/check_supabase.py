"""
Simple DB connectivity checker — safe to run locally after you set DATABASE_URL in your environment.
Do NOT hardcode secrets in files.

Usage:
. .\.venv\Scripts\Activate.ps1
$env:DATABASE_URL = "postgresql://user:pass@host:5432/dbname?sslmode=require"
python scripts\check_supabase.py
"""
import os
import sys
import sqlalchemy

url = os.getenv('DATABASE_URL')
if not url:
    print('DATABASE_URL is not set. Set it in your shell or .env and retry.')
    sys.exit(2)

print('Testing connection to:', url.split('@')[-1])
try:
    engine = sqlalchemy.create_engine(url)
    with engine.connect() as conn:
        r = conn.execute(sqlalchemy.text('SELECT 1'))
        print('Query result:', list(r))
    print('OK: Connected to database')
except Exception as e:
    print('ERROR: could not connect to database:', e)
    sys.exit(1)
