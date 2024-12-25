import mysql.connector
from mysql.connector import Error
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets setup
SERVICE_ACCOUNT_FILE = r'C:/Users/Abu Hurairah/Desktop/Quiz Project/Quiz Backend/credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

try:
    print("Loading Google Sheets credentials...")
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    print("Google Sheets authentication successful.")
except Exception as e:
    print(f"Error loading Google Sheets credentials: {e}")
    exit()

# Open the Google Sheet
SPREADSHEET_ID = '1Ql4A3XeyTwaPWpMOslpF5_wyKQNJ2PkvMcq5ibaBdoI'
try:
    print("Opening Google Sheet...")
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    print("Google Sheet opened successfully.")
except Exception as e:
    print(f"Error opening Google Sheet: {e}")
    exit()

# MySQL connection setup
def get_db_connection():
    try:
        print("Establishing database connection...")
        conn = mysql.connector.connect(
            host='DESKTOP-I4EERB9',
            user='Rohan',
            password='root',
            database='quiz'
        )
        print("Database connection established successfully.")
        return conn
    except Error as e:
        print(f"Error connecting to the database: {e}")
        exit()

# Function to fetch new rows from quiz_summary and write to Google Sheets
def sync_to_google_sheet():
    try:
        print("Starting sync process to Google Sheets...")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        print("Fetching unsynced rows from the database...")
        query = "SELECT * FROM quiz_summary WHERE synced_to_google = 0"
        cursor.execute(query)
        new_rows = cursor.fetchall()
        print(f"Fetched {len(new_rows)} new rows.")

        if new_rows:
            print("Writing rows to Google Sheets...")
        for row in new_rows:
            # Convert datetime object to string
            inserted_at = row['inserted_at'].strftime('%Y-%m-%d %H:%M:%S') if row['inserted_at'] else None

            sheet.append_row([
                row['id'], row['student_name'], row['quiz_title'],
                row['score'], row['attempt_number'], row['feedback'], inserted_at
            ])
            print(f"Row with ID {row['id']} written to Google Sheets.")

            # Mark the row as synced
            update_query = "UPDATE quiz_summary SET synced_to_google = 1 WHERE id = %s"
            cursor.execute(update_query, (row['id'],))

        conn.commit()
        print("All rows synced and database updated.")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Database error during sync: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during sync: {e}")

# Main function
if __name__ == '__main__':
    print("Starting Google Sheets integration script...")
    sync_to_google_sheet()
    print("Google Sheets integration script completed.")
