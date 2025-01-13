import logging
import json
import time
from flask import Blueprint, jsonify, request, current_app, render_template
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
from database.database import db, User, Sensor, SensorType, AutomationRule
from datetime import datetime, timedelta
from threading import Lock
from flask_socketio import SocketIO, emit


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a Blueprint for automation
autobp = Blueprint('autobp', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"  # Replace with your MQTT broker address
BROKER_PORT = 1883               # Default MQTT port
MQTT_TOPIC = "home/#"            # Topic to subscribe to
socketio = SocketIO()
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

def control_relay(device_id, request_type, **kwargs):
    try:
        # Check if the device is registered in the database
        device = Sensor.query.filter_by(device_id=device_id).first()
        if not device:
            return {"error": f"Device {device_id} is not registered"}, 404

        # Handle GET and POST requests differently
        if request_type == 'GET':
            args = kwargs.get('args', {})
            command = args.get('state', '').upper()  # Get command from query parameters
        elif request_type == 'POST':
            json_data = kwargs.get('json_data', {})
            if not json_data or 'state' not in json_data:
                return {"error": "Invalid request. 'state' is required."}, 400
            command = json_data['state'].upper()
        else:
            return {"error": "Invalid request type. Use 'GET' or 'POST'."}, 400

        # Validate the command
        if command not in ['ON', 'OFF']:
            return {"error": "Invalid command. Use 'ON' or 'OFF'."}, 400

        # Publish command to MQTT topic
        mqtt_topic = f"home/{device_id}/relay/command"
        mqtt_client.publish(mqtt_topic, command)
        
        # Log the action
        logger.info(f"Relay {device_id} set to {command}")

        # Return success response
        return {
            "message": f"Relay {device_id} set to {command}",
            "command": command
        }, 200

    except Exception as e:
        logger.error(f"Error controlling relay {device_id}: {str(e)}")
        return {"error": str(e)}, 500

global_sensor_data = {}
sensor_data_lock = Lock()

def fetch_and_categorize_sensor_data():
    """Fetch and categorize sensor data from the database."""
    global global_sensor_data, sensor_data_lock

    try:
        # Fetch all registered sensors and their types from the database
        sensors = (
            db.session.query(
                Sensor.id,
                Sensor.device_id,
                Sensor.sensor_key,
                Sensor.sensor_type_id,
                SensorType.type_key,
                SensorType.display_name,
                SensorType.unit,
                SensorType.states,
            )
            .join(SensorType, Sensor.sensor_type_id == SensorType.id)
            .all()
        )

        # Categorize sensors by their type
        categorized_data = {}
        for sensor in sensors:
            sensor_type = sensor.type_key
            if sensor_type not in categorized_data:
                categorized_data[sensor_type] = {
                    "type_display_name": sensor.display_name,
                    "unit": sensor.unit,
                    "states": sensor.states,
                    "sensors": [],
                }
            categorized_data[sensor_type]["sensors"].append({
                "device_id": sensor.device_id,
                "sensor_key": sensor.sensor_key,
                "last_value": last_known_state.get(sensor.device_id, {}).get("data", {}).get(sensor.sensor_key),
                "sensor_id": sensor.id,
                "sensor_type_id": sensor.sensor_type_id,
            })

        # Update global sensor data with thread safety
        with sensor_data_lock:
            global_sensor_data = categorized_data

    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        raise  # Re-raise the exception to handle it in the calling function


@autobp.route('/automation/sensors', methods=['GET'])
@login_required
def fetch_sensor_data():
    try:
        # Check if any sensor data is available
        if not last_known_state:
            return jsonify({"message": "No sensor data available"}), 200

        # Fetch and categorize sensor data
        fetch_and_categorize_sensor_data()

        # Return categorized sensor data
        with sensor_data_lock:
            return jsonify(global_sensor_data), 200

    except Exception as e:
        logger.error(f"Error fetching sensor data: {e}")
        return jsonify({"error": "Failed to fetch sensor data", "message": str(e)}), 500
    
@autobp.route('/automation/sensors/rule_applied', methods=['GET'])  
@login_required  
def fetch_sensor_rules_applied():  
    """  
    Fetch only sensors that have automation rules applied and their matching status.  
    Executes automation rules when conditions are met.  
    """  
    # Module level variables for rule execution tracking  
    last_rule_execution = {}  

    def should_execute_rule(rule_id, debounce_seconds=60):  
        """Check if enough time has passed since the last rule execution"""  
        current_time = datetime.now()  
        last_execution = last_rule_execution.get(rule_id)  
        
        if last_execution is None or (current_time - last_execution) > timedelta(seconds=debounce_seconds):  
            last_rule_execution[rule_id] = current_time  
            return True  
        return False  

    def execute_automation_rule(rule_info, is_matched):  
        """Execute automation rule based on the matching condition with debouncing"""  
        if not rule_info['enabled']:  
            return  
            
        try:  
            rule_id = rule_info['rule_id']  
            
            if not should_execute_rule(rule_id):  
                logger.debug(f"Skipping rule execution due to debounce: {rule_info['auto_title']}")  
                return  
                
            relay_device_id = rule_info['relay_device_id']  
            action = rule_info['action'].upper()  
            
            if is_matched and action in ['ON', 'OFF']:  
                response, status_code = control_relay(  
                    device_id=relay_device_id,  
                    request_type='POST',  
                    json_data={'state': action}  
                )  
                
                if status_code != 200:  
                    logger.error(f"Failed to execute automation rule: {response.get('error', 'Unknown error')}")  
                else:  
                    logger.info(f"Successfully executed automation rule: {rule_info['auto_title']}")  
                    
        except Exception as e:  
            logger.error(f"Error executing automation rule: {str(e)}")  

    def check_rule_match(value, condition, threshold):  
        """Helper function to check if a value matches a rule's condition"""  
        try:  
            if value is None:  
                return False  
                
            # Handle numeric comparisons  
            if isinstance(value, (int, float)) and threshold.replace('.', '').isdigit():  
                numeric_value = float(value)  
                numeric_threshold = float(threshold)  
                
                if condition == 'GREATER_THAN':  
                    return numeric_value > numeric_threshold  
                elif condition == 'LESS_THAN':  
                    return numeric_value < numeric_threshold  
                elif condition == 'EQUALS':  
                    return numeric_value == numeric_threshold  
                    
            # Handle string/state comparisons  
            else:  
                str_value = str(value).lower()  
                str_threshold = str(threshold).lower()  
                
                if condition == 'EQUALS':  
                    return str_value == str_threshold  
                    
            return False  
            
        except (ValueError, TypeError):  
            return False  

    try:  
        if not last_known_state:  
            return jsonify({"message": "No sensor data available"}), 200  

        current_user_id = current_user.userid  

        with sensor_data_lock:  
            sensor_rules_data = {}  
            
            # Modified query to only fetch sensors with active rules  
            sensor_rules = (  
                db.session.query(  
                    Sensor.id,  
                    Sensor.device_id,  
                    Sensor.sensor_key,  
                    Sensor.sensor_type_id,  
                    SensorType.type_key,  
                    SensorType.display_name,  
                    SensorType.unit,  
                    SensorType.states,  
                    AutomationRule.id.label('rule_id'),  
                    AutomationRule.condition,  
                    AutomationRule.threshold,  
                    AutomationRule.relay_device_id,  
                    AutomationRule.action,  
                    AutomationRule.enabled,  
                    AutomationRule.auto_title,  
                    AutomationRule.auto_description  
                )  
                .join(SensorType, Sensor.sensor_type_id == SensorType.id)  
                .join(  # Changed from outerjoin to join to only get sensors with rules  
                    AutomationRule,  
                    db.and_(  
                        Sensor.id == AutomationRule.sensor_id,  
                        AutomationRule.user_id == current_user_id  
                    )  
                )  
                .all()  
            )  

            # Process only sensors with rules  
            for sensor in sensor_rules:  
                sensor_type = sensor.type_key  
                if sensor_type not in sensor_rules_data:  
                    sensor_rules_data[sensor_type] = {  
                        "type_display_name": sensor.display_name,  
                        "unit": sensor.unit,  
                        "states": sensor.states,  
                        "sensors": [],  
                    }  

                current_value = last_known_state.get(sensor.device_id, {}).get("data", {}).get(sensor.sensor_key)  

                # Check if the rule conditions are currently matched  
                is_matched = check_rule_match(current_value, sensor.condition, sensor.threshold)  
                
                # Create a human-readable status message  
                status_message = (  
                    f"Current value ({current_value}) "  
                    f"{'matches' if is_matched else 'does not match'} "  
                    f"condition: {sensor.condition} {sensor.threshold}"  
                )  

                rule_info = {  
                    "rule_id": sensor.rule_id,  
                    "condition": sensor.condition,  
                    "threshold": sensor.threshold,  
                    "relay_device_id": sensor.relay_device_id,  
                    "action": sensor.action,  
                    "enabled": sensor.enabled,  
                    "auto_title": sensor.auto_title,  
                    "auto_description": sensor.auto_description,  
                    "is_matched": is_matched,  
                    "status_message": status_message  
                }  
                
                # Execute the automation rule if conditions are met  
                execute_automation_rule(rule_info, is_matched)  

                # Check if sensor already exists in the list  
                sensor_exists = False  
                for existing_sensor in sensor_rules_data[sensor_type]["sensors"]:  
                    if existing_sensor["sensor_id"] == sensor.id:  
                        if "rules" not in existing_sensor:  
                            existing_sensor["rules"] = []  
                        existing_sensor["rules"].append(rule_info)  
                        sensor_exists = True  
                        break  

                # If sensor doesn't exist, add it  
                if not sensor_exists:  
                    sensor_data = {  
                        "device_id": sensor.device_id,  
                        "sensor_key": sensor.sensor_key,  
                        "last_value": current_value,  
                        "sensor_id": sensor.id,  
                        "sensor_type_id": sensor.sensor_type_id,  
                        "rules": [rule_info]  
                    }  
                    sensor_rules_data[sensor_type]["sensors"].append(sensor_data)  

            return jsonify(sensor_rules_data), 200  

    except Exception as e:  
        logger.error(f"Error fetching sensor rules data: {e}")  
        return jsonify({"error": "Failed to fetch sensor rules data", "message": str(e)}), 500
    


@autobp.route('/automation/rule/add', methods=['GET', 'POST'])  
def add_automation_rule():  
    if request.method == 'GET':  
        return jsonify({  
            "message": "Send a POST request with JSON data to add a new automation rule."  
        }), 200  

    elif request.method == 'POST':  
        try:  
            data = request.get_json()  

            required_fields = [  
                'sensor_id', 'sensor_type_id', 'condition', 'threshold',  # Fixed typo here  
                'relay_device_id', 'action'  
            ]  
            for field in required_fields:  
                if field not in data:  
                    return jsonify({  
                        "error": f"Missing required field: {field}"  
                    }), 400  

            new_rule = AutomationRule(  
                user_id=data.get('user_id', 1),  
                sensor_id=data['sensor_id'],  
                sensor_type_id=data['sensor_type_id'],  
                condition=data['condition'],  
                threshold=data['threshold'],  
                relay_device_id=data['relay_device_id'],  
                action=data['action'],  
                enabled=data.get('enabled', True),  
                auto_title=data.get('auto_title'),  
                auto_description=data.get('auto_description'),  
            )  

            db.session.add(new_rule)  
            db.session.commit()  

            return jsonify({  
                "message": "Automation rule added successfully!",  
                "rule_id": new_rule.id  
            }), 201  

        except Exception as e:  
            db.session.rollback()  
            return jsonify({  
                "error": "Failed to add automation rule.",  
                "details": str(e)  
            }), 500

@autobp.route('/automation/rules', methods=['GET'])  
def get_all_automation_rules():  
    try:  
        # Query all rules from the database  
        rules = AutomationRule.query.all()  
        
        # Convert rules to list of dictionaries using the as_dict method  
        rules_list = [rule.as_dict() for rule in rules]  
        
        return jsonify({  
            "message": "Successfully retrieved automation rules",  
            "count": len(rules_list),  
            "rules": rules_list  
        }), 200  
        
    except Exception as e:  
        return jsonify({  
            "error": "Failed to retrieve automation rules",  
            "details": str(e)  
        }), 500
    
    
#for debug purposes only do not delete
@autobp.route('/automation/relay/<device_id>', methods=['GET', 'POST'])
@login_required
def relay_route(device_id):
    if request.method == 'GET':
        return jsonify(*control_relay(device_id, 'GET', args=request.args))
    elif request.method == 'POST':
        return jsonify(*control_relay(device_id, 'POST', json_data=request.get_json()))


@autobp.route('/automation/sensor/datatype/<sensor_key>', methods=['GET'])
@login_required
def get_sensor_datatype(sensor_key):
    return fetch_sensor_datatype(sensor_key)

@autobp.route('/automation', methods=['GET'])
def automation():
    return render_template('automationrule/automation.html')


