# WhatsApp Sender FastAPI Backend

Backend API for bulk WhatsApp message sending system.

## Stack
- FastAPI
- PostgreSQL
- Redis + RQ
- SQLAlchemy (async)

## Setup
```bash
# Install dependencies
poetry install

# Setup environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
make dev
```

## Architecture
See `docs/architecture.md` for details.
