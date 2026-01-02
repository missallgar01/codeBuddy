import json, os, secrets
from datetime import datetime, timezone
from flask import current_app

def assignments_dir() -> str:
    d = os.path.join(current_app.root_path, "assignments")
    os.makedirs(d, exist_ok=True)
    return d

def assignment_path(aid: int) -> str:
    return os.path.join(assignments_dir(), f"assignment_{aid}.json")

def load_assignment(aid: int) -> dict | None:
    p = assignment_path(aid)
    if not os.path.exists(p):
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_assignment(aid: int, data: dict) -> None:
    p = assignment_path(aid)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def delete_assignment(aid: int) -> None:
    p = assignment_path(aid)
    if os.path.exists(p):
        os.remove(p)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ensure_assignment_json(aid: int, owner_id: int | None = None) -> dict:
    """
    Ensure there is a JSON file for this assignment.
    If missing, create a placeholder so templates/routes don't crash.
    """
    data = load_assignment(aid)
    if data:
        return data

    # Create a minimal placeholder
    data = {
        "id": aid,
        "owner_id": owner_id,
        "title": f"Assignment {aid}",
        "description": "",
        "starter_code": "",
        "tests_path": None,
        "mark_scheme": {"cases": []},
    }
    save_assignment(aid, data)
    return data