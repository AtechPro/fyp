from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from database.database import db, User  # Import User and db

# Create a blueprint for user management
usermanage = Blueprint('usermanage', __name__, template_folder='templates')

# List all users (view-only page)
@usermanage.route('/users', methods=['GET'])
@login_required
def list_users():
    # Only admins should be able to access this
    if not current_user.is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('usermanage/usermanage.html', users=users)
