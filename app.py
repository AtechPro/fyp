from flask import Flask
from database.database import db, User 
from view import views
from templates.usermanage.usermanage import usermanage
from templates.feedback.feedback import feedbackbp
from templates.dashboard.dashboard import dashboardbp
from templates.devicemanage.devicemanage import devicemanage_bp
from flask_login import LoginManager
from datetime import timedelta
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/database.db'  # Database location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "mysecretkey"  
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

app.register_blueprint(views) 
app.register_blueprint(usermanage)
app.register_blueprint(feedbackbp)

app.register_blueprint(devicemanage_bp)
app.register_blueprint(dashboardbp)

#initialized socketio
# socketio.init_app(app)

# Initialize the database
db.init_app(app)

# Initialize the Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'views.login'  


def create_initial_user(app):
    with app.app_context():
        db.create_all()  
        if not User.query.filter_by(username='admin').first():  
            admin_user = User(
                username='admin',
                name='Administrator',
                role=1,  # Admin role
                password='admin'  
            )
            db.session.add(admin_user) 
            db.session.commit()  
            print("Initial admin user created.")
        else:
            print("Admin user already exists.")


@login_manager.user_loader
def load_user(userid):
    return db.session.get(User, int(userid))

if __name__ == '__main__':
    with app.app_context():
        create_initial_user(app)  
    app.run(debug=True, host='0.0.0.0')  
