from flask import Flask
from database.database import db, User #need to mention the class one by one
from view import views  # Import views
from templates.usermanage.usermanage import usermanage
from templates.report.report import report_module
from flask_login import LoginManager
from datetime import timedelta
# from mqtttest.com import 




app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/database.db'  # Database location
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "mysecretkey"  # Change this to a more secure key later
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)


# Initialize the database
db.init_app(app)

# Initialize the Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'views.login'  # Ensure the correct view for login


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


app.register_blueprint(views) 
app.register_blueprint(usermanage)
app.register_blueprint(report_module)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

if __name__ == '__main__':
    with app.app_context():
        create_initial_user(app)  
    app.run(debug=True, host='0.0.0.0')  
