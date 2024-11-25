from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db, User 


usermanage = Blueprint('usermanage', __name__, template_folder='templates')


@usermanage.route('/users', methods=['GET'])
@login_required
def list_users():
  
    if not current_user.is_admin():
        return redirect(url_for('views.home'))

    users = User.query.all()
    return render_template('usermanage/usermanage.html', users=users)



@usermanage.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin():
        return redirect(url_for('index'))

    user = User.query.get_or_404(id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.name = request.form['name']
        
        # Check if the user being edited is the current admin
        if current_user.userid == user.userid and int(request.form['role']) != current_user.role:
            return redirect(url_for('usermanage.edit_user', userid=id))

        user.role = int(request.form['role'])  
        
        db.session.commit()
        return redirect(url_for('usermanage.list_users'))

    return render_template('usermanage/edit_user.html', user=user)




@usermanage.route('/delete_user/<int:userid>', methods=['POST'])
@login_required
def delete_user(userid):
    
    if not current_user.is_admin():
        return redirect(url_for('usermanage.list_users'))

    if current_user.userid == userid:
        return redirect(url_for('usermanage.list_users'))

    user = User.query.get_or_404(userid)
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while trying to delete the user: {str(e)}', 'error')

    return redirect(url_for('usermanage.list_users'))

@usermanage.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    # Ensure that only admins can access this route
    if not current_user.is_admin():
        return redirect(url_for('usermanage.list_users'))

    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            return redirect(url_for('usermanage.add_user'))

        role = int(request.form['role'])  

        # Create new user
        new_user = User(username=username, name=name, role=role, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('usermanage.list_users'))

    return render_template('usermanage/usermanage.html')

