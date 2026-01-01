from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from .models import db, User, Role, Class, Enrollment
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_username = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        # allow username or email
        user = User.query.filter((User.email==email_or_username)|(User.username==email_or_username)).first()
        if not user or not user.check_password(password):
            flash('Invalid credentials', 'danger')
        else:
            login_user(user)
            return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        join_code = request.form.get('join_code', '').strip()
        if not name or not email or not password:
            flash('Please fill in name, email and password.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('register.html')
        u = User(email=email, name=name, role=Role.STUDENT, username=email.split('@')[0])
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        if join_code:
            klass = Class.query.filter_by(code=join_code).first()
            if klass:
                db.session.add(Enrollment(class_id=klass.id, student_id=u.id))
                db.session.commit()
                flash(f"Joined class: {klass.name}", 'info')
            else:
                flash('Invite code not found. You can try again later.', 'warning')
        login_user(u)
        return redirect(url_for('main.dashboard'))
    return render_template('register.html')

@auth_bp.route('/register-teacher', methods=['GET', 'POST'])
def register_teacher():
    token_env = os.getenv('TEACHER_INVITE_TOKEN')
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        token = request.form.get('invite_token', '').strip()
        if not token_env:
            flash('Teacher registration is disabled.', 'danger')
            return render_template('register_teacher.html')
        if token != token_env:
            flash('Invalid invite token.', 'danger')
            return render_template('register_teacher.html')
        if User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return render_template('register_teacher.html')
        u = User(email=email, name=name, role=Role.TEACHER, username=email.split('@')[0])
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash('Teacher account created. Please sign in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register_teacher.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
