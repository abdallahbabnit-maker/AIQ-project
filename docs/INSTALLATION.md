# AIQ — Installation on Termux (Android)

## Prerequisites
- Termux app
- PostgreSQL (pkg install postgresql)
- Python 3.11+

## Setup
1. pg_ctl -D "$PREFIX/var/lib/postgresql" start
2. cd ~/aiq
3. pip install -r requirements.txt
4. alembic upgrade head
5. PYTHONPATH=. python3 scripts/create_founder.py

## Run
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

## Test
python3 -m pytest tests -q
python3 scripts/smoke_api.py

## Stop server
pkill -f "uvicorn app.main"
