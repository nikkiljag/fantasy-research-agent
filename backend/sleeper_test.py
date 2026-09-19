import json
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "sleeper_players.json"


def get_all_players():
    if CACHE_FILE.exists():
        print("Loading player data from local cache...")
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    print("Downloading Sleeper player database...")

    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    response.raise_for_status()

    players = response.json()

    CACHE_FILE.parent.mkdir(exist_ok=True)

    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(players, file)

    print("Player database cached locally.")

    return players


username = input("Enter your Sleeper username: ")

# Get user
user_url = f"https://api.sleeper.app/v1/user/{username}"
user = requests.get(user_url).json()

if not user:
    print("Sleeper user not found.")
    raise SystemExit

user_id = user["user_id"]

# Get user's 2026 leagues
season = 2026
leagues_url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
leagues = requests.get(leagues_url).json()

league = leagues[0]
scoring_settings = league["scoring_settings"]
roster_positions = league["roster_positions"]
league_id = league["league_id"]

# Get league rosters
rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
rosters = requests.get(rosters_url).json()

my_roster = None

for roster in rosters:
    if roster["owner_id"] == user_id:
        my_roster = roster
        break

if my_roster is None:
    print("Could not find your roster.")
    raise SystemExit

# Load Sleeper player database
players = get_all_players()

print(f"\nLeague: {league['name']}")
print(f"Record: {my_roster['settings'].get('wins', 0)}-{my_roster['settings'].get('losses', 0)}")

print("\nRoster positions:")
print(roster_positions)

print("\nImportant scoring settings:")
print("Passing TD:", scoring_settings.get("pass_td", 0))
print("Passing yards:", scoring_settings.get("pass_yd", 0))
print("Rushing yards:", scoring_settings.get("rush_yd", 0))
print("Receiving yards:", scoring_settings.get("rec_yd", 0))
print("Reception:", scoring_settings.get("rec", 0))

starters = my_roster["starters"]
all_players = my_roster["players"]

bench = [player_id for player_id in all_players if player_id not in starters]

print("\nSTARTERS")

for player_id in starters:
    player = players.get(player_id)

    if player:
        name = player.get("full_name", player_id)
        position = player.get("position", "")
        team = player.get("team", "")
        print(f"{name} | {position} | {team}")
    else:
        print(f"{player_id} | DEF")

print("\nBENCH")

for player_id in bench:
    player = players.get(player_id)

    if player:
        name = player.get("full_name", player_id)
        position = player.get("position", "")
        team = player.get("team", "")
        print(f"{name} | {position} | {team}")
    else:
        print(f"{player_id} | DEF")