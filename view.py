from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from database.database import db, User  # Import User and db
import uuid


views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return redirect(url_for('dashboard.dashboard'))

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password:
            # Invalidate any existing session
            if user.session_id:
                session.pop(user.session_id, None)
            
            # Generate a new session ID
            new_session_id = str(uuid.uuid4())
            user.session_id = new_session_id
            db.session.commit()
            
            # Store the session ID in the session
            session['session_id'] = new_session_id
            
            login_user(user)
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('loginmodule/login.html')

@views.route('/logout')
def logout():
    if current_user.is_authenticated:
        current_user.session_id = None
        db.session.commit()
        logout_user()
    return redirect(url_for('views.login'))


@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return redirect(url_for('views.register'))

        admin_exists = User.query.filter_by(role=1).first()
        role = 0 if admin_exists else 1
        new_user = User(username=username, name=name, role=role, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('views.login'))

    return render_template('loginmodule/register.html')
