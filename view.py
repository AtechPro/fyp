from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user
from database.database import db, User, Feedback  # Import User and db

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("home.html")

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        found_user = User.query.filter_by(username=username).first()

        if found_user and found_user.password == password:  # Consider using hashed passwords
            login_user(found_user)
            session.permanent = True  # Make the session permanent
            return redirect(url_for('views.home'))
        else:
            flash('Incorrect username or password. Please try again.', 'error')  # Flash error message
            return redirect(url_for('views.login'))

    return render_template('loginmodule/login.html')

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


@views.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('views.login'))
