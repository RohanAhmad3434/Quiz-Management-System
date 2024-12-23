# app.py
from flask import Flask
from flask_cors import CORS
from controllers.Admin_controller import admin_bp
from controllers.Student_controller import student_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication


# Test API to check if the server is running
@app.route('/hello', methods=['GET'])
def hello_world():
    return "Hello, World! The flask server is running !"

# # Register Blueprints
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(student_bp, url_prefix='/api/student')

if __name__ == '__main__':
    app.run(debug=True)
