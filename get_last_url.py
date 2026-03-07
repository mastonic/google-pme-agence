import sqlite3

try:
    conn = sqlite3.connect("backend/localpulse.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, generated_copy FROM businesses WHERE status='completed' LIMIT 1")
    row = cursor.fetchone()
    if row:
        print(f"Name: {row[0]}")
        print("Copy snippet:", row[1][-200:])
    else:
        print("No completed business")
    conn.close()
except Exception as e:
    print(e)
