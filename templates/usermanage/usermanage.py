from flask import Blueprint, jsonify, request, render_template, url_for, redirect
from flask_login import login_required, current_user
from database.database import db, User

usermanage = Blueprint('usermanage', __name__, template_folder='templates')


@usermanage.route('/userslists', methods=['GET'])
@login_required
def list_users():
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    users = User.query.all()
    users_data = [{
        'userid': user.userid,
        'username': user.username,
        'name': user.name,
        'role': user.role,
        'session_id': user.session_id  # Include session_id in the response
    } for user in users]

    return jsonify({'status': 'success', 'users': users_data})


# Add a new user
@usermanage.route('/users/add', methods=['POST'])
@login_required
def add_user():
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    username = data.get('username')
    name = data.get('name')
    password = data.get('password')
    role = int(data.get('role', 0))  # Default role is 0 (User)

    if not username or not name or not password:
        return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'status': 'error', 'message': 'Username already exists'}), 400

    new_user = User(username=username, name=name, role=role, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'User added successfully'})


# Edit a user
@usermanage.route('/users/edit/<int:userid>', methods=['PUT'])
@login_required
def edit_user(userid):
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    user = User.query.get_or_404(userid)
    data = request.get_json()

    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400

    # Prevent admins from changing their own role
    if current_user.userid == user.userid and 'role' in data and int(data['role']) != current_user.role:
        return jsonify({'status': 'error', 'message': 'Cannot change your own role'}), 400

    # Update user fields
    if 'username' in data:
        user.username = data['username']
    if 'name' in data:
        user.name = data['name']
    if 'role' in data:
        user.role = int(data['role'])
    if 'password' in data:
        user.password = data['password']

    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User updated successfully'})


# Delete a user
@usermanage.route('/users/delete/<int:userid>', methods=['DELETE'])
@login_required
def delete_user(userid):
    if not current_user.is_admin():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

    if current_user.userid == userid:
        return jsonify({'status': 'error', 'message': 'Cannot delete yourself'}), 400

    user = User.query.get_or_404(userid)
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500


# Render the user management page
@usermanage.route('/users', methods=['GET'])
@login_required
def manage_users_page():
    if not current_user.is_admin():
        return redirect(url_for('views.home'))

    return render_template('usermanage/usermanage.html')