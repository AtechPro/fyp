from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, login_required, logout_user, current_user
from database.database import db, User, Report  # Import User and db

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template("dashboard.html")

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        found_user = User.query.filter_by(username=username).first()

        if found_user and found_user.password == password:
            login_user(found_user)
            session.permanent = True  # Make the session permanent
            return redirect(url_for('views.home'))
        else:
            flash('Invalid username or password')
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

        flash('Registration successful')
        return redirect(url_for('views.login'))

    return render_template('loginmodule/register.html')


@views.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        report_title = request.form['report_title']
        report_desc = request.form['report_desc']
        new_report = Report(userid=current_user.userid, username=current_user.username, report_title=report_title, report_desc=report_desc)
        db.session.add(new_report)
        db.session.commit()
        flash('Report submitted successfully')
        return redirect(url_for('views.report'))
    return render_template('report.html')


@views.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('views.login'))



"""
@views.route('/backup-restore')
def backup_restore():
    return render_template('backup_restore.html')

@views.route('/automation-rule')
def automation_rule():
    return render_template('automation_rule.html')

@views.route('/user-management')
def user_management():
    return render_template('user_management.html')

@views.route('/device-management')
def device_management():
    return render_template('device_management.html')

@views.route('/zone-management')
def zone_management():
    return render_template('zone_management.html')

@views.route('/timer-scheduler')
def timer_scheduler():
    return render_template('timer_scheduler.html')

"""



