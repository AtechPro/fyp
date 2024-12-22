from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import json
from threading import Thread
import time
from database.database import db, Device, Sensor

devicemanage_bp = Blueprint('devicemanage', __name__)

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt" 
BROKER_PORT = 1883
MQTT_TOPIC = "home/#"  
DEVICE_TIMEOUT = 3  # seconds
CHECK_INTERVAL = 3  # seconds

# In-memory device store
devices = {}

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the MQTT broker."""
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker with return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received from MQTT."""
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("deviceId")
        ip_address = payload.get("ip")

        if not device_id or not ip_address:
            print("Invalid MQTT message: missing deviceId or IP address.")
            return

        # Update or create device in memory
        if device_id not in devices:
            devices[device_id] = {
                "ip_address": ip_address,
                "status": "online",
                "last_seen": datetime.now().isoformat(),
                "sensors": {}
            }
        else:
            devices[device_id]["last_seen"] = datetime.now().isoformat()
            devices[device_id]["status"] = "online"

        # Update or add sensors from the MQTT payload
        for key, value in payload.items():
            if key not in ["deviceId", "ip"]:
                devices[device_id]["sensors"][key] = {
                    "value": value,
                    "status": "online",
                    "last_seen": datetime.now().isoformat()
                }
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def monitor_device_status():
    """Background task to monitor device status based on last seen time."""
    while True:
        now = datetime.now()
        for device_id, device_info in devices.items():
            last_seen = datetime.fromisoformat(device_info["last_seen"])

            # Check if the device has been offline for too long
            if (now - last_seen) > timedelta(seconds=DEVICE_TIMEOUT):
                if device_info["status"] != "offline":
                    device_info["status"] = "offline"
                    print(f"Device {device_id} marked as offline.")
            else:
                if device_info["status"] != "online":
                    device_info["status"] = "online"
                    print(f"Device {device_id} marked as online.")
        time.sleep(CHECK_INTERVAL)

# Start monitoring device status in the background
status_monitor_thread = Thread(target=monitor_device_status, daemon=True)
status_monitor_thread.start()

def init_mqtt_client():
    """Initialize and start the MQTT client."""
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

@devicemanage_bp.route('/device')
@login_required
def get_devices():
    """API to fetch device list."""
    user_id = current_user.get_id()  # Get the current logged in user
    device_list = []
    for device_id, device_info in devices.items():
        paired_device = Device.query.filter_by(device_id=device_id, userid=user_id).first()

        # Add device info to the response
        device_list.append({
            "device_id": device_id,
            "ip_address": device_info.get("ip_address", "N/A"),
            "status": device_info.get("status", "offline"),
            "last_seen": device_info.get("last_seen"),
            "paired": paired_device is not None,  # Check if the device is paired with the user
            "sensors": device_info.get("sensors", [])  # Include sensor data if available
        })

    return jsonify(device_list)

@devicemanage_bp.route('/devicemanage')
@login_required
def devicemanage():
    """Render the device management page."""
    device_list = [
        {
            "device_id": device_id,
            "ip_address": device_info["ip_address"],
            "status": device_info["status"],
            "last_seen": device_info["last_seen"],
            "sensors": device_info["sensors"]
        }
        for device_id, device_info in devices.items()
    ]
    return render_template('devicemanage/devicemanage.html', user=current_user, devices=device_list)

@devicemanage_bp.route('/add_device', methods=['POST'])
@login_required
def add_device():
    """API to add a new device and associated sensors."""
    data = request.get_json()
    device_id = data.get('device_id')
    user_id = current_user.get_id()

    # Check if the device already exists
    if Device.query.filter_by(device_id=device_id).first():
        return jsonify({"error": "Device already exists"}), 400

    # Create a new device entry
    new_device = Device(device_id=device_id, userid=user_id, status=True)
    db.session.add(new_device)

    # Categorize sensors
    def categorize_sensor_type(sensor_key, value):
        binary_states = ['ON', 'OFF', 'OPEN', 'CLOSED', 'CLEAR', 'TRIGGERED']
        
        if isinstance(value, str) and value.upper() in binary_states:
            if sensor_key in ['reed_switch', 'photo_interrupter']:
                return 'Contact Sensor'
            elif sensor_key == 'relay':
                return 'Relay'
        
        if isinstance(value, (int, float)):
            if sensor_key == 'temperature':
                return 'Temperature Sensor'
            elif sensor_key == 'humidity':
                return 'Humidity Sensor'
        
        return 'Unknown Sensor'
    if device_id in devices:
        device_info = devices[device_id]
        
        # Add sensors from the device's sensor information
        for sensor_key, sensor_data in device_info.get('sensors', {}).items():
            sensor_type = categorize_sensor_type(sensor_key, sensor_data.get('value'))
            
            new_sensor = Sensor(
                device_id=device_id,
                sensor_key=sensor_key,
                sensor_type=sensor_type,
                value=str(sensor_data.get('value')),
                status=sensor_data.get('status', 'online'),
                last_seen=datetime.now()
            )
            db.session.add(new_sensor)

    db.session.commit()
    return jsonify({"message": "Device and sensors added successfully"}), 201


@devicemanage_bp.route('/delete_device/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """API to delete a device and its associated sensors."""
    # Find the device
    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        return jsonify({"error": "Device not found"}), 404

    try:
        # Delete associated sensors first
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        for sensor in sensors:
            db.session.delete(sensor)

        # Delete the device itself
        db.session.delete(device)
        db.session.commit()

        return jsonify({"message": "Device and sensors deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()  # Rollback transaction in case of an error
        return jsonify({"error": f"Failed to delete device: {str(e)}"}), 500

init_mqtt_client()
