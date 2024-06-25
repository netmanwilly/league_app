import requests
import os
import sqlite3
import sys

requests.packages.urllib3.disable_warnings()


RIOT_API_KEY = 'REDACTED'

DATABASE = 'REDACTED'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def fetch_puuid(username):
    gameName = username.split("#")[0]
    tagLine = username.split("#")[1]
    URI = "https://americas.api.riotgames.com"
    API = f'/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}?api_key={RIOT_API_KEY}'

    HEADERS = {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com"
    }

    RESPONSE = requests.get(URI + API, headers=HEADERS, verify=False)
    if RESPONSE.status_code != 200:
        raise ValueError(f'ERROR FETCHING PUUID! {RESPONSE.status_code}')

    data = RESPONSE.json()
    return data['puuid']

def fetch_match_history(puuid):
    URI = "https://americas.api.riotgames.com"
    API = f'/lol/match/v5/matches/by-puuid/{puuid}/ids?api_key={RIOT_API_KEY}&count=10'

    HEADERS = {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com"
    }

    RESPONSE = requests.get(URI + API, headers=HEADERS, verify=False)
    if RESPONSE.status_code != 200:
        raise ValueError(f'ERROR FETCHING MATCH HISTORY! {RESPONSE.status_code}')

    data = RESPONSE.json()
    return data

def fetch_match_details(match_id):
    URI = "https://americas.api.riotgames.com"
    API = f'/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}'

    HEADERS = {
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://developer.riotgames.com"
    }

    RESPONSE = requests.get(URI + API, headers=HEADERS, verify=False)
    if RESPONSE.status_code != 200:
        raise ValueError(f'ERROR FETCHING MATCH DETAILS! {RESPONSE.status_code}')

    data = RESPONSE.json()
    return data

def update_database(username):
    conn = get_db()
    cursor = conn.cursor()

    puuid = fetch_puuid(username)
    match_ids = fetch_match_history(puuid)

    for match_id in match_ids:
        cursor.execute("""
            SELECT match_id FROM match_history WHERE match_id=? AND username=?
        """, (match_id, username))
    
        if cursor.fetchone() is not None:
            print(f"Match {match_id} for user {username} already in the database. Skipping.")
            continue

   # If match_id doesn't exist for this username, proceed with insertion
        match_data = fetch_match_details(match_id)  
        if match_data:
            try:
                metadata = match_data["metadata"]
                participants = metadata["participants"]
                epoch_time = int(match_data["info"]["gameStartTimestamp"] // 1000)
                user_index = participants.index(puuid)
                specific = match_data["info"]["participants"][user_index]

                champion = specific["championName"]
                kills = specific["kills"]
                deaths = specific["deaths"]
                assists = specific["assists"]
                win = specific["win"]

                cursor.execute('''
                    INSERT INTO match_history (match_id, champion, kills, deaths, assists, win, epoch_time, username)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (match_id, champion, kills, deaths, assists, win, epoch_time, username))

                print(f"Inserted match {match_id} for user {username} into database.")
            except Exception as e:
                print(f"Error processing match {match_id} for user {username}: {e}")
                continue
        else:
            print(f"Error fetching match details for {match_id}. Skipping.")
    
        conn.commit()  # Commit after each insertion or batch of insertions

    cursor.close()  # Close cursor after all operations



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python leaguestats.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    update_database(username)

