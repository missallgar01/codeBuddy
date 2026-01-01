# Stop the app
docker compose down

# Delete old DB
rm -f instance/classroom.db

# Recreate tables + seed admin/student
docker compose up -d
docker compose exec web python manage.py

