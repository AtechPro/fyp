import os
import logging
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
import json
import time
from database.database import db, User, Sensor, SensorType, DashboardSensor



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
def on_message(_client, _userdata, msg):
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

# Initialize MQTT client when the module is loaded
def init_app(app):
    init_mqtt_client()
    app.before_first_request(init_mqtt_client)

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
@login_required
def get_combined_sensor_data(device_id, sensor_key):
    try:
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"

        # Check if the sensor exists in the database
        sensor = Sensor.query.filter_by(device_id=device_id, sensor_key=sensor_key).first()
        if not sensor:
            return jsonify({
                "error": f"Sensor {sensor_key} not found for device {device_id}",
                "message": "Sensor not found in the database"
            }), 404

        # Check for real-time data from MQTT
        device_data = last_known_state.get(device_id, {}).get("data", {})
        response_data = {}

        if sensor_key in device_data:
            # Real-time data is available
            value = device_data[sensor_key]
            response_data = {
                "sensor_key": sensor_key,
                "value": value,
                "source": "mqtt",
                "last_seen": "real-time"
            }
        else:
            return jsonify({
                "error": f"Sensor {sensor_key} not found for device {device_id}",
                "message": "Data not available in real-time"
            }), 404

        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error in get_combined_sensor_data: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve sensor data",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500

# Get All Sensors Route

# Example of adding a sensor to dashboard
@dashboardbp.route('/dashboard/add_sensor/<int:sensor_id>', methods=['POST'])
@login_required
def add_to_dashboard(sensor_id):
    try:
        # Check if sensor exists
        sensor = Sensor.query.get(sensor_id)
        if not sensor:
            return jsonify({"message": "Sensor not found"}), 404
            
        # Check if already on dashboard
        existing = DashboardSensor.query.filter_by(sensor_id=sensor_id).first()
        if existing:
            return jsonify({"message": "Sensor already on dashboard"}), 400
            
        # Add to dashboard
        dashboard_sensor = DashboardSensor(sensor_id=sensor_id)
        db.session.add(dashboard_sensor)
        db.session.commit()
        
        return jsonify({
            "message": "Sensor added to dashboard",
            "dashboard_sensor": dashboard_sensor.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to add sensor to dashboard",
            "message": str(e)
        }), 500
    
@dashboardbp.route('/dashboard/remove_sensor/<int:dashboard_sensor_id>', methods=['DELETE'])
@login_required
def remove_from_dashboard(dashboard_sensor_id):
    try:
        # Check if dashboard sensor exists
        dashboard_sensor = DashboardSensor.query.get(dashboard_sensor_id)
        if not dashboard_sensor:
            return jsonify({"message": "Dashboard sensor not found"}), 404
            
        # Remove from dashboard
        db.session.delete(dashboard_sensor)
        db.session.commit()
        
        return jsonify({
            "message": "Sensor removed from dashboard",
            "dashboard_sensor_id": dashboard_sensor_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to remove sensor from dashboard",
            "message": str(e)
        }), 500

#debugging
@dashboardbp.route('/dashboard/unregistered_dashboard_sensors', methods=['GET'])
@login_required
def get_unregistered_dashboard_sensors():
    try:
        # Fetch all records from the Sensor table
        sensors = Sensor.query.all()

        # Fetch all registered sensors from the DashboardSensor table
        registered_sensor_ids = {sensor.sensor_id for sensor in DashboardSensor.query.all()}

        # Filter out registered sensors, only include unregistered sensors
        unregistered_sensors = [
            sensor.to_dict() for sensor in sensors
            if sensor.id not in registered_sensor_ids
        ]

        # Return the list of unregistered sensors as JSON
        return jsonify(unregistered_sensors)

    except Exception as e:
        logger.error(f"Error fetching dashboard sensors: {str(e)}")
        return jsonify({
            "error": "Failed to fetch dashboard sensors",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500


@dashboardbp.route('/dashboard/dashboard_sensors', methods=['GET'])
@login_required
def get_registered_dashboard_sensors():
    try:
        # Fetch all records from the Sensor table
        sensors = Sensor.query.all()

        # Fetch all registered sensors from the DashboardSensor table
        registered_sensor_ids = {sensor.sensor_id for sensor in DashboardSensor.query.all()}

        # Filter out unregistered sensors, only include registered sensors
        registered_sensors = [
            sensor.to_dict() for sensor in sensors
            if sensor.id in registered_sensor_ids
        ]

        # Return the list of registered sensors as JSON
        return jsonify(registered_sensors)

    except Exception as e:
        logger.error(f"Error fetching dashboard sensors: {str(e)}")
        return jsonify({
            "error": "Failed to fetch dashboard sensors",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500


@dashboardbp.route('/dashboard/dashboardsensor', methods=['GET'])
@login_required
def dashboardsensor():
    try:
        # Step 1: Get all dashboard sensors with their related sensor data
        dashboard_entries = DashboardSensor.query.join(Sensor).all()

        if not dashboard_entries:
            return jsonify({
                "message": "No sensors added to dashboard"
            }), 404

        # Create a set of (device_id, sensor_key) pairs for sensors on the dashboard
        dashboard_sensors = {(entry.sensor.device_id, entry.sensor.sensor_key): entry for entry in dashboard_entries}

        # Step 2: Collect real-time data from MQTT
        current_time = time.time()
        categorized_data = {}

        for device_id, details in last_known_state.items():
            # Only process if this device has sensors on the dashboard
            for sensor_key, value in details["data"].items():
                # Check if this (device_id, sensor_key) pair is on the dashboard
                dashboard_sensor = dashboard_sensors.get((device_id, sensor_key))
                if dashboard_sensor:
                    if current_time - details.get("timestamp", 0) <= MAX_MESSAGE_AGE:
                        if sensor_key not in categorized_data:
                            categorized_data[sensor_key] = []
                        categorized_data[sensor_key].append({
                            "sensor_id": dashboard_sensor.sensor_id,  # Add sensor_id
                            "dashboard_sensor_id": dashboard_sensor.id,  # Add the dashboard sensor id
                            "device_id": device_id,
                            "sensor_key": sensor_key,
                            "value": value,
                            "last_seen": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(details["timestamp"]))
                        })

        if not categorized_data:
            return jsonify({
                "message": "No recent data found for the sensors on the dashboard"
            }), 404

        # Step 3: Return the categorized data
        return jsonify(categorized_data)

    except Exception as e:
        logger.error(f"Error fetching dashboard sensors: {str(e)}")
        return jsonify({
            "error": "Failed to fetch dashboard sensors",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500



@dashboardbp.route('/dashboard/<device_id>/relay/command', methods=['GET', 'POST'])
@login_required
def control_relay(device_id):
    try:
        # Handle GET and POST requests differently
        if request.method == 'GET':
            command = request.args.get('state', '').upper()
        else:
            data = request.get_json()
            if not data or 'state' not in data:
                return jsonify({"error": "Invalid request. 'state' is required."}), 400
            command = data['state'].upper()

        # Validate the command
        if command not in ['ON', 'OFF']:
            return jsonify({"error": "Invalid command. Use 'ON' or 'OFF'."}), 400

        # Publish command to MQTT topic
        mqtt_topic = f"home/{device_id}/relay/command"
        result = mqtt_client.publish(mqtt_topic, command)
        
        # Log action
        logger.info(f"Relay {device_id} set to {command}")

        return jsonify({
            "message": f"Relay {device_id} set to {command}",
            "command": command
        }), 200

    except Exception as e:
        logger.error(f"Error controlling relay for device {device_id}: {str(e)}")
        return jsonify({
            "error": "Failed to control relay",
            "message": str(e)
        }), 500
    

@dashboardbp.route('/dashboard/sensor_types', methods=['GET'])
@login_required
def get_sensor_types():
    try:
        # Fetch all sensor types from the database
        sensor_types = SensorType.query.all()
        
        # Format the response
        sensor_types_data = [
            {
                "id": sensor.id,  # Include sensor ID
                "type_key": sensor.type_key,
                "display_name": sensor.display_name,  # Use display_name instead of type_key
                "unit": sensor.unit,
                "states": sensor.states
            }
            for sensor in sensor_types
        ]
        
        return jsonify(sensor_types_data)
    except Exception as e:
        logger.error(f"Error fetching sensor types: {str(e)}")
        return jsonify({"error": "Failed to fetch sensor types"}), 500
