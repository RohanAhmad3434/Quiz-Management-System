from flask import Blueprint, request, jsonify, current_app, send_file
from models.db_connection import get_db_connection
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message


from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials

def upload_to_drive(file_path, folder_id):
    """Upload a file to Google Drive and return its file ID."""
    try:
        print("Starting upload_to_drive function.")

        # Authenticate using the service account credentials
        print(f"Authenticating with service account credentials from: {file_path}")
        creds = Credentials.from_service_account_file(
            r'C:/Users/Abu Hurairah/Desktop/Quiz Project/Quiz Backend/controllers/service_account.json',
            scopes=['https://www.googleapis.com/auth/drive']
        )
        service = build('drive', 'v3', credentials=creds)
        print("Google Drive service initialized.")

        # Prepare the file metadata and upload
        print(f"Preparing to upload file: {file_path} to folder ID: {folder_id}")
        file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
        media = MediaFileUpload(file_path, resumable=True)

        # Uploading file
        uploaded_file = service.files().create(
            body=file_metadata, media_body=media, fields='id'
        ).execute()

        # Get the uploaded file ID
        file_id = uploaded_file.get('id')
        print(f"File uploaded successfully. File ID: {file_id}")

        return file_id
    except Exception as e:
        print("An error occurred during the file upload.")
        print(f"Error: {e}")
        return None  # Return None or handle the error as required


admin_bp = Blueprint('admin', __name__)

mail = Mail()

# Helper function to send email
def send_email(to_email, subject, body):
    try:
        msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=[to_email])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        raise Exception(f"Failed to send email: {e}")

# Admin Login API
@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Login for Admin"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT id, password FROM admins WHERE email = %s"
    cursor.execute(query, (email,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if not admin or admin['password'] != password:
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({"message": "Login successful", "id": admin['id']}), 200




# Create a new student
@admin_bp.route('/student/create', methods=['POST'])
def create_student():
    """Create a new student."""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    class_id = data.get('class_id')  # Optional field

    if not all([name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO students (name, email, password, class_id) 
        VALUES (%s, %s, %s, %s)
    """
    cursor.execute(query, (name, email, password, class_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Student created successfully"}), 201



# View all students
@admin_bp.route('/students', methods=['GET'])
def get_all_students():
    """Retrieve all students."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT s.id, s.name, s.email, c.name AS class_name 
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
    """
    cursor.execute(query)
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(students), 200



# Retrieve a student by ID
@admin_bp.route('/student/<int:student_id>', methods=['GET'])
def get_student_by_id(student_id):
    """Retrieve a specific student by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT s.id, s.name, s.email, c.name AS class_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = %s
    """
    cursor.execute(query, (student_id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()

    if not student:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(student), 200



# Update a student
@admin_bp.route('/student/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student details."""
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    class_id = data.get('class_id')  # Optional field

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        UPDATE students 
        SET name = %s, email = %s, password = %s, class_id = %s
        WHERE id = %s
    """
    cursor.execute(query, (name, email, password, class_id, student_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Student updated successfully"}), 200



# Delete a student
@admin_bp.route('/student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM students WHERE id = %s"
    cursor.execute(query, (student_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Student deleted successfully"}), 200


# Fetch all classes with id , name 
@admin_bp.route('/classes', methods=['GET'])
def get_classes():
    """Retrieve all classes."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name FROM classes"
    cursor.execute(query)
    classes = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(classes), 200




#                  Classes Apis

# Create a new class
@admin_bp.route('/class/create', methods=['POST'])
def create_class():
    """Create a new class."""
    data = request.json
    name = data.get('name')
    created_by = data.get('created_by')

    if not name:
        return jsonify({"error": "Class name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO classes (name, created_by) 
        VALUES (%s, %s)
    """
    cursor.execute(query, (name, created_by))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Class created successfully"}), 201

# Update a class
@admin_bp.route('/class/<int:class_id>', methods=['PUT'])
def update_class(class_id):
    """Update class details."""
    data = request.json
    name = data.get('name')

    if not name:
        return jsonify({"error": "Class name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        UPDATE classes 
        SET name = %s
        WHERE id = %s
    """
    cursor.execute(query, (name, class_id))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Class updated successfully"}), 200

# Delete a class
@admin_bp.route('/class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    """Delete a class."""
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM classes WHERE id = %s"
    cursor.execute(query, (class_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Class deleted successfully"}), 200


# retrieve all classes with id , name , cretaed_by
@admin_bp.route('/class/classes', methods=['GET'])
def retrieve_classes():
    """Retrieve all classes."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id, name, created_by FROM classes"
    cursor.execute(query)
    classes = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(classes), 200


# Fetch admin name by created_by
@admin_bp.route('/admin/<int:admin_id>', methods=['GET'])
def get_admin_name(admin_id):
    """Fetch admin name by ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT name FROM admins WHERE id = %s"
    cursor.execute(query, (admin_id,))
    admin = cursor.fetchone()
    cursor.close()
    conn.close()

    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    return jsonify(admin), 200

# Retrieve a class by class_id along with the admin's name (created_by)
@admin_bp.route('/class/<int:class_id>', methods=['GET'])
def get_class_by_id(class_id):
    """Retrieve a class by its ID along with the admin's name who created it."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query to fetch class details and admin's name based on created_by
    query = """
        SELECT c.name
        FROM classes c
        WHERE c.id = %s
    """
    cursor.execute(query, (class_id,))
    class_details = cursor.fetchone()
    cursor.close()
    conn.close()

    if not class_details:
        return jsonify({"error": "Class not found"}), 404

    return jsonify(class_details), 200




#                              Quiz Apis 

# Add a new quiz
@admin_bp.route('/quiz/create', methods=['POST'])
def create_quiz():
    """Create a new quiz."""
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    attempt_limit = data.get('attempt_limit', 3)
    created_by = data.get('created_by')

    if not title or not created_by:
        return jsonify({"error": "Title and Created By are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO quizzes (title, description, attempt_limit, created_by)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (title, description, attempt_limit, created_by))
        conn.commit()
        return jsonify({"message": "Quiz created successfully"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Update a quiz
@admin_bp.route('/quiz/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    """Update quiz details."""
    data = request.json
    title = data.get('title')
    description = data.get('description', '')
    attempt_limit = data.get('attempt_limit')

    if not title:
        return jsonify({"error": "Title is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            UPDATE quizzes
            SET title = %s, description = %s, attempt_limit = %s
            WHERE id = %s
        """
        cursor.execute(query, (title, description, attempt_limit, quiz_id))
        conn.commit()
        return jsonify({"message": "Quiz updated successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Delete a quiz
@admin_bp.route('/quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    """Delete a quiz."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM quizzes WHERE id = %s"
        cursor.execute(query, (quiz_id,))
        conn.commit()
        return jsonify({"message": "Quiz deleted successfully"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Retrieve all quizzes
@admin_bp.route('/quiz/all', methods=['GET'])
def retrieve_all_quizzes():
    """Retrieve all quizzes."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, title, description, attempt_limit, created_by FROM quizzes"
        cursor.execute(query)
        quizzes = cursor.fetchall()
        return jsonify(quizzes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Retrieve a quiz by ID
@admin_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
def retrieve_quiz_by_id(quiz_id):
    """Retrieve a specific quiz by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, title, description, attempt_limit, created_by FROM quizzes WHERE id = %s"
        cursor.execute(query, (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            return jsonify({"error": "Quiz not found"}), 404

        return jsonify(quiz), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
        
        
        
#                          Question Apis for Quiz

    
        
 # Create a question for a quiz
@admin_bp.route('/quiz/<int:quiz_id>/question', methods=['POST'])
def create_question(quiz_id):
    """Create a question for a quiz."""
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question text is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO quiz_questions (quiz_id, question)
            VALUES (%s, %s)
        """
        cursor.execute(query, (quiz_id, question))
        conn.commit()
        return jsonify({"message": "Question created successfully"}), 201
    except Exception as e:
        conn.rollback()
        if "Duplicate entry" in str(e):
            return jsonify({"error": "This question already exists for the quiz"}), 400
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Retrieve questions by quiz ID
@admin_bp.route('/quiz/<int:quiz_id>/questions', methods=['GET'])
def retrieve_questions_by_quiz_id(quiz_id):
    """Retrieve all questions for a specific quiz."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, question
            FROM quiz_questions
            WHERE quiz_id = %s
        """
        cursor.execute(query, (quiz_id,))
        questions = cursor.fetchall()

        if not questions:
            return jsonify({"message": "No questions found for this quiz"}), 404

        return jsonify(questions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
       


# Retrieve all questions
@admin_bp.route('/questions', methods=['GET'])
def retrieve_all_questions():
    """Retrieve all questions across all quizzes."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT quiz_questions.id, quiz_questions.question, quizzes.title AS quiz_title
            FROM quiz_questions
            JOIN quizzes ON quiz_questions.quiz_id = quizzes.id
        """
        cursor.execute(query)
        questions = cursor.fetchall()

        if not questions:
            return jsonify({"message": "No questions found"}), 404

        return jsonify(questions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
        
        
        
#                          option Apis for Question

# Create an option
@admin_bp.route('/options/create', methods=['POST'])
def create_option():
    """Create an option for a specific question."""
    data = request.json
    question_id = data.get('question_id')
    option_text = data.get('option_text')
    is_correct = data.get('is_correct', False)

    if not question_id or not option_text:
        return jsonify({"error": "Question ID and Option Text are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO quiz_options (question_id, option_text, is_correct)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (question_id, option_text, is_correct))
        conn.commit()
        return jsonify({"message": "Option created successfully"}), 201
    except Exception as e:
        if e.args[0] == 1062:  # Duplicate entry error
            return jsonify({"error": "Option already exists for this question"}), 400
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# Retrieve options by question ID
@admin_bp.route('/options/<int:question_id>', methods=['GET'])
def retrieve_options_by_question(question_id):
    """Retrieve all options for a specific question."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, option_text, is_correct
            FROM quiz_options
            WHERE question_id = %s
        """
        cursor.execute(query, (question_id,))
        options = cursor.fetchall()

        if not options:
            return jsonify({"message": "No options found for this question"}), 404

        return jsonify(options), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



@admin_bp.route('/options', methods=['GET'])
def retrieve_all_options():
    """Retrieve all options across all questions."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                quiz_options.id AS option_id,
                quiz_options.option_text,
                quiz_options.is_correct,
                quiz_questions.id AS question_id,
                quiz_questions.question AS question_text
            FROM quiz_options
            JOIN quiz_questions ON quiz_options.question_id = quiz_questions.id
        """
        cursor.execute(query)
        options = cursor.fetchall()

        if not options:
            return jsonify({"message": "No options found"}), 404

        return jsonify(options), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





#                    Quiz-student Assignment Apis   



@admin_bp.route('/assignments/create', methods=['POST'])
def create_quiz_assignment():
    """
    Assign a quiz to a student.
    """
    data = request.json
    quiz_id = data.get('quiz_id')
    student_id = data.get('student_id')

    if not quiz_id or not student_id:
        return jsonify({"error": "Quiz ID and Student ID are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO quiz_student_assignments (quiz_id, student_id)
            VALUES (%s, %s)
        """
        cursor.execute(query, (quiz_id, student_id))
        conn.commit()
        return jsonify({"message": "Quiz assigned to student successfully"}), 201
    except Exception as e:
        if e.args[0] == 1062:  # Duplicate entry error
            return jsonify({"error": "This quiz is already assigned to this student"}), 400
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/assignments', methods=['GET'])
def get_all_assignments():
    """
    Retrieve all quiz assignments.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                a.id AS assignment_id,
                q.title AS quiz_title,
                s.name AS student_name,
                a.quiz_id,
                a.student_id
            FROM 
                quiz_student_assignments a
            JOIN quizzes q ON a.quiz_id = q.id
            JOIN students s ON a.student_id = s.id
        """
        cursor.execute(query)
        assignments = cursor.fetchall()

        results = []
        for assignment in assignments:
            results.append({
                "assignment_id": assignment[0],
                "quiz_title": assignment[1],
                "student_name": assignment[2],
                "quiz_id": assignment[3],
                "student_id": assignment[4]
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """
    Delete a specific quiz assignment.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM quiz_student_assignments WHERE id = %s"
        cursor.execute(query, (assignment_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Assignment not found"}), 404
        return jsonify({"message": "Assignment deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
    
    
    
#              --------------------------    Quiz-class Assignment Apis----------------------


@admin_bp.route('/class-assignments/create', methods=['POST'])
def create_class_assignment():
    """
    Assign a quiz to a class.
    """
    data = request.json
    quiz_id = data.get('quiz_id')
    class_id = data.get('class_id')

    if not quiz_id or not class_id:
        return jsonify({"error": "Quiz ID and Class ID are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO quiz_class_assignments (quiz_id, class_id)
            VALUES (%s, %s)
        """
        cursor.execute(query, (quiz_id, class_id))
        conn.commit()
        return jsonify({"message": "Quiz assigned to class successfully"}), 201
    except Exception as e:
        if e.args[0] == 1062:  # Duplicate entry error
            return jsonify({"error": "This quiz is already assigned to this class"}), 400
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/class-assignments', methods=['GET'])
def get_all_class_assignments():
    """
    Retrieve all quiz-class assignments.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            SELECT 
                a.id AS assignment_id,
                q.title AS quiz_title,
                c.name AS class_name,
                a.quiz_id,
                a.class_id
            FROM 
                quiz_class_assignments a
            JOIN quizzes q ON a.quiz_id = q.id
            JOIN classes c ON a.class_id = c.id
        """
        cursor.execute(query)
        assignments = cursor.fetchall()

        results = []
        for assignment in assignments:
            results.append({
                "assignment_id": assignment[0],
                "quiz_title": assignment[1],
                "class_name": assignment[2],
                "quiz_id": assignment[3],
                "class_id": assignment[4]
            })

        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@admin_bp.route('/class-assignments/<int:assignment_id>', methods=['DELETE'])
def delete_class_assignment(assignment_id):
    """
    Delete a specific quiz-class assignment.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "DELETE FROM quiz_class_assignments WHERE id = %s"
        cursor.execute(query, (assignment_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Assignment not found"}), 404
        return jsonify({"message": "Assignment deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





#                              create Quiz Results Api


@admin_bp.route('/results/create', methods=['POST'])
def create_result():
    """
    Create a result entry for a quiz attempt.
    """
    data = request.json
    student_id = data.get('student_id')
    quiz_id = data.get('quiz_id')
    attempt_number = data.get('attempt_number')
    score = data.get('score')
    feedback = data.get('feedback', None)

    # Validate required fields
    if not student_id or not quiz_id or not attempt_number or score is None:
        return jsonify({"error": "Student ID, Quiz ID, Attempt Number, and Score are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert into the quiz_results table
        query = """
            INSERT INTO quiz_results (student_id, quiz_id, attempt_number, score, feedback)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (student_id, quiz_id, attempt_number, score, feedback))
        conn.commit()

        return jsonify({"message": "Result created successfully"}), 201
    except Exception as e:
        if e.args[0] == 1062:  # Duplicate entry error
            return jsonify({"error": "Result for this attempt already exists"}), 400
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()






#                    ----------- view Quiz Results Api --------------

@admin_bp.route('/results', methods=['GET'])
def get_all_results():
    """Retrieve all quiz results grouped by quiz title."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Query to fetch grouped quiz results
        results_query = """
            SELECT 
                s.name AS student_name,
                q.title AS quiz_title,
                qr.score,
                qr.feedback,
                qr.attempt_number
            FROM 
                quiz_results qr
            JOIN 
                students s ON qr.student_id = s.id
            JOIN 
                quizzes q ON qr.quiz_id = q.id
            ORDER BY 
                q.title ASC, s.name ASC, qr.attempt_number ASC
        """
        cursor.execute(results_query)
        results = cursor.fetchall()

        if not results:
            return jsonify({"message": "No results found"}), 404

        # Group results by quiz title
        grouped_results = {}
        for result in results:
            quiz_title = result['quiz_title']
            if quiz_title not in grouped_results:
                grouped_results[quiz_title] = []
            grouped_results[quiz_title].append({
                "student_name": result['student_name'],
                "score": result['score'],
                "feedback": result['feedback'],
                "attempt_number": result['attempt_number']
            })

        return jsonify(grouped_results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()






#             ----------------------- Upload study material api-------------------

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads', 'study_materials')  # Absolute path
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt', 'xlsx'}

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if the file type is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/study-materials/upload', methods=['POST'])
def upload_study_material():
    """Admin uploads and assigns study material to a class."""
    title = request.form.get('title')
    description = request.form.get('description', '')
    class_id = request.form.get('class_id')
    admin_id = request.form.get('admin_id')
    file = request.files.get('file')

    if not title or not class_id or not admin_id or not file:
        return jsonify({"error": "All fields (title, class_id, admin_id, and file) are required."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed."}), 400

    # Save the file temporarily
    filename = secure_filename(file.filename)
    local_file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(local_file_path)
    print(f"File saved locally at {local_file_path}")

    try:
        print("Saving file locally...")
        # Upload file to Google Drive
        folder_id = "15tm2g81xTv0H2UYv_pYnnvwc-D8juZLr"  # Replace with your Drive folder ID
        drive_file_id = upload_to_drive(local_file_path, folder_id)
        if not drive_file_id:
            raise ValueError("File upload to Google Drive failed. No file ID returned.")
        print("File uploaded to Google Drive with ID:", drive_file_id)

        # Insert study material record into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO study_materials (title, description, file_path, file_drive_id, class_id, uploaded_by)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        # Save the file path and drive file ID
        drive_file_link = f"https://drive.google.com/file/d/{drive_file_id}/view"
        cursor.execute(query, (title, description, drive_file_link, drive_file_id, class_id, admin_id))
        conn.commit()
        print("Database insertion successful.")
        # Only return a minimal success message
        return jsonify({"message": "Study material uploaded successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

@admin_bp.route('/study-materials/download/<filename>', methods=['GET'])
def download_study_material(filename):
    """Serve the study material file for download."""
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found."}), 404

        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
        
        
        

@admin_bp.route('/study-materials', methods=['GET'])
def get_study_materials():
    """Retrieve all uploaded study materials with class names."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                sm.id, 
                sm.title, 
                sm.description, 
                sm.file_path, 
                c.name AS class_name
            FROM 
                study_materials sm
            LEFT JOIN 
                classes c ON sm.class_id = c.id
        """
        cursor.execute(query)
        materials = cursor.fetchall()
        return jsonify({"materials": materials}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





#                    ------------------------------------------------------------------


# Send Notification to Class
@admin_bp.route('/notifications/class', methods=['POST'])
def send_class_notification():
    data = request.json
    message = data.get('message')
    class_id = data.get('class_id')
    admin_id = data.get('created_by')

    if not all([message, class_id, admin_id]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch all students in the specified class
        cursor.execute("""
            SELECT name, email
            FROM students
            WHERE class_id = %s
        """, (class_id,))
        students = cursor.fetchall()

        if not students:
            return jsonify({"error": "No students found for the specified class"}), 404

        # Insert the notification into the class_notifications table
        cursor.execute("""
            INSERT INTO class_notifications (message, class_id, created_by)
            VALUES (%s, %s, %s)
        """, (message, class_id, admin_id))
        conn.commit()

        # Send emails to each student
        for student in students:
            student_email = student['email']
            student_name = student['name']

            # Send email to the student
            subject = "New Class Notification"
            body = f"Dear {student_name},\n\n{message}\n\nBest regards,\nAdmin Team"
            send_email(student_email, subject, body)

        return jsonify({"message": "Notification sent to class and emails delivered to all students"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# Send Notification to Student
@admin_bp.route('/notifications/student', methods=['POST'])
def send_student_notification():
    data = request.json
    message = data.get('message')
    student_id = data.get('student_id')
    admin_id = data.get('created_by')

    if not all([message, student_id, admin_id]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the student's email and name
        cursor.execute("SELECT name, email FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Insert the notification into the database
        cursor.execute("""
            INSERT INTO student_notifications (message, student_id, created_by)
            VALUES (%s, %s, %s)
        """, (message, student_id, admin_id))
        conn.commit()

        # Send email to the student
        student_email = student['email']
        student_name = student['name']
        subject = "New Notification from Admin"
        body = f"Dear {student_name},\n\n{message}\n\nBest regards,\nAdmin Team"
        send_email(student_email, subject, body)

        return jsonify({"message": "Notification sent to student and email delivered"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




#          -------------------------View Messages from Students-------------------

# View Messages from Students
@admin_bp.route('/messages', methods=['GET'])
def view_student_messages():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                m.id AS message_id,
                s.name AS student_name,
                m.subject AS message_title,
                m.content AS message_content,
                m.created_at AS sent_at
            FROM messages m
            JOIN students s ON m.sender_id = s.id
            ORDER BY m.created_at DESC
        """
        cursor.execute(query)
        messages = cursor.fetchall()
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# ----------------------------------------------------------------------------

@admin_bp.route('/notifications/classes', methods=['GET'])
def view_class_notifications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                cn.id AS notification_id,
                c.name AS class_name,
                cn.message AS notification_message,
                cn.created_at AS sent_at
            FROM class_notifications cn
            JOIN classes c ON cn.class_id = c.id
            ORDER BY cn.created_at DESC
        """
        cursor.execute(query)
        notifications = cursor.fetchall()
        return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
        
        
@admin_bp.route('/notifications/students', methods=['GET'])
def view_student_notifications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 
                sn.id AS notification_id,
                s.name AS student_name,
                sn.message AS notification_message,
                sn.created_at AS sent_at
            FROM student_notifications sn
            JOIN students s ON sn.student_id = s.id
            ORDER BY sn.created_at DESC
        """
        cursor.execute(query)
        notifications = cursor.fetchall()
        return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





#                --------------------- ----------------------- -------------------

# Fetch Class ID by Class Name
@admin_bp.route('/class/id', methods=['GET'])
def get_class_id_by_name():
    """Retrieve a class ID by its name."""
    class_name = request.args.get('name', '').strip()
    if not class_name:
        return jsonify({"error": "Class name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id FROM classes WHERE name = %s LIMIT 1"
    cursor.execute(query, (class_name,))
    class_record = cursor.fetchone()
    cursor.close()
    conn.close()

    if class_record:
        return jsonify({"id": class_record['id']}), 200
    else:
        return jsonify({"error": "Class not found"}), 404


# Fetch Student ID by Student Name
@admin_bp.route('/student/id', methods=['GET'])
def get_student_id_by_name():
    """Retrieve a student ID by their name."""
    student_name = request.args.get('name', '').strip()
    if not student_name:
        return jsonify({"error": "Student name is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id FROM students WHERE name = %s LIMIT 1"
    cursor.execute(query, (student_name,))
    student_record = cursor.fetchone()
    cursor.close()
    conn.close()

    if student_record:
        return jsonify({"id": student_record['id']}), 200
    else:
        return jsonify({"error": "Student not found"}), 404
