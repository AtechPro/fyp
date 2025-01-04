from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from database.database import db, Feedback

feedbackbp = Blueprint('feedback', __name__)

# Serve the feedback.html template
@feedbackbp.route('/feedback', methods=['GET'])
@login_required
def feedback_page():
    return render_template('feedback/feedback.html')

# Submit Feedback (JSON)
@feedbackbp.route('/feedbacks', methods=['POST'])
@login_required
def submit_feedback():
    data = request.get_json()
    feedback_title = data.get('feedback_title')
    feedback_desc = data.get('feedback_desc')

    if not feedback_title or not feedback_desc:
        return jsonify({'error': 'Both title and description are required.'}), 400

    new_feedback = Feedback(
        userid=current_user.userid,
        feedback_title=feedback_title,
        feedback_desc=feedback_desc
    )
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify({'message': 'Feedback submitted successfully!'}), 201

# Get Feedbacks (JSON)
@feedbackbp.route('/feedbacks', methods=['GET'])
@login_required
def get_feedbacks():
    if current_user.role == 1:  # Admin
        feedbacks = Feedback.query.all()  # Admins can see all feedbacks
    else:  # Regular user
        feedbacks = Feedback.query.filter_by(userid=current_user.userid).all()  # Users can only see their own feedbacks

    feedback_list = [{
        'feedback_id': fb.feedback_id,
        'userid': fb.userid,
        'feedback_title': fb.feedback_title,
        'feedback_desc': fb.feedback_desc
    } for fb in feedbacks]

    return jsonify(feedback_list), 200

# Edit Feedback (JSON)
@feedbackbp.route('/feedbacks/<int:feedback_id>', methods=['PUT'])
@login_required
def edit_feedback(feedback_id):
    feedback_to_edit = Feedback.query.get_or_404(feedback_id)

    # Admins can edit any feedback, but users can only edit their own
    if current_user.role != 1 and feedback_to_edit.userid != current_user.userid:
        return jsonify({'error': 'You do not have permission to edit this feedback.'}), 403

    data = request.get_json()
    feedback_to_edit.feedback_title = data.get('feedback_title', feedback_to_edit.feedback_title)
    feedback_to_edit.feedback_desc = data.get('feedback_desc', feedback_to_edit.feedback_desc)
    db.session.commit()
    return jsonify({'message': 'Feedback updated successfully!'}), 200

# Delete Feedback (JSON)
@feedbackbp.route('/feedbacks/<int:feedback_id>', methods=['DELETE'])
@login_required
def delete_feedback(feedback_id):
    feedback_to_delete = Feedback.query.get_or_404(feedback_id)

    # Admins can delete any feedback, but users can only delete their own
    if current_user.role != 1 and feedback_to_delete.userid != current_user.userid:
        return jsonify({'error': 'You do not have permission to delete this feedback.'}), 403

    db.session.delete(feedback_to_delete)
    db.session.commit()
    return jsonify({'message': 'Feedback deleted successfully!'}), 200