import os
import json
from pathlib import Path

from .models import db, User, Role, Assignment
from .assignment_store import save_assignment, assignments_dir


def seed_admin():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        return

    if not User.query.filter_by(email=email).first():
        u = User(
            email=email,
            name="Admin Teacher",
            role=Role.TEACHER,
            username=email.split("@")[0],
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()


def seed_dummy_student():
    email = os.getenv("STUDENT_EMAIL", "student@example.com")
    password = os.getenv("STUDENT_PASSWORD", "Stud3nt!123")
    if not User.query.filter_by(email=email).first():
        u = User(email=email, name="Test Student", role=Role.STUDENT, username="student")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()


def seed_assignments_from_json():
    """
    Seeds assignment JSON files into the app JSON store.

    Input folder:
      - ENV ASSIGNMENT_SEED_DIR (default: "seed_assignments")
      - Or you can place JSON files anywhere and set ASSIGNMENT_SEED_DIR to that path.

    Each JSON must contain:
      - id (int)
      - owner_id (int)
      - title (str)
      - description (str)
      - starter_code (str)
      - tests_path (null/str)
      - mark_scheme (obj/null)
    """
    seed_dir = Path(os.getenv("ASSIGNMENT_SEED_DIR", "seed_assignments"))
    if not seed_dir.exists() or not seed_dir.is_dir():
        # Nothing to seed; silently return (keeps setup smooth)
        return

    # Ensure destination folder exists
    out_dir = assignments_dir()

    for fp in sorted(seed_dir.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[seed] SKIP {fp} (invalid json): {e}")
            continue

        # Required fields
        missing = [k for k in ("id", "owner_id", "title") if k not in data]
        if missing:
            print(f"[seed] SKIP {fp} (missing keys: {missing})")
            continue

        aid = int(data["id"])
        owner_id = int(data["owner_id"])

        # 1) Ensure DB index row exists (for relationships)
        a = Assignment.query.get(aid)
        if not a:
            a = Assignment(id=aid, owner_id=owner_id)

            # If your current Assignment model still has required detail columns,
            # populate them from JSON so DB constraints don't fail.
            if hasattr(Assignment, "title"):
                a.title = data.get("title", f"Assignment {aid}")
            if hasattr(Assignment, "description_md"):
                a.description_md = data.get("description", "") or ""
            if hasattr(Assignment, "starter_code"):
                a.starter_code = data.get("starter_code", "") or ""
            if hasattr(Assignment, "tests_path"):
                a.tests_path = data.get("tests_path", None)
            if hasattr(Assignment, "mark_scheme_json"):
                ms = data.get("mark_scheme")
                a.mark_scheme_json = json.dumps(ms) if ms is not None else None

            db.session.add(a)
            db.session.commit()
            print(f"[seed] DB created Assignment id={aid} owner_id={owner_id}")
        else:
            # Keep owner_id consistent
            if getattr(a, "owner_id", None) != owner_id:
                a.owner_id = owner_id
                db.session.commit()
                print(f"[seed] DB updated owner_id for Assignment id={aid} -> {owner_id}")

        # 2) Save JSON into app store (source of truth for details)
        save_assignment(aid, data)
        print(f"[seed] JSON saved -> {out_dir}/assignment_{aid}.json")


def seed_all():
    """
    Call this from an app context.
    Example:
      from app.seed import seed_all
      seed_all()
    """
    seed_admin()
    seed_dummy_student()
    seed_assignments_from_json()