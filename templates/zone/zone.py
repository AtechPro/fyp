from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from database.database import db, User, Zone, ZoneSensor, Sensor, SensorType

zone_bp = Blueprint('zone', __name__)

# Utility Functions
def get_user_zones(user_id):
    """Get all zones for a specific user with their sensors."""
    zones = Zone.query.filter_by(user_id=user_id).all()
    zones_data = []
    
    for zone in zones:
        sensors = []
        for zs in zone.sensors:
            sensor = Sensor.query.get(zs.sensor_id)
            if sensor:
                sensor_type = SensorType.query.get(sensor.sensor_type_id)
                sensors.append({
                    "sensor_id": sensor.id,
                    "name": sensor.sensor_key,
                    "type": sensor_type.type_key if sensor_type else "Unknown",
                    "display_name": sensor_type.display_name if sensor_type else "Unknown",
                    "unit": sensor_type.unit if sensor_type else None
                })
        
        zones_data.append({
            "zone_id": zone.id,
            "name": zone.name,
            "description": zone.description,
            "sensors": sensors
        })
    
    return zones_data

def get_unassigned_sensors(user_id):
    """Get all sensors not assigned to any zone."""
    # Get all assigned sensor IDs
    assigned_sensors = db.session.query(ZoneSensor.sensor_id).all()
    assigned_sensor_ids = [s[0] for s in assigned_sensors]
    
    # Query for unassigned sensors
    unassigned = Sensor.query.filter(
        ~Sensor.id.in_(assigned_sensor_ids),
        Sensor.userid == user_id
    ).all()
    
    sensors_data = []
    for sensor in unassigned:
        sensor_type = SensorType.query.get(sensor.sensor_type_id)
        sensors_data.append({
            "sensor_id": sensor.id,
            "name": sensor.sensor_key,
            "type": sensor_type.type_key if sensor_type else "Unknown",
            "display_name": sensor_type.display_name if sensor_type else "Unknown",
            "unit": sensor_type.unit if sensor_type else None
        })
    
    return sensors_data

def create_new_zone(user_id, name, description, sensor_ids):
    """Create a new zone with the given sensors."""
    try:
        # Check if zone name already exists for this user
        existing = Zone.query.filter_by(user_id=user_id, name=name).first()
        if existing:
            return False, "Zone name already exists"
        
        # Create new zone
        zone = Zone(
            user_id=user_id,
            name=name,
            description=description
        )
        db.session.add(zone)
        db.session.flush()  # Get the zone ID
        
        # Add sensors to zone
        for sensor_id in sensor_ids:
            # Check if sensor exists and belongs to the user
            sensor = Sensor.query.filter_by(id=sensor_id, userid=user_id).first()
            if not sensor:
                continue
                
            # Check if sensor already assigned
            existing_assignment = ZoneSensor.query.filter_by(sensor_id=sensor_id).first()
            if existing_assignment:
                continue
                
            zone_sensor = ZoneSensor(zone_id=zone.id, sensor_id=sensor_id)
            db.session.add(zone_sensor)
        
        db.session.commit()
        return True, "Zone created successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def delete_zone(user_id, zone_id):
    """Delete a zone if it belongs to the user."""
    try:
        zone = Zone.query.filter_by(id=zone_id, user_id=user_id).first()
        if not zone:
            return False, "Zone not found"
            
        db.session.delete(zone)
        db.session.commit()
        return True, "Zone deleted successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)

def update_zone(user_id, zone_id, name, description, sensor_ids):
    """Update an existing zone."""
    try:
        # Check if zone exists and belongs to user
        zone = Zone.query.filter_by(id=zone_id, user_id=user_id).first()
        if not zone:
            return False, "Zone not found"
        
        # Check if new name conflicts with existing zones
        if name != zone.name:
            existing = Zone.query.filter_by(user_id=user_id, name=name).first()
            if existing:
                return False, "Zone name already exists"
        
        # Update zone details
        zone.name = name
        zone.description = description
        
        # Remove existing sensor associations
        ZoneSensor.query.filter_by(zone_id=zone_id).delete()
        
        # Add new sensor associations
        for sensor_id in sensor_ids:
            # Check if sensor exists and belongs to the user
            sensor = Sensor.query.filter_by(id=sensor_id, userid=user_id).first()
            if not sensor:
                continue
                
            zone_sensor = ZoneSensor(zone_id=zone_id, sensor_id=sensor_id)
            db.session.add(zone_sensor)
        
        db.session.commit()
        return True, "Zone updated successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)

# Routes
@zone_bp.route('/api/zone', methods=['GET'])
@login_required
def get_zones():
    """Get all zones for the current user."""
    zones = get_user_zones(current_user.userid)
    return jsonify(zones)

@zone_bp.route('/api/unassigned-sensors', methods=['GET'])
@login_required
def unassigned_sensors():
    """Get all unassigned sensors."""
    sensors = get_unassigned_sensors(current_user.userid)
    return jsonify(sensors)

@zone_bp.route('/api/zone', methods=['POST'])
@login_required
def create_zone():
    """Create a new zone."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({"error": "Zone name is required"}), 400
        
    success, message = create_new_zone(
        user_id=current_user.userid,
        name=data['name'],
        description=data.get('description', ''),
        sensor_ids=data.get('sensor_ids', [])
    )
    
    if success:
        return jsonify({"message": message}), 201
    return jsonify({"error": message}), 400

@zone_bp.route('/api/zone/<int:zone_id>', methods=['PUT'])
@login_required
def update_zone_route(zone_id):
    """Update an existing zone."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({"error": "Zone name is required"}), 400
        
    success, message = update_zone(
        user_id=current_user.userid,
        zone_id=zone_id,
        name=data['name'],
        description=data.get('description', ''),
        sensor_ids=data.get('sensor_ids', [])
    )
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 400

@zone_bp.route('/api/zone/<int:zone_id>', methods=['DELETE'])
@login_required
def remove_zone(zone_id):
    """Delete a zone."""
    success, message = delete_zone(current_user.userid, zone_id)
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 400

@zone_bp.route('/zone', methods=['GET'])
@login_required
def zone_management():
    """Render the zone management page."""
    return render_template('zone/zonemanage.html')

# Debug routes - should be disabled in production
@zone_bp.route('/debug/zones', methods=['GET'])
def debug_get_zones():
    """Debug route to retrieve all zones and their sensors."""
    zones = Zone.query.all()
    response = []

    for zone in zones:
        sensors = []
        for zs in zone.sensors:
            sensor = Sensor.query.get(zs.sensor_id)
            if sensor:
                sensor_type = SensorType.query.get(sensor.sensor_type_id)
                sensors.append({
                    "sensor_id": sensor.id,
                    "name": sensor.sensor_key,
                    "type": sensor_type.type_key if sensor_type else "Unknown",
                    "display_name": sensor_type.display_name if sensor_type else "Unknown",
                    "unit": sensor_type.unit if sensor_type else None
                })
        
        response.append({
            "zone_id": zone.id,
            "name": zone.name,
            "description": zone.description,
            "user_id": zone.user_id,
            "sensors": sensors
        })

    return jsonify(response), 200

# Add this utility function
def update_zone_details(user_id, zone_id, name, description):
    """Update only the name and description of a zone."""
    try:
        # Check if zone exists and belongs to the user
        zone = Zone.query.filter_by(id=zone_id, user_id=user_id).first()
        if not zone:
            return False, "Zone not found"
        
        # Check if the new name conflicts with existing zones
        if name != zone.name:
            existing = Zone.query.filter_by(user_id=user_id, name=name).first()
            if existing:
                return False, "Zone name already exists"
        
        # Update zone details
        zone.name = name
        zone.description = description
        
        db.session.commit()
        return True, "Zone details updated successfully"
        
    except Exception as e:
        db.session.rollback()
        return False, str(e)

# Add this route
@zone_bp.route('/api/zone/<int:zone_id>/details', methods=['PUT'])
@login_required
def update_zone_details_route(zone_id):
    """Update only the name and description of a zone."""
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({"error": "Zone name is required"}), 400
        
    success, message = update_zone_details(
        user_id=current_user.userid,
        zone_id=zone_id,
        name=data['name'],
        description=data.get('description', '')
    )
    
    if success:
        return jsonify({"message": message}), 200
    return jsonify({"error": message}), 400