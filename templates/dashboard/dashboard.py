import logging
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
import json
import time
from database.database import db, User, Sensor, SensorType

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a Blueprint for the dashboard
dashboardbp = Blueprint('dashboard', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MAX_MESSAGE_AGE = 10  # Maximum age of messages in seconds
MQTT_TOPIC = "home/#"

# MQTT Client
mqtt_client = mqtt.Client()
last_known_state = {}  # Stores the latest state of each device

# Initialize MQTT Client
def init_mqtt_client():
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        logger.info(f"Connected to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")

# MQTT on_connect callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect with return code {rc}")

# MQTT on_message callback
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("deviceId", "Unknown")
        if device_id not in last_known_state:
            last_known_state[device_id] = {"data": {}, "timestamp": time.time()}
        for key, value in payload.items():
            if key != "deviceId":
                last_known_state[device_id]["data"][key] = value
        last_known_state[device_id]["timestamp"] = time.time()
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# Dashboard Route
@dashboardbp.route('/dashboard')
@login_required
def dashboard():
    try:
        current_time = time.time()
        # Filter out stale messages
        filtered_data = {
            device_id: details["data"]
            for device_id, details in last_known_state.items()
            if current_time - details.get("timestamp", 0) <= MAX_MESSAGE_AGE
        }
        messages = filtered_data
    except Exception as e:
        logger.error(f"Error filtering dashboard messages: {e}")
        messages = {}
    user = User.query.filter_by(userid=current_user.userid).first()
    return render_template('dashboard/dashboard.html', messages=messages, user=user)

# Get Combined Sensor Data Route
@dashboardbp.route('/dashboard/sensor/<device_id>/<sensor_key>', methods=['GET'])
def get_combined_sensor_data(device_id, sensor_key):
    try:
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"

        # Fetch the sensor from the database
        sensor = Sensor.query.filter_by(device_id=device_id, sensor_key=sensor_key).first()
        if not sensor:
            return jsonify({
                "error": f"Sensor {sensor_key} not found for device {device_id}",
                "message": "This sensor is not registered in the database"
            }), 404

        # Fetch the sensor type details
        sensor_type = SensorType.query.get(sensor.sensor_type_id)
        if not sensor_type:
            return jsonify({
                "error": f"Sensor type not found for sensor {sensor_key}",
                "message": "This sensor type is not registered in the database"
            }), 404

        # Check for real-time data from MQTT
        device_data = last_known_state.get(device_id, {}).get("data", {})
        response_data = {}

        if sensor_key in device_data:
            # Real-time data is available
            value = device_data[sensor_key]
            if sensor_type.states:  # Check if this is a status sensor
                if value not in sensor_type.states:
                    value = 'UNKNOWN'
                response_data = {
                    "sensor_key": sensor_key,
                    "sensor_type": sensor_type.display_name,
                    "value": value,
                    "unit": "N/A",
                    "source": "mqtt",
                    "last_seen": "real-time"
                }
            else:
                response_data = {
                    "sensor_key": sensor_key,
                    "sensor_type": sensor_type.display_name,
                    "value": value,
                    "unit": sensor_type.unit or 'N/A',
                    "source": "mqtt",
                    "last_seen": "real-time"
                }
        else:
            # Fall back to database data
            if sensor:
                value = sensor.value
                if sensor_type.states:  # Check if this is a status sensor
                    if value not in sensor_type.states:
                        value = 'UNKNOWN'
                    response_data = {
                        "sensor_key": sensor.sensor_key,
                        "sensor_type": sensor_type.display_name,
                        "value": value,
                        "unit": "N/A",
                        "source": "database",
                        "last_seen": sensor.last_seen
                    }
                else:
                    response_data = {
                        "sensor_key": sensor.sensor_key,
                        "sensor_type": sensor_type.display_name,
                        "value": value,
                        "unit": sensor_type.unit or 'N/A',
                        "source": "database",
                        "last_seen": sensor.last_seen
                    }
            else:
                return jsonify({
                    "error": f"Sensor {sensor_key} not found for device {device_id}",
                    "message": "Data not available in real-time or database"
                }), 404

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in get_combined_sensor_data: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve sensor data",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

# Get All Sensors Route
@dashboardbp.route('/dashboard/sensors')
@login_required
def get_sensors():
    try:
        user = User.query.filter_by(userid=current_user.userid).first()
        sensors = Sensor.query.filter_by(userid=user.userid).all()
        sensor_list = []
        for sensor in sensors:
            sensor_type = SensorType.query.get(sensor.sensor_type_id)
            sensor_list.append({
                "sensor_id": sensor.id,
                "sensor_type": sensor_type.display_name,
                "value": sensor.value,
                "status": sensor.status,
                "unit": sensor_type.unit or 'N/A'
            })
        return jsonify(sensor_list)
    except Exception as e:
        logger.error(f"Error in get_sensors: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve sensor list",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

# Initialize MQTT client when the module is loaded
init_mqtt_client()