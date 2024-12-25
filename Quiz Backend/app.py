# app.py
from flask import Flask
from flask_cors import CORS
from controllers.Admin_controller import admin_bp
from controllers.Student_controller import student_bp
from flask_mail import Mail

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication


# Email Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rohanahmad0345@gmail.com'
app.config['MAIL_PASSWORD'] = 'hxgd iqxn bver eeea'

# Initialize Mail
mail = Mail(app)


# Test API to check if the server is running
@app.route('/hello', methods=['GET'])
def hello_world():
    return "Hello, World! The flask server is running !"

# # Register Blueprints
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(student_bp, url_prefix='/api/student')

if __name__ == '__main__':
    app.run(debug=True)
