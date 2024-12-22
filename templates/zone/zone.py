from flask import Flask, Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from database.database import db, Zone, ZoneSensor, Sensor

zone_bp = Blueprint('zone', __name__)

# Helper Functions
def get_sensor_zone(sensor_id):
    """Get the zone information for a specific sensor."""
    zone_sensor = ZoneSensor.query.filter_by(sensor_id=sensor_id).first()
    if zone_sensor:
        return Zone.query.get(zone_sensor.zone_id)
    return None

def get_unassigned_sensors(userid):
    """Get all sensors that aren't assigned to any zone."""
    assigned_sensors = db.session.query(ZoneSensor.sensor_id)
    return Sensor.query.filter_by(userid=userid).filter(
        ~Sensor.sensor_id.in_(assigned_sensors)
    ).all()

def create_zone_with_sensors(zone_name, zone_desc, sensor_ids, userid):
    """Create a new zone and assign multiple sensors to it."""
    # Check if zone exists
    existing_zone = Zone.query.filter_by(name=zone_name, userid=userid).first()
    if existing_zone:
        return "Zone already exists.", 400

    # Create new zone
    new_zone = Zone(
        name=zone_name,
        description=zone_desc,
        userid=userid
    )
    db.session.add(new_zone)
    db.session.flush()  # Get the zone ID without committing

    # Assign sensors
    already_assigned = []
    newly_assigned = []
    
    for sensor_id in sensor_ids:
        existing = ZoneSensor.query.filter_by(sensor_id=sensor_id).first()
        if existing:
            already_assigned.append(sensor_id)
            continue
            
        new_link = ZoneSensor(zone_id=new_zone.zid, sensor_id=sensor_id)
        db.session.add(new_link)
        newly_assigned.append(sensor_id)

    db.session.commit()
    
    response = {
        "message": f"Zone '{zone_name}' created successfully.",
        "newly_assigned": newly_assigned,
        "already_assigned": already_assigned
    }
    return response, 200

def bulk_reassign_sensors(zone_id, sensor_ids):
    """Reassign multiple sensors to a different zone."""
    zone = Zone.query.get(zone_id)
    if not zone:
        return "Zone not found.", 404

    success = []
    already_in_zone = []
    not_found = []

    for sensor_id in sensor_ids:
        sensor = Sensor.query.get(sensor_id)
        if not sensor:
            not_found.append(sensor_id)
            continue

        existing = ZoneSensor.query.filter_by(sensor_id=sensor_id).first()
        if existing:
            if existing.zone_id == zone_id:
                already_in_zone.append(sensor_id)
                continue
            # Remove from old zone
            db.session.delete(existing)

        # Add to new zone
        new_link = ZoneSensor(zone_id=zone_id, sensor_id=sensor_id)
        db.session.add(new_link)
        success.append(sensor_id)

    db.session.commit()
    
    return {
        "message": f"Sensors reassigned to zone '{zone.name}'",
        "success": success,
        "already_in_zone": already_in_zone,
        "not_found": not_found
    }, 200

# Flask Endpoints
@zone_bp.route('/zone', methods=['GET'])
@login_required
def zone_page():
    return render_template('zone/zone.html')

@zone_bp.route('/create', methods=['POST'])
@login_required
def create_zone_endpoint():
    data = request.json
    result, status_code = create_zone_with_sensors(
        data['zone_name'],
        data.get('zone_desc', ''),
        data.get('sensor_ids', []),
        current_user.userid
    )
    return jsonify(result), status_code

@zone_bp.route('/reassign/<int:zone_id>', methods=['POST'])
@login_required
def reassign_sensors_endpoint(zone_id):
    data = request.json
    result, status_code = bulk_reassign_sensors(zone_id, data['sensor_ids'])
    return jsonify(result), status_code

@zone_bp.route('/unassigned-sensors', methods=['GET'])
@login_required
def get_unassigned_sensors_endpoint():
    sensors = get_unassigned_sensors(current_user.userid)
    return jsonify([{
        "sensor_id": sensor.sensor_id,
        "sensor_key": sensor.sensor_key,
        "name": sensor.name
    } for sensor in sensors])

@zone_bp.route('/sensor/<int:sensor_id>/zone', methods=['GET'])
@login_required
def get_sensor_zone_endpoint(sensor_id):
    zone = get_sensor_zone(sensor_id)
    if zone:
        return jsonify({
            "zone_id": zone.zid,
            "name": zone.name,
            "description": zone.description
        })
    return jsonify({"message": "Sensor not assigned to any zone"}), 404

@zone_bp.route('/zones/with-sensors', methods=['GET'])
@login_required
def get_zones_with_sensors():
    zones = Zone.query.filter_by(userid=current_user.userid).all()
    result = []
    
    for zone in zones:
        zone_sensors = ZoneSensor.query.filter_by(zone_id=zone.zid).all()
        sensors = [{
            "sensor_id": zs.sensor.sensor_id,
            "sensor_key": zs.sensor.sensor_key,
            "name": zs.sensor.name
        } for zs in zone_sensors]
        
        result.append({
            "zone_id": zone.zid,
            "name": zone.name,
            "description": zone.description,
            "sensors": sensors
        })
    
    return jsonify(result)