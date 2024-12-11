from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
import paho.mqtt.client as mqtt
import json
from database.database import db, User  # Assuming these are defined in your database module

# Flask Blueprint
devicemanage_bp = Blueprint('devicemanage', __name__)

# In-memory storage for devices and sensors
devices = {}

# MQTT Configuration
BROKER_ADDRESS = "atechpromqtt"  # Replace with your MQTT broker's address
BROKER_PORT = 1883
MQTT_TOPIC = "home/#"  # MQTT topic to subscribe to

# MQTT Client
mqtt_client = mqtt.Client()

# MQTT Event Handlers
def on_connect(client, userdata, flags, rc):
    """ Callback for MQTT connection event """
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT broker with return code {rc}")

def on_message(client, userdata, msg):
    """ Callback for MQTT message event """
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

# Route for Device Management page
@devicemanage_bp.route('/devicemanage')
@login_required
def devicemanage():
    """ Render Device Management page for logged-in users """
    return render_template('devicemanage/devicemanage.html', user=current_user)

# API Endpoint for devices
@devicemanage_bp.route('/devices')
@login_required
def get_devices():
    """ Fetch devices for the logged-in user """
    # Assuming devices are globally shared. Modify this if devices are user-specific.
    return jsonify(devices)

# API Endpoint to add or update a device (if needed)
@devicemanage_bp.route('/devices', methods=['POST'])
@login_required
def add_device():
    """ Add a new device or update an existing one """
    try:
        payload = request.json
        device_id = payload.get("deviceId")
        ip_address = payload.get("ip")

        if not device_id or not ip_address:
            return jsonify({"error": "Missing deviceId or IP address"}), 400

        # Add or update the device in memory
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

        return jsonify({"message": "Device added/updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process the request: {e}"}), 500

# Initialize MQTT client on blueprint import
init_mqtt_client()
