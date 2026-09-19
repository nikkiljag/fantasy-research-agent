from sleeper import (
    get_all_players,
    get_leagues,
    get_player_info,
    get_rosters,
    get_user,
    get_user_roster,
)


username = input("Enter your Sleeper username: ")

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
league_id = league["league_id"]

rosters = get_rosters(league_id)
my_roster = get_user_roster(rosters, user_id)

if my_roster is None:
    print("Could not find your roster.")
    raise SystemExit

players = get_all_players()

scoring_settings = league["scoring_settings"]
roster_positions = league["roster_positions"]

starters = my_roster["starters"]
all_players = my_roster["players"]

bench = [
    player_id
    for player_id in all_players
    if player_id not in starters
]

print(f"\nLeague: {league['name']}")
print(
    f"Record: "
    f"{my_roster['settings'].get('wins', 0)}-"
    f"{my_roster['settings'].get('losses', 0)}"
)

print("\nRoster positions:")
print(roster_positions)

print("\nImportant scoring settings:")
print("Passing TD:", scoring_settings.get("pass_td", 0))
print("Passing yards:", scoring_settings.get("pass_yd", 0))
print("Rushing yards:", scoring_settings.get("rush_yd", 0))
print("Receiving yards:", scoring_settings.get("rec_yd", 0))
print("Reception:", scoring_settings.get("rec", 0))

print("\nSTARTERS")

for player_id in starters:
    player = get_player_info(player_id, players)

    print(
        f"{player['name']} | "
        f"{player['position']} | "
        f"{player['team']}"
    )

print("\nBENCH")

for player_id in bench:
    player = get_player_info(player_id, players)

    print(
        f"{player['name']} | "
        f"{player['position']} | "
        f"{player['team']}"
    )