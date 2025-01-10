import os
import logging
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
import json
import time
from database.database import db, User, Sensor, SensorType, DashboardTile



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
@dashboardbp.route('/dashboard/sensors')
@login_required
def get_sensors():
    try:
        # Collect real-time data from MQTT
        sensor_list = []
        current_time = time.time()
        for device_id, details in last_known_state.items():
            if current_time - details.get("timestamp", 0) <= MAX_MESSAGE_AGE:
                for key, value in details["data"].items():
                    sensor_list.append({
                        "device_id": device_id,
                        "sensor_key": key,
                        "value": value,
                        "last_seen": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(details["timestamp"]))
                    })
        return jsonify(sensor_list)
    except Exception as e:
        logger.error(f"Error in get_sensors: {str(e)}")
        return jsonify({
            "error": "Failed to retrieve sensor list",
            "message": f"An unexpected error occurred: {str(e)}"
        }), 500


@dashboardbp.route('/dashboard/categorize_sensors', methods=['GET'])
@login_required
def categorize_sensors():
    try:
        # Step 1: Check the database for paired sensors
        paired_sensors = Sensor.query.all()
        paired_sensor_ids = {sensor.device_id for sensor in paired_sensors}

        # Step 2: Collect real-time data from MQTT
        current_time = time.time()
        categorized_data = {}

        for device_id, details in last_known_state.items():
            # Only process data from paired sensors
            if device_id in paired_sensor_ids:
                if current_time - details.get("timestamp", 0) <= MAX_MESSAGE_AGE:
                    for key, value in details["data"].items():
                        sensor_type = key  # Assuming sensor_key is the sensor type
                        if sensor_type not in categorized_data:
                            categorized_data[sensor_type] = []
                        categorized_data[sensor_type].append({
                            "device_id": device_id,
                            "sensor_key": key,
                            "value": value,
                            "last_seen": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(details["timestamp"]))
                        })

        # Step 3: Return the categorized data
        return jsonify(categorized_data)

    except Exception as e:
        logger.error(f"Error categorizing sensors: {str(e)}")
        return jsonify({
            "error": "Failed to categorize sensors",
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


@dashboardbp.route('/dashboard/tiles', methods=['GET', 'POST'])
@login_required
def manage_tiles():
    if request.method == 'GET':
        try:
            # Fetch all tiles for the current user
            user_tiles = DashboardTile.query.filter_by(userid=current_user.userid).all()
            logger.info(f"Fetched tiles for user {current_user.userid}: {user_tiles}")

            tiles = [
                {
                    "id": tile.id,
                    "sensor_id": tile.sensor_id,
                    "sensor_type": tile.sensor.sensor_type.display_name,
                    "value": tile.sensor.value,
                    "unit": tile.sensor.sensor_type.unit
                }
                for tile in user_tiles
            ]
            return jsonify(tiles)
        except Exception as e:
            logger.error(f"Error fetching tiles: {str(e)}")
            return jsonify({"error": "Failed to fetch tiles"}), 500

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or 'sensor_id' not in data:
                return jsonify({"error": "Invalid request. 'sensor_id' is required."}), 400

            sensor_id = data['sensor_id']

            # Check if the sensor exists
            sensor = Sensor.query.get(sensor_id)
            if not sensor:
                return jsonify({"error": f"Sensor with ID {sensor_id} not found"}), 404

            # Check if the tile already exists for the user
            existing_tile = DashboardTile.query.filter_by(userid=current_user.userid, sensor_id=sensor_id).first()
            if existing_tile:
                return jsonify({"error": "Tile already exists for this sensor"}), 400

            # Create a new tile
            new_tile = DashboardTile(userid=current_user.userid, sensor_id=sensor_id)
            db.session.add(new_tile)
            db.session.commit()

            return jsonify({
                "message": "Tile added successfully",
                "tile_id": new_tile.id
            }), 201
        except Exception as e:
            logger.error(f"Error adding tile: {str(e)}")
            db.session.rollback()
            return jsonify({"error": "Failed to add tile"}), 500


@dashboardbp.route('/dashboard/tiles/<int:tile_id>', methods=['DELETE'])
@login_required
def delete_tile(tile_id):
    try:
        # Fetch the tile
        tile = DashboardTile.query.get_or_404(tile_id)

        # Ensure the tile belongs to the current user
        if tile.userid != current_user.userid:
            return jsonify({"error": "Unauthorized to delete this tile"}), 403

        # Delete the tile
        db.session.delete(tile)
        db.session.commit()

        return jsonify({"message": "Tile deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting tile: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete tile"}), 500