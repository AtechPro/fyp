from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db, User, Feedback 

feedbackbp = Blueprint('feedback', __name__, template_folder='templates')

@feedbackbp.route('/feedback', methods=['GET', 'POST'])
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
            username=current_user.username,
            feedback_title=feedback_title,
            feedback_desc=feedback_desc
        )
        
        db.session.add(new_feedback)
        db.session.commit()
        flash('Feedback submitted successfully', 'success')
        return redirect(url_for('feedback.submit_feedback'))  

    return render_template('feedback/feedback.html')


@feedbackbp.route('/admin/feedbacks', methods=['GET'])
@login_required
def view_admin_feedbacks():
    if current_user.role != 1:  # Assuming role 1 is for admin
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('feedback.submit_feedback'))  

    feedbacks = Feedback.query.all()  
    return render_template('feedback/adminfeedback.html', feedbacks=feedbacks)

@feedbackbp.route('/user/feedbacks', methods=['GET'])
@login_required
def view_user_feedbacks():
    user_feedbacks = Feedback.query.filter_by(userid=current_user.userid).all()
    return render_template('feedback/userfeedback.html', feedbacks=user_feedbacks)
