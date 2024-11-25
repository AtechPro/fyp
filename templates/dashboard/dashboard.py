from flask import Blueprint, render_template, jsonify
import requests

dashboardbp = Blueprint('dashboard', __name__)

@dashboardbp.route('/dashboard')
def dashboard():
    # Fetch MQTT messages
    try:
        response = requests.get('http://localhost:5000/mqtt/messages')  # Adjust the URL if necessary
        messages = response.json()
    except Exception as e:
        messages = []

    return render_template('dashboard/dashboard.html', messages=messages)
