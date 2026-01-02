import os, tempfile, shutil, subprocess, sys
from datetime import datetime
from io import BytesIO
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort, current_app, jsonify, send_from_directory, send_file
from flask_login import login_required, current_user
from markdown2 import markdown
import bleach, secrets
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from .models import db, User, Role, Class, Enrollment, Assignment, ClassAssignment, Submission, RubricCriterion, RubricGrade
from .grading import grade_submission, grade_submission_detailed

main_bp = Blueprint('main', __name__)

ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union({'p','img','h1','h2','h3','h4','h5','h6','pre','code','table','thead','tbody','tr','th','td'})
ALLOWED_ATTRS = {**bleach.sanitizer.ALLOWED_ATTRIBUTES, 'img': ['src', 'alt', 'style']}

def _allowed_image(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]

@main_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(folder, filename, as_attachment=False)

@main_bp.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    if current_user.role != Role.TEACHER:
        abort(403)
    if "images" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["images"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not _allowed_image(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    base = secure_filename(file.filename or f"pasted_{datetime.utcnow().timestamp()}.png")
    name, dot, ext = base.partition(".")
    i, final = 0, base
    while os.path.exists(os.path.join(folder, final)):
        i += 1
        final = f"{name}_{i}.{ext}" if ext else f"{name}_{i}"
    file.save(os.path.join(folder, final))
    url = url_for("main.uploaded_file", filename=final, _external=False)
    return jsonify({"url": url})

@main_bp.route('/')
@login_required
def dashboard():
    if current_user.role == Role.TEACHER:
        classes = Class.query.filter_by(teacher_id=current_user.id).all()
        assignments = Assignment.query.filter_by(owner_id=current_user.id).all()
        return render_template('teacher_dashboard.html', classes=classes, assignments=assignments)
    else:
        enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
        return render_template('student_dashboard.html', enrollments=enrollments)

@main_bp.route('/classes/create', methods=['GET','POST'])
@login_required
def class_create():
    if current_user.role != Role.TEACHER:
        abort(403)
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        c = Class(name=name, code=code, teacher_id=current_user.id)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('class_create.html')

@main_bp.route('/classes/join', methods=['POST'])
@login_required
def class_join():
    if current_user.role != Role.STUDENT:
        abort(403)
    code = request.form.get('code')
    klass = Class.query.filter_by(code=code).first()
    if not klass:
        flash('Invalid class code', 'danger')
    else:
        existing = Enrollment.query.filter_by(class_id=klass.id, student_id=current_user.id).first()
        if not existing:
            db.session.add(Enrollment(class_id=klass.id, student_id=current_user.id))
            db.session.commit()
            flash(f'Joined {klass.name}', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/assignments/create', methods=['GET','POST'])
@login_required
def assignment_create():
    if current_user.role != Role.TEACHER:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title')
        description = bleach.clean(request.form.get('description'), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
        starter = request.form.get('starter_code')
        tests_path = request.form.get('tests_path') or None
        mark_scheme_json = request.form.get('mark_scheme_json') or None
        a = Assignment(title=title, description_md=description, starter_code=starter,
                       tests_path=tests_path, mark_scheme_json=mark_scheme_json, owner_id=current_user.id)
        db.session.add(a)
        db.session.commit()
        flash('Assignment created', 'success')
        return redirect(url_for('main.assignment_detail', aid=a.id))
    return render_template('assignment_form.html', mode='create', assignment=None)

@main_bp.route('/assignments/<int:aid>/edit', methods=['GET','POST'])
@login_required
def assignment_edit(aid):
    if current_user.role != Role.TEACHER:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    if a.owner_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '')
        starter = request.form.get('starter_code', '')
        tests_path = request.form.get('tests_path') or None
        mark_scheme_json = request.form.get('mark_scheme_json') or None
        if not title:
            flash('Title is required.', 'danger')
            return render_template('assignment_form.html', mode='edit', assignment=a)
        description = bleach.clean(description, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)
        a.title = title
        a.description_md = description
        a.starter_code = starter
        a.tests_path = tests_path
        a.mark_scheme_json = mark_scheme_json
        db.session.commit()
        flash('Assignment updated.', 'success')
        return redirect(url_for('main.assignment_detail', aid=a.id))
    return render_template('assignment_form.html', mode='edit', assignment=a)

@main_bp.route('/assignments/<int:aid>/delete', methods=['POST'])
@login_required
def assignment_delete(aid):
    if current_user.role != Role.TEACHER:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    if a.owner_id != current_user.id:
        abort(403)
    db.session.delete(a)
    db.session.commit()
    flash('Assignment deleted.', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/assignments/<int:aid>', methods=['GET','POST'])
@login_required
def assignment_detail(aid):
    a = Assignment.query.get_or_404(aid)
    if current_user.role == Role.STUDENT:
        class_ids = [en.klass.id for en in current_user.enrollments]
        allowed = ClassAssignment.query.filter(ClassAssignment.assignment_id==aid, ClassAssignment.class_id.in_(class_ids)).first()
        if not allowed:
            abort(403)
    if request.method == 'POST' and current_user.role == Role.STUDENT:
        code = request.form.get('code')
        rows, total, max_total, passed = grade_submission_detailed(code, a.mark_scheme_json or '{"cases": []}')
        sub = Submission(assignment_id=aid, student_id=current_user.id, code=code,
                         score=total, max_score=max_total, feedback="",
                         passed=passed, is_draft=False, auto_score=total, auto_max=max_total)
        db.session.add(sub)
        db.session.commit()
        flash(f"Submitted. Score: {total}/{max_total}", 'info')
        return redirect(url_for('main.assignment_detail', aid=aid))
    description_html = markdown(a.description_md)

    last_rows = []
    last_total = 0.0
    last_max = 0.0
    last_rubric_rows, last_rubric_total, last_rubric_max = [], 0.0, 0.0

    if current_user.role == Role.STUDENT:
        sub = (Submission.query
               .filter_by(assignment_id=aid, student_id=current_user.id)
               .order_by(Submission.created_at.desc())
               .first())
        if sub and a.mark_scheme_json:
            last_rows, last_total, last_max, _ = grade_submission_detailed(sub.code, a.mark_scheme_json)
        if sub:
            crits = RubricCriterion.query.filter_by(assignment_id=a.id).order_by(RubricCriterion.order_index).all()
            gmap = {g.criterion_id: g.awarded for g in RubricGrade.query.filter_by(submission_id=sub.id).all()}
            for c in crits:
                aw = float(gmap.get(c.id, 0.0))
                last_rubric_rows.append({"label": c.label, "max": c.max_marks, "awarded": aw})
                last_rubric_total += aw
                last_rubric_max += float(c.max_marks)

    return render_template('assignment_detail.html',
                           assignment=a,
                           description_html=description_html,
                           last_rows=last_rows, last_total=last_total, last_max=last_max,
                           last_rubric_rows=last_rubric_rows,
                           last_rubric_total=last_rubric_total,
                           last_rubric_max=last_rubric_max)

@main_bp.route('/assignments/<int:aid>/assign', methods=['POST'])
@login_required
def assignment_assign(aid):
    if current_user.role != Role.TEACHER:
        abort(403)
    klass_id = int(request.form.get('class_id'))
    due = request.form.get('due_at')
    due_dt = datetime.fromisoformat(due) if due else None
    db.session.add(ClassAssignment(class_id=klass_id, assignment_id=aid, due_at=due_dt))
    db.session.commit()
    flash('Assigned to class', 'success')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/run_code', methods=['POST'])
@login_required
def run_code():
    data = request.get_json(force=True)
    code = (data or {}).get('code', '')
    timeout = 5
    workdir = tempfile.mkdtemp(prefix='run_')
    try:
        path = os.path.join(workdir, 'student.py')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        proc = subprocess.Popen([sys.executable, path], cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return jsonify({"error": "Execution timed out"})
        output = (stdout or '') + ('\n' + stderr if stderr else '')
        return jsonify({"output": output[:8000]})
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

@main_bp.route('/assignments/<int:aid>/save_draft', methods=['POST'])
@login_required
def save_draft(aid):
    if current_user.role != Role.STUDENT:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    class_ids = [en.klass.id for en in current_user.enrollments]
    allowed = ClassAssignment.query.filter(ClassAssignment.assignment_id==aid, ClassAssignment.class_id.in_(class_ids)).first()
    if not allowed:
        abort(403)
    data = request.get_json(force=True) or {}
    code = data.get("code", "")
    sub = Submission(assignment_id=aid, student_id=current_user.id, code=code, is_draft=True)
    db.session.add(sub)
    db.session.commit()
    return jsonify({"ok": True, "saved_at": sub.created_at.isoformat()})

# Rubric editor
@main_bp.route('/assignments/<int:aid>/rubric', methods=['GET', 'POST'])
@login_required
def rubric_edit(aid):
    if current_user.role != Role.TEACHER:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    if a.owner_id != current_user.id:
        abort(403)
    if request.method == 'POST':
        keys = request.form.getlist('key[]')
        labels = request.form.getlist('label[]')
        maxes = request.form.getlist('max_marks[]')
        orders = request.form.getlist('order_index[]')
        RubricCriterion.query.filter_by(assignment_id=a.id).delete(synchronize_session=False)
        for i in range(len(keys)):
            k = (keys[i] or f"crit_{i}").strip()
            l = (labels[i] or f"Criterion {i+1}").strip()
            try:
                m = float(maxes[i])
            except Exception:
                m = 1.0
            try:
                oi = int(orders[i])
            except Exception:
                oi = i
            db.session.add(RubricCriterion(assignment_id=a.id, key=k, label=l, max_marks=m, order_index=oi))
        db.session.commit()
        flash('Rubric updated.', 'success')
        return redirect(url_for('main.rubric_edit', aid=a.id))
    criteria = RubricCriterion.query.filter_by(assignment_id=a.id).order_by(RubricCriterion.order_index).all()
    return render_template('rubric_edit.html', assignment=a, criteria=criteria)

@main_bp.route('/assignments/<int:aid>/submissions')
@login_required
def submissions_list(aid):
    if current_user.role != Role.TEACHER:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    if a.owner_id != current_user.id:
        abort(403)
    subs = (Submission.query.filter_by(assignment_id=aid).order_by(Submission.created_at.desc()).all())
    return render_template('submissions_list.html', assignment=a, submissions=subs)

@main_bp.route('/assignments/<int:aid>/submissions/<int:sid>', methods=['GET','POST'])
@login_required
def submission_grade(aid, sid):
    if current_user.role != Role.TEACHER:
        abort(403)
    a = Assignment.query.get_or_404(aid)
    if a.owner_id != current_user.id:
        abort(403)
    sub = Submission.query.get_or_404(sid)
    rows, auto_total, auto_max, _ = grade_submission_detailed(sub.code, a.mark_scheme_json or '{"cases": []}')
    sub.auto_score = auto_total
    sub.auto_max = auto_max
    crits = RubricCriterion.query.filter_by(assignment_id=a.id).order_by(RubricCriterion.order_index).all()
    if request.method == 'POST':
        awarded_by_id = {}
        for c in crits:
            try:
                awarded_by_id[c.id] = max(0.0, min(c.max_marks, float(request.form.get(f"crit_{c.id}", "0"))))
            except Exception:
                awarded_by_id[c.id] = 0.0
        existing = { (g.submission_id, g.criterion_id): g for g in RubricGrade.query.filter_by(submission_id=sub.id).all() }
        for c in crits:
            key = (sub.id, c.id)
            g = existing.get(key)
            if not g:
                g = RubricGrade(submission_id=sub.id, criterion_id=c.id, awarded=awarded_by_id[c.id])
                db.session.add(g)
            else:
                g.awarded = awarded_by_id[c.id]
        sub.teacher_feedback = request.form.get('teacher_feedback', '').strip()
        rubric_total = sum(awarded_by_id.values())
        rubric_max = sum(c.max_marks for c in crits)
        sub.rubric_score = rubric_total
        sub.rubric_max = rubric_max
        sub.final_score = (sub.rubric_score or 0.0) + (sub.auto_score or 0.0)
        sub.final_max = (sub.rubric_max or 0.0) + (sub.auto_max or 0.0)
        db.session.commit()
        flash('Marks and feedback saved.', 'success')
        return redirect(url_for('main.submissions_list', aid=a.id))
    awarded_map = {g.criterion_id: g.awarded for g in RubricGrade.query.filter_by(submission_id=sub.id).all()}
    return render_template('submission_grade.html', assignment=a, sub=sub, criteria=crits, awarded_map=awarded_map, auto_rows=rows, auto_total=auto_total, auto_max=auto_max)

# Teacher manage students
@main_bp.route('/teacher/students', methods=['GET','POST'])
@login_required
def teacher_students():
    if current_user.role != Role.TEACHER:
        abort(403)
    created = None
    if request.method == 'POST':
        first = request.form.get('first_name','').strip()
        last  = request.form.get('last_name','').strip()
        username = request.form.get('username','').strip().lower()
        email = request.form.get('email','').strip().lower()
        password = secrets.token_urlsafe(8)
        if not username:
            flash('Username is required.', 'danger')
            return redirect(url_for('main.teacher_students'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('main.teacher_students'))
        display_name = f"{first} {last}".strip() or username
        u = User(email=email or f"{username}@example.local",
                 name=display_name, first_name=first, last_name=last,
                 username=username, role=Role.STUDENT)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        created = {"id": u.id, "username": u.username, "email": u.email, "password": password, "name": u.name}
        flash(f"Student {u.name} created.", 'success')
    students = User.query.filter_by(role=Role.STUDENT).order_by(User.last_name, User.first_name, User.email).all()
    return render_template('teacher_students.html', students=students, created=created)

@main_bp.route('/teacher/students/<int:uid>/credentials.pdf')
@login_required
def student_credentials_pdf(uid):
    if current_user.role != Role.TEACHER:
        abort(403)
    u = User.query.get_or_404(uid)
    if u.role != Role.STUDENT:
        abort(404)
    temp_pass = secrets.token_urlsafe(8)
    u.set_password(temp_pass)
    db.session.commit()
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, h-72, "Student Login Details")
    c.setFont("Helvetica", 12)
    y = h - 110
    lines = [
        f"Name: {u.name}",
        f"Username: {u.username or ''}",
        f"Email: {u.email}",
        f"Temporary Password: {temp_pass}",
        "",
        "Use these credentials to sign in and change your password after login."
    ]
    for line in lines:
        c.drawString(72, y, line); y -= 20
    c.showPage(); c.save(); buf.seek(0)
    filename = f"credentials_{u.username or u.id}.pdf"
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename)
