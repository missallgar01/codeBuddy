from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager

class Role:
    STUDENT = "student"
    TEACHER = "teacher"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(120), default="")
    last_name  = db.Column(db.String(120), default="")
    username   = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.STUDENT)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(16), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher = db.relationship('User', backref='classes_taught', foreign_keys=[teacher_id])

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    student = db.relationship('User', backref='enrollments', foreign_keys=[student_id])
    klass = db.relationship('Class', backref='enrollments', foreign_keys=[class_id])

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # DB no longer stores details (JSON only)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref='assignments')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Keep relationships (these still use assignment_id)
    class_assignments = db.relationship('ClassAssignment', cascade="all, delete-orphan", backref='assignment', lazy='dynamic')
    submissions = db.relationship('Submission', cascade="all, delete-orphan", backref='assignment', lazy='dynamic')
    rubric_criteria = db.relationship('RubricCriterion', cascade="all, delete-orphan", backref='assignment', lazy='dynamic')

class ClassAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    due_at = db.Column(db.DateTime, nullable=True)
    klass = db.relationship('Class', backref='class_assignments')

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    code = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Float, default=0.0)
    max_score = db.Column(db.Float, default=0.0)
    feedback = db.Column(db.Text, default="")
    passed = db.Column(db.Boolean, default=False)
    is_draft = db.Column(db.Boolean, default=False)
    # rubric + final
    teacher_feedback = db.Column(db.Text, default="")
    auto_score = db.Column(db.Float, default=0.0)
    auto_max = db.Column(db.Float, default=0.0)
    rubric_score = db.Column(db.Float, default=0.0)
    rubric_max = db.Column(db.Float, default=0.0)
    final_score = db.Column(db.Float, default=0.0)
    final_max = db.Column(db.Float, default=0.0)

    student = db.relationship('User', backref='submissions', foreign_keys=[student_id])

class RubricCriterion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'), nullable=False)
    key = db.Column(db.String(64), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=1.0)
    order_index = db.Column(db.Integer, nullable=False, default=0)

class RubricGrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    criterion_id = db.Column(db.Integer, db.ForeignKey('rubric_criterion.id'), nullable=False)
    awarded = db.Column(db.Float, nullable=False, default=0.0)
