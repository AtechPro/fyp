import logging
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
import paho.mqtt.client as mqtt
import json, time
from database.database import db, User, Sensor

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

dashboardbp = Blueprint('dashboard', __name__)

BROKER_ADDRESS = "atechpromqtt"
BROKER_PORT = 1883
MAX_MESSAGE_AGE = 10
MQTT_TOPIC = "home/#"

mqtt_client = mqtt.Client()
last_known_state = {}

SENSOR_TYPES = {
    'temperature': {'unit': '°C', 'type': 'Temperature Sensor'},
    'humidity': {'unit': '%', 'type': 'Humidity Sensor'},
    'reed_switch': {'type': 'Status Sensor', 'states': ['OPEN', 'CLOSED']},
    'photo_interrupter': {'type': 'Status Sensor', 'states': ['CLEAR', 'BLOCKED']},
    'relay': {'type': 'Status Sensor', 'states': ['ON', 'OFF']},
    'pir': {'type': 'Motion Sensor', 'states': ['MOTION DETECTED', 'NO MOTION']},
    'photoresistor': {'type': 'Analog Sensor', 'unit': 'Lux'},
}

def init_mqtt_client():
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
        logger.info(f"Connected to MQTT broker at {BROKER_ADDRESS}:{BROKER_PORT}")
    except Exception as e:
        logger.error(f"Error connecting to MQTT broker: {e}")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Successfully connected to MQTT broker")
        client.subscribe(MQTT_TOPIC)
    else:
        logger.error(f"Failed to connect with return code {rc}")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    device_id = payload.get("deviceId", "Unknown")
    if device_id not in last_known_state:
        last_known_state[device_id] = {"data": {}}
    for key, value in payload.items():
        if key != "deviceId":
            last_known_state[device_id]["data"][key] = value

@dashboardbp.route('/dashboard')
@login_required
def dashboard():
    try:
        current_time = time.time()
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

@dashboardbp.route('/dashboard/sensor/<device_id>/<sensor_key>', methods=['GET'])
def get_combined_sensor_data(device_id, sensor_key):
    try:
        if not device_id.startswith("Device"):
            device_id = f"Device{device_id.zfill(2)}"
        if sensor_key not in SENSOR_TYPES:
            return jsonify({
                "error": f"Invalid sensor type: {sensor_key}",
                "message": "This sensor type is not supported"
            }), 400
        sensor = Sensor.query.filter_by(device_id=device_id, sensor_key=sensor_key).first()
        if not sensor:
            return jsonify({
                "error": f"Sensor {sensor_key} not found for device {device_id}",
                "message": "This sensor is not registered in the database"
            }), 404
        device_data = last_known_state.get(device_id, {}).get("data", {})
        response_data = {}
        if sensor_key in device_data:
            if sensor_key in ['reed_switch', 'photo_interrupter', 'pir']:
                state = device_data[sensor_key]
                if state not in SENSOR_TYPES[sensor_key].get('states', []):
                    state = 'UNKNOWN'
                response_data = {
                    "sensor_key": sensor_key,
                    "sensor_type": sensor_key,
                    "value": state,
                    "unit": "N/A",
                    "source": "mqtt",
                    "last_seen": "real-time"
                }
            else:
                response_data = {
                    "sensor_key": sensor_key,
                    "sensor_type": sensor_key,
                    "value": device_data[sensor_key],
                    "unit": SENSOR_TYPES[sensor_key].get('unit', 'N/A'),
                    "source": "mqtt",
                    "last_seen": "real-time"
                }
        else:
            if sensor:
                if sensor_key in ['reed_switch', 'photo_interrupter', 'pir']:
                    state = sensor.value
                    if state not in SENSOR_TYPES[sensor_key].get('states', []):
                        state = 'UNKNOWN'
                    response_data = {
                        "sensor_key": sensor.sensor_key,
                        "sensor_type": sensor.sensor_type,
                        "value": state,
                        "unit": "N/A",
                        "source": "database",
                        "last_seen": sensor.last_seen
                    }
                else:
                    response_data = {
                        "sensor_key": sensor.sensor_key,
                        "sensor_type": sensor.sensor_type,
                        "value": sensor.value,
                        "unit": SENSOR_TYPES.get(sensor.sensor_type, {}).get('unit', 'N/A'),
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


@dashboardbp.route('/dashboard/sensors')
@login_required
def get_sensors():
    user = User.query.filter_by(userid=current_user.userid).first()
    sensors = Sensor.query.filter_by(userid=user.userid).all()
    sensor_list = [{
        "sensor_id": sensor.id,
        "sensor_type": sensor.sensor_type,
        "value": sensor.value,
        "status": sensor.status
    } for sensor in sensors]
    return jsonify(sensor_list)


init_mqtt_client()

