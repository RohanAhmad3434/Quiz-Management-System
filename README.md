📝 Quiz Management System

A full-stack web application that allows students to take quizzes, view results, and access study materials. 
Admins can create quizzes, upload study content, and manage users through a secure interface. 
The system features dynamic question handling, result evaluation, and role-based access.

🚀 Features

👨‍🏫 Admin Panel:
- Create and manage quizzes with multiple-choice questions
- Upload study materials (PDFs, docs) for student access
- View quiz results and user performance
- Manage users (students)

👨‍🎓 Student Panel:
- Register and log in to the system
- View and download study materials
- Attempt quizzes with randomized questions
- View scores and feedback


## 🧰 Tech Stack:

- Frontend: HTML, CSS, JavaScript  
- Backend: Python (Flask)  
- Database: MySQL  
- Tools:  
  - Postman (API Testing)   


🗂️ Folder Structure:

Quiz-Management-System/
│
├── Quiz Backend/              # Flask app for APIs, quiz logic
├── Quiz Frontend/             # HTML/CSS/JS for client interface
├── uploads/study_materials/   # Uploaded study content for students
└── .hintrc                    # Configuration file


🛠️ How to Run Locally

🔹 Step 1: Clone the Repository

git clone https://github.com/RohanAhmad3434/Quiz-Management-System.git
cd Quiz-Management-System


🔹 Step 2: Set Up Backend

1. Navigate to the backend folder:
   cd "Quiz Backend"
  
2. Create a virtual environment and activate it:
   python -m venv venv
   venv\Scripts\activate  # On Windows
   
3. Install dependencies:
   pip install -r requirements.txt
   
4. Configure your MySQL connection in config.py or app.py.
   
5. Run the Flask server:
   python app.py


🔹 Step 3: Run Frontend

1. Open the Quiz Frontend folder.
2. Launch index.html or respective UI file in your browser.
3. Ensure the frontend uses correct API endpoints (e.g., `http://localhost:5000/api/...`).


🔐 Authentication & Roles

- Role-based access control (Admin, Student)
- Session-based login.

