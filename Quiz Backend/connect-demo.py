import mysql.connector

try:
    conn = mysql.connector.connect(
        host="DESKTOP-I4EERB9",
        user="Rohan",
        password="root",
        database="quiz"
    )
    print("Connection successful!")
except mysql.connector.Error as err:
    print(f"Error: {err}")
