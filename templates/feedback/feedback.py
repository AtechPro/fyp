from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db, User, Feedback 

feedbackbp = Blueprint('feedback', __name__, template_folder='templates')

@feedbackbp.route('/feedbacks', methods=['GET', 'POST'])
@login_required
def submit_feedback():  
    if request.method == 'POST':
        feedback_title = request.form['feedback_title']
        feedback_desc = request.form['feedback_desc']
        
        if not feedback_title or not feedback_desc:
            flash('Both title and description are required.', 'error')
            return redirect(url_for('feedback.submit_feedback'))  

        new_feedback = Feedback(
            userid=current_user.userid,
            feedback_title=feedback_title,
            feedback_desc=feedback_desc
        )
        
        db.session.add(new_feedback)
        db.session.commit()
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('feedback.submit_feedback'))  

    return render_template('feedback/feedback.html')


@feedbackbp.route('/feedbacks/admin', methods=['GET'])
@login_required
def view_admin_feedbacks():
    if current_user.role != 1:  # Assuming role 1 is for admin
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('feedback.submit_feedback'))  

    admin_feedbacks = Feedback.query.all()  # Get all feedbacks from database
    return render_template('feedback/adminfeedback.html', feedbacks=admin_feedbacks)


@feedbackbp.route('/feedbacks/user', methods=['GET'])
@login_required
def view_user_feedbacks():
    user_feedbacks = Feedback.query.filter_by(userid=current_user.userid).all()
    return render_template('feedback/userfeedback.html', feedbacks=user_feedbacks)

@feedbackbp.route('/feedbacks/edit/<int:feedback_id>', methods=['GET', 'POST'])
@login_required
def edit_feedback(feedback_id):
    # Get the feedback by its ID
    edit_feedback = Feedback.query.get_or_404(feedback_id)
    if edit_feedback.userid != current_user.userid:
        flash('You cannot edit feedback that does not belong to you.', 'error')
        return redirect(url_for('feedback.view_user_feedbacks'))
    if request.method == 'POST':
        edit_feedback.comment = request.form['comment']
        db.session.commit()
        flash('Feedback updated successfully!', 'success')
        return redirect(url_for('feedback.view_user_feedbacks')) 
    
    return render_template('feedback/edit_feedback.html', feedback=edit_feedback) #will do this html later

@feedbackbp.route('/feedbacks/delete/<int:feedback_id>', methods=['POST'])
@login_required
def delete_feedback(feedback_id):
    # Get the feedback by its ID
    del_feedback = Feedback.query.get_or_404(feedback_id)
    if del_feedback.userid != current_user.userid:
        flash('You cannot delete feedback that does not belong to you.', 'error')
        return redirect(url_for('feedback.view_user_feedbacks'))
    
    # Delete the feedback from the database
    db.session.delete(del_feedback)
    db.session.commit() 
    
    flash('Feedback deleted successfully!', 'success')
    return redirect(url_for('feedback.view_user_feedbacks'))  