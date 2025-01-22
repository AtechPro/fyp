import logging
import json
import time
from flask import Blueprint, jsonify, request, current_app, render_template
from flask_login import login_required, current_user
from datetime import datetime
import paho.mqtt.client as mqtt
from database.database import db, User, Sensor, SensorType, TimerScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()

def schedule_timers():
    # Fetch timers for the current user
    timers = TimerScheduler.query.filter_by(user_id=current_user.userid).all()
    
    if timers:
        for timer in timers:
            # Construct the cron trigger based on the timer data
            days_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
            days = [days_map[day] for day in timer.days.split(",")]  # support multiple days

            trigger = CronTrigger(
                day_of_week=",".join(str(day) for day in days),
                hour=int(timer.trigger_time.split(":")[0]),
                minute=int(timer.trigger_time.split(":")[1]),
                second=0
            )
            
            # Add job to scheduler with the relay control
            scheduler.add_job(
                control_relay, 
                trigger,
                args=[timer.relay_device_id], 
                kwargs={'state': timer.action}
            )

scheduler.start()

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

@timerbp.route('/timer/relays', methods=['GET'])
@login_required
def fetch_relay_state():
    try:
        # Check if any data is available
        if not last_known_state:
            return jsonify({"message": "No relay data available"}), 200

        # Extract relay state for each device
        relay_states = {
            device_id: {
                "relay_state": details["data"].get("relay", "UNKNOWN"),  # Default to UNKNOWN if no relay state found
                "timestamp": details.get("timestamp")
            }
            for device_id, details in last_known_state.items()
        }

        # If no relays are present in the data
        if not relay_states:
            return jsonify({"message": "No relay states found"}), 200

        # Return the relay states
        return jsonify(relay_states), 200

    except Exception as e:
        logger.error(f"Error fetching relay states: {e}")
        return jsonify({"error": "An error occurred while fetching relay states"}), 500




@timerbp.route('/timer/scheduler', methods=['POST'])
def create_timer():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    required_fields = ["trigger_time", "days", "action", "relay_device_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Convert days list to a comma-separated string
    days_string = ",".join(data['days'])

    # Create and save the timer
    new_timer = TimerScheduler(
        user_id=current_user.userid,
        trigger_time=data['trigger_time'],
        days=days_string,  # Save as a string
        enabled=data.get('enabled', True),
        description=data.get('description'),
        title=data.get('title'),
        action=data['action'],
        relay_device_id=data['relay_device_id']
    )

    # Commit to the database
    db.session.add(new_timer)
    db.session.commit()

    # Return success
    return jsonify({"message": "Timer created successfully", "timer": new_timer.to_dict()}), 201

@timerbp.route('/timer/scheduler/<int:timer_id>', methods=['PUT'])
def edit_timer(timer_id):
    # Get the data from the request JSON
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    # Check if the timer exists
    timer = TimerScheduler.query.filter_by(id=timer_id, user_id=current_user.userid).first()
    if not timer:
        return jsonify({"error": "Timer not found"}), 404

    # Update the fields as necessary
    if "trigger_time" in data:
        timer.trigger_time = data['trigger_time']
    if "days" in data:
        timer.days = ",".join(data['days'])
    if "action" in data:
        timer.action = data['action']
    if "relay_device_id" in data:
        timer.relay_device_id = data['relay_device_id']
    if "enabled" in data:
        timer.enabled = data['enabled']
    if "description" in data:
        timer.description = data['description']
    if "title" in data:
        timer.title = data['title']

    # Commit changes to the database
    db.session.commit()

    # Return success with the updated timer as JSON
    return jsonify({"message": "Timer updated successfully", "timer": timer.to_dict()}), 200


# Delete Timer
@timerbp.route('/timer/scheduler', methods=['DELETE'])
def delete_timer():
    # Get the JSON data containing the timer_id to delete
    data = request.get_json()
    if not data or "timer_id" not in data:
        return jsonify({"error": "Invalid JSON data, 'timer_id' is required"}), 400

    timer_id = data['timer_id']

    # Find the timer by ID and user_id
    timer = TimerScheduler.query.filter_by(id=timer_id, user_id=current_user.userid).first()
    if not timer:
        return jsonify({"error": "Timer not found"}), 404

    # Delete the timer
    db.session.delete(timer)
    db.session.commit()

    # Return success message
    return jsonify({"message": "Timer deleted successfully"}), 200


@timerbp.route('/timer/scheduler', methods=['GET'])
def get_timers():
    # Fetch all timers for the current user
    timers = TimerScheduler.query.filter_by(user_id=current_user.userid).all()

    if not timers:
        return jsonify({"message": "No timers found for the current user."}), 404

    # Convert all timer objects to dictionaries
    timers_list = [timer.to_dict() for timer in timers]

    return jsonify({"timers": timers_list}), 200



@timerbp.route('/timer/current-time', methods=['GET'])
def get_current_time():
    try:
        # Get the current time
        current_time = datetime.now().strftime("%H:%M:%S")  # Format: HH:MM:SS
        return jsonify({"current_time": current_time}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    
@timerbp.route('/timer/trigger_relay', methods=['GET']) # can't impeliment on the background
def trigger_relay():
    try:
        # Fetch all timers for the current user
        timers = TimerScheduler.query.filter_by(user_id=current_user.userid).all()

        if not timers:
            return jsonify({"message": "No timers found for the current user."}), 404
        
        # Get the current time and day
        current_time = datetime.now().strftime("%H:%M")
        current_day = datetime.now().strftime("%a") 
        
        triggered_timers = []

        for timer in timers:
            # Initialize a default message and status
            status = {"timer": timer.to_dict(), "reacted": False}

            # Check if the current day matches the timer days
            days_map = timer.days.split(",")  # Multiple days support
            if current_day not in days_map:
                status["message"] = f"Timer not scheduled for today ({current_day})."
                triggered_timers.append(status)
                continue  # Skip to the next timer
            
            # Check if the current time matches the trigger time
            if current_time == timer.trigger_time:
                # Trigger the relay action (ON or OFF)
                device = Sensor.query.filter_by(device_id=timer.relay_device_id).first()
                if not device:
                    status["message"] = f"Device {timer.relay_device_id} is not registered."
                    triggered_timers.append(status)
                    continue  # Skip if device is not found

                # Validate the action (ON/OFF)
                command = timer.action.upper()
                if command not in ['ON', 'OFF']:
                    status["message"] = "Invalid command. Use 'ON' or 'OFF'."
                    triggered_timers.append(status)
                    continue  # Skip if the command is invalid

                # Publish command to MQTT topic
                mqtt_topic = f"home/{timer.relay_device_id}/relay/command"
                mqtt_client.publish(mqtt_topic, command)
                
                # Log the action
                logger.info(f"Relay {timer.relay_device_id} set to {command}")

                # Update the status for successful execution
                status.update({
                    "message": f"Relay {timer.relay_device_id} set to {command}",
                    "reacted": True
                })
            else:
                # Timer not triggered due to time mismatch
                status["message"] = f"Timer not triggered; current time ({current_time}) does not match {timer.trigger_time}."
            
            # Add status to the response
            triggered_timers.append(status)
        
        # Return all timer reactions and statuses
        return jsonify({
            "triggered_timers": triggered_timers
        }), 200

    except Exception as e:
        logger.error(f"Error checking timers: {str(e)}")
        return jsonify({
            "error": "Failed to check timers",
            "message": str(e)
        }), 500



# Debugging purpose
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



@timerbp.route('/timer/sensor/<sensor_key>/datatype', methods=['GET'])
@login_required
def get_sensor_datatype(sensor_key):
    return fetch_sensor_datatype(sensor_key)

@timerbp.route('/timer', methods=['GET'])
def timerpg():
    return render_template('timerscheduler/timer.html')

@timerbp.route('/scheduler', methods=['GET'])
def schedulerpg():
    return render_template('timerscheduler/scheduler.html')




