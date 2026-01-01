import json

def grade_submission_detailed(code: str, mark_scheme_json: str):
    if not mark_scheme_json:
        return [], 0.0, 0.0, False
    try:
        scheme = json.loads(mark_scheme_json)
    except Exception as e:
        return [{
            "index": 1, "function": None, "args": [], "kwargs": {},
            "expected": None, "got": None, "correct": False,
            "marks_awarded": 0.0, "marks_available": 0.0,
            "error": f"Invalid mark scheme JSON: {e}"
        }], 0.0, 0.0, False

    ns = {}
    rows = []
    try:
        exec(code, ns, ns)
    except Exception as e:
        cases = scheme.get("cases", [])
        for i, case in enumerate(cases, start=1):
            m = float(case.get("marks", 1))
            rows.append({
                "index": i, "function": case.get("function"), "args": case.get("args", []),
                "kwargs": case.get("kwargs", {}), "expected": case.get("expected"),
                "got": None, "correct": False, "marks_awarded": 0.0, "marks_available": m,
                "error": f"Code raised on import: {e}"
            })
        max_total = sum(float(c.get("marks", 1)) for c in cases)
        return rows, 0.0, max_total, False

    total = 0.0
    max_total = 0.0

    for i, case in enumerate(scheme.get("cases", []), start=1):
        func_name = case.get("function")
        args = case.get("args", [])
        kwargs = case.get("kwargs", {})
        expected = case.get("expected")
        marks_available = float(case.get("marks", 1))
        max_total += marks_available

        row = {
            "index": i, "function": func_name, "args": args, "kwargs": kwargs,
            "expected": expected, "got": None, "correct": False,
            "marks_awarded": 0.0, "marks_available": marks_available
        }

        try:
            func = ns.get(func_name)
            if not callable(func):
                row["error"] = f"Function '{func_name}' not found"
            else:
                got = func(*args, **kwargs)
                row["got"] = got
                if got == expected:
                    row["correct"] = True
                    row["marks_awarded"] = marks_available
                    total += marks_available
        except Exception as e:
            row["error"] = repr(e)

        rows.append(row)

    return rows, total, max_total, total == max_total


def grade_submission(code: str, mark_scheme_json: str):
    rows, total, max_total, passed = grade_submission_detailed(code, mark_scheme_json)
    lines = []
    for r in rows:
        prefix = "✅" if r["correct"] else "❌"
        msg = r.get("error")
        line = f"{prefix} Case {r['index']}: {r['function']}({r['args']})"
        if msg:
            line += f" — {msg}"
        else:
            line += f" expected {r['expected']!r}, got {r['got']!r}"
        lines.append(line)
    feedback = "\n".join(lines)
    return total, max_total, feedback, passed
