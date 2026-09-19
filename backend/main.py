from services.fantasy_data import get_team_context


username = input("Enter your Sleeper username: ")

try:
    team = get_team_context(username)

except ValueError as error:
    print(f"\nError: {error}")
    raise SystemExit


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
    f"{len(team['roster']['players'])}"
)

print(
    f"Mapped NFL players: "
    f"{team['roster_mapping'].height}"
)

print(
    f"Weekly stat rows: "
    f"{team['weekly_stats'].height}"
)

print(
    f"Snap-count rows: "
    f"{team['snap_counts'].height}"
)

print(
    f"Weekly status rows: "
    f"{team['weekly_status'].height}"
)