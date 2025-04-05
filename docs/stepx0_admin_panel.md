# Admin panel

We don't have alembic migrations yet, so we need to create the database manually.

```bash
ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
```
Note "user" is a reserved keyword in Postgres, so we are quoting it.

