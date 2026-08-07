# Migrations

Schema is managed by Alembic. Migrations are hand-written SQL (no ORM autogen).

## Commands

```bash
# from backend/
alembic upgrade head            # apply all pending migrations
alembic downgrade -1            # roll back one
alembic current                 # show current revision
alembic history                 # list all revisions
alembic revision -m "add foo"   # new empty migration
```

## First-time setup

- **Fresh DB:** `alembic upgrade head`
- **Existing DB with the old init_db.sql already applied:**
  `alembic stamp 0001 && alembic upgrade head`
  (`stamp` marks 0001 as applied without running it, since the tables already exist.)

## Config

`alembic/env.py` pulls `DATABASE_URL` from `trialmind.config.get_settings()` —
no need to set `sqlalchemy.url` in `alembic.ini`.
