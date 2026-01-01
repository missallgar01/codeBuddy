import os
from .models import db, User, Role

def seed_admin():
    email = os.getenv('ADMIN_EMAIL')
    password = os.getenv('ADMIN_PASSWORD')
    if not email or not password:
        return
    if not User.query.filter_by(email=email).first():
        u = User(email=email, name='Admin Teacher', role=Role.TEACHER, username=email.split('@')[0])
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

def seed_dummy_student():
    email = os.getenv('STUDENT_EMAIL', 'student@example.com')
    password = os.getenv('STUDENT_PASSWORD', 'Stud3nt!123')
    if not User.query.filter_by(email=email).first():
        u = User(email=email, name='Test Student', role=Role.STUDENT, username='student')
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
