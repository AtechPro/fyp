from flask import Blueprint, jsonify, request
from flask_login import login_required
from database.database import db
from datetime import datetime, timedelta
import threading
import paho.mqtt.client as mqtt
import logging

dashboardbp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
mqtt_client = mqtt.Client()
mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT, 60)

# Add a new timer
@dashboardbp.route('/timer/add', methods=['POST'])
@login_required
def add_timer():
    data = request.json
    name = data['name']
    device_id = data['deviceId']
    start_time = datetime.fromisoformat(data['startTime'])
    duration = int(data['duration'])
    action = data['action']

    # Save to database
    timer = Timer(name=name, device_id=device_id, start_time=start_time, duration=duration, action=action)
    db.session.add(timer)
    db.session.commit()

    # Start a thread to handle the timer
    threading.Thread(target=handle_timer, args=(timer,)).start()

    logger.info(f"Timer '{name}' scheduled for device '{device_id}'.")
    return jsonify({'success': True})

# Get all active timers
@dashboardbp.route('/timer/get', methods=['GET'])
@login_required
def get_timers():
    timers = Timer.query.all()
    timer_list = [{
        'name': timer.name,
        'deviceId': timer.device_id,
        'startTime': timer.start_time.isoformat(),
        'duration': timer.duration,
        'action': timer.action,
    } for timer in timers]

    return jsonify(timer_list)

# Handle timer expiration
def handle_timer(timer):
    time_to_wait = (timer.start_time - datetime.now()).total_seconds()
    if time_to_wait > 0:
        time.sleep(time_to_wait)

    # Publish MQTT action
    mqtt_client.publish(f"home/{timer.device_id}/action", json.dumps({'action': timer.action}))
    logger.info(f"Timer '{timer.name}' triggered for device '{timer.device_id}' with action '{timer.action}'.")

    # Remove timer from database
    db.session.delete(timer)
    db.session.commit()
