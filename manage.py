from app import create_app, db
from app.models import *
from app.seed import seed_all

app = create_app()
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_all()
        print("DB initialized; admin teacher + dummy student seeded.")
