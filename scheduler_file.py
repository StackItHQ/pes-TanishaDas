import schedule
import time
from sync_sheets import sync_sheet_to_db
from sync_db import sync_db_to_sheet


schedule.every(5).minutes.do(sync_sheet_to_db)
schedule.every(5).minutes.do(sync_db_to_sheet)

while True:
    schedule.run_pending()
    time.sleep(1)
