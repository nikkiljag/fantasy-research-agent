from services.analytics import summarize_team
from services.fantasy_data import get_team_context


username = input("Enter your Sleeper username: ")

try:
    team = get_team_context(username)

except ValueError as error:
    print(f"\nError: {error}")
    raise SystemExit


# ==================================================
# TEAM OVERVIEW
# ==================================================

print("\n==============================")
print("TEAM CONTEXT LOADED")
print("==============================")

print(f"\nLeague: {team['league']['name']}")

print(
    f"Record: "
    f"{team['roster']['wins']}-"
    f"{team['roster']['losses']}"
)

print(
    f"Roster players: "
    f"{len(team['player_contexts'])}"
)


# ==================================================
# PLAYER ANALYTICS
# ==================================================

summaries = summarize_team(
    team["player_contexts"]
)


print("\n==============================")
print("PLAYER SUMMARIES")
print("==============================")

for player in summaries:

    print(
        f"\n{player['name']} "
        f"| {player['position']} "
        f"| {player['lineup_status']}"
    )

    print(
        f"Games with stats: "
        f"{player['games_with_stats']}"
    )

    print(
        f"Latest game with stats: "
        f"Week {player['latest_game_week']}"
    )

    print(
        f"Latest NFL status: "
        f"{player['latest_status']} "
        f"(Week {player['latest_status_week']})"
    )

    print(
        f"Latest offensive snap %: "
        f"{player['latest_offense_snap_pct']} "
        f"(Week {player['latest_snap_week']})"
    )

    print(
        f"PPR average: "
        f"{player['fantasy']['average_ppr_points']}"
    )

    if "passing" in player:
        print(
            "Passing:",
            player["passing"]
        )

    if "rushing" in player:
        print(
            "Rushing:",
            player["rushing"]
        )

    if "receiving" in player:
        print(
            "Receiving:",
            player["receiving"]
        )


# ==================================================
# CHART DATA TEST
# ==================================================

print("\n==============================")
print("CHART DATA TEST")
print("==============================")

for player in summaries:

    if player["name"] == "Amon-Ra St. Brown":

        print(
            "\nAmon-Ra St. Brown:"
        )

        print(
            player["series"]
        )