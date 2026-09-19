import json
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "sleeper_players.json"


def get_user(username):
    url = f"https://api.sleeper.app/v1/user/{username}"
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_leagues(user_id, season=2026):
    url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/{season}"
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_rosters(league_id):
    url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_user_roster(rosters, user_id):
    for roster in rosters:
        if roster["owner_id"] == user_id:
            return roster

    return None


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

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(players, file)

    print("Player database cached locally.")

    return players


def get_player_info(player_id, players):
    player = players.get(player_id)

    if player:
        return {
            "id": player_id,
            "name": player.get("full_name", player_id),
            "position": player.get("position", ""),
            "team": player.get("team", ""),
        }

    # Handles team defenses such as PIT
    return {
        "id": player_id,
        "name": player_id,
        "position": "DEF",
        "team": player_id,
    }