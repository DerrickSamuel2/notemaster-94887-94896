# Supabase Integration Documentation for notes_backend

This backend connects to a Supabase PostgreSQL database to persist notes for the Notes application.

## Configuration

Add the following environment variables (via a `.env` or deployment environment):

- `SUPABASE_URL`: The Supabase project URL (e.g., `https://qgmcdylmdodofjpuuklq.supabase.co`)
- `SUPABASE_KEY`: The Supabase API service key (private; keep this secret!)

These are loaded at runtime via python-dotenv and os.environ.

## Install Supabase Python Client

Add to `requirements.txt`:
```
supabase==2.0.5
```

## Table Schema

Supabase project should have a table named `notes` with:

| Column   | Type    | Description                   |
|----------|---------|-------------------------------|
| id       | integer | Primary Key, auto-increment   |
| title    | text    | Note title (required)         |
| content  | text    | Note body/content             |

Example SQL for creation:
```sql
CREATE TABLE notes (
    id serial PRIMARY KEY,
    title text NOT NULL,
    content text
);
```

## Usage in FastAPI

- The application uses `supabase-py` to perform CRUD against the Supabase table.
- The connection is established per request using credentials from environment variables.
- Ensure your project/database credentials are correct!

## Security Note

Do **NOT** expose your Supabase service key publicly.
Keep backend and frontend deployments secured and keys private.
