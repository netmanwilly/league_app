from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import sqlite3
import subprocess
import os

app = Flask(__name__)

# Absolute path to the SQLite database
DATABASE = 'REDACTED'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user/<username>')
def user_dashboard(username):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch statistics
    cursor.execute("""
        SELECT AVG(kills) AS avg_kills, AVG(deaths) AS avg_deaths, AVG(assists) AS avg_assists
        FROM match_history
        WHERE username=?
    """, (username,))
    result = cursor.fetchone()
    avg_kills, avg_deaths, avg_assists = (result['avg_kills'], result['avg_deaths'], result['avg_assists']) if result else (0, 0, 0)

    # Fetch win/loss counts
    cursor.execute("""
        SELECT COUNT(*) FROM match_history
        WHERE username=? AND win=1
    """, (username,))
    wins = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM match_history
        WHERE username=? AND win=0
    """, (username,))
    losses = cursor.fetchone()[0]
    win_loss_ratio = wins / (wins + losses) if (wins + losses) > 0 else 0.0

    # Fetch top 3 champions
    cursor.execute("""
        SELECT champion, COUNT(*) AS champ_count
        FROM match_history
        WHERE username=?
        GROUP BY champion
        ORDER BY champ_count DESC
        LIMIT 3
    """, (username,))
    top_champs = cursor.fetchall()

    # Fetch last 10 matches
    cursor.execute("""
        SELECT match_id, champion, kills, deaths, assists, win
        FROM match_history
        WHERE username=?
        ORDER BY epoch_time DESC
        LIMIT 10
    """, (username,))
    last_entries = cursor.fetchall()

    return render_template('user_dashboard.html', username=username, avg_kills=avg_kills, avg_deaths=avg_deaths, avg_assists=avg_assists,
                           win_loss_ratio=win_loss_ratio, top_champs=top_champs, last_entries=last_entries)

@app.route('/search_user', methods=['POST'])
def search_user():
    username = request.form['username']

    # Check if the user exists in the database
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM match_history
        WHERE username=?
    """, (username,))
    user_exists = cursor.fetchone()[0] > 0

    if not user_exists:
        # Fetch and insert data if user doesn't exist
        try:
            python_interpreter = 'REDACTED'
            script_path = 'REDACTED'
            subprocess.run([python_interpreter, script_path, username], check=True, env=os.environ.copy())
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return render_template('home.html', error="Failed to fetch data from the API.")

        # Re-check the database after attempting to fetch data
        cursor.execute("""
            SELECT COUNT(*) FROM match_history
            WHERE username=?
        """, (username,))
        user_exists = cursor.fetchone()[0] > 0

        if not user_exists:
            # If the user still does not exist, handle it appropriately
            return render_template('home.html', error="No data found for the user even after API fetch.")

    return redirect(url_for('user_dashboard', username=username))

@app.route('/update_user_data/<username>', methods=['POST'])
def update_user_data(username):
    try:
        python_interpreter = 'REDACTED'
        script_path = 'REDACTED'
        subprocess.run([python_interpreter, script_path, username], check=True, env=os.environ.copy())
        return redirect(url_for('user_dashboard', username=username))
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return jsonify(success=False), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    app.run(debug=True)
