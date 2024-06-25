from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)
DB_FILE = 'REDACTED'

def connect_db():
    conn = sqlite3.connect(DB_FILE)
    return conn

@app.route('/data', methods=['GET'])
def get_data():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM match_history")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)



