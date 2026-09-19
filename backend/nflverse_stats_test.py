import polars as pl

from sleeper import (
    get_leagues,
    get_rosters,
    get_user,
    get_user_roster,
)

from nflverse import (
    build_roster_mapping,
    get_players_missing_stats,
    get_roster_weekly_stats,
)


pl.Config.set_tbl_rows(-1)


username = input("Enter your Sleeper username: ")

# Sleeper data
user = get_user(username)

if not user:
    print("Sleeper user not found.")
    raise SystemExit

user_id = user["user_id"]

leagues = get_leagues(user_id)

if not leagues:
    print("No leagues found.")
    raise SystemExit

league = leagues[0]

rosters = get_rosters(league["league_id"])
my_roster = get_user_roster(rosters, user_id)

if my_roster is None:
    print("Could not find your roster.")
    raise SystemExit


# Build Sleeper -> nflverse mapping
print("\nBuilding roster player mapping...")

roster_mapping = build_roster_mapping(
    my_roster["players"]
)

print(f"Mapped {roster_mapping.height} individual players.")


# Load weekly NFL stats
print("\nLoading 2026 weekly NFL stats...")

roster_stats = get_roster_weekly_stats(
    roster_mapping,
    season=2026
)


# Useful columns for this test
desired_columns = [
    "week",
    "name",
    "position",
    "team",
    "opponent_team",

    "completions",
    "attempts",
    "passing_yards",
    "passing_tds",
    "passing_interceptions",

    "carries",
    "rushing_yards",
    "rushing_tds",

    "targets",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "receiving_air_yards",

    "fantasy_points",
    "fantasy_points_ppr",
]

available_columns = [
    column
    for column in desired_columns
    if column in roster_stats.columns
]

display_stats = (
    roster_stats
    .select(available_columns)
    .sort(["week", "name"])
)


print(f"\n2026 NFL stats for {league['name']}:\n")
print(display_stats)


# Show players with no weekly stats
missing_players = get_players_missing_stats(
    roster_mapping,
    roster_stats
)

if missing_players.height > 0:
    print("\nPlayers with no 2026 weekly stat rows yet:\n")
    print(missing_players)
else:
    print("\nAll mapped players currently have weekly stat rows.")