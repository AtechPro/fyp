from flask import request, jsonify, Blueprint
#from database.database import Device 

# In-memory device list for simplicity (replace with database in production)
device_management = Blueprint('device_management', __name__, template_folder='templates')
devices = []

@device_management.route('/devices', methods=['GET'])
def list_devices():
    """Return a list of all registered devices."""
    return jsonify({'devices': devices}), 200

@device_management.route('/devices', methods=['POST'])
def add_device():
    """Add a new device to the list."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    device_id = data.get('deviceId')
    ip_address = data.get('ip')
    
    if not device_id or not ip_address:
        return jsonify({'error': 'deviceId and ip are required'}), 400
    
    # Check if the device already exists
    for device in devices:
        if device['deviceId'] == device_id:
            return jsonify({'error': 'Device already exists'}), 409

    # Add the device
    new_device = {'deviceId': device_id, 'ip': ip_address}
    devices.append(new_device)
    return jsonify(new_device), 201

@device_management.route('/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device by its deviceId."""
    global devices
    devices = [device for device in devices if device['deviceId'] != device_id]
    return jsonify({'message': f'Device {device_id} removed'}), 200
