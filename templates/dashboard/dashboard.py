from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
import requests
from database.database import db, User  # Importing database and User model

dashboardbp = Blueprint('dashboard', __name__)

@dashboardbp.route('/dashboard')
@login_required  # Ensures that only logged-in users can access this route
def dashboard():
    # Fetch MQTT messages
    try:
        response = requests.get('http://localhost:5000/mqtt/messages')  # Adjust the URL if necessary
        messages = response.json()
    except Exception as e:
        messages = []

    # Fetch user information from the database (if needed)
    user = User.query.filter_by(userid=current_user.userid).first()

    return render_template('dashboard/dashboard.html', messages=messages, user=user)
