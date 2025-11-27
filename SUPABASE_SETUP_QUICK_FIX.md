# Supabase Deprecated

Supabase has been removed from this project. Authentication now runs on **Firebase Auth** and data persistence is handled by **Cloud SQL (Postgres)** behind the `/api` routes.

## What to do instead

1. Configure Firebase client + admin keys in `.env.local` (see `env.example`).
2. Point `DATABASE_URL` (or `POSTGRES_*` vars) at your Cloud SQL Postgres instance.
3. Deploy with `firebase deploy` to Firebase Hosting (Next.js frameworks backend is enabled in `firebase.json`).

If you still have local Supabase data, export it and import into Cloud SQL tables (`user_storage`, `overhead_employees`) using `cloudsql_schema.sql`.
