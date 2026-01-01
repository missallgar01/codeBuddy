# Flask Classroom — Plus

A self-hosted Python coding classroom with:
- Teacher/Student roles, class invite codes
- Assignment create/edit/delete, Markdown + image uploads (paste + resize)
- Monaco editor with Run + Submit, student **Save Draft**
- Automated tests (JSON mark scheme) with ✓/✗ table and totals
- Teacher rubric criteria + feedback + final grade
- Teacher can create student accounts (first/last/username), generate temp passwords, **export PDF** credentials
- SQLite + Docker
  
## Quickstart
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py
# open http://localhost:8000
```
**Docker DB path:** `DATABASE_URL=sqlite:////app/instance/classroom.db`

## Default accounts
- Admin Teacher (.env): `ADMIN_EMAIL` / `ADMIN_PASSWORD`
- Dummy Student: `student@example.com` / `Stud3nt!123`

## Notes
- We use plain forms (no Flask-WTF). CSRF disabled via `.env`.
- Image pasting inserts `<img ... style="width:480px;">`. Double-click inside the description box to change width (e.g. `320px` or `50%`).

