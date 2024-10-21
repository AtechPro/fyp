from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db, User 


usermanage = Blueprint('usermanage', __name__, template_folder='templates')


@usermanage.route('/users', methods=['GET'])
@login_required
def list_users():
  
    if not current_user.is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('index'))

    users = User.query.all()
    return render_template('usermanage/usermanage.html', users=users)

@usermanage.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        # Update user details
        user.username = request.form['username']
        user.name = request.form['name']
        user.role = int(request.form['role'])  # Convert role to integer (1 for Admin, 0 for User)
        db.session.commit()
        flash("User updated successfully.")
        return redirect(url_for('usermanage.list_users'))

    return render_template('usermanage/edit_user.html', user=user)

@usermanage.route('/users/delete/<int:id>', methods=['POST'])
@login_required
def delete_user(id):
    if not current_user.is_admin():
        flash("Access denied. Admins only.")
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.")
    return redirect(url_for('list_users'))
