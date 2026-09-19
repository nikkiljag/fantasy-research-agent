import json
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CACHE_FILE = (
    PROJECT_ROOT
    / "data"
    / "cache"
    / "sleeper_players.json"
)


def get_user(username):
    """
    Retrieve a Sleeper user by username or user ID.
    """

    url = (
        f"https://api.sleeper.app/v1/user/"
        f"{username}"
    )

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_leagues(user_id, season=2026):
    """
    Retrieve all NFL leagues for a Sleeper user.
    """

    url = (
        f"https://api.sleeper.app/v1/user/"
        f"{user_id}/leagues/nfl/{season}"
    )

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_rosters(league_id):
    """
    Retrieve every roster in a Sleeper league.
    """

    url = (
        f"https://api.sleeper.app/v1/league/"
        f"{league_id}/rosters"
    )

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_league_users(league_id):
    """
    Retrieve every user / manager in a Sleeper league.
    """

    url = (
        f"https://api.sleeper.app/v1/league/"
        f"{league_id}/users"
    )

    response = requests.get(url)
    response.raise_for_status()

    return response.json()


def get_user_roster(rosters, user_id):
    """
    Find the roster owned by a specific Sleeper user.
    """

    for roster in rosters:

        if roster.get("owner_id") == user_id:
            return roster

    return None


def get_all_players():
    """
    Load the Sleeper NFL player database.

    Uses a local cache so the large player file
    is not downloaded repeatedly.
    """

    if CACHE_FILE.exists():

        print(
            "Loading player data from local cache..."
        )

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    print(
        "Downloading Sleeper player database..."
    )

    url = (
        "https://api.sleeper.app/v1/players/nfl"
    )

    response = requests.get(url)
    response.raise_for_status()

    players = response.json()

    CACHE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            players,
            file,
        )

    print(
        "Player database cached locally."
    )

    return players


def get_player_info(
    player_id,
    players,
):
    """
    Retrieve basic player information from
    Sleeper's player database.
    """

    player = players.get(player_id)

    if player:

        return {
            "id": player_id,
            "name": player.get(
                "full_name",
                player_id,
            ),
            "position": player.get(
                "position",
                "",
            ),
            "team": player.get(
                "team",
                "",
            ),
        }

    # Team defenses such as PIT
    return {
        "id": player_id,
        "name": f"{player_id} D/ST",
        "position": "DEF",
        "team": player_id,
    }