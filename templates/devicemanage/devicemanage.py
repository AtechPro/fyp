from flask import Blueprint, request, jsonify, current_app
from flask import requests

# Device Management Blueprint
devicebp = Blueprint('device', __name__)

# In-memory store for registered devices
devices = {}  # Example: {"device_id": {"name": "Living Room Sensor", "status": "active"}}

# Route: Register a Device
@devicebp.route('/devices/register', methods=['POST'])
def register_device():
    try:
        data = request.json
        device_id = data.get('device_id')
        name = data.get('name')

        if not device_id or not name:
            return jsonify({"error": "Device ID and name are required."}), 400

        if device_id in devices:
            return jsonify({"error": f"Device {device_id} is already registered."}), 400

        # Register the device in the in-memory store
        devices[device_id] = {"name": name, "status": "active"}

        # Subscribe to the device's topics using MQTT blueprint
        mqtt_response = requests.post(f"http://localhost:5000/mqtt/subscribe/{device_id}")
        if mqtt_response.status_code != 200:
            return jsonify({"error": "Failed to subscribe to device topics."}), mqtt_response.status_code

        return jsonify({"success": True, "device": devices[device_id]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Get All Registered Devices
@devicebp.route('/devices', methods=['GET'])
def get_devices():
    return jsonify(devices), 200


# Route: Unregister a Device
@devicebp.route('/devices/unregister/<device_id>', methods=['POST'])
def unregister_device(device_id):
    try:
        if device_id not in devices:
            return jsonify({"error": f"Device {device_id} not found."}), 404

        # Remove the device from the in-memory store
        del devices[device_id]

        # Unsubscribe from the device's topics using MQTT blueprint
        mqtt_response = requests.post(f"http://localhost:5000/mqtt/unsubscribe/{device_id}")
        if mqtt_response.status_code != 200:
            return jsonify({"error": "Failed to unsubscribe from device topics."}), mqtt_response.status_code

        return jsonify({"success": True, "message": f"Device {device_id} unregistered."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route: Publish a Command to a Device
@devicebp.route('/devices/<device_id>/relay', methods=['POST'])
def control_device_relay(device_id):
    try:
        if device_id not in devices:
            return jsonify({"error": f"Device {device_id} not registered."}), 404

        data = request.json
        command = data.get('command')  # Example: "ON" or "OFF"

        if not command:
            return jsonify({"error": "Command is required."}), 400

        # Publish a relay command using MQTT blueprint
        mqtt_response = requests.post(
            f"http://localhost:5000/mqtt/publish/{device_id}/relay/command",
            json={"command": command}
        )
        if mqtt_response.status_code != 200:
            return jsonify({"error": "Failed to publish command to device."}), mqtt_response.status_code

        return jsonify({"success": True, "command": command}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
