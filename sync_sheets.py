from googleapiclient.discovery import build
from google.oauth2 import service_account
import mysql.connector


SERVICE_ACCOUNT_FILE = 'sync-435618-962845203da8.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '13eGjIe-Pq7aGGd_2gqeIp68CujiIGrm0hy7VymYzLOw'
RANGE = 'Sheet1!A1:D100'

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="sendhelp",
    database="sync"
)
cursor = db.cursor()


def get_sheet_data():
    
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE).execute()
    return result.get('values', [])


def sync_sheet_to_db(sheet_data):
    google_sheet_ids = set(row[0] for row in sheet_data if len(row) >= 3)

    
    cursor.execute("SELECT id FROM project")
    db_ids = set(str(row[0]) for row in cursor.fetchall())

    for row in sheet_data:
        if len(row) < 3:
            print(f"Skipping incomplete row: {row}")
            continue

        id = row[0]
        role = row[1]
        gender = row[2]

        
        print(f"Processing ID: {id}, Role: {role}, Gender: {gender}")

        
        cursor.execute("SELECT COUNT(*) FROM project WHERE id = %s", (id,))
        exists = cursor.fetchone()[0] > 0

        if exists:
           
            query = "UPDATE project SET role = %s, gender = %s WHERE id = %s"
            cursor.execute(query, (role, gender, int(id)))
        else:
           
            query = "INSERT INTO project (id, role, gender) VALUES (%s, %s, %s)"
            cursor.execute(query, (int(id), role, gender))

    rows_to_delete = db_ids - google_sheet_ids

    if rows_to_delete:
        print(f"Deleting rows with IDs: {rows_to_delete}")
        delete_query = "DELETE FROM project WHERE id = %s"
        for row_id in rows_to_delete:
            cursor.execute(delete_query, (row_id,))


    db.commit()

        

if __name__ == "__main__":
    sheet_data = get_sheet_data()
    sync_sheet_to_db(sheet_data)
