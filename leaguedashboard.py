from flask import Flask, render_template, request, redirect, url_for, jsonify, g
import sqlite3
import subprocess
import os
import json

app = Flask(__name__)

# Absolute path to the SQLite database
DATABASE = 'REDACTED'


def load_game_types(json_path):
    with open(json_path, 'r') as file:
        game_types = json.load(file)
    return {entry['queueId']: entry['description'] for entry in game_types}



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


game_types = load_game_types('/home/binu/league_app/game_types.json')

@app.route('/user/<username>')
def user_dashboard(username):
    conn = get_db()
    cursor = conn.cursor()

    # Fetch statistics
    cursor.execute("""
        SELECT AVG(kills) AS avg_kills, AVG(deaths) AS avg_deaths, AVG(assists) AS avg_assists
        FROM match_history
        WHERE username=? AND queueId=420
    """, (username,))
    result = cursor.fetchone()
    avg_kills, avg_deaths, avg_assists = (result['avg_kills'], result['avg_deaths'], result['avg_assists']) if result else (0, 0, 0)

    kda_ratio = (avg_kills + avg_assists) / avg_deaths if avg_deaths else 'Infinity'

    # Fetch win/loss counts
    cursor.execute("""
        SELECT COUNT(*) FROM match_history
        WHERE username=? AND win=1 AND queueId=420
    """, (username,))
    wins = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(*) FROM match_history
        WHERE username=? AND win=0 AND queueId=420
    """, (username,))
    losses = cursor.fetchone()[0]

    # Fetch top 3 champions
    cursor.execute("""
        SELECT champion, COUNT(*) AS champ_count
        FROM match_history
        WHERE username=? AND queueId=420
        GROUP BY champion
        ORDER BY champ_count DESC
        LIMIT 3
    """, (username,))
    top_champs = cursor.fetchall()

    # Fetch last 10 matches and calculate LP differences
    cursor.execute("""
        SELECT queueId, champion, kills, deaths, assists, win, lp_after_match
        FROM match_history
        WHERE username=? AND queueId=420
        ORDER BY epoch_time DESC
        LIMIT 10
    """, (username,))
    matches = cursor.fetchall()

    last_lp = None
    matches_with_diff = []
    for match in matches:
        queueId, champion, kills, deaths, assists, win, lp_after_match = match
        lp_diff = None
        if last_lp is not None:
            lp_diff = lp_after_match - last_lp
        formatted_lp_diff = f"{'+' if lp_diff is not None and lp_diff >= 0 else ''}{lp_diff}" if lp_diff is not None else "N/A"
        matches_with_diff.append((queueId, formatted_lp_diff, champion, kills, deaths, assists, 'Win' if win else 'Loss'))
        last_lp = lp_after_match

    # Fetch ranked information
    cursor.execute("""
        SELECT tier AS tier, rank AS rank, leaguepoints AS lp
        FROM ranked_info
        WHERE username=?
    """, (username,))
    ranked_result = cursor.fetchone()

    # Safely unpack the ranked result, or set defaults
    if ranked_result:
        tier = ranked_result['tier'].capitalize()
        rank = ranked_result['rank']
        lp = ranked_result['lp']
    else:
        tier, rank, lp = ('Unknown', 'N/A', 0)

    cursor.close()
    return render_template('user_dashboard.html',
                            username=username,
                            avg_kills=avg_kills,
                            avg_deaths=avg_deaths,
                            avg_assists=avg_assists,
                            kda_ratio=kda_ratio,
                            wins=wins,
                            losses=losses,
                            top_champs=top_champs,
                            last_entries=matches_with_diff,
                            tier=tier,
                            rank=rank,
                            lp=lp,
                            game_types=game_types)


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
