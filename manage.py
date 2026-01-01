from app import create_app, db
from app.models import *
from app.seed import seed_admin, seed_dummy_student
app = create_app()
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_admin()
        seed_dummy_student()
        print("DB initialized; admin teacher + dummy student seeded.")
