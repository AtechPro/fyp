import logging
import json
import time
from flask import Blueprint, jsonify, request, current_app, render_template
from flask_login import login_required, current_user
from datetime import datetime
import paho.mqtt.client as mqtt
from database.database import db, User, Sensor, SensorType, timerscheduler


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a Blueprint for automation
timerbp = Blueprint('timerbp', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"  # Replace with your MQTT broker address
BROKER_PORT = 1883               # Default MQTT port
MQTT_TOPIC = "home/#"            # Topic to subscribe to

# MQTT Client
mqtt_client = mqtt.Client()

# Store the latest sensor data
last_known_state = {}

# Initialize MQTT Client
def init_mqtt_client():
    """Initialize and connect the MQTT client to the broker."""
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
    """Callback when the MQTT client connects to the broker."""
    if rc == 0:
        logger.info("Successfully connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)  # Subscribe to the topic
    else:
        logger.error(f"Failed to connect with return code {rc}")

# MQTT on_message callback
def on_message(_client, _userdata, msg):
    """Callback when an MQTT message is received."""
    try:
        payload = json.loads(msg.payload.decode())  # Decode the JSON payload
        device_id = payload.get("deviceId", "Unknown")  # Extract device ID

        # Log the received message
        logger.debug(f"Received message from {device_id}: {payload}")

        # Update the last known state of the device
        if device_id not in last_known_state:
            last_known_state[device_id] = {"data": {}, "timestamp": time.time()}

        # Update the data and timestamp of the device
        for key, value in payload.items():
            if key != "deviceId":
                last_known_state[device_id]["data"][key] = value
        last_known_state[device_id]["timestamp"] = time.time()

    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# Initialize MQTT client when the module is loaded
init_mqtt_client()

def fetch_sensor_datatype(sensor_key): # later will need to show as the sensor type invovled on the reactor (relay)
    """
    Fetch the data type (unit or states) of a sensor based on its sensor_key.
    """
    try:
        # Query the Sensor table to find the sensor by its sensor_key
        sensor = Sensor.query.filter_by(sensor_key=sensor_key).first()

        # Check if the sensor exists
        if not sensor:
            return jsonify({"error": f"Sensor with key '{sensor_key}' not found"}), 404

        # Get the associated SensorType
        sensor_type = sensor.sensor_type

        # Prepare the response data
        response_data = {
            "sensor_key": sensor_key,
            "sensor_type": sensor_type.type_key,
            "display_name": sensor_type.display_name,
        }

        # Add unit or states based on the sensor type
        if sensor_type.unit:
            response_data["unit"] = sensor_type.unit
        elif sensor_type.states:
            response_data["states"] = sensor_type.states

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error fetching sensor data type for {sensor_key}: {e}")
        return jsonify({"error": "Failed to fetch sensor data type", "message": str(e)}), 500

@timerbp.route('/timer/sensors', methods=['GET'])
@login_required
def fetch_sensor_data():
    try:
        # Check if any sensor data is available
        if not last_known_state:
            return jsonify({"message": "No sensor data available"}), 200

        # Fetch all registered device IDs from the database
        registered_devices = Sensor.query.with_entities(Sensor.device_id).distinct().all()
        registered_device_ids = {device.device_id for device in registered_devices}

        # Filter the last_known_state to only include registered devices
        filtered_data = {
            device_id: details
            for device_id, details in last_known_state.items()
            if device_id in registered_device_ids
        }

        # If no registered devices are found in the MQTT data
        if not filtered_data:
            return jsonify({"message": "No data available for registered devices"}), 200

        # Return the filtered sensor data
        return jsonify(filtered_data), 200

    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        return jsonify({"error": "Failed to fetch sensor data", "message": str(e)}), 500
    
    return fetch_sensor_datatype(sensor_key)



@timerbp.route('/timer/relay/<device_id>', methods=['GET', 'POST'])
@login_required
def control_relay(device_id):
    try:
        # Check if the device is registered in the database
        device = Sensor.query.filter_by(device_id=device_id).first()
        if not device:
            return jsonify({"error": f"Device {device_id} is not registered"}), 404

        # Handle GET and POST requests differently
        if request.method == 'GET':
            command = request.args.get('state', '').upper()  # Get command from query parameters
        else:
            data = request.get_json()  # Get command from JSON payload
            if not data or 'state' not in data:
                return jsonify({"error": "Invalid request. 'state' is required."}), 400
            command = data['state'].upper()

        # Validate the command
        if command not in ['ON', 'OFF']:
            return jsonify({"error": "Invalid command. Use 'ON' or 'OFF'."}), 400

        # Publish command to MQTT topic
        mqtt_topic = f"home/{device_id}/relay/command"
        result = mqtt_client.publish(mqtt_topic, command)
        
        # Log the action
        logger.info(f"Relay {device_id} set to {command}")

        # Return success response
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

    except Exception as e:
        logger.error(f"Error controlling relay for device {device_id}: {str(e)}")
        return jsonify({
            "error": "Failed to control relay",
            "message": str(e)
        }), 500

@timerbp.route('/timer/sensors/timer_applied', methods=['GET'])
@login_required
def fetch_sensor_timer_rules():
    """
    Fetch sensors with timer-based rules applied and execute timer-based actions.
    Checks and applies timer-based automation rules for sensors.
    """
    try:
        current_user_id = current_user.userid
        current_time = datetime.now()
        current_day = current_time.strftime('%A').lower()

        # Query to fetch timer-based rules for the current user
        timer_rules = (
            db.session.query(
                timerscheduler,
                Sensor,
                SensorType
            )
            .join(Sensor, timerscheduler.sensor_id == Sensor.id)
            .join(SensorType, Sensor.sensor_type_id == SensorType.id)
            .filter(
                timerscheduler.user_id == current_user_id,
                timerscheduler.enabled == True
            )
            .all()
        )

        timer_rules_data = {}

        for timer_rule, sensor, sensor_type in timer_rules:
            # Check if current time is within the scheduled time range
            start_time = datetime.strptime(timer_rule.start_time, '%H:%M').time()
            end_time = datetime.strptime(timer_rule.end_time, '%H:%M').time()
            current_clock_time = current_time.time()

            # Check if the current day is in the scheduled days
            scheduled_days = timer_rule.days.lower().split(',')
            is_day_matched = current_day in scheduled_days

            # Check if current time is within the specified time range
            is_time_matched = start_time <= current_clock_time <= end_time

            # Determine if the rule should be executed
            is_rule_matched = is_day_matched and is_time_matched

            if is_rule_matched:
                try:
                    # Execute the timer-based action
                    relay_device_id = timer_rule.relay_device_id
                    action = timer_rule.action.upper()

                    if action in ['ON', 'OFF']:
                        response, status_code = control_relay(
                            device_id=relay_device_id,
                            request_type='POST',
                            json_data={'state': action}
                        )

                        if status_code != 200:
                            logger.error(f"Failed to execute timer rule: {timer_rule.timer_title}")
                        else:
                            logger.info(f"Successfully executed timer rule: {timer_rule.timer_title}")

                except Exception as e:
                    logger.error(f"Error executing timer rule: {str(e)}")

            # Prepare timer rules data for response
            sensor_type_key = sensor_type.type_key
            if sensor_type_key not in timer_rules_data:
                timer_rules_data[sensor_type_key] = {
                    "type_display_name": sensor_type.display_name,
                    "unit": sensor_type.unit,
                    "sensors": []
                }

            # Check if sensor already exists in the list
            sensor_exists = False
            for existing_sensor in timer_rules_data[sensor_type_key]["sensors"]:
                if existing_sensor["sensor_id"] == sensor.id:
                    if "timer_rules" not in existing_sensor:
                        existing_sensor["timer_rules"] = []
                    
                    timer_rule_info = {
                        "timer_id": timer_rule.id,
                        "start_time": timer_rule.start_time,
                        "end_time": timer_rule.end_time,
                        "days": timer_rule.days,
                        "action": timer_rule.action,
                        "relay_device_id": timer_rule.relay_device_id,
                        "timer_title": timer_rule.timer_title,
                        "timer_desc": timer_rule.timer_desc,
                        "is_matched": is_rule_matched,
                        "status_message": f"Rule {'matched' if is_rule_matched else 'not matched'}: "
                                          f"Days: {timer_rule.days}, "
                                          f"Time: {timer_rule.start_time}-{timer_rule.end_time}"
                    }
                    existing_sensor["timer_rules"].append(timer_rule_info)
                    sensor_exists = True
                    break

            # If sensor doesn't exist, add it
            if not sensor_exists:
                sensor_data = {
                    "device_id": sensor.device_id,
                    "sensor_key": sensor.sensor_key,
                    "sensor_id": sensor.id,
                    "sensor_type_id": sensor.sensor_type_id,
                    "timer_rules": [{
                        "timer_id": timer_rule.id,
                        "start_time": timer_rule.start_time,
                        "end_time": timer_rule.end_time,
                        "days": timer_rule.days,
                        "action": timer_rule.action,
                        "relay_device_id": timer_rule.relay_device_id,
                        "timer_title": timer_rule.timer_title,
                        "timer_desc": timer_rule.timer_desc,
                        "is_matched": is_rule_matched,
                        "status_message": f"Rule {'matched' if is_rule_matched else 'not matched'}: "
                                          f"Days: {timer_rule.days}, "
                                          f"Time: {timer_rule.start_time}-{timer_rule.end_time}"
                    }]
                }
                timer_rules_data[sensor_type_key]["sensors"].append(sensor_data)

        return jsonify(timer_rules_data), 200

    except Exception as e:
        logger.error(f"Error fetching timer rules data: {e}")
        return jsonify({"error": "Failed to fetch timer rules data", "message": str(e)}), 500





@timerbp.route('/timer/sensor/<sensor_key>/datatype', methods=['GET'])
@login_required
def get_sensor_datatype(sensor_key):
    return fetch_sensor_datatype(sensor_key)

@timerbp.route('/timer', methods=['GET'])
def automation():
    return render_template('timerscheduler/timer.html')