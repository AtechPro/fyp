import os
import shutil
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, render_template, url_for, redirect
from flask_login import current_user

# Define the blueprint
backup_restore_bp = Blueprint('backup_restore', __name__, template_folder='templates/backuprestore')

# Resolve the absolute path of the database based on the current working directory
project_root = os.getcwd()  # Get the current working directory (where the app is run from)
DB_PATH = os.path.join(project_root, 'database', 'database.db')  # Absolute path to the database file
BACKUP_DIR = os.path.join(project_root, 'backups')  # Backup directory relative to the project root

# Helper function to get the timestamped backup filename
def get_backup_filename():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(BACKUP_DIR, f'backup_{timestamp}.db')

# Route to backup the database (copy the .db file)
@backup_restore_bp.route('/backup', methods=['GET'])
def backup_database():
    try:
        # Create backup directory if it doesn't exist
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # Backup filename with timestamp
        backup_filename = get_backup_filename()

        # Check if the database file exists before proceeding
        if not os.path.exists(DB_PATH):
            return jsonify({'error': f'Database file not found: {DB_PATH}'}), 500

        # Copy the database file to the backup location
        shutil.copy(DB_PATH, backup_filename)

        # Send the backup file to the client
        return send_file(
            backup_filename,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        )

    except Exception as e:
        return jsonify({'error': f'Error during backup: {str(e)}'}), 500

# Route to restore the database from a backup (overwrite .db file)
@backup_restore_bp.route('/restore', methods=['POST'])
def restore_database():
    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file provided'}), 400

        backup_file = request.files['backup_file']
        if backup_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check if the uploaded file is a valid backup
        if not backup_file.filename.endswith('.db'):
            return jsonify({'error': 'Invalid backup file format. Only .db files are allowed.'}), 400

        # Get the backup filename and save it temporarily
        backup_file_path = os.path.join(BACKUP_DIR, backup_file.filename)
        backup_file.save(backup_file_path)

        # Check if the backup file is different from the current database file
        if os.path.samefile(DB_PATH, backup_file_path):
            return jsonify({'message': 'The backup file is the same as the current database. No restore needed.'}), 200

        # Restore the database by overwriting the current .db file
        shutil.copy(backup_file_path, DB_PATH)

        return jsonify({'message': 'Database restored successfully'}), 200

    except Exception as e:
        return jsonify({'error': f'Error during restore: {str(e)}'}), 500

# Helper route to get list of available backups
@backup_restore_bp.route('/backups', methods=['GET'])
def list_backups():
    try:
        if not os.path.exists(BACKUP_DIR):
            return jsonify({'backups': []})

        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.endswith('.db'):
                file_path = os.path.join(BACKUP_DIR, filename)
                file_stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'size': file_stat.st_size,
                    'created_at': datetime.fromtimestamp(file_stat.st_ctime).isoformat()
                })

        # Return backups sorted by creation date (descending)
        return jsonify({'backups': sorted(backups, key=lambda x: x['created_at'], reverse=True)})

    except Exception as e:
        return jsonify({'error': f'Error listing backups: {str(e)}'}), 500


# Route to download a specific backup file
@backup_restore_bp.route('/backups/<filename>', methods=['GET'])
def download_backup(filename):
    try:
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404

        return send_file(
            backup_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'Error downloading backup: {str(e)}'}), 500


# Route to delete a specific backup file
@backup_restore_bp.route('/backups/<filename>', methods=['DELETE'])
def delete_backup(filename):
    try:
        # Full path of the backup file to delete
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        # Check if the file exists before trying to delete it
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404

        # Remove the backup file
        os.remove(backup_path)

        return jsonify({'message': f'Backup "{filename}" deleted successfully.'}), 200

    except Exception as e:
        return jsonify({'error': f'Error deleting backup: {str(e)}'}), 500



# Render the backup/restore UI page
@backup_restore_bp.route('/backup_restore')
def backup_restore_page():
    if current_user.role != 1:
        # Redirect to home page if user is not authorized
        return redirect(url_for('dashboard.dashboard'))  # Replace 'home' with the name of your home route
    
    return render_template('backuprestore/backuprestore.html')
