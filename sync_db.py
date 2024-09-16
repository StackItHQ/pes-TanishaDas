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

def get_mysql_data():
    cursor.execute("SELECT * FROM project")
    return cursor.fetchall()


def get_sheet_data():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE).execute()
    return result.get('values', [])


def sync_db_to_sheet(db_data, sheet_data):
    
    google_sheet_ids = set(row[0] for row in sheet_data if len(row) >= 3)


    db_ids = set(str(row[0]) for row in db_data)

  
    for db_row in db_data:
        id = str(db_row[0])
        role = db_row[1]
        gender = db_row[2]

        
        if id in google_sheet_ids:
            print(f"Updating ID {id} in Google Sheets")
            range_name = f'Sheet1!A{id}:C{id}'
            values = [[id, role, gender]]
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption="RAW",
                body={"values": values}
            ).execute()
        else:
            print(f"Inserting ID {id} in Google Sheets")
            new_row_values = [id, role, gender]
            sheet_data.append(new_row_values)
            service.spreadsheets().values().append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE,
                valueInputOption="RAW",
                body={"values": [new_row_values]}
            ).execute()

  
    rows_to_delete = google_sheet_ids - db_ids
    if rows_to_delete:
        print(f"Deleting rows with IDs: {rows_to_delete}")
        delete_rows_from_sheet(rows_to_delete)

def delete_rows_from_sheet(rows_to_delete):
    requests = []
    for row_id in rows_to_delete:
        requests.append({
            "deleteDimension": {
                "range": {
                    "sheetId": 0,  
                    "dimension": "ROWS",
                    "startIndex": int(row_id) - 1,
                    "endIndex": int(row_id)
                }
            }
        })

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()

if __name__ == "__main__":
 
    db_data = get_mysql_data()
    sheet_data = get_sheet_data()

    sync_db_to_sheet(db_data, sheet_data)
