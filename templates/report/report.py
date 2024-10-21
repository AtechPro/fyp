from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from database.database import db, User, Report 

report_module = Blueprint('report', __name__, template_folder='templates')

@report_module.route('/report', methods=['GET', 'POST'])
@login_required
def submit_report():  
    if request.method == 'POST':
        report_title = request.form['report_title']
        report_desc = request.form['report_desc']
        
        
        if not report_title or not report_desc:
            flash('Both title and description are required.', 'error')
            return redirect(url_for('report.submit_report'))  

        new_report = Report(
            userid=current_user.userid,
            username=current_user.username,
            report_title=report_title,
            report_desc=report_desc
        )
        
        db.session.add(new_report)
        db.session.commit()
        flash('Report submitted successfully', 'success')
        return redirect(url_for('report.submit_report'))  

    return render_template('report/report.html')


@report_module.route('/admin/reports', methods=['GET'])
@login_required
def view_admin_reports():
    if current_user.role != 1:  # Assuming role 1 is for admin
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('report.submit_report'))  

    reports = Report.query.all()  
    return render_template('report/adminreport.html', reports=reports)