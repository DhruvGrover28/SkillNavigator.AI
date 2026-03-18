# Render deployment configuration
# Force Python runtime detection

build:
  - pip install -r requirements.txt

deploy:
  - cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT