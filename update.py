import sqlite3
from datetime import datetime

db_path = 'REDACTED'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Assuming you have a way to get the epoch time for old records
cursor.execute("SELECT match_id FROM match_history WHERE epoch_time IS NULL")
match_ids = cursor.fetchall()

for match_id in match_ids:
    match_id = match_id[0]
    # Fetch the match data again or calculate the epoch time if possible
    # This example assumes the epoch time is fetched directly
    # Update the epoch_time column
    cursor.execute("""
        UPDATE match_history SET epoch_time = ?
        WHERE match_id = ?
    """, (new_epoch_time, match_id))

conn.commit()
conn.close()

