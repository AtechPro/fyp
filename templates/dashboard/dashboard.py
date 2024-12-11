import logging
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
import json, time
from database.database import db, User

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dashboardbp = Blueprint('dashboard', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MAX_MESSAGE_AGE = 10
MQTT_TOPIC = "home/#"

mqtt_client = mqtt.Client()
last_known_state = {}

# Sensor Configuration (matching client-side configuration)
SENSOR_TYPES = {
    'temperature': {'unit': '°C'},
    'humidity': {'unit': '%'},
    'reed_switch': {'type': 'status', 'states': ['OPEN', 'CLOSED']},
    'photo_interrupter': {'type': 'status', 'states': ['CLEAR', 'BLOCKED']},
    'relay': {'type': 'status', 'states': ['ON', 'OFF']}
}

# Initialize MQTT client
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
        
        # Validate device ID format
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"
        
        last_known_state[device_id] = {
            "data": payload,
            "timestamp": time.time()
        }

        # Log received data to check if temperature is included
        logger.debug(f"Received message for device {device_id}: {json.dumps(payload)}")

    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON payload received on topic {msg.topic}")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")


# Dashboard route to render dashboard page
@dashboardbp.route('/dashboard')
@login_required
def dashboard():
    """
    Render the dashboard template and provide MQTT messages.
    """
    try:
        current_time = time.time()
        # Filtering messages based on time threshold
        filtered_data = {
            device_id: details["data"]
            for device_id, details in last_known_state.items()
            if current_time - details["timestamp"] <= MAX_MESSAGE_AGE
        }
        messages = filtered_data
    except Exception as e:
        logger.error(f"Error filtering dashboard messages: {e}")
        messages = {}

    user = User.query.filter_by(userid=current_user.userid).first()
    return render_template('dashboard/dashboard.html', messages=messages, user=user)

# API route to fetch sensor data for a specific device and sensor type
@dashboardbp.route('/dashboard/message/<device_id>/<sensor_type>', methods=['GET'])
def get_sensor_data(device_id, sensor_type):
    """
    Get specific sensor data for a device.
    """
    try:
        # Validate sensor type
        if sensor_type not in SENSOR_TYPES:
            return jsonify({"error": f"Invalid sensor type: {sensor_type}"}), 400
        
        # Normalize device ID
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"
        
        # Retrieve device data from the last known state
        device_data = last_known_state.get(device_id, {}).get("data", {})
        
        # Check if the requested sensor type is available for the device
        if sensor_type in device_data:
            return jsonify({sensor_type: device_data[sensor_type]})
        
        # Handle missing sensor data
        return jsonify({"error": f"{sensor_type} data not available for device {device_id}"}), 404
    
    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500

# Relay control route
@dashboardbp.route('/relay/<device_id>/<relay_state>', methods=['GET'])
def control_relay(device_id, relay_state):
    """
    Control relay for a specific device.
    """
    try:
        # Validate relay state
        if relay_state not in ['ON', 'OFF']:
            return jsonify({"error": "Invalid relay state. Must be 'ON' or 'OFF'"}), 400
        
        # Normalize device ID
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"
        
        # Publish relay control message
        relay_topic = f"home/{device_id}/relay/command"
        logger.debug(f"Publishing to topic: {relay_topic}, message: {relay_state}")
        mqtt_client.publish(relay_topic, relay_state)
        
        return jsonify({"message": f"Relay {relay_state} command sent to {device_id}"}), 200
    
    except Exception as e:
        logger.error(f"Error controlling relay: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500



# Initialize MQTT connection when the module is imported
init_mqtt_client()
