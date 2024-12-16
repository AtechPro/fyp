from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import json
from threading import Thread
import time
from database.database import db, Device  # Assuming you have a Device model

# Flask Blueprint
devicemanage_bp = Blueprint('devicemanage', __name__)

# Configuration for MQTT
BROKER_ADDRESS = "atechpromqtt"  # Replace with your MQTT broker's address
BROKER_PORT = 1883
MQTT_TOPIC = "home/#"  # MQTT topic to subscribe to
DEVICE_TIMEOUT = 5  # Timeout in seconds to mark a device as offline
CHECK_INTERVAL = 3  # Interval in seconds to check device statuses

# In-memory storage for devices and sensors
devices = {}

# MQTT Client
mqtt_client = mqtt.Client()

# MQTT Event Handlers
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker with return code {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        device_id = payload.get("deviceId")
        ip_address = payload.get("ip")

        if not device_id or not ip_address:
            print("Invalid MQTT message: missing deviceId or IP address.")
            return

        # Debugging: Print the received payload
        # print(f"Received MQTT message: {payload}")

        # Update or create device in memory
        if device_id not in devices:
            devices[device_id] = {
                "ip_address": ip_address,
                "status": "online",
                "last_seen": datetime.now().isoformat(),
                "sensors": {}
            }
            #print(f"Added new device: {device_id}")
        else:
            devices[device_id]["last_seen"] = datetime.now().isoformat()
            devices[device_id]["status"] = "online"
            #print(f"Updated device: {device_id}")

        # Update or add sensors
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
    """ Background task to check and update device statuses """
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
                    
        time.sleep(CHECK_INTERVAL)  # Check the devices periodically


# Start Background Task
status_monitor_thread = Thread(target=monitor_device_status, daemon=True)
status_monitor_thread.start()

# Initialize MQTT Client
def init_mqtt_client():
    """ Initialize the MQTT client and connect to the broker """
    try:
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.connect(BROKER_ADDRESS, BROKER_PORT)
        mqtt_client.loop_start()
    except Exception as e:
        print(f"Error connecting to MQTT broker: {e}")

# Route for Device Management Page
@devicemanage_bp.route('/devicemanage')
@login_required
def devicemanage():
    # Ensure devices from memory are passed to the template
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


@devicemanage_bp.route('/devices')
@login_required
def get_devices():
    """ Fetch devices for the logged-in user """
    user_id = current_user.get_id()  # Assuming Flask-Login is used

    # Query devices in memory and compare with database entries
    device_list = []
    for device_id, device_info in devices.items():
        paired_device = Device.query.filter_by(device_id=device_id, userid=user_id).first()

        device_list.append({
            "device_id": device_id,
            "ip_address": device_info.get("ip_address", "N/A"),
            "status": device_info.get("status", "offline"),
            "last_seen": device_info.get("last_seen"),
            "paired": paired_device is not None,  # True if the device exists in the database
            "sensors": device_info.get("sensors", [])
        })

    return jsonify(device_list)


@devicemanage_bp.route('/add_device', methods=['POST'])
def add_device():
    data = request.get_json()
    device_id = data.get('device_id')
    user_id = current_user.get_id()  # Assuming Flask-Login is used

    # Check if device already exists
    if Device.query.filter_by(device_id=device_id).first():
        return jsonify({"error": "Device already exists"}), 400

    new_device = Device(device_id=device_id, userid=user_id)
    db.session.add(new_device)
    db.session.commit()
    return jsonify({"message": "Device added successfully"}), 201


@devicemanage_bp.route('/delete_device/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    device = Device.query.filter_by(device_id=device_id).first()

    if not device:
        return jsonify({"error": "Device not found"}), 404

    db.session.delete(device)
    db.session.commit()
    return jsonify({"message": "Device deleted successfully"}), 200

init_mqtt_client()
