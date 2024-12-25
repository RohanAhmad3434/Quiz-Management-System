from flask import Blueprint, request, jsonify
from models.db_connection import get_db_connection
import uuid
import subprocess

student_bp = Blueprint('student_bp', __name__)

# Student Login API
@student_bp.route('/login', methods=['POST'])
def student_login():
    """Login for Student"""
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Fetch student details
        query = "SELECT id, password FROM students WHERE email = %s"
        cursor.execute(query, (email,))
        student = cursor.fetchone()

        if not student or student['password'] != password:
            return jsonify({"error": "Invalid email or password"}), 401

        student_id = student['id']

        # Check if a session already exists
        cursor.execute("SELECT session_token FROM sessions WHERE student_id = %s", (student_id,))
        existing_session = cursor.fetchone()

        if existing_session:
            return jsonify({"error": "You are already logged in on another device"}), 403

        # Generate a unique session token
        session_token = str(uuid.uuid4())

        # Insert new session token into the database
        cursor.execute(
            "INSERT INTO sessions (student_id, session_token) VALUES (%s, %s)",
            (student_id, session_token)
        )
        conn.commit()

        return jsonify({
            "message": "Login successful",
            "id": student_id,
            "session_token": session_token
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# Student Logout API
@student_bp.route('/logout', methods=['POST'])
def student_logout():
    """Logout for Student"""
    data = request.json
    session_token = data.get('session_token')

    if not session_token:
        return jsonify({"error": "Session token is required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Remove session token from the database
        cursor.execute("DELETE FROM sessions WHERE session_token = %s", (session_token,))
        conn.commit()

        return jsonify({"message": "Logout successful"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()






# Fetch assigned quizzes for a student



@student_bp.route('/student/<int:student_id>/quizzes', methods=['GET'])
def get_assigned_quizzes(student_id):
    """Retrieve quizzes assigned to the student or their class."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT DISTINCT q.id AS quiz_id, q.title AS quiz_title, q.description 
            FROM quizzes q
            LEFT JOIN quiz_student_assignments qsa ON q.id = qsa.quiz_id AND qsa.student_id = %s
            LEFT JOIN quiz_class_assignments qca ON q.id = qca.quiz_id
            LEFT JOIN students s ON s.class_id = qca.class_id
            WHERE qsa.student_id = %s OR (s.id = %s AND qca.class_id = s.class_id)
        """
        cursor.execute(query, (student_id, student_id, student_id))
        quizzes = cursor.fetchall()
        return jsonify(quizzes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




@student_bp.route('/quizzes/<int:quiz_id>/questions', methods=['GET'])
def get_quiz_questions(quiz_id):
    """Retrieve questions and their options for the selected quiz."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT q.id AS question_id, q.question AS question_text, 
                   o.id AS option_id, o.option_text, o.is_correct 
            FROM quiz_questions q
            JOIN quiz_options o ON q.id = o.question_id
            WHERE q.quiz_id = %s
        """
        cursor.execute(query, (quiz_id,))
        data = cursor.fetchall()

        # Group questions with their options
        questions = {}
        for row in data:
            question_id = row['question_id']
            if question_id not in questions:
                questions[question_id] = {
                    "question_id": question_id,
                    "question_text": row['question_text'],
                    "options": []
                }
            questions[question_id]['options'].append({
                "option_id": row['option_id'],
                "option_text": row['option_text'],
                "is_correct": row['is_correct']  # Used for result calculation
            })

        return jsonify(list(questions.values())), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



#                   Submit Quiz API for student

@student_bp.route('/student/<int:student_id>/quizzes/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz_result(student_id, quiz_id):
    """Handle quiz submission, calculate score, and store results."""
    data = request.json
    answers = data.get('answers')  # {question_id: selected_option_id}

    if not answers:
        return jsonify({"error": "Answers are required"}), 400

    # Convert keys to integers for consistency
    answers = {int(k): v for k, v in answers.items()}

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the attempt limit for the quiz
        cursor.execute("SELECT attempt_limit FROM quizzes WHERE id = %s", (quiz_id,))
        quiz_data = cursor.fetchone()

        if not quiz_data:
            return jsonify({"error": "Quiz not found"}), 404

        attempt_limit = quiz_data['attempt_limit']

        # Check if the student has exceeded the attempt limit
        cursor.execute(
            "SELECT COUNT(*) AS attempt_count FROM quiz_results WHERE student_id = %s AND quiz_id = %s",
            (student_id, quiz_id)
        )
        attempt_count = cursor.fetchone()['attempt_count']

        if attempt_count >= attempt_limit:
            return jsonify({"error": f"You have reached the maximum attempt limit of {attempt_limit}"}), 403

        # Ensure the student is assigned to the quiz either directly or via class
        cursor.execute("""
            SELECT 1 FROM quizzes q
            LEFT JOIN quiz_student_assignments qsa ON q.id = qsa.quiz_id AND qsa.student_id = %s
            LEFT JOIN quiz_class_assignments qca ON q.id = qca.quiz_id
            LEFT JOIN students s ON qca.class_id = s.class_id
            WHERE q.id = %s AND (qsa.quiz_id IS NOT NULL OR s.id = %s)
        """, (student_id, quiz_id, student_id))
        assignment = cursor.fetchone()

        if not assignment:
            return jsonify({"error": "You are not assigned to this quiz"}), 403

        # Fetch correct answers
        cursor.execute("""
            SELECT q.id AS question_id, o.id AS correct_option_id
            FROM quiz_questions q
            JOIN quiz_options o ON q.id = o.question_id
            WHERE o.is_correct = 1 AND q.quiz_id = %s
        """, (quiz_id,))
        correct_answers = {row['question_id']: row['correct_option_id'] for row in cursor.fetchall()}

        # Calculate score
        score = sum(
            1 for q_id, opt_id in answers.items()
            if correct_answers.get(q_id) and int(correct_answers[q_id]) == int(opt_id)
        )

        # Store result
        feedback = f"Your score is {score}/{len(correct_answers)}."
        cursor.execute("""
            INSERT INTO quiz_results (student_id, quiz_id, attempt_number, score, feedback)
            VALUES (%s, %s, %s, %s, %s)
        """, (student_id, quiz_id, attempt_count + 1, score, feedback))
        conn.commit()
        
        try:
            subprocess.run(
                ['python', r'C:/Users/Abu Hurairah/Desktop/Quiz Project/Quiz Backend/google-sheet-integeration.py'], 
                check=True, 
                capture_output=True, 
                text=True
            )
            print("google-sheet-intergeration file run successfully")
        except FileNotFoundError as e:
            return jsonify({"error": f"Google Sheets integration script not found: {str(e)}"}), 500
        except subprocess.CalledProcessError as e:
            return jsonify({
                "error": "Failed to update Google Sheets.",
                "details": e.stderr or str(e)
            }), 500
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


      
        
        return jsonify({"message": "Quiz submitted successfully", "score": score, "feedback": feedback}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




#                   Result API for student

@student_bp.route('/student/<int:student_id>/results', methods=['GET'])
def get_student_results(student_id):
    """Retrieve quiz results for a specific student, grouped by quiz title and ordered by attempt number."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Query to fetch quiz results for the student
        results_query = """
            SELECT 
                qr.quiz_id,
                q.title AS quiz_title,
                qr.score,
                qr.feedback,
                qr.attempt_number
            FROM 
                quiz_results qr
            JOIN 
                quizzes q ON qr.quiz_id = q.id
            WHERE 
                qr.student_id = %s
            ORDER BY 
                q.title ASC, qr.attempt_number ASC
        """
        cursor.execute(results_query, (student_id,))
        results = cursor.fetchall()

        if not results:
            return jsonify({"message": "No results found for this student"}), 404

        # Group results by quiz title
        grouped_results = {}
        for result in results:
            quiz_title = result['quiz_title']
            if quiz_title not in grouped_results:
                grouped_results[quiz_title] = []
            grouped_results[quiz_title].append({
                "quiz_id": result['quiz_id'],
                "score": result['score'],
                "feedback": result['feedback'],
                "attempt_number": result['attempt_number']
            })

        # Convert grouped results to a list for JSON serialization
        response_data = [
            {"quiz_title": title, "results": grouped_results[title]}
            for title in grouped_results
        ]

        return jsonify({"student_id": student_id, "quizzes": response_data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()





#                     -------------------- get study material --------------------


@student_bp.route('/<int:student_id>/study-materials', methods=['GET'])
def get_study_materials(student_id):
    """Retrieve study materials for the student's class."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Fetch the student's class
        class_query = "SELECT class_id FROM students WHERE id = %s"
        cursor.execute(class_query, (student_id,))
        student = cursor.fetchone()

        if not student or not student['class_id']:
            return jsonify({"message": "Student is not enrolled in any class."}), 404

        class_id = student['class_id']

        # Fetch study materials for the class
        materials_query = """
            SELECT 
                sm.title, sm.description, sm.file_path, sm.uploaded_by
            FROM 
                study_materials sm
            WHERE 
                sm.class_id = %s
            ORDER BY 
                sm.title ASC
        """
        cursor.execute(materials_query, (class_id,))
        materials = cursor.fetchall()

        if not materials:
            return jsonify({"message": "No study materials available for this class."}), 404

        return jsonify({"class_id": class_id, "study_materials": materials}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()




#         -------------------       contact with Admin and get notifications -------------------

# Fetch Notifications for Student
@student_bp.route('/<int:student_id>/notifications', methods=['GET'])
def get_student_notifications(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT message, created_at FROM student_notifications
            WHERE student_id = %s
            UNION
            SELECT cn.message, cn.created_at
            FROM class_notifications cn
            JOIN students s ON cn.class_id = s.class_id
            WHERE s.id = %s
        """
        cursor.execute(query, (student_id, student_id))
        notifications = cursor.fetchall()
        return jsonify(notifications), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()



#                ----------------------- Send Message to Admin -----------------------

# Send Message to Admin
@student_bp.route('/messages', methods=['POST'])
def send_message_to_admin():
    data = request.json
    sender_id = data.get('sender_id')
    subject = data.get('subject')
    content = data.get('content')

    if not all([sender_id, subject, content]):
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO messages (sender_id, subject, content)
            VALUES (%s, %s, %s)
        """, (sender_id, subject, content))
        conn.commit()
        return jsonify({"message": "Message sent to admin"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
        
        
        
        
@student_bp.route('/messages/<int:student_id>', methods=['GET'])
def get_messages_by_student(student_id):
    """Fetch messages sent by a specific student."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, subject, content, created_at 
            FROM messages 
            WHERE sender_id = %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (student_id,))
        messages = cursor.fetchall()
        if not messages:
            return jsonify({"message": "No messages found for this student"}), 404
        return jsonify(messages), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
